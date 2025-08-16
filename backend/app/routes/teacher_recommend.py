from datetime import datetime
from flask import Blueprint, g, render_template, request, jsonify, session
from app.utils.database import db
from app.models.teacher_recommend import TeacherRecommend
from app.models.teaching_design import TeachingDesign
from app.utils.recommend_to_teachers import generate_final_markdown, generate_final_json, recommend_pictures
from app.models.user import User
from app.services.log_service import LogService

teacher_recommend_bp=Blueprint('teacher_recommend_bp', __name__)
def is_logged_in():
    return 'user_id' in session
def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

@teacher_recommend_bp.before_request
def before_request():
    if request.method == 'OPTIONS':
        return
    # 检查用户是否已登录
    if is_logged_in():
        # 获取当前用户并存储到 g 对象中
        g.current_user = get_current_user()
    else:
        # 如果用户未登录，返回未授权错误
        return jsonify({'error': 'Unauthorized'}), 401
    
@teacher_recommend_bp.route('/generate_recommendation/<int:teaching_design_id>', methods=['POST'])
def generate_recommendation(teaching_design_id):
    """生成推荐教师列表"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': '用户不存在'}), 404

    user_id = current_user.id

    if not teaching_design_id or not user_id:
        return jsonify({"error": "缺少必要的参数"}), 400

    # 查询指定的教学设计
    teaching_design = TeachingDesign.query.get(teaching_design_id)
    if not teaching_design:
        return jsonify({"error": "未找到对应的教学设计"}), 404

    # 检查权限：只有创建者或管理员可以生成推荐
    if teaching_design.creator_id != current_user.id and current_user.role != 'admin':
        return jsonify({"error": "无权生成推荐"}), 403

    try:
        # 调用 AI 函数处理教学设计的 input 字段内容
        ai_video_result = generate_final_json(teaching_design.input)
        # ai_image_result = "{\n    \"images\": [\n        \"https://images.unsplash.com/photo-1527689368864-3a821dbccc34?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3MzQwOTR8MHwxfHJhbmRvbXx8fHx8fHx8fDE3NDQ0NjA4NDZ8&ixlib=rb-4.0.3&q=80&w=1080\",\n        \"https://images.unsplash.com/photo-1499752228123-488eb1d280dd?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3MzQwOTR8MHwxfHJhbmRvbXx8fHx8fHx8fDE3NDQ0NjA4NDZ8&ixlib=rb-4.0.3&q=80&w=1080\",\n        \"https://images.unsplash.com/45/QDSMoAMTYaZoXpcwBjsL__DSC0104-1.jpg?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3MzQwOTR8MHwxfHJhbmRvbXx8fHx8fHx8fDE3NDQ0NjA4NDZ8&ixlib=rb-4.0.3&q=80&w=1080\",\n        \"https://images.unsplash.com/photo-1476733419970-c703149c016b?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3MzQwOTR8MHwxfHJhbmRvbXx8fHx8fHx8fDE3NDQ0NjA4NDZ8&ixlib=rb-4.0.3&q=80&w=1080\"\n    ]\n}"
        #recommend_pictures(teaching_design.input)

        # 创建 TeacherRecommend 记录并存储结果
        teacher_recommend = TeacherRecommend(
            user_id=user_id,
            teaching_design_id=teaching_design_id,
            video_recommendations=ai_video_result,
            # image_recommendations=ai_image_result
        )
        db.session.add(teacher_recommend)
        db.session.commit()

        return jsonify({
            "message": "推荐内容生成成功",
            "recommendation_id": teacher_recommend.id
        }), 201

    except Exception as e:
        # 如果发生错误，回滚数据库会话并返回错误信息
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
@teacher_recommend_bp.route('/get_recommendation_by_design/<int:teaching_design_id>', methods=['GET'])
def get_recommendation_by_design(teaching_design_id):
    """获得推荐资源"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': '用户不存在'}), 404

    try:
        # 查询指定的教学设计
        teaching_design = TeachingDesign.query.get(teaching_design_id)
        if not teaching_design:
            return jsonify({"error": "未找到对应的教学设计"}), 404

        # 检查权限：只有在教案非公开情况下，教学设计的创建者或管理员可以查看推荐资源
        if not TeachingDesign.is_public and teaching_design.creator_id != current_user.id and current_user.role != 'admin':
            return jsonify({"error": "无权查看此教学设计的推荐资源"}), 403

        # 查询对应的推荐资源
        teacher_recommend = TeacherRecommend.query.filter_by(teaching_design_id=teaching_design_id).first()
        if not teacher_recommend:
            # 如果没有推荐资源，返回空对象或特定提示信息
            teacher_recommend = None

        # 构建响应数据
        recommendation_data = {
            "video_recommendations": teacher_recommend.video_recommendations,
            # "image_recommendations": teacher_recommend.image_recommendations
        }

        return jsonify({"data": recommendation_data}), 200

    except Exception as e:
        # 如果发生错误，返回错误信息
        return jsonify({"error": str(e)}), 500
    
@teacher_recommend_bp.after_request
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