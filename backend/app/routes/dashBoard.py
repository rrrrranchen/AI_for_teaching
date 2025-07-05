from datetime import datetime
from flask import Blueprint, g, jsonify, request, session

from app.models.StudentOperationLog import StudentOperationLog
from app.utils.database import db
from app.services.log_service import LogService
from app.models.AdminOperationLog import AdminOperationLog
from app.models.TeacherOperationLog import TeacherOperationLog
from app.models.user import User
from datetime import datetime, timedelta

OPERATION_TYPE_MAPPING = {
    'GET_courseclass_get_courseclasses': '查看课程班级列表',
    'POST_courseclass_create_courseclass': '创建课程班级',
    'PUT_courseclass_update_courseclass': '更新课程班级',
    'DELETE_courseclass_delete_courseclass': '删除课程班级',
    
    # 学生相关
    'GET_student_get_student_info': '查看学生信息',
    'POST_student_submit_homework': '提交作业',
    'GET_student_view_materials': '查看学习资料',
    
    # 教师相关
    'GET_teacher_get_teaching_courses': '查看授课课程',
    'POST_teacher_grade_homework': '批改作业',
    'PUT_teacher_update_grade': '更新成绩'
}

REVERSE_OPERATION_MAPPING = {v: k for k, v in OPERATION_TYPE_MAPPING.items()}

dashboard_bp = Blueprint('dashBoard', __name__)

def is_logged_in():
    return 'user_id' in session

def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

@dashboard_bp.before_request
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

def get_friendly_operation_type(operation_type):
    """将原始操作类型转换为友好名称"""
    return OPERATION_TYPE_MAPPING.get(operation_type, operation_type)

def get_original_operation_type(friendly_name):
    """将友好名称转换回原始操作类型"""
    return REVERSE_OPERATION_MAPPING.get(friendly_name, friendly_name)



@dashboard_bp.route('/usage_count', methods=['POST'])
def get_user_usage_count():
    """
    统一查询用户使用次数(JSON请求格式)，支持学生和教师
    请求体示例:
    {
        "user_type": "student",  // 必填，"student"或"teacher"
        "user_id": 123,         // 必填
        "operation_type": "提交作业",  // 可选，可使用友好名称
        "time_range": "day"     // 必填，"day"表示当日，"week"表示本周
    }
    """
    # 获取JSON请求数据
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400
    
    # 获取参数
    user_type = data.get('user_type')
    if not user_type or user_type not in ['student', 'teacher']:
        return jsonify({'error': 'user_type is required and must be "student" or "teacher"'}), 400
    
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    time_range = data.get('time_range')
    if not time_range or time_range not in ['day', 'week']:
        return jsonify({'error': 'time_range is required and must be "day" or "week"'}), 400
    
    operation_type = data.get('operation_type')
    
    # 根据用户类型选择模型
    if user_type == 'student':
        model = StudentOperationLog
        id_field = 'student_id'
    else:
        model = TeacherOperationLog
        id_field = 'user_id'
    
    # 计算时间范围
    now = datetime.now()
    if time_range == 'day':
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        date_label = now.strftime('%Y-%m-%d')
    else:
        start_time = now - timedelta(days=now.weekday())
        start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(days=6, hours=23, minutes=59, seconds=59, microseconds=999999)
        date_label = f"{start_time.strftime('%Y-%m-%d')}至{(start_time + timedelta(days=6)).strftime('%Y-%m-%d')}"
    
    # 构建查询
    query = model.query.filter(
        getattr(model, id_field) == user_id,
        model.operation_time.between(start_time, end_time)
    )
    
    # 处理操作类型过滤
    if operation_type:
        # 检查是否是友好名称
        original_op_type = get_original_operation_type(operation_type)
        query = query.filter(model.operation_type == original_op_type)
    
    # 获取总数
    total_count = query.count()
    
    # 按操作类型分组统计
    type_counts = db.session.query(
        model.operation_type,
        db.func.count().label('count')
    ).filter(
        getattr(model, id_field) == user_id,
        model.operation_time.between(start_time, end_time)
    )
    
    if operation_type:
        type_counts = type_counts.filter(model.operation_type == original_op_type)
    
    type_counts = type_counts.group_by(model.operation_type).all()
    
    # 转换操作类型为友好名称
    friendly_type_counts = {
        get_friendly_operation_type(op_type): count 
        for op_type, count in type_counts
    }
    
    return jsonify({
        'user_type': user_type,
        'user_id': user_id,
        'time_range': time_range,
        'date_range': date_label,
        'total_operations': total_count,
        'operations_by_type': friendly_type_counts
    }), 200

@dashboard_bp.route('/available_operations', methods=['GET'])
def get_available_operations():
    """
    获取系统支持的所有操作类型及其友好名称
    可用于前端下拉框选择
    """
    # 可以从数据库查询实际存在的操作类型
    existing_types = set()
    
    # 查询学生日志中的操作类型
    student_types = db.session.query(
        StudentOperationLog.operation_type
    ).distinct().all()
    existing_types.update(t[0] for t in student_types)
    
    # 查询教师日志中的操作类型
    teacher_types = db.session.query(
        TeacherOperationLog.operation_type
    ).distinct().all()
    existing_types.update(t[0] for t in teacher_types)
    
    # 构建响应数据
    operations = []
    for op_type in sorted(existing_types):
        operations.append({
            'value': op_type,
            'label': get_friendly_operation_type(op_type),
            'category': op_type.split('_')[1]  # 按模块分类
        })
    
    return jsonify({'operations': operations}), 200


@dashboard_bp.route('/operation_logs', methods=['GET'])
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

@dashboard_bp.after_request
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
