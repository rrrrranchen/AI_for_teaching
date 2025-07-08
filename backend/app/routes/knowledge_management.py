from datetime import datetime
import os
import shutil
import uuid
from flask import Blueprint, current_app, g, jsonify, request, session
from app.utils.database import db
from app.models.user import User
from app.models.KnowledgeBase import KnowledgeBase
from app.models.Category import Category
from app.utils.create_kb import BASE_PATH, CATEGORY_PATH, create_structured_db, create_unstructured_db
from app.routes.knowledge_for_teachers import delete_file_resources, update_single_knowledge_base
from app.models.CategoryFile import CategoryFile
from app.models.CategoryFileImage import CategoryFileImage
from app.utils.create_cat import UPLOAD_FOLDER_KNOWLEDGE, allowed_file_non_structural, allowed_file_structural, create_user_category_folder, upload_file_to_folder_non_structural, upload_file_to_folder_structural
from werkzeug.utils import secure_filename
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
    


@knowledge_management_bp.route('/admin/knowledge_bases', methods=['POST'])
def admin_get_all_knowledge_bases():
    """管理员获取所有知识库（支持多条件分类查询）"""
    try:
        # 获取JSON格式的请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'INVALID_REQUEST',
                'message': '请求数据必须是JSON格式'
            }), 400

        # 从请求数据中获取查询参数
        is_system = data.get('is_system')
        base_type = data.get('base_type')
        author_id = data.get('author_id')
        kb_name = data.get('name')  # 知识库名称模糊查询
        author_name = data.get('author_name')  # 作者名称模糊查询
        page = data.get('page', 1)  # 分页参数，默认为1
        per_page = data.get('per_page', 20)  # 每页数量，默认为20

        # 验证分页参数
        try:
            page = int(page)
            per_page = int(per_page)
            if page < 1 or per_page < 1:
                raise ValueError
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'INVALID_PAGINATION',
                'message': '分页参数必须是正整数'
            }), 400

        # 构建基础查询
        query = KnowledgeBase.query.options(
            db.joinedload(KnowledgeBase.categories).load_only(Category.id, Category.name),
            db.joinedload(KnowledgeBase.author).load_only(User.id, User.username)
        )

        # 添加过滤条件 - 系统属性
        if is_system is not None:
            if isinstance(is_system, bool):
                query = query.filter(KnowledgeBase.is_system == is_system)
            else:
                return jsonify({
                    'success': False,
                    'error': 'INVALID_SYSTEM_FLAG',
                    'message': 'is_system参数必须是布尔值'
                }), 400

        # 添加过滤条件 - 类型
        if base_type:
            query = query.filter(KnowledgeBase.base_type == base_type)

        # 添加过滤条件 - 作者ID
        if author_id is not None:
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

        # 执行分页查询
        paginated_kbs = query.paginate(page=page, per_page=per_page, error_out=False)

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
        } for kb in paginated_kbs.items]

        # 构造响应
        response = {
            'success': True,
            'data': result,
            'pagination': {
                'total': paginated_kbs.total,
                'pages': paginated_kbs.pages,
                'current_page': paginated_kbs.page,
                'per_page': paginated_kbs.per_page,
                'has_next': paginated_kbs.has_next,
                'has_prev': paginated_kbs.has_prev
            },
            'filters': {
                'is_system': is_system,
                'base_type': base_type,
                'author_id': author_id,
                'name': kb_name,
                'author_name': author_name
            }
        }

        return jsonify(response), 200

    except Exception as e:
        current_app.logger.error(
            f"管理员获取知识库失败 - Error: {str(e)}",
            exc_info=True
        )
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500
    

@knowledge_management_bp.route('/admin/knowledge_bases/create', methods=['POST'])
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

