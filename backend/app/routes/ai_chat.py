
from flask import Blueprint, current_app

from app.models.CategoryFile import CategoryFile
from app.models.KnowledgeBase import KnowledgeBase
from app.models.Category import Category
from app.utils.database import db

ai_chat_bp = Blueprint('ai_chat', __name__)


from flask import Blueprint, request, jsonify, Response
from app.models.courseclass import Courseclass
from app.utils.create_kb import chat_stream
import json

ai_chat_bp = Blueprint('ai_chat', __name__)

class NameResolver:
    """名称解析器，用于高效查询显示名称"""
    def __init__(self):
        self.kb_cache = {}  # {stored_basename: {'id': int, 'name': str}}
        self.category_cache = {}  # {stored_categoryname: {'id': int, 'name': str}}
        self.file_cache = {}  # {stored_filename: {'id': int, 'name': str}}
    
    def preload_names(self, stored_basenames):
        """预加载所有可能需要的显示名称"""
        # 1. 加载知识库信息
        kbs = KnowledgeBase.query.filter(
            KnowledgeBase.stored_basename.in_(stored_basenames)
        ).all()
        self.kb_cache = {
            kb.stored_basename: {
                'id': kb.id,
                'name': kb.name
            } for kb in kbs
        }
        
        # 2. 加载关联类目
        kb_ids = [kb.id for kb in kbs]
        categories = db.session.query(Category).join(
            Category.knowledge_bases
        ).filter(
            KnowledgeBase.id.in_(kb_ids)
        ).all()
        self.category_cache = {
            cat.stored_categoryname: {
                'id': cat.id,
                'name': cat.name
            } for cat in categories
        }
        
        # 3. 加载关联文件
        category_ids = [cat.id for cat in categories]
        files = CategoryFile.query.filter(
            CategoryFile.category_id.in_(category_ids)
        ).all()
        self.file_cache = {
            file.stored_filename: {
                'id': file.id,
                'name': file.name
            } for file in files
        }

def format_sources(sources, name_resolver):
    """格式化来源信息"""
    if not sources:
        return {
            "message": "本次回答未引用特定来源",
            "sources": []
        }
    
    result = []
    for kb_stored_name, categories in sources.items():
        # 获取知识库信息
        kb_info = name_resolver.kb_cache.get(kb_stored_name) or {
            'id': None,
            'name': kb_stored_name
        }
        
        for cat_stored_name, files in categories.items():
            # 获取类目信息
            cat_info = name_resolver.category_cache.get(cat_stored_name) or {
                'id': None,
                'name': cat_stored_name
            }
            
            for file_stored_name, chunks in files.items():
                # 获取文件信息
                file_info = name_resolver.file_cache.get(file_stored_name) or {
                    'id': None,
                    'name': file_stored_name
                }
                
                # 构建片段信息
                chunk_details = []
                for chunk in chunks:
                    chunk_details.append({
                        "position": chunk.get('position'),
                        "text": chunk.get('text'),
                        "similarity": chunk.get('similarity'),
                        "metadata": chunk.get('metadata', {})
                    })
                
                # 构建完整来源对象
                result.append({
                    "knowledge_base": {
                        "id": kb_info['id'],
                        "name": kb_info['name']
                    },
                    "category": {
                        "id": cat_info['id'],
                        "name": cat_info['name']
                    },
                    "file": {
                        "id": file_info['id'],
                        "name": file_info['name']
                    },
                    "chunks": chunk_details
                })
    
    return {
        "message": f"本次回答参考了 {len(result)} 个来源",
        "source_count": len(result),
        "sources": result
    }

@ai_chat_bp.route('/course_class_chat', methods=['POST'])
def course_class_chat():
    """
    基于班级知识库的AI聊天接口
    请求参数 (JSON):
    {
        "class_id": 123,               // 班级ID (必填)
        "query": "如何安装Python?",     // 用户问题 (必填)
        "thinking_mode": true,         // 是否思考模式 (必填)
        "history": [],                 // 对话历史 (可选)
        "similarity_threshold": 0.2,   // 相似度阈值 (可选)
        "chunk_cnt": 5,                // 返回片段数 (可选)
        "api_key": "your-api-key",     // 自定义API密钥 (可选)
        "data_type_filter": null       // 数据类型过滤 (可选)
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求体必须为JSON格式"}), 400
        
        # 验证必要参数
        required_fields = ['class_id', 'query', 'thinking_mode']
        if not all(field in data for field in required_fields):
            return jsonify({"error": "缺少必要字段: class_id, query, thinking_mode"}), 400
        
        # 获取班级及关联知识库
        course_class = Courseclass.query.get(data['class_id'])
        if not course_class:
            return jsonify({"error": "班级未找到"}), 404
        
        # 获取关联知识库的stored_basename列表
        db_names = [kb.stored_basename for kb in course_class.knowledge_bases]
        if not db_names:
            return jsonify({"error": "该班级未关联任何知识库"}), 400
        
        # 初始化名称解析器并预加载数据
        name_resolver = NameResolver()
        name_resolver.preload_names(db_names)
        
        # 流式响应生成器
        def generate():
            formatted_sources = None
            
            for token, chunks, status, sources in chat_stream(
                query=data['query'],
                db_names=db_names,
                model="deepseek-chat",
                history=data.get('history', []),
                thinking_mode=data['thinking_mode'],
                similarity_threshold=data.get('similarity_threshold', 0.2),
                chunk_cnt=data.get('chunk_cnt', 5),
                api_key=data.get('api_key'),
                data_type_filter=data.get('data_type_filter')
            ):
                if status == "chunks":
                    # 格式化来源信息
                    formatted_sources = format_sources(sources, name_resolver) if sources else {
                        "message": "未引用特定来源",
                        "sources": []
                    }
                    yield f"data: {json.dumps({'status': 'chunks', 'content': chunks})}\n\n"
                
                elif status == "reasoning":
                    yield f"data: {json.dumps({'status': 'reasoning', 'content': token})}\n\n"
                
                elif status in ["content", "tokens"]:
                    yield f"data: {json.dumps({'status': 'content', 'content': token})}\n\n"
                
                elif status == "end":
                    response_data = {
                        "status": "end",
                        "content": token,
                        "sources": formatted_sources or {
                            "message": "未引用特定来源",
                            "sources": []
                        }
                    }
                    yield f"data: {json.dumps(response_data)}\n\n"
                
                elif status == "error":
                    yield f"data: {json.dumps({'status': 'error', 'content': token})}\n\n"
        
        return Response(generate(), mimetype='text/event-stream')
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"服务器内部错误: {str(e)}"}), 500