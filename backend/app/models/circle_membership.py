"""圈子成员关系模型：用户与圈子的多对多关联表。"""
from datetime import datetime

from app.extensions import db


class CircleMembership(db.Model):
    """用户加入的圈子（群成员关系）。"""

    __tablename__ = 'circle_memberships'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    circle_id = db.Column(db.Integer, db.ForeignKey('circles.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'circle_id', name='uq_circle_member_user_circle'),
    )

    # 关系
    circle = db.relationship('Circle', back_populates='memberships')
    user = db.relationship('User', backref='circle_memberships')
