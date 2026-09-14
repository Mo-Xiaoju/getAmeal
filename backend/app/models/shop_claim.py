"""店铺认领申请模型：商户申请认领无主店铺，待管理员审核。

与 Shop.status 的内容审核语义刻意分开：店铺的公开与否由 Shop.status 决定，
认领只决定店铺归属（owner_id）。审核认领申请绝不改动 Shop.status / is_active，
否则一次归属权审批会连带把店铺从公开列表下架。
"""
from datetime import datetime

from app.extensions import db


class ShopClaim(db.Model):
    """商户对某家无主店铺的认领申请。"""

    __tablename__ = 'shop_claims'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    shop_id = db.Column(db.Integer, db.ForeignKey('shops.id'), nullable=False, index=True)
    applicant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    # 审核状态：pending 待审核 | approved 已通过（店铺归属已转移）| rejected 已驳回
    status = db.Column(db.String(20), nullable=False, default='pending', server_default='pending',
                       index=True)  # 管理端队列按 status 过滤
    reason = db.Column(db.String(500), nullable=True)         # 申请人填写的认领理由
    review_reason = db.Column(db.String(500), nullable=True)  # 审核意见 / 驳回原因
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系：N:1 店铺 / 申请人 / 审核人
    shop = db.relationship('Shop', back_populates='claims')
    applicant = db.relationship('User', foreign_keys=[applicant_id])
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])
