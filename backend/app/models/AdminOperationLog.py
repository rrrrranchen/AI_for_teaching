from datetime import datetime
from app.utils.database import db


class AdminOperationLog(db.Model):
    __tablename__ = 'admin_operation_log'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    operation_type = db.Column(db.String(100), nullable=False)  # 操作类型，如“创建用户”、“删除课程”等
    operation_detail = db.Column(db.Text, nullable=False)  # 操作详情，具体描述操作内容
    operation_time = db.Column(db.DateTime, default=datetime.utcnow)  # 操作时间点
    ip_address = db.Column(db.String(45), nullable=True)  # 操作时的IP地址

    admin = db.relationship('User', back_populates='admin_operation_logs')

    def __repr__(self):
        return f'<AdminOperationLog admin_id={self.admin_id}, operation_type={self.operation_type}, operation_detail={self.operation_detail}, operation_time={self.operation_time}>'