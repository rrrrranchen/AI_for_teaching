import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from app.models.ppttemplate import PPTTemplate
from app.utils.database import db

ppt_templates_management_bp = Blueprint('ppt_templates_management_bp', __name__)

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
        file.save(os.path.join(TEMPLATE_UPLOAD_FOLDER, template_name))
        
        # 保存图片
        image.save(os.path.join(TEMPLATE_IMAGE_UPLOAD_FOLDER, image_name))
        
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
