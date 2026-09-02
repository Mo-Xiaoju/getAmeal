"""店铺与评价相关路由。"""
from flask import Blueprint, g, request

from app.services.dish_service import DishService
from app.services.recommend_service import RecommendService
from app.services.shop_service import ShopService
from app.utils.decorators import optional_login, require_login
from app.utils.responses import ok

bp_shop = Blueprint('shop', __name__)


@bp_shop.route('', methods=['GET'], strict_slashes=False)
def get_shop_list():
    """店铺列表：支持学校/关键词/分类筛选、排序、分页。"""
    params = request.args.to_dict()
    return ok(ShopService.list_shops(params))


@bp_shop.route('/recommend', methods=['GET'])
def get_recommend():
    """推荐店铺：当前学校内按评分/人气（可选按距离）。"""
    params = request.args.to_dict()
    return ok(RecommendService.recommend(params))


@bp_shop.route('/<int:shop_id>/dishes', methods=['GET'])
def get_shop_dishes(shop_id):
    """店铺在售菜品列表（分页）。"""
    params = request.args.to_dict()
    return ok(DishService.list_by_shop(shop_id, params))


@bp_shop.route('/<int:shop_id>', methods=['GET'])
@optional_login
def get_shop_detail(shop_id):
    """店铺详情（带登录态时回显是否已收藏）。"""
    return ok(ShopService.get_detail(shop_id))


@bp_shop.route('/<int:shop_id>/reviews', methods=['GET'])
def get_shop_reviews(shop_id):
    """店铺评价列表（分页）。"""
    params = request.args.to_dict()
    return ok(ShopService.list_reviews(shop_id, params))


@bp_shop.route('/<int:shop_id>/reviews', methods=['POST'])
@require_login
def add_shop_review(shop_id):
    """发表评价（需登录）。"""
    data = request.get_json(silent=True) or {}
    return ok(ShopService.add_review(g.current_user, shop_id, data), message='评价成功')


@bp_shop.route('/<int:shop_id>/favorite', methods=['POST'])
@require_login
def add_favorite(shop_id):
    """收藏店铺（需登录）。"""
    return ok(ShopService.toggle_favorite(g.current_user, shop_id), message='已收藏')


@bp_shop.route('/<int:shop_id>/favorite', methods=['DELETE'])
@require_login
def remove_favorite(shop_id):
    """取消收藏（需登录）。"""
    return ok(ShopService.toggle_favorite(g.current_user, shop_id), message='已取消收藏')
