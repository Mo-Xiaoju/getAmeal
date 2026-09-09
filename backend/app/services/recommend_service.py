"""首页推荐流打分引擎（设计文档《首页推荐流算法设计.md》§6 的归一化落地版）。

范围 = A+B：
- A 规则改进：贝叶斯平滑评分（修“5.0/1 压过 4.8/200”的冷启动陷阱）、时间新鲜度衰减、
  严格过滤 `is_active + status='approved'`（笔记本身无 status，靠父店过滤）。
- B 轻个性化：把用户**在该校内**（school_id 收敛，防跨校串味）的收藏/好评/点赞/收藏帖
  等行为聚合成轻画像 RecProfile；证据足够时把各维偏好折进店铺/菜品/笔记三轨打分，
  否则退化为改进版热门榜（**绝不返回空列表**）。

与设计文档的一处实现修正：md 原式把 0–5 的评分与 0–1 的 fresh/cat 直接加权，量纲不一致；
这里统一把评分类项归一化到 0..1（`bayes/5`）再加权，权重才表达真实相对份额。

可解释性：每项附 `rec_reason`（原因列表），无该偏好维度时不写入。阶段 C（埋点闭环）不在本期。
"""
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.categories import canonicalize, family_of
from app.extensions import db
from app.models import Dish, Favorite, Like, Post, Review, Shop, UserFollow
from app.schemas.dish import DishSchema
from app.schemas.shop import ShopSchema
from app.services.shop_service import _haversine_km

_shop_list_schema = ShopSchema(many=True)
_dish_list_schema = DishSchema(many=True)
DEFAULT_LIMIT = 6
BAYES_M = 10             # 贝叶斯平滑先验强度（折算的虚拟样本数）
EVIDENCE_MIN = 3         # 画像可用所需的最少正向行为数
MIN_DISTINCT_SHOPS = 2   # 画像可用所需的最少去重店铺
POOL_LIMIT = 200         # 候选池上限（池内先按人气预取，再做全量打分）
PRIOR_FALLBACK = 4.0     # 全校无评分时的默认先验均分
TAU = {'shop': 180, 'dish': 90, 'post': 14}          # 新鲜度衰减窗口（天，线性衰减至 0）
W_SHOP = {'quality': 0.45, 'fresh': 0.15, 'cat': 0.30, 'author': 0.10}
W_DISH = {'quality': 0.50, 'parent': 0.30, 'tags': 0.20}
W_POST = {'hot': 0.35, 'fresh': 0.30, 'author': 0.20, 'sim': 0.15}

# 判定某维“足以写进 rec_reason”的阈值
_REASON_FRESH_DAYS = {'shop': 21, 'dish': 7, 'post': 3}
_REASON_QUALITY = 0.80   # 归一化质量 >= 0.8 视为口碑好
_REASON_HOT = 0.50       # 归一化热度 >= 0.5 视为近期热门


# ---- 轻画像 ----
@dataclass
class RecProfile:
    """用户在校内的轻行为画像。available 表示证据足、可个性化。"""
    evidence: int = 0
    distinct_shops: int = 0
    cat_weights: dict = field(default_factory=dict)   # 归一化后：norm_cat -> 份额(和≈1)
    tags: set = field(default_factory=set)            # 从点赞/收藏的笔记标签中聚合
    followee_ids: set = field(default_factory=set)

    @property
    def available(self) -> bool:
        return self.evidence >= EVIDENCE_MIN and self.distinct_shops >= MIN_DISTINCT_SHOPS and bool(self.cat_weights)


# ---- 数值工具 ----
def _norm_cat(raw) -> str:
    """category 匹配口径：走规范词表（trim/lower + 别名归并，见 app.categories）。"""
    return canonicalize(raw)


def _cat_share(profile, canonical) -> float:
    """候选店分类对画像的命中份额：精确命中优先；miss 时给粗粒度族弱兜底。

    族兜底只发生在精确 0 分时，取同族其它成员的偏好和 ×0.5——不会反客为主，
    避免"只爱奶茶却被大量咖啡店顶上来"；无族或画像不可用时恒为 0。
    canonical 已由 _norm_cat 产出，画像键亦为规范值，两侧口径一致。
    """
    share = profile.cat_weights.get(canonical, 0.0)
    if share:
        return share
    members = family_of(canonical)
    if len(members) > 1:
        return 0.5 * sum(profile.cat_weights.get(c, 0.0) for c in members if c != canonical)
    return 0.0


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    union = a | b
    return len(a & b) / len(union)


