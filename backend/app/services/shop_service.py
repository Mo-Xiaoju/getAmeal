"""店铺与评价业务逻辑。"""
import json
import math

from app.categories import canonicalize
from app.extensions import db
from app.models import Favorite, Review, Shop
from app.schemas.shop import ReviewSchema, ShopDetailSchema, ShopSchema
from app.utils.exceptions import NotFoundError, PermissionError, ValidationError
from app.utils.pagination import paginate

_shop_schema = ShopSchema()
_shop_list_schema = ShopSchema(many=True)
_shop_detail_schema = ShopDetailSchema()
_review_schema = ReviewSchema()
_review_list_schema = ReviewSchema(many=True)

_EARTH_RADIUS_KM = 6371.0


def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    """两点球面距离（公里）。"""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return _EARTH_RADIUS_KM * 2 * math.asin(math.sqrt(a))


def _get_active_shop(shop_id: int) -> Shop:
    """对外只放行 approved 且上架的店铺；pending/rejected 仅 owner 走商户中心可见。"""
    shop = Shop.query.get(shop_id)
    if shop is None or not shop.is_active or shop.status != 'approved':
        raise NotFoundError(message='店铺不存在', code=4040)
    return shop


class ShopService:
    """店铺查询、筛选、评价、收藏等业务。"""

    # ---- 列表与详情 ----
    @staticmethod
    def list_shops(params: dict) -> dict:
        """店铺列表：school_id / keyword / category 筛选 + 排序 + 分页。"""
        query = Shop.query.filter_by(is_active=True, status='approved')

        school_id = params.get('school_id')
        if school_id:
            query = query.filter(Shop.school_id == int(school_id))

        keyword = (params.get('keyword') or '').strip()
        if keyword:
            query = query.filter(Shop.name.like(f'%{keyword}%'))

        category = canonicalize(params.get('category'))
        if category:
            query = query.filter(Shop.category == category)

        sort = params.get('sort')
        if sort == 'newest':
            query = query.order_by(Shop.created_at.desc(), Shop.id.desc())
        else:  # 默认按评分
            query = query.order_by(Shop.avg_rating.desc(), Shop.rating_count.desc(), Shop.id.desc())

        page = int(params.get('page') or 1)
        page_size = int(params.get('page_size') or 10)
        result = paginate(query, page, page_size)
        return {**result, 'items': _shop_list_schema.dump(result['items'])}

    @staticmethod
    def get_detail(shop_id: int) -> dict:
        """店铺详情。"""
        return _shop_detail_schema.dump(_get_active_shop(shop_id))

    # ---- 评价 ----
    @staticmethod
    def list_reviews(shop_id: int, params: dict) -> dict:
        """店铺评价列表（分页，按时间倒序）。"""
        _get_active_shop(shop_id)
        query = Review.query.filter_by(shop_id=shop_id).order_by(Review.created_at.desc(), Review.id.desc())
        page = int(params.get('page') or 1)
        page_size = int(params.get('page_size') or 10)
        result = paginate(query, page, page_size)
        return {**result, 'items': _review_list_schema.dump(result['items'])}

    @staticmethod
    def add_review(user, shop_id: int, data: dict) -> dict:
        """发表评价，并更新店铺平均分。"""
        shop = _get_active_shop(shop_id)
        rating = int(data.get('rating') or 0)
        if rating < 1 or rating > 5:
            raise ValidationError(message='评分需在 1-5 之间', code=4000)

        review = Review(
            user_id=user.id,
            shop_id=shop.id,
            rating=rating,
            content=(data.get('content') or '').strip() or None,
            images=json.dumps(data.get('images') or [], ensure_ascii=False),
        )
        # 增量更新店铺平均分（保留浮点全精度，dump 时再四舍五入，避免反复加减漂移）
        shop.rating_count += 1
        shop.avg_rating = (shop.avg_rating * (shop.rating_count - 1) + rating) / shop.rating_count
        db.session.add(review)
        db.session.commit()
        return _review_schema.dump(review)

    @staticmethod
    def delete_review(user, review_id: int) -> None:
        """删除自己的某条评价（含店铺均分回退）。"""
        review = Review.query.get(review_id)
        if review is None:
            raise NotFoundError(message='评价不存在', code=4042)
        if review.user_id != user.id and user.role != 'admin':
            raise PermissionError(message='无权删除该评价', code=4030)

        # 回退平均分（对增量加分的逆向，保留浮点全精度）
        shop = review.shop
        if shop is not None and shop.rating_count > 1:
            shop.rating_count -= 1
            shop.avg_rating = (shop.avg_rating * (shop.rating_count + 1) - review.rating) / shop.rating_count
        elif shop is not None:
            shop.rating_count = 0
            shop.avg_rating = 0.0
        db.session.delete(review)
        db.session.commit()

    # ---- 收藏 ----
    @staticmethod
    def toggle_favorite(user, shop_id: int) -> dict:
        """收藏/取消收藏（幂等），返回当前是否已收藏。"""
        _get_active_shop(shop_id)
        favorite = Favorite.query.filter_by(user_id=user.id, shop_id=shop_id).first()
        if favorite:
            db.session.delete(favorite)
            db.session.commit()
            return {'favorited': False}
        db.session.add(Favorite(user_id=user.id, shop_id=shop_id))
        db.session.commit()
        return {'favorited': True}

    @staticmethod
    def is_favorited(user, shop_id: int) -> bool:
        """是否已收藏（详情页回显用）。"""
        return Favorite.query.filter_by(user_id=user.id, shop_id=shop_id).first() is not None

    # ---- 我的评价 ----
    @staticmethod
    def list_my_reviews(user, params: dict) -> dict:
        """当前用户评价列表（分页，含店铺信息）。"""
        query = Review.query.filter_by(user_id=user.id).order_by(Review.created_at.desc(), Review.id.desc())
        page = int(params.get('page') or 1)
        page_size = int(params.get('page_size') or 10)
        result = paginate(query, page, page_size)
        items = [
            {**_review_schema.dump(rv), 'shop': _shop_schema.dump(rv.shop) if rv.shop else None}
            for rv in result['items']
        ]
        return {**result, 'items': items}
