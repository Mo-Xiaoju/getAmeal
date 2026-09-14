"""商户中心路由（仅商户角色可访问）。"""
from flask import Blueprint, g, request

from app.services.claim_service import ClaimService
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
    return ok(ClaimService.list_claimable(g.current_user, request.args.to_dict()))


@bp_merchant.route('/shops/<int:shop_id>/claim', methods=['POST'])
@require_merchant
def claim_shop(shop_id):
    """提交认领申请（需管理员审核，通过后才归到自己名下）。"""
    data = request.get_json(silent=True) or {}
    return ok(ClaimService.apply(g.current_user, shop_id, data),
              message='认领申请已提交，等待管理员审核')


@bp_merchant.route('/claims', methods=['GET'])
@require_merchant
def list_my_claims():
    """我的认领申请列表。"""
    return ok(ClaimService.list_mine(g.current_user, request.args.to_dict()))


@bp_merchant.route('/claims/<int:claim_id>', methods=['DELETE'])
@require_merchant
def cancel_claim(claim_id):
    """撤回我的待审认领申请。"""
    ClaimService.cancel(g.current_user, claim_id)
    return ok(None, message='已撤回')


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
