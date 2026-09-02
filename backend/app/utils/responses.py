"""统一响应结构。

约定所有接口返回 { code, message, data }：
- ok()：业务成功，HTTP 200
- error()：业务失败，业务码与 HTTP 状态码分离
"""
from flask import jsonify


def ok(data=None, message: str = 'success', code: int = 0):
    """成功响应。"""
    return jsonify({'code': code, 'message': message, 'data': data})


def error(message: str = 'error', code: int = 400, data=None, status_code: int = 200):
    """失败响应。"""
    return jsonify({'code': code, 'message': message, 'data': data}), status_code
