"""菜品相关路由。"""
from flask import Blueprint, request

from app.services.dish_service import DishService
from app.utils.responses import ok

bp_dish = Blueprint('dish', __name__)


@bp_dish.route('/recommend', methods=['GET'])
def get_dish_recommend():
    """推荐菜品：当前学校内按评分/人气。"""
    params = request.args.to_dict()
    return ok(DishService.recommend(params))


@bp_dish.route('/<int:dish_id>', methods=['GET'])
def get_dish_detail(dish_id):
    """菜品详情。"""
    return ok(DishService.get_detail(dish_id))


@bp_dish.route('', methods=['GET'], strict_slashes=False)
def get_dish_list():
    """菜品列表：支持 school_id / shop_id 过滤、分页。"""
    params = request.args.to_dict()
    return ok(DishService.list(params))
