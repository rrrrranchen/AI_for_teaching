import os
import uuid
from venv import logger
from bson import ObjectId
from flask import Blueprint, app, current_app, json, make_response, redirect, render_template, request, jsonify, send_file, session
from jwt import InvalidKeyError
from sqlalchemy import func, select
from app.utils.database import db
from app.models.user import User
from app.models.courseclass import Courseclass
from app.models.resources import Metadata, MultimediaResource
from app.models.relationship import teacher_class
from app.utils.file_validators import allowed_file
from app.utils.fileparser import FileParser
from app.utils.secure_filename import secure_filename
from app.utils.preview_generator import generate_preview
from werkzeug.utils import safe_join  
from mongoengine.errors import DoesNotExist, ValidationError
from app.models.course import Course
from app.models.teaching_design import TeachingDesign
from app.models.teachingdesignversion import TeachingDesignVersion
from app.models.question import Question
from app.services.lesson_plan import generate_teaching_plans

teachingdesign_bp=Blueprint('teachingdesign',__name__)

def get_pre_class_questions_as_feedback(course_id):
    """
    提取指定课程的课前预习题目及学生答题情况，作为student_feedback参数
    :param course_id: 课程ID
    :return: 格式化后的学生反馈字符串，包含题目和答题情况
    """
    # 查询该课程的所有课前预习题目及相关学生答案（单次查询优化）
    pre_class_questions = (Question.query
                          .filter_by(course_id=course_id, timing='pre_class', is_public=True)
                          .options(db.joinedload(Question.answers))
                          .all())

    if not pre_class_questions:
        return "该课程暂无课前预习题目"

    feedback_lines = ["课前预习题目及学生答题情况汇总:"]
    all_answers = []
    question_stats = []

    for question in pre_class_questions:
        answers = question.answers
        all_answers.extend(answers)
        
        # 计算当前题目的统计
        total_answers = len(answers)
        correct_count = sum(1 for a in answers if a.correct_percentage >= 80)
        correct_rate = (correct_count / total_answers * 100) if total_answers > 0 else 0
        avg_correct = sum(a.correct_percentage for a in answers) / total_answers if total_answers > 0 else 0
        
        question_stats.append({
            'question': question,
            'total_answers': total_answers,
            'correct_rate': correct_rate,
            'avg_correct': avg_correct
        })

        # 添加题目信息到反馈
        feedback_lines.append(f"\n题目ID: {question.id}")
        feedback_lines.append(f"题型: {get_question_type_name(question.type)}")
        feedback_lines.append(f"内容: {question.content[:50]}...")
        feedback_lines.append(f"难度: {question.difficulty if question.difficulty else '未设置'}")

        if total_answers > 0:
            feedback_lines.append(f"答题情况: {correct_count}/{total_answers}人答对 (正确率: {correct_rate:.1f}%)")
            
            # 添加常见错误示例
            wrong_answers = [a.answer for a in answers if a.correct_percentage < 80]
            if wrong_answers:
                common_wrong = max(set(wrong_answers), key=wrong_answers.count)
                feedback_lines.append(f"常见错误答案示例: '{common_wrong[:50]}...'")  # 限制错误答案长度
        else:
            feedback_lines.append("暂无学生答题数据")

    # 添加总体统计
    if all_answers:
        total_questions = len(pre_class_questions)
        total_attempts = len(all_answers)
        overall_avg = sum(a.correct_percentage for a in all_answers) / total_attempts

        feedback_lines.append("\n总体统计:")
        feedback_lines.append(f"- 预习题目数量: {total_questions}题")
        feedback_lines.append(f"- 学生答题人次: {total_attempts}次")
        feedback_lines.append(f"- 平均正确率: {overall_avg:.1f}%")

        # 找出最难和最易的题目
        if len(question_stats) > 1:
            hardest = min(question_stats, key=lambda x: x['avg_correct'])
            easiest = max(question_stats, key=lambda x: x['avg_correct'])
            
            feedback_lines.append(f"- 最难题目: 题目ID {hardest['question'].id} (平均正确率: {hardest['avg_correct']:.1f}%)")
            feedback_lines.append(f"- 最易题目: 题目ID {easiest['question'].id} (平均正确率: {easiest['avg_correct']:.1f}%)")

    return "\n".join(feedback_lines)

def get_question_type_name(type_enum):
    """辅助函数：获取题型名称"""
    return {
        'choice': '选择题',
        'fill': '填空题',
        'short_answer': '简答题'
    }.get(type_enum, '未知题型')
def generate_lesson_plans(objectives, course_content):
    return [
        {
            "content": "版本1内容",
            "recommend_rate": "80"  # 改为字符串形式的数字
        },
        {
            "content": "版本2内容",
            "recommend_rate": "85"
        },
        {
            "content": "版本3内容", 
            "recommend_rate": "90"
        }
    ]
def is_logged_in():
    """检查用户是否登录"""
    return 'user_id' in session

def get_current_user():
    """获取当前登录用户"""
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

def is_teacher_of_course(course_id):
    """检查当前用户是否是课程的任课老师"""
    current_user = get_current_user()
    if not current_user or current_user.role != 'teacher':
        return False
    
    # 获取课程所属的课程班
    course = Course.query.get(course_id)
    if not course:
        return False
    
    course_class = Courseclass.query.filter(Courseclass.courses.contains(course)).first()
    if not course_class:
        return False
    
    # 检查用户是否是课程班的老师
    association = db.session.scalar(
        select(func.count()).where(
            teacher_class.c.teacher_id == current_user.id,
            teacher_class.c.class_id == course_class.id
        )
    )
    return association > 0

