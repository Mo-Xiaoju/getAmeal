"""评论/回复与点赞的共用业务逻辑。

笔记评论和评价回复共用 comments 一张表（多态写法见 models/comment.py 的 docstring），
所以这里也是两者唯一的实现处：post_service 与评价路由都委托过来，不各写一份。

两条铁律，都在 add_reply 里强制：
1. 被回复人（reply_to_user_id）由服务端从父评论作者派生。客户端只能传 parent_id ——
   否则任何人都能伪造 @ 对象。
2. 回复固定两层。回复一条嵌套回复时，parent_id 归一化到它的根，被回复人进
   reply_to_user_id。这样树不会递归，schema 也不必自引用到底。

可见性检查写成本模块的私有函数，而不是复用 shop_service 的 _get_active_shop：
shop_service 已经依赖本模块（attach_reply_previews / purge_for_review），
反向 import 会成环。多这几行换来单向依赖。
"""
from flask import g

from app.extensions import db
from app.models import Comment, CommentLike, Like, Post, Review, User
from app.schemas.comment import CommentCreateSchema, CommentSchema
from app.utils.exceptions import NotFoundError, ValidationError
from app.utils.pagination import paginate

_comment_schema = CommentSchema()
_comment_list_schema = CommentSchema(many=True)

# 列表里每条最多预览几条顶层回复（更多走 /replies 接口展开）
PREVIEW_LIMIT = 3
# 子回复硬上限：两层模型下每个根的子回复天然很少，这里只是防极端数据撑爆响应
CHILD_LIMIT = 50


# ---- 可见性检查（各自抛与所属路由一致的错误码）----

def _get_active_post(post_id: int) -> Post:
    post = Post.query.get(post_id)
    if post is None or not post.is_active:
        raise NotFoundError(message='笔记不存在', code=4044)
    return post


def _get_active_review(review_id: int) -> Review:
    review = Review.query.get(review_id)
    if review is None:
        raise NotFoundError(message='评价不存在', code=4042)
    shop = review.shop
    if shop is None or not shop.is_active or shop.status != 'approved':
        raise NotFoundError(message='评价不存在', code=4042)
    return review


def _get_comment(comment_id: int) -> Comment:
    comment = Comment.query.get(comment_id)
    if comment is None:
        raise NotFoundError(message='评论不存在', code=4048)
    return comment


def _assert_thread_visible(comment: Comment) -> None:
    """评论/回复所在的线程根必须还可见，否则点赞或回复会造出挂在已删内容上的死数据。"""
    if comment.post_id is not None:
        _get_active_post(comment.post_id)
    else:
        _get_active_review(comment.review_id)


def _fill_reply_target_nicknames(comments) -> None:
    """一次查完这批评论里所有 @ 对象的昵称，写进 g.reply_target_nicknames。

    在 schema 里逐条读 obj.reply_to_user.nickname 也能跑（代码库里 _nickname 就是这么写的），
    但那是每条一次 lazy load；这里多一条 IN 查询就能让整个响应免掉。
    """
    target_ids = {c.reply_to_user_id for c in comments if c.reply_to_user_id}
    if not target_ids:
        return
    nicknames = dict(
        User.query.filter(User.id.in_(target_ids))
        .with_entities(User.id, User.nickname)
        .all()
    )
    g.reply_target_nicknames = {**(getattr(g, 'reply_target_nicknames', None) or {}), **nicknames}


