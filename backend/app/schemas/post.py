"""探店笔记相关 Schema。"""
import json

from flask import g
from marshmallow import EXCLUDE, Schema, fields

from app.models import Favorite, Like, UserFollow


def _liked_post_ids() -> set:
    """当前登录用户已点赞的笔记 id 集合。

    列表卡片也要按"我点过赞没有"上色，逐条查库在列表页就是 N 次查询，
    所以这里一次取完、并在本次请求内缓存（g 是请求级的，不会跨请求串数据）。
    """
    ids = getattr(g, 'liked_post_ids', None)
    if ids is None:
        user = getattr(g, 'current_user', None)
        ids = (
            {row[0] for row in Like.query.with_entities(Like.post_id).filter_by(user_id=user.id)}
            if user is not None
            else set()
        )
        g.liked_post_ids = ids
    return ids


def _favorited_post_ids() -> set:
    """当前登录用户已收藏的笔记 id 集合（同上；shop_id 为空的是收藏店铺，跳过）。"""
    ids = getattr(g, 'favorited_post_ids', None)
    if ids is None:
        user = getattr(g, 'current_user', None)
        ids = (
            {
                row[0]
                for row in Favorite.query.with_entities(Favorite.post_id).filter_by(user_id=user.id)
                if row[0] is not None
            }
            if user is not None
            else set()
        )
        g.favorited_post_ids = ids
    return ids


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
    # 当前登录用户视角的互动状态：列表卡片要按状态上色（已点赞 / 已收藏），详情页复用同一对字段
    liked = fields.Method('_liked')
    favorited = fields.Method('_favorited')

    def _liked(self, obj) -> bool:
        return obj.id in _liked_post_ids()

    def _favorited(self, obj) -> bool:
        return obj.id in _favorited_post_ids()

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
    """笔记详情：在列表项基础上扩展登录用户视角状态（liked / favorited 继承自列表项）。"""

    is_following = fields.Method('_is_following')

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
