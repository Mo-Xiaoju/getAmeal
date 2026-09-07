"""用户认证相关 Schema。"""
from marshmallow import EXCLUDE, Schema, fields, validate

from app.schemas.school import SchoolSchema

# 用户角色：student 学生 | merchant 商户 | admin 管理员（admin 仅由管理员后台授予）
ROLES = ('student', 'merchant')


class RegisterSchema(Schema):
    """注册请求。"""

    username = fields.Str(required=True)
    password = fields.Str(required=True)
    nickname = fields.Str(required=False, load_default=None)
    school_id = fields.Int(required=False, load_default=None)
    role = fields.Str(load_default='student', validate=validate.OneOf(ROLES))

    class Meta:
        unknown = EXCLUDE


class LoginSchema(Schema):
    """登录请求。"""

    username = fields.Str(required=True)
    password = fields.Str(required=True)

    class Meta:
        unknown = EXCLUDE


class UserSchema(Schema):
    """用户信息。"""

    id = fields.Int()
    username = fields.Str()
    nickname = fields.Str()
    avatar_url = fields.Str()
    role = fields.Str()
    school_id = fields.Int()
    school = fields.Nested(SchoolSchema, dump_only=True)
    is_active = fields.Bool()
    created_at = fields.DateTime()


class PasswordChangeSchema(Schema):
    """修改密码请求。"""

    old_password = fields.Str(required=True)
    new_password = fields.Str(required=True)

    class Meta:
        unknown = EXCLUDE


class UpdateMeSchema(Schema):
    """更新个人信息请求。"""

    nickname = fields.Str()
    avatar_url = fields.Str()
    school_id = fields.Int()

    class Meta:
        unknown = EXCLUDE
