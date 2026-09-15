"""店铺认领业务：商户提交认领申请，管理员审核通过后转移店铺归属。

为什么单独成服务而不是塞进 merchant_service / admin_service：
认领天然横跨商户侧（申请）与管理侧（审核）。塞进任一边都会逼另一边重复实现
「什么样的店可认领」这条判定——本仓库已经因为同类重复产出过一份完全死掉的
audit_service.py。这里把认领逻辑集中一处，routes/merchant.py 与 routes/admin.py 共用。

与内容审核（Shop.status）的关系：认领只决定店铺归属（owner_id），
审核认领申请**绝不改动** shop.status / shop.is_active，否则一次归属权审批
会连带把店铺从公开列表下架。
"""
from datetime import datetime

from sqlalchemy import and_, or_

from app.extensions import db
from app.models import Shop, ShopClaim, User
from app.schemas.shop import ShopSchema
from app.services.event_log_service import EventLogService
from app.utils.exceptions import NotFoundError, PermissionError, ValidationError
from app.utils.pagination import paginate

_shop_schema = ShopSchema()

#: 认领申请的审核状态
CLAIM_STATUSES = ('pending', 'approved', 'rejected')

#: 同一店铺被通过后，其余待审申请的驳回原因
_LOST_RACE_REASON = '店铺已被其他商户认领'

#: 通过认领时，复验失败的原因码 → 面向管理员的话术
_APPROVE_ISSUE_MESSAGES = {
    'not_found': '店铺不存在或已下架，无法通过',
    'not_public': '店铺当前不在公开状态，无法通过认领',
    'already_owned': '该店铺已是该商户的店铺',
    'occupied': '该店铺已有商户入驻，无法通过该申请',
}


def _claimable_query(user_id: int):
    """可认领店铺的基础查询：已公开（approved、未下架）且尚未被商户入驻。

    范围：owner 为空（管理员种子店）或 owner 非商户角色（学生代提交）的店铺；
    本人名下的店铺天然不在列。
    判定与 _claimability_issue 等价——两者必须同步修改。
    """
    return (
        Shop.query.outerjoin(User, User.id == Shop.owner_id)
        .filter(
            Shop.is_active.is_(True),
            Shop.status == 'approved',
            # 注意 SQL 中 owner_id != user 对 NULL 不成立，须显式放行 owner_id IS NULL。
            or_(
                Shop.owner_id.is_(None),
                and_(Shop.owner_id != user_id, User.role != 'merchant'),
            ),
        )
    )


def _claimability_issue(shop, user_id: int):
    """店铺不可认领的原因码；可认领返回 None。

    逻辑与 _claimable_query 等价——两者必须同步修改。
    返回原因码而非文案，是为了让申请侧与审核侧各自给出面向自己读者的话术。
    """
    if shop is None or not shop.is_active:
        return 'not_found'
    if shop.status != 'approved':
        return 'not_public'
    if shop.owner_id == user_id:
        return 'already_owned'
    owner = getattr(shop, 'owner', None)
    if shop.owner_id is not None and owner is not None and owner.role == 'merchant':
        return 'occupied'
    return None


def _merchant_view(claim: ShopClaim) -> dict:
    """商户视角的申请记录（含店铺摘要）。"""
    shop = claim.shop
    return {
        'id': claim.id,
        'status': claim.status,
        'reason': claim.reason,
        'review_reason': claim.review_reason,
        'created_at': claim.created_at.isoformat() if claim.created_at else None,
        'reviewed_at': claim.reviewed_at.isoformat() if claim.reviewed_at else None,
        'shop': {
            'id': shop.id,
            'name': shop.name,
            'address': shop.address,
            'image_url': shop.image_url,
            'owner_id': shop.owner_id,
        } if shop else None,
    }


def _admin_view(claim: ShopClaim) -> dict:
    """管理员视角的申请记录（含申请人与店铺详情，供审核决策）。"""
    shop = claim.shop
    applicant = claim.applicant
    owner = shop.owner if shop else None
    pending_count = 0
    if shop:
        pending_count = ShopClaim.query.filter(
            ShopClaim.shop_id == shop.id, ShopClaim.status == 'pending'
        ).count()
    return {
        'id': claim.id,
        'status': claim.status,
        'reason': claim.reason,
        'review_reason': claim.review_reason,
        'created_at': claim.created_at.isoformat() if claim.created_at else None,
        'applicant': {
            'id': applicant.id,
            'nickname': applicant.nickname,
            'school_name': applicant.school.name if applicant.school else None,
        } if applicant else None,
        'shop': {
            'id': shop.id,
            'name': shop.name,
            'address': shop.address,
            'category': shop.category,
            'image_url': shop.image_url,
            'owner_id': shop.owner_id,
            'owner_nickname': owner.nickname if owner else None,
        } if shop else None,
        # 该店当前有几份待审申请：让管理员知道自己是在几个申请人之间做选择
        'pending_claim_count': pending_count,
    }


