"""探店笔记相关 Schema。"""
import json

from flask import g
from marshmallow import EXCLUDE, Schema, fields

from app.models import Favorite, UserFollow
# 评论/回复 Schema 的实现在 schemas/comment.py（笔记评论与评价回复共用一张表），
# 这里再导出一次，使 post_service 现有的 import 不必挪动。
from app.schemas.comment import CommentCreateSchema, CommentSchema  # noqa: F401
from app.schemas.interaction import liked_post_ids as _liked_post_ids


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


# CommentSchema / CommentCreateSchema 见 app/schemas/comment.py（已在文件顶部导入并再导出）
