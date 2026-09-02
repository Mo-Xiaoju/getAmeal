"""关注模型：用户之间的关注关系。"""
from datetime import datetime

from app.extensions import db


class UserFollow(db.Model):
    """用户关注关系（follower 关注 followee）。"""

    __tablename__ = 'user_follows'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    followee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('follower_id', 'followee_id', name='uq_follow_follower_followee'),
    )

    # 关系：双向指向 User
    follower = db.relationship('User', foreign_keys=[follower_id],
                               backref=db.backref('following', lazy='dynamic'))
    followee = db.relationship('User', foreign_keys=[followee_id],
                               backref=db.backref('followers', lazy='dynamic'))
