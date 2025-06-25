from datetime import datetime
from app.utils.database import db

class StudentOperationLog(db.Model):
    __tablename__ = 'student_operation_log'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    operation_type = db.Column(db.String(100), nullable=False)  # 操作类型，如“提交作业”、“查看课程”等
    operation_detail = db.Column(db.Text, nullable=False)  # 操作详情，具体描述操作内容
    operation_time = db.Column(db.DateTime, default=datetime.utcnow)  # 操作时间点

    student = db.relationship('User', back_populates='student_operation_logs')

    def __repr__(self):
        return f'<StudentOperationLog student_id={self.student_id}, operation_type={self.operation_type}, operation_detail={self.operation_detail}, operation_time={self.operation_time}>'