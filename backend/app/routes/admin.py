"""管理后台路由（需管理员权限）。"""
from flask import Blueprint, g, request

from app.services.admin_service import AdminService
from app.utils.decorators import require_admin
from app.utils.responses import ok

bp_admin = Blueprint('admin', __name__)


@bp_admin.route('/shops', methods=['GET'])
@require_admin
def admin_get_shops():
    """店铺管理列表。"""
    params = request.args.to_dict()
    return ok(AdminService.list_shops(params))


@bp_admin.route('/shops', methods=['POST'])
@require_admin
def admin_add_shop():
    """新增店铺。"""
    data = request.get_json(silent=True) or {}
    return ok(AdminService.add_shop(data), message='店铺已创建')


@bp_admin.route('/shops/<int:shop_id>', methods=['PUT'])
@require_admin
def admin_update_shop(shop_id):
    """修改店铺信息。"""
    data = request.get_json(silent=True) or {}
    return ok(AdminService.update_shop(shop_id, data), message='已更新')


@bp_admin.route('/shops/<int:shop_id>', methods=['DELETE'])
@require_admin
def admin_delete_shop(shop_id):
    """删除/下架店铺（软删除）。"""
    return ok(AdminService.delete_shop(shop_id), message='店铺已下架')


@bp_admin.route('/users', methods=['GET'])
@require_admin
def admin_get_users():
    """用户列表（分页）。"""
    params = request.args.to_dict()
    return ok(AdminService.list_users(params))


@bp_admin.route('/users/<int:user_id>', methods=['PUT'])
@require_admin
def admin_update_user(user_id):
    """修改用户（封禁 / 变更角色）。"""
    data = request.get_json(silent=True) or {}
    return ok(AdminService.update_user(g.current_user, user_id, data), message='已更新')


# ---- 内容审核 ----
@bp_admin.route('/audits/shops', methods=['GET'])
@require_admin
def admin_audit_shops():
    """待审店铺列表（含该店全部待审菜品）。"""
    params = request.args.to_dict()
    return ok(AdminService.list_audit_shops(params))


@bp_admin.route('/audits/dishes', methods=['GET'])
@require_admin
def admin_audit_dishes():
    """待审菜品列表（父店已通过的逐条审核）。"""
    params = request.args.to_dict()
    return ok(AdminService.list_audit_dishes(params))


@bp_admin.route('/audits/shops/<int:shop_id>/review', methods=['POST'])
@require_admin
def admin_review_shop(shop_id):
    """单店审核（通过 / 驳回）。"""
    data = request.get_json(silent=True) or {}
    return ok(AdminService.review_shop(g.current_user, shop_id, data), message='审核完成')


@bp_admin.route('/audits/shops/<int:shop_id>/bulk', methods=['POST'])
@require_admin
def admin_bulk_review_shop(shop_id):
    """整店审核：店铺与其全部待审菜品一并通过/驳回。"""
    data = request.get_json(silent=True) or {}
    return ok(AdminService.bulk_review_shop(g.current_user, shop_id, data), message='审核完成')


@bp_admin.route('/audits/dishes/<int:dish_id>/review', methods=['POST'])
@require_admin
def admin_review_dish(dish_id):
    """单菜品审核（通过 / 驳回）。"""
    data = request.get_json(silent=True) or {}
    return ok(AdminService.review_dish(g.current_user, dish_id, data), message='审核完成')


@bp_admin.route('/stats', methods=['GET'])
def admin_get_stats():
    """数据统计。"""
    return ok()  # TODO: AdminService.get_stats()
