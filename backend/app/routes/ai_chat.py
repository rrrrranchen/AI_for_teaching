
from flask import Blueprint, current_app, session
from app.models.chat_history import ChatHistory
from app.models.CategoryFile import CategoryFile
from app.models.KnowledgeBase import KnowledgeBase
from app.models.Category import Category
from app.utils.database import db




from flask import Blueprint, request, jsonify, Response
from app.models.courseclass import Courseclass
from app.utils.ai_chat import chat_stream, chat_stream2
import json

from app.models.chat_history import ChatHistory
from app.models.user import User
from app.models.question import Question
from app.models.studentanswer import StudentAnswer

ai_chat_bp = Blueprint('ai_chat', __name__)
def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None
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

from flask import current_app


@ai_chat_bp.route('/course_class_chat/<int:chat_history_id>', methods=['POST'])
def course_class_chat(chat_history_id):
    """
    基于班级知识库的AI聊天接口（使用现有会话ID）
    请求参数 (JSON):
    {
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
        # 获取当前应用的实际对象（非代理）
        app = current_app._get_current_object()
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求体必须为JSON格式"}), 400
        
        # 验证必要参数
        required_fields = ['query', 'thinking_mode']
        if not all(field in data for field in required_fields):
            return jsonify({"error": "缺少必要字段: query, thinking_mode"}), 400
        
        # 获取会话记录
        chat_record = ChatHistory.query.filter_by(id=chat_history_id).first()
        if not chat_record:
            return jsonify({"error": "会话记录未找到"}), 404
        
        # 从会话记录中获取班级ID
        class_id = chat_record.courseclass_id
        if not class_id:
            return jsonify({"error": "该会话未关联班级"}), 400
        
        # 获取班级及关联知识库
        course_class = Courseclass.query.get(class_id)
        if not course_class:
            return jsonify({"error": "班级未找到"}), 404
        
        # 获取关联知识库的stored_basename列表
        db_names = [kb.stored_basename for kb in course_class.knowledge_bases]
        if not db_names:
            return jsonify({"error": "该班级未关联任何知识库"}), 400
        
        # 初始化名称解析器并预加载数据
        name_resolver = NameResolver()
        name_resolver.preload_names(db_names)
        
        # 从数据库加载现有对话历史
        existing_history = chat_record.get_content()
        
        # 如果是新会话（历史记录为空），则更新会话名称为问题的前7个字符
        if not existing_history and chat_record.name == "New Conversation":
            new_name = (data['query'][:12] + "...") if len(data['query']) > 12 else data['query']
            chat_record.name = new_name
            db.session.commit()  # 提前提交名称更新
        
        # 流式响应生成器
        def generate():
            # 在生成器内部手动创建应用上下文
            with app.app_context():
                formatted_sources = None
                new_messages = []
                full_response = ""
                thinking_content = ""  # 初始化思考内容变量
                
                # 重新获取会话记录（确保在应用上下文中）
                chat_record_internal = ChatHistory.query.filter_by(id=chat_history_id).first()
                if not chat_record_internal:
                    yield f"data: {json.dumps({'status': 'error', 'content': '会话记录未找到'})}\n\n"
                    return
                
                # 从数据库加载现有对话历史
                existing_history_internal = chat_record_internal.get_content()
                
                # 添加用户问题到临时历史
                current_history = existing_history_internal + [{
                    "id": len(existing_history_internal),
                    "role": "user",
                    "content": data['query']
                }]
                
                # 调用流式聊天函数
                for token, chunks, status, sources in chat_stream(
                    query=data['query'],
                    db_names=db_names,
                    model="deepseek-chat",
                    history=current_history,  # 使用包含新问题的完整历史
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
                        thinking_content += token  # 累积思考内容
                        yield f"data: {json.dumps({'status': 'reasoning', 'content': token})}\n\n"
                    
                    elif status in ["content", "tokens"]:
                        full_response += token  # 累积完整响应
                        yield f"data: {json.dumps({'status': 'content', 'content': token})}\n\n"
                    
                    elif status == "end":
                        # 构造助手回复
                        assistant_message = {
                            "id": len(existing_history_internal) + 1,
                            "role": "assistant",
                            "content": full_response,
                            "thinkingMode": data['thinking_mode'],
                            "thinkingContent": thinking_content,  # 添加思考内容
                            "sources": formatted_sources or {
                                "message": "未引用特定来源",
                                "sources": []
                            }
                        }
                        
                        # 添加到新消息列表
                        new_messages = [
                            {"id": len(existing_history_internal), "role": "user", "content": data['query']},
                            assistant_message
                        ]
                        
                        response_data = {
                            "status": "end",
                            "content": full_response,
                            "sources": formatted_sources or {
                                "message": "未引用特定来源",
                                "sources": []
                            }
                        }
                        yield f"data: {json.dumps(response_data)}\n\n"
                    
                    elif status == "error":
                        yield f"data: {json.dumps({'status': 'error', 'content': token})}\n\n"
                
                # 流结束后更新数据库
                if new_messages:
                    try:
                        # 重新获取记录（确保在应用上下文中）
                        updated_record = ChatHistory.query.filter_by(id=chat_history_id).first()
                        if updated_record:
                            # 获取最新历史记录并追加新消息
                            current_history = updated_record.get_content()
                            updated_history = current_history + new_messages
                            
                            # 安全设置内容
                            updated_record.set_content(updated_history)
                            db.session.commit()
                            
                            # 记录成功
                            app.logger.info(f"成功更新会话记录 ID: {chat_history_id}")
                    except Exception as e:
                        db.session.rollback()
                        app.logger.error(f"更新会话记录失败: {str(e)}")
                        # 尝试记录错误数据
                        try:
                            app.logger.debug(f"更新失败的数据: {str(new_messages)[:500]}")
                        except:
                            pass
        
        return Response(generate(), mimetype='text/event-stream')
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({"error": f"服务器内部错误: {str(e)}"}), 500

@ai_chat_bp.route('/create_conversation/<int:courseclass_id>', methods=['POST'])
def create_conversation(courseclass_id):
    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "Unauthorized"}), 401  # 用户未登录

    student_id = current_user.id

    # 初始化一个新的会话，默认名称和空内容
    new_chat_history = ChatHistory(
        courseclass_id=courseclass_id,
        student_id=student_id,
        name="New Conversation",  # 默认会话名称
        content=json.dumps([])    # 初始化为空对话列表
    )

    db.session.add(new_chat_history)
    db.session.commit()

    # 返回新创建的会话信息
    return jsonify({
        "success": True,
        "chat_id": new_chat_history.id,
        "name": new_chat_history.name,
        "created_at": new_chat_history.created_at.isoformat() if new_chat_history.created_at else None
    }), 201


@ai_chat_bp.route('/course_class_conversations/<int:courseclass_id>', methods=['GET'])
def get_course_class_conversations(courseclass_id):
    """
    获取指定课程班的所有对话记录
    返回: [{
        "id": 会话ID,
        "name": "会话名称",
        "created_at": "创建时间(ISO格式)"
    }]
    """
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "未授权访问"}), 401

        # 查询该课程班下当前用户的所有会话
        conversations = ChatHistory.query.filter_by(
            courseclass_id=courseclass_id,
            student_id=current_user.id
        ).order_by(ChatHistory.created_at.desc()).all()

        result = [{
            "id": conv.id,
            "name": conv.name,
            "created_at": conv.created_at.isoformat() if conv.created_at else None
        } for conv in conversations]

        return jsonify(result)

    except Exception as e:
        current_app.logger.error(f"获取课程班对话列表失败: {str(e)}")
        return jsonify({"error": "服务器内部错误"}), 500


@ai_chat_bp.route('/conversation_detail/<int:chat_history_id>', methods=['GET'])
def get_conversation_detail(chat_history_id):
    """
    获取指定会话的详细信息
    返回: {
        "id": 会话ID,
        "name": "会话名称",
        "created_at": "创建时间",
        "courseclass_id": 关联课程班ID,
        "messages": [对话历史],
        "student_id": 学生ID
    }
    """
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "未授权访问"}), 401

        # 查询会话记录
        conversation = ChatHistory.query.filter_by(
            id=chat_history_id,
            student_id=current_user.id  # 确保只能访问自己的会话
        ).first()

        if not conversation:
            return jsonify({"error": "会话记录未找到"}), 404

        return jsonify({
            "id": conversation.id,
            "name": conversation.name,
            "created_at": conversation.created_at.isoformat(),
            "courseclass_id": conversation.courseclass_id,
            "messages": conversation.get_content(),
            "student_id": conversation.student_id
        })

    except Exception as e:
        current_app.logger.error(f"获取会话详情失败: {str(e)}")
        return jsonify({"error": "服务器内部错误"}), 500
    
@ai_chat_bp.route('/update_conversation_name/<int:chat_history_id>', methods=['PUT'])
def update_conversation_name(chat_history_id):
    """
    修改会话名称
    请求参数 (JSON):
    {
        "new_name": "新的会话名称"  // 必填
    }
    """
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "未授权访问"}), 401

        data = request.get_json()
        if not data or 'new_name' not in data:
            return jsonify({"error": "缺少new_name参数"}), 400

        new_name = data['new_name'].strip()
        if not new_name:
            return jsonify({"error": "会话名称不能为空"}), 400

        # 查询并更新会话记录
        conversation = ChatHistory.query.filter_by(
            id=chat_history_id,
            student_id=current_user.id  # 确保只能修改自己的会话
        ).first()

        if not conversation:
            return jsonify({"error": "会话记录未找到"}), 404

        conversation.name = new_name
        db.session.commit()

        return jsonify({
            "success": True,
            "new_name": new_name,
            "chat_id": chat_history_id
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新会话名称失败: {str(e)}")
        return jsonify({"error": "服务器内部错误"}), 500

@ai_chat_bp.route('/question_chat/<int:question_id>', methods=['POST'])
def question_class_chat(question_id):
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
    响应格式 (SSE):
    {
        "type": "thinking|answer|sources|error",
        "content": "...",
        "metadata": {...}  // 可选附加信息
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
        question = Question.query.get(question_id)
        if not question:
            return jsonify({"error": "题目未找到"}), 404
        
        # 获取当前用户（学生）的作答记录
        current_user_id = get_current_user().id
        student_answer = None
        
        if current_user_id:
            student_answer = StudentAnswer.query.filter_by(
                student_id=current_user_id,
                question_id=question_id
            ).first()
        
        # 构建题目分析上下文
        question_context = ""
        if data.get('include_answer_analysis', False):
            question_context = f"""
            ### 题目信息
            题目ID: {question.id}
            题目类型: {question.type}
            题目内容: {question.content}
            正确答案: {question.correct_answer}
            题目解析: {question.analysis or "无"}
            """
            
            if student_answer:
                question_context += f"""
                ### 当前学生用户作答
                学生答案: {student_answer.answer}
                正确率: {student_answer.correct_percentage}%
                作答时间: {student_answer.answered_at.strftime('%Y-%m-%d %H:%M')}
                """
            
            # 将题目上下文添加到查询中
            data['query'] = f"{question_context}\n\n### 学生用户问题\n{data['query']}\n"
        
        # 流式响应生成器
        def generate():
            formatted_sources = None
            full_response = ""
            thinking_content = ""  # 初始化思考内容变量
            
            # 根据学生作答情况选择不同的流处理函数
            if student_answer:
                stream_generator = chat_stream(
                    query=data['query'],
                    db_names=db_names,
                    model="deepseek-chat",
                    history=data.get('history', []),
                    thinking_mode=data['thinking_mode'],
                    similarity_threshold=data.get('similarity_threshold', 0.2),
                    chunk_cnt=data.get('chunk_cnt', 5),
                    api_key=data.get('api_key'),
                    data_type_filter=data.get('data_type_filter')
                )
            else:
                stream_generator = chat_stream2(
                    query=data['query'],
                    db_names=db_names,
                    model="deepseek-chat",
                    history=data.get('history', []),
                    thinking_mode=data['thinking_mode'],
                    similarity_threshold=data.get('similarity_threshold', 0.2),
                    chunk_cnt=data.get('chunk_cnt', 5),
                    api_key=data.get('api_key'),
                    data_type_filter=data.get('data_type_filter')
                )
            
            # 统一处理流式响应
            for token, chunks, status, sources in stream_generator:
                if status == "chunks":
                    # 格式化来源信息
                    formatted_sources = format_sources(sources, name_resolver) if sources else {
                        "message": "未引用特定来源",
                        "sources": []
                    }
                    yield f"data: {json.dumps({'status': 'chunks', 'content': chunks})}\n\n"
                
                elif status == "reasoning":
                    thinking_content += token  # 累积思考内容
                    yield f"data: {json.dumps({'status': 'reasoning', 'content': token})}\n\n"
                
                elif status in ["content", "tokens"]:
                    full_response += token  # 累积完整响应
                    yield f"data: {json.dumps({'status': 'content', 'content': token})}\n\n"
                
                elif status == "end":
                    response_data = {
                        "status": "end",
                        "content": full_response,
                        "sources": formatted_sources or {
                            "message": "未引用特定来源",
                            "sources": []
                        }
                    }
                    yield f"data: {json.dumps(response_data)}\n\n"
                
                elif status == "error":
                    yield f"data: {json.dumps({'status': 'error', 'content': token})}\n\n"

        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "服务器内部错误",
            "details": str(e)
        }), 500