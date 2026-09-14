"""当前登录用户视角的互动状态（点赞），按请求缓存在 g 上。

列表页每条都要按「我点过赞没有」上色，逐条查库就是 N 次查询，
所以这里一次取完、并在本次请求内缓存（g 是请求级的，不会跨请求串数据）。

三种点赞目标各自独立，**不要合并成一个集合**：笔记赞和评价赞来自 likes 表的
两个不同列，评论赞来自 comment_likes 表，混在一起就分不清 id 的含义了。

注意：读取这些字段的路由必须挂 @optional_login，否则 g.current_user 永远不存在，
已登录用户拿到的点赞态会全部是 false。
"""
from flask import g

from app.models import CommentLike, Like


def _liked_ids(g_key: str, column) -> set:
    """惰性取「当前用户已点赞的 X id 集合」，按 g_key 在请求内缓存。

    过滤掉 NULL：likes.post_id 现在可空（同一张表也存评价点赞），不过滤的话
    集合里会混进 None —— 对 `obj.id in ids` 无害，但让集合失去"全是有效 id"的含义。
    """
    ids = getattr(g, g_key, None)
    if ids is None:
        user = getattr(g, 'current_user', None)
        ids = (
            {
                row[0]
                for row in Like.query.with_entities(column).filter_by(user_id=user.id)
                if row[0] is not None
            }
            if user is not None
            else set()
        )
        setattr(g, g_key, ids)
    return ids


def liked_post_ids() -> set:
    """当前用户已点赞的笔记 id 集合。"""
    return _liked_ids('liked_post_ids', Like.post_id)


def liked_review_ids() -> set:
    """当前用户已点赞的评价 id 集合。"""
    return _liked_ids('liked_review_ids', Like.review_id)


def liked_comment_ids() -> set:
    """当前用户已点赞的评论/回复 id 集合。"""
    ids = getattr(g, 'liked_comment_ids', None)
    if ids is None:
        user = getattr(g, 'current_user', None)
        ids = (
            {row[0] for row in CommentLike.query.with_entities(CommentLike.comment_id).filter_by(user_id=user.id)}
            if user is not None
            else set()
        )
        g.liked_comment_ids = ids
    return ids


# ---- 回复预览（由 CommentService.attach_reply_previews 播种，schema 只读）----
#
# 回复森林必须由 service 播种，不能像点赞那样在 schema 里惰性自取：
# schema 只知道单条评价/笔记的 id，自取就得全表扫。这里统一读 g 上的两张表，
# 由 service 每页固定 2 条查询填好。**不要"优化"成在 schema 里查库。**
#
# 两张表对应两个不同的问法，别合并：
#   reply_preview  —— "这条笔记/评价下面有哪些顶层回复"（列表页每条问答一次）
#   reply_children —— "这条顶层回复下面有哪些子回复"（两层树里往下一层）

def reply_preview(scope: str, parent_id: int) -> dict:
    """某条笔记/评价的顶层回复预览。scope: 'post' | 'review'；parent_id: 笔记/评价 id。"""
    return getattr(g, 'reply_preview', {}).get((scope, parent_id)) or {'count': 0, 'items': []}


def reply_children(root_id: int) -> dict:
    """某条顶层评论/回复下的子回复。root_id: 顶层评论的 id。"""
    return getattr(g, 'reply_children', {}).get(root_id) or {'count': 0, 'items': []}


def reply_target_nicknames() -> dict:
    """被回复人昵称映射 {user_id: nickname}，由 service 批量填好（避免逐条 lazy load）。"""
    return getattr(g, 'reply_target_nicknames', {})
