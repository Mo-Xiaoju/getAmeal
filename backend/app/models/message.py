"""消息模型：通用消息，三种渠道由外键“三选一”区分（私信/群聊/全校群聊）。"""
from datetime import datetime

from app.extensions import db


class Message(db.Model):
    """平台消息。

    三种渠道按“哪个目标外键非空”区分：
        - recipient_id 非空 → 私信（1 对 1，发给该用户）
        - circle_id     非空 → 圈子/群聊消息
        - school_id     非空 → 全校群聊消息（按学校房间）
    同一消息仅落在一种渠道。
    """

    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 发送者
    content = db.Column(db.Text, nullable=False)                                # 消息内容
    images = db.Column(db.Text, nullable=True)                                  # 图片地址（JSON 数组字符串）
    circle_id = db.Column(db.Integer, db.ForeignKey('circles.id'), nullable=True, index=True)     # 群聊目标群
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)    # 私信目标用户
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True, index=True)     # 全校群聊目标学校
    read_at = db.Column(db.DateTime, nullable=True)                             # 私信已读时间
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # 关系（user 与 recipient 都指向 users 表，须显式指定外键避免歧义）
    user = db.relationship('User', foreign_keys=[user_id], backref='messages')
    circle = db.relationship('Circle')
    recipient = db.relationship('User', foreign_keys=[recipient_id])
