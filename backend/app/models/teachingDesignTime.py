from app.utils.database import db
from datetime import datetime
class TeachingDesignTime(db.Model):
    __tablename__ = 'teaching_design_time'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    design_id = db.Column(db.Integer, db.ForeignKey('teaching_design.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_seconds = db.Column(db.Integer, default=0)  # 累计总秒数
    last_start_time = db.Column(db.DateTime)  # 最后一次开始时间
    is_active = db.Column(db.Boolean, default=False)  # 是否正在计时
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # 关系定义
    design = db.relationship('TeachingDesign', backref='time_records')
    user = db.relationship('User', backref='design_time_records')

    def start_timer(self):
        self.last_start_time = datetime.utcnow()
        self.is_active = True
        db.session.commit()
    
    def pause_timer(self):
        if self.is_active and self.last_start_time:
            elapsed = (datetime.utcnow() - self.last_start_time).total_seconds()
            self.total_seconds += int(elapsed)
            self.is_active = False
            db.session.commit()
    
    def get_current_time(self):
        current_total = self.total_seconds
        if self.is_active and self.last_start_time:
            current_total += (datetime.utcnow() - self.last_start_time).total_seconds()
        return int(current_total)
