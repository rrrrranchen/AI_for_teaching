from datetime import datetime
import os
import shutil
import uuid
from flask import Blueprint, current_app, g, jsonify, request, session
from werkzeug.utils import secure_filename
from yaml import load_all
from app.utils.database import db
from app.models.user import User
from app.models.Category import Category
from app.models.relationship import category_knowledge_base

from app.models.CategoryFile import CategoryFile
from app.models.KnowledgeBase import KnowledgeBase
from app.utils.create_cat import ALLOWED_NON_STRUCTURAL_EXTENSIONS, ALLOWED_STRUCTURAL_EXTENSIONS, UPLOAD_FOLDER_KNOWLEDGE, allowed_file_non_structural, allowed_file_structural, create_knowledge_base_folder, create_user_category_folder, upload_file_to_folder_non_structural, upload_file_to_folder_structural
from app.utils.create_kb import BASE_PATH, create_structured_db, create_unstructured_db,CATEGORY_PATH
from app.utils.ai_chat import _retrieve_chunks_from_multiple_dbs
from app.models.courseclass import Courseclass
from app.models.CategoryFileImage import CategoryFileImage
from app.utils.keywords_search import calculate_keyword_match, extract_keywords

knowledge_for_teachers_bp = Blueprint('knowledge_for_teachers', __name__)

def is_logged_in():
    return 'user_id' in session

def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None
def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

@knowledge_for_teachers_bp.before_request
def before_request():
    if request.method == 'OPTIONS':
        return
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    g.current_user = get_current_user()
    if g.current_user.role != 'teacher':
        return jsonify({'error': 'Forbidden'}), 403


@knowledge_for_teachers_bp.route('/teacher/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    """
    更新类目的基本状态
    可更新字段: name, description, is_public
    禁止修改字段: category_type
    """
    try:
        # 1. 验证请求数据
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'INVALID_DATA'}), 400

        # 2. 获取当前用户拥有的类目
        category = Category.query.filter_by(
            id=category_id,
            author_id=g.current_user.id
        ).first()

        if not category:
            return jsonify({'success': False, 'error': 'CATEGORY_NOT_FOUND_OR_NOT_OWNED'}), 404

        # 3. 检查是否是系统类目（系统类目不可修改）
        if category.is_system:
            return jsonify({'success': False, 'error': 'SYSTEM_CATEGORY_CANNOT_MODIFY'}), 403

        # 4. 准备更新数据（排除category_type）
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

        # 5. 如果有尝试修改category_type，返回错误
        if 'category_type' in data:
            return jsonify({
                'success': False,
                'error': 'CATEGORY_TYPE_CANNOT_MODIFY',
                'message': '类目类型不可修改'
            }), 400

        # 6. 如果没有可更新字段
        if not update_data:
            return jsonify({'success': False, 'error': 'NO_VALID_UPDATE_FIELDS'}), 400

        # 7. 执行更新
        with db.session.begin_nested():
            for key, value in update_data.items():
                setattr(category, key, value)
            category.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '类目更新成功',
            'updated_fields': list(update_data.keys())
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"类目更新失败 - CategoryID: {category_id}, Error: {str(e)}",
            exc_info=True
        )
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500
    


# 类目管理接口
@knowledge_for_teachers_bp.route('/teacher/categories', methods=['GET'])
def get_categories():
    """获取当前用户的所有类目，分别返回结构化和非结构化的类目"""
    # 获取当前用户的所有类目
    categories = Category.query.filter_by(author_id=g.current_user.id).all()
    
    # 分别筛选结构化和非结构化的类目
    structured_categories = [cat for cat in categories if cat.category_type == 'structural']
    non_structured_categories = [cat for cat in categories if cat.category_type == 'non_structural']
    
    # 构造结构化类目的响应数据
    structured_categories_data = [{
        'id': cat.id,
        'name': cat.name,
        'description': cat.description,
        'category_type': cat.category_type,
        'created_at': cat.created_at.isoformat(),
        'is_public': cat.is_public,
        'file_count': len(cat.category_files)
    } for cat in structured_categories]
    
    # 构造非结构化类目的响应数据
    non_structured_categories_data = [{
        'id': cat.id,
        'name': cat.name,
        'description': cat.description,
        'category_type': cat.category_type,
        'created_at': cat.created_at.isoformat(),
        'is_public': cat.is_public,
        'file_count': len(cat.category_files)
    } for cat in non_structured_categories]
    
    # 返回包含结构化和非结构化类目的响应
    return jsonify({
        'structured_categories': structured_categories_data,
        'non_structured_categories': non_structured_categories_data
    })

@knowledge_for_teachers_bp.route('/teacher/categories', methods=['POST'])
def create_category():
    """创建新类目接口"""
    try:
        # 获取当前用户
        current_user = g.current_user
        
        # 解析请求数据
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        name = data.get('name')
        description = data.get('description', '')
        category_type = data.get('category_type')
        is_public = data.get('is_public', False)
        
        # 验证必要字段
        if not name:
            return jsonify({'error': 'Category name is required'}), 400
        if not category_type or category_type not in ['structural', 'non_structural']:
            return jsonify({'error': 'Valid category type is required (structural or non_structural)'}), 400
        
        # 创建类目数据库记录（先不设置路径）
        new_category = Category(
            name=name,
            description=description,
            author_id=current_user.id,
            stored_categoryname='',
            category_path='', 
            category_type=category_type,
            is_public=is_public,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(new_category)
        db.session.commit()  # 先提交以获取ID
        
        # 创建类目文件夹
        relative_path = create_user_category_folder(
            user_id=current_user.id,
            category_id=new_category.id
        )
        categoryname=os.path.basename(relative_path)
        # 更新类目路径
        new_category.category_path = os.path.join(CATEGORY_PATH,categoryname)
        new_category.stored_categoryname=categoryname
        db.session.commit()
        
        # 返回创建成功的响应
        return jsonify({
            'message': 'Category created successfully',
            'category': {
                'id': new_category.id,
                'name': new_category.name,
                'path': new_category.category_path,
                'type': new_category.category_type,
                'is_public': new_category.is_public
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@knowledge_for_teachers_bp.route('/teacher/categories/<int:category_id>/files', methods=['DELETE'])
def delete_category_files(category_id):
    """批量删除类目中的文件"""
    try:
        # 1. 验证类目所有权
        category = Category.query.filter_by(
            id=category_id, 
            author_id=g.current_user.id
        ).first()
        if not category:
            return jsonify({'success': False, 'error': 'CATEGORY_NOT_FOUND'}), 404
        
        # 2. 获取请求数据
        data = request.get_json()
        if not data or 'file_ids' not in data:
            return jsonify({'success': False, 'error': 'MISSING_FILE_IDS'}), 400
            
        file_ids = data['file_ids']
        if not isinstance(file_ids, list) or not file_ids:
            return jsonify({'success': False, 'error': 'INVALID_FILE_IDS'}), 400
        
        # 3. 查询要删除的文件（不使用joinedload）
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
                # 获取关联图片（对dynamic关系需要调用.all()）
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
                    f"文件删除失败 - FileID: {file.id}, Error: {str(e)}",
                    exc_info=True
                )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '文件批量删除完成',
            'deleted': deleted_files,
            'failed': failed_files,
            'knowledge_bases_updated': need_update_kbs
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"文件批量删除失败 - CategoryID: {category_id}, Error: {str(e)}",
            exc_info=True
        )
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500
def delete_file_resources(file):
    """安全删除文件资源（增强版）"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    errors = []
    
    def safe_remove(path):
        """安全删除单个文件"""
        try:
            if path and isinstance(path, (str, bytes, os.PathLike)):
                full_path = os.path.join(project_root, path)
                if os.path.exists(full_path):
                    os.remove(full_path)
                    return True
            return False
        except Exception as e:
            errors.append(f"路径: {path}, 错误: {str(e)}")
            return False
    
    # 删除主文件
    if hasattr(file, 'file_path'):
        safe_remove(file.file_path)
    
    # 删除原始文件（如果存在）
    if hasattr(file, 'original_file_path'):
        safe_remove(file.original_file_path)
    
    # 删除关联图片（如果存在）
    if hasattr(file, 'category_files_images'):
        for image in file.category_files_images:
            if hasattr(image, 'file_path'):
                safe_remove(image.file_path)
    
    if errors:
        raise RuntimeError("; ".join(errors))


@knowledge_for_teachers_bp.route('/teacher/categories/<int:category_id>/files', methods=['POST'])
def upload_files_to_category(category_id):
    """批量上传文件到类目"""
    # 1. 验证类目权限
    category = Category.query.filter_by(id=category_id, author_id=g.current_user.id).first()
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
        f"user_{g.current_user.id}_category_{category_id}"
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
                return jsonify({'error': 'No selected file'}), 400
            
            # 结构化文件处理
            if category.category_type == 'structural':
                if not allowed_file_structural(file.filename):
                    return jsonify({'error': 'File type not allowed for structural category'}), 400
                relative_path, o_relative_path = upload_file_to_folder_structural(file, target_folder)
                
                # 创建文件记录
                category_file = CategoryFile(
                    name=secure_filename(file.filename),
                    stored_filename=os.path.basename(relative_path),
                    category_id=category_id,
                    author_id=g.current_user.id,
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
                    return jsonify({'error': 'File type not allowed for non-structural category'}), 400
                
                # 调用非结构化处理函数
                txt_relative_path, image_relative_paths, o_relative_path = upload_file_to_folder_non_structural(
                    file, target_folder
                )
                
                # 创建主文件记录
                category_file = CategoryFile(
                    name=secure_filename(file.filename),
                    stored_filename=os.path.basename(txt_relative_path),
                    category_id=category_id,
                    author_id=g.current_user.id,
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
                    'url': txt_relative_path
                })

        except Exception as e:
            db.session.rollback()
            failed_files.append({
                'name': file.filename, 
                'error': str(e)
            })

    # 7. 提交数据库变更
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Batch upload completed',
            'data': {
                'succeeded': success_files,
                'failed': failed_files,
                'knowledge_bases_updated': need_update_kbs
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'DATABASE_ERROR',
            'message': str(e)
        }), 500
    

