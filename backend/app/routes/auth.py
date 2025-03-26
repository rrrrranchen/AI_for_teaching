import os
from flask import Blueprint,  render_template, request, jsonify, session
from app.utils.file_upload import upload_file
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

    # 检查角色字段是否合法（可选字段）
    role = data.get('role', 'student')  # 默认为学生
    if role not in ['student', 'teacher']:
        return jsonify({'message': 'Invalid role. Allowed roles are "student" or "teacher".'}), 400

    # 创建新用户
    new_user = User(
        username=data['username'],
        email=data['email'],
        role=role,  # 设置用户角色
        signature=data.get('signature')  # 个性签名（可选字段）
    )
    new_user.set_password(data['password'])  # 设置密码哈希

    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully', 'role': role}), 201

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

# 获取当前用户信息接口
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
        'role': user.role,  # 返回用户角色
        'signature': user.signature,
        'avatar': user.avatar,  # 返回用户头像
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

@auth_bp.route('/profile/update_avatar', methods=['POST'])
def update_avatar():
    """
    更新或添加用户头像接口。
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'message': 'Unauthorized'}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    if 'avatar' not in request.files:
        return jsonify({'message': 'No file part'}), 400

    file = request.files['avatar']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400

    try:
        # 调用 file_upload.py 中的 upload_file 函数
        relative_path = upload_file(file)
        
        # 更新用户头像路径
        user.avatar = relative_path
        db.session.commit()
        
        
        return jsonify({'message': 'Avatar updated successfully', 'avatar': relative_path}), 200
    except ValueError as e:
        return jsonify({'message': str(e)}), 400




@auth_bp.route('/register-page')
def register_page():
    return render_template('register.html')

@auth_bp.route('/login-page')
def login_page():
    return render_template('login.html')

@auth_bp.route('/profile-page')
def profile_page():
    return render_template('profile.html')