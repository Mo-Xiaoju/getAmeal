"""管理后台业务逻辑。"""

import json
from datetime import datetime, timedelta

from sqlalchemy import case, func

from app.extensions import db
from app.models import Dish, EventLog, School, Shop, User
from app.services.event_log_service import EventLogService
from app.utils.exceptions import NotFoundError, ValidationError
from app.utils.pagination import paginate

# 管理员可授予的角色：student 学生 | merchant 商户 | admin 管理员
ADMIN_ROLES = ('student', 'merchant', 'admin')


def _user_admin_view(user: User) -> dict:
    """管理员视角的用户信息。"""
    return {
        'id': user.id,
        'username': user.username,
        'nickname': user.nickname,
        'avatar_url': user.avatar_url,
        'role': user.role,
        'school_name': user.school.name if user.school else None,
        'is_active': user.is_active,
        'created_at': user.created_at.isoformat() if user.created_at else None,
    }


def _shop_admin_view(shop: Shop) -> dict:
    """管理员视角的店铺信息。"""
    return {
        'id': shop.id,
        'school_id': shop.school_id,
        'school_name': shop.school_name,
        'name': shop.name,
        'description': shop.description,
        'address': shop.address,
        'longitude': shop.longitude,
        'latitude': shop.latitude,
        'category': shop.category,
        'price_range': shop.price_range,
        'avg_rating': round(shop.avg_rating or 0.0, 2),
        'rating_count': shop.rating_count,
        'image_url': shop.image_url,
        'is_active': shop.is_active,
        'status': shop.status,
        'owner_id': shop.owner_id,
        'created_at': shop.created_at.isoformat() if shop.created_at else None,
    }


