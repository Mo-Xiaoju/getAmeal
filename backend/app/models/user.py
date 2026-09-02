"""用户模型。role 字段区分普通学生与管理员。"""
from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class User(db.Model):
    """系统用户。"""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True, index=True)
    username = db.Column(db.String(50), unique=True, nullable=False)      # 登录名
    password_hash = db.Column(db.String(255), nullable=False)             # 密码哈希（werkzeug scrypt 哈希长度约 200）
    nickname = db.Column(db.String(50), nullable=False)                   # 昵称
    avatar_url = db.Column(db.String(255), nullable=True)                 # 头像地址
    role = db.Column(db.String(10), nullable=False, default='student')    # 'student' | 'admin'
    is_active = db.Column(db.Boolean, nullable=False, default=True)       # 是否封禁
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系：N:1 学校；1:N 笔记
    school = db.relationship('School', back_populates='users')
    posts = db.relationship('Post', back_populates='user', lazy='dynamic')

    # 关注关系：following=我关注的 UserFollow 行；followers=关注我的 UserFollow 行（定义见 UserFollow）

    # ---- 密码工具 ----
    def set_password(self, password: str) -> None:
        """写入密码哈希（werkzeug 加盐哈希）。"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """校验明文密码是否匹配哈希。"""
        return check_password_hash(self.password_hash, password)
