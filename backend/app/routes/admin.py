"""管理后台路由（需管理员权限）。"""
from flask import Blueprint

from app.utils.responses import ok

bp_admin = Blueprint('admin', __name__)


@bp_admin.route('/shops', methods=['GET'])
def admin_get_shops():
    """店铺管理列表。"""
    return ok()  # TODO: AdminService.list_shops()


@bp_admin.route('/shops', methods=['POST'])
def admin_add_shop():
    """新增店铺。"""
    return ok()  # TODO: AdminService.add_shop()


@bp_admin.route('/shops/<int:shop_id>', methods=['PUT'])
def admin_update_shop(shop_id):
    """修改店铺信息。"""
    return ok()  # TODO: AdminService.update_shop(shop_id)


@bp_admin.route('/shops/<int:shop_id>', methods=['DELETE'])
def admin_delete_shop(shop_id):
    """删除/下架店铺（软删除）。"""
    return ok()  # TODO: AdminService.delete_shop(shop_id)


@bp_admin.route('/users', methods=['GET'])
def admin_get_users():
    """用户列表。"""
    return ok()  # TODO: AdminService.list_users()


@bp_admin.route('/users/<int:user_id>', methods=['PUT'])
def admin_update_user(user_id):
    """修改用户（封禁 / 变更角色）。"""
    return ok()  # TODO: AdminService.update_user(user_id)


@bp_admin.route('/reviews', methods=['GET'])
def admin_get_reviews():
    """评价审核列表。"""
    return ok()  # TODO: AdminService.list_reviews()


@bp_admin.route('/reviews/<int:review_id>', methods=['DELETE'])
def admin_delete_review(review_id):
    """删除评价。"""
    return ok()  # TODO: AdminService.delete_review(review_id)


@bp_admin.route('/stats', methods=['GET'])
def admin_get_stats():
    """数据统计。"""
    return ok()  # TODO: AdminService.get_stats()