@knowledge_management_bp.route('/admin/knowledge_bases/batch', methods=['DELETE'])
def admin_batch_delete_knowledge_bases():
    """管理员批量删除知识库"""
    try:
        # 获取要删除的知识库ID列表
        data = request.get_json()
        if not data or 'kb_ids' not in data:
            return jsonify({
                'success': False,
                'error': 'INVALID_REQUEST',
                'message': '请求数据必须包含kb_ids字段'
            }), 400

        kb_ids = data['kb_ids']
        if not isinstance(kb_ids, list) or len(kb_ids) == 0:
            return jsonify({
                'success': False,
                'error': 'INVALID_PARAMETER',
                'message': 'kb_ids必须是包含至少一个元素的数组'
            }), 400

        # 查询所有要删除的知识库
        knowledge_bases = KnowledgeBase.query.filter(KnowledgeBase.id.in_(kb_ids)).all()
        
        if not knowledge_bases:
            return jsonify({
                'success': False,
                'error': 'NOT_FOUND',
                'message': '未找到指定的知识库'
            }), 404

        # 记录删除结果
        deleted_ids = []
        failed_ids = []
        
        for kb in knowledge_bases:
            try:
                # 删除物理文件夹
                full_path = os.path.join(
                    UPLOAD_FOLDER_KNOWLEDGE, 
                    kb.file_path.replace('static/knowledge/', '')
                )
                if os.path.exists(full_path):
                    shutil.rmtree(full_path)
                
                # 标记删除数据库记录
                db.session.delete(kb)
                deleted_ids.append(kb.id)
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(
                    f"删除知识库 {kb.id} 失败 - Error: {str(e)}",
                    exc_info=True
                )
                failed_ids.append({
                    'id': kb.id,
                    'error': str(e)
                })

        # 提交所有成功的删除操作
        db.session.commit()

        response = {
            'success': True,
            'data': {
                'deleted_count': len(deleted_ids),
                'deleted_ids': deleted_ids,
                'failed_count': len(failed_ids),
                'failed_ids': failed_ids
            }
        }

        if failed_ids:
            response['success'] = False
            response['error'] = 'PARTIAL_SUCCESS'
            response['message'] = '部分知识库删除失败'

        return jsonify(response), 200 if not failed_ids else 207

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"批量删除知识库失败 - Error: {str(e)}",
            exc_info=True
        )
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500

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
    

@knowledge_management_bp.route('/admin/knowledge_bases/<int:kb_id>/categories/batch_add', methods=['POST'])
def admin_batch_add_categories_to_knowledge_base(kb_id):
    """管理员为知识库批量添加类目"""
    try:
        data = request.get_json()
        if not data or 'category_ids' not in data or not isinstance(data['category_ids'], list):
            return jsonify({
                'success': False,
                'error': 'MISSING_REQUIRED_FIELDS',
                'message': '缺少category_ids参数或参数格式不正确'
            }), 400

        # 验证知识库存在性
        kb = KnowledgeBase.query.get(kb_id)
        if not kb:
            return jsonify({
                'success': False,
                'error': 'KNOWLEDGE_BASE_NOT_FOUND'
            }), 404

        # 获取所有类目
        categories = Category.query.filter(Category.id.in_(data['category_ids'])).all()
        if len(categories) != len(data['category_ids']):
            return jsonify({
                'success': False,
                'error': 'CATEGORY_NOT_FOUND',
                'message': '部分类目未找到'
            }), 404

        added_categories = []
        duplicate_categories = []
        type_mismatch_categories = []

        for category in categories:
            # 检查类目是否已关联
            if category in kb.categories:
                duplicate_categories.append({
                    'id': category.id,
                    'name': category.name
                })
                continue

            # 检查类目类型是否匹配
            if (kb.base_type == 'non_structural' and category.category_type != 'non_structural') or \
               (kb.base_type == 'structural' and category.category_type != 'structural'):
                type_mismatch_categories.append({
                    'id': category.id,
                    'name': category.name,
                    'type': category.category_type
                })
                continue

            # 添加类目关联
            kb.categories.append(category)
            added_categories.append({
                'id': category.id,
                'name': category.name,
                'type': category.category_type
            })

        if not added_categories:
            return jsonify({
                'success': False,
                'error': 'NO_VALID_CATEGORIES',
                'message': '没有有效的类目可添加',
                'duplicates': duplicate_categories,
                'type_mismatches': type_mismatch_categories
            }), 400

        kb.need_update = True  # 标记需要更新
        kb.updated_at = datetime.utcnow()
        db.session.commit()

        # 自动更新知识库
        try:
            update_single_knowledge_base(kb)
            return jsonify({
                'success': True,
                'message': '类目批量添加成功且知识库已更新',
                'added_categories': added_categories,
                'duplicates': duplicate_categories,
                'type_mismatches': type_mismatch_categories,
                'knowledge_base_id': kb.id,
                'knowledge_base_name': kb.name,
                'is_system': kb.is_system
            }), 200
        except Exception as update_error:
            db.session.rollback()
            current_app.logger.error(
                f"系统知识库自动更新失败 - KB ID: {kb.id}, Error: {str(update_error)}",
                exc_info=True
            )
            return jsonify({
                'success': False,
                'error': 'AUTO_UPDATE_FAILED',
                'message': '类目批量添加成功但知识库更新失败，请手动更新',
                'added_categories': added_categories,
                'duplicates': duplicate_categories,
                'type_mismatches': type_mismatch_categories,
                'knowledge_base_id': kb.id
            }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"管理员批量添加类目失败 - KB ID: {kb_id}, Error: {str(e)}",
            exc_info=True
        )
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


