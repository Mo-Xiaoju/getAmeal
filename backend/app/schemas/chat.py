"""群聊消息相关 Schema。"""
from marshmallow import Schema, fields


class MessageSchema(Schema):
    """群聊消息。"""

    id = fields.Int()
    user_id = fields.Int()
    nickname = fields.Str()
    avatar_url = fields.Str()
    content = fields.Str()
    created_at = fields.DateTime()


class MessageCreateSchema(Schema):
    """发送消息请求。"""

    content = fields.Str(required=True)


class MessageQuerySchema(Schema):
    """历史消息查询参数。"""

    page = fields.Int(load_default=1)
    page_size = fields.Int(load_default=10)
