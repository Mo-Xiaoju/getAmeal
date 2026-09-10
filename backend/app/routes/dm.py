"""私信（1 对 1）相关路由。"""
from flask import Blueprint, g, request

from app.schemas.message import DmSendSchema
from app.services.message_service import MessageService
from app.utils.decorators import require_consumer, require_login
from app.utils.responses import ok
from app.utils.exceptions import ValidationError

bp_dm = Blueprint('dm', __name__)


@bp_dm.route('/conversations', methods=['GET'])
@require_login
def list_conversations():
    """我的私信会话列表（按最近活跃排序 + 未读数）。"""
    return ok(MessageService.conversations(g.current_user))


@bp_dm.route('/unread-count', methods=['GET'])
@require_login
def get_unread_count():
    """我收到的未读私信总数（未读徽标）。"""
    return ok(MessageService.unread_count(g.current_user))


@bp_dm.route('/suggestions', methods=['GET'])
@require_login
def list_suggestions():
    """推荐可私聊对象（官方助手 / 管理员 / 最近关注）。"""
    return ok(MessageService.dm_suggestions(g.current_user))


@bp_dm.route('/conversations/<int:peer_id>', methods=['GET'])
@require_login
def get_peer_messages(peer_id):
    """与某人的私信历史（before_id 向上拉取）。"""
    params = request.args.to_dict()
    return ok(MessageService.dm_messages(g.current_user, peer_id, params))


@bp_dm.route('/send', methods=['POST'])
@require_consumer
def send_dm():
    """发送私信（实时送达；离线时仍落库，可在历史中看到）。"""
    raw = request.get_json(silent=True) or {}
    data = DmSendSchema().load(raw)
    content = (data.get('content') or '').strip()
    if not content:
        raise ValidationError(message='消息内容不能为空', code=4000)
    channel = {'type': 'dm', 'id': data['recipient_id']}
    # shop_id 透传给服务层：schema 会 EXCLUDE 掉未知字段，需从原始请求取，
    # 由 MessageService 统一拦截「私信不支持关联店铺」（与 socket 路径一致）
    message = MessageService.send(g.current_user, channel, content, None, raw.get('shop_id'))
    return ok(message, message='发送成功')


@bp_dm.route('/conversations/<int:peer_id>/read', methods=['POST'])
@require_login
def mark_peer_read(peer_id):
    """打开会话后把对方发给我的未读消息标记为已读。"""
    MessageService.mark_read(g.current_user, peer_id)
    return ok(None, message='success')
