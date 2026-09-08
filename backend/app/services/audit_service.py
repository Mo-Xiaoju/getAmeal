"""管理端审核业务：学生提交的店铺/菜品 通过 / 驳回。

队列划分：
- 店铺队列（list_shops）：待审/已审的店铺（默认 pending），含该店仍 pending 的菜品，
  支持「整店通过/驳回」把店铺与这些菜品一并处理；
- 菜品队列（list_dishes）：父店已 approved 的待审/已审菜品，供逐条单独审核。
"""
from datetime import datetime

from app.extensions import db
from app.models import Dish, Shop
from app.schemas.dish import DishSchema
from app.schemas.shop import ShopSchema
from app.utils.exceptions import NotFoundError, ValidationError
from app.utils.pagination import paginate

VALID_STATUS = ('approved', 'pending', 'rejected')
VALID_ACTIONS = ('approve', 'reject')

_shop_schema = ShopSchema()
_dish_schema = DishSchema()


def _submitter(user) -> dict:
    """提交者简要信息（昵称/登录名/学校）。"""
    if user is None:
        return None
    return {
        'id': user.id,
        'nickname': user.nickname,
        'username': user.username,
        'school_name': user.school.name if user.school else None,
    }


def _parse_status(params: dict, default: str = 'pending') -> str:
    status = (params.get('status') or default).strip()
    if status not in VALID_STATUS:
        raise ValidationError(message=f'status 必须为 {" / ".join(VALID_STATUS)} 之一', code=4000)
    return status


def _parse_action(data: dict) -> str:
    action = (data.get('action') or '').strip()
    if action not in VALID_ACTIONS:
        raise ValidationError(message='action 必须为 approve / reject', code=4000)
    return action


def _mark(obj, admin, action: str, reason: str) -> None:
    """写审核结果：approve → approved；reject → rejected + 原因。"""
    obj.reviewed_by = admin.id
    obj.reviewed_at = datetime.utcnow()
    if action == 'approve':
        obj.status = 'approved'
        obj.reject_reason = None
    else:
        obj.status = 'rejected'
        obj.reject_reason = reason


def _dish_item(dish: Dish) -> dict:
    item = _dish_schema.dump(dish)
    item['submitter'] = _submitter(dish.owner)
    item['created_at'] = dish.created_at.isoformat() if dish.created_at else None
    return item


def _shop_item(shop: Shop, with_pending_dishes: bool) -> dict:
    item = _shop_schema.dump(shop)
    item['submitter'] = _submitter(shop.owner)
    item['created_at'] = shop.created_at.isoformat() if shop.created_at else None
    if with_pending_dishes:
        item['pending_dishes'] = [
            _dish_item(d) for d in Dish.query.filter_by(shop_id=shop.id, is_active=True, status='pending')
            .order_by(Dish.id.asc()).all()
        ]
    return item


class AuditService:
    """内容审核业务。"""

    @staticmethod
    def list_shops(params: dict) -> dict:
        """店铺审核队列（默认 pending，可按 status 查看历史）。"""
        status = _parse_status(params)
        query = (
            Shop.query.filter(Shop.is_active.is_(True), Shop.status == status)
            .order_by(Shop.updated_at.desc(), Shop.id.desc())
        )
        page = int(params.get('page') or 1)
        page_size = int(params.get('page_size') or 10)
        result = paginate(query, page, page_size)
        return {**result, 'items': [_shop_item(s, with_pending_dishes=True) for s in result['items']]}

    @staticmethod
    def list_dishes(params: dict) -> dict:
        """菜品审核队列：父店已 approved 的待审菜品（默认 pending）。"""
        status = _parse_status(params)
        query = (
            Dish.query.join(Shop)
            .filter(
                Dish.is_active.is_(True),
                Dish.status == status,
                Shop.is_active.is_(True),
                Shop.status == 'approved',
            )
            .order_by(Dish.updated_at.desc(), Dish.id.desc())
        )
        page = int(params.get('page') or 1)
        page_size = int(params.get('page_size') or 10)
        result = paginate(query, page, page_size)
        return {**result, 'items': [_dish_item(d) for d in result['items']]}

    @staticmethod
    def review_shop(admin, shop_id: int, data: dict) -> dict:
        """审核单家店铺。"""
        shop = db.session.get(Shop, shop_id)
        if shop is None or not shop.is_active:
            raise NotFoundError(message='店铺不存在', code=4040)
        action = _parse_action(data)
        reason = None
        if action == 'reject':
            reason = (data.get('reason') or '').strip() or None
            if not reason:
                raise ValidationError(message='驳回需填写原因', code=4000)
        _mark(shop, admin, action, reason)
        db.session.commit()
        return {'id': shop.id, 'status': shop.status}

    @staticmethod
    def bulk_review_shop(admin, shop_id: int, data: dict) -> dict:
        """整店审核：店铺与其全部待审菜品按同一 action 一并处理。"""
        shop = db.session.get(Shop, shop_id)
        if shop is None or not shop.is_active:
            raise NotFoundError(message='店铺不存在', code=4040)
        action = _parse_action(data)
        reason = None
        if action == 'reject':
            reason = (data.get('reason') or '').strip() or None
            if not reason:
                raise ValidationError(message='驳回需填写原因', code=4000)
        _mark(shop, admin, action, reason)
        pending_dishes = Dish.query.filter_by(shop_id=shop.id, is_active=True, status='pending').all()
        for dish in pending_dishes:
            _mark(dish, admin, action, reason)
        db.session.commit()
        return {'id': shop.id, 'status': shop.status, 'affected_dishes': len(pending_dishes)}

    @staticmethod
    def review_dish(admin, dish_id: int, data: dict) -> dict:
        """审核单道菜品（通过前置校验：父店须已 approved）。"""
        dish = db.session.get(Dish, dish_id)
        if dish is None or not dish.is_active:
            raise NotFoundError(message='菜品不存在', code=4046)
        action = _parse_action(data)
        reason = None
        if action == 'reject':
            reason = (data.get('reason') or '').strip() or None
            if not reason:
                raise ValidationError(message='驳回需填写原因', code=4000)
        if action == 'approve':
            shop = dish.shop
            if shop is None or not shop.is_active or shop.status != 'approved':
                raise ValidationError(message='该菜品所属店铺尚未通过审核，请先在店铺队列处理', code=4000)
        _mark(dish, admin, action, reason)
        db.session.commit()
        return {'id': dish.id, 'status': dish.status}
