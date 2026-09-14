"""评论模型：探店笔记评论 / 评价回复共用一张表。

按 favorites 的「可空外键多态」惯用法区分归属对象，四类行的写法固定为：

    顶层笔记评论 : post_id=X,   review_id=NULL, parent_id=NULL
    笔记下的回复 : post_id=X,   review_id=NULL, parent_id=Y   (Y 是根评论)
    顶层评价回复 : post_id=NULL, review_id=X,  parent_id=NULL
    评价下的回复 : post_id=NULL, review_id=X,  parent_id=Y   (Y 是根回复)

关键：post_id / review_id 是「线程归属」，**每一条行都要带上（含嵌套回复）**，
这样取整条线程就是一句 WHERE review_id = X，不用 join 也不用递归。
两者恰好其一非空，由 CommentService 保证（本仓库迁移里没有 CHECK 约束的先例）。

回复固定两层：回复某条嵌套回复时，parent_id 归一化到它的根，被回复人用
reply_to_user_id 表达（前端渲染成 @昵称）。
"""
from datetime import datetime

from app.extensions import db


class Comment(db.Model):
    """探店笔记评论或评价回复。"""

    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 线程归属：二选一，见模块 docstring
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True, index=True)
    review_id = db.Column(db.Integer, db.ForeignKey('reviews.id'), nullable=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # 回复的父评论：NULL 表示顶层；非空时恒为根评论（回复嵌套回复会被归一化到根）
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True, index=True)
    # 被回复人：仅回复时有值，由服务端从父评论作者派生（不接受客户端传入，否则可冒充 @）
    reply_to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    content = db.Column(db.String(500), nullable=False)
    like_count = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # 关系
    post = db.relationship('Post', back_populates='comments')
    review = db.relationship('Review', back_populates='replies')
    user = db.relationship('User', foreign_keys=[user_id], backref='comments')
    reply_to_user = db.relationship('User', foreign_keys=[reply_to_user_id])
    parent = db.relationship('Comment', remote_side=[id], back_populates='children')
    children = db.relationship('Comment', back_populates='parent')
