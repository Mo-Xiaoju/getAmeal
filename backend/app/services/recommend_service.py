"""推荐算法业务逻辑。

简化实现（设计文档 13 节「推荐算法复杂 → 先按时间+热度排序」）：
- 默认：当前学校内按评分/人气（avg_rating desc, rating_count desc）取 Top N。
- 可选：携带经纬度时按距离加权排序（距离近 + 评分高）。
"""
from app.models import Shop
from app.schemas.shop import ShopSchema
from app.services.shop_service import _haversine_km

_shop_list_schema = ShopSchema(many=True)
DEFAULT_LIMIT = 6


class RecommendService:
    """基于位置/口碑的店铺推荐算法。"""

    @staticmethod
    def recommend(params: dict, limit: int = DEFAULT_LIMIT) -> dict:
        query = Shop.query.filter_by(is_active=True)

        school_id = params.get('school_id')
        if school_id:
            query = query.filter(Shop.school_id == int(school_id))

        # 取热度最高的候选再按距离微调，保证候选质量
        candidates = query.order_by(Shop.avg_rating.desc(), Shop.rating_count.desc(), Shop.id.desc()).limit(limit).all()

        latitude = params.get('latitude')
        longitude = params.get('longitude')
        if latitude is not None and longitude is not None:
            def _distance(shop: Shop) -> float:
                if shop.latitude is None or shop.longitude is None:
                    return float('inf')
                return _haversine_km(float(latitude), float(longitude), shop.latitude, shop.longitude)
            candidates = sorted(candidates, key=_distance)

        return {'items': _shop_list_schema.dump(candidates), 'total': len(candidates)}
