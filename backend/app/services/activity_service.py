"""用户个人动态：浏览记录落库 + 「我的收藏 / 我的点赞 / 浏览记录」三类查看列表。

个人视角的收藏跨「店铺+笔记」、点赞只针对笔记、浏览横跨「店铺+菜品+笔记」，
统一收口在本模块，避免继续散落在 shop/post 各自的 service 里。
"""
import math
from datetime import datetime

from app.extensions import db
from app.models import Dish, Favorite, Like, Post, Shop, ViewRecord
from app.schemas.dish import DishSchema
from app.schemas.post import PostSchema
from app.schemas.shop import ShopSchema
from app.utils.exceptions import ValidationError

_shop_schema = ShopSchema()
_post_schema = PostSchema()
_dish_schema = DishSchema()

_TARGET_TYPES = {'shop', 'dish', 'post'}


def _page(items: list, params: dict) -> dict:
    """内存分页壳：返回 {items,total,page,page_size,total_pages}（与 SQL 分页一致）。"""
    try:
        page = int(params.get('page') or 1)
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = int(params.get('page_size') or 10)
    except (TypeError, ValueError):
        page_size = 10
    page = max(page, 1)
    page_size = min(max(page_size, 1), 50)
    total = len(items)
    total_pages = math.ceil(total / page_size) if total else 0
    start = (page - 1) * page_size
    return {
        'items': items[start:start + page_size],
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages,
    }


