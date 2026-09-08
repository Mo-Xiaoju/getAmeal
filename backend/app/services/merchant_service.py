"""商户中心业务逻辑：商户管理自己的店铺与菜单（仅限本人的店铺/菜品）。"""
from app.extensions import db
from app.models import Dish, Shop
from app.schemas.dish import DishCreateSchema, DishSchema, DishUpdateSchema
from app.schemas.shop import ShopCreateSchema, ShopSchema, ShopUpdateSchema
from app.utils.exceptions import ApiError, NotFoundError, PermissionError, ValidationError
from app.utils.pagination import paginate

_shop_schema = ShopSchema()
_shop_list_schema = ShopSchema(many=True)
_dish_schema = DishSchema()
_dish_list_schema = DishSchema(many=True)


def _get_owned_shop(user, shop_id: int) -> Shop:
    """获取当前商户自己的店铺（不存在 / 非本人 → 报错）。"""
    shop = db.session.get(Shop, shop_id)
    if shop is None or not shop.is_active:
        raise NotFoundError(message='店铺不存在', code=4040)
    if shop.owner_id != user.id:
        raise PermissionError(message='无权操作该店铺', code=4032)
    return shop


def _get_owned_dish(user, dish_id: int) -> Dish:
    """获取当前商户自己店铺下的菜品（校验归属）。"""
    dish = db.session.get(Dish, dish_id)
    if dish is None or not dish.is_active:
        raise NotFoundError(message='菜品不存在', code=4046)
    if dish.shop is None or dish.shop.owner_id != user.id:
        raise PermissionError(message='无权操作该菜品', code=4032)
    return dish


def _validate_unique_shop_name(name: str) -> None:
    """店铺名全局唯一（含已软删），重名直接友好报错。"""
    name = name.strip()
    if not name:
        raise ValidationError(message='店铺名不能为空', code=4000)
    if Shop.query.filter_by(name=name).first() is not None:
        raise ValidationError(message=f'店铺「{name}」已存在，请勿重复创建', code=4006)


def _self_publish(obj) -> None:
    """商户本人维护的内容直接发布：若历史记录卡在待审/驳回（如学生晋升商户后），
    编辑时顺带置 approved 并清空审核痕迹，避免永远无人审核。"""
    if obj.status in ('pending', 'rejected'):
        obj.status = 'approved'
        obj.reject_reason = None
        obj.reviewed_by = None
        obj.reviewed_at = None


def _serialize_shop(shop: Shop, with_dish_count: bool = False) -> dict:
    item = _shop_schema.dump(shop)
    if with_dish_count:
        item['dish_count'] = Dish.query.filter_by(shop_id=shop.id, is_active=True).count()
    return item


class MerchantService:
    """商户业务：店铺 + 菜品管理（仅限本人）。"""

    # ---- 店铺 ----
    @staticmethod
    def list_my_shops(user, params: dict) -> dict:
        """我的店铺列表（含菜品数）。"""
        query = Shop.query.filter_by(owner_id=user.id).order_by(Shop.id.desc())
        page = int(params.get('page') or 1)
        page_size = int(params.get('page_size') or 10)
        result = paginate(query, page, page_size)
        items = [_serialize_shop(s, with_dish_count=True) for s in result['items']]
        return {**result, 'items': items}

    @staticmethod
    def create_shop(user, data: dict) -> dict:
        """新增店铺（商户创建即 approved，无需审核）。"""
        data = ShopCreateSchema().load(data)
        _validate_unique_shop_name(data['name'])
        shop = Shop(**data, owner_id=user.id, status='approved')
        db.session.add(shop)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise ApiError(message='店铺创建失败，请重试', code=4002)
        return _serialize_shop(shop)

    @staticmethod
    def update_shop(user, shop_id: int, data: dict) -> dict:
        """修改自己的店铺信息（商户本人维护的内容直接发布，无需再审核）。"""
        shop = _get_owned_shop(user, shop_id)
        data = ShopUpdateSchema().load(data)
        for key, value in data.items():
            if value is not None:
                setattr(shop, key, value)
        _self_publish(shop)  # 历史待审/驳回记录经商户编辑即通过
        db.session.commit()
        return _serialize_shop(shop)

    @staticmethod
    def delete_shop(user, shop_id: int) -> None:
        """删除自己的店铺（软删除）。"""
        shop = _get_owned_shop(user, shop_id)
        shop.is_active = False
        db.session.commit()

    # ---- 菜单（菜品）----
    @staticmethod
    def list_my_dishes(user, shop_id: int, params: dict) -> dict:
        """某店铺的菜品列表（分页）。"""
        _get_owned_shop(user, shop_id)
        query = Dish.query.filter_by(shop_id=shop_id).order_by(Dish.id.desc())
        page = int(params.get('page') or 1)
        page_size = int(params.get('page_size') or 10)
        result = paginate(query, page, page_size)
        return {**result, 'items': _dish_list_schema.dump(result['items'])}

    @staticmethod
    def create_dish(user, shop_id: int, data: dict) -> dict:
        """给自己的店铺添加菜品（创建即 approved，归属商户本人）。"""
        _get_owned_shop(user, shop_id)
        data = DishCreateSchema().load(data)
        tags = ','.join(t.strip() for t in data.pop('tags') or [] if t and t.strip())
        dish = Dish(shop_id=shop_id, owner_id=user.id, status='approved', tags=tags or None, **data)
        db.session.add(dish)
        db.session.commit()
        return _dish_schema.dump(dish)

    @staticmethod
    def update_dish(user, dish_id: int, data: dict) -> dict:
        """修改自己店铺下的菜品（商户本人维护的内容直接发布，无需再审核）。"""
        dish = _get_owned_dish(user, dish_id)
        data = DishUpdateSchema().load(data)
        for key, value in data.items():
            if value is None:
                continue
            if key == 'tags':
                value = ','.join(t.strip() for t in value if t.strip()) or None
            setattr(dish, key, value)
        _self_publish(dish)
        db.session.commit()
        return _dish_schema.dump(dish)

    @staticmethod
    def delete_dish(user, dish_id: int) -> None:
        """删除自己店铺下的菜品（软删除）。"""
        dish = _get_owned_dish(user, dish_id)
        dish.is_active = False
        db.session.commit()
