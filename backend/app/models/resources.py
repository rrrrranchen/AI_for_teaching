from bson import ObjectId
from mongoengine import Document, StringField, IntField, ObjectIdField, DateTimeField, ListField, EmbeddedDocument, EmbeddedDocumentField, DictField
from datetime import datetime
from mongoengine import BooleanField

class Metadata(EmbeddedDocument):
    # 通用元数据字段
    file_size = IntField(required=True)  # 文件大小（字节）
    format = StringField(required=True)  # 文件扩展名（小写，如pdf/mp4）
    mime_type = StringField()  # MIME类型（如application/pdf）
    
    # 媒体相关字段
    duration = IntField()  # 视频/音频时长（秒）
    resolution = StringField()  # 分辨率（如1920x1080）
    bitrate = IntField()  # 比特率（音频/视频）
    
    # 文档相关字段
    page_count = IntField()  # PDF/PPT页数
    word_count = IntField()  # 文档字数估算
    author = StringField()  # 文档作者
    
    # 图像相关字段
    color_mode = StringField()  # RGB/CMYK等
    dpi = IntField()  # 打印分辨率
    
    # 扩展元数据（用于存储特殊字段）
    extra = DictField()  # 存储其他工具特定元数据

class MultimediaResource(Document):
    _id = ObjectIdField(required=True, primary_key=True, default=lambda: ObjectId())
    
    # 基础信息
    type = StringField(required=True, choices=(
        "image", "video", "audio", 
        "document", "presentation", "spreadsheet",
        "archive", "ebook", "other"
    ))
    title = StringField(required=True, max_length=200)
    description = StringField(max_length=500)
    
    # 系统关联
    course_id = IntField(required=False)  # 关联MySQL的course.id
    class_ids = ListField(IntField(), required=False, default=list)  # 适用的班级ID数组
    uploader_id = IntField(required=True)  # 上传者ID（关联user.id）
    
    # 存储信息
    storage_path = StringField(required=True)  # 物理存储路径
    storage_service = StringField(choices=("local", "s3", "oss"), default="local")
    preview_urls = DictField()  # 不同尺寸的预览图 {"thumbnail": "...", "medium": "..."}
    
    # 技术元数据
    metadata = EmbeddedDocumentField(Metadata, required=True)
    
    # 状态标记
    is_processed = BooleanField(default=False)  # 是否已完成处理
    is_public = BooleanField(default=False)  # 是否公开可见
    is_teaching_design = BooleanField(default=False)  # 是否为教学设计，默认为 False
    # 时间信息
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField()
    
    # 索引配置
    meta = {
        'indexes': [
            'course_id',
            'class_ids',
            'uploader_id',
            'type',
            {'fields': ['created_at'], 'expireAfterSeconds': 3600*24*365}  # 自动过期（示例）
        ],
        'ordering': ['-created_at']
    }

    def clean(self):
        """在保存前自动更新修改时间"""
        self.updated_at = datetime.utcnow()

    def generate_previews(self):
        """生成预览图的抽象方法（需子类实现）"""
        raise NotImplementedError

    def get_download_url(self):
        """获取下载URL的抽象方法"""
        if self.storage_service == "local":
            return f"/downloads/{self._id}"
        elif self.storage_service == "s3":
            return f"https://{self.storage_path}"
        return None

    def __repr__(self):
        return f'<MultimediaResource {self._id} ({self.type})>'