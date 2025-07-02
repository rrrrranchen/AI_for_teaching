from flask import Blueprint, request, jsonify
from app.models.ppttemplate import PPTTemplate
from app.utils.database import db

ppt_templates_management_bp = Blueprint('ppt_templates_management_bp', __name__)

@ppt_templates_management_bp.route('/ppt_templates', methods=['GET'])
def get_ppt_templates():
    """
    获取所有PPT模板
    """
    templates = PPTTemplate.query.all()
    return jsonify([{
        'id': template.id,
        'name': template.name,
        'url': template.url,
        'image_url': template.image_url
    } for template in templates])

@ppt_templates_management_bp.route('/ppt_templates', methods=['POST'])
def create_ppt_template():
    """
    创建新的PPT模板
    请求体示例:
    {
        "name": "",
        "url": "",
        "image_url": ""
    }
    """
    data = request.get_json()
    
    # 验证必填字段
    if not all(key in data for key in ['name', 'url', 'image_url']):
        return jsonify({'error': '缺少必填字段: name, url 或 image_url'}), 400
    
    # 检查名称是否已存在
    if PPTTemplate.query.filter_by(name=data['name']).first():
        return jsonify({'error': '模板名称已存在'}), 409
    
    try:
        new_template = PPTTemplate(
            name=data['name'],
            url=data['url'],
            image_url=data['image_url']
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
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@ppt_templates_management_bp.route('/ppt_templates/<int:template_id>', methods=['GET'])
def get_ppt_template(template_id):
    """
    获取单个PPT模板详情
    """
    template = PPTTemplate.query.get_or_404(template_id)
    return jsonify({
        'id': template.id,
        'name': template.name,
        'url': template.url,
        'image_url': template.image_url
    })

@ppt_templates_management_bp.route('/ppt_templates/<int:template_id>', methods=['DELETE'])
def delete_ppt_template(template_id):
    """
    删除PPT模板
    """
    template = PPTTemplate.query.get_or_404(template_id)
    db.session.delete(template)
    db.session.commit()
    return jsonify({'message': 'PPT模板删除成功'}), 200