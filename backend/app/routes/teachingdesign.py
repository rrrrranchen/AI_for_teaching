from bson import ObjectId
from flask import Blueprint, render_template, request, jsonify, session
import mongoengine
from app.utils.database import db
from app.models.teachingdesign import Assessment, Content, InteractionFlow, TeachingDesign, TimePlan
from app.services.demo import generate_teaching_design
from app.models.course import Course

teachingdesign_bp=Blueprint('teachingdesign',__name__)


def is_logged_in():
    return 'user_id' in session


@teachingdesign_bp.route('/generate_teaching_design', methods=['POST'])
def teaching_design_api():
    # 获取请求中的JSON数据
    data = request.json

    # 提取参数
    course_id = data.get('course_id')  # 前端传入的课程ID
    content = data.get('content', [])
    purpose = data.get('purpose', [])
    interaction = data.get('interaction', [])
    time = data.get('time', 0)

    # 从数据库中获取课程描述
    course = Course.query.get(course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    course_description = course.description

    # 调用生成教学方案设计的函数
    teaching_design_data = generate_teaching_design(course_description, content, purpose, interaction, time)

    # 创建TeachingDesign文档
    teaching_design = TeachingDesign(
        course_id=course_id,  # 使用传入的course_id
        version=1,  # 假设版本号为1
        status="draft",  # 初始状态为草稿
        generated_by="AI",  # 假设由AI生成
        content=Content(
            objectives=teaching_design_data["content"]["objectives"],  # 确保传入了 objectives
            total_time=teaching_design_data["content"]["total_time"],  # 确保传入了 total_time
            resources=teaching_design_data["content"]["resources"],  # 确保传入了 resources
            key_point=teaching_design_data["content"]["key_point"],
            time_plan=[TimePlan(phase=tp["phase"], duration=tp["duration"], content=tp["content"]) for tp in teaching_design_data["content"]["time_plan"]],
            interaction_flows=[InteractionFlow(type=ifl["type"], description=ifl["description"], trigger_time=ifl["trigger_time"]) for ifl in teaching_design_data["content"]["interaction_flows"]],
            assessment=Assessment(
                criteria=teaching_design_data["content"]["assessment"]["criteria"],
                question_bank=[1, 2, 3],  # 示例题目ID
                assessresult=teaching_design_data["content"]["assessment"]["assessresult"],
                recommend_rate=teaching_design_data["content"]["assessment"]["recommend_rate"]
            )
        )
    )

    # 保存到MongoDB
    try:
        teaching_design.save()
    except mongoengine.errors.ValidationError as e:
        return jsonify({"error": str(e)}), 400

    # 返回成功响应
    return jsonify({"message": "Teaching design saved successfully", "id": str(teaching_design.id)})