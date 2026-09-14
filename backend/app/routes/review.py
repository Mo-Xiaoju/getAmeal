"""评价互动相关路由：点赞与回复。

评价本身的新增/删除在 routes/shop.py（POST /api/shops/<id>/reviews）。
"""
from flask import Blueprint, g, request

from app.services.comment_service import CommentService
from app.utils.decorators import optional_login, require_consumer
from app.utils.responses import ok

bp_review = Blueprint('review', __name__)


@bp_review.route('/<int:review_id>/like', methods=['POST'])
@require_consumer
def toggle_review_like(review_id):
    """点赞/取消点赞评价（幂等，商户不可）。"""
    return ok(CommentService.toggle_review_like(g.current_user, review_id))


@bp_review.route('/<int:review_id>/replies', methods=['GET'])
@optional_login
def get_review_replies(review_id):
    """评价的顶层回复列表（展开「查看全部 N 条回复」用，分页）。"""
    params = request.args.to_dict()
    return ok(CommentService.list_replies(params, review_id=review_id))


@bp_review.route('/<int:review_id>/replies', methods=['POST'])
@require_consumer
def add_review_reply(review_id):
    """回复评价（或回复其下的某条回复，带 parent_id；商户不可）。"""
    data = request.get_json(silent=True) or {}
    return ok(
        CommentService.add_reply(g.current_user, data, review_id=review_id),
        message='回复成功',
    )
