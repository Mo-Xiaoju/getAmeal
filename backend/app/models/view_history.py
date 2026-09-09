"""浏览记录模型：用户浏览过（详情页打开过）的店铺/菜品/笔记，去重只保留最近一次。"""
from datetime import datetime

from app.extensions import db


class ViewRecord(db.Model):
    """用户最近浏览记录（每 用户+目标 只保留一行，刷新时间）。"""

    __tablename__ = 'view_history'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    target_type = db.Column(db.String(16), nullable=False)   # 'shop' | 'dish' | 'post'
    target_id = db.Column(db.Integer, nullable=False)
    viewed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'target_type', 'target_id', name='uq_view_user_target'),
        db.Index('ix_view_user_viewed', 'user_id', 'viewed_at'),
    )

    # 关系
    user = db.relationship('User', backref='view_records')
