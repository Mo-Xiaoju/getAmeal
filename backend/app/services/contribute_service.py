"""学生代维护商户/菜单业务逻辑。

针对未入驻平台的商户，学生可提交店铺与菜品，内容标记 status=pending，经管理员
审核后对外开放展示。审核通过的店/菜再次编辑会回到 pending 重新审核。
社区共建：任何学生都能向「未被商户认领且已公开」的店铺补充菜品（仍待审），
菜品归属提交者本人；店铺信息仅其提交者本人可维护。
"""
from sqlalchemy import or_

from app.extensions import db
from app.models import Dish, Shop
from app.schemas.dish import DishCreateSchema, DishSchema, DishUpdateSchema
from app.schemas.shop import ShopCreateSchema, ShopSchema, ShopUpdateSchema
from app.utils.exceptions import ApiError, NotFoundError, PermissionError, ValidationError

_shop_schema = ShopSchema()
_dish_schema = DishSchema()
_dish_list_schema = DishSchema(many=True)


def _get_owned_shop(user, shop_id: int) -> Shop:
    """获取本人提交的店铺（不存在 / 非本人 → 报错）。"""
    shop = db.session.get(Shop, shop_id)
    if shop is None or not shop.is_active:
        raise NotFoundError(message='店铺不存在', code=4040)
    if shop.owner_id != user.id:
        raise PermissionError(message='无权操作该店铺', code=4032)
    return shop


def _get_mutable_dish(user, dish_id: int) -> Dish:
    """获取本人可维护的菜品：菜品提交者本人，或其所属店铺的提交者本人。"""
    dish = db.session.get(Dish, dish_id)
    if dish is None or not dish.is_active:
        raise NotFoundError(message='菜品不存在', code=4046)
    mine_dish = dish.owner_id == user.id
    mine_shop = dish.shop is not None and dish.shop.owner_id == user.id
    if not (mine_dish or mine_shop):
        raise PermissionError(message='无权操作该菜品', code=4032)
    return dish


def _get_contribute_target_shop(user, shop_id: int) -> Shop:
    """加菜的目标店铺：本人提交的店（任意状态），或已公开且未被商户认领的社区店。"""
    shop = db.session.get(Shop, shop_id)
    if shop is None or not shop.is_active:
        raise NotFoundError(message='店铺不存在', code=4040)
    if shop.owner_id == user.id:
        return shop
    # 未被商户认领：owner 为空（管理员种子店）或 owner 非商户角色
    owner = shop.owner
    community = shop.owner_id is None or (owner is not None and owner.role != 'merchant')
    if shop.status == 'approved' and community:
        return shop
    raise PermissionError(
        message='仅可向自己提交的店铺，或已公开且未被商户认领的店铺补充菜品', code=4032
    )


def _reset_audit(obj) -> None:
    """提交者编辑后回到待审核：置 pending 并清空历史审核记录。"""
    obj.status = 'pending'
    obj.reject_reason = None
    obj.reviewed_by = None
    obj.reviewed_at = None


def _validate_unique_shop_name(name: str, exclude_id: int = None) -> None:
    """店铺名全局唯一，重名提示关联已有店铺（改名时排除自身）。"""
    name = name.strip()
    if not name:
        raise ValidationError(message='店铺名不能为空', code=4000)
    query = Shop.query.filter_by(name=name)
    if exclude_id is not None:
        query = query.filter(Shop.id != exclude_id)
    if query.first() is not None:
        raise ValidationError(message=f'店铺「{name}」已存在，请直接选择关联该店铺', code=4006)


