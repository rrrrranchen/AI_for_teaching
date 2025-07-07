from datetime import datetime
import os
import uuid
from flask import Blueprint, current_app, g, jsonify, request, session
from app.utils.database import db
from app.models.user import User
from app.models.KnowledgeBase import KnowledgeBase
from app.models.Category import Category
from app.utils.create_kb import BASE_PATH, create_structured_db, create_unstructured_db

knowledge_management_bp=Blueprint('knowledge_management',__name__)


def is_logged_in():
    return 'user_id' in session

def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

@knowledge_management_bp.before_request
def before_request():
    # 检查用户是否已登录
    if request.method == 'OPTIONS':
        return
    if is_logged_in():
        # 获取当前用户并存储到 g 对象中
        g.current_user = get_current_user()
        # 检查用户是否为管理员
        if g.current_user and g.current_user.role != 'admin':
            return jsonify({'error': 'Forbidden'}), 403
    else:
        # 如果用户未登录，返回未授权错误
        return jsonify({'error': 'Unauthorized'}), 401
    


@knowledge_management_bp.route('/admin/knowledge_bases', methods=['GET'])
def admin_get_all_knowledge_bases():
    """管理员获取所有知识库（支持多条件分类查询）"""
    try:
        # 获取所有查询参数
        is_system = request.args.get('is_system')
        base_type = request.args.get('base_type')
        author_id = request.args.get('author_id')
        kb_name = request.args.get('name')  # 知识库名称模糊查询
        author_name = request.args.get('author_name')  # 作者名称模糊查询
        
        # 构建基础查询
        query = KnowledgeBase.query.options(
            db.joinedload(KnowledgeBase.categories).load_only(Category.id, Category.name),
            db.joinedload(KnowledgeBase.author).load_only(User.id, User.username)
        )
        
        # 添加过滤条件 - 系统属性
        if is_system is not None:
            is_system_bool = is_system.lower() == 'true'
            query = query.filter(KnowledgeBase.is_system == is_system_bool)
            
        # 添加过滤条件 - 类型
        if base_type:
            query = query.filter(KnowledgeBase.base_type == base_type)
            
        # 添加过滤条件 - 作者ID
        if author_id:
            try:
                author_id_int = int(author_id)
                query = query.filter(KnowledgeBase.author_id == author_id_int)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'INVALID_AUTHOR_ID',
                    'message': '作者ID必须是整数'
                }), 400
        
        # 添加过滤条件 - 知识库名称模糊查询
        if kb_name:
            # 使用不区分大小写的模糊查询
            query = query.filter(KnowledgeBase.name.ilike(f'%{kb_name}%'))
        
        # 添加过滤条件 - 作者名称模糊查询
        if author_name:
            # 使用不区分大小写的模糊查询并关联用户表
            query = query.join(KnowledgeBase.author).filter(User.username.ilike(f'%{author_name}%'))
        
        # 执行查询
        knowledge_bases = query.all()
        
        # 构建响应数据
        result = [{
            'id': kb.id,
            'name': kb.name,
            'description': kb.description,
            'author_id': kb.author_id,
            'author_name': kb.author.username if kb.author else None,
            'is_public': kb.is_public,
            'is_system': kb.is_system,
            'base_type': kb.base_type,
            'need_update': kb.need_update,
            'created_at': kb.created_at.isoformat(),
            'updated_at': kb.updated_at.isoformat() if kb.updated_at else None,
            'categories': [{'id': cat.id, 'name': cat.name} for cat in kb.categories]
        } for kb in knowledge_bases]
        
        # 添加查询参数信息到响应
        response = {
            'success': True,
            'data': result,
            'filters': {
                'is_system': is_system,
                'base_type': base_type,
                'author_id': author_id,
                'name': kb_name,
                'author_name': author_name
            },
            'result_count': len(result)
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    

@knowledge_management_bp.route('/admin/knowledge_bases', methods=['POST'])
def admin_create_knowledge_base():
    """管理员创建知识库（作者固定为当前管理员）"""
    data = request.get_json()
    
    # 基本参数验证
    required_fields = ['name', 'category_ids', 'base_type']
    if not data or any(field not in data for field in required_fields):
        return jsonify({
            'error': 'MISSING_REQUIRED_FIELDS',
            'message': f'缺少必要参数: {", ".join(required_fields)}'
        }), 400
    
    try:
        # 获取当前管理员ID
        admin_id = session.get('user_id')
        
        # 验证当前用户是否为管理员
        current_user = User.query.get(admin_id)
        # 获取类目信息
        categories = Category.query.filter(Category.id.in_(data['category_ids'])).all()
        if not categories:
            return jsonify({'error': 'INVALID_CATEGORY', 'message': '未找到指定类目'}), 400
        
        # 按类型分组类目
        unstructured_categories = []
        structured_categories = []
        
        for category in categories:
            if category.category_type == 'non_structural':
                unstructured_categories.append(category.stored_categoryname)
            elif category.category_type == 'structural':
                structured_categories.append(category.stored_categoryname)
        
        # 检查知识库类型是否与类目类型一致
        if data['base_type'] == 'non_structural' and structured_categories:
            return jsonify({'error': 'TYPE_MISMATCH', 'message': '知识库类型为非结构化，但存在结构化类目'}), 400
        elif data['base_type'] == 'structural' and unstructured_categories:
            return jsonify({'error': 'TYPE_MISMATCH', 'message': '知识库类型为结构化，但存在非结构化类目'}), 400
        
        # 生成唯一知识库名称
        db_name = data['name']
        unique_name = f"{uuid.uuid4()}_{db_name}"
        
        # 根据类目类型调用不同的创建函数
        if unstructured_categories:
            create_unstructured_db(unique_name, unstructured_categories)
        elif structured_categories:
            create_structured_db(unique_name, structured_categories)
        
        # 创建知识库数据库记录（作者固定为当前管理员）
        knowledge_base = KnowledgeBase(
            name=data['name'],
            stored_basename=unique_name,
            description=data.get('description', ''),
            author_id=admin_id,  # 固定为当前管理员ID
            is_public=data.get('is_public', False),
            is_system=True,
            file_path=os.path.join(BASE_PATH, unique_name),
            base_type=data['base_type'],
            need_update=data.get('need_update', False)
        )
        
        # 关联类目
        for category in categories:
            knowledge_base.categories.append(category)
        
        db.session.add(knowledge_base)
        db.session.commit()
        
        # 构造响应
        response_data = {
            'id': knowledge_base.id,
            'name': knowledge_base.name,
            'description': knowledge_base.description,
            'is_public': knowledge_base.is_public,
            'is_system': knowledge_base.is_system,
            'author_id': knowledge_base.author_id,
            'author_name': current_user.username,
            'created_at': knowledge_base.created_at.isoformat(),
            'file_path': knowledge_base.file_path,
            'categories': [{
                'id': cat.id,
                'name': cat.name,
                'type': cat.category_type
            } for cat in knowledge_base.categories],
            'message': '知识库创建成功'
        }
        
        return jsonify(response_data), 201
    
    except ValueError as e:
        return jsonify({'error': 'INVALID_REQUEST', 'message': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"知识库创建失败: {str(e)}", exc_info=True)
        return jsonify({'error': 'SERVER_ERROR', 'message': '知识库创建失败'}), 500


@knowledge_management_bp.route('/admin/knowledge_bases/<int:kb_id>', methods=['PUT'])
def admin_update_knowledge_base(kb_id):
    """管理员更新知识库（包括系统知识库）"""
    try:
        data = request.get_json()
        kb = KnowledgeBase.query.get(kb_id)
        if not kb:
            return jsonify({'success': False, 'error': 'KNOWLEDGE_BASE_NOT_FOUND'}), 404
        
        # 更新字段
        if 'name' in data:
            kb.name = data['name']
        if 'description' in data:
            kb.description = data['description']
        if 'is_public' in data:
            kb.is_public = data['is_public']
        
        
        kb.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '知识库更新成功',
            'updated_fields': list(data.keys())
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
