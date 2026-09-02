"""蓝图注册汇总。"""
from flask import Flask

from app.routes import admin, auth, chat, dish, post, school, shop, user


def register_blueprints(app: Flask) -> None:
    """注册全部业务蓝图。"""
    app.register_blueprint(auth.bp_auth, url_prefix='/api/auth')
    app.register_blueprint(school.bp_school, url_prefix='/api')
    app.register_blueprint(shop.bp_shop, url_prefix='/api/shops')
    app.register_blueprint(dish.bp_dish, url_prefix='/api/dishes')
    app.register_blueprint(post.bp_post, url_prefix='/api/posts')
    app.register_blueprint(user.bp_user, url_prefix='/api/user')
    app.register_blueprint(chat.bp_chat, url_prefix='/api/chat')
    app.register_blueprint(admin.bp_admin, url_prefix='/api/admin')