class ContributeService:
    """学生代维护商户/菜单业务。"""

    @staticmethod
    def list_my(user, params: dict) -> dict:
        """我的提交：
        - items：本人提交的店铺（含其菜品列表）
        - contributed_dishes：我在其他学生/管理员店铺下补充的菜品
        """
        page = int(params.get('page') or 1)
        page_size = int(params.get('page_size') or 10)
        offset = (page - 1) * page_size

        # 1) 本人提交的店铺 + 内嵌菜品
        shop_query = Shop.query.filter_by(owner_id=user.id).order_by(Shop.id.desc())
        shop_total = shop_query.count()
        shops = shop_query.offset(offset).limit(page_size).all()
        items = []
        for shop in shops:
            item = _shop_schema.dump(shop)
            item['dishes'] = _dish_list_schema.dump(
                Dish.query.filter_by(shop_id=shop.id, is_active=True).order_by(Dish.id.asc()).all()
            )
            items.append(item)
        total_pages = (shop_total + page_size - 1) // page_size if shop_total else 0

        # 2) 我在他人店铺提交的菜品（含 NULL owner 的管理员种子店）
        dish_query = (
            Dish.query.join(Shop)
            .filter(
                Dish.owner_id == user.id,
                Dish.is_active.is_(True),
                or_(Shop.owner_id.is_(None), Shop.owner_id != user.id),
            )
            .order_by(Dish.id.desc())
        )
        dish_total = dish_query.count()
        contributed = []
        for dish in dish_query.offset(offset).limit(page_size).all():
            item = _dish_schema.dump(dish)
            item['shop_status'] = dish.shop.status if dish.shop else None  # 店铺重新审核中提示
            contributed.append(item)

        return {
            'items': items,
            'total': shop_total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
            'contributed_dishes': contributed,
            'dish_total': dish_total,
        }

    @staticmethod
    def create_shop(user, data: dict) -> dict:
        """提交新店铺（status=pending，待审核）。"""
        data = ShopCreateSchema().load(data)
        _validate_unique_shop_name(data['name'])
        shop = Shop(**data, owner_id=user.id, status='pending')
        db.session.add(shop)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise ApiError(message='提交失败，请重试', code=4002)
        return _shop_schema.dump(shop)

    @staticmethod
    def update_shop(user, shop_id: int, data: dict) -> dict:
        """修改本人提交的店铺：编辑后回到待审核（approved 亦重新审核）。"""
        shop = _get_owned_shop(user, shop_id)
        data = ShopUpdateSchema().load(data)
        name = data.get('name')
        if name is not None:
            name = name.strip()
            if not name:
                raise ValidationError(message='店铺名不能为空', code=4000)
            _validate_unique_shop_name(name, exclude_id=shop.id)
            data['name'] = name
        changed = False
        for key, value in data.items():
            if value is None:
                continue
            if key == 'image_url' and value == '':
                value = None  # 清空封面（空串与 None 等价，避免误判为变更触发重审）
            if getattr(shop, key, None) == value:
                continue
            setattr(shop, key, value)
            changed = True
        if changed:
            _reset_audit(shop)
        db.session.commit()
        return _shop_schema.dump(shop)

    @staticmethod
    def delete_shop(user, shop_id: int) -> None:
        """删除本人提交的店铺（软删除）。"""
        shop = _get_owned_shop(user, shop_id)
        shop.is_active = False
        db.session.commit()

    @staticmethod
    def add_dish(user, shop_id: int, data: dict) -> dict:
        """给店铺补充菜品（status=pending，待审核）。
        放行范围：本人提交的店，或已公开且未被商户认领的社区店。
        """
        shop = _get_contribute_target_shop(user, shop_id)
        data = DishCreateSchema().load(data)
        tags = ','.join(t.strip() for t in data.pop('tags') or [] if t and t.strip())
        dish = Dish(shop_id=shop.id, owner_id=user.id, status='pending', tags=tags or None, **data)
        db.session.add(dish)
        db.session.commit()
        return _dish_schema.dump(dish)

    @staticmethod
    def update_dish(user, dish_id: int, data: dict) -> dict:
        """修改本人可维护的菜品：编辑后回到待审核。"""
        dish = _get_mutable_dish(user, dish_id)
        data = DishUpdateSchema().load(data)
        changed = False
        for key, value in data.items():
            if value is None:
                continue
            if key == 'tags':
                value = ','.join(t.strip() for t in value if t.strip()) or None
            if key == 'image_url' and value == '':
                value = None  # 清空菜品图（空串与 None 等价，避免误判触发重审）
            if getattr(dish, key, None) == value:
                continue
            setattr(dish, key, value)
            changed = True
        if changed:
            _reset_audit(dish)
        db.session.commit()
        return _dish_schema.dump(dish)

    @staticmethod
    def delete_dish(user, dish_id: int) -> None:
        """删除本人可维护的菜品（软删除）。"""
        dish = _get_mutable_dish(user, dish_id)
        dish.is_active = False
        db.session.commit()
