"""校园群聊相关路由（需登录）。"""
from flask import Blueprint

from app.utils.responses import ok

bp_chat = Blueprint('chat', __name__)


@bp_chat.route('/messages', methods=['GET'])
def get_messages():
    """获取群聊历史消息（分页）。"""
    return ok()  # TODO: ChatService.list_messages()


@bp_chat.route('/messages', methods=['POST'])
def send_message():
    """发送群聊消息。"""
    return ok()  # TODO: ChatService.send_message()


@bp_chat.route('/messages/stream', methods=['GET'])
def stream_messages():
    """SSE 实时消息流（占位）。"""
    return ok()  # TODO: ChatService.stream_messages()