@teachingdesign_bp.before_request
def check_authentication():
    """全局权限检查（排除特定路由）"""
    excluded_routes = ['teachingdesign.get_version_detail', 'teachingdesign.get_design_versions']
    if request.endpoint in excluded_routes:
        return
    
    if not is_logged_in():
        return make_response(code=401, message="请先登录")
    
@teachingdesign_bp.route('/createteachingdesign', methods=['POST'])
def create_teaching_design():
    """
    创建教学设计并生成三个版本（自动获取预习题目作为反馈）
    请求参数:
    {
        "course_id": int,       # 课程ID（必填）
        "title": str,           # 设计标题
        "objectives": str,      # 教学目标
        "course_content": str   # 课程内容
    }
    """
    try:
        # 1. 身份验证和基础校验
        current_user = get_current_user()
        if not current_user or current_user.role != 'teacher':
            return jsonify(code=403, message="无操作权限"), 403

        data = request.get_json()
        if not data or 'course_id' not in data:
            return jsonify(code=400, message="缺少必要参数"), 400

        # 2. 自动获取课前预习题目作为学生反馈
        student_feedback = get_pre_class_questions_as_feedback(data['course_id'])
        
        # 3. 生成教学方案（使用自动获取的反馈）
        teaching_plans = generate_teaching_plans(
            course_content=data.get('course_content', ''),
            student_feedback=student_feedback
        )

        # 4. 创建数据库记录（示例代码，需适配您的ORM）
        new_design = TeachingDesign(
            course_id=data['course_id'],
            creator_id=current_user.id,
            title=data.get('title', '未命名设计')
        )
        db.session.add(new_design)
        db.session.flush()

        # 5. 保存生成的版本
        versions = []
        for i, plan in enumerate(teaching_plans['plans'], 1):
            version = TeachingDesignVersion(
                design_id=new_design.id,
                version=f'v{i}',
                content=json.dumps({
                    'objectives': data.get('objectives', ''),
                    'plan_content': plan['content'],
                    'analysis': plan.get('analysis', '')
                }),
                recommendation_score=plan['recommendation'],
                level=plan['level']
            )
            db.session.add(version)
            versions.append(version)

        # 6. 设置当前版本（选择推荐指数最高的）
        if versions:
            best_version = max(versions, key=lambda v: v.recommendation_score)
            new_design.current_version_id = best_version.id

        db.session.commit()

        # 7. 返回响应
        return jsonify({
            "code": 200,
            "data": {
                "design_id": new_design.id,
                "feedback_used": student_feedback[:200] + "..." if len(student_feedback) > 200 else student_feedback,
                "versions": [{
                    "id": v.id,
                    "level": v.level,
                    "recommendation": v.recommendation_score
                } for v in versions]
            }
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"创建教学设计失败: {str(e)}")
        return jsonify(code=500, message="服务器内部错误"), 500

@teachingdesign_bp.route('/<int:design_id>/versions', methods=['GET'])
def get_design_versions(design_id):
    """
    根据教学设计ID获取所有版本
    ---
    tags:
      - 教学设计
    parameters:
      - name: design_id
        in: path
        type: integer
        required: true
        description: 教学设计ID
    responses:
      200:
        description: 获取成功
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 200
            message:
              type: string
              example: "获取成功"
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 1
                  version:
                    type: string
                    example: "v1"
                  content:
                    type: string
                    example: "教学内容..."
                  recommendation_score:
                    type: number
                    format: float
                    example: 85.5
                  created_at:
                    type: string
                    format: date-time
                    example: "2023-08-20T10:30:00Z"
                  updated_at:
                    type: string
                    format: date-time
                    example: "2023-08-21T14:25:00Z"
      404:
        description: 教学设计不存在
      403:
        description: 无访问权限
    """
    try:
        # 1. 基础验证
        current_user = get_current_user()
        if not current_user:
            return jsonify(code=401, message="请先登录"), 401

        # 2. 查询教学设计
        design = TeachingDesign.query.get(design_id)
        if not design:
            return jsonify(code=404, message="教学设计不存在"), 404

        # 3. 权限验证（教师只能查看自己课程的）
        if current_user.role == 'teacher' and not is_teacher_of_course(design.course_id):
            return jsonify(code=403, message="无访问权限"), 403

        # 4. 查询所有版本（按版本号排序）
        versions = TeachingDesignVersion.query.filter_by(
            design_id=design_id
        ).order_by(TeachingDesignVersion.version).all()

        # 5. 构建响应数据
        versions_data = []
        for version in versions:
            try:
                content = json.loads(version.content) if version.content else None
            except json.JSONDecodeError:
                content = version.content
            
            versions_data.append({
                "id": version.id,
                "version": version.version,
                "content": content,
                "recommendation_score": version.recommendation_score,
                "created_at": version.created_at.isoformat() if version.created_at else None,
                "updated_at": version.updated_at.isoformat() if version.updated_at else None,
                "author_id": version.author_id
            })

        return jsonify(
            code=200,
            message="获取成功",
            data={
                "design_id": design.id,
                "title": design.title,
                "current_version_id": design.current_version_id,
                "versions": versions_data
            }
        ), 200

    except Exception as e:
        logger.error(f"获取教学设计版本失败: {str(e)}", exc_info=True)
        return jsonify(code=500, message="服务器内部错误"), 500