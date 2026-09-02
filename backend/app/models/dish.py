"""菜品模型。"""
from datetime import datetime

from app.extensions import db


class Dish(db.Model):
    """店铺在售菜品。"""

    __tablename__ = 'dishes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    shop_id = db.Column(db.Integer, db.ForeignKey('shops.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)                 # 菜品名
    price = db.Column(db.Numeric(10, 2), nullable=False, default=0)  # 单价（元）
    description = db.Column(db.String(500), nullable=True)           # 描述
    image_url = db.Column(db.String(255), nullable=True)             # 图片
    tags = db.Column(db.String(200), nullable=True)                  # 标签，逗号分隔：辣/招牌/素食
    avg_rating = db.Column(db.Float, nullable=False, default=0.0)    # 平均评分
    rating_count = db.Column(db.Integer, nullable=False, default=0)  # 评分人数
    is_active = db.Column(db.Boolean, nullable=False, default=True)  # 是否在售（软删除）
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系：N:1 店铺
    shop = db.relationship('Shop', back_populates='dishes')
