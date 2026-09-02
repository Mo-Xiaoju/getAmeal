"""收藏模型：用户与店铺/笔记的多对多关联表（二选一，由对应外键是否为空区分）。"""
from datetime import datetime

from app.extensions import db


class Favorite(db.Model):
    """用户收藏的店铺或探店笔记。"""

    __tablename__ = 'favorites'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    shop_id = db.Column(db.Integer, db.ForeignKey('shops.id'), nullable=True)   # 收藏店铺
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True)   # 收藏笔记
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'shop_id', name='uq_favorite_user_shop'),
        db.UniqueConstraint('user_id', 'post_id', name='uq_favorite_user_post'),
    )

    # 关系
    user = db.relationship('User', backref='favorites')
    shop = db.relationship('Shop', backref='favorited_by')
    post = db.relationship('Post', backref='favorited_by')
