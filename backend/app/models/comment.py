"""笔记评论模型。"""
from datetime import datetime

from app.extensions import db


class Comment(db.Model):
    """探店笔记下的评论。"""

    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # 关系：N:1 笔记与用户
    post = db.relationship('Post', back_populates='comments')
    user = db.relationship('User', backref='comments')
