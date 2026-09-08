"""管理端内容审核路由（学生提交的店铺/菜品，仅管理员可访问）。"""
from flask import Blueprint, g, request

from app.services.audit_service import AuditService
from app.utils.decorators import require_admin
from app.utils.responses import ok

bp_audit = Blueprint('audit', __name__)


@bp_audit.route('/audits/shops', methods=['GET'])
@require_admin
def list_shops():
    """店铺审核队列（status: approved/pending/rejected，默认 pending）。"""
    return ok(AuditService.list_shops(request.args.to_dict()))


@bp_audit.route('/audits/dishes', methods=['GET'])
@require_admin
def list_dishes():
    """菜品审核队列（父店已 approved 的待审菜品）。"""
    return ok(AuditService.list_dishes(request.args.to_dict()))


@bp_audit.route('/audits/shops/<int:shop_id>/review', methods=['POST'])
@require_admin
def review_shop(shop_id):
    """审核单家店铺：{ action: approve|reject, reason? }（reject 必填原因）。"""
    data = request.get_json(silent=True) or {}
    return ok(AuditService.review_shop(g.current_user, shop_id, data), message='已处理')


@bp_audit.route('/audits/shops/<int:shop_id>/bulk', methods=['POST'])
@require_admin
def bulk_review_shop(shop_id):
    """整店审核：店铺与其全部待审菜品一并通过/驳回。"""
    data = request.get_json(silent=True) or {}
    return ok(AuditService.bulk_review_shop(g.current_user, shop_id, data), message='已处理')


@bp_audit.route('/audits/dishes/<int:dish_id>/review', methods=['POST'])
@require_admin
def review_dish(dish_id):
    """审核单道菜品：{ action: approve|reject, reason? }。"""
    data = request.get_json(silent=True) or {}
    return ok(AuditService.review_dish(g.current_user, dish_id, data), message='已处理')
