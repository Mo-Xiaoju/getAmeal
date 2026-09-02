"""个人中心相关 Schema。"""
from marshmallow import Schema, fields


class ProfileSchema(Schema):
    """个人信息。"""

    id = fields.Int()
    username = fields.Str()
    nickname = fields.Str()
    avatar_url = fields.Str()
    role = fields.Str()
    created_at = fields.DateTime()


class ProfileUpdateSchema(Schema):
    """更新个人信息请求。"""

    nickname = fields.Str()
    avatar_url = fields.Str()


class MyReviewsQuerySchema(Schema):
    """我的评价列表查询参数。"""

    page = fields.Int(load_default=1)
    page_size = fields.Int(load_default=10)
