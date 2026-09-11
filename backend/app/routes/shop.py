"""店铺与评价相关路由。"""
from flask import Blueprint, g, request

from app.categories import CATEGORIES, ZONES
from app.services.activity_service import ActivityService
from app.services.dish_service import DishService
from app.services.recommend_service import RecommendService
from app.services.shop_service import ShopService
from app.utils.decorators import optional_login, require_consumer
from app.utils.responses import ok

bp_shop = Blueprint('shop', __name__)


@bp_shop.route('', methods=['GET'], strict_slashes=False)
def get_shop_list():
    """店铺列表：支持学校/关键词/分类筛选、排序、分页。"""
    params = request.args.to_dict()
    return ok(ShopService.list_shops(params))


@bp_shop.route('/categories', methods=['GET'])
def get_shop_categories():
    """店铺规范分类列表（受控词表唯一来源，供前端表单下拉 / 筛选取值）。"""
    return ok({'categories': CATEGORIES})


@bp_shop.route('/zones', methods=['GET'])
def get_shop_zones():
    """店铺大分类词表（校内/周边/外卖），供前端下拉与筛选取值。"""
    return ok({'zones': ZONES})


@bp_shop.route('/recommend', methods=['GET'])
@optional_login
def get_recommend():
    """推荐店铺：校内 approved+active；登录且有足够行为则轻个性化，否则改进热门榜。"""
    params = request.args.to_dict()
    return ok(RecommendService.shops(g.current_user, params))


@bp_shop.route('/<int:shop_id>/dishes', methods=['GET'])
def get_shop_dishes(shop_id):
    """店铺在售菜品列表（分页）。"""
    params = request.args.to_dict()
    return ok(DishService.list_by_shop(shop_id, params))


@bp_shop.route('/<int:shop_id>', methods=['GET'])
@optional_login
def get_shop_detail(shop_id):
    """店铺详情（带登录态时回显是否已收藏，并记录进浏览历史）。"""
    data = ShopService.get_detail(shop_id)
    ActivityService.record_view(getattr(g, 'current_user', None), 'shop', shop_id)
    return ok(data)


@bp_shop.route('/<int:shop_id>/reviews', methods=['GET'])
def get_shop_reviews(shop_id):
    """店铺评价列表（分页）。"""
    params = request.args.to_dict()
    return ok(ShopService.list_reviews(shop_id, params))


@bp_shop.route('/<int:shop_id>/reviews', methods=['POST'])
@require_consumer
def add_shop_review(shop_id):
    """发表评价（需学生/管理员，商户不可）。"""
    data = request.get_json(silent=True) or {}
    return ok(ShopService.add_review(g.current_user, shop_id, data), message='评价成功')


@bp_shop.route('/<int:shop_id>/favorite', methods=['POST'])
@require_consumer
def add_favorite(shop_id):
    """收藏店铺（需学生/管理员，商户不可）。"""
    return ok(ShopService.toggle_favorite(g.current_user, shop_id), message='已收藏')


@bp_shop.route('/<int:shop_id>/favorite', methods=['DELETE'])
@require_consumer
def remove_favorite(shop_id):
    """取消收藏（需学生/管理员，商户不可）。"""
    return ok(ShopService.toggle_favorite(g.current_user, shop_id), message='已取消收藏')
