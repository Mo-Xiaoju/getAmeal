"""圈子（QQ/微信群）业务逻辑：创建、加入/退出、成员与群消息。"""
from app.extensions import db
from app.models import Circle, CircleMembership, School, User
from app.schemas.circle import CircleCreateSchema, CircleDetailSchema, CircleUpdateSchema
from app.utils.exceptions import NotFoundError, PermissionError, ValidationError
from app.utils.pagination import paginate

_circle_schema = CircleDetailSchema()
_circle_list_schema = CircleDetailSchema(many=True)


def _get_active_circle(circle_id: int) -> Circle:
    """按 id 取启用中的圈子，不存在则抛 4047。"""
    circle = db.session.get(Circle, circle_id)
    if circle is None or not circle.is_active:
        raise NotFoundError(message='圈子不存在', code=4047)
    return circle


def _get_active_school(school_id: int) -> School:
    school = db.session.get(School, school_id)
    if school is None or not school.is_active:
        raise NotFoundError(message='学校不存在', code=4041)
    return school


def _is_member(user: User, circle: Circle) -> bool:
    return (
        CircleMembership.query.filter_by(user_id=user.id, circle_id=circle.id).first() is not None
    )


def _require_member(user: User, circle: Circle) -> None:
    """校验用户已是圈子成员（群聊历史/发言仅成员可见）。"""
    if not _is_member(user, circle):
        raise PermissionError(message='请先加入圈子', code=4030)


def _user_brief(user: User) -> dict:
    return {'id': user.id, 'nickname': user.nickname, 'avatar_url': user.avatar_url}


class CircleService:
    """圈子的查询、创建、改删与入会等业务。"""

    # ---- 查询 ----
    @staticmethod
    def list(params: dict) -> dict:
        """按学校浏览圈子：school_id 必填 + keyword 过滤，分页。"""
        school_id = params.get('school_id')
        if not school_id:
            raise ValidationError(message='缺少学校参数', code=4000)
        _get_active_school(int(school_id))

        query = Circle.query.filter_by(school_id=int(school_id), is_active=True)
        keyword = (params.get('keyword') or '').strip()
        if keyword:
            query = query.filter(Circle.name.like(f'%{keyword}%'))
        query = query.order_by(Circle.member_count.desc(), Circle.id.desc())

        page = int(params.get('page') or 1)
        page_size = int(params.get('page_size') or 10)
        result = paginate(query, page, page_size)
        return {**result, 'items': _circle_list_schema.dump(result['items'])}

    @staticmethod
    def joined(user: User, params: dict) -> dict:
        """我加入的圈子（分页）。"""
        page = int(params.get('page') or 1)
        page_size = int(params.get('page_size') or 10)
        query = (
            CircleMembership.query.filter_by(user_id=user.id)
            .join(Circle, Circle.id == CircleMembership.circle_id)
            .filter(Circle.is_active.is_(True))
            .order_by(CircleMembership.id.desc())
        )
        result = paginate(query, page, page_size)
        circles = [m.circle for m in result['items']]
        return {**result, 'items': _circle_list_schema.dump(circles)}

    @staticmethod
    def get_detail(circle_id: int) -> dict:
        """圈子详情（带当前用户 joined 状态）。"""
        return _circle_schema.dump(_get_active_circle(circle_id))

    @staticmethod
    def members(circle_id: int, params: dict) -> dict:
        """圈子成员列表（分页）。"""
        _get_active_circle(circle_id)
        page = int(params.get('page') or 1)
        page_size = int(params.get('page_size') or 30)
        query = (
            CircleMembership.query.filter_by(circle_id=circle_id)
            .join(User, User.id == CircleMembership.user_id)
            .filter(User.is_active.is_(True))
            .order_by(CircleMembership.id.asc())
        )
        result = paginate(query, page, page_size)
        return {**result, 'items': [_user_brief(m.user) for m in result['items']]}

    # ---- 创建 / 改删 ----
    @staticmethod
    def create(user: User, data: dict) -> dict:
        """创建圈子并让创建者自动成为成员。"""
        data = CircleCreateSchema().load(data)
        school = _get_active_school(int(data['school_id']))
        name = (data.get('name') or '').strip()
        if not name:
            raise ValidationError(message='圈子名称不能为空', code=4000)

        circle = Circle(
            school_id=school.id,
            creator_id=user.id,
            name=name[:60],
            cover_url=(data.get('cover_url') or '').strip()[:255] or None,
            description=(data.get('description') or '').strip()[:500] or None,
            member_count=1,
        )
        db.session.add(circle)
        db.session.flush()
        db.session.add(CircleMembership(circle_id=circle.id, user_id=user.id))
        db.session.commit()
        return _circle_schema.dump(circle)

    @staticmethod
    def update(user: User, circle_id: int, data: dict) -> dict:
        """更新自己的圈子（名称/封面/简介）。"""
        circle = _get_active_circle(circle_id)
        if circle.creator_id != user.id and user.role != 'admin':
            raise PermissionError(message='仅圈子创建者可编辑', code=4030)

        data = CircleUpdateSchema().load(data)
        if data.get('name') is not None:
            name = data['name'].strip()
            if not name:
                raise ValidationError(message='圈子名称不能为空', code=4000)
            circle.name = name[:60]
        if data.get('cover_url') is not None:
            circle.cover_url = data['cover_url'].strip()[:255] or None
        if data.get('description') is not None:
            circle.description = data['description'].strip()[:500] or None
        db.session.commit()
        return _circle_schema.dump(circle)

    @staticmethod
    def delete(user: User, circle_id: int) -> None:
        """解散自己的圈子（软删除，成员关系保留作废）。"""
        circle = _get_active_circle(circle_id)
        if circle.creator_id != user.id and user.role != 'admin':
            raise PermissionError(message='仅圈子创建者可解散', code=4030)
        circle.is_active = False
        db.session.commit()

    # ---- 加入 / 退出 ----
    @staticmethod
    def toggle_join(user: User, circle_id: int) -> dict:
        """加入/退出圈子（幂等），返回 { joined, member_count }。

        圈子按学校隔离：仅允许加入自己学校下的圈子。
        """
        circle = _get_active_circle(circle_id)
        if user.school_id != circle.school_id:
            if user.school_id is None:
                raise ValidationError(message='请先在个人中心选择学校', code=4000)
            raise PermissionError(message='圈子仅限本校同学加入', code=4030)

        membership = CircleMembership.query.filter_by(user_id=user.id, circle_id=circle.id).first()
        if membership:
            db.session.delete(membership)
            circle.member_count = max(circle.member_count - 1, 0)
            joined = False
        else:
            db.session.add(CircleMembership(circle_id=circle.id, user_id=user.id))
            circle.member_count += 1
            joined = True
        db.session.commit()
        return {'joined': joined, 'member_count': circle.member_count}

    # ---- 圈内群消息 ----
    @staticmethod
    def list_messages(circle_id: int, user: User, params: dict) -> dict:
        """圈子群聊历史（仅成员可见，before_id 向上拉取）。"""
        circle = _get_active_circle(circle_id)
        _require_member(user, circle)
        from app.services.message_service import MessageService
        return MessageService.circle_messages(circle.id, params)
