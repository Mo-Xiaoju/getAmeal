"""店铺与评价相关 Schema。"""
import json

from flask import g
from marshmallow import EXCLUDE, Schema, fields, pre_load, validate

from app.models import Favorite
from app.schemas.comment import CommentSchema
from app.schemas.interaction import liked_review_ids, reply_preview

_reply_list_schema = CommentSchema(many=True)


class ShopSchema(Schema):
    """店铺列表项。"""

    id = fields.Int()
    school_id = fields.Int()
    school_name = fields.Method('_school_name')
    name = fields.Str()
    category = fields.Str()
    zone = fields.Str()  # 大分类：校内 / 周边 / 外卖；空表示未设置，前端不渲染角标
    price_range = fields.Str()
    avg_rating = fields.Function(lambda obj: round(obj.avg_rating or 0.0, 2))
    rating_count = fields.Int()
    address = fields.Str()
    image_url = fields.Str()
    status = fields.Str()  # approved / pending / rejected
    reject_reason = fields.Str()  # 驳回原因（仅供提交者/审核端回显）

    def _school_name(self, obj) -> str:
        return getattr(obj, 'school_name', None) or (obj.school.name if obj.school else None)


class ShopCreateSchema(Schema):
    """新增店铺请求（商户 / 学生提交共用）。"""

    school_id = fields.Int(required=True)
    name = fields.Str(required=True)
    address = fields.Str(required=True)
    description = fields.Str(load_default=None)
    category = fields.Str(load_default=None)
    zone = fields.Str(load_default=None)  # 落库前经 coerce_zone 校验，非词表值报 400
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
    zone = fields.Str()
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
    owner_id = fields.Int()  # 店铺归属（前端据此判定是否展示管理按钮）
    community_maintained = fields.Method('_community_maintained')  # 是否尚未被商户入驻（仅用于文案区分，补充菜品已对全部公开店开放）
    favorited = fields.Method('_favorited')

    def _community_maintained(self, obj) -> bool:
        """是否尚未被商户入驻（owner 为空或 owner 非商户角色），用于前端展示提示文案。"""
        if obj.owner_id is None:
            return True
        owner = getattr(obj, 'owner', None)
        return owner is None or owner.role != 'merchant'

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
    zone = fields.Str()          # 大分类筛选：校内 / 周边 / 外卖
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
    dish_id = fields.Int()
    dish_name = fields.Method('_dish_name')  # 关联菜品名（未关联为 null）
    nickname = fields.Method('_nickname')
    avatar_url = fields.Method('_avatar')
    rating = fields.Int()
    content = fields.Str()
    images = fields.Method('_images')  # 解析后的图集（原先是原始 JSON 字符串）
    like_count = fields.Int()
    liked = fields.Method('_liked')           # 当前登录用户是否已点赞（未登录恒 false）
    reply_count = fields.Method('_reply_count')
    replies = fields.Method('_replies')       # 最多 3 条预览，更多走 /reviews/<id>/replies
    created_at = fields.DateTime()

    def _nickname(self, obj) -> str:
        return obj.user.nickname if obj.user else None

    def _avatar(self, obj) -> str:
        return obj.user.avatar_url if obj.user else None

    def _dish_name(self, obj):
        return obj.dish.name if obj.dish else None

    def _images(self, obj) -> list:
        """图集：解析 images JSON；历史行（无图片）回退空列表。"""
        try:
            imgs = json.loads(obj.images) if obj.images else None
        except (TypeError, ValueError):
            imgs = None
        return imgs if isinstance(imgs, list) else []

    def _liked(self, obj) -> bool:
        return obj.id in liked_review_ids()

    def _reply_count(self, obj) -> int:
        return reply_preview('review', obj.id)['count']

    def _replies(self, obj) -> list:
        return _reply_list_schema.dump(reply_preview('review', obj.id)['items'])


class ReviewCreateSchema(Schema):
    """发表评价请求。"""

    rating = fields.Int(required=True)
    content = fields.Str(required=False, load_default=None)
    # 上限与前端 MultiImageField 的 max 对齐（原先接口不设上限）
    images = fields.List(fields.Str(), validate=validate.Length(max=9))
    # 关联菜品（可空）：必须属于本店，由 ShopService 校验；''/0 一律视为未关联
    dish_id = fields.Int(load_default=None, allow_none=True)

    class Meta:
        unknown = EXCLUDE

    @pre_load
    def _blank_dish_id(self, data, **kwargs):
        """el-select 可清空，清空后发的是空串。

        不归一化的话 fields.Int 会先报「Not a valid integer」，
        ShopService._resolve_dish 里那句「''/0 一律视为未关联」就永远走不到。
        """
        if isinstance(data, dict) and isinstance(data.get('dish_id'), str):
            if not data['dish_id'].strip():
                data = {**data, 'dish_id': None}
        return data


class FavoriteSchema(Schema):
    """收藏信息。"""

    id = fields.Int()
    shop_id = fields.Int()
    created_at = fields.DateTime()
    shop = fields.Nested(ShopSchema)   # 嵌套店铺信息
