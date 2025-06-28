from datetime import datetime
from app.utils.database import db


class PPTTemplate(db.Model):
    """
    PPT模板数据模型
    """
    __tablename__ = 'ppt_templates'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 主键
    name = db.Column(db.String(255), nullable=False, unique=True)  # 模板名称
    url = db.Column(db.String(500), nullable=False)  # 模板的URL
    image_url = db.Column(db.String(500), nullable=False)  # 展示图片的URL

    def __repr__(self):
        return f"PPTTemplate(name={self.name}, url={self.url}, image_url={self.image_url})"