from app.utils.database import db
from datetime import datetime


class TeacherOperationLog(db.Model):
    __tablename__ = 'teacher_operation_log'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    operation_type = db.Column(db.String(100), nullable=False)  # 操作类型，如“创建课程”、“编辑教学设计”等
    operation_detail = db.Column(db.Text, nullable=False)  
    operation_time = db.Column(db.DateTime, default=datetime.utcnow)  

    user = db.relationship('User', back_populates='operation_logs')

    def __repr__(self):
        return f'<TeacherOperationLog user_id={self.user_id}, operation_type={self.operation_type}, operation_detail={self.operation_detail}, operation_time={self.operation_time}>'
