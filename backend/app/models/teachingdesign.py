from mongoengine import Document, StringField, IntField, ObjectIdField, DateTimeField, ListField, EmbeddedDocument, EmbeddedDocumentField
from datetime import datetime
from bson import ObjectId


class Assessment(EmbeddedDocument):
    criteria = ListField(StringField(), required=True)
    question_bank = ListField(IntField(), required=True)
    assessresult = StringField()  # 添加评估结果字段
    recommend_rate = IntField()   # 添加推荐指数字段
    
class InteractionFlow(EmbeddedDocument):
    type = StringField(required=True)
    description = StringField(required=True)
    trigger_time = IntField(required=True)

class TimePlan(EmbeddedDocument):
    phase = StringField(required=True)
    duration = IntField(required=True)
    content = StringField(required=True)

class Content(EmbeddedDocument):
    objectives = ListField(StringField(), required=True)
    total_time = IntField(required=True)
    resources = ListField(ObjectIdField(), required=True)
    key_point = ListField(StringField(), required=True)
    time_plan = ListField(EmbeddedDocumentField(TimePlan), required=True)
    interaction_flows = ListField(EmbeddedDocumentField(InteractionFlow), required=True)
    assessment = EmbeddedDocumentField(Assessment, required=True)

class ModifiedActivity(EmbeddedDocument):
    original = StringField(required=True)
    revised = StringField(required=True)

class TeacherFeedback(EmbeddedDocument):
    modified_activities = ListField(EmbeddedDocumentField(ModifiedActivity))

# 主文档
# 教学方案设计表
class TeachingDesign(Document):
    course_id = IntField(required=True)
    version = IntField(required=True)
    status = StringField(choices=("draft", "published"), required=True)
    generated_by = StringField(choices=("AI", "teacher"), required=True)
    content = EmbeddedDocumentField(Content, required=True)
    teacher_feedback = EmbeddedDocumentField(TeacherFeedback)
    created_at = DateTimeField(default=datetime.utcnow)

    def __repr__(self):
        return f'<TeachingDesign {self.id}>'

