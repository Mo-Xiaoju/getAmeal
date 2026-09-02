"""学校模型：用户与店铺的数据隔离边界。"""
from datetime import datetime

from app.extensions import db


class School(db.Model):
    """学校：用户选择学校后浏览该校下的店铺内容。"""

    __tablename__ = 'schools'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False)         # 学校名称
    address = db.Column(db.String(200), nullable=True)                    # 所在地（省/市）
    logo_url = db.Column(db.String(255), nullable=True)                   # logo 地址
    is_active = db.Column(db.Boolean, nullable=False, default=True)       # 是否启用
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系：1:N 店铺
    shops = db.relationship('Shop', back_populates='school', lazy='dynamic')
    users = db.relationship('User', back_populates='school', lazy='dynamic')

    def __repr__(self) -> str:
        return f'<School {self.id} {self.name}>'
