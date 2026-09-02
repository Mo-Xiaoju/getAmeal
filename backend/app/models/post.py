"""探店笔记模型。"""
from datetime import datetime

from app.extensions import db


class Post(db.Model):
    """用户发布的探店笔记。"""

    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(100), nullable=False)                        # 标题
    content = db.Column(db.Text, nullable=False)                             # 正文
    images = db.Column(db.Text, nullable=True)                               # 图片地址（JSON 数组字符串）
    shop_id = db.Column(db.Integer, db.ForeignKey('shops.id'), nullable=True)  # 关联店铺（可选）
    tags = db.Column(db.String(200), nullable=True)                          # 标签，逗号分隔
    like_count = db.Column(db.Integer, nullable=False, default=0)            # 点赞数
    favorite_count = db.Column(db.Integer, nullable=False, default=0)        # 收藏数
    comment_count = db.Column(db.Integer, nullable=False, default=0)         # 评论数
    is_active = db.Column(db.Boolean, nullable=False, default=True)          # 是否可见（软删除）
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系：N:1 用户与店铺；1:N 点赞/收藏/评论
    user = db.relationship('User', back_populates='posts')
    shop = db.relationship('Shop')
    comments = db.relationship('Comment', back_populates='post', lazy='dynamic')

    @property
    def shop_name(self) -> str:
        """关联店铺名称（供序列化使用）。"""
        return self.shop.name if self.shop else None