@knowledge_management_bp.route('/admin/knowledge_bases/<int:kb_id>/categories/batch_remove', methods=['POST'])
def admin_batch_remove_categories_from_knowledge_base(kb_id):
    """管理员从知识库批量删除类目"""
    try:
        data = request.get_json()
        if not data or 'category_ids' not in data or not isinstance(data['category_ids'], list):
            return jsonify({
                'success': False,
                'error': 'MISSING_REQUIRED_FIELDS',
                'message': '缺少category_ids参数或参数格式不正确'
            }), 400

        # 验证知识库存在性
        kb = KnowledgeBase.query.get(kb_id)
        if not kb:
            return jsonify({
                'success': False,
                'error': 'KNOWLEDGE_BASE_NOT_FOUND'
            }), 404

        removed_categories = []
        not_linked_categories = []

        for category_id in data['category_ids']:
            # 检查类目是否关联
            category = next((cat for cat in kb.categories if cat.id == category_id), None)
            if not category:
                not_linked_categories.append(category_id)
                continue

            # 移除类目关联
            kb.categories.remove(category)
            removed_categories.append({
                'id': category.id,
                'name': category.name
            })

        if not removed_categories:
            return jsonify({
                'success': False,
                'error': 'NO_VALID_CATEGORIES',
                'message': '没有有效的类目可移除',
                'not_linked': not_linked_categories
            }), 400

        kb.need_update = True  # 标记需要更新
        kb.updated_at = datetime.utcnow()
        db.session.commit()

        # 自动更新知识库
        try:
            update_single_knowledge_base(kb)
            return jsonify({
                'success': True,
                'message': '类目批量移除成功且知识库已更新',
                'removed_categories': removed_categories,
                'not_linked': not_linked_categories,
                'knowledge_base_id': kb.id,
                'knowledge_base_name': kb.name,
                'is_system': kb.is_system
            }), 200
        except Exception as update_error:
            db.session.rollback()
            current_app.logger.error(
                f"系统知识库自动更新失败 - KB ID: {kb.id}, Error: {str(update_error)}",
                exc_info=True
            )
            return jsonify({
                'success': False,
                'error': 'AUTO_UPDATE_FAILED',
                'message': '类目批量移除成功但知识库更新失败，请手动更新',
                'removed_categories': removed_categories,
                'not_linked': not_linked_categories,
                'knowledge_base_id': kb.id
            }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"管理员批量移除类目失败 - KB ID: {kb_id}, Error: {str(e)}",
            exc_info=True
        )
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500

@knowledge_management_bp.route('/admin/knowledge_bases/<int:kb_id>/update', methods=['POST'])
def admin_update_single_knowledge_base(kb_id):
    """管理员更新单个知识库"""
    try:
        # 管理员可以更新任何知识库，不需要验证作者
        kb = KnowledgeBase.query.get(kb_id)
        
        if not kb:
            return jsonify({
                'success': False,
                'error': 'KNOWLEDGE_BASE_NOT_FOUND',
                'message': '知识库不存在'
            }), 404

        # 获取请求参数，决定是否强制更新
        data = request.get_json() or {}
        force_update = data.get('force', False)

        # 检查是否需要更新（除非强制更新）
        if not force_update and not kb.need_update:
            return jsonify({
                'success': True,
                'message': '知识库无需更新',
                'updated': False,
                'details': {
                    'knowledge_base_id': kb.id,
                    'name': kb.name,
                    'current_version': kb.version,
                    'last_updated': kb.updated_at.isoformat() if kb.updated_at else None
                }
            }), 200

        try:
            # 执行更新
            update_single_knowledge_base(kb, force=force_update)
            
            # 刷新对象以获取最新数据
            db.session.refresh(kb)
            
            return jsonify({
                'success': True,
                'message': '知识库更新成功',
                'updated': True,
                'details': {
                    'knowledge_base_id': kb.id,
                    'name': kb.name,
                    'new_version': kb.version,
                    'updated_at': kb.updated_at.isoformat() if kb.updated_at else None
                }
            }), 200

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"管理员更新知识库失败 - ID: {kb_id}, Error: {str(e)}",
                exc_info=True
            )
            return jsonify({
                'success': False,
                'error': 'UPDATE_FAILED',
                'message': str(e),
                'knowledge_base_id': kb_id
            }), 500

    except Exception as e:
        current_app.logger.error(
            f"管理员更新知识库处理异常 - ID: {kb_id}, Error: {str(e)}",
            exc_info=True
        )
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500

