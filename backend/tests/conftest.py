"""pytest 全局夹具。"""
import pytest


@pytest.fixture
def app():
    """测试用 Flask 应用实例（testing 配置）。"""
    pass


@pytest.fixture
def client(app):
    """测试客户端。"""
    pass


@pytest.fixture
def db_session(app):
    """测试数据库会话（每用例事务回滚）。"""
    pass


@pytest.fixture
def auth_headers(client):
    """登录后返回的鉴权请求头。"""
    pass
