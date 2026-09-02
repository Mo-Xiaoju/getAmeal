"""学生提交商户/菜单业务逻辑。

商户尚未入驻平台时，学生可代为提交店铺与菜单，提交内容标记为 status=pending。
TODO(审核机制)：待实现管理员审核队列——按 pending 审核后置为 approved/rejected；
当前 pending 内容对 C 端可见可用，审核流程落地后再按需过滤 / 放行。
"""
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


def _get_owned_dish(user, dish_id: int) -> Dish:
    """获取本人店铺下的菜品（校验归属）。"""
    dish = db.session.get(Dish, dish_id)
    if dish is None or not dish.is_active:
        raise NotFoundError(message='菜品不存在', code=4046)
    if dish.shop is None or dish.shop.owner_id != user.id:
        raise PermissionError(message='无权操作该菜品', code=4032)
    return dish


def _validate_unique_shop_name(name: str) -> None:
    """店铺名全局唯一，重名直接提示改为关联已有店铺。"""
    name = name.strip()
    if not name:
        raise ValidationError(message='店铺名不能为空', code=4000)
    if Shop.query.filter_by(name=name).first() is not None:
        raise ValidationError(message=f'店铺「{name}」已存在，请直接选择关联该店铺', code=4006)


class ContributeService:
    """学生提交商户/菜单业务。"""

    @staticmethod
    def list_my(user, params: dict) -> dict:
        """我的提交：本人创建的店铺（含其菜品列表）。"""
        query = Shop.query.filter_by(owner_id=user.id).order_by(Shop.id.desc())
        page = int(params.get('page') or 1)
        page_size = int(params.get('page_size') or 10)
        total = query.count()
        shops = query.offset((page - 1) * page_size).limit(page_size).all()
        total_pages = (total + page_size - 1) // page_size if total else 0
        items = []
        for shop in shops:
            item = _shop_schema.dump(shop)
            item['dishes'] = _dish_list_schema.dump(
                Dish.query.filter_by(shop_id=shop.id, is_active=True).order_by(Dish.id.asc()).all()
            )
            items.append(item)
        return {'items': items, 'total': total, 'page': page, 'page_size': page_size, 'total_pages': total_pages}

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
        """修改本人提交的店铺。"""
        shop = _get_owned_shop(user, shop_id)
        data = ShopUpdateSchema().load(data)
        for key, value in data.items():
            if value is not None:
                setattr(shop, key, value)
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
        """给本人提交的店铺添加菜单（status=pending，待审核）。"""
        _get_owned_shop(user, shop_id)
        data = DishCreateSchema().load(data)
        tags = ','.join(t.strip() for t in data.pop('tags') or [] if t and t.strip())
        dish = Dish(shop_id=shop_id, status='pending', tags=tags or None, **data)
        db.session.add(dish)
        db.session.commit()
        return _dish_schema.dump(dish)

    @staticmethod
    def update_dish(user, dish_id: int, data: dict) -> dict:
        """修改本人提交的菜单。"""
        dish = _get_owned_dish(user, dish_id)
        data = DishUpdateSchema().load(data)
        for key, value in data.items():
            if value is None:
                continue
            if key == 'tags':
                value = ','.join(t.strip() for t in value if t.strip()) or None
            setattr(dish, key, value)
        db.session.commit()
        return _dish_schema.dump(dish)

    @staticmethod
    def delete_dish(user, dish_id: int) -> None:
        """删除本人提交的菜单（软删除）。"""
        dish = _get_owned_dish(user, dish_id)
        dish.is_active = False
        db.session.commit()
