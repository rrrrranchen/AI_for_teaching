from flask import request
from datetime import datetime
from app.models.StudentOperationLog import StudentOperationLog
from app.models.TeacherOperationLog import TeacherOperationLog
from app.models.AdminOperationLog import AdminOperationLog
from app.utils.database import db

class LogService:
    @staticmethod
    def log_operation(user_id, user_type, operation_type, details=None):
        """通用日志记录方法"""
        # 根据用户类型选择模型类
        log_models = {
            'admin': AdminOperationLog,
            'teacher': TeacherOperationLog,
            'student': StudentOperationLog
        }
        
        if user_type not in log_models:
            raise ValueError(f"不支持的日志类型: {user_type}")

        try:
            # 动态设置用户ID字段
            log_data = {
                'operation_type': operation_type,
                'operation_detail': str(details),
                'operation_time': datetime.now()
            }
            
            # 特殊字段处理
            if user_type == 'admin':
                log_data['admin_id'] = user_id
                log_data['ip_address'] = request.remote_addr
            elif user_type == 'teacher':
                log_data['user_id'] = user_id
            else:  # student
                log_data['student_id'] = user_id

            # 创建日志记录
            log_class = log_models[user_type]
            log = log_class(**log_data)
            
            db.session.add(log)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"[LogService] 日志记录失败: {str(e)}")
            return False

    @staticmethod
    def verify_log_exists(user_type):
        """验证日志是否成功写入数据库"""
        log_models = {
            'admin': AdminOperationLog,
            'teacher': TeacherOperationLog,
            'student': StudentOperationLog
        }
        
        if user_type not in log_models:
            return False
        
        try:
            count = db.session.query(log_models[user_type]).count()
            print(f"[验证] {user_type}类型日志记录数: {count}")
            return count > 0
        except Exception as e:
            print(f"[验证] 查询失败: {str(e)}")
            return False


    @staticmethod
    def log_request(response, user_info=None):
        """统一处理请求日志记录"""
        # 不记录 OPTIONS 请求和错误响应
        if request.method == 'OPTIONS' or not (200 <= response.status_code < 400):
            return response
        
        # 不记录日志查询请求本身（避免递归）
        if request.path == '/operation_logs':
            return response
        
        # 如果没有用户信息，也不记录
        if not user_info or not user_info.get('id'):
            return response
        
        # 正常记录其他请求
        try:
            operation_type = f"{request.method.lower()}_{request.endpoint.replace('.', '_')}"
            details = {
                'path': request.path,
                'params': dict(request.args) if request.args else None,
                'status': response.status_code,
                'timestamp': datetime.now().isoformat()
            }
            
            LogService.log_operation(
                user_id=user_info.get('id'),
                user_type=user_info.get('role', 'admin'),
                operation_type=operation_type,
                details=details
            )
        except Exception as e:
            print(f"[LogService] 请求日志处理异常: {str(e)}")
        
        return response
