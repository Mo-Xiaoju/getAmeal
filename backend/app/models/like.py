"""点赞模型：用户对笔记的点赞关系。"""
from datetime import datetime

from app.extensions import db


class Like(db.Model):
    """用户点赞的笔记。"""

    __tablename__ = 'likes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'post_id', name='uq_like_user_post'),
    )

    # 关系
    user = db.relationship('User', backref='likes')
    post = db.relationship('Post', backref='liked_by')
