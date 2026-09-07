"""消息相关 Schema：私信 / 圈子群聊 / 全校群聊共用一套消息结构。"""
import json

from marshmallow import EXCLUDE, Schema, fields


class MessageSchema(Schema):
    """消息体（三种渠道通用）。

    channel 由消息模型的外键「三选一」推断：recipient_id → dm；circle_id → circle；school_id → school。
    """

    id = fields.Int()
    user_id = fields.Int()
    content = fields.Str()
    images = fields.Method('_images')
    channel = fields.Method('_channel')
    author = fields.Method('_author')
    created_at = fields.DateTime()

    def _images(self, obj) -> list:
        try:
            return json.loads(obj.images or '[]')
        except (TypeError, ValueError):
            return []

    def _channel(self, obj) -> dict:
        if obj.recipient_id is not None:
            return {'type': 'dm', 'id': obj.recipient_id}
        if obj.circle_id is not None:
            return {'type': 'circle', 'id': obj.circle_id}
        return {'type': 'school', 'id': obj.school_id}

    def _author(self, obj) -> dict:
        if obj.user is None:
            return None
        return {
            'id': obj.user.id,
            'nickname': obj.user.nickname,
            'avatar_url': obj.user.avatar_url,
        }


class DmSendSchema(Schema):
    """私信发送请求。"""

    recipient_id = fields.Int(required=True)
    content = fields.Str(required=True)

    class Meta:
        unknown = EXCLUDE


class MessageSendSchema(Schema):
    """全校群聊发送请求。"""

    content = fields.Str(required=True)

    class Meta:
        unknown = EXCLUDE
