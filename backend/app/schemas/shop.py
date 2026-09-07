"""店铺与评价相关 Schema。"""
from flask import g
from marshmallow import EXCLUDE, Schema, fields

from app.models import Favorite


class ShopSchema(Schema):
    """店铺列表项。"""

    id = fields.Int()
    school_id = fields.Int()
    school_name = fields.Method('_school_name')
    name = fields.Str()
    category = fields.Str()
    price_range = fields.Str()
    avg_rating = fields.Function(lambda obj: round(obj.avg_rating or 0.0, 2))
    rating_count = fields.Int()
    address = fields.Str()
    image_url = fields.Str()
    status = fields.Str()  # approved / pending / rejected

    def _school_name(self, obj) -> str:
        return getattr(obj, 'school_name', None) or (obj.school.name if obj.school else None)


class ShopCreateSchema(Schema):
    """新增店铺请求（商户 / 学生提交共用）。"""

    school_id = fields.Int(required=True)
    name = fields.Str(required=True)
    address = fields.Str(required=True)
    description = fields.Str(load_default=None)
    category = fields.Str(load_default=None)
    price_range = fields.Str(load_default=None)
    longitude = fields.Float(load_default=None)
    latitude = fields.Float(load_default=None)
    image_url = fields.Str(load_default=None)

    class Meta:
        unknown = EXCLUDE


class ShopUpdateSchema(Schema):
    """修改店铺请求。"""

    name = fields.Str()
    address = fields.Str()
    description = fields.Str()
    category = fields.Str()
    price_range = fields.Str()
    longitude = fields.Float()
    latitude = fields.Float()
    image_url = fields.Str()

    class Meta:
        unknown = EXCLUDE


class ShopDetailSchema(ShopSchema):
    """店铺详情：在列表项基础上扩展。"""

    description = fields.Str()
    longitude = fields.Float()
    latitude = fields.Float()
    created_at = fields.DateTime()
    favorited = fields.Method('_favorited')

    def _favorited(self, obj) -> bool:
        """当前登录用户是否已收藏（未登录恒为 False）。"""
        user = getattr(g, 'current_user', None)
        if user is None:
            return False
        return Favorite.query.filter_by(user_id=user.id, shop_id=obj.id).first() is not None


class ShopQuerySchema(Schema):
    """店铺列表查询参数。"""

    school_id = fields.Int()
    keyword = fields.Str()
    category = fields.Str()
    sort = fields.Str()          # 排序方式：rating / distance / newest
    longitude = fields.Float()   # 当前位置经度（距离排序用）
    latitude = fields.Float()    # 当前位置纬度
    page = fields.Int(load_default=1)
    page_size = fields.Int(load_default=10)

    class Meta:
        unknown = EXCLUDE


class ReviewSchema(Schema):
    """评价信息。"""

    id = fields.Int()
    user_id = fields.Int()
    shop_id = fields.Int()
    nickname = fields.Method('_nickname')
    avatar_url = fields.Method('_avatar')
    rating = fields.Int()
    content = fields.Str()
    images = fields.Str()
    created_at = fields.DateTime()

    def _nickname(self, obj) -> str:
        return obj.user.nickname if obj.user else None

    def _avatar(self, obj) -> str:
        return obj.user.avatar_url if obj.user else None


class ReviewCreateSchema(Schema):
    """发表评价请求。"""

    rating = fields.Int(required=True)
    content = fields.Str(required=False, load_default=None)
    images = fields.List(fields.Str())

    class Meta:
        unknown = EXCLUDE


class FavoriteSchema(Schema):
    """收藏信息。"""

    id = fields.Int()
    shop_id = fields.Int()
    created_at = fields.DateTime()
    shop = fields.Nested(ShopSchema)   # 嵌套店铺信息