class AdminService:
    """管理后台业务。"""

    # ---- 用户管理 ----
    @staticmethod
    def list_users(params: dict) -> dict:
        """用户列表（分页）。"""
        query = User.query.order_by(User.id.desc())
        page = int(params.get('page') or 1)
        page_size = int(params.get('page_size') or 10)
        result = paginate(query, page, page_size)
        return {**result, 'items': [_user_admin_view(u) for u in result['items']]}

    @staticmethod
    def update_user(admin, user_id: int, data: dict) -> dict:
        """变更用户角色 / 停用启封。禁止管理员修改自己。"""
        user = db.session.get(User, user_id)
        if user is None:
            raise NotFoundError(message='用户不存在', code=4045)
        if user.id == admin.id:
            raise ValidationError(message='不能修改自己的角色或状态', code=4000)

        role = data.get('role')
        if role is not None:
            if role not in ADMIN_ROLES:
                raise ValidationError(message=f'角色必须为 {" / ".join(ADMIN_ROLES)} 之一', code=4000)
            user.role = role
        if 'is_active' in data:
            user.is_active = bool(data['is_active'])
        db.session.commit()
        return _user_admin_view(user)

    # ---- 店铺管理 ----
    @staticmethod
    def list_shops(params: dict) -> dict:
        """店铺管理列表（分页，支持 school_id / keyword 筛选）。"""
        query = Shop.query.order_by(Shop.id.desc())

        school_id = params.get('school_id')
        if school_id:
            query = query.filter(Shop.school_id == int(school_id))

        keyword = (params.get('keyword') or '').strip()
        if keyword:
            query = query.filter(Shop.name.like(f'%{keyword}%'))

        page = int(params.get('page') or 1)
        page_size = int(params.get('page_size') or 10)
        result = paginate(query, page, page_size)
        return {**result, 'items': [_shop_admin_view(s) for s in result['items']]}

    @staticmethod
    def add_shop(data: dict) -> dict:
        """管理员新增店铺。"""
        school_id = data.get('school_id')
        if not school_id:
            raise ValidationError(message='必须指定学校', code=4000)
        school = db.session.get(School, int(school_id))
        if school is None:
            raise NotFoundError(message='学校不存在', code=4041)

        name = (data.get('name') or '').strip()
        if not name:
            raise ValidationError(message='店铺名称不能为空', code=4000)
        if Shop.query.filter_by(name=name).first():
            raise ValidationError(message='店铺名称已存在', code=4000)

        shop = Shop(
            school_id=school.id,
            name=name,
            address=(data.get('address') or '').strip() or '待定',
            description=(data.get('description') or '').strip() or None,
            category=(data.get('category') or '').strip() or None,
            price_range=(data.get('price_range') or '').strip() or None,
            longitude=data.get('longitude'),
            latitude=data.get('latitude'),
            image_url=(data.get('image_url') or '').strip() or None,
        )
        db.session.add(shop)
        db.session.commit()
        return _shop_admin_view(shop)

    @staticmethod
    def update_shop(shop_id: int, data: dict) -> dict:
        """修改店铺信息。"""
        shop = db.session.get(Shop, shop_id)
        if shop is None:
            raise NotFoundError(message='店铺不存在', code=4040)

        if 'name' in data:
            name = data['name'].strip()
            if not name:
                raise ValidationError(message='店铺名称不能为空', code=4000)
            existing = Shop.query.filter(Shop.name == name, Shop.id != shop_id).first()
            if existing:
                raise ValidationError(message='店铺名称已存在', code=4000)
            shop.name = name

        for field in ('address', 'description', 'category', 'price_range', 'image_url'):
            if field in data:
                val = data[field]
                setattr(shop, field, val.strip() if isinstance(val, str) else val)

        for field in ('longitude', 'latitude'):
            if field in data:
                setattr(shop, field, data[field])

        if 'is_active' in data:
            shop.is_active = bool(data['is_active'])
        if 'status' in data:
            shop.status = data['status']

        db.session.commit()
        return _shop_admin_view(shop)

    @staticmethod
    def delete_shop(shop_id: int) -> dict:
        """删除/下架店铺（软删除）。"""
        shop = db.session.get(Shop, shop_id)
        if shop is None:
            raise NotFoundError(message='店铺不存在', code=4040)
        shop.is_active = False
        db.session.commit()
        return _shop_admin_view(shop)

    # ---- 内容审核 ----
    @staticmethod
    def list_audit_shops(params: dict) -> dict:
        """待审店铺列表（含该店全部待审菜品）。"""
        query = Shop.query.filter(Shop.status == 'pending').order_by(Shop.id.desc())
        page = int(params.get('page') or 1)
        page_size = int(params.get('page_size') or 10)
        result = paginate(query, page, page_size)

        def _audit_shop_view(shop: Shop) -> dict:
            view = _shop_admin_view(shop)
            view['submitter'] = {
                'id': shop.owner.id,
                'nickname': shop.owner.nickname,
                'school_name': shop.owner.school.name if shop.owner.school else None,
            } if shop.owner else None
            view['pending_dishes'] = [
                {
                    'id': d.id,
                    'name': d.name,
                    'price': float(d.price),
                    'submitter': {
                        'id': d.owner.id,
                        'nickname': d.owner.nickname,
                    } if d.owner else None,
                }
                for d in shop.dishes.filter(Dish.status == 'pending').all()
            ]
            return view

        return {**result, 'items': [_audit_shop_view(s) for s in result['items']]}

    @staticmethod
    def list_audit_dishes(params: dict) -> dict:
        """待审菜品列表（父店已通过的逐条审核）。"""
        query = Dish.query.join(Shop).filter(
            Dish.status == 'pending',
            Shop.status == 'approved'
        ).order_by(Dish.id.desc())

        page = int(params.get('page') or 1)
        page_size = int(params.get('page_size') or 10)
        result = paginate(query, page, page_size)

        def _audit_dish_view(dish: Dish) -> dict:
            return {
                'id': dish.id,
                'name': dish.name,
                'price': float(dish.price),
                'shop_id': dish.shop_id,
                'shop_name': dish.shop.name if dish.shop else None,
                'submitter': {
                    'id': dish.owner.id,
                    'nickname': dish.owner.nickname,
                } if dish.owner else None,
                'created_at': dish.created_at.isoformat() if dish.created_at else None,
            }

        return {**result, 'items': [_audit_dish_view(d) for d in result['items']]}

    @staticmethod
    def _do_review(entity, admin, action: str, reason: str = None):
        """通用审核逻辑。"""
        if action not in ('approve', 'reject'):
            raise ValidationError(message='action 必须为 approve 或 reject', code=4000)
        entity.status = 'approved' if action == 'approve' else 'rejected'
        entity.reviewed_by = admin.id
        entity.reviewed_at = datetime.utcnow()
        entity.reject_reason = reason if action == 'reject' else None

        # 埋点：店铺 / 菜品 审核通过或驳回（单店/整店/单菜品审核都汇聚于此）
        target_type = 'shop' if isinstance(entity, Shop) else 'dish'
        school_id = entity.school_id if target_type == 'shop' else (
            entity.shop.school_id if entity.shop else None
        )
        EventLogService.record(
            admin, f'{target_type}_{action}',
            target_type=target_type, target_id=entity.id, school_id=school_id,
            extra={'name': entity.name, 'reason': reason} if reason else {'name': entity.name},
        )

    @staticmethod
    def review_shop(admin, shop_id: int, data: dict) -> dict:
        """单店审核（通过 / 驳回）。"""
        shop = db.session.get(Shop, shop_id)
        if shop is None:
            raise NotFoundError(message='店铺不存在', code=4040)
        if shop.status != 'pending':
            raise ValidationError(message='该店铺不在待审核状态', code=4000)

        action = data.get('action')
        reason = data.get('reason')
        AdminService._do_review(shop, admin, action, reason)
        db.session.commit()
        return _shop_admin_view(shop)

    @staticmethod
    def bulk_review_shop(admin, shop_id: int, data: dict) -> dict:
        """整店审核：店铺与其全部待审菜品一并通过/驳回。"""
        shop = db.session.get(Shop, shop_id)
        if shop is None:
            raise NotFoundError(message='店铺不存在', code=4040)

        action = data.get('action')
        reason = data.get('reason')

        AdminService._do_review(shop, admin, action, reason)

        affected = 0
        for dish in shop.dishes.filter(Dish.status == 'pending').all():
            AdminService._do_review(dish, admin, action, reason)
            affected += 1

        db.session.commit()
        view = _shop_admin_view(shop)
        view['affected_dishes'] = affected
        return view

    @staticmethod
    def review_dish(admin, dish_id: int, data: dict) -> dict:
        """单菜品审核（通过 / 驳回）。"""
        dish = db.session.get(Dish, dish_id)
        if dish is None:
            raise NotFoundError(message='菜品不存在', code=4040)
        if dish.status != 'pending':
            raise ValidationError(message='该菜品不在待审核状态', code=4000)

        action = data.get('action')
        reason = data.get('reason')
        AdminService._do_review(dish, admin, action, reason)
        db.session.commit()
        return {
            'id': dish.id,
            'name': dish.name,
            'status': dish.status,
        }

    # ---- 数据统计（埋点看板） ----
    @staticmethod
    def get_stats(params: dict) -> dict:
        """数据统计看板聚合数据：概览 + 近 N 天趋势 + 类型/学校分布。"""
        days = int(params.get('days') or 14)
        days = max(min(days, 90), 1)
        since = datetime.utcnow() - timedelta(days=days)

        submit_types = ('shop_submit', 'dish_submit')
        approve_types = ('shop_approve', 'dish_approve')
        reject_types = ('shop_reject', 'dish_reject')

        # 概览：存量 + 事件计数 + 通过率
        total_submits = EventLog.query.filter(EventLog.event_type.in_(submit_types)).count()
        total_approves = EventLog.query.filter(EventLog.event_type.in_(approve_types)).count()
        total_rejects = EventLog.query.filter(EventLog.event_type.in_(reject_types)).count()
        reviewed = total_approves + total_rejects
        summary = {
            'total_users': User.query.count(),
            'total_shops': Shop.query.count(),
            'total_dishes': Dish.query.count(),
            'total_events': EventLog.query.count(),
            'total_submits': total_submits,
            'total_approves': total_approves,
            'total_rejects': total_rejects,
            'approval_rate': round(total_approves / reviewed, 4) if reviewed else 0.0,
        }

        # 趋势：近 N 天按天聚合
        trend_rows = (
            db.session.query(
                func.date(EventLog.created_at).label('day'),
                func.sum(case((EventLog.event_type.in_(submit_types), 1), else_=0)).label('submits'),
                func.sum(case((EventLog.event_type.in_(approve_types), 1), else_=0)).label('approves'),
                func.sum(case((EventLog.event_type.in_(reject_types), 1), else_=0)).label('rejects'),
            )
            .filter(EventLog.created_at >= since)
            .group_by(func.date(EventLog.created_at))
            .all()
        )
        by_day = {
            str(r.day): {
                'submits': int(r.submits or 0),
                'approves': int(r.approves or 0),
                'rejects': int(r.rejects or 0),
            }
            for r in trend_rows
        }
        today = datetime.utcnow().date()
        trend = []
        for i in range(days - 1, -1, -1):
            d = (today - timedelta(days=i)).isoformat()
            trend.append({'date': d, **by_day.get(d, {'submits': 0, 'approves': 0, 'rejects': 0})})

        # 按事件类型分布
        by_type = [
            {'event_type': et, 'count': c}
            for et, c in (
                db.session.query(EventLog.event_type, func.count(EventLog.id))
                .group_by(EventLog.event_type)
                .order_by(func.count(EventLog.id).desc())
                .all()
            )
        ]

        # 按学校分布
        by_school = [
            {'school_id': sid, 'name': name, 'count': c}
            for sid, name, c in (
                db.session.query(EventLog.school_id, School.name, func.count(EventLog.id))
                .join(School, School.id == EventLog.school_id)
                .group_by(EventLog.school_id, School.name)
                .order_by(func.count(EventLog.id).desc())
                .all()
            )
        ]

        return {
            'summary': summary,
            'trend': trend,
            'by_type': by_type,
            'by_school': by_school,
        }

    @staticmethod
    def list_events(params: dict) -> dict:
        """事件明细列表（分页，可按 event_type 过滤）。"""
        query = EventLog.query.order_by(EventLog.id.desc())
        event_type = (params.get('event_type') or '').strip()
        if event_type:
            query = query.filter(EventLog.event_type == event_type)
        page = int(params.get('page') or 1)
        page_size = int(params.get('page_size') or 20)
        result = paginate(query, page, page_size)
        return {**result, 'items': [AdminService._event_view(e) for e in result['items']]}

    @staticmethod
    def _event_view(log: EventLog) -> dict:
        """事件日志序列化。"""
        extra = None
        if log.extra:
            try:
                extra = json.loads(log.extra)
            except (ValueError, TypeError):
                extra = log.extra
        return {
            'id': log.id,
            'actor_id': log.actor_id,
            'actor_role': log.actor_role,
            'actor_nickname': log.actor.nickname if log.actor else None,
            'event_type': log.event_type,
            'target_type': log.target_type,
            'target_id': log.target_id,
            'school_id': log.school_id,
            'school_name': log.school.name if log.school else None,
            'extra': extra,
            'created_at': log.created_at.isoformat() if log.created_at else None,
        }
