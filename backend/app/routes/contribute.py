"""学生提交商户/菜单路由（需学生/管理员登录，商户不可）。

审查机制 TODO：pending 内容暂对 C 端可见，待审核队列落地后再放行/过滤。
"""
from flask import Blueprint, g, request

from app.services.contribute_service import ContributeService
from app.utils.decorators import require_consumer
from app.utils.responses import ok

bp_contribute = Blueprint('contribute', __name__)


@bp_contribute.route('/my', methods=['GET'])
@require_consumer
def list_my():
    """我的提交：本人创建的店铺及菜单。"""
    return ok(ContributeService.list_my(g.current_user, request.args.to_dict()))


@bp_contribute.route('/shops', methods=['POST'])
@require_consumer
def create_shop():
    """提交新店铺（pending）。"""
    data = request.get_json(silent=True) or {}
    return ok(ContributeService.create_shop(g.current_user, data), message='提交成功，待审核')


@bp_contribute.route('/shops/<int:shop_id>', methods=['PUT'])
@require_consumer
def update_shop(shop_id):
    """修改本人提交的店铺。"""
    data = request.get_json(silent=True) or {}
    return ok(ContributeService.update_shop(g.current_user, shop_id, data), message='已更新')


@bp_contribute.route('/shops/<int:shop_id>', methods=['DELETE'])
@require_consumer
def delete_shop(shop_id):
    """删除本人提交的店铺。"""
    ContributeService.delete_shop(g.current_user, shop_id)
    return ok(None, message='已删除')


@bp_contribute.route('/shops/<int:shop_id>/dishes', methods=['POST'])
@require_consumer
def add_dish(shop_id):
    """给本人提交的店铺添加菜单（pending）。"""
    data = request.get_json(silent=True) or {}
    return ok(ContributeService.add_dish(g.current_user, shop_id, data), message='提交成功，待审核')


@bp_contribute.route('/dishes/<int:dish_id>', methods=['PUT'])
@require_consumer
def update_dish(dish_id):
    """修改本人提交的菜单。"""
    data = request.get_json(silent=True) or {}
    return ok(ContributeService.update_dish(g.current_user, dish_id, data), message='已更新')


@bp_contribute.route('/dishes/<int:dish_id>', methods=['DELETE'])
@require_consumer
def delete_dish(dish_id):
    """删除本人提交的菜单。"""
    ContributeService.delete_dish(g.current_user, dish_id)
    return ok(None, message='已删除')
