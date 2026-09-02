"""业务异常定义。

所有业务异常统一继承 ApiError，由全局错误处理器捕获并输出统一响应。
"""


class ApiError(Exception):
    """业务异常基类。"""

    def __init__(self, message: str = '请求失败', code: int = 400, status_code: int = 200):
        self.message = message      # 面向用户的提示信息
        self.code = code            # 业务码
        self.status_code = status_code  # HTTP 状态码
        super().__init__(message)


class ValidationError(ApiError):
    """参数校验失败。"""


class NotFoundError(ApiError):
    """资源不存在。"""


class AuthenticationError(ApiError):
    """未认证或凭证失效。"""


class PermissionError(ApiError):
    """无操作权限。"""


class DatabaseError(ApiError):
    """数据库操作失败。"""