def _bayes(avg, count, prior, m: int = BAYES_M) -> float:
    """贝叶斯平滑均分：样本少时向学校先验收缩，避免 5.0/1 压过 4.8/200。"""
    avg = float(avg or 0.0)
    count = int(count or 0)
    return (avg * count + prior * m) / (count + m)


def _age_days(created_at) -> float:
    """距今天数。模型 created_at 为 naive-UTC（datetime.utcnow），保持同口径避免种子反填不一致。"""
    if created_at is None:
        return 0.0
    if created_at.tzinfo is not None:
        created_at = created_at.replace(tzinfo=None)
    return max(0.0, (datetime.utcnow() - created_at).total_seconds() / 86400.0)


def _fresh(created_at, tau: float) -> float:
    """时间新鲜度：0 天→1，满 tau 天→0，线性衰减。"""
    return max(0.0, 1.0 - _age_days(created_at) / float(tau))


def _school_prior(school_id) -> float:
    """该校有评店铺的平均分作为贝叶斯先验；没有则回退 4.0。"""
    if school_id is None:
        return PRIOR_FALLBACK
    value = db.session.query(func.avg(Shop.avg_rating)).filter(
        Shop.school_id == school_id,
        Shop.is_active.is_(True),
        Shop.status == 'approved',
        Shop.rating_count > 0,
    ).scalar()
    return float(value) if value else PRIOR_FALLBACK


def _int_or_none(raw):
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _build_profile(user, school_id) -> RecProfile:
    """聚合用户在该校的轻行为画像（所有证据按 Shop.school_id 收敛）。

    计数口径：每个正向行为行 +1 evidence；其目标店铺计入 distinct 集合（去重）。
    - 收藏店铺：category 权重 +2.0
    - 好评店铺（rating>=4）：category 权重 +1.5
    - 点赞/收藏笔记：父店 category +1.0，并把笔记 tags 并入画像（同一帖点赞+收藏只计一次）
    - 关注：不在此计 evidence，仅记录 followee_ids 供 author 维度用
    """
    profile = RecProfile()
    if user is None or school_id is None:
        return profile

    seen_shop_ids = set()

    def _acc(shop: Shop, weight: float) -> None:
        """累加一个正向行为行：+1 evidence，记录店铺 id 与分类权重。"""
        if shop is None:
            return
        cat = _norm_cat(shop.category)
        if not cat:
            return
        profile.evidence += 1
        seen_shop_ids.add(shop.id)
        profile.cat_weights[cat] = profile.cat_weights.get(cat, 0.0) + weight

    def _acc_post(post: Post) -> None:
        _acc(post.shop, 1.0)
        for t in (post.tags or '').split(','):
            t = t.strip().lower()
            if t:
                profile.tags.add(t)

    # 1) 收藏的店铺
    fav_shops = (
        db.session.query(Shop)
        .join(Favorite, Favorite.shop_id == Shop.id)
        .filter(Favorite.user_id == user.id, Shop.school_id == school_id)
        .all()
    )
    for shop in fav_shops:
        _acc(shop, 2.0)

    # 2) 对该校店铺的好评（rating>=4；差评不构成正向偏好证据）
    good_reviews = (
        db.session.query(Shop)
        .join(Review, Review.shop_id == Shop.id)
        .filter(Review.user_id == user.id, Review.rating >= 4, Shop.school_id == school_id)
        .all()
    )
    for shop in good_reviews:
        _acc(shop, 1.5)

    # 3) 点赞/收藏的笔记（同帖去重）
    post_ids = {
        row.post_id
        for row in (
            db.session.query(Favorite).filter(
                Favorite.user_id == user.id, Favorite.post_id.isnot(None)
            ).all()
        )
    } | {
        row.post_id
        for row in db.session.query(Like).filter(Like.user_id == user.id).all()
    }
    if post_ids:
        posts = (
            db.session.query(Post)
            .options(joinedload(Post.shop))
            .filter(Post.id.in_(post_ids), Post.is_active.is_(True))
            .all()
        )
        # 先过滤出父店在校内的笔记（跨校店铺帖子不参与该校画像）
        for post in posts:
            if post.shop is not None and post.shop.school_id == school_id:
                _acc_post(post)

    # 4) 关注
    follows = UserFollow.query.filter_by(follower_id=user.id).all()
    profile.followee_ids = {f.followee_id for f in follows}

    profile.distinct_shops = len(seen_shop_ids)
    total = sum(profile.cat_weights.values())
    if total > 0:
        profile.cat_weights = {cat: w / total for cat, w in profile.cat_weights.items()}
    return profile


