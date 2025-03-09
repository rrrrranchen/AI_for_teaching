from flask import Blueprint, render_template, request, jsonify, session
from werkzeug.security import check_password_hash
from app.utils.database import db
from app.models.user import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    用户注册接口。
    """
    data = request.get_json()

    # 检查必填字段
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing required fields'}), 400

    # 检查用户名和邮箱是否已存在
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already exists'}), 400

    # 创建新用户
    new_user = User(
        username=data['username'],
        email=data['email'],
        signature=data.get('signature')  
    )
    new_user.set_password(data['password'])  # 设置密码哈希

    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    用户登录接口。
    """
    data = request.get_json()

    # 检查必填字段
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Missing username or password'}), 400

    # 查找用户
    user = User.query.filter_by(username=data['username']).first()
    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Invalid username or password'}), 401

    # 将用户 ID 存入 session
    session['user_id'] = user.id
    
    return jsonify({'message': 'User logged in successfully'}), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    用户注销接口。
    """
    # 清除 session 数据
    session.pop('user_id', None)
    return jsonify({'message': 'User logged out successfully'}), 200

@auth_bp.route('/profile', methods=['GET'])
def profile():
    """
    获取当前用户信息接口。
    """
    # 从 session 中获取用户 ID
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'message': 'Unauthorized'}), 401

    # 查找用户
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    # 返回用户信息
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'signature': user.signature,
        'created_at': user.created_at.isoformat()
    }), 200

@auth_bp.route('/profile/update', methods=['PUT'])
def update_profile():
    """
    更新当前用户信息接口。
    """
    # 从 session 中获取用户 ID
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'message': 'Unauthorized'}), 401

    # 查找用户
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    # 获取请求数据
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No data provided'}), 400

    # 更新用户名
    if 'username' in data:
        # 检查新用户名是否已被其他用户使用
        existing_user = User.query.filter_by(username=data['username']).first()
        if existing_user and existing_user.id != user.id:
            return jsonify({'message': 'Username already exists'}), 400
        user.username = data['username']

    # 更新邮箱
    if 'email' in data:
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user and existing_user.id != user.id:
            return jsonify({'message': 'Email already exists'}), 400
        user.email = data['email']

    # 更新签名
    if 'signature' in data:
        user.signature = data['signature']

    # 更新密码
    if 'password' in data:
        user.set_password(data['password'])

    # 提交更改
    db.session.commit()

    return jsonify({'message': 'User profile updated successfully'}), 200

@auth_bp.route('/register-page')
def register_page():
    return render_template('register.html')

@auth_bp.route('/login-page')
def login_page():
    return render_template('login.html')

@auth_bp.route('/profile-page')
def profile_page():
    return render_template('profile.html')