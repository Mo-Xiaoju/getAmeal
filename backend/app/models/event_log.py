"""事件日志模型：业务关键节点的埋点记录（追加式、不去重）。"""
from datetime import datetime

from app.extensions import db


class EventLog(db.Model):
    """业务事件日志（埋点）。

    event_type 受控词表：
        shop_submit / dish_submit         提交店铺 / 菜品
        shop_approve / shop_reject        店铺审核通过 / 驳回
        dish_approve / dish_reject        菜品审核通过 / 驳回
        post_create                       发布探店笔记
    """

    __tablename__ = 'event_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    actor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    actor_role = db.Column(db.String(16), nullable=True)   # student | merchant | admin（冗余便于聚合）
    event_type = db.Column(db.String(50), nullable=False, index=True)
    target_type = db.Column(db.String(16), nullable=True)  # shop | dish | post
    target_id = db.Column(db.Integer, nullable=True, index=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True, index=True)
    extra = db.Column(db.Text, nullable=True)              # JSON 字符串（店铺名/分类/驳回原因等）
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    # 关系（只读，无 backref 以免与其它模型冲突）
    actor = db.relationship('User', foreign_keys=[actor_id])
    school = db.relationship('School', foreign_keys=[school_id])