@knowledge_management_bp.route('/admin/knowledge_bases/system/batch_update', methods=['POST'])
def admin_batch_update_system_knowledge_bases():
    """管理员批量更新所有需要更新的系统知识库"""
    try:
        # 查询所有需要更新的系统知识库
        pending_kbs = KnowledgeBase.query.filter_by(
            is_system=True,
            need_update=True
        ).all()

        if not pending_kbs:
            return jsonify({
                'success': True,
                'message': '没有需要更新的系统知识库',
                'updated_count': 0
            }), 200

        updated_count = 0
        failed_updates = []

        for kb in pending_kbs:
            try:
                # 更新单个知识库
                update_single_knowledge_base(kb)
                updated_count += 1
                
                # 记录管理员操作日志
                current_app.logger.info(
                    f"管理员更新系统知识库成功 - 管理员ID: {g.current_user.id}, "
                    f"知识库ID: {kb.id}, 名称: {kb.name}"
                )
            except Exception as e:
                failed_updates.append({
                    'knowledge_base_id': kb.id,
                    'name': kb.name,
                    'error': str(e)
                })
                current_app.logger.error(
                    f"系统知识库更新失败 - 管理员ID: {g.current_user.id}, "
                    f"知识库ID: {kb.id}, Name: {kb.name}, Error: {str(e)}",
                    exc_info=True
                )

        return jsonify({
            'success': True,
            'message': '系统知识库批量更新完成',
            'updated_count': updated_count,
            'failed_count': len(failed_updates),
            'failed_updates': failed_updates,
            'system_knowledge_bases': True  # 标记这是系统知识库批量更新
        }), 200

    except Exception as e:
        current_app.logger.error(
            f"管理员批量更新系统知识库失败 - 管理员ID: {g.current_user.id}, Error: {str(e)}",
            exc_info=True
        )
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500
    

