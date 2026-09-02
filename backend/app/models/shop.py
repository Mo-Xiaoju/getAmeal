"""店铺模型。"""
from datetime import datetime

from app.extensions import db


class Shop(db.Model):
    """校园周边店铺。"""

    __tablename__ = 'shops'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False, index=True)
    name = db.Column(db.String(100), unique=True, nullable=False)         # 店名
    description = db.Column(db.Text, nullable=True)                       # 简介
    address = db.Column(db.String(200), nullable=False)                   # 地址
    longitude = db.Column(db.Float, nullable=True)                        # 经度（用于距离推荐）
    latitude = db.Column(db.Float, nullable=True)                         # 纬度
    category = db.Column(db.String(50), nullable=True)                    # 分类：川菜/快餐/奶茶…
    price_range = db.Column(db.String(20), nullable=True)                 # 人均区间：如 "10-20元"
    avg_rating = db.Column(db.Float, nullable=False, default=0.0)         # 平均评分
    rating_count = db.Column(db.Integer, nullable=False, default=0)       # 评分人数
    image_url = db.Column(db.String(255), nullable=True)                  # 封面图
    is_active = db.Column(db.Boolean, nullable=False, default=True)       # 是否上架（软删除）
    # 商户/提交者归属；NULL 表示由管理员创建
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    # 审核状态：approved 已通过 | pending 待审核（学生提交）| rejected 已驳回
    status = db.Column(db.String(20), nullable=False, default='approved', server_default='approved')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系：N:1 学校/归属用户；1:N 菜品、评价与收藏
    school = db.relationship('School', back_populates='shops')
    owner = db.relationship('User', backref='owned_shops')
    dishes = db.relationship('Dish', back_populates='shop', lazy='dynamic')
    reviews = db.relationship('Review', back_populates='shop', lazy='dynamic')

    @property
    def school_name(self) -> str:
        """所属学校名称（供序列化使用，不落库）。"""
        return self.school.name if self.school else None
