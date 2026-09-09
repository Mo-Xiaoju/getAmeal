"""管理后台路由（需管理员权限）。"""
from flask import Blueprint, g, request

from app.services.admin_service import AdminService
from app.utils.decorators import require_admin
from app.utils.exceptions import ValidationError
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


@bp_admin.route('/shops/<int:shop_id>/category', methods=['PUT'])
@require_admin
def admin_reclassify_shop_category(shop_id):
    """归类店铺分类（受控词表），body {category}，传 null 可清空。"""
    data = request.get_json(silent=True) or {}
    if 'category' not in data:
        raise ValidationError(message='请提供 category 字段（可传 null 清空分类）', code=4000)
    return ok(AdminService.reclassify_shop_category(shop_id, data.get('category')), message='已更新')


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
