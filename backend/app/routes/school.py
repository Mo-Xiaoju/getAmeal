"""学校相关路由。"""
from flask import Blueprint, request

from app.services.school_service import SchoolService
from app.utils.responses import ok

bp_school = Blueprint('school', __name__)


@bp_school.route('/schools', methods=['GET'])
def get_schools():
    """学校列表。"""
    return ok(SchoolService.list_schools())


@bp_school.route('/schools/<int:school_id>/shops', methods=['GET'])
def get_school_shops(school_id):
    """某学校下的店铺列表（分页）。"""
    params = request.args.to_dict()
    return ok(SchoolService.get_shops_of_school(school_id, params))
