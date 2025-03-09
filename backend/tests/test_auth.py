import pytest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.utils.database import  db   
from app.models.user import User

@pytest.fixture(scope="module")
def app():
    """
    创建 Flask 测试应用
    """
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"  # 使用内存数据库
    app.config["JWT_SECRET_KEY"] = "test-secret"  # 测试用的 JWT 密钥

    with app.app_context():
        db.create_all()  # 创建数据库表
        yield app
        db.session.remove()
        db.drop_all()  # 清理数据库


@pytest.fixture(scope="module")
def client(app):
    """
    创建 Flask 测试客户端
    """
    return app.test_client()


@pytest.fixture(scope="module")
def user(app):
    """
    创建一个测试用户
    """
    with app.app_context():
        user = User(username="testuser", email="testuser@example.com")
        user.set_password("testpassword")
        db.session.add(user)
        db.session.commit()
        return user


def test_register(client):
    """
    测试用户注册接口
    """
    data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "newpassword"
    }
    response = client.post("/auth/register", json=data)
    assert response.status_code == 201
    assert response.json["message"] == "User registered successfully"

    # 测试重复注册
    response = client.post("/auth/register", json=data)
    assert response.status_code == 400
    assert response.json["message"] in ["Username already exists", "Email already exists"]


def test_login(client, user):
    """
    测试用户登录接口
    """
    data = {
        "username": "testuser",
        "password": "testpassword"
    }
    response = client.post("/auth/login", json=data)
    assert response.status_code == 200
    assert "access_token" in response.json

    # 测试错误的用户名或密码
    data["password"] = "wrongpassword"
    response = client.post("/auth/login", json=data)
    assert response.status_code == 401
    assert response.json["message"] == "Invalid username or password"


def test_logout(client, user):
    """
    测试用户注销接口
    """
    # 获取 JWT
    login_data = {
        "username": "testuser",
        "password": "testpassword"
    }
    login_response = client.post("/auth/login", json=login_data)
    token = login_response.json["access_token"]

    # 测试注销
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/auth/logout", headers=headers)
    assert response.status_code == 200
    assert response.json["message"] == "User logged out successfully"


def test_profile(client, user):
    """
    测试获取用户信息接口
    """
    # 获取 JWT
    login_data = {
        "username": "testuser",
        "password": "testpassword"
    }
    login_response = client.post("/auth/login", json=login_data)
    token = login_response.json["access_token"]

    # 测试获取用户信息
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/auth/profile", headers=headers)
    assert response.status_code == 200
    assert response.json["username"] == "testuser"
    assert response.json["email"] == "testuser@example.com"