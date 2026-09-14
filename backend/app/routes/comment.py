"""评论互动相关路由。

笔记评论的发表/列表在 routes/post.py（回复也是那一个接口，多带 parent_id）；
评价回复的发表在 routes/review.py。这里只有两者共用的点赞 —— comments 是一张
表，评论 id 不区分来源，所以点赞入口也只有这一个。
"""
from flask import Blueprint, g, request

from app.services.comment_service import CommentService
from app.utils.decorators import optional_login, require_consumer
from app.utils.responses import ok

bp_comment = Blueprint('comment', __name__)


@bp_comment.route('/<int:comment_id>/like', methods=['POST'])
@require_consumer
def toggle_comment_like(comment_id):
    """点赞/取消点赞评论或回复（幂等，商户不可）。"""
    return ok(CommentService.toggle_comment_like(g.current_user, comment_id))


@bp_comment.route('/<int:comment_id>/replies', methods=['GET'])
@optional_login
def get_comment_replies(comment_id):
    """某条评论的二级回复列表（展开「查看全部 N 条回复」用，分页）。

    传根评论 id 或它下面任意一条回复的 id 都能用，服务端会归一化到根。
    """
    params = request.args.to_dict()
    return ok(CommentService.list_children(comment_id, params))