class ActivityService:
    """个人中心动态：浏览记录与我的收藏/点赞列表。"""

    # ---- 浏览记录（落库） ----
    @staticmethod
    def record_view(user, target_type: str, target_id: int) -> None:
        """记录一次详情浏览：同一 用户+目标 只留一行、刷新到最近；未登录直接忽略。"""
        if user is None:
            return
        if target_type not in _TARGET_TYPES:
            raise ValidationError(message='不支持的浏览对象类型', code=4000)
        record = ViewRecord.query.filter_by(
            user_id=user.id, target_type=target_type, target_id=target_id
        ).first()
        if record is not None:
            record.viewed_at = datetime.utcnow()
        else:
            db.session.add(ViewRecord(user_id=user.id, target_type=target_type, target_id=target_id))
        db.session.commit()

    # ---- 我的收藏（店铺 + 笔记） ----
    @staticmethod
    def list_favorites(user, params: dict) -> dict:
        """当前用户收藏列表（type=shop|post|all，默认 all；已下架/删除目标自动隐藏）。"""
        ftype = (params.get('type') or 'all').strip().lower() or 'all'
        if ftype not in ('all', 'shop', 'post'):
            raise ValidationError(message='type 仅支持 shop / post / all', code=4000)

        query = Favorite.query.filter_by(user_id=user.id)
        if ftype == 'shop':
            query = query.filter(Favorite.shop_id.isnot(None))
        elif ftype == 'post':
            query = query.filter(Favorite.post_id.isnot(None))
        rows = query.all()

        # 存活目标白名单：店铺需 上架+审核通过，笔记需未删除
        shop_ids = {r.shop_id for r in rows if r.shop_id}
        post_ids = {r.post_id for r in rows if r.post_id}
        alive_shops = set()
        if shop_ids:
            alive_shops = {sid for (sid,) in Shop.query.with_entities(Shop.id).filter(
                Shop.id.in_(shop_ids), Shop.is_active.is_(True), Shop.status == 'approved'
            ).all()}
        alive_posts = set()
        if post_ids:
            alive_posts = {pid for (pid,) in Post.query.with_entities(Post.id).filter(
                Post.id.in_(post_ids), Post.is_active.is_(True)
            ).all()}

        items = []
        for row in sorted(rows, key=lambda r: (r.created_at, r.id), reverse=True):
            if row.shop_id and row.shop_id in alive_shops:
                items.append({
                    'id': row.id, 'type': 'shop', 'created_at': row.created_at,
                    'shop': _shop_schema.dump(row.shop), 'post': None,
                })
            elif row.post_id and row.post_id in alive_posts:
                items.append({
                    'id': row.id, 'type': 'post', 'created_at': row.created_at,
                    'shop': None, 'post': _post_schema.dump(row.post),
                })
        return _page(items, params)

    # ---- 我的点赞（笔记） ----
    @staticmethod
    def list_likes(user, params: dict) -> dict:
        """当前用户点赞过的笔记列表（已删除笔记自动隐藏）。"""
        rows = Like.query.filter_by(user_id=user.id).all()
        post_ids = {r.post_id for r in rows if r.post_id}
        alive_posts = set()
        if post_ids:
            alive_posts = {pid for (pid,) in Post.query.with_entities(Post.id).filter(
                Post.id.in_(post_ids), Post.is_active.is_(True)
            ).all()}

        items = []
        for row in sorted(rows, key=lambda r: (r.created_at, r.id), reverse=True):
            if row.post_id not in alive_posts:
                continue
            items.append({
                'id': row.id, 'post_id': row.post_id, 'created_at': row.created_at,
                'post': _post_schema.dump(row.post),
            })
        return _page(items, params)

    # ---- 我的浏览记录（店铺 / 菜品 / 笔记） ----
    @staticmethod
    def list_history(user, params: dict) -> dict:
        """当前用户浏览记录（type=shop|dish|post|all，默认 all），按最近浏览倒序。"""
        htype = (params.get('type') or 'all').strip().lower() or 'all'
        if htype not in ('all', 'shop', 'dish', 'post'):
            raise ValidationError(message='type 仅支持 shop / dish / post / all', code=4000)

        query = ViewRecord.query.filter_by(user_id=user.id)
        if htype != 'all':
            query = query.filter(ViewRecord.target_type == htype)
        rows = query.all()

        shop_ids = {r.target_id for r in rows if r.target_type == 'shop'}
        dish_ids = {r.target_id for r in rows if r.target_type == 'dish'}
        post_ids = {r.target_id for r in rows if r.target_type == 'post'}

        # 存活目标对象表（仅保留 店铺上架且审核通过 / 菜品存活且归属店铺上架 / 笔记未删除）
        shop_map = {}
        if shop_ids:
            shop_map = {s.id: s for s in Shop.query.filter(
                Shop.id.in_(shop_ids), Shop.is_active.is_(True), Shop.status == 'approved'
            ).all()}
        dish_map = {}
        if dish_ids:
            dish_map = {d.id: d for d in Dish.query.join(
                Shop, Dish.shop_id == Shop.id
            ).filter(
                Dish.id.in_(dish_ids), Dish.is_active.is_(True),
                Shop.is_active.is_(True), Shop.status == 'approved',
            ).all()}
        post_map = {}
        if post_ids:
            post_map = {p.id: p for p in Post.query.filter(
                Post.id.in_(post_ids), Post.is_active.is_(True)
            ).all()}

        items = []
        for row in sorted(rows, key=lambda r: (r.viewed_at, r.id), reverse=True):
            if row.target_type == 'shop':
                target = shop_map.get(row.target_id)
                if target is None:
                    continue
                items.append({
                    'id': row.id, 'target_type': 'shop', 'target_id': row.target_id,
                    'viewed_at': row.viewed_at, 'shop': _shop_schema.dump(target),
                    'dish': None, 'post': None,
                })
            elif row.target_type == 'dish':
                target = dish_map.get(row.target_id)
                if target is None:
                    continue
                items.append({
                    'id': row.id, 'target_type': 'dish', 'target_id': row.target_id,
                    'viewed_at': row.viewed_at, 'shop': None,
                    'dish': _dish_schema.dump(target), 'post': None,
                })
            else:
                target = post_map.get(row.target_id)
                if target is None:
                    continue
                items.append({
                    'id': row.id, 'target_type': 'post', 'target_id': row.target_id,
                    'viewed_at': row.viewed_at, 'shop': None,
                    'dish': None, 'post': _post_schema.dump(target),
                })
        return _page(items, params)
