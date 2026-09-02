"""应用包。

采用应用工厂模式：create_app() 完成配置加载、扩展初始化、蓝图注册与错误处理注册。
"""
from flask import Flask

from app import models  # noqa: F401  确保全部模型注册到 db.metadata（迁移/建表依赖）
from app.config import config_map
from app.extensions import cors, db, jwt, migrate
from app.routes import register_blueprints


def create_app(config_name: str = 'development') -> Flask:
    """创建 Flask 应用实例。

    流程：
        1. 加载配置（config_map 中的配置类）
        2. 初始化扩展（db / migrate / jwt / cors）
        3. 注册业务蓝图
        4. 注册全局错误处理器
    """
    app = Flask(__name__)
    app.config.from_object(config_map.get(config_name, config_map['default']))

    # ---- 初始化扩展 ----
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, origins=app.config.get('CORS_ORIGINS', '*'))

    # ---- 注册蓝图 ----
    register_blueprints(app)

    # ---- 注册全局错误处理器 ----
    from app.errors.handlers import register_error_handlers, register_jwt_handlers
    register_error_handlers(app)
    register_jwt_handlers(jwt)

    # ---- 注册 CLI 命令 ----
    from app.cli import register_cli
    register_cli(app)

    return app
