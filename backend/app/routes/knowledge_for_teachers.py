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


from app.models.CategoryFile import CategoryFile
from app.models.KnowledgeBase import KnowledgeBase
from app.services.create_cat import ALLOWED_NON_STRUCTURAL_EXTENSIONS, ALLOWED_STRUCTURAL_EXTENSIONS, UPLOAD_FOLDER_KNOWLEDGE, allowed_file_non_structural, allowed_file_structural, create_knowledge_base_folder, create_user_category_folder, upload_file_to_folder_non_structural, upload_file_to_folder_structural
from app.services.create_kb import BASE_PATH, create_structured_db, create_unstructured_db,CATEGORY_PATH
from app.models.courseclass import Courseclass
from app.models.CategoryFileImage import CategoryFileImage

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
    courseclass = Courseclass.query.filter_by(id=courseclass_id).first()
    if not courseclass:
        return jsonify({'error': 'Courseclass not found'}), 404
    
    data = request.get_json()
    if not data or 'knowledge_base_ids' not in data:
        return jsonify({'error': 'No knowledge_base_ids provided'}), 400
    
    knowledge_base_ids = data['knowledge_base_ids']
    knowledge_bases = KnowledgeBase.query.filter(KnowledgeBase.id.in_(knowledge_base_ids)).all()
    if len(knowledge_bases) != len(knowledge_base_ids):
        return jsonify({'error': 'Some knowledge bases not found'}), 404
    
    try:
        for kb in knowledge_bases:
            # 检查知识库是否为开放的
            if not kb.is_public:
                # 检查知识库的作者是否为当前登录用户
                if kb.author_id != g.current_user.id:
                    return jsonify({'error': 'Knowledge base is not public and you are not the author'}), 403
                
                # 检查该班级的教师是否为当前登录用户
                if not any(teacher.id == g.current_user.id for teacher in courseclass.teachers):
                    return jsonify({'error': 'You are not a teacher of this courseclass'}), 403
        
        # 批量添加知识库到课程班
        courseclass.knowledge_bases.extend(kb for kb in knowledge_bases if kb not in courseclass.knowledge_bases)
        db.session.commit()
        return jsonify({'message': 'Knowledge bases added to courseclass successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    

@knowledge_for_teachers_bp.route('/teacher/courseclasses/<int:courseclass_id>/knowledge_bases', methods=['PUT'])
def update_knowledge_bases_of_courseclass(courseclass_id):
    """更新课程班与知识库的关系"""
    courseclass = Courseclass.query.filter_by(id=courseclass_id, author_id=g.current_user.id).first()
    if not courseclass:
        return jsonify({'error': 'Courseclass not found'}), 404
    
    data = request.get_json()
    if not data or 'knowledge_base_ids' not in data:
        return jsonify({'error': 'No knowledge_base_ids provided'}), 400
    
    knowledge_base_ids = data['knowledge_base_ids']
    knowledge_bases = KnowledgeBase.query.filter(KnowledgeBase.id.in_(knowledge_base_ids)).all()
    if len(knowledge_bases) != len(knowledge_base_ids):
        return jsonify({'error': 'Some knowledge bases not found'}), 404
    
    for kb in knowledge_bases:
        # 检查知识库是否为开放的
        if not kb.is_public:
            # 检查知识库的作者是否为当前登录用户
            if kb.author_id != g.current_user.id:
                return jsonify({'error': 'Knowledge base is not public and you are not the author'}), 403
            
            # 检查该班级的教师是否为当前登录用户
            if not any(teacher.id == g.current_user.id for teacher in courseclass.teachers):
                return jsonify({'error': 'You are not a teacher of this courseclass'}), 403
    
    try:
        # 更新课程班与知识库的关系
        courseclass.knowledge_bases = knowledge_bases
        db.session.commit()
        return jsonify({'message': 'Knowledge bases of courseclass updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
