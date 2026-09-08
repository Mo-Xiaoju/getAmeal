"""全局异常处理钩子。

通过 Blueprint 的 app_errorhandler 在应用层面注册错误处理器，
由 create_app() 调用 register_error_handlers() 完成挂载。
"""
from marshmallow import ValidationError as MarshmallowValidationError
from flask import Blueprint

from app.utils.exceptions import (
    ApiError,
    AuthenticationError,
    DatabaseError,
    NotFoundError,
    PermissionError,
)
from app.utils.responses import error

bp_errors = Blueprint('errors', __name__)


def register_error_handlers(app) -> None:
    """注册错误处理蓝图（在 create_app 中调用）。"""
    app.register_blueprint(bp_errors)


def register_jwt_handlers(jwt) -> None:
    """注册 flask-jwt-extended 的错误处理（在 create_app 中调用）。

    未带 token / token 无效 / 过期 / 被撤销时统一返回 HTTP 401。
    """

    @jwt.unauthorized_loader
    def missing_token(reason):
        return error(message='未登录或凭证缺失', code=4010, status_code=401)

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return error(message='凭证无效', code=4011, status_code=401)

    @jwt.expired_token_loader
    def expired_token(jwt_header, jwt_payload):
        return error(message='登录已过期，请重新登录', code=4012, status_code=401)

    @jwt.revoked_token_loader
    def revoked_token(jwt_header, jwt_payload):
        return error(message='凭证已失效', code=4013, status_code=401)


@bp_errors.app_errorhandler(ApiError)
def handle_api_error(e):
    """业务异常统一出口。"""
    return error(message=e.message, code=e.code, status_code=e.status_code)


@bp_errors.app_errorhandler(MarshmallowValidationError)
def handle_validation_error(e):
    """参数校验失败。"""
    return error(message='参数校验失败', code=400, data={'errors': e.messages})


@bp_errors.app_errorhandler(NotFoundError)
def handle_not_found(e):
    """资源不存在。"""
    return error(message=e.message, code=e.code, status_code=e.status_code)


@bp_errors.app_errorhandler(AuthenticationError)
def handle_authentication_error(e):
    """未认证 / 凭证失效。"""
    return error(message=e.message, code=e.code, status_code=e.status_code)


@bp_errors.app_errorhandler(PermissionError)
def handle_permission_error(e):
    """无操作权限。"""
    return error(message=e.message, code=e.code, status_code=e.status_code)


@bp_errors.app_errorhandler(DatabaseError)
def handle_database_error(e):
    """数据库异常。"""
    return error(message=e.message, code=e.code, status_code=e.status_code)


@bp_errors.app_errorhandler(404)
def handle_404(e):
    """兜底 404。"""
    return error(message='资源不存在', code=404, status_code=404)


@bp_errors.app_errorhandler(413)
def handle_413(e):
    """请求体超限（图片 >16MB 等），返回 JSON 信封而非 Flask 默认 HTML。"""
    return error(message='文件过大，最大支持 16MB', code=4000, status_code=413)


@bp_errors.app_errorhandler(500)
def handle_500(e):
    """兜底 500。"""
    return error(message='服务器内部错误', code=500, status_code=500)
