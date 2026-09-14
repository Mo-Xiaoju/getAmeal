"""评论/回复相关 Schema（笔记评论与评价回复共用）。

从 schemas/post.py 再导出，使 post_service 现有的 import 不必挪动。
"""
from marshmallow import EXCLUDE, Schema, fields

from app.schemas.interaction import liked_comment_ids, reply_children, reply_target_nicknames


class CommentSchema(Schema):
    """一条评论或回复（顶层带回复预览，子回复恒为空树）。"""

    id = fields.Int()
    post_id = fields.Int()
    review_id = fields.Int()
    user_id = fields.Int()
    nickname = fields.Method('_nickname')
    avatar_url = fields.Method('_avatar')
    content = fields.Str()
    parent_id = fields.Int()
    reply_to_user_id = fields.Int()
    reply_to_nickname = fields.Method('_reply_to_nickname')
    like_count = fields.Int()
    liked = fields.Method('_liked')          # 当前登录用户是否已点赞（未登录恒 false）
    reply_count = fields.Method('_reply_count')  # 该评论下的回复总数
    replies = fields.Method('_replies')      # 最多 3 条预览，更多走 /replies 接口
    created_at = fields.DateTime()

    def _nickname(self, obj) -> str:
        return obj.user.nickname if obj.user else None

    def _avatar(self, obj) -> str:
        return obj.user.avatar_url if obj.user else None

    def _reply_to_nickname(self, obj):
        """被回复人昵称：走 service 批量填好的映射，避免逐条 lazy load User。"""
        if obj.reply_to_user_id is None:
            return None
        return reply_target_nicknames().get(obj.reply_to_user_id)

    def _liked(self, obj) -> bool:
        return obj.id in liked_comment_ids()

    def _reply_count(self, obj) -> int:
        """顶层才有子回复；子回复恒为 0，且不再往下递归（回复固定两层）。"""
        if obj.parent_id is not None:
            return 0
        return reply_children(obj.id)['count']

    def _replies(self, obj) -> list:
        if obj.parent_id is not None:
            return []
        return _comment_list_schema.dump(reply_children(obj.id)['items'])


class CommentCreateSchema(Schema):
    """发表评论/回复请求。

    只接受 parent_id：被回复人（reply_to_user_id）由服务端从父评论作者派生，
    客户端传了也无效——否则任何人都能伪造 @ 对象。
    """

    content = fields.Str(required=True)
    parent_id = fields.Int(load_default=None, allow_none=True)

    class Meta:
        unknown = EXCLUDE


_comment_schema = CommentSchema()
_comment_list_schema = CommentSchema(many=True)
