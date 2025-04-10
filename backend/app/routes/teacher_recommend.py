from flask import Blueprint, render_template, request, jsonify, session
from app.utils.database import db
from app.models.teacher_recommend import TeacherRecommend
from app.models.teaching_design import TeachingDesign
from app.services.recommend_to_teachers import generate_final_markdown, recommend_pictures

teacher_recommend_bp=Blueprint('teacher_recommend_bp', __name__)

@teacher_recommend_bp.route('/generate_recommendation', methods=['POST'])
def generate_recommendation():
    data = request.json
    teaching_design_id = data.get('teaching_design_id')
    user_id = data.get('user_id')

    if not teaching_design_id or not user_id:
        return jsonify({"error": "缺少必要的参数"}), 400

    # 查询指定的教学设计
    teaching_design = TeachingDesign.query.get(teaching_design_id)
    if not teaching_design:
        return jsonify({"error": "未找到对应的教学设计"}), 404

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

    return jsonify({"message": "推荐内容生成成功", "recommendation_id": teacher_recommend.id}), 201