# ---- 打分入口 ----
class RecommendService:
    """首页推荐流三轨的统一打分引擎（店铺/菜品/笔记）。"""

    @staticmethod
    def shops(user, params: dict, limit: int = DEFAULT_LIMIT) -> dict:
        """店铺轨：候选 = 校内 approved+active；个性化不足时退化为改进热门榜。

        score = .45*(bayes/5) + .15*fresh + 画像可用时[.30*分类偏好 + .10*作者偏好]
        附 rec_reason；可选 lat/lng 仅在分数并列时做距离微序（不影响主导排序）。
        兼容参数：page_size / limit 均可控制返回条数（默认 6，cap 20）。
        """
        limit = _requested_limit(params, 'page_size', 'limit', limit)
        school_id = _int_or_none(params.get('school_id'))
        profile = _build_profile(user, school_id)
        prior = _school_prior(school_id)

        query = Shop.query.filter(Shop.is_active.is_(True), Shop.status == 'approved')
        if school_id:
            query = query.filter(Shop.school_id == school_id)
        # 候选池：人气预取（评分倒序）控制全量打分规模
        pool = query.order_by(Shop.avg_rating.desc(), Shop.rating_count.desc()).limit(POOL_LIMIT).all()

        lat = _float_or_none(params.get('latitude'))
        lng = _float_or_none(params.get('longitude'))

        reasons = {}
        scored = []
        for shop in pool:
            quality = _bayes(shop.avg_rating, shop.rating_count, prior) / 5.0
            fresh = _fresh(shop.created_at, TAU['shop'])
            score = W_SHOP['quality'] * quality + W_SHOP['fresh'] * fresh

            reason = []
            if quality >= _REASON_QUALITY:
                reason.append('评分口碑好')
            if _age_days(shop.created_at) <= _REASON_FRESH_DAYS['shop']:
                reason.append('新上架')

            if profile.available:
                cat_share = _cat_share(profile, _norm_cat(shop.category))
                is_followed_owner = bool(shop.owner_id and shop.owner_id in profile.followee_ids)
                score += W_SHOP['cat'] * cat_share + W_SHOP['author'] * (1.0 if is_followed_owner else 0.0)
                if cat_share > 0:
                    reason.append(f'和你喜欢的同类:{shop.category}')
                if is_followed_owner:
                    reason.append('你关注的商家经营')

            # 距离：仅作为分数并列时的稳定微序（保留旧接口的经纬度参数语义）
            dist = 0.0
            if lat is not None and lng is not None:
                if shop.latitude is None or shop.longitude is None:
                    dist = float('inf')
                else:
                    dist = _haversine_km(lat, lng, shop.latitude, shop.longitude)
            scored.append((-score, dist, -shop.id, shop, reason))

        scored.sort(key=lambda t: (t[0], t[1], t[2]))
        ranked = [shop for _, _, _, shop, _ in scored][:limit]
        reasons = {shop.id: reason for _, _, _, shop, reason in scored}

        items = _shop_list_schema.dump(ranked)
        for item in items:
            item['rec_reason'] = reasons.get(item['id']) or []
        return {'items': items, 'total': len(pool)}

    @staticmethod
    def dishes(user, params: dict, limit: int = DEFAULT_LIMIT) -> dict:
        """菜品轨：父店为 approved+active 且校内；个性化 = 父店偏好的投影。

        score = .5*(bayes/5) + .3*父店口碑 + 画像可用时[.2*标签重合度]
        诚实说明：菜品无直接互动，个性化靠“你喜欢的店的菜 + 相似标签”；dish.avg_rating 仅为种子演示值，
        非服务维护字段，故父店口碑权重高于菜品自身评分。兼容参数：limit 控制条数（默认 6，cap 20）。
        """
        limit = _requested_limit(params, 'limit', None, limit)
        school_id = _int_or_none(params.get('school_id'))
        profile = _build_profile(user, school_id)
        prior = _school_prior(school_id)

        query = (
            Dish.query.join(Shop, Dish.shop_id == Shop.id)
            .filter(
                Dish.is_active.is_(True),
                Dish.status == 'approved',
                Shop.is_active.is_(True),
                Shop.status == 'approved',
            )
        )
        if school_id:
            query = query.filter(Shop.school_id == school_id)
        pool = query.order_by(Dish.avg_rating.desc(), Dish.rating_count.desc()).limit(POOL_LIMIT).all()

        # 父店口碑一次算好复用（0..1）
        parent_quality = {
            shop.id: _bayes(shop.avg_rating, shop.rating_count, prior) / 5.0
            for shop in {d.shop for d in pool if d.shop is not None}
        }

        reasons = {}
        scored = []
        for dish in pool:
            quality = _bayes(dish.avg_rating, dish.rating_count, prior) / 5.0
            parent = parent_quality.get(dish.shop_id, PRIOR_FALLBACK / 5.0)
            score = W_DISH['quality'] * quality + W_DISH['parent'] * parent

            reason = []
            if quality >= _REASON_QUALITY:
                reason.append('菜品口碑好')
            if _age_days(dish.created_at) <= _REASON_FRESH_DAYS['dish']:
                reason.append('新上架')

            if profile.available:
                tags = {t.strip().lower() for t in (dish.tags or '').split(',') if t.strip()}
                overlap = _jaccard(tags, profile.tags)
                score += W_DISH['tags'] * overlap
                if overlap > 0:
                    reason.append('标签合你口味')
            if reason and (dish.shop is not None) and (_norm_cat(dish.shop.category) in profile.cat_weights):
                reason.append(f'来自你喜欢的店:{dish.shop.name}')

            scored.append((-score, -dish.id, dish, reason))

        scored.sort(key=lambda t: (t[0], t[1]))
        ranked = [dish for _, _, dish, _ in scored][:limit]
        reasons = {dish.id: reason for _, _, dish, reason in scored}

        items = _dish_list_schema.dump(ranked)
        for item in items:
            item['rec_reason'] = reasons.get(item['id']) or []
        return {'items': items, 'total': len(pool)}

    @staticmethod
    def rank_posts(user, params: dict):
        """笔记池混合排序，返回 (有序 Post 列表, 与之一一对应的 rec_reason 列表)。

        score = .35*(hot/max_hot) + .30*fresh + 画像可用时[.20*是否关注作者 + .15*相似度]
        其中相似度 = .5*分类偏好 + .5*标签重合。调用方（PostService）负责分页切片。
        """
        school_id = _int_or_none(params.get('school_id'))
        profile = _build_profile(user, school_id)

        query = (
            Post.query.join(Shop, Post.shop_id == Shop.id)
            .filter(
                Post.is_active.is_(True),
                Shop.is_active.is_(True),
                Shop.status == 'approved',
            )
            .options(joinedload(Post.shop), joinedload(Post.user))
        )
        if school_id:
            query = query.filter(Shop.school_id == school_id)
        pool = query.limit(POOL_LIMIT).all()

        hot_max = max((p.like_count + p.favorite_count + p.comment_count) for p in pool) if pool else 0
        hot_max = hot_max or 1

        reasons = {}
        scored = []
        for post in pool:
            total_heat = post.like_count + post.favorite_count + post.comment_count
            hot = total_heat / float(hot_max)
            fresh = _fresh(post.created_at, TAU['post'])
            score = W_POST['hot'] * hot + W_POST['fresh'] * fresh

            reason = []
            if hot >= _REASON_HOT:
                reason.append('近期热门')
            if _age_days(post.created_at) <= _REASON_FRESH_DAYS['post']:
                reason.append('刚刚发布')

            if profile.available:
                cat_share = 0.0
                if post.shop is not None:
                    cat_share = _cat_share(profile, _norm_cat(post.shop.category))
                is_followed_author = post.user_id in profile.followee_ids
                tags = {t.strip().lower() for t in (post.tags or '').split(',') if t.strip()}
                sim = 0.5 * cat_share + 0.5 * _jaccard(tags, profile.tags)
                score += W_POST['author'] * (1.0 if is_followed_author else 0.0) + W_POST['sim'] * sim

                if is_followed_author:
                    reason.append('你关注的人发布')
                if cat_share > 0:
                    reason.append('内容合你口味')

            scored.append((-score, -post.id, post, reason))

        scored.sort(key=lambda t: (t[0], t[1]))
        ranked = [post for _, _, post, _ in scored]
        reason_list = [reason for _, _, _, reason in scored]
        return ranked, reason_list


def _float_or_none(raw):
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _requested_limit(params: dict, first_key: str, second_key, default: int) -> int:
    """读取请求条数参数并夹取到 [1, 20]。"""
    for key in (first_key, second_key):
        if not key:
            continue
        raw = params.get(key)
        if raw is None:
            continue
        try:
            return min(max(int(raw), 1), 20)
        except (TypeError, ValueError):
            continue
    return max(default, 1)
