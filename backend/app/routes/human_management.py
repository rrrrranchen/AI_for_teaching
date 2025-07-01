from datetime import datetime, timedelta
from flask import Blueprint, g, jsonify, request, session
from sqlalchemy import distinct, func
from app.utils.database import db
from app.models.user import User

from app.models.relationship import student_class,teacher_class,course_courseclass
human_management_bp = Blueprint('human_management', __name__)

def is_logged_in():
    return 'user_id' in session

def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

@human_management_bp.before_request
def before_request():
    # 检查用户是否已登录
    if is_logged_in():
        # 获取当前用户并存储到 g 对象中
        g.current_user = get_current_user()
        # 检查用户是否为管理员
        if g.current_user and g.current_user.role != 'admin':
            return jsonify({'error': 'Forbidden'}), 403
    else:
        # 如果用户未登录，返回未授权错误
        return jsonify({'error': 'Unauthorized'}), 401
    
#筛选查询用户信息
@human_management_bp.route('/admin/query_users', methods=['GET'])
def query_users():
    # 获取请求的 JSON 数据
    data = request.get_json(silent=True) or {}

    # 获取筛选条件
    role = data.get('role', None)  # 角色筛选参数
    username = data.get('username', None)  # 用户名筛选参数

    # 查询所有用户
    query = User.query

    # 根据角色筛选
    if role:
        query = query.filter(User.role == role)

    # 根据用户名筛选
    if username:
        query = query.filter(User.username.like(f'%{username}%'))

    # 根据用户ID排序
    query = query.order_by(User.id.asc())

    # 获取查询结果
    users = query.all()

    # 构造返回数据
    user_list = []
    for user in users:
        user_data = {
            'id': user.id,
            'username': user.username,
            'role': user.role,
            'email': user.email,
            'signature': user.signature,
            'avatar': user.avatar,
            'created_at': user.created_at.isoformat()
        }
        user_list.append(user_data)

    return jsonify(user_list)

#更新用户信息
@human_management_bp.route('/admin/update_user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    # 获取请求的 JSON 数据
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400

    # 查询用户是否存在
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # 更新用户信息
    if 'username' in data:
        user.username = data['username']
    if 'email' in data:
        user.email = data['email']
    if 'role' in data:
        user.role = data['role']
    if 'signature' in data:
        user.signature = data['signature']
    if 'password' in data:
        user.set_password(data['password'])

    # 提交更改到数据库
    db.session.commit()

    # 返回更新后的用户信息
    user_data = {
        'id': user.id,
        'username': user.username,
        'role': user.role,
        'email': user.email,
        'signature': user.signature,
        'created_at': user.created_at.isoformat()
    }

    return jsonify(user_data), 200

#批量删除多个用户
@human_management_bp.route('/admin/delete_users', methods=['DELETE'])
def delete_users():
    # 获取请求的 JSON 数据
    data = request.get_json()
    if not data or 'user_ids' not in data:
        return jsonify({'error': 'No user IDs provided'}), 400

    user_ids = data['user_ids']
    if not isinstance(user_ids, list) or not all(isinstance(uid, int) for uid in user_ids):
        return jsonify({'error': 'Invalid user IDs format'}), 400

    # 查询要删除的用户
    users = User.query.filter(User.id.in_(user_ids)).all()
    if not users:
        return jsonify({'error': 'No users found with the provided IDs'}), 404

    # 删除用户及其关联关系
    for user in users:
        # 删除用户发布的帖子
        for post in user.posts:
            db.session.delete(post)
        
        # 删除用户发布的评论
        for comment in user.comments:
            db.session.delete(comment)
        
        # 删除用户点赞的帖子
        for liked_post in user.liked_posts:
            db.session.delete(liked_post)
        
        # 删除用户收藏的帖子
        for favorite in user.favorites:
            db.session.delete(favorite)
        
        # 删除用户创建的教学设计版本
        for teaching_design_version in user.teaching_design_versions:
            db.session.delete(teaching_design_version)
        
        # 删除用户创建的教学设计
        for teaching_design in user.teaching_designs:
            db.session.delete(teaching_design)
        
        # 删除用户相关的操作日志
        for log in user.operation_logs:
            db.session.delete(log)
        
        # 删除用户
        db.session.delete(user)

    # 提交更改到数据库
    db.session.commit()

    return jsonify({'message': 'Users deleted successfully'}), 200

#添加用户
@human_management_bp.route('/admin/add_user', methods=['POST'])
def add_user():
    # 获取请求的 JSON 数据
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400

    # 获取用户信息
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')
    email = data.get('email')
    signature = data.get('signature', '')

    # 验证必填字段
    if not username or not password or not role or not email:
        return jsonify({'error': 'Missing required fields'}), 400

    # 检查用户名是否已存在
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400

    # 检查邮箱是否已存在
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 400

    # 创建新用户
    new_user = User(
        username=username,
        role=role,
        email=email,
        signature=signature,
    )
    new_user.set_password(password)  # 设置密码

    # 添加用户到数据库
    db.session.add(new_user)
    db.session.commit()

    # 返回成功响应
    return jsonify({
        'message': 'User added successfully',
        'user': {
            'id': new_user.id,
            'username': new_user.username,
            'role': new_user.role,
            'email': new_user.email,
            'signature': new_user.signature,
            'created_at': new_user.created_at.isoformat()
        }
    }), 201