@knowledge_for_teachers_bp.route('/teacher/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """删除一个类目及其所有关联资源"""
    try:
        # 1. 验证类目所有权
        category = Category.query.filter_by(
            id=category_id,
            author_id=g.current_user.id
        ).first()
        
        if not category:
            return jsonify({'success': False, 'error': 'CATEGORY_NOT_FOUND'}), 404

        # 2. 检查是否是系统类目
        if category.is_system:
            return jsonify({'success': False, 'error': 'SYSTEM_CATEGORY_CANNOT_DELETE'}), 403

        # 3. 获取关联资源
        related_knowledge_bases = category.knowledge_bases
        category_files = category.category_files

        # 4. 开始事务处理
        with db.session.begin_nested():
            # 4.1 删除文件资源
            deleted_files_count = 0
            for file in category_files:
                try:
                    # 安全删除文件资源
                    if hasattr(file, 'file_path') or hasattr(file, 'original_file_path'):
                        delete_file_resources(file)
                    
                    # 删除关联图片
                    if hasattr(file, 'category_files_images'):
                        for image in file.category_files_images:
                            db.session.delete(image)
                    
                    # 删除文件记录
                    db.session.delete(file)
                    deleted_files_count += 1
                    
                except Exception as file_error:
                    current_app.logger.error(
                        f"文件删除失败 - FileID: {file.id}, Error: {str(file_error)}",
                        exc_info=True
                    )
                    continue

            # 4.2 更新关联知识库
            for kb in related_knowledge_bases:
                kb.need_update = True
                kb.updated_at = datetime.utcnow()

            # 4.3 删除类目
            db.session.delete(category)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '类目删除成功',
            'deleted_files_count': deleted_files_count,
            'affected_knowledge_bases': [kb.id for kb in related_knowledge_bases]
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"类目删除失败 - CategoryID: {category_id}, Error: {str(e)}",
            exc_info=True
        )
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500
    
from sqlalchemy.orm import load_only
@knowledge_for_teachers_bp.route('/teacher/categories/<int:category_id>/files', methods=['GET'])
def get_category_files(category_id):
    """获取类目中的所有原始文件"""
    try:
        # 1. 验证类目权限
        category = Category.query.filter_by(
            id=category_id,
            author_id=g.current_user.id
        ).first()
        if not category:
            return jsonify({'success': False, 'error': 'CATEGORY_NOT_FOUND'}), 404

        # 2. 查询类目下的所有文件（只包含原始文件信息）
        files = CategoryFile.query.filter_by(
            category_id=category_id
        ).options(
            load_only(
                CategoryFile.id,
                CategoryFile.name,
                CategoryFile.original_file_path,
                CategoryFile.file_type,
                CategoryFile.created_at
            )
        ).all()

        # 3. 构建响应数据
        files_data = []
        for file in files:
            files_data.append({
                'id': file.id,
                'name': file.name,
                'url': file.original_file_path,  # 原始文件路径
                'file_type': file.file_type,
                'created_at': file.created_at.isoformat() if file.created_at else None
            })

        return jsonify({
            'success': True,
            'data': files_data,
            'count': len(files_data)
        }), 200

    except Exception as e:
        current_app.logger.error(
            f"获取类目文件失败 - CategoryID: {category_id}, Error: {str(e)}",
            exc_info=True
        )
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': "获取文件列表失败，请稍后再试"
        }), 500