class CommentService:
    """评论/回复与点赞。"""

    # ---- 发表评论/回复 ----
    @staticmethod
    def add_reply(user, data: dict, *, post_id=None, review_id=None) -> dict:
        """在笔记或评价下发一条评论/回复。post_id / review_id 恰好传一个。"""
        data = CommentCreateSchema().load(data)
        if post_id is not None:
            _get_active_post(post_id)
        else:
            _get_active_review(review_id)

        content = (data.get('content') or '').strip()
        if not content:
            raise ValidationError(message='评论内容不能为空', code=4000)

        parent = None
        parent_id = data.get('parent_id')
        if parent_id:
            parent = _get_comment(int(parent_id))
            _assert_thread_visible(parent)
            # 父评论必须属于同一线程，否则可以把回复挂到别处的评论上
            in_same_thread = (
                (post_id is not None and parent.post_id == post_id and parent.review_id is None)
                or (review_id is not None and parent.review_id == review_id)
            )
            if not in_same_thread:
                raise ValidationError(message='回复的评论不属于该内容', code=4000)

        comment = Comment(
            post_id=post_id,
            review_id=review_id,
            user_id=user.id,
            # 归一化到根 + 记录被回复人，回复固定两层
            parent_id=(parent.parent_id or parent.id) if parent else None,
            reply_to_user_id=parent.user_id if parent else None,
            content=content[:500],
        )
        db.session.add(comment)
        db.session.commit()
        # 新回复的 @ 对象是本次请求新出现的，g 映射里多半没有它，补一条
        _fill_reply_target_nicknames([comment])
        return _comment_schema.dump(comment)

    # ---- 回复列表（展开「查看全部」用）----
    @staticmethod
    def list_children(comment_id: int, params: dict) -> dict:
        """某条评论/回复下的全部子回复（分页）——「查看全部 N 条回复」点开就是这里。

        传根 id 或它下面任意一条子回复的 id 都能用：先归一化到根再取子集，
        因为回复固定两层，这里的每条结果的 replies 必然为空，不会再往下嵌套。
        """
        comment = _get_comment(comment_id)
        _assert_thread_visible(comment)
        root_id = comment.parent_id or comment.id

        query = Comment.query.filter_by(parent_id=root_id).order_by(Comment.id.asc())
        page = int(params.get('page') or 1)
        page_size = int(params.get('page_size') or 20)
        result = paginate(query, page, page_size)
        _fill_reply_target_nicknames(result['items'])
        return {**result, 'items': _comment_list_schema.dump(result['items'])}

    @staticmethod
    def list_replies(params: dict, *, post_id=None, review_id=None) -> dict:
        """某条笔记/评价下的顶层回复（分页，每条带自己的全部子回复）。

        与 list_children 的区别：这个取的是**线程的一级回复**（评价列表点「查看全部」
        用它），那个取的是**某条回复下的二级回复**。
        """
        if post_id is not None:
            _get_active_post(post_id)
            scope, scope_col, scope_id = 'post', Comment.post_id, post_id
        else:
            _get_active_review(review_id)
            scope, scope_col, scope_id = 'review', Comment.review_id, review_id

        query = (
            Comment.query
            .filter(scope_col == scope_id, Comment.parent_id.is_(None))
            .order_by(Comment.id.asc())
        )
        page = int(params.get('page') or 1)
        page_size = int(params.get('page_size') or 20)
        result = paginate(query, page, page_size)
        # 先装填预览，_comment_list_schema.dump 里每个根的 _replies 才拿得到子回复
        CommentService.attach_reply_previews([scope_id], scope)
        return {**result, 'items': _comment_list_schema.dump(result['items'])}

    # ---- 回复预览装填 ----
    @staticmethod
    def attach_reply_previews(parent_ids, scope: str) -> None:
        """为当前页的笔记/评价批量装填回复预览，写进请求级 g 供 schema 读取。

        scope: 'post' | 'review'；parent_ids: 笔记/评价的 id 列表。
        **固定 2 条查询**（先取该页全部顶层回复，再一次取它们的全部子回复），
        与页大小无关 —— 逐条查就是 N+1。
        """
        parent_ids = [pid for pid in (parent_ids or []) if pid]
        if not parent_ids:
            return

        scope_col = Comment.post_id if scope == 'post' else Comment.review_id
        roots = (
            Comment.query
            .filter(scope_col.in_(parent_ids), Comment.parent_id.is_(None))
            .order_by(Comment.id.asc())
            .all()
        )
        children = (
            Comment.query
            .filter(Comment.parent_id.in_([r.id for r in roots]))
            .order_by(Comment.id.asc())
            .all()
            if roots
            else []
        )

        roots_by_parent = {}     # ('post'|'review', id) -> [顶层回复]
        for root in roots:
            roots_by_parent.setdefault((scope, getattr(root, scope_col.key)), []).append(root)

        children_by_root = {}    # 顶层回复 id -> [子回复]
        for child in children:
            children_by_root.setdefault(child.parent_id, []).append(child)

        previews = {}
        for key, items in roots_by_parent.items():
            # "N 条回复"是用户眼里的全部回复，要把子回复也数进去；
            # items 只给前 PREVIEW_LIMIT 个根，展开后由 /replies 补全。
            previews[key] = {
                'count': sum(1 + len(children_by_root.get(r.id, [])) for r in items),
                'items': items[:PREVIEW_LIMIT],
            }
        child_previews = {
            root.id: {
                'count': len(children_by_root.get(root.id, [])),
                'items': children_by_root.get(root.id, [])[:CHILD_LIMIT],
            }
            for root in roots
        }

        _fill_reply_target_nicknames(roots + children)

        g.reply_preview = {**(getattr(g, 'reply_preview', None) or {}), **previews}
        g.reply_children = {**(getattr(g, 'reply_children', None) or {}), **child_previews}

    # ---- 点赞 ----
    @staticmethod
    def toggle_review_like(user, review_id: int) -> dict:
        """点赞/取消点赞评价（幂等）。"""
        review = _get_active_review(review_id)
        like = Like.query.filter_by(user_id=user.id, review_id=review.id).first()
        if like:
            db.session.delete(like)
            review.like_count = max(review.like_count - 1, 0)
            db.session.commit()
            return {'liked': False, 'like_count': review.like_count}
        db.session.add(Like(user_id=user.id, review_id=review.id))
        review.like_count += 1
        db.session.commit()
        return {'liked': True, 'like_count': review.like_count}

    @staticmethod
    def toggle_comment_like(user, comment_id: int) -> dict:
        """点赞/取消点赞评论或回复（幂等）。笔记评论与评价回复共用一套。"""
        comment = _get_comment(comment_id)
        _assert_thread_visible(comment)
        like = CommentLike.query.filter_by(user_id=user.id, comment_id=comment.id).first()
        if like:
            db.session.delete(like)
            comment.like_count = max(comment.like_count - 1, 0)
            db.session.commit()
            return {'liked': False, 'like_count': comment.like_count}
        db.session.add(CommentLike(user_id=user.id, comment_id=comment.id))
        comment.like_count += 1
        db.session.commit()
        return {'liked': True, 'like_count': comment.like_count}

    # ---- 随评价一起清除 ----
    @staticmethod
    def purge_for_review(review_id: int) -> None:
        """删除某评价下的全部回复及其点赞（不含评价本身；均分回退由调用方做）。

        集中在这里，将来加管理员删除路由也不会漏掉任何一张表。
        顺序不能改：先断 comment_likes 的外键 → parent_id 置空解开自引用
        （否则同一句多行 DELETE 会撞 1451）→ 删 comments → 删评价点赞。
        """
        comment_ids = [
            cid for (cid,) in db.session.query(Comment.id).filter_by(review_id=review_id).all()
        ]
        if comment_ids:
            CommentLike.query.filter(CommentLike.comment_id.in_(comment_ids)).delete(
                synchronize_session=False
            )
            Comment.query.filter(Comment.id.in_(comment_ids)).update(
                {'parent_id': None}, synchronize_session=False
            )
            Comment.query.filter(Comment.id.in_(comment_ids)).delete(synchronize_session=False)
        Like.query.filter_by(review_id=review_id).delete(synchronize_session=False)
