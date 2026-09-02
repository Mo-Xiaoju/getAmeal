"""应用配置。

不同运行环境对应不同配置类；敏感信息通过环境变量（.env）加载。
"""
import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class Config:
    """基础配置：所有环境共用的默认值。"""

    # ---- 密钥 ----
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES_HOURS', '24')))

    # ---- 数据库（MySQL 5.7+）----
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'SQLALCHEMY_DATABASE_URI',
        'mysql+pymysql://root:123456@localhost:3306/campus_food?charset=utf8mb4',
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ---- 跨域 ----
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*')

    # ---- 分页 ----
    PAGE_SIZE_DEFAULT = int(os.environ.get('PAGE_SIZE_DEFAULT', '10'))
    PAGE_SIZE_MAX = int(os.environ.get('PAGE_SIZE_MAX', '50'))


class DevelopmentConfig(Config):
    """开发环境。"""
    DEBUG = True


class TestingConfig(Config):
    """测试环境：使用独立测试库。"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'TEST_DATABASE_URI',
        'mysql+pymysql://root:123456@localhost:3306/campus_food_test?charset=utf8mb4',
    )


class ProductionConfig(Config):
    """生产环境。"""
    DEBUG = False


# 配置名 -> 配置类
config_map = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
