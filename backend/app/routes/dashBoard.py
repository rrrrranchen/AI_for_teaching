from datetime import datetime
from flask import Blueprint, g, jsonify, request, session

from app.models.StudentOperationLog import StudentOperationLog
from app.utils.database import db
from app.services.log_service import LogService
from app.models.AdminOperationLog import AdminOperationLog
from app.models.TeacherOperationLog import TeacherOperationLog
from app.models.user import User


dashBoard_bp = Blueprint('dashBoard', __name__)

def is_logged_in():
    return 'user_id' in session

def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

@dashBoard_bp.before_request
def before_request():
    if request.method == 'OPTIONS':
        return
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


@dashBoard_bp.route('/student_usage_count', methods=['POST'])  # 改为POST方法
def get_student_usage_count():
    """
    查询学生使用次数(JSON请求格式)
    请求体示例:
    {
        "student_id": 123,
        "operation_type": "提交作业",  // 可选
        "start_date": "2023-01-01",   // 可选
        "end_date": "2023-12-31"      // 可选
    }
    """
    # 获取JSON请求数据
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400
    
    # 获取参数
    student_id = data.get('student_id')
    if not student_id:
        return jsonify({'error': 'student_id is required'}), 400
    
    operation_type = data.get('operation_type')
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    
    # 构建查询
    query = StudentOperationLog.query.filter_by(student_id=student_id)
    
    # 添加可选过滤条件
    if operation_type:
        query = query.filter_by(operation_type=operation_type)
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            query = query.filter(StudentOperationLog.operation_time >= start_date)
        except ValueError:
            return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            query = query.filter(StudentOperationLog.operation_time <= end_date)
        except ValueError:
            return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
    
    # 获取总数
    total_count = query.count()
    
    # 按操作类型分组统计
    type_counts = db.session.query(
        StudentOperationLog.operation_type,
        db.func.count().label('count')
    ).filter_by(student_id=student_id)
    
    if start_date_str and end_date_str:
        type_counts = type_counts.filter(
            StudentOperationLog.operation_time.between(start_date, end_date)
        )
    
    type_counts = type_counts.group_by(
        StudentOperationLog.operation_type
    ).all()
    
    # 构造返回结果
    response = jsonify({
        'student_id': student_id,
        'total_operations': total_count,
        'operations_by_type': dict(type_counts)
    }), 200


@dashBoard_bp.route('/operation_logs', methods=['GET'])
def get_operation_logs():
    """
    获取操作日志(根据用户类型查询不同的日志表)
    查询参数:
    - user_type: 必须提供 ('student', 'teacher' 或 'admin')
    - user_id: 按用户ID筛选
    - operation_type: 按操作类型筛选
    - start_date: 开始日期 (YYYY-MM-DD)
    - end_date: 结束日期 (YYYY-MM-DD)
    - limit: 返回数量限制 (默认100)
    """
    from datetime import datetime
    
    user_type = request.args.get('user_type')
    if not user_type or user_type not in ['student', 'teacher', 'admin']:
        return jsonify({'error': 'Invalid user_type. Must be student, teacher or admin'}), 400
    
    # 获取其他查询参数
    user_id = request.args.get('user_id', type=int)
    operation_type = request.args.get('operation_type')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    limit = request.args.get('limit', default=100, type=int)
    
    # 根据用户类型选择不同的模型
    if user_type == 'student':
        model = StudentOperationLog
        id_field = 'student_id'
    elif user_type == 'teacher':
        model = TeacherOperationLog
        id_field = 'user_id'
    else:  # admin
        model = AdminOperationLog
        id_field = 'admin_id'
    
    # 构建基础查询
    query = db.session.query(model)
    # 添加过滤条件
    if user_id:
        query = query.filter(getattr(model, id_field) == user_id)
    if operation_type:
        query = query.filter(model.operation_type == operation_type)
    
    # 处理日期范围
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            query = query.filter(model.operation_time >= start_date)
        except ValueError:
            return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            query = query.filter(model.operation_time <= end_date)
        except ValueError:
            return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
    
    # 排序和限制
    logs = query.order_by(model.operation_time.desc()).limit(limit).all()
    
    # 构造返回结果
    result = []
    for log in logs:
        log_data = {
            'id': log.id,
            'user_id': getattr(log, id_field),
            'operation_type': log.operation_type,
            'operation_detail': log.operation_detail,
            'operation_time': log.operation_time.isoformat()
        }
        if user_type == 'admin':
            log_data['ip_address'] = log.ip_address
        result.append(log_data)
    
    return jsonify({'logs': result}), 200

@dashBoard_bp.after_request
def log_after_request(response):
    # 跳过预检请求和错误响应
    if request.method == 'OPTIONS' or not (200 <= response.status_code < 400):
        return response

    # 获取当前用户（兼容多种形式）
    current_user = getattr(g, 'current_user', None)
    
    # 处理User模型对象
    if current_user and hasattr(current_user, 'id'):  # 检查是否是模型对象
        user_info = {
            'id': current_user.id,  # 使用对象属性访问
            'role': getattr(current_user, 'role', 'unknown')
        }
    elif isinstance(current_user, dict):  # 兼容字典形式
        user_info = current_user
    else:
        return response  # 无有效用户信息

    # 需要记录日志的路由
    loggable_routes = ['/operation_logs', '/student_usage_count']
    
    if request.path in loggable_routes:
        LogService.log_operation(
            user_id=user_info['id'],
            user_type=user_info['role'],
            operation_type=f"{request.method}_{request.endpoint}",
            details={
                'path': request.path,
                'params': dict(request.args) if request.args else None,
                'status': response.status_code,
                'timestamp': datetime.now().isoformat()
            }
        )
    
    return response
