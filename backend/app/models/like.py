"""点赞模型：用户对笔记或评价的点赞关系。"""
from datetime import datetime

from app.extensions import db


class Like(db.Model):
    """用户点赞的笔记或评价（二选一，由对应外键是否为空区分）。"""

    __tablename__ = 'likes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True, index=True)    # 点赞笔记
    review_id = db.Column(db.Integer, db.ForeignKey('reviews.id'), nullable=True, index=True)  # 点赞评价
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # 两个唯一约束各自独立：MySQL 唯一索引视多个 NULL 互不相同，
    # 所以 post_id 为空的行不会互相冲突（favorites 依赖同一机制）。
    __table_args__ = (
        db.UniqueConstraint('user_id', 'post_id', name='uq_like_user_post'),
        db.UniqueConstraint('user_id', 'review_id', name='uq_like_user_review'),
    )

    # 关系
    user = db.relationship('User', backref='likes')
    post = db.relationship('Post', backref='liked_by')
    review = db.relationship('Review', backref='liked_by')
