"""校园群聊（全校大群，按学校隔离）相关路由。"""
from flask import Blueprint, g, request

from app.services.message_service import MessageService
from app.utils.decorators import require_login
from app.utils.exceptions import PermissionError, ValidationError
from app.utils.responses import ok

bp_chat = Blueprint('chat', __name__)


def _school_id_of(user) -> int:
    """全校群聊的目标学校 = 当前用户绑定学校（学校隔离）。"""
    if user.school_id is None:
        raise ValidationError(message='请先在个人中心选择学校', code=4000)
    return user.school_id


@bp_chat.route('/messages', methods=['GET'])
@require_login
def get_school_messages():
    """本校全校群聊历史（before_id 向上拉取）。"""
    params = request.args.to_dict()
    school_id = params.get('school_id')
    if school_id:
        if int(school_id) != g.current_user.school_id:
            raise PermissionError(message='仅能查看本校群聊', code=4030)
    else:
        school_id = _school_id_of(g.current_user)
    return ok(MessageService.school_messages(int(school_id), params))


@bp_chat.route('/messages', methods=['POST'])
@require_login
def send_school_message():
    """发送全校群聊消息（所有登录角色，含商户）；可附带店铺标注。"""
    data = request.get_json(silent=True) or {}
    content = (data.get('content') or '').strip()
    shop_id = data.get('shop_id')
    if not content and not shop_id:
        raise ValidationError(message='消息内容不能为空', code=4000)
    channel = {'type': 'school', 'id': _school_id_of(g.current_user)}
    message = MessageService.send(g.current_user, channel, content, None, shop_id)
    return ok(message, message='发送成功')
