"""管理后台业务逻辑。"""
from app.categories import coerce_category
from app.extensions import db
from app.models import School, Shop, User
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

    @staticmethod
    def reclassify_shop_category(shop_id: int, category) -> dict:
        """管理员归类店铺分类（任意状态均可，含已过审的历史脏值）。

        category 经 coerce_category 强制落规范分类；传空则清空分类。
        """
        shop = db.session.get(Shop, shop_id)
        if shop is None or not shop.is_active:
            raise NotFoundError(message='店铺不存在', code=4040)
        shop.category = coerce_category(category)
        db.session.commit()
        return {'id': shop.id, 'name': shop.name, 'category': shop.category}
