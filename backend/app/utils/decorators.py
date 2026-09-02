"""通用装饰器：登录态 / 管理员鉴权。"""
from functools import wraps

from flask import g
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required,
    verify_jwt_in_request,
)

from app.extensions import db
from app.models import User
from app.utils.exceptions import AuthenticationError, PermissionError


def _resolve_current_user() -> User:
    """根据 JWT 身份加载用户并写入 flask.g。"""
    user = db.session.get(User, int(get_jwt_identity()))
    if user is None:
        raise AuthenticationError(message='用户不存在', code=4010)
    if not user.is_active:
        raise AuthenticationError(message='账号已被禁用', code=4011)
    g.current_user = user
    return user


def require_login(func):
    """校验当前用户已登录（access token 有效）。"""

    @wraps(func)
    @jwt_required()
    def wrapper(*args, **kwargs):
        _resolve_current_user()
        return func(*args, **kwargs)

    return wrapper


def require_refresh_token(func):
    """校验 refresh token 有效（用于 /api/auth/refresh）。"""

    @wraps(func)
    @jwt_required(refresh=True)
    def wrapper(*args, **kwargs):
        _resolve_current_user()
        return func(*args, **kwargs)

    return wrapper


def require_admin(func):
    """校验当前用户已登录且角色为 admin。"""

    @wraps(func)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user = _resolve_current_user()
        if user.role != 'admin':
            raise PermissionError(message='需要管理员权限', code=4030)
        return func(*args, **kwargs)

    return wrapper


def require_merchant(func):
    """校验当前用户已登录且角色为 merchant（商户）。"""

    @wraps(func)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user = _resolve_current_user()
        if user.role != 'merchant':
            raise PermissionError(message='需要商户权限', code=4031)
        return func(*args, **kwargs)

    return wrapper


def require_consumer(func):
    """校验当前用户已登录且不是商户（商户仅允许管理自己的店铺与菜单）。"""

    @wraps(func)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user = _resolve_current_user()
        if user.role == 'merchant':
            raise PermissionError(message='商户不可进行此操作', code=4031)
        return func(*args, **kwargs)

    return wrapper


def optional_login(func):
    """可选登录：携带有效 token 时解析用户，未登录/失效则放行（不抛错）。"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request(optional=True)
            if get_jwt_identity() is not None:
                g.current_user = db.session.get(User, int(get_jwt_identity()))
        except Exception:
            g.current_user = None
        return func(*args, **kwargs)

    return wrapper
