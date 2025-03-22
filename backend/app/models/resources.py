from mongoengine import Document, StringField, IntField, ObjectIdField, DateTimeField, ListField, EmbeddedDocument, EmbeddedDocumentField
from datetime import datetime

class Metadata(EmbeddedDocument):
    duration = IntField()  # 视频/音频时长（秒）
    resolution = StringField()  # 分辨率（如1920x1080）
    file_size = IntField()  # 文件大小（MB）
    format = StringField()  # 文件格式（如mp4/png/docx）

class MultimediaResource(Document):
    _id = ObjectIdField(required=True, primary_key=True, default=lambda: ObjectId())
    type = StringField(required=True, choices=("image", "video", "ppt", "doc"))
    title = StringField(required=True)
    course_id = IntField(required=True)  # 关联MySQL的course.id
    class_ids = ListField(IntField(), required=True)  # 适用的班级ID数组
    knowledge_tags = ListField(StringField(), required=True)  # 知识点标签
    uploader_id = IntField(required=True)  # 上传者ID（关联user.id）
    storage_path = StringField(required=True)  # 云存储路径
    preview_url = StringField(required=True)  # 缩略图/预览地址
    metadata = EmbeddedDocumentField(Metadata, required=True)  # 技术元数据
    created_at = DateTimeField(default=datetime.utcnow)

    def __repr__(self):
        return f'<MultimediaResource {self._id}>'