class ClaimService:
    """店铺认领申请：商户提交 / 撤回 / 查看，管理员审核。"""

    # ---- 商户侧 ----
    @staticmethod
    def list_claimable(user, params: dict) -> dict:
        """列出当前商户可认领的店铺，并标注本人申请状态与他人竞争情况。

        可用 school_id 限定当前学校，keyword 按店名模糊筛选（与 admin_service.list_shops 同款）。
        """
        query = _claimable_query(user.id).order_by(Shop.id.desc())
        school_id = params.get('school_id')
        if school_id:
            try:
                query = query.filter(Shop.school_id == int(school_id))
            except (TypeError, ValueError):
                pass  # 非法 school_id 视为不限定
        keyword = (params.get('keyword') or '').strip()
        if keyword:
            query = query.filter(Shop.name.like(f'%{keyword}%'))
        page = int(params.get('page') or 1)
        page_size = int(params.get('page_size') or 10)
        result = paginate(query, page, page_size)
        shops = result['items']

        # 一次性取回本页店铺的申请情况，避免逐店查询
        shop_ids = [s.id for s in shops]
        my_status = {}
        pending_count = {}
        if shop_ids:
            for claim in (
                ShopClaim.query.filter(
                    ShopClaim.shop_id.in_(shop_ids), ShopClaim.applicant_id == user.id
                ).order_by(ShopClaim.id.asc()).all()
            ):
                my_status[claim.shop_id] = claim.status  # 升序遍历，后者覆盖为最新一条
            for shop_id, count in (
                db.session.query(ShopClaim.shop_id, db.func.count(ShopClaim.id))
                .filter(
                    ShopClaim.shop_id.in_(shop_ids),
                    ShopClaim.status == 'pending',
                    ShopClaim.applicant_id != user.id,
                )
                .group_by(ShopClaim.shop_id)
                .all()
            ):
                pending_count[shop_id] = int(count)

        items = []
        for shop in shops:
            item = _shop_schema.dump(shop)
            item['dish_count'] = shop.dishes.filter_by(is_active=True).count()
            item['my_claim_status'] = my_status.get(shop.id)
            item['pending_claim_count'] = pending_count.get(shop.id, 0)
            items.append(item)
        return {**result, 'items': items}

    @staticmethod
    def apply(user, shop_id: int, data: dict) -> dict:
        """提交认领申请（待管理员审核，不立即转移归属）。"""
        shop = db.session.get(Shop, shop_id)
        issue = _claimability_issue(shop, user.id)
        if issue == 'not_found':
            raise NotFoundError(message='店铺不存在', code=4040)
        if issue == 'not_public':
            raise ValidationError(message='仅可认领已公开（审核通过）的店铺', code=4000)
        if issue == 'already_owned':
            raise ValidationError(message='该店铺已是你的店铺，无需认领', code=4000)
        if issue == 'occupied':
            raise ValidationError(message='该店铺已有商户入驻，无需认领', code=4000)

        # 同一商户对同一店铺只允许一份待审申请
        existing = ShopClaim.query.filter_by(
            shop_id=shop_id, applicant_id=user.id, status='pending'
        ).first()
        if existing is not None:
            raise ValidationError(message='你已提交过该店铺的认领申请，请等待审核', code=4000)

        reason = (data.get('reason') or '').strip()[:500] or None
        claim = ShopClaim(shop_id=shop_id, applicant_id=user.id, status='pending', reason=reason)
        db.session.add(claim)
        try:
            db.session.flush()  # 拿到 claim.id 供埋点
            EventLogService.record(user, 'shop_claim_submit',
                                   target_type='claim', target_id=claim.id,
                                   school_id=shop.school_id,
                                   extra={'shop_id': shop.id, 'shop_name': shop.name})
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        return _merchant_view(claim)

    @staticmethod
    def list_mine(user, params: dict) -> dict:
        """我的认领申请列表（分页）。"""
        query = ShopClaim.query.filter_by(applicant_id=user.id).order_by(ShopClaim.id.desc())
        page = int(params.get('page') or 1)
        page_size = int(params.get('page_size') or 10)
        result = paginate(query, page, page_size)
        return {**result, 'items': [_merchant_view(c) for c in result['items']]}

    @staticmethod
    def cancel(user, claim_id: int) -> None:
        """撤回自己的待审申请（仅本人 + 仅待审；已审核的记录不可撤回）。"""
        claim = db.session.get(ShopClaim, claim_id)
        if claim is None:
            raise NotFoundError(message='认领申请不存在', code=4048)
        if claim.applicant_id != user.id:
            raise PermissionError(message='无权操作该申请', code=4032)
        if claim.status != 'pending':
            raise ValidationError(message='该申请已审核，无法撤回', code=4000)
        db.session.delete(claim)
        db.session.commit()

    # ---- 管理员侧 ----
    @staticmethod
    def list_for_admin(params: dict) -> dict:
        """认领申请审核队列（status 默认 pending）。"""
        status = params.get('status') or 'pending'
        if status not in CLAIM_STATUSES:
            status = 'pending'
        query = (
            ShopClaim.query.filter(ShopClaim.status == status)
            .order_by(ShopClaim.id.desc())
        )
        page = int(params.get('page') or 1)
        page_size = int(params.get('page_size') or 10)
        result = paginate(query, page, page_size)
        return {**result, 'items': [_admin_view(c) for c in result['items']]}

    @staticmethod
    def review(admin, claim_id: int, data: dict) -> dict:
        """审核认领申请：通过则把店铺归属转给申请人，并连带驳回同店其余待审申请。"""
        claim = db.session.get(ShopClaim, claim_id)
        if claim is None:
            raise NotFoundError(message='认领申请不存在', code=4048)
        if claim.status != 'pending':
            raise ValidationError(message='该认领申请已处理', code=4000)

        action = data.get('action')
        if action not in ('approve', 'reject'):
            raise ValidationError(message='action 必须为 approve 或 reject', code=4000)

        if action == 'approve':
            losers = ClaimService._approve(claim, admin)
        else:
            losers = []
            reason = (data.get('reason') or '').strip()[:500] or '未通过审核'
            ClaimService._apply_review(claim, admin, 'reject', reason)

        db.session.commit()

        # 通知在事务提交之后发出（沿用仓库「持久化成功后再广播」的约定）
        ClaimService._notify(claim, action)
        for loser in losers:
            ClaimService._notify(loser, 'reject')

        return _admin_view(claim)

    @staticmethod
    def _approve(claim: ShopClaim, admin) -> list:
        """通过认领：加锁复验店铺仍可认领，再转移归属。返回被连带驳回的申请。"""
        # 行锁：两个管理员同时对同一家店的两份竞争申请点通过时，
        # 后者必须阻塞到前者提交，再复验失败而中止，而不是把店抢走。
        shop = (
            db.session.query(Shop)
            .filter(Shop.id == claim.shop_id)
            .with_for_update()
            .first()
        )
        issue = _claimability_issue(shop, claim.applicant_id)
        # already_owned / occupied 也在此拦下：前者是重复通过，后者是竞争申请已被抢先满足
        if issue is not None:
            raise ValidationError(message=_APPROVE_ISSUE_MESSAGES[issue], code=4000)

        shop.owner_id = claim.applicant_id
        ClaimService._apply_review(claim, admin, 'approve', None)

        # 同店其余待审申请一并驳回：店铺已被认领，它们已无成立可能
        losers = ShopClaim.query.filter(
            ShopClaim.shop_id == claim.shop_id,
            ShopClaim.status == 'pending',
            ShopClaim.id != claim.id,
        ).all()
        for loser in losers:
            ClaimService._apply_review(loser, admin, 'reject', _LOST_RACE_REASON)
        return losers

    @staticmethod
    def _apply_review(claim: ShopClaim, admin, action: str, reason: str) -> None:
        """写入审核结果并埋点（不 commit，由调用方统一提交）。"""
        claim.status = 'approved' if action == 'approve' else 'rejected'
        claim.review_reason = reason if action == 'reject' else None
        claim.reviewed_by = admin.id
        claim.reviewed_at = datetime.utcnow()

        shop = claim.shop
        EventLogService.record(
            admin, f'shop_claim_{action}',
            target_type='claim', target_id=claim.id,
            school_id=shop.school_id if shop else None,
            extra={'shop_id': claim.shop_id, 'shop_name': shop.name if shop else None,
                   'applicant_id': claim.applicant_id, 'reason': reason},
        )

    @staticmethod
    def _notify(claim: ShopClaim, action: str) -> None:
        """把审核结果通过站内消息告知申请人（失败不影响审核结果）。"""
        from app.services.message_service import MessageService

        shop_name = claim.shop.name if claim.shop else '该店铺'
        if action == 'approve':
            content = f'你认领的店铺「{shop_name}」已通过审核，现在可以在商户中心管理它了。'
        else:
            content = f'你对店铺「{shop_name}」的认领申请未通过：{claim.review_reason or "未通过审核"}'
        MessageService.send_system_notice(claim.applicant, content)
