"""用户社交业务逻辑：关注 / 取关 / 关注列表。"""
from app.extensions import db
from app.models import User, UserFollow
from app.utils.exceptions import ValidationError
from app.utils.pagination import paginate


def _user_brief(user: User, viewer=None) -> dict:
    """用户对外简要信息（供关注列表使用）。"""
    is_following = False
    if viewer is not None and viewer.id != user.id:
        is_following = (
            UserFollow.query.filter_by(follower_id=viewer.id, followee_id=user.id).first() is not None
        )
    return {
        'id': user.id,
        'nickname': user.nickname,
        'username': user.username,
        'avatar_url': user.avatar_url,
        'school_name': user.school.name if user.school else None,
        'is_following': is_following,
    }


class UserService:
    """关注等社交业务。"""

    @staticmethod
    def toggle_follow(user, target_id: int) -> dict:
        """关注/取关用户（幂等）。"""
        if user.id == target_id:
            raise ValidationError(message='不能关注自己', code=4000)
        target = User.query.get(target_id)
        if target is None or not target.is_active:
            raise ValidationError(message='用户不存在', code=4045)

        follow = UserFollow.query.filter_by(follower_id=user.id, followee_id=target_id).first()
        if follow:
            db.session.delete(follow)
            db.session.commit()
            return {'following': False}
        db.session.add(UserFollow(follower_id=user.id, followee_id=target_id))
        db.session.commit()
        return {'following': True}

    @staticmethod
    def list_following(user, params: dict) -> dict:
        """我关注的人（分页）。"""
        query = UserFollow.query.filter_by(follower_id=user.id).order_by(UserFollow.id.desc())
        page = int(params.get('page') or 1)
        page_size = int(params.get('page_size') or 10)
        result = paginate(query, page, page_size)
        items = [_user_brief(f.followee, viewer=user) for f in result['items']]
        return {**result, 'items': items}

    @staticmethod
    def list_followers(user, params: dict) -> dict:
        """关注我的人（分页）。"""
        query = UserFollow.query.filter_by(followee_id=user.id).order_by(UserFollow.id.desc())
        page = int(params.get('page') or 1)
        page_size = int(params.get('page_size') or 10)
        result = paginate(query, page, page_size)
        items = [_user_brief(f.follower, viewer=user) for f in result['items']]
        return {**result, 'items': items}

    @staticmethod
    def follow_counts(user_id: int) -> dict:
        """关注/粉丝数。"""
        return {
            'following_count': UserFollow.query.filter_by(follower_id=user_id).count(),
            'follower_count': UserFollow.query.filter_by(followee_id=user_id).count(),
        }
