"""管理后台业务逻辑。"""
from app.extensions import db
from app.models import User
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


class AdminService:
    """管理后台业务。"""

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
