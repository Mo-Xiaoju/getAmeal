"""Flask 扩展实例。

集中定义扩展对象，在 create_app() 中调用 init_app() 绑定到应用实例。
"""
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
sio = SocketIO()
