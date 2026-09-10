"""探店笔记业务逻辑：发布、浏览、点赞、收藏、评论。"""
import json
import math

from app.extensions import db
from app.models import Comment, Favorite, Like, Post, Shop
from app.schemas.post import (
    CommentCreateSchema,
    CommentSchema,
    PostCreateSchema,
    PostDetailSchema,
    PostSchema,
)
from app.services.recommend_service import RecommendService
from app.utils.exceptions import NotFoundError, PermissionError, ValidationError
from app.utils.pagination import paginate

_post_schema = PostSchema()
_post_list_schema = PostSchema(many=True)
_post_detail_schema = PostDetailSchema()
_comment_schema = CommentSchema()
_comment_list_schema = CommentSchema(many=True)


def _get_active_post(post_id: int) -> Post:
    post = Post.query.get(post_id)
    if post is None or not post.is_active:
        raise NotFoundError(message='笔记不存在', code=4044)
    return post


def _get_active_shop(shop_id: int) -> Shop:
    shop = Shop.query.get(shop_id)
    if shop is None or not shop.is_active:
        raise NotFoundError(message='店铺不存在', code=4040)
    return shop


class PostService:
    """笔记的查询、发布、互动等业务。"""

    # ---- 发布与删除 ----
    @staticmethod
    def create(user, data: dict) -> dict:
        """发布探店笔记。"""
        data = PostCreateSchema().load(data)
        title = (data.get('title') or '').strip()
        content = (data.get('content') or '').strip()
        if not title:
            raise ValidationError(message='标题不能为空', code=4000)
        if not content:
            raise ValidationError(message='正文不能为空', code=4000)

        # 必填关联店铺：笔记必须绑定一个现存在售店铺
        shop_id = int(data['shop_id'])
        _get_active_shop(shop_id)

        post = Post(
            user_id=user.id,
            title=title[:100],
            content=content,
            images=json.dumps(data.get('images') or [], ensure_ascii=False),
            shop_id=shop_id,
            tags=(data.get('tags') or '').strip()[:200] or None,
        )
        db.session.add(post)
        db.session.commit()
        return _post_detail_schema.dump(post)

    @staticmethod
    def delete_post(user, post_id: int) -> None:
        """删除自己的笔记（软删除）。"""
        post = _get_active_post(post_id)
        if post.user_id != user.id and user.role != 'admin':
            raise PermissionError(message='无权删除该笔记', code=4030)
        post.is_active = False
        db.session.commit()

    # ---- 列表与详情 ----
    @staticmethod
    def list(params: dict, user=None) -> dict:
        """笔记列表：school_id / keyword / user_id 过滤，newest / hot / recommend 排序，分页。

        recommend 仅首页推荐流使用（走打分引擎 rank_posts）；其余分支语义保持不变。
        """
        if params.get('sort') == 'recommend':
            return PostService._list_recommend(params, user)

        query = Post.query.filter_by(is_active=True)
        school_id = params.get('school_id')
        if school_id:
            query = query.join(Shop).filter(Shop.school_id == int(school_id))

        keyword = (params.get('keyword') or '').strip()
        if keyword:
            query = query.filter(
                db.or_(Post.title.like(f'%{keyword}%'), Post.content.like(f'%{keyword}%'))
            )

        # 按作者过滤（他人主页的笔记列表）。注意 sort=recommend 走上面的分支，
        # 不会经过这里，用户主页统一用默认的 newest 排序。
        user_id = params.get('user_id')
        if user_id:
            try:
                query = query.filter(Post.user_id == int(user_id))
            except (TypeError, ValueError):
                raise ValidationError(message='user_id 参数不合法', code=4000)

        sort = params.get('sort')
        if sort == 'hot':
            # 热度 = 点赞 + 收藏 + 评论
            query = query.order_by(
                (Post.like_count + Post.favorite_count + Post.comment_count).desc(),
                Post.id.desc(),
            )
        else:  # 默认最新
            query = query.order_by(Post.created_at.desc(), Post.id.desc())

        page = int(params.get('page') or 1)
        page_size = int(params.get('page_size') or 10)
        result = paginate(query, page, page_size)
        return {**result, 'items': _post_list_schema.dump(result['items'])}

    @staticmethod
    def _list_recommend(params: dict, user=None) -> dict:
        """首页推荐流分支：整池打分排序后再做内存分页切片（保证翻页顺序稳定）。"""
        posts, reasons = RecommendService.rank_posts(user, params)

        try:
            page = int(params.get('page') or 1)
        except (TypeError, ValueError):
            page = 1
        try:
            page_size = int(params.get('page_size') or 10)
        except (TypeError, ValueError):
            page_size = 10
        page = max(page, 1)
        page_size = min(max(page_size, 1), 20)

        total = len(posts)
        total_pages = math.ceil(total / page_size) if total else 0
        start = (page - 1) * page_size
        chunk = posts[start:start + page_size]
        items = _post_list_schema.dump(chunk)
        for item, reason in zip(items, reasons[start:start + page_size]):
            item['rec_reason'] = reason
        return {'items': items, 'total': total, 'page': page,
                'page_size': page_size, 'total_pages': total_pages}

    @staticmethod
    def list_my_posts(user, params: dict) -> dict:
        """当前用户的笔记列表（分页）。"""
        query = Post.query.filter_by(user_id=user.id, is_active=True).order_by(
            Post.created_at.desc(), Post.id.desc()
        )
        page = int(params.get('page') or 1)
        page_size = int(params.get('page_size') or 10)
        result = paginate(query, page, page_size)
        return {**result, 'items': _post_list_schema.dump(result['items'])}

    @staticmethod
    def get_detail(post_id: int) -> dict:
        """笔记详情（含当前登录用户的点赞/收藏/关注状态）。"""
        return _post_detail_schema.dump(_get_active_post(post_id))

    # ---- 点赞 / 收藏 ----
    @staticmethod
    def toggle_like(user, post_id: int) -> dict:
        """点赞/取消点赞（幂等）。"""
        post = _get_active_post(post_id)
        like = Like.query.filter_by(user_id=user.id, post_id=post.id).first()
        if like:
            db.session.delete(like)
            post.like_count = max(post.like_count - 1, 0)
            db.session.commit()
            return {'liked': False, 'like_count': post.like_count}
        db.session.add(Like(user_id=user.id, post_id=post.id))
        post.like_count += 1
        db.session.commit()
        return {'liked': True, 'like_count': post.like_count}

    @staticmethod
    def toggle_favorite(user, post_id: int) -> dict:
        """收藏/取消收藏笔记（幂等）。"""
        post = _get_active_post(post_id)
        favorite = Favorite.query.filter_by(user_id=user.id, post_id=post.id).first()
        if favorite:
            db.session.delete(favorite)
            post.favorite_count = max(post.favorite_count - 1, 0)
            db.session.commit()
            return {'favorited': False, 'favorite_count': post.favorite_count}
        db.session.add(Favorite(user_id=user.id, post_id=post.id))
        post.favorite_count += 1
        db.session.commit()
        return {'favorited': True, 'favorite_count': post.favorite_count}

    # ---- 评论 ----
    @staticmethod
    def add_comment(user, post_id: int, data: dict) -> dict:
        """发表评论，并更新笔记评论数。"""
        data = CommentCreateSchema().load(data)
        post = _get_active_post(post_id)
        content = (data.get('content') or '').strip()
        if not content:
            raise ValidationError(message='评论内容不能为空', code=4000)
        comment = Comment(user_id=user.id, post_id=post.id, content=content[:500])
        post.comment_count += 1
        db.session.add(comment)
        db.session.commit()
        return _comment_schema.dump(comment)

    @staticmethod
    def list_comments(post_id: int, params: dict) -> dict:
        """笔记评论列表（分页，按时间正序）。"""
        _get_active_post(post_id)
        query = Comment.query.filter_by(post_id=post_id).order_by(Comment.id.asc())
        page = int(params.get('page') or 1)
        page_size = int(params.get('page_size') or 20)
        result = paginate(query, page, page_size)
        return {**result, 'items': _comment_list_schema.dump(result['items'])}
