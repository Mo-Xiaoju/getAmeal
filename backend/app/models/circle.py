"""圈子（QQ/微信群）模型。"""
from datetime import datetime

from app.extensions import db


class Circle(db.Model):
    """美食圈子：按学校隔离的可加入群聊群组。"""

    __tablename__ = 'circles'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False, index=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    name = db.Column(db.String(60), nullable=False)                            # 圈子/群名
    cover_url = db.Column(db.String(255), nullable=True)                       # 封面图
    description = db.Column(db.String(500), nullable=True)                     # 简介
    member_count = db.Column(db.Integer, nullable=False, default=0)            # 成员数（冗余计数）
    is_active = db.Column(db.Boolean, nullable=False, default=True)            # 软删除
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    creator = db.relationship('User')
    school = db.relationship('School')
    memberships = db.relationship('CircleMembership', back_populates='circle', lazy='dynamic')

    def __repr__(self):
        return f'<Circle {self.id} {self.name}>'
