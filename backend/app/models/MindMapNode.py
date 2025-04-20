from datetime import datetime
from bson import ObjectId
from app.utils.database import db

class MindMapNode(db.Model):
    __tablename__ = 'mind_map_node'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    teachingdesignid = db.Column(
        db.Integer, 
        db.ForeignKey('teaching_design.id'),
        nullable=False
    )
    node_name = db.Column(db.String(255), nullable=False)
    node_content = db.Column(db.Text)
    parent_node_id = db.Column(
        db.Integer, 
        db.ForeignKey('mind_map_node.id', ondelete='CASCADE')
    )
    is_leaf = db.Column(db.Boolean, default=True)
    ai_analysis = db.Column(db.Text, nullable=True)

    # 定义与 MindMapNode 表的自关联关系
    parent_node = db.relationship(
        'MindMapNode',
        remote_side=[id],
        back_populates='children'
    )
    # 定义子节点关系，启用级联删除
    children = db.relationship(
        'MindMapNode',
        back_populates='parent_node',
        cascade='all, delete-orphan'
    )