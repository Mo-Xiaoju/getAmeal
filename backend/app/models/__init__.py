"""数据模型包。

统一在此导入全部模型，便于 Flask-Migrate / SQLAlchemy 自动发现表结构。
"""
from app.models.comment import Comment
from app.models.dish import Dish
from app.models.favorite import Favorite
from app.models.follow import UserFollow
from app.models.like import Like
from app.models.message import Message
from app.models.post import Post
from app.models.review import Review
from app.models.school import School
from app.models.shop import Shop
from app.models.user import User

__all__ = [
    'User', 'School', 'Shop', 'Dish', 'Review', 'Favorite', 'Message',
    'Post', 'Comment', 'Like', 'UserFollow',
]
