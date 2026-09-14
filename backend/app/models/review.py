"""评价模型：用户对店铺（可关联具体菜品）的评分与文字评价。"""
from datetime import datetime

from app.extensions import db


class Review(db.Model):
    """店铺评价。"""

    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    shop_id = db.Column(db.Integer, db.ForeignKey('shops.id'), nullable=False)
    # 关联菜品：NULL = 纯店铺评价；非空时必须属于本店（由 ShopService 校验），
    # 菜品详情页据此展示「菜品评价」。不做历史数据回填推断——地址/文本猜菜品会猜错。
    dish_id = db.Column(db.Integer, db.ForeignKey('dishes.id'), nullable=True, index=True)
    rating = db.Column(db.Integer, nullable=False)                        # 评分 1-5
    content = db.Column(db.Text, nullable=True)                           # 评价内容
    images = db.Column(db.Text, nullable=True)                            # 图片地址（JSON 数组字符串）
    like_count = db.Column(db.Integer, nullable=False, default=0)         # 点赞数
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系：N:1 用户与店铺；1:N 回复
    user = db.relationship('User', backref='reviews')
    shop = db.relationship('Shop', back_populates='reviews')
    # joined：小表，一次 LEFT JOIN 就能拿到 dish_name，省掉详情/列表里逐条查菜品
    dish = db.relationship('Dish', lazy='joined')
    replies = db.relationship('Comment', back_populates='review', lazy='dynamic')
