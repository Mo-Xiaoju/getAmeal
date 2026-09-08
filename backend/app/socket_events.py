"""SocketIO 事件处理：连接鉴权、实时消息收发、圈内房间订阅。

连接建立时按 JWT 解析用户，并把 socket 加入：
- user_<id>            私信房间（收发双方各一个）
- circle_<id>          其已加入圈子的群聊房间
- chat_school_<学校id>  其学校的全校群聊房间

消息发送统一走 MessageService.send：持久化成功后广播一次到目标房间；
REST 发送端点与 socket send 事件共用同一条路径。

用模块级 sid→user_id 映射（threading 模式单进程）记录连接身份，
断连时清理；同一用户可多端在线（多个 sid）。
"""
import threading

from flask import request
from flask_jwt_extended import decode_token
from flask_socketio import join_room, leave_room

from app.extensions import db, sio
from app.models import CircleMembership, School, User

_lock = threading.Lock()
_conn_user = {}  # sid -> user_id


def _auth_user(token) -> User:
    """解析 access token 并加载用户，失败返回 None。"""
    if not token:
        return None
    try:
        user_id = int(decode_token(token)['sub'])
    except Exception:
        return None
    user = db.session.get(User, user_id)
    if user is None or not user.is_active:
        return None
    return user


@sio.on('connect')
def on_connect(auth=None):
    """WebSocket 握手：校验 token，成功则订阅私信/群聊/全校群房间。"""
    token = None
    if isinstance(auth, dict):
        token = auth.get('token')
    user = _auth_user(token)
    if user is None:
        return False  # 拒绝连接

    sid = request.sid
    with _lock:
        _conn_user[sid] = user.id

    join_room(f'user_{user.id}')                    # 私信房间
    if user.school_id:
        join_room(f'chat_school_{user.school_id}')  # 全校群聊房间
    for m in CircleMembership.query.filter_by(user_id=user.id).all():
        if m.circle and m.circle.is_active:
            join_room(f'circle_{m.circle.id}')      # 已加入圈子房间
    return True


@sio.on('send')
def on_send(data):
    """实时发送消息（主发送路径）。

    data = { channel: {type, id}, content, shop_id? }。以回调返回发送结果：
    {ok: True, message} 成功；{ok: False, message} 失败（前端据此走 REST 兜底）。
    商户只能发校园群聊，其余由 MessageService.send 内统一约束。
    """
    sid = request.sid
    with _lock:
        user_id = _conn_user.get(sid)
    if not user_id:
        return {'ok': False, 'message': '未登录或连接已失效'}
    user = db.session.get(User, user_id)
    if user is None or not user.is_active:
        return {'ok': False, 'message': '账号不可用'}

    channel = (data or {}).get('channel')
    content = (data or {}).get('content')
    shop_id = (data or {}).get('shop_id')
    try:
        from app.services.message_service import MessageService
        message = MessageService.send(user, channel, content, None, shop_id)
        return {'ok': True, 'message': message}
    except Exception as exc:
        return {'ok': False, 'message': getattr(exc, 'message', str(exc) or '发送失败')}


@sio.on('circle:join')
def on_circle_join(data):
    """加入圈子成功后订阅该群房间（仅当真是成员）。"""
    sid = request.sid
    with _lock:
        user_id = _conn_user.get(sid)
    circle_id = (data or {}).get('circle_id')
    if not user_id or not circle_id:
        return {'ok': False, 'message': '参数缺失'}
    membership = CircleMembership.query.filter_by(user_id=user_id, circle_id=int(circle_id)).first()
    if membership is None:
        return {'ok': False, 'message': '请先加入圈子'}
    circle = membership.circle
    if circle is None or not circle.is_active:
        return {'ok': False, 'message': '圈子不存在或已解散'}
    join_room(f'circle_{circle.id}')
    return {'ok': True}


@sio.on('circle:leave')
def on_circle_leave(data):
    """退出圈子后取消订阅该群房间。"""
    circle_id = (data or {}).get('circle_id')
    if not circle_id:
        return {'ok': False, 'message': '参数缺失'}
    leave_room(f'circle_{int(circle_id)}')
    return {'ok': True}


@sio.on('school:join')
def on_school_join(data):
    """选择/切换学校后订阅该校群聊房间。

    connect 时只会按账号当时绑定的 school_id 加入全校群房间；
    若用户是登录后才选校/换校（新注册账号无学校），必须在此补订阅，
    否则收不到别人发的全校群聊，自己发的也无回显。
    """
    sid = request.sid
    with _lock:
        user_id = _conn_user.get(sid)
    school_id = (data or {}).get('school_id')
    if not user_id or not school_id:
        return {'ok': False, 'message': '参数缺失'}
    school = db.session.get(School, int(school_id))
    if school is None or not school.is_active:
        return {'ok': False, 'message': '学校不存在或已停用'}
    user = db.session.get(User, user_id)
    if user is None or user.school_id != school.id:
        return {'ok': False, 'message': '请先绑定到该校'}
    join_room(f'chat_school_{school.id}')
    return {'ok': True}


@sio.on('school:leave')
def on_school_leave(data):
    """离开旧学校群聊房间（仅在会话中把学校从 A 换成 B 时调用）。"""
    school_id = (data or {}).get('school_id')
    if not school_id:
        return {'ok': False, 'message': '参数缺失'}
    leave_room(f'chat_school_{int(school_id)}')
    return {'ok': True}


@sio.on('disconnect')
def on_disconnect():
    """清理连接身份（房间订阅由服务器自动回收）。"""
    sid = request.sid
    with _lock:
        _conn_user.pop(sid, None)
