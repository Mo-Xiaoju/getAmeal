"""探店笔记相关路由。"""
from flask import Blueprint, g, request

from app.services.activity_service import ActivityService
from app.services.post_service import PostService
from app.utils.decorators import optional_login, require_consumer, require_login
from app.utils.responses import ok

bp_post = Blueprint('post', __name__)


@bp_post.route('', methods=['GET'], strict_slashes=False)
@optional_login
def get_post_list():
    """笔记列表：school_id / keyword 过滤，newest / hot / recommend 排序，分页。"""
    params = request.args.to_dict()
    return ok(PostService.list(params, user=g.current_user))


@bp_post.route('', methods=['POST'], strict_slashes=False)
@require_consumer
def create_post():
    """发布探店笔记（需学生/管理员，商户不可）。"""
    data = request.get_json(silent=True) or {}
    return ok(PostService.create(g.current_user, data), message='发布成功')


@bp_post.route('/mine', methods=['GET'])
@require_login
def get_my_posts():
    """当前用户的笔记列表（分页）。"""
    params = request.args.to_dict()
    return ok(PostService.list_my_posts(g.current_user, params))


@bp_post.route('/<int:post_id>', methods=['GET'])
@optional_login
def get_post_detail(post_id):
    """笔记详情（带登录态时回显点赞/收藏/关注状态，并记录进浏览历史）。"""
    data = PostService.get_detail(post_id)
    ActivityService.record_view(getattr(g, 'current_user', None), 'post', post_id)
    return ok(data)


@bp_post.route('/<int:post_id>', methods=['DELETE'])
@require_consumer
def delete_post(post_id):
    """删除自己的笔记（软删除，商户不可）。"""
    PostService.delete_post(g.current_user, post_id)
    return ok(None, message='删除成功')


@bp_post.route('/<int:post_id>/like', methods=['POST'])
@require_consumer
def toggle_like(post_id):
    """点赞/取消点赞笔记（幂等，商户不可）。"""
    return ok(PostService.toggle_like(g.current_user, post_id))


@bp_post.route('/<int:post_id>/favorite', methods=['POST'])
@require_consumer
def toggle_favorite(post_id):
    """收藏/取消收藏笔记（幂等，商户不可）。"""
    return ok(PostService.toggle_favorite(g.current_user, post_id))


@bp_post.route('/<int:post_id>/comments', methods=['GET'])
def get_comments(post_id):
    """笔记评论列表（分页）。"""
    params = request.args.to_dict()
    return ok(PostService.list_comments(post_id, params))


@bp_post.route('/<int:post_id>/comments', methods=['POST'])
@require_consumer
def add_comment(post_id):
    """发表评论（需学生/管理员，商户不可）。"""
    data = request.get_json(silent=True) or {}
    return ok(PostService.add_comment(g.current_user, post_id, data), message='评论成功')
