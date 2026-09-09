"""个人中心相关路由（需登录）。"""
from flask import Blueprint, g, request

from app.services.activity_service import ActivityService
from app.services.shop_service import ShopService
from app.services.user_service import UserService
from app.utils.decorators import require_consumer, require_login
from app.utils.responses import ok

bp_user = Blueprint('user', __name__)


@bp_user.route('/favorites', methods=['GET'])
@require_login
def get_favorites():
    """当前用户收藏列表（店铺/笔记，type 可选，分页）。"""
    params = request.args.to_dict()
    return ok(ActivityService.list_favorites(g.current_user, params))


@bp_user.route('/likes', methods=['GET'])
@require_login
def get_my_likes():
    """当前用户点赞过的笔记列表（分页）。"""
    params = request.args.to_dict()
    return ok(ActivityService.list_likes(g.current_user, params))


@bp_user.route('/history', methods=['GET'])
@require_login
def get_my_history():
    """当前用户浏览记录（店铺/菜品/笔记，type 可选，分页）。"""
    params = request.args.to_dict()
    return ok(ActivityService.list_history(g.current_user, params))


@bp_user.route('/following', methods=['GET'])
@require_login
def get_following():
    """当前用户关注的人（分页）。"""
    params = request.args.to_dict()
    return ok(UserService.list_following(g.current_user, params))


@bp_user.route('/followers', methods=['GET'])
@require_login
def get_followers():
    """关注当前用户的人（分页）。"""
    params = request.args.to_dict()
    return ok(UserService.list_followers(g.current_user, params))


@bp_user.route('/<int:user_id>/follow', methods=['POST'])
@require_consumer
def toggle_follow(user_id):
    """关注/取关用户（幂等，商户不可）。"""
    return ok(UserService.toggle_follow(g.current_user, user_id))


@bp_user.route('/reviews', methods=['GET'])
@require_login
def get_my_reviews():
    """当前用户的评价列表（分页）。"""
    params = request.args.to_dict()
    return ok(ShopService.list_my_reviews(g.current_user, params))


@bp_user.route('/reviews/<int:review_id>', methods=['DELETE'])
@require_login
def delete_my_review(review_id):
    """删除当前用户的某条评价。"""
    ShopService.delete_review(g.current_user, review_id)
    return ok(None, message='删除成功')