# 知识库管理接口
@knowledge_for_teachers_bp.route('/teacher/knowledge_bases', methods=['GET'])
def get_knowledge_bases():
    """获取当前用户的所有知识库（包含关联类目信息）"""
    try:
        # 查询知识库并预加载关联的类目
        knowledge_bases = KnowledgeBase.query.filter_by(
            author_id=g.current_user.id
        ).options(
            db.joinedload(KnowledgeBase.categories).load_only(Category.id, Category.name)
        ).all()

        # 构建响应数据
        result = []
        for kb in knowledge_bases:
            # 收集关联类目信息
            categories_info = [{
                'id': cat.id,
                'name': cat.name
            } for cat in kb.categories]

            result.append({
                'id': kb.id,
                'name': kb.name,
                'description': kb.description,
                'created_at': kb.created_at.isoformat() if kb.created_at else None,
                'updated_at': kb.updated_at.isoformat() if kb.updated_at else None,
                'is_public': kb.is_public,
                'need_update': kb.need_update,
                'category_count': len(kb.categories),
                'categories': categories_info  # 新增的类目详细信息
            })

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500

@knowledge_for_teachers_bp.route('/teacher/knowledge_bases/pending_updates', methods=['GET'])
def get_pending_update_knowledge_bases():
    """获取当前用户所有待更新的知识库"""
    try:
        # 查询所有需要更新的知识库
        pending_kbs = KnowledgeBase.query.filter_by(
            author_id=g.current_user.id,
            need_update=True
        ).options(
            db.joinedload(KnowledgeBase.categories).load_only(Category.id, Category.name)
        ).all()

        # 构建响应数据
        result = [{
            'id': kb.id,
            'name': kb.name,
            'description': kb.description,
            'created_at': kb.created_at.isoformat(),
            'categories': [{
                'id': cat.id,
                'name': cat.name
            } for cat in kb.categories],
            'update_reason': '手动标记更新'  # 可以根据实际情况添加更多更新原因信息
        } for kb in pending_kbs]

        return jsonify({
            'success': True,
            'count': len(result),
            'data': result
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


@knowledge_for_teachers_bp.route('/teacher/knowledge_bases/batch_update', methods=['POST'])
def batch_update_knowledge_bases():
    """批量更新所有需要更新的知识库"""
    try:
        # 查询所有需要更新的知识库
        pending_kbs = KnowledgeBase.query.filter_by(
            author_id=g.current_user.id,
            need_update=True
        ).all()

        if not pending_kbs:
            return jsonify({
                'success': True,
                'message': '没有需要更新的知识库',
                'updated_count': 0
            }), 200

        updated_count = 0
        failed_updates = []

        for kb in pending_kbs:
            try:
                # 更新单个知识库
                update_single_knowledge_base(kb)
                updated_count += 1
            except Exception as e:
                failed_updates.append({
                    'knowledge_base_id': kb.id,
                    'name': kb.name,
                    'error': str(e)
                })
                current_app.logger.error(
                    f"知识库更新失败 - ID: {kb.id}, Name: {kb.name}, Error: {str(e)}",
                    exc_info=True
                )

        return jsonify({
            'success': True,
            'message': '批量更新完成',
            'updated_count': updated_count,
            'failed_count': len(failed_updates),
            'failed_updates': failed_updates
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


@knowledge_for_teachers_bp.route('/teacher/knowledge_bases/<int:kb_id>/update', methods=['POST'])
def update_single_knowledge_base_endpoint(kb_id):
    """更新单个知识库"""
    try:
        # 验证知识库所有权
        kb = KnowledgeBase.query.filter_by(
            id=kb_id,
            author_id=g.current_user.id
        ).first()

        if not kb:
            return jsonify({
                'success': False,
                'error': 'KNOWLEDGE_BASE_NOT_FOUND'
            }), 404

        # 检查是否需要更新
        if not kb.need_update:
            return jsonify({
                'success': True,
                'message': '知识库无需更新',
                'updated': False
            }), 200

        try:
            # 执行更新
            update_single_knowledge_base(kb)
            
            return jsonify({
                'success': True,
                'message': '知识库更新成功',
                'updated': True
            }), 200

        except Exception as e:
            current_app.logger.error(
                f"知识库更新失败 - ID: {kb.id}, Name: {kb.name}, Error: {str(e)}",
                exc_info=True
            )
            return jsonify({
                'success': False,
                'error': 'UPDATE_FAILED',
                'message': str(e)
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


def update_single_knowledge_base(knowledge_base: KnowledgeBase):
    """更新单个知识库的核心逻辑"""
    # 1. 准备类目信息
    categories = knowledge_base.categories
    unstructured_categories = []
    structured_categories = []
    
    for category in categories:
        if category.category_type == 'non_structural':
            unstructured_categories.append(category.stored_categoryname)
        elif category.category_type == 'structural':
            structured_categories.append(category.stored_categoryname)
    
    # 2. 删除原知识库文件夹内容
    kb_path = os.path.join(BASE_PATH, knowledge_base.stored_basename)
    if os.path.exists(kb_path):
        shutil.rmtree(kb_path)
    
    # 3. 重新创建知识库
    if knowledge_base.base_type == 'non_structural':
        create_unstructured_db(knowledge_base.stored_basename, unstructured_categories)
    else:
        create_structured_db(knowledge_base.stored_basename, structured_categories)
    
    # 4. 更新数据库记录
    knowledge_base.need_update = False
    knowledge_base.updated_at = datetime.utcnow()
    db.session.commit()

@knowledge_for_teachers_bp.route('/teacher/knowledge_bases', methods=['POST'])
def create_knowledge_base_endpoint():
    """创建知识库接口（通过类目ID）"""
    data = request.get_json()
    
    # 基本参数验证
    required_fields = ['name', 'category_ids', 'base_type']
    if not data or any(field not in data for field in required_fields):
        return jsonify({
            'error': 'MISSING_REQUIRED_FIELDS',
            'message': f'缺少必要参数: {", ".join(required_fields)}'
        }), 400
    
    try:
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
        
        # 检查知识库是否已存在
        db_name = data['name']
        unique_name = f"{uuid.uuid4()}_{db_name}"
        
        
        # 根据类目类型调用不同的创建函数
        if unstructured_categories:
            create_unstructured_db(unique_name, unstructured_categories)
        elif structured_categories:
            create_structured_db(unique_name, structured_categories)
        
        # 获取当前用户 ID
        aid = session.get('user_id')
        if aid is None:
            return jsonify({'error': 'UNAUTHORIZED', 'message': '未登录用户'}), 401
        
        # 创建知识库数据库记录
        knowledge_base = KnowledgeBase(
            name=data['name'],
            stored_basename=unique_name,
            description=data.get('description', ''),
            author_id=aid,
            is_public=data.get('is_public', False),
            file_path=os.path.join(BASE_PATH, unique_name),
            base_type=data['base_type']
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
            'author_id': knowledge_base.author_id,
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



@knowledge_for_teachers_bp.route('/teacher/knowledge_bases/<int:kb_id>', methods=['DELETE'])
def delete_knowledge_base(kb_id):
    """删除知识库"""
    knowledge_base = KnowledgeBase.query.filter_by(id=kb_id, author_id=g.current_user.id).first()
    if not knowledge_base:
        return jsonify({'error': 'Knowledge base not found'}), 404
    
    try:
        # 删除物理文件夹
        full_path = os.path.join(UPLOAD_FOLDER_KNOWLEDGE, knowledge_base.file_path.replace('static/knowledge/', ''))
        if os.path.exists(full_path):
            shutil.rmtree(full_path)
        
        # 删除数据库记录
        db.session.delete(knowledge_base)
        db.session.commit()
        return jsonify({'message': 'Knowledge base deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@knowledge_for_teachers_bp.route('/teacher/courseclasses/<int:courseclass_id>/knowledge_bases', methods=['POST'])
def add_knowledge_bases_to_courseclass(courseclass_id):
    """为课程班批量添加知识库"""
    try:
        # 验证课程班是否存在
        courseclass = Courseclass.query.filter_by(id=courseclass_id).first()
        if not courseclass:
            return jsonify({
                'success': False,
                'error': 'COURSECLASS_NOT_FOUND',
                'message': '课程班不存在'
            }), 404
        
        # 验证请求数据
        data = request.get_json()
        if not data or 'knowledge_base_ids' not in data:
            return jsonify({
                'success': False,
                'error': 'MISSING_KNOWLEDGE_BASE_IDS',
                'message': '缺少知识库ID列表'
            }), 400
        
        knowledge_base_ids = data['knowledge_base_ids']
        if not isinstance(knowledge_base_ids, list):
            return jsonify({
                'success': False,
                'error': 'INVALID_KNOWLEDGE_BASE_IDS',
                'message': '知识库ID列表格式不正确'
            }), 400
        
        # 获取所有知识库
        knowledge_bases = KnowledgeBase.query.filter(
            KnowledgeBase.id.in_(knowledge_base_ids)
        ).all()
        
        if len(knowledge_bases) != len(knowledge_base_ids):
            return jsonify({
                'success': False,
                'error': 'SOME_KNOWLEDGE_BASES_NOT_FOUND',
                'message': '部分知识库未找到'
            }), 404
        
        # 检查权限并统计需要增加使用次数的知识库
        kbs_to_increment = []
        for kb in knowledge_bases:
            # 检查知识库是否为开放的
            if not kb.is_public:
                # 检查知识库的作者是否为当前登录用户
                if kb.author_id != g.current_user.id:
                    return jsonify({
                        'success': False,
                        'error': 'PRIVATE_KNOWLEDGE_BASE',
                        'message': f'知识库 "{kb.name}" 不是公开的且您不是创建者'
                    }), 403
                
                # 检查该班级的教师是否为当前登录用户
                if not any(teacher.id == g.current_user.id for teacher in courseclass.teachers):
                    return jsonify({
                        'success': False,
                        'error': 'NOT_COURSECLASS_TEACHER',
                        'message': '您不是该课程班的教师'
                    }), 403
            
            # 如果知识库不是当前用户创建的且尚未关联到课程班，则增加使用计数
            if kb.author_id != g.current_user.id and kb not in courseclass.knowledge_bases:
                kbs_to_increment.append(kb)
        
        # 执行数据库操作
        with db.session.begin_nested():
            # 增加使用计数
            for kb in kbs_to_increment:
                kb.usage_count += 1
            
            # 批量添加知识库到课程班
            courseclass.knowledge_bases.extend(
                kb for kb in knowledge_bases 
                if kb not in courseclass.knowledge_bases
            )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '知识库添加成功',
            'data': {
                'added_count': len(knowledge_bases),
                'usage_incremented': len(kbs_to_increment),
                'knowledge_bases': [{
                    'id': kb.id,
                    'name': kb.name,
                    'usage_count': kb.usage_count if kb in kbs_to_increment else '未变化'
                } for kb in knowledge_bases]
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"添加知识库到课程班失败 - CourseclassID: {courseclass_id}, UserID: {g.current_user.id}, Error: {str(e)}",
            exc_info=True
        )
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500

    

@knowledge_for_teachers_bp.route('/teacher/courseclasses/<int:courseclass_id>/knowledge_bases', methods=['PUT'])
def update_knowledge_bases_of_courseclass(courseclass_id):
    """更新课程班与知识库的关系（全量更新）"""
    try:
        # 验证课程班所有权
        courseclass = Courseclass.query.filter_by(
            id=courseclass_id,
            author_id=g.current_user.id
        ).first()
        
        if not courseclass:
            return jsonify({
                'success': False,
                'error': 'COURSECLASS_NOT_FOUND_OR_NOT_OWNED',
                'message': '课程班不存在或您不是创建者'
            }), 404
        
        # 验证请求数据
        data = request.get_json()
        if not data or 'knowledge_base_ids' not in data:
            return jsonify({
                'success': False,
                'error': 'MISSING_KNOWLEDGE_BASE_IDS',
                'message': '缺少知识库ID列表'
            }), 400
        
        knowledge_base_ids = data['knowledge_base_ids']
        if not isinstance(knowledge_base_ids, list):
            return jsonify({
                'success': False,
                'error': 'INVALID_KNOWLEDGE_BASE_IDS',
                'message': '知识库ID列表格式不正确'
            }), 400
        
        # 获取所有知识库
        knowledge_bases = KnowledgeBase.query.filter(
            KnowledgeBase.id.in_(knowledge_base_ids)
        ).all()
        
        if len(knowledge_bases) != len(knowledge_base_ids):
            return jsonify({
                'success': False,
                'error': 'SOME_KNOWLEDGE_BASES_NOT_FOUND',
                'message': '部分知识库未找到'
            }), 404
        
        # 获取当前关联的知识库ID集合
        current_kb_ids = {kb.id for kb in courseclass.knowledge_bases}
        new_kb_ids = set(knowledge_base_ids)
        
        # 找出新增和移除的知识库
        added_kb_ids = new_kb_ids - current_kb_ids
        removed_kb_ids = current_kb_ids - new_kb_ids
        
        # 找出需要增加和减少使用次数的知识库
        kbs_to_increment = [
            kb for kb in knowledge_bases 
            if kb.id in added_kb_ids and kb.author_id != g.current_user.id
        ]
        
        kbs_to_decrement = [
            kb for kb in courseclass.knowledge_bases
            if kb.id in removed_kb_ids and kb.author_id != g.current_user.id
        ]
        
        # 检查所有知识库权限
        for kb in knowledge_bases:
            if not kb.is_public and kb.author_id != g.current_user.id:
                return jsonify({
                    'success': False,
                    'error': 'PRIVATE_KNOWLEDGE_BASE',
                    'message': f'知识库 "{kb.name}" 不是公开的且您不是创建者'
                }), 403
        
        # 执行数据库操作
        with db.session.begin_nested():
            # 增加新增知识库的使用计数
            for kb in kbs_to_increment:
                kb.usage_count += 1
            
            # 减少移除知识库的使用计数（确保不小于0）
            for kb in kbs_to_decrement:
                kb.usage_count = max(0, kb.usage_count - 1)
            
            # 更新课程班与知识库的关系
            courseclass.knowledge_bases = knowledge_bases
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '课程班知识库关系更新成功',
            'data': {
                'total_knowledge_bases': len(knowledge_bases),
                'added': len(added_kb_ids),
                'removed': len(removed_kb_ids),
                'usage_incremented': len(kbs_to_increment),
                'usage_decremented': len(kbs_to_decrement),
                'knowledge_bases': [{
                    'id': kb.id,
                    'name': kb.name,
                    'usage_count': kb.usage_count,
                    'status': '新增' if kb.id in added_kb_ids else 
                             '移除' if kb.id in removed_kb_ids else '保留'
                } for kb in knowledge_bases + list(courseclass.knowledge_bases)]
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"更新课程班知识库关系失败 - CourseclassID: {courseclass_id}, UserID: {g.current_user.id}, Error: {str(e)}",
            exc_info=True
        )
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


@knowledge_for_teachers_bp.route('/teacher/knowledge_bases/<int:kb_id>/categories/batch_add', methods=['POST'])
def batch_add_categories_to_knowledge_base(kb_id):
    """为知识库批量添加类目"""
    try:
        data = request.get_json()
        if not data or 'category_ids' not in data or not isinstance(data['category_ids'], list):
            return jsonify({
                'success': False,
                'error': 'MISSING_REQUIRED_FIELDS',
                'message': '缺少category_ids参数或参数格式不正确'
            }), 400

        # 验证知识库所有权
        kb = KnowledgeBase.query.filter_by(
            id=kb_id,
            author_id=g.current_user.id
        ).first()

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
        db.session.commit()

        # 自动更新知识库
        try:
            update_single_knowledge_base(kb)
            return jsonify({
                'success': True,
                'message': '类目批量添加成功且知识库已更新',
                'added_categories': added_categories,
                'duplicates': duplicate_categories,
                'type_mismatches': type_mismatch_categories
            }), 200
        except Exception as update_error:
            db.session.rollback()
            current_app.logger.error(
                f"知识库自动更新失败 - KB ID: {kb.id}, Error: {str(update_error)}",
                exc_info=True
            )
            return jsonify({
                'success': False,
                'error': 'AUTO_UPDATE_FAILED',
                'message': '类目批量添加成功但知识库更新失败，请手动更新',
                'added_categories': added_categories,
                'duplicates': duplicate_categories,
                'type_mismatches': type_mismatch_categories
            }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


@knowledge_for_teachers_bp.route('/teacher/knowledge_bases/<int:kb_id>/categories/batch_remove', methods=['DELETE'])
def batch_remove_categories_from_knowledge_base(kb_id):
    """从知识库批量删除类目"""
    try:
        data = request.get_json()
        if not data or 'category_ids' not in data or not isinstance(data['category_ids'], list):
            return jsonify({
                'success': False,
                'error': 'MISSING_REQUIRED_FIELDS',
                'message': '缺少category_ids参数或参数格式不正确'
            }), 400

        # 验证知识库所有权
        kb = KnowledgeBase.query.filter_by(
            id=kb_id,
            author_id=g.current_user.id
        ).first()

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
        db.session.commit()

        # 自动更新知识库
        try:
            update_single_knowledge_base(kb)
            return jsonify({
                'success': True,
                'message': '类目批量移除成功且知识库已更新',
                'removed_categories': removed_categories,
                'not_linked': not_linked_categories
            }), 200
        except Exception as update_error:
            db.session.rollback()
            current_app.logger.error(
                f"知识库自动更新失败 - KB ID: {kb.id}, Error: {str(update_error)}",
                exc_info=True
            )
            return jsonify({
                'success': False,
                'error': 'AUTO_UPDATE_FAILED',
                'message': '类目批量移除成功但知识库更新失败，请手动更新',
                'removed_categories': removed_categories,
                'not_linked': not_linked_categories
            }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500
    

@knowledge_for_teachers_bp.route('/public/knowledge_bases/search', methods=['GET'])
def search_public_knowledge_bases():
    """模糊搜索公开知识库（名称匹配优先于描述匹配）"""
    try:
        # 获取查询参数
        keyword = request.args.get('keyword', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # 验证参数
        if not keyword:
            return jsonify({
                'success': False,
                'error': 'MISSING_KEYWORD',
                'message': '请输入搜索关键字'
            }), 400
            
        if page < 1 or per_page < 1:
            return jsonify({
                'success': False,
                'error': 'INVALID_PAGINATION',
                'message': '分页参数必须是正整数'
            }), 400

        # 构建基础查询（只查询非当前用户的公开知识库）
        base_query = KnowledgeBase.query.filter(
            KnowledgeBase.author_id != g.current_user.id,
            KnowledgeBase.is_public == True,
            db.or_(
                KnowledgeBase.name.ilike(f'%{keyword}%'),
                KnowledgeBase.description.ilike(f'%{keyword}%')
            )
        ).options(
            db.joinedload(KnowledgeBase.categories).load_only(Category.id, Category.name),
            db.joinedload(KnowledgeBase.author).load_only(User.id, User.username)
        )

        # 添加排序规则：名称匹配的优先，然后按更新时间降序
        query = base_query.order_by(
            db.case(
                [KnowledgeBase.name.ilike(f'%{keyword}%'), 1],
                else_=2
            ),
            KnowledgeBase.updated_at.desc()
        )

        # 执行分页查询
        paginated_kbs = query.paginate(page=page, per_page=per_page, error_out=False)

        # 构造响应数据
        results = []
        for kb in paginated_kbs.items:
            # 判断匹配类型
            name_match = keyword.lower() in kb.name.lower()
            desc_match = kb.description and keyword.lower() in kb.description.lower()
            
            match_type = '名称匹配' if name_match else '描述匹配'
            match_score = 1 if name_match else 0.5  # 名称匹配得分更高

            results.append({
                'id': kb.id,
                'name': kb.name,
                'description': kb.description,
                'is_public': kb.is_public,
                'created_at': kb.created_at.isoformat(),
                'updated_at': kb.updated_at.isoformat() if kb.updated_at else None,
                # 'author': {
                #     'id': kb.author.id,
                #     'username': kb.author.username
                # },
                'author_id': kb.author_id,
                'author_name': kb.author.name,
                'categories': [{
                    'id': cat.id,
                    'name': cat.name
                } for cat in kb.categories],
                'match_type': match_type,
                'match_score': match_score
            })

        # 按匹配分数降序排序（确保名称匹配的在前）
        results.sort(key=lambda x: x['match_score'], reverse=True)

        return jsonify({
            'success': True,
            'data': {
                'results': results,
                'pagination': {
                    'total': paginated_kbs.total,
                    'pages': paginated_kbs.pages,
                    'current_page': paginated_kbs.page,
                    'per_page': paginated_kbs.per_page,
                    'has_next': paginated_kbs.has_next,
                    'has_prev': paginated_kbs.has_prev
                },
                'search_meta': {
                    'keyword': keyword,
                    'total_matches': paginated_kbs.total,
                    'name_matches': sum(1 for r in results if r['match_type'] == '名称匹配'),
                    'desc_matches': sum(1 for r in results if r['match_type'] == '描述匹配')
                }
            }
        }), 200

    except Exception as e:
        current_app.logger.error(
            f"公开知识库搜索失败 - UserID: {g.current_user.id}, Error: {str(e)}",
            exc_info=True
        )
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500
    

@knowledge_for_teachers_bp.route('/public/knowledge_bases/deep_search', methods=['GET'])
def deep_search_public_knowledge_bases():
    """
    深度搜索公开知识库内容
    参数:
        - keyword: 搜索关键词 (必需)
        - kb_ids: 知识库ID列表，逗号分隔 (可选)
        - similarity: 相似度阈值 (0-1, 默认0.7)
        - chunk_count: 返回的片段数量 (默认5)
        - data_type: 过滤数据类型 (可选)
    """
    try:
        # 获取查询参数
        keyword = request.args.get('keyword', '').strip()
        kb_ids = request.args.get('kb_ids', '')
        similarity = float(request.args.get('similarity', 0.7))
        chunk_count = int(request.args.get('chunk_count', 5))
        data_type = request.args.get('data_type', None)

        # 验证必要参数
        if not keyword:
            return jsonify({
                'success': False,
                'error': 'MISSING_KEYWORD',
                'message': '请输入搜索关键词'
            }), 400

        # 获取非当前用户的公开知识库
        query = KnowledgeBase.query.filter(
            KnowledgeBase.author_id != g.current_user.id,
            KnowledgeBase.is_public == True
        ).options(
            db.joinedload(KnowledgeBase.author).load_only(User.id, User.username)
        )
        
        # 如果有指定知识库ID，则过滤
        if kb_ids:
            kb_id_list = [int(id) for id in kb_ids.split(',') if id.isdigit()]
            query = query.filter(KnowledgeBase.id.in_(kb_id_list))

        knowledge_bases = query.all()

        if not knowledge_bases:
            return jsonify({
                'success': False,
                'error': 'NO_PUBLIC_KNOWLEDGE_BASES',
                'message': '未找到符合条件的公开知识库'
            }), 404

        # 获取知识库名称列表
        db_names = [kb.stored_basename for kb in knowledge_bases]

        # 调用核心检索函数
        model_context, display_context, source_dict = _retrieve_chunks_from_multiple_dbs(
            query=keyword,
            db_names=db_names,
            similarity_threshold=similarity,
            chunk_cnt=chunk_count,
            data_type_filter=data_type
        )

        # 如果没有检索到内容
        if not source_dict:
            return jsonify({
                'success': True,
                'message': '未找到匹配内容',
                'data': {
                    'keyword': keyword,
                    'matches': 0,
                    'results': []
                }
            }), 200

        # 重构结果格式
        results = []
        for db_name, categories in source_dict.items():
            # 获取知识库信息
            kb = next((kb for kb in knowledge_bases if kb.stored_basename == db_name), None)
            kb_info = {
                'id': kb.id if kb else None,
                'name': kb.name if kb else db_name,
                'is_public': True,
                # 'author': {
                #     'id': kb.author.id if kb else None,
                #     'username': kb.author.username if kb else None
                # }
                'author_id': kb.author.id if kb else None,
                'author_name': kb.author.username if kb else None,
            }

            for category, files in categories.items():
                for file_name, chunks in files.items():
                    for chunk in chunks:
                        results.append({
                            'knowledge_base': kb_info,
                            'category': category,
                            'file': file_name,
                            'text': chunk['text'],
                            'score': chunk['score'],
                            'position': chunk['position']
                        })

        # 按分数降序排序
        results.sort(key=lambda x: x['score'], reverse=True)

        return jsonify({
            'success': True,
            'data': {
                'keyword': keyword,
                'matches': len(results),
                'similarity_threshold': similarity,
                'results': results,
                'model_context': model_context,
                'display_context': display_context
            }
        }), 200

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': 'INVALID_PARAMETER',
            'message': f'参数错误: {str(e)}'
        }), 400
    except Exception as e:
        current_app.logger.error(
            f"公开知识库深度搜索失败 - UserID: {g.current_user.id}, Error: {str(e)}",
            exc_info=True
        )
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500                                           
    

@knowledge_for_teachers_bp.route('/teacher/courseclasses/<int:courseclass_id>/knowledge_bases/recommendations', methods=['GET'])
def get_recommended_knowledge_bases(courseclass_id):
    """
    根据课程班信息推荐相关知识库
    参数:
        - limit: 返回结果数量(默认5)
        - min_usage_count: 最小使用次数阈值(默认3)
        - keyword_weight: 关键词匹配权重(0-1, 默认0.6)
        - category_weight: 类别匹配权重(0-1, 默认0.3)
        - usage_weight: 使用次数权重(0-1, 默认0.1)
    """
    try:
        # 验证课程班是否存在及用户权限
        courseclass = Courseclass.query.filter_by(id=courseclass_id).first()
        if not courseclass:
            return jsonify({
                'success': False,
                'error': 'COURSECLASS_NOT_FOUND',
                'message': '课程班不存在'
            }), 404
        
        # 检查用户是否是课程班教师
        if g.current_user not in courseclass.teachers:
            return jsonify({
                'success': False,
                'error': 'PERMISSION_DENIED',
                'message': '您不是该课程班的教师'
            }), 403
        
        # 获取查询参数
        limit = 5
        min_usage_count = 0
        keyword_weight = 0.6
        category_weight = 0.3
        usage_weight = 0.1
        
        # 权重归一化检查
        total_weight = keyword_weight + category_weight + usage_weight
        if not (0.999 <= total_weight <= 1.001):  # 允许微小的浮点误差
            return jsonify({
                'success': False,
                'error': 'INVALID_WEIGHTS',
                'message': '权重总和必须等于1'
            }), 400
        
        # 获取课程班已关联的知识库ID(用于排除)
        linked_kb_ids = {kb.id for kb in courseclass.knowledge_bases}
        
        # 获取课程班当前知识库的类别ID
        current_category_ids = set()
        for kb in courseclass.knowledge_bases:
            current_category_ids.update(cat.id for cat in kb.categories)
        
        # 构建基础查询
        query = KnowledgeBase.query.filter(
            KnowledgeBase.is_public == True,  # 只推荐公开知识库
            KnowledgeBase.id.notin_(linked_kb_ids),  # 排除已关联的
            KnowledgeBase.usage_count >= min_usage_count  # 满足最小使用次数
        ).options(
            db.joinedload(KnowledgeBase.author).load_only(User.id, User.username),
            db.joinedload(KnowledgeBase.categories).load_only(Category.id, Category.name)
        )
        
        # 提取课程班关键词
        class_keywords = extract_keywords(f"{courseclass.name} {courseclass.description or ''}")
        
        # 获取所有候选知识库
        candidate_kbs = query.all()
        
        if not candidate_kbs:
            return jsonify({
                'success': True,
                'data': {
                    'courseclass_id': courseclass.id,
                    'courseclass_name': courseclass.name,
                    'message': '没有符合条件的推荐知识库',
                    'recommendations': []
                }
            }), 200
        
        # 计算每个知识库的推荐分数
        scored_kbs = []
        max_usage = max(kb.usage_count for kb in candidate_kbs) or 1  # 避免除以0
        
        for kb in candidate_kbs:
            # 1. 关键词匹配分数
            kb_keywords = extract_keywords(f"{kb.name} {kb.description or ''}")
            keyword_score = calculate_keyword_match(class_keywords, kb_keywords)
            
            # 2. 类别匹配分数
            kb_category_ids = {cat.id for cat in kb.categories}
            if current_category_ids:
                category_score = len(current_category_ids & kb_category_ids) / len(current_category_ids)
            else:
                category_score = 0
            
            # 3. 使用次数分数 (归一化到0-1)
            usage_score = kb.usage_count / max_usage
            
            # 综合分数
            total_score = (keyword_weight * keyword_score +
                          category_weight * category_score +
                          usage_weight * usage_score)
            
            scored_kbs.append({
                'kb': kb,
                'scores': {
                    'total': total_score,
                    'keyword': keyword_score,
                    'category': category_score,
                    'usage': usage_score
                }
            })
        
        # 按总分排序
        scored_kbs.sort(key=lambda x: x['scores']['total'], reverse=True)
        
        # 获取前limit个推荐
        recommended_kbs = [item['kb'] for item in scored_kbs[:limit]]
        
        # 构建响应数据
        results = []
        for idx, kb in enumerate(recommended_kbs):
            match_reasons = []
            scores = scored_kbs[idx]['scores']
            
            # 构建匹配原因描述
            if scores['keyword'] > 0.5:
                match_reasons.append('高关键词匹配')
            elif scores['keyword'] > 0.2:
                match_reasons.append('部分关键词匹配')
                
            if scores['category'] > 0:
                match_reasons.append('同类别知识库')
                
            if scores['usage'] > 0.7:
                match_reasons.append('高使用量')
            elif scores['usage'] > 0.3:
                match_reasons.append('中等使用量')
                
            if not match_reasons:
                match_reasons.append('综合推荐')
            
            results.append({
                'id': kb.id,
                'name': kb.name,
                'description': kb.description,
                'usage_count': kb.usage_count,
                'author': {
                    'id': kb.author.id,
                    'username': kb.author.username
                },
                'categories': [{
                    'id': cat.id,
                    'name': cat.name
                } for cat in kb.categories],
                'match_reason': '、'.join(match_reasons),
                'score_details': {
                    'total_score': round(scores['total'], 3),
                    'keyword_score': round(scores['keyword'], 3),
                    'category_score': round(scores['category'], 3),
                    'usage_score': round(scores['usage'], 3)
                }
            })
        
        return jsonify({
            'success': True,
            'data': {
                'courseclass_id': courseclass.id,
                'courseclass_name': courseclass.name,
                'courseclass_keywords': class_keywords,
                'current_category_ids': list(current_category_ids),
                'recommendation_strategy': {
                    'keyword_weight': keyword_weight,
                    'category_weight': category_weight,
                    'usage_weight': usage_weight
                },
                'recommendations': results
            }
        }), 200

    except Exception as e:
        current_app.logger.error(
            f"获取推荐知识库失败 - CourseclassID: {courseclass_id}, UserID: {g.current_user.id}, Error: {str(e)}",
            exc_info=True
        )
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500
    

@knowledge_for_teachers_bp.route('/teacher/knowledge_bases/migrate_public', methods=['POST'])
def migrate_public_knowledge_base():
    """将公共知识库迁移为个人知识库"""
    try:
        data = request.get_json()
        if not data or 'knowledge_base_id' not in data:
            return jsonify({
                'success': False,
                'error': 'MISSING_KNOWLEDGE_BASE_ID',
                'message': '缺少知识库ID'
            }), 400

        kb_id = data['knowledge_base_id']
        public_kb = KnowledgeBase.query.filter_by(
            id=kb_id,
            is_public=True
        ).first()

        if not public_kb:
            return jsonify({
                'success': False,
                'error': 'PUBLIC_KNOWLEDGE_BASE_NOT_FOUND',
                'message': '公共知识库不存在或不是公开的'
            }), 404
        
        # 获取作者信息
        author = User.query.get(public_kb.author_id)
        author_name = author.username if author else "未知作者"

        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        BASE_PATH = os.path.join(project_root, 'static', 'knowledge', 'base')
        
        # 新知识库的存储路径
        new_basename = f"kb_{uuid.uuid4().hex}"
        new_dir = os.path.join(BASE_PATH, new_basename)
        
        # 复制文件
        if public_kb.file_path:
            shutil.copytree(public_kb.file_path, new_dir)
        else:
            return jsonify({
                'success': False,
                'error': 'SOURCE_KB_FILES_NOT_FOUND',
                'message': '原知识库文件不存在'
            }), 404

        # 创建新的知识库记录
        new_kb = KnowledgeBase(
            name=f"{public_kb.name} (副本)",
            stored_basename=new_basename,
            description=public_kb.description,
            file_path=new_dir,
            is_public=False,
            is_system=False,
            base_type=public_kb.base_type,
            author_id=public_kb.author_id
        )

        db.session.add(new_kb)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '公共知识库迁移成功',
            'data': {
                'new_knowledge_base': {
                    'id': new_kb.id,
                    'name': new_kb.name,
                    'path': new_dir,
                    'original_author': author_name  # 添加原作者名称
                }
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        # 清理可能已创建的文件
        if 'new_dir' in locals() and os.path.exists(new_dir):
            shutil.rmtree(new_dir, ignore_errors=True)
            
        current_app.logger.error(
            f"迁移公共知识库失败 - KBID: {kb_id}, UserID: {g.current_user.id}, Error: {str(e)}",
            exc_info=True
        )
        return jsonify({
            'success': False,
            'error': 'MIGRATION_FAILED',
            'message': f'迁移失败: {str(e)}'
        }), 500


@knowledge_for_teachers_bp.route('/public/knowledge_bases', methods=['GET'])
def get_public_knowledge_bases():
    """获取所有公开且不属于当前用户的知识库（无分页）"""
    try:
        # 获取查询参数
        sort_by = request.args.get('sort_by', 'updated_at')
        order = request.args.get('order', 'desc')
        category_id = request.args.get('category_id', None)
        base_type = request.args.get('base_type', None)
        min_usage = request.args.get('min_usage', None, type=int)
        
        # 验证参数
        valid_sort_fields = ['name', 'created_at', 'updated_at', 'usage_count']
        if sort_by not in valid_sort_fields:
            return jsonify({
                'success': False,
                'error': 'INVALID_SORT_FIELD',
                'message': f'排序字段必须是以下之一: {", ".join(valid_sort_fields)}'
            }), 400
            
        if order not in ['asc', 'desc']:
            return jsonify({
                'success': False,
                'error': 'INVALID_ORDER',
                'message': '排序顺序必须是asc或desc'
            }), 400
            
        if base_type and base_type not in ['structural', 'non_structural']:
            return jsonify({
                'success': False,
                'error': 'INVALID_BASE_TYPE',
                'message': '知识库类型必须是structural或non_structural'
            }), 400

        # 构建基础查询
        query = KnowledgeBase.query.filter(
            KnowledgeBase.is_public == True,
            KnowledgeBase.author_id != g.current_user.id
        ).options(
            db.joinedload(KnowledgeBase.author).load_only(User.id, User.username),
            db.joinedload(KnowledgeBase.categories).load_only(Category.id, Category.name)
        )

        # 应用过滤条件
        if category_id:
            query = query.join(
                category_knowledge_base,
                category_knowledge_base.c.knowledge_base_id == KnowledgeBase.id
            ).filter(
                category_knowledge_base.c.category_id == category_id
            )
            
        if base_type:
            query = query.filter(KnowledgeBase.base_type == base_type)
            
        if min_usage is not None:
            query = query.filter(KnowledgeBase.usage_count >= min_usage)

        # 应用排序
        sort_column = getattr(KnowledgeBase, sort_by)
        if order == 'desc':
            sort_column = sort_column.desc()
        query = query.order_by(sort_column)

        # 获取所有结果
        knowledge_bases = query.all()

        # 构造响应数据
        results = []
        for kb in knowledge_bases:
            results.append({
                'id': kb.id,
                'name': kb.name,
                'description': kb.description,
                'base_type': kb.base_type,
                'is_public': kb.is_public,
                'usage_count': kb.usage_count,
                'created_at': kb.created_at.isoformat(),
                'updated_at': kb.updated_at.isoformat() if kb.updated_at else None,
                # 'author': {
                #     'id': kb.author.id,
                #     'username': kb.author.username
                # },
                'author_id': kb.author_id,
                'author_name': kb.author.name,
                'categories': [{
                    'id': cat.id,
                    'name': cat.name
                } for cat in kb.categories],
                'can_migrate': True  # 表示当前用户可以迁移此知识库
            })

        return jsonify({
            'success': True,
            'data': {
                'knowledge_bases': results,
                'count': len(results),
                'filters': {
                    'applied': {
                        'category_id': category_id,
                        'base_type': base_type,
                        'min_usage': min_usage
                    },
                    'sort': {
                        'by': sort_by,
                        'order': order
                    }
                }
            }
        }), 200

    except Exception as e:
        current_app.logger.error(
            f"获取公开知识库失败 - UserID: {g.current_user.id}, Error: {str(e)}",
            exc_info=True
        )
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500