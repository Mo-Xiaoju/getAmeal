"""菜品业务逻辑。"""
import json

from app.models import Dish, Shop
from app.schemas.dish import DishSchema
from app.utils.exceptions import NotFoundError
from app.utils.pagination import paginate

_dish_schema = DishSchema()
_dish_list_schema = DishSchema(many=True)


# ---- 菜品图集（images JSON 列权威，image_url 保留为封面兼容）----

def dish_image_list(dish: Dish) -> list:
    """当前菜品的完整图列表：解析 images JSON；历史行（仅 image_url）回退单图。"""
    try:
        imgs = json.loads(dish.images) if dish.images else None
    except (TypeError, ValueError):
        imgs = None
    if isinstance(imgs, list) and imgs:
        return imgs
    return [dish.image_url] if dish.image_url else []


def image_urls_from_payload(data: dict):
    """从 schema 解析后的请求数据提取最终图片 URL 列表。
    images(list) 优先（显式 [] = 清空）；否则兼容 image_url 单图（空串清空）。
    返回 (是否涉及图片, 归一后的 url 列表)。"""
    images = data.get('images')
    if isinstance(images, list):
        return True, [u.strip() for u in images if u and u.strip()]
    image_url = data.get('image_url')
    if image_url is not None:
        u = (image_url or '').strip()
        return True, [u] if u else []
    return False, []


def apply_dish_images_for_create(data: dict) -> None:
    """创建菜品前，把请求里的图片字段归一成入库形态（就地改 data）。"""
    handled, urls = image_urls_from_payload(data)
    if not handled:
        return
    data['images'] = json.dumps(urls, ensure_ascii=False) if urls else None
    data['image_url'] = urls[0] if urls else None


def sync_dish_images(dish: Dish, data: dict) -> bool:
    """更新菜品时同步图集（images 权威 + 封面 image_url）。
    把请求里的 images/image_url 摘出处理，避免进入通用 setattr 循环（None 会被跳过而清不掉）；
    与现有图列表不同才落库。返回是否发生了图片变更。"""
    handled, urls = image_urls_from_payload(data)
    if not handled:
        return False
    data.pop('images', None)
    data.pop('image_url', None)
    if urls == dish_image_list(dish):
        return False
    dish.images = json.dumps(urls, ensure_ascii=False) if urls else None
    dish.image_url = urls[0] if urls else None
    return True


def _get_active_dish(dish_id: int) -> Dish:
    """对外菜品详情：菜品在售且所属店铺 approved+上架，才对外可见。"""
    dish = Dish.query.get(dish_id)
    if dish is None or not dish.is_active:
        raise NotFoundError(message='菜品不存在', code=4043)
    if dish.shop is None or not dish.shop.is_active or dish.shop.status != 'approved':
        raise NotFoundError(message='菜品不存在', code=4043)
    return dish


def _get_active_shop(shop_id: int) -> Shop:
    """对外某店铺的菜品列表：仅 approved+上架的店铺（pending/rejected 不公示）。"""
    shop = Shop.query.get(shop_id)
    if shop is None or not shop.is_active or shop.status != 'approved':
        raise NotFoundError(message='店铺不存在', code=4040)
    return shop


class DishService:
    """菜品查询、推荐等业务。"""

    # ---- 列表与详情 ----
    @staticmethod
    def list_by_shop(shop_id: int, params: dict) -> dict:
        """店铺下的在售菜品（分页，按上架顺序）。仅对外展示 approved 菜品。"""
        _get_active_shop(shop_id)
        query = Dish.query.filter_by(shop_id=shop_id, is_active=True, status='approved').order_by(Dish.id.asc())
        page = int(params.get('page') or 1)
        page_size = int(params.get('page_size') or 20)
        result = paginate(query, page, page_size)
        return {**result, 'items': _dish_list_schema.dump(result['items'])}

    @staticmethod
    def list(params: dict) -> dict:
        """菜品列表：支持 school_id / shop_id 过滤，按评分/人气排序 + 分页。
        仅展示 approved 菜品，且所属店铺 approved+上架（pending/rejected 不对外公示）。"""
        query = Dish.query.join(Shop).filter(
            Dish.is_active.is_(True),
            Dish.status == 'approved',
            Shop.is_active.is_(True),
            Shop.status == 'approved',
        )
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
