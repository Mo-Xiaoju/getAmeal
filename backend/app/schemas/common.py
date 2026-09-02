"""通用 Schema：统一响应结构与分页参数。"""
from marshmallow import Schema, fields


class MessageResponse(Schema):
    """统一响应结构：{ code, message, data }。"""

    code = fields.Int()
    message = fields.Str()
    data = fields.Raw()


class PaginationParams(Schema):
    """分页查询参数。"""

    page = fields.Int(load_default=1)
    page_size = fields.Int(load_default=10)


class PaginationMeta(Schema):
    """分页元信息。"""

    page = fields.Int()
    page_size = fields.Int()
    total = fields.Int()
    total_pages = fields.Int()
