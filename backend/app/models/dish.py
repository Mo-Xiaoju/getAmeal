"""菜品模型。"""
from datetime import datetime

from app.extensions import db


class Dish(db.Model):
    """店铺在售菜品。"""

    __tablename__ = 'dishes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    shop_id = db.Column(db.Integer, db.ForeignKey('shops.id'), nullable=False, index=True)
    # 菜品提交/创建者；NULL 表示管理员/商户（历史种子数据）创建。学生补充到社区店的菜归属提交者本人
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    name = db.Column(db.String(100), nullable=False)                 # 菜品名
    price = db.Column(db.Numeric(10, 2), nullable=False, default=0)  # 单价（元）
    description = db.Column(db.String(500), nullable=True)           # 描述
    image_url = db.Column(db.String(255), nullable=True)             # 封面图（= 第一张图，兼容旧读取端）
    images = db.Column(db.Text, nullable=True)                        # 图片地址（JSON 数组字符串，权威图集）
    tags = db.Column(db.String(200), nullable=True)                  # 标签，逗号分隔：辣/招牌/素食
    avg_rating = db.Column(db.Float, nullable=False, default=0.0)    # 平均评分
    rating_count = db.Column(db.Integer, nullable=False, default=0)  # 评分人数
    is_active = db.Column(db.Boolean, nullable=False, default=True)  # 是否在售（软删除）
    # 审核状态：approved 已通过 | pending 待审核（学生提交）| rejected 已驳回
    status = db.Column(db.String(20), nullable=False, default='approved', server_default='approved')
    # 审核记录：审核人 / 时间 / 驳回原因（approved 时常为 NULL）
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reject_reason = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系：N:1 店铺
    shop = db.relationship('Shop', back_populates='dishes')
    owner = db.relationship('User', backref='owned_dishes', foreign_keys=[owner_id])
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])
