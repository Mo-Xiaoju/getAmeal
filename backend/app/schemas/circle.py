"""圈子（QQ/微信群）相关 Schema。"""
from flask import g
from marshmallow import EXCLUDE, Schema, fields

from app.models import CircleMembership


class CircleSchema(Schema):
    """圈子列表项 / 详情基础字段。"""

    id = fields.Int()
    school_id = fields.Int()
    name = fields.Str()
    cover_url = fields.Str()
    description = fields.Str()
    member_count = fields.Int()
    creator = fields.Method('_creator')
    created_at = fields.DateTime()

    def _creator(self, obj) -> dict:
        if obj.creator is None:
            return None
        return {
            'id': obj.creator.id,
            'nickname': obj.creator.nickname,
            'avatar_url': obj.creator.avatar_url,
        }


class CircleDetailSchema(CircleSchema):
    """圈子详情：在基础字段上扩展当前登录用户的成员状态。"""

    joined = fields.Method('_joined')

    def _joined(self, obj) -> bool:
        user = getattr(g, 'current_user', None)
        if user is None:
            return False
        return (
            CircleMembership.query.filter_by(user_id=user.id, circle_id=obj.id).first() is not None
        )


class CircleCreateSchema(Schema):
    """创建圈子请求。"""

    school_id = fields.Int(required=True)   # 圈子按学校隔离，创建时必须指定学校
    name = fields.Str(required=True)
    cover_url = fields.Str(load_default=None)
    description = fields.Str(load_default=None)

    class Meta:
        unknown = EXCLUDE


class CircleUpdateSchema(Schema):
    """更新圈子请求（仅创建者可改）。"""

    name = fields.Str(load_default=None)
    cover_url = fields.Str(load_default=None)
    description = fields.Str(load_default=None)

    class Meta:
        unknown = EXCLUDE
