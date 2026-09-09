"""商户中心路由（仅商户角色可访问）。"""
from flask import Blueprint, g, request

from app.services.merchant_service import MerchantService
from app.utils.decorators import require_merchant
from app.utils.responses import ok

bp_merchant = Blueprint('merchant', __name__)


@bp_merchant.route('/shops', methods=['GET'])
@require_merchant
def list_my_shops():
    """我的店铺列表。"""
    return ok(MerchantService.list_my_shops(g.current_user, request.args.to_dict()))


@bp_merchant.route('/shops/claimable', methods=['GET'])
@require_merchant
def list_claimable_shops():
    """可认领的店铺（已公开且未被商户认领，可按 school_id 限定）。"""
    return ok(MerchantService.list_claimable(g.current_user, request.args.to_dict()))


@bp_merchant.route('/shops/<int:shop_id>/claim', methods=['POST'])
@require_merchant
def claim_shop(shop_id):
    """认领一家未入驻店铺到自己名下。"""
    return ok(MerchantService.claim_shop(g.current_user, shop_id), message='认领成功')


@bp_merchant.route('/shops', methods=['POST'])
@require_merchant
def create_shop():
    """新增我的店铺。"""
    data = request.get_json(silent=True) or {}
    return ok(MerchantService.create_shop(g.current_user, data), message='店铺创建成功')


@bp_merchant.route('/shops/<int:shop_id>', methods=['PUT'])
@require_merchant
def update_shop(shop_id):
    """修改我的店铺。"""
    data = request.get_json(silent=True) or {}
    return ok(MerchantService.update_shop(g.current_user, shop_id, data), message='已更新')


@bp_merchant.route('/shops/<int:shop_id>', methods=['DELETE'])
@require_merchant
def delete_shop(shop_id):
    """删除我的店铺（软删除）。"""
    MerchantService.delete_shop(g.current_user, shop_id)
    return ok(None, message='已删除')


@bp_merchant.route('/shops/<int:shop_id>/dishes', methods=['GET'])
@require_merchant
def list_my_dishes(shop_id):
    """某店铺的菜品列表。"""
    return ok(MerchantService.list_my_dishes(g.current_user, shop_id, request.args.to_dict()))


@bp_merchant.route('/shops/<int:shop_id>/dishes', methods=['POST'])
@require_merchant
def create_dish(shop_id):
    """给店铺添加菜品。"""
    data = request.get_json(silent=True) or {}
    return ok(MerchantService.create_dish(g.current_user, shop_id, data), message='菜品添加成功')


@bp_merchant.route('/dishes/<int:dish_id>', methods=['PUT'])
@require_merchant
def update_dish(dish_id):
    """修改菜品。"""
    data = request.get_json(silent=True) or {}
    return ok(MerchantService.update_dish(g.current_user, dish_id, data), message='已更新')


@bp_merchant.route('/dishes/<int:dish_id>', methods=['DELETE'])
@require_merchant
def delete_dish(dish_id):
    """删除菜品（软删除）。"""
    MerchantService.delete_dish(g.current_user, dish_id)
    return ok(None, message='已删除')