@knowledge_management_bp.route('/admin/categories/<int:category_id>', methods=['PUT'])
def admin_update_category(category_id):
    """
    管理员更新类目状态
    可更新字段: name, description, is_public
    禁止修改字段: category_type
    """
    try:
        # 1. 验证请求数据
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'INVALID_DATA'}), 400

        # 2. 获取类目（管理员可以操作所有类目）
        category = Category.query.get(category_id)
        if not category:
            return jsonify({'success': False, 'error': 'CATEGORY_NOT_FOUND'}), 404

        # 3. 准备更新数据（排除category_type）
        update_data = {}
        if 'name' in data and data['name']:
            if len(data['name'].strip()) > 100:
                return jsonify({'success': False, 'error': 'NAME_TOO_LONG'}), 400
            update_data['name'] = data['name'].strip()

        if 'description' in data:
            update_data['description'] = data['description'].strip() if data['description'] else None

        if 'is_public' in data:
            if isinstance(data['is_public'], bool):
                update_data['is_public'] = data['is_public']
            else:
                return jsonify({'success': False, 'error': 'INVALID_PUBLIC_STATUS'}), 400

        # 4. 如果有尝试修改category_type，返回错误
        if 'category_type' in data:
            return jsonify({
                'success': False,
                'error': 'CATEGORY_TYPE_CANNOT_MODIFY',
                'message': '类目类型不可修改'
            }), 400

        # 5. 如果没有可更新字段
        if not update_data:
            return jsonify({'success': False, 'error': 'NO_VALID_UPDATE_FIELDS'}), 400

        # 6. 执行更新
        with db.session.begin_nested():
            for key, value in update_data.items():
                setattr(category, key, value)
            category.updated_at = datetime.utcnow()

        db.session.commit()

        # 记录管理员操作日志
        current_app.logger.info(
            f"管理员更新类目 - 管理员ID: {g.current_user.id}, "
            f"类目ID: {category_id}, 更新字段: {list(update_data.keys())}"
        )

        return jsonify({
            'success': True,
            'message': '类目更新成功',
            'updated_fields': list(update_data.keys()),
            'category': {
                'id': category.id,
                'name': category.name,
                'is_public': category.is_public,
                'is_system': category.is_system,
                'category_type': category.category_type
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"管理员更新类目失败 - CategoryID: {category_id}, Error: {str(e)}",
            exc_info=True
        )
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


@knowledge_management_bp.route('/admin/categories/search', methods=['GET'])
def admin_search_categories():
    """管理员模糊搜索类目"""
    try:
        # 获取查询参数
        name = request.args.get('name', '').strip()
        category_type = request.args.get('type')
        is_system = request.args.get('is_system')
        author_id = request.args.get('author_id')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))

        # 构建基础查询
        query = Category.query.options(
            db.joinedload(Category.author).load_only(User.id, User.username))
        
        # 添加过滤条件 - 名称模糊查询
        if name:
            query = query.filter(Category.name.ilike(f'%{name}%'))
        
        # 添加过滤条件 - 类目类型
        if category_type in ['structural', 'non_structural']:
            query = query.filter(Category.category_type == category_type)
        
        # 添加过滤条件 - 系统类目
        if is_system is not None:
            is_system_bool = is_system.lower() == 'true'
            query = query.filter(Category.is_system == is_system_bool)
        
        # 添加过滤条件 - 作者ID
        if author_id:
            try:
                author_id_int = int(author_id)
                query = query.filter(Category.author_id == author_id_int)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'INVALID_AUTHOR_ID',
                    'message': '作者ID必须是整数'
                }), 400

        # 执行分页查询
        paginated_categories = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 构造响应数据
        categories_data = [{
            'id': cat.id,
            'name': cat.name,
            'description': cat.description,
            'category_type': cat.category_type,
            'is_public': cat.is_public,
            'is_system': cat.is_system,
            'created_at': cat.created_at.isoformat(),
            'updated_at': cat.updated_at.isoformat() if cat.updated_at else None,
            'author': {
                'id': cat.author.id if cat.author else None,
                'username': cat.author.username if cat.author else None
            },
            'file_count': len(cat.category_files)
        } for cat in paginated_categories.items]

        return jsonify({
            'success': True,
            'data': categories_data,
            'pagination': {
                'total': paginated_categories.total,
                'pages': paginated_categories.pages,
                'current_page': paginated_categories.page,
                'per_page': paginated_categories.per_page,
                'has_next': paginated_categories.has_next,
                'has_prev': paginated_categories.has_prev
            },
            'search_params': {
                'name': name,
                'type': category_type,
                'is_system': is_system,
                'author_id': author_id
            }
        }), 200

    except Exception as e:
        current_app.logger.error(
            f"管理员搜索类目失败 - Error: {str(e)}",
            exc_info=True
        )
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500
    
