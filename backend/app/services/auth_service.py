"""用户认证业务逻辑：注册 / 登录 / 资料维护 / 密码修改 / token 刷新。"""
from flask_jwt_extended import create_access_token, create_refresh_token

from app.extensions import db
from app.models import School, User
from app.schemas.auth import (
    LoginSchema,
    PasswordChangeSchema,
    RegisterSchema,
    UpdateMeSchema,
    UserSchema,
)
from app.utils.exceptions import ApiError, AuthenticationError, NotFoundError

_user_schema = UserSchema()


class AuthService:
    """注册 / 登录 / 密码管理等业务。"""

    @staticmethod
    def _tokens(user: User) -> dict:
        """签发 access_token 与 refresh_token。"""
        identity = str(user.id)
        return {
            'access_token': create_access_token(identity=identity),
            'refresh_token': create_refresh_token(identity=identity),
        }

    @staticmethod
    def _payload(user: User) -> dict:
        """用户信息的对外字段。"""
        return _user_schema.dump(user)

    @staticmethod
    def _validate_school(school_id) -> int:
        """校验学校存在且启用，返回学校 id。"""
        school = School.query.get(int(school_id))
        if school is None or not school.is_active:
            raise NotFoundError(message='学校不存在', code=4041)
        return school.id

    # ---- 注册 ----
    @classmethod
    def register(cls, data: dict) -> dict:
        """注册新用户，成功后返回用户信息与 token（自动登录）。

        可选传入 school_id 绑定学校（首次选择学校后注册）。
        """
        data = RegisterSchema().load(data)
        username = data['username'].strip()
        if User.query.filter_by(username=username).first():
            raise ApiError(message='用户名已存在', code=4001)

        user = User(
            username=username,
            nickname=(data.get('nickname') or username).strip() or username,
            role='student',
        )
        if data.get('school_id'):
            user.school_id = cls._validate_school(data['school_id'])
        user.set_password(data['password'])
        db.session.add(user)
        try:
            db.session.flush()
        except Exception:
            db.session.rollback()
            raise ApiError(message='注册失败，请稍后重试', code=4002)
        # 先序列化（此时未 commit），即使序列化出错也不会残留一个"注册成功但报错"的账号
        payload = cls._payload(user)
        db.session.commit()

        return {'user': payload, **cls._tokens(user)}

    # ---- 登录 ----
    @classmethod
    def login(cls, data: dict) -> dict:
        """账号密码登录，返回用户信息与 token。"""
        data = LoginSchema().load(data)
        user = User.query.filter_by(username=data['username'].strip()).first()
        if user is None or not user.check_password(data['password']):
            raise AuthenticationError(message='用户名或密码错误', code=4010)

        if not user.is_active:
            raise ApiError(message='账号已被禁用，请联系管理员', code=4011)

        return {'user': cls._payload(user), **cls._tokens(user)}

    # ---- 当前用户信息 ----
    @staticmethod
    def get_current_user(user: User) -> dict:
        """获取当前登录用户信息。"""
        return AuthService._payload(user)

    # ---- 更新资料 ----
    @classmethod
    def update_current_user(cls, user: User, data: dict) -> dict:
        """更新昵称 / 头像 / 绑定学校。"""
        data = UpdateMeSchema().load(data)
        for field in ('nickname', 'avatar_url'):
            if field in data:
                setattr(user, field, data[field].strip() if isinstance(data[field], str) else data[field])
        if 'school_id' in data and data['school_id'] is not None:
            user.school_id = cls._validate_school(data['school_id'])
        db.session.flush()
        payload = cls._payload(user)
        db.session.commit()
        return payload

    # ---- 修改密码 ----
    @staticmethod
    def change_password(user: User, data: dict) -> None:
        """校验原密码后修改新密码。"""
        data = PasswordChangeSchema().load(data)
        if not user.check_password(data['old_password']):
            raise AuthenticationError(message='原密码错误', code=4012)

        user.set_password(data['new_password'])
        db.session.commit()

    # ---- 刷新 token ----
    @classmethod
    def refresh(cls, user: User) -> dict:
        """refresh_token 换发新 token 对。"""
        return cls._tokens(user)
