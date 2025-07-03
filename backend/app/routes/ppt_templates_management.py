from datetime import datetime
import os
from flask import Blueprint, current_app, g, request, jsonify, session
from werkzeug.utils import secure_filename
from app.models.ppttemplate import PPTTemplate
from app.utils.database import db
from app.models.user import User
from app.services.log_service import LogService

ppt_templates_management_bp = Blueprint('ppt_templates_management_bp', __name__)

def is_logged_in():
    return 'user_id' in session

def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

@ppt_templates_management_bp.before_request
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

# 配置上传目录
TEMPLATE_UPLOAD_FOLDER = 'static/template'
TEMPLATE_IMAGE_UPLOAD_FOLDER = 'static/templateimage'
ALLOWED_EXTENSIONS = {'pptx', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_next_template_number():
    """获取下一个可用的模板编号"""
    existing_templates = PPTTemplate.query.all()
    existing_numbers = [int(t.name.replace('template', '').replace('.pptx', '')) 
                      for t in existing_templates if t.name.startswith('template')]
    return max(existing_numbers) + 1 if existing_numbers else 1

@ppt_templates_management_bp.route('/ppt_templates', methods=['GET'])
def get_ppt_templates():
    """获取所有PPT模板"""
    templates = PPTTemplate.query.all()
    return jsonify([{
        'id': template.id,
        'name': template.name,
        'url': f'/static/template/{template.name}.pptx',
        'image_url': f'/static/templateimage/{template.name}.png'
    } for template in templates])

@ppt_templates_management_bp.route('/ppt_templates', methods=['POST'])
def create_ppt_template():
    """创建新的PPT模板"""
    template_dir = os.path.join(current_app.root_path, 'static', 'template')
    image_dir = os.path.join(current_app.root_path, 'static', 'templateimage')
    
    # 确保目录存在（跨平台兼容）
    os.makedirs(template_dir, exist_ok=True)
    os.makedirs(image_dir, exist_ok=True)
    
    # 检查文件上传
    if 'file' not in request.files or 'image' not in request.files:
        return jsonify({'error': '缺少文件或图片'}), 400

    file = request.files['file']
    image = request.files['image']
    

    # 验证文件类型
    if not (allowed_file(file.filename) and allowed_file(image.filename)):
        return jsonify({'error': '不允许的文件类型'}), 400
    
    # 获取下一个模板编号
    next_num = get_next_template_number()
    template_name = f'template{next_num}.pptx'
    image_name = f'template{next_num}.png'
    
    try:
        # 保存PPT文件
        file.save(os.path.join(template_dir, template_name))
        
        # 保存图片
        image.save(os.path.join(image_dir, image_name))
        
        # 创建数据库记录
        new_template = PPTTemplate(
            name=template_name,
            url=f'/static/template/{template_name}',
            image_url=f'/static/templateimage/{image_name}'
        )
        db.session.add(new_template)
        db.session.commit()
        
        return jsonify({
            'message': 'PPT模板创建成功',
            'template': {
                'id': new_template.id,
                'name': new_template.name,
                'url': new_template.url,
                'image_url': new_template.image_url
            }
        }), 201
    except Exception as e:
        # 如果出错，删除已上传的文件
        if os.path.exists(os.path.join(TEMPLATE_UPLOAD_FOLDER, template_name)):
            os.remove(os.path.join(TEMPLATE_UPLOAD_FOLDER, template_name))
        if os.path.exists(os.path.join(TEMPLATE_IMAGE_UPLOAD_FOLDER, image_name)):
            os.remove(os.path.join(TEMPLATE_IMAGE_UPLOAD_FOLDER, image_name))
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@ppt_templates_management_bp.route('/ppt_templates/<int:template_id>', methods=['GET'])
def get_ppt_template(template_id):
    """获取单个PPT模板详情"""
    template = PPTTemplate.query.get_or_404(template_id)
    return jsonify({
        'id': template.id,
        'name': template.name,
        'url': template.url,
        'image_url': template.image_url
    })

@ppt_templates_management_bp.route('/ppt_templates/<int:template_id>', methods=['DELETE'])
def delete_ppt_template(template_id):
    """删除PPT模板"""
    template = PPTTemplate.query.get_or_404(template_id)
    
    try:
        # 删除文件
        ppt_path = os.path.join(TEMPLATE_UPLOAD_FOLDER, template.name)
        image_path = os.path.join(TEMPLATE_IMAGE_UPLOAD_FOLDER, 
                               template.name.replace('.pptx', '.png'))
        
        if os.path.exists(ppt_path):
            os.remove(ppt_path)
        if os.path.exists(image_path):
            os.remove(image_path)
        
        # 删除数据库记录
        db.session.delete(template)
        db.session.commit()
        
        return jsonify({'message': 'PPT模板删除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@ppt_templates_management_bp.after_request
def log_after_request(response):
    # 跳过预检请求和错误响应
    if request.method == 'OPTIONS' or not (200 <= response.status_code < 400):
        return response

    # 获取当前用户（已通过before_request验证）
    current_user = g.current_user
    user_info = {
        'id': current_user.id,
        'role': current_user.role
    }

    # 记录所有成功请求（无需白名单检查）
    LogService.log_operation(
        user_id=user_info['id'],
        user_type=user_info['role'],
        operation_type=f"{request.method}_{request.endpoint.replace('.', '_')}",
        details={
            'path': request.path,
            'method': request.method,
            'params': dict(request.args) if request.args else None,
            'body': request.get_json(silent=True) if request.method in ['POST', 'PUT', 'PATCH', 'DELETE'] else None,
            'status': response.status_code,
            'timestamp': datetime.now().isoformat()
        }
    )
    return response