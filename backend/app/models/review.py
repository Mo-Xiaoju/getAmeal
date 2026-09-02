"""评价模型：用户对店铺的评分与文字评价。"""
from datetime import datetime

from app.extensions import db


class Review(db.Model):
    """店铺评价。"""

    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    shop_id = db.Column(db.Integer, db.ForeignKey('shops.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)                        # 评分 1-5
    content = db.Column(db.Text, nullable=True)                           # 评价内容
    images = db.Column(db.Text, nullable=True)                            # 图片地址（JSON 数组字符串）
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系：N:1 用户与店铺
    user = db.relationship('User', backref='reviews')
    shop = db.relationship('Shop', back_populates='reviews')
