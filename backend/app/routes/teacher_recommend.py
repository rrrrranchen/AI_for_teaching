from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session
from app.utils.database import db
from app.models.teacher_recommend import TeacherRecommend
from app.models.teaching_design import TeachingDesign
from app.utils.recommend_to_teachers import generate_final_markdown, recommend_pictures
from app.models.user import User

teacher_recommend_bp=Blueprint('teacher_recommend_bp', __name__)
def is_logged_in():
    return 'user_id' in session
def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

    
@teacher_recommend_bp.route('/generate_recommendation/<int:teaching_design_id>', methods=['POST'])
def generate_recommendation(teaching_design_id):
    # 检查用户是否登录
    if not is_logged_in():
        return jsonify({'error': '未登录'}), 401

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
        ai_video_result = generate_final_markdown(teaching_design.input)
        ai_image_result = recommend_pictures(teaching_design.input)

        # 创建 TeacherRecommend 记录并存储结果
        teacher_recommend = TeacherRecommend(
            user_id=user_id,
            teaching_design_id=teaching_design_id,
            video_recommendations=ai_video_result,
            image_recommendations=ai_image_result
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
    # 检查用户是否登录
    if not is_logged_in():
        return jsonify({'error': '未登录'}), 401

    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': '用户不存在'}), 404

    try:
        # 查询指定的教学设计
        teaching_design = TeachingDesign.query.get(teaching_design_id)
        if not teaching_design:
            return jsonify({"error": "未找到对应的教学设计"}), 404

        # 检查权限：只有教学设计的创建者或管理员可以查看推荐资源
        if teaching_design.creator_id != current_user.id and current_user.role != 'admin':
            return jsonify({"error": "无权查看此教学设计的推荐资源"}), 403

        # 查询对应的推荐资源
        teacher_recommend = TeacherRecommend.query.filter_by(teaching_design_id=teaching_design_id).first()
        if not teacher_recommend:
            # 如果没有推荐资源，返回空对象或特定提示信息
            return jsonify({"data": None}), 200

        # 构建响应数据
        recommendation_data = {
            "video_recommendations": teacher_recommend.video_recommendations,
            "image_recommendations": teacher_recommend.image_recommendations
        }

        return jsonify({"data": recommendation_data}), 200

    except Exception as e:
        # 如果发生错误，返回错误信息
        return jsonify({"error": str(e)}), 500