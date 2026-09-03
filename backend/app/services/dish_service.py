"""菜品业务逻辑。"""
from app.models import Dish, Shop
from app.schemas.dish import DishSchema
from app.utils.exceptions import NotFoundError
from app.utils.pagination import paginate

_dish_schema = DishSchema()
_dish_list_schema = DishSchema(many=True)


def _get_active_dish(dish_id: int) -> Dish:
    dish = Dish.query.get(dish_id)
    if dish is None or not dish.is_active:
        raise NotFoundError(message='菜品不存在', code=4043)
    return dish


def _get_active_shop(shop_id: int) -> Shop:
    shop = Shop.query.get(shop_id)
    if shop is None or not shop.is_active:
        raise NotFoundError(message='店铺不存在', code=4040)
    return shop


class DishService:
    """菜品查询、推荐等业务。"""

    # ---- 列表与详情 ----
    @staticmethod
    def list_by_shop(shop_id: int, params: dict) -> dict:
        """店铺下的在售菜品（分页，按上架顺序）。"""
        _get_active_shop(shop_id)
        query = Dish.query.filter_by(shop_id=shop_id, is_active=True).order_by(Dish.id.asc())
        page = int(params.get('page') or 1)
        page_size = int(params.get('page_size') or 20)
        result = paginate(query, page, page_size)
        return {**result, 'items': _dish_list_schema.dump(result['items'])}

    @staticmethod
    def list(params: dict) -> dict:
        """菜品列表：支持 school_id / shop_id 过滤，按评分/人气排序 + 分页。"""
        query = Dish.query.join(Shop).filter(Dish.is_active.is_(True), Shop.is_active.is_(True))
        school_id = params.get('school_id')
        if school_id:
            query = query.filter(Shop.school_id == int(school_id))
        shop_id = params.get('shop_id')
        if shop_id:
            query = query.filter(Dish.shop_id == int(shop_id))
        query = query.order_by(Dish.avg_rating.desc(), Dish.rating_count.desc(), Dish.id.desc())
        page = int(params.get('page') or 1)
        page_size = int(params.get('page_size') or 20)
        result = paginate(query, page, page_size)
        return {**result, 'items': _dish_list_schema.dump(result['items'])}

    @staticmethod
    def get_detail(dish_id: int) -> dict:
        """菜品详情。"""
        return _dish_schema.dump(_get_active_dish(dish_id))
