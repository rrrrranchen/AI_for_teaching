from datetime import datetime
from flask import Blueprint, jsonify, request

from app.models.StudentOperationLog import StudentOperationLog
from app.utils.database import db

dashBoard_bp = Blueprint('dashBoard', __name__)

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
    result = {
        'student_id': student_id,
        'total_operations': total_count,
        'operations_by_type': dict(type_counts)
    }
    
    return jsonify(result), 200