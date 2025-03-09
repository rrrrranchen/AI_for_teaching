from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from app.utils.database import db

class MediaResource(db.Model):
    __tablename__ = 'media_resource'

    id = db.Column(db.Integer, primary_key=True)
    lesson_plan_id = db.Column(db.Integer, db.ForeignKey('lesson_plan.id'), nullable=False)
    type = db.Column(db.Enum('image', 'video', 'audio', name='media_type'), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<MediaResource {self.id}>'