"""群聊消息模型：校内实时交流。"""
from datetime import datetime

from app.extensions import db


class Message(db.Model):
    """校园群聊消息。"""

    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)                          # 消息内容
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # TODO: 关系属性（user）待填充
