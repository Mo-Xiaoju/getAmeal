"""商户中心业务逻辑：商户管理自己的店铺与菜单（仅限本人的店铺/菜品）。"""
from sqlalchemy import and_, or_

from app.categories import normalize_category_payload
from app.extensions import db
from app.models import Dish, Shop, User
from app.schemas.dish import DishCreateSchema, DishSchema, DishUpdateSchema
from app.services.dish_service import apply_dish_images_for_create, sync_dish_images
from app.services.event_log_service import EventLogService
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
    def list_claimable(user, params: dict) -> dict:
        """列出当前商户可认领的店铺：已公开（approved、未下架）且尚未被商户认领。

        认领范围：owner 为空（管理员种子店）或 owner 非商户角色（学生代提交）的店铺；
        本人名下的店铺天然不在列。可用 school_id 限定当前学校。
        """
        query = (
            Shop.query.outerjoin(User, User.id == Shop.owner_id)
            .filter(
                Shop.is_active.is_(True),
                Shop.status == 'approved',
                # owner 为空（管理员种子店）可认领；owner 非本人且非商户角色的社区店可认领。
                # 注意 SQL 中 owner_id != user 对 NULL 不成立，须显式放行 owner_id IS NULL。
                or_(
                    Shop.owner_id.is_(None),
                    and_(Shop.owner_id != user.id, User.role != 'merchant'),
                ),
            )
            .order_by(Shop.id.desc())
        )
        school_id = params.get('school_id')
        if school_id:
            try:
                query = query.filter(Shop.school_id == int(school_id))
            except (TypeError, ValueError):
                pass  # 非法 school_id 视为不限定
        page = int(params.get('page') or 1)
        page_size = int(params.get('page_size') or 10)
        result = paginate(query, page, page_size)
        items = [_serialize_shop(s, with_dish_count=True) for s in result['items']]
        return {**result, 'items': items}

    @staticmethod
    def claim_shop(user, shop_id: int) -> dict:
        """认领一家未入驻店铺到自己名下，认领后可在商户中心管理其菜单。

        仅限已公开（approved）且未被商户认领的店；认领即刻生效（店铺本就对公开放映）。
        """
        shop = db.session.get(Shop, shop_id)
        if shop is None or not shop.is_active:
            raise NotFoundError(message='店铺不存在', code=4040)
        if shop.status != 'approved':
            raise ValidationError(message='仅可认领已公开（审核通过）的店铺', code=4000)
        if shop.owner_id == user.id:
            raise ValidationError(message='该店铺已是你的店铺，无需认领', code=4000)
        owner = shop.owner
        if owner is not None and owner.role == 'merchant':
            raise ValidationError(message='该店铺已有商户入驻，无需认领', code=4000)
        shop.owner_id = user.id
        db.session.commit()
        return _serialize_shop(shop, with_dish_count=True)

    @staticmethod
    def create_shop(user, data: dict) -> dict:
        """新增店铺（商户创建即 approved，无需审核）。"""
        data = ShopCreateSchema().load(data)
        data = normalize_category_payload(data)
        _validate_unique_shop_name(data['name'])
        shop = Shop(**data, owner_id=user.id, status='approved')
        db.session.add(shop)
        try:
            db.session.flush()  # 拿到 shop.id 供埋点
            EventLogService.record(user, 'shop_submit', target_type='shop', target_id=shop.id,
                                   school_id=shop.school_id,
                                   extra={'name': shop.name, 'category': shop.category})
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
        data = normalize_category_payload(data)
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
        shop = _get_owned_shop(user, shop_id)
        data = DishCreateSchema().load(data)
        apply_dish_images_for_create(data)
        tags = ','.join(t.strip() for t in data.pop('tags') or [] if t and t.strip())
        dish = Dish(shop_id=shop_id, owner_id=user.id, status='approved', tags=tags or None, **data)
        db.session.add(dish)
        db.session.flush()  # 拿到 dish.id 供埋点
        EventLogService.record(user, 'dish_submit', target_type='dish', target_id=dish.id,
                               school_id=shop.school_id, extra={'name': dish.name})
        db.session.commit()
        return _dish_schema.dump(dish)

    @staticmethod
    def update_dish(user, dish_id: int, data: dict) -> dict:
        """修改自己店铺下的菜品（商户本人维护的内容直接发布，无需再审核）。"""
        dish = _get_owned_dish(user, dish_id)
        data = DishUpdateSchema().load(data)
        # 图集单独处理（含封面），摘出后其余字段照旧走通用循环
        sync_dish_images(dish, data)
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
