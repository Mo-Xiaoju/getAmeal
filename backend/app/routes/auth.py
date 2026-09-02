"""认证相关路由。"""
from flask import Blueprint, g, request

from app.services.auth_service import AuthService
from app.utils.decorators import require_login, require_refresh_token
from app.utils.responses import ok

bp_auth = Blueprint('auth', __name__)


@bp_auth.route('/register', methods=['POST'])
def register():
    """注册新用户，返回用户信息与 token。"""
    data = request.get_json(silent=True) or {}
    result = AuthService.register(data)
    return ok(result, message='注册成功')


@bp_auth.route('/login', methods=['POST'])
def login():
    """登录，返回 JWT token 与用户信息。"""
    data = request.get_json(silent=True) or {}
    result = AuthService.login(data)
    return ok(result, message='登录成功')


@bp_auth.route('/refresh', methods=['POST'])
@require_refresh_token
def refresh():
    """刷新 access_token。"""
    result = AuthService.refresh(g.current_user)
    return ok(result, message='刷新成功')


@bp_auth.route('/logout', methods=['POST'])
@require_login
def logout():
    """登出（前端清除 token，服务端侧刷新令牌为无状态 JWT，无需撤销）。"""
    return ok(None, message='已退出登录')


@bp_auth.route('/me', methods=['GET'])
@require_login
def get_me():
    """获取当前登录用户信息。"""
    result = AuthService.get_current_user(g.current_user)
    return ok(result)


@bp_auth.route('/me', methods=['PUT'])
@require_login
def update_me():
    """更新当前登录用户信息。"""
    data = request.get_json(silent=True) or {}
    result = AuthService.update_current_user(g.current_user, data)
    return ok(result, message='更新成功')


@bp_auth.route('/password', methods=['PUT'])
@require_login
def change_password():
    """修改登录密码。"""
    data = request.get_json(silent=True) or {}
    AuthService.change_password(g.current_user, data)
    return ok(None, message='密码修改成功')
