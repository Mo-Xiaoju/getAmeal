"""评论点赞模型：用户对评论/回复的点赞关系。

被赞对象只有 comments 一张表（笔记评论与评价回复共用），所以不需要再多态。
"""
from datetime import datetime

from app.extensions import db


class CommentLike(db.Model):
    """用户点赞的评论或回复。"""

    __tablename__ = 'comment_likes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'comment_id', name='uq_comment_like_user_comment'),
    )

    # 关系
    user = db.relationship('User', backref='comment_likes')
    comment = db.relationship('Comment', backref='liked_by')