@knowledge_management_bp.route('/admin/categories', methods=['POST'])
def admin_create_category():
    """管理员创建新系统类目"""
    try:
        # 解析请求数据
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'NO_DATA_PROVIDED'}), 400
        
        # 验证必要字段
        required_fields = ['name', 'category_type']
        if any(field not in data for field in required_fields):
            return jsonify({
                'success': False,
                'error': 'MISSING_REQUIRED_FIELDS',
                'message': f'缺少必要参数: {", ".join(required_fields)}'
            }), 400

        name = data['name'].strip()
        description = data.get('description', '').strip()
        category_type = data['category_type']
        is_public = data.get('is_public', False)

        # 验证类目类型
        if category_type not in ['structural', 'non_structural']:
            return jsonify({
                'success': False,
                'error': 'INVALID_CATEGORY_TYPE',
                'message': '类目类型必须是structural或non_structural'
            }), 400

        # 创建类目数据库记录
        new_category = Category(
            name=name,
            description=description,
            author_id=g.current_user.id,  # 记录创建者
            stored_categoryname='',
            category_path='',
            category_type=category_type,
            is_public=is_public,
            is_system=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(new_category)
        db.session.commit()  # 先提交以获取ID

        # 创建类目文件夹
        relative_path = create_user_category_folder(
            user_id=g.current_user.id,
            category_id=new_category.id
        )
        categoryname = os.path.basename(relative_path)
        
        # 更新类目路径
        new_category.category_path = os.path.join(
            CATEGORY_PATH,
            categoryname
        )
        new_category.stored_categoryname = categoryname
        db.session.commit()

        # 记录管理员操作日志
        current_app.logger.info(
            f"管理员创建类目 - 管理员ID: {g.current_user.id}, "
            f"类目ID: {new_category.id}, 名称: {name}, 系统类目: {True}"
        )

        return jsonify({
            'success': True,
            'message': '类目创建成功',
            'category': {
                'id': new_category.id,
                'name': new_category.name,
                'description': new_category.description,
                'path': new_category.category_path,
                'type': new_category.category_type,
                'is_public': new_category.is_public,
                'is_system': new_category.is_system,
                'author_id': new_category.author_id
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"管理员创建类目失败 - Error: {str(e)}",
            exc_info=True
        )
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500
    
@knowledge_management_bp.route('/admin/categories/<int:category_id>/files', methods=['DELETE'])
def admin_delete_category_files(category_id):
    """管理员批量删除类目中的文件（可操作系统类目）"""
    try:
        # 1. 获取类目（管理员可以操作所有类目）
        category = Category.query.get(category_id)
        if not category:
            return jsonify({'success': False, 'error': 'CATEGORY_NOT_FOUND'}), 404
        
        # 2. 获取请求数据
        data = request.get_json()
        if not data or 'file_ids' not in data:
            return jsonify({'success': False, 'error': 'MISSING_FILE_IDS'}), 400
            
        file_ids = data['file_ids']
        if not isinstance(file_ids, list) or not file_ids:
            return jsonify({'success': False, 'error': 'INVALID_FILE_IDS'}), 400
        
        # 3. 查询要删除的文件
        files_to_delete = CategoryFile.query.filter(
            CategoryFile.id.in_(file_ids),
            CategoryFile.category_id == category_id
        ).all()
        
        if not files_to_delete:
            return jsonify({'success': False, 'error': 'NO_FILES_FOUND'}), 404
        
        # 4. 检查是否有关联的知识库需要更新
        need_update_kbs = bool(category.knowledge_bases)
        if need_update_kbs:
            for kb in category.knowledge_bases:
                kb.need_update = True
                kb.updated_at = datetime.utcnow()
        
        # 5. 处理每个文件及其图片
        deleted_files = []
        failed_files = []
        
        for file in files_to_delete:
            try:
                # 获取关联图片
                images = file.category_files_images.all()
                
                # 删除物理文件
                delete_file_resources(file)
                
                # 删除关联图片记录
                for image in images:
                    db.session.delete(image)
                
                # 删除主文件记录
                db.session.delete(file)
                
                deleted_files.append(file.id)
                
            except Exception as e:
                failed_files.append({
                    'file_id': file.id,
                    'error': str(e)
                })
                current_app.logger.error(
                    f"管理员删除文件失败 - FileID: {file.id}, Error: {str(e)}",
                    exc_info=True
                )
        
        db.session.commit()
        
        # 记录管理员操作日志
        current_app.logger.info(
            f"管理员批量删除文件 - 管理员ID: {g.current_user.id}, "
            f"类目ID: {category_id}, 删除文件数: {len(deleted_files)}, 失败数: {len(failed_files)}"
        )
        
        return jsonify({
            'success': True,
            'message': '文件批量删除完成',
            'deleted': deleted_files,
            'failed': failed_files,
            'knowledge_bases_updated': need_update_kbs,
            'is_system_category': category.is_system
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"管理员批量删除文件失败 - CategoryID: {category_id}, Error: {str(e)}",
            exc_info=True
        )
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500
    
@knowledge_management_bp.route('/admin/categories/<int:category_id>/files', methods=['POST'])
def admin_upload_files_to_category(category_id):
    """管理员批量上传文件到类目（可操作系统类目）"""
    try:
        # 1. 获取类目（管理员可以操作所有类目）
        category = Category.query.get(category_id)
        if not category:
            return jsonify({'success': False, 'error': 'CATEGORY_NOT_FOUND'}), 404

        # 2. 检查文件是否存在
        if 'files' not in request.files:
            return jsonify({'success': False, 'error': 'NO_FILES_PART'}), 400
        
        files = request.files.getlist('files')
        if not files or any(f.filename == '' for f in files):
            return jsonify({'success': False, 'error': 'EMPTY_FILENAME'}), 400

        # 3. 初始化响应数据
        success_files = []
        failed_files = []
        
        # 4. 创建目标目录
        target_folder = os.path.join(
            UPLOAD_FOLDER_KNOWLEDGE,
            'category',
            f"user_{category.author_id}_category_{category_id}"
        )
        os.makedirs(target_folder, exist_ok=True)

        # 5. 检查是否有关联的知识库需要更新
        need_update_kbs = bool(category.knowledge_bases)
        if need_update_kbs:
            for kb in category.knowledge_bases:
                kb.need_update = True
                kb.updated_at = datetime.utcnow()

        # 6. 处理每个文件
        for file in files:
            try:
                if file.filename == '':
                    failed_files.append({'name': '', 'error': 'EMPTY_FILENAME'})
                    continue
                
                # 结构化文件处理
                if category.category_type == 'structural':
                    if not allowed_file_structural(file.filename):
                        failed_files.append({
                            'name': file.filename, 
                            'error': 'FILE_TYPE_NOT_ALLOWED'
                        })
                        continue
                    
                    relative_path, o_relative_path = upload_file_to_folder_structural(file, target_folder)
                    
                    # 创建文件记录
                    category_file = CategoryFile(
                        name=secure_filename(file.filename),
                        stored_filename=os.path.basename(relative_path),
                        category_id=category_id,
                        author_id=category.author_id,  # 保留原始作者
                        file_path=relative_path,
                        original_file_path=o_relative_path,
                        file_type='structural',
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                        is_public=category.is_public
                    )
                    db.session.add(category_file)
                    
                    success_files.append({
                        'id': category_file.id,
                        'name': file.filename,
                        'url': relative_path,
                        'images': []
                    })
                
                # 非结构化文件处理
                else:
                    if not allowed_file_non_structural(file.filename):
                        failed_files.append({
                            'name': file.filename, 
                            'error': 'FILE_TYPE_NOT_ALLOWED'
                        })
                        continue
                    
                    # 调用非结构化处理函数
                    txt_relative_path, image_relative_paths, o_relative_path = upload_file_to_folder_non_structural(
                        file, target_folder
                    )
                    
                    # 创建主文件记录
                    category_file = CategoryFile(
                        name=secure_filename(file.filename),
                        stored_filename=os.path.basename(txt_relative_path),
                        category_id=category_id,
                        author_id=category.author_id,  # 保留原始作者
                        file_path=txt_relative_path,
                        original_file_path=o_relative_path,
                        file_type='non_structural',
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                        is_public=category.is_public
                    )
                    db.session.add(category_file)
                    db.session.flush()
                    
                    # 存储图片信息
                    images_data = []
                    for img_path in image_relative_paths:
                        img_record = CategoryFileImage(
                            category_file_id=category_file.id,
                            stored_filename=os.path.basename(img_path),
                            file_path=img_path,
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )
                        db.session.add(img_record)
                        images_data.append({
                            'id': img_record.id,
                            'path': img_path,
                            'filename': os.path.basename(img_path)
                        })
                    
                    success_files.append({
                        'id': category_file.id,
                        'name': file.filename,
                        'url': txt_relative_path,
                        'images': images_data
                    })

            except Exception as e:
                db.session.rollback()
                failed_files.append({
                    'name': file.filename, 
                    'error': str(e)
                })

        # 7. 提交数据库变更
        db.session.commit()
        
        # 记录管理员操作日志
        current_app.logger.info(
            f"管理员批量上传文件 - 管理员ID: {g.current_user.id}, "
            f"类目ID: {category_id}, 成功数: {len(success_files)}, 失败数: {len(failed_files)}"
        )

        return jsonify({
            'success': True,
            'message': '文件批量上传完成',
            'data': {
                'succeeded': success_files,
                'failed': failed_files,
                'knowledge_bases_updated': need_update_kbs,
                'is_system_category': category.is_system
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"管理员批量上传文件失败 - CategoryID: {category_id}, Error: {str(e)}",
            exc_info=True
        )
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


@knowledge_management_bp.route('/admin/categories/<int:category_id>', methods=['DELETE'])
def admin_delete_category(category_id):
    """管理员删除类目（可操作系统类目）"""
    try:
        # 1. 获取类目（管理员可以操作所有类目）
        category = Category.query.get(category_id)
        if not category:
            return jsonify({'success': False, 'error': 'CATEGORY_NOT_FOUND'}), 404

        # 2. 获取关联资源
        related_knowledge_bases = category.knowledge_bases
        category_files = category.category_files
        is_system = category.is_system

        # 3. 开始事务处理
        with db.session.begin_nested():
            # 3.1 删除文件资源
            deleted_files_count = 0
            for file in category_files:
                try:
                    # 安全删除文件资源
                    delete_file_resources(file)
                    
                    # 删除关联图片
                    for image in file.category_files_images:
                        db.session.delete(image)
                    
                    # 删除文件记录
                    db.session.delete(file)
                    deleted_files_count += 1
                    
                except Exception as file_error:
                    current_app.logger.error(
                        f"管理员删除文件失败 - FileID: {file.id}, Error: {str(file_error)}",
                        exc_info=True
                    )
                    continue

            # 3.2 更新关联知识库
            for kb in related_knowledge_bases:
                kb.need_update = True
                kb.updated_at = datetime.utcnow()

            # 3.3 删除类目
            db.session.delete(category)

        db.session.commit()

        # 记录管理员操作日志
        current_app.logger.info(
            f"管理员删除类目 - 管理员ID: {g.current_user.id}, "
            f"类目ID: {category_id}, 系统类目: {is_system}, 删除文件数: {deleted_files_count}"
        )

        return jsonify({
            'success': True,
            'message': '类目删除成功',
            'deleted_files_count': deleted_files_count,
            'affected_knowledge_bases': [kb.id for kb in related_knowledge_bases],
            'was_system_category': is_system
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"管理员删除类目失败 - CategoryID: {category_id}, Error: {str(e)}",
            exc_info=True
        )
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500
    
@knowledge_management_bp.route('/admin/categories/<int:category_id>/files', methods=['GET'])
def admin_get_category_files(category_id):
    """管理员获取类目中的所有文件（分存储文件和原始文件）"""
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        file_type = request.args.get('type')  # 可选参数：structural/non_structural

        # 验证分页参数
        if page < 1 or per_page < 1:
            return jsonify({
                'success': False,
                'error': 'INVALID_PAGINATION',
                'message': '分页参数必须是正整数'
            }), 400

        # 获取类目
        category = Category.query.get(category_id)
        if not category:
            return jsonify({
                'success': False,
                'error': 'CATEGORY_NOT_FOUND',
                'message': '类目不存在'
            }), 404

        # 构建基础查询
        query = CategoryFile.query.filter_by(category_id=category_id)
        
        # 按文件类型过滤
        if file_type in ['structural', 'non_structural']:
            query = query.filter_by(file_type=file_type)

        # 执行分页查询
        paginated_files = query.paginate(page=page, per_page=per_page, error_out=False)

        # 获取所有文件ID用于批量查询图片
        file_ids = [file.id for file in paginated_files.items]
        
        # 批量查询关联图片（如果文件是非结构化类型）
        images_map = {}
        if file_ids:
            images = CategoryFileImage.query.filter(
                CategoryFileImage.category_file_id.in_(file_ids)
            ).all()
            for img in images:
                if img.category_file_id not in images_map:
                    images_map[img.category_file_id] = []
                images_map[img.category_file_id].append({
                    'id': img.id,
                    'path': img.file_path,
                    'filename': img.stored_filename,
                    'description': img.description
                })

        # 构造响应数据
        files_data = []
        for file in paginated_files.items:
            file_data = {
                'id': file.id,
                'name': file.name,
                'stored_filename': file.stored_filename,
                'file_type': file.file_type,
                'is_public': file.is_public,
                'created_at': file.created_at.isoformat(),
                'updated_at': file.updated_at.isoformat() if file.updated_at else None,
                'author_id': file.author_id,
                'storage_files': {
                    'processed_file': file.file_path,
                    'original_file': file.original_file_path
                },
                'images': images_map.get(file.id, [])
            }

            files_data.append(file_data)

        return jsonify({
            'success': True,
            'data': {
                'files': files_data,
                'category_info': {
                    'id': category.id,
                    'name': category.name,
                    'type': category.category_type,
                    'is_system': category.is_system
                },
                'pagination': {
                    'total': paginated_files.total,
                    'pages': paginated_files.pages,
                    'current_page': paginated_files.page,
                    'per_page': paginated_files.per_page,
                    'has_next': paginated_files.has_next,
                    'has_prev': paginated_files.has_prev
                }
            }
        }), 200

    except Exception as e:
        current_app.logger.error(
            f"获取类目文件失败 - CategoryID: {category_id}, Error: {str(e)}",
            exc_info=True
        )
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500
    

