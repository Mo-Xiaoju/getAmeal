"""探店笔记相关 Schema。"""
import json

from flask import g
from marshmallow import EXCLUDE, Schema, fields

from app.models import Like, UserFollow


class PostSchema(Schema):
    """笔记列表项。"""

    id = fields.Int()
    user_id = fields.Int()
    title = fields.Str()
    content = fields.Str()
    images = fields.Method('_images')
    shop_id = fields.Int()
    shop_name = fields.Method('_shop_name')
    tags = fields.Method('_tags')
    like_count = fields.Int()
    favorite_count = fields.Int()
    comment_count = fields.Int()
    created_at = fields.DateTime()
    author = fields.Method('_author')

    def _images(self, obj) -> list:
        try:
            return json.loads(obj.images or '[]')
        except (TypeError, ValueError):
            return []

    def _shop_name(self, obj) -> str:
        return getattr(obj, 'shop_name', None) or (obj.shop.name if obj.shop else None)

    def _tags(self, obj) -> list:
        return [t for t in (obj.tags or '').split(',') if t]

    def _author(self, obj) -> dict:
        if obj.user is None:
            return None
        return {'id': obj.user.id, 'nickname': obj.user.nickname, 'avatar_url': obj.user.avatar_url}


class PostDetailSchema(PostSchema):
    """笔记详情：在列表项基础上扩展登录用户视角状态。"""

    liked = fields.Method('_liked')
    favorited = fields.Method('_favorited')
    is_following = fields.Method('_is_following')

    def _liked(self, obj) -> bool:
        user = getattr(g, 'current_user', None)
        if user is None:
            return False
        return Like.query.filter_by(user_id=user.id, post_id=obj.id).first() is not None

    def _favorited(self, obj) -> bool:
        from app.models import Favorite
        user = getattr(g, 'current_user', None)
        if user is None:
            return False
        return Favorite.query.filter_by(user_id=user.id, post_id=obj.id).first() is not None

    def _is_following(self, obj) -> bool:
        user = getattr(g, 'current_user', None)
        if user is None or obj.user is None or user.id == obj.user_id:
            return False
        return UserFollow.query.filter_by(follower_id=user.id, followee_id=obj.user_id).first() is not None


class PostCreateSchema(Schema):
    """发布笔记请求。"""

    title = fields.Str(required=True)
    content = fields.Str(required=True)
    images = fields.List(fields.Str(), load_default=list)
    shop_id = fields.Int(required=True)  # 必填：笔记必须关联已有店铺
    tags = fields.Str(load_default=None)

    class Meta:
        unknown = EXCLUDE


class CommentSchema(Schema):
    """笔记评论。"""

    id = fields.Int()
    post_id = fields.Int()
    user_id = fields.Int()
    nickname = fields.Method('_nickname')
    avatar_url = fields.Method('_avatar')
    content = fields.Str()
    created_at = fields.DateTime()

    def _nickname(self, obj) -> str:
        return obj.user.nickname if obj.user else None

    def _avatar(self, obj) -> str:
        return obj.user.avatar_url if obj.user else None


class CommentCreateSchema(Schema):
    """发表评论请求。"""

    content = fields.Str(required=True)

    class Meta:
        unknown = EXCLUDE
