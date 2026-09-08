"""消息业务逻辑：私信 / 圈子群聊 / 全校群聊 三渠道的收发与聚合。

设计约定：
- Message 表「三选一」外键区分渠道（recipient_id → dm；circle_id → circle；school_id → school）。
- 发送路径统一：服务层持久化成功后调用 sio.emit 向目标房间广播一次；
  REST 发送端点与 SocketIO send 事件共用 MessageService.send，消息不重复。
"""
import json
from datetime import datetime

from app.extensions import db, sio
from app.models import Circle, CircleMembership, Message, School, Shop, User
from app.schemas.message import MessageSchema
from app.utils.exceptions import PermissionError, ValidationError
from app.utils.pagination import paginate

_message_schema = MessageSchema()
_message_list_schema = MessageSchema(many=True)


def _get_active_user(user_id: int) -> User:
    user = db.session.get(User, user_id)
    if user is None or not user.is_active:
        from app.utils.exceptions import NotFoundError
        raise NotFoundError(message='用户不存在', code=4045)
    return user


class MessageService:
    """三渠道消息的发送、历史查询与私信会话聚合。"""

    # ---- 发送（服务层持久化 + 广播） ----
    @staticmethod
    def send(user: User, channel: dict, content: str, images: list = None, shop_id: int = None) -> dict:
        """发送一条消息并广播到对应房间。

        channel 形如 { 'type': 'dm'|'circle'|'school', 'id': <目标 id> }。
        shop_id：店铺关联标注，仅 circle / school 群聊支持；私信不接受。
        内容可为空串：仅在附带店铺时允许「纯店卡」消息。
        """
        channel_type = (channel or {}).get('type')
        target_id = (channel or {}).get('id')
        text = (content or '').strip()
        if channel_type not in ('dm', 'circle', 'school'):
            raise ValidationError(message='未知的会话类型', code=4000)

        # 商户仅可在校园群聊发言：同时约束 REST 与 socket 两条发送路径
        if user.role == 'merchant' and channel_type != 'school':
            raise PermissionError(message='商户仅可在校园群聊发言', code=4031)

        # 可选店铺关联：仅接受可公示店铺（approved + 在售），作用域在各自分支内再收敛
        shop = None
        if shop_id:
            shop = db.session.get(Shop, int(shop_id))
            if shop is None or not shop.is_active or shop.status != 'approved':
                raise ValidationError(message='关联的店铺不存在或不可用', code=4000)
        if not text and shop is None:
            raise ValidationError(message='消息内容不能为空', code=4000)

        # 三渠道各自的权限校验
        if channel_type == 'dm':
            if shop is not None:
                raise ValidationError(message='私信不支持关联店铺', code=4000)
            recipient = _get_active_user(int(target_id))
            if recipient.id == user.id:
                raise ValidationError(message='不能给自己发私信', code=4000)
            msg = Message(user_id=user.id, content=text[:1000], recipient_id=recipient.id)
        elif channel_type == 'circle':
            circle = db.session.get(Circle, int(target_id))
            if circle is None or not circle.is_active:
                raise PermissionError(message='圈子不存在或已解散', code=4047)
            member = (
                CircleMembership.query.filter_by(user_id=user.id, circle_id=circle.id).first()
            )
            if member is None:
                raise PermissionError(message='请先加入圈子再发言', code=4030)
            if shop is not None and shop.school_id != circle.school_id:
                raise PermissionError(message='仅能关联本圈店铺', code=4030)
            msg = Message(user_id=user.id, content=text[:1000], circle_id=circle.id,
                          shop_id=shop.id if shop else None)
        else:  # school
            school = db.session.get(School, int(target_id))
            if school is None or not school.is_active:
                raise PermissionError(message='学校不存在', code=4041)
            if user.school_id != school.id:
                if user.school_id is None:
                    raise ValidationError(message='请先选择学校', code=4000)
                raise PermissionError(message='仅能发送到本校群聊', code=4030)
            if shop is not None and shop.school_id != school.id:
                raise PermissionError(message='仅能关联本校店铺', code=4030)
            msg = Message(user_id=user.id, content=text[:1000], school_id=school.id,
                          shop_id=shop.id if shop else None)

        if images:
            msg.images = json.dumps(list(images)[:6], ensure_ascii=False)
        db.session.add(msg)
        db.session.commit()

        # 持久化成功后再广播（避免广播未落库消息）
        payload = {'channel': {'type': channel_type, 'id': int(target_id)},
                   'message': _message_schema.dump(msg)}
        MessageService._broadcast(user, channel_type, int(target_id), payload)
        return payload['message']

    @staticmethod
    def _broadcast(sender: User, channel_type: str, target_id: int, payload: dict) -> None:
        """按渠道把消息发到对应 SocketIO 房间（单次广播）。"""
        if channel_type == 'dm':
            sio.emit('message', payload, to=f'user_{sender.id}')
            sio.emit('message', payload, to=f'user_{target_id}')
        elif channel_type == 'circle':
            sio.emit('message', payload, to=f'circle_{target_id}')
        else:
            sio.emit('message', payload, to=f'chat_school_{target_id}')

    # ---- 圈子群聊历史 ----
    @staticmethod
    def circle_messages(circle_id: int, params: dict) -> dict:
        """某圈子群聊历史（权限由调用方校验成员身份）。"""
        query = Message.query.filter_by(circle_id=circle_id).order_by(Message.id.desc())
        before_id = params.get('before_id')
        if before_id:
            query = query.filter(Message.id < int(before_id))
        page = int(params.get('page') or 1)
        page_size = int(params.get('page_size') or 30)
        result = paginate(query, page, page_size)
        items = list(reversed(result['items']))  # 翻转回时间正序
        return {**result, 'items': _message_list_schema.dump(items)}

    # ---- 全校群聊历史 ----
    @staticmethod
    def school_messages(school_id: int, params: dict) -> dict:
        """某学校全校群聊历史。"""
        query = Message.query.filter_by(school_id=school_id).order_by(Message.id.desc())
        before_id = params.get('before_id')
        if before_id:
            query = query.filter(Message.id < int(before_id))
        page = int(params.get('page') or 1)
        page_size = int(params.get('page_size') or 30)
        result = paginate(query, page, page_size)
        items = list(reversed(result['items']))
        return {**result, 'items': _message_list_schema.dump(items)}

    # ---- 私信 ----
    @staticmethod
    def dm_messages(user: User, peer_id: int, params: dict) -> dict:
        """与某人的私信历史（双向，before_id 向上拉取）。"""
        _get_active_user(peer_id)
        query = Message.query.filter(
            db.or_(
                db.and_(Message.user_id == user.id, Message.recipient_id == peer_id),
                db.and_(Message.user_id == peer_id, Message.recipient_id == user.id),
            )
        ).order_by(Message.id.desc())
        before_id = params.get('before_id')
        if before_id:
            query = query.filter(Message.id < int(before_id))
        page = int(params.get('page') or 1)
        page_size = int(params.get('page_size') or 30)
        result = paginate(query, page, page_size)
        items = list(reversed(result['items']))
        return {**result, 'items': _message_list_schema.dump(items)}

    @staticmethod
    def conversations(user: User) -> dict:
        """我的私信会话列表：按对端聚合最近一条消息与未读数，按最近活跃倒序。"""
        rows = (
            Message.query.filter(
                db.or_(
                    Message.user_id == user.id,
                    Message.recipient_id == user.id,
                )
            )
            .order_by(Message.id.asc())
            .all()
        )
        last_by_peer = {}
        unread_by_peer = {}
        for m in rows:
            peer_id = m.user_id if m.recipient_id == user.id else m.recipient_id
            if not peer_id:
                continue
            last_by_peer[peer_id] = m  # 升序遍历，后到的覆盖成最新一条
            if m.recipient_id == user.id and m.read_at is None:
                unread_by_peer[peer_id] = unread_by_peer.get(peer_id, 0) + 1

        items = []
        if last_by_peer:
            peer_ids = list(last_by_peer.keys())
            peers = {u.id: u for u in User.query.filter(User.id.in_(peer_ids)).all()}
            for peer_id, last in sorted(last_by_peer.items(), key=lambda kv: kv[1].id, reverse=True):
                peer = peers.get(peer_id)
                if peer is None:
                    continue
                items.append({
                    'peer': {'id': peer.id, 'nickname': peer.nickname, 'avatar_url': peer.avatar_url},
                    'last_message': _message_schema.dump(last),
                    'unread_count': unread_by_peer.get(peer_id, 0),
                })
        return {'items': items, 'total': len(items)}

    @staticmethod
    def unread_count(user: User) -> dict:
        """我收到的未读私信总数（供未读徽标）。"""
        total = Message.query.filter_by(recipient_id=user.id, read_at=None).count()
        return {'total': total}

    @staticmethod
    def mark_read(user: User, peer_id: int) -> None:
        """打开与某人的会话后，把对方发给我的未读消息标记为已读。"""
        _get_active_user(peer_id)
        rows = Message.query.filter_by(recipient_id=user.id, user_id=peer_id, read_at=None).all()
        now = datetime.utcnow()
        for m in rows:
            m.read_at = now
        db.session.commit()
