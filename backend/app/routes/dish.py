"""菜品相关路由。"""
from flask import Blueprint, g, request

from app.services.dish_service import DishService
from app.services.recommend_service import RecommendService
from app.utils.decorators import optional_login
from app.utils.responses import ok

bp_dish = Blueprint('dish', __name__)


@bp_dish.route('/recommend', methods=['GET'])
@optional_login
def get_dish_recommend():
    """推荐菜品：父店校内 approved+active；登录且有画像则按店铺偏好/标签个性化。"""
    params = request.args.to_dict()
    return ok(RecommendService.dishes(g.current_user, params))


@bp_dish.route('/<int:dish_id>', methods=['GET'])
def get_dish_detail(dish_id):
    """菜品详情。"""
    return ok(DishService.get_detail(dish_id))


@bp_dish.route('', methods=['GET'], strict_slashes=False)
def get_dish_list():
    """菜品列表：支持 school_id / shop_id 过滤、分页。"""
    params = request.args.to_dict()
    return ok(DishService.list(params))
