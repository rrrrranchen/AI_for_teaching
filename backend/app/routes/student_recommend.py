from typing import Dict, List
from flask import Blueprint, jsonify, session
from app.utils.database import db
from app.models.courseclass import Courseclass
from app.models.course import Course
from app.models.user import User
from app.models.relationship import teacher_class,student_class,course_courseclass
from app.models.question import Question
from app.routes.teaching_design import get_question_type_name
from app.models.studentanswer import StudentAnswer
from sqlalchemy.orm import Session
from app.models.student_recommend import StudentRecommend
from app.utils.recommend_to_students import extract_keywords_from_report, generate_final_json
from app.models.studentanalysisreport import StudentAnalysisReport
student_recommend_bp=Blueprint('student_recommend_bp', __name__)
def is_logged_in():
    return 'user_id' in session
def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None
def get_pre_class_student_answers_by_course(session: Session, user_id: int, course_id: int) -> List[Dict]:
    """
    根据用户 ID 和课程 ID 查询该用户在该课程中的课前习题作答记录，并整理成字典列表。

    :param session: SQLAlchemy 的数据库会话
    :param user_id: 用户的 ID
    :param course_id: 课程的 ID
    :return: 包含课前习题作答记录的字典列表
    """
    # 查询指定用户在指定课程中的课前习题作答记录
    student_answers = (
        session.query(
            StudentAnswer.id,
            StudentAnswer.question_id,
            StudentAnswer.answer,
            StudentAnswer.correct_percentage,
            StudentAnswer.answered_at,
            StudentAnswer.modified_by,
            StudentAnswer.modified_at,
            Question.content.label("question_content"),
            Question.correct_answer,
            Question.difficulty,
            Question.timing
        )
        .join(Question, StudentAnswer.question_id == Question.id)
        .filter(StudentAnswer.student_id == user_id)
        .filter(StudentAnswer.course_id == course_id)
        .filter(Question.timing == 'pre_class')  # 只选择课前习题
        .all()
    )

    # 初始化一个列表，用于存储处理后的数据
    processed_answers = []

    # 遍历每个作答记录，提取关键信息并封装为字典
    for answer in student_answers:
        processed_answer = {
            "answer_id": answer.id,
            "question_id": answer.question_id,
            "question_content": answer.question_content,
            "correct_answer": answer.correct_answer,
            "student_answer": answer.answer,
            "correct_percentage": answer.correct_percentage,
            "difficulty": answer.difficulty,
            "timing": answer.timing
        }
        processed_answers.append(processed_answer)

    return processed_answers

def save_student_recommendation(session: Session, user_id: int, course_id: int, report):
    """
    根据用户 ID 和课程 ID 查询课前习题作答记录，生成推荐内容，并存储到 student_recommend 表中。

    :param session: SQLAlchemy 的数据库会话
    :param user_id: 用户的 ID
    :param course_id: 课程的 ID
    :param report: 课前习题作答记录
    """
    try:
        # 调用生成推荐内容的函数

        keywords = extract_keywords_from_report(report)
        recommendations_content =generate_final_json(keywords)
        # 创建 StudentRecommend 记录
        student_recommend = StudentRecommend(
            user_id=user_id,
            course_id=course_id,
            type='pre_class',
            content=recommendations_content
        )

        # 将记录保存到数据库
        session.add(student_recommend)
        session.commit()

        return student_recommend

    except Exception as e:
        session.rollback()
        raise e


def generate_and_save_pre_class_recommendations(session: Session, user_id: int, course_id: int):
    """
    根据用户 ID 和课程 ID 查询课前习题作答记录，生成推荐内容，并存储到 student_recommend 表中。

    :param session: SQLAlchemy 的数据库会话
    :param user_id: 用户的 ID
    :param course_id: 课程的 ID
    """
    # 查询课前习题作答记录
    report = get_pre_class_student_answers_by_course(session, user_id, course_id)

    # 保存推荐内容
    student_recommend = save_student_recommendation(session, user_id, course_id, report)

    return student_recommend

@student_recommend_bp.route('/generate_pre_class_recommendations/<int:course_id>', methods=['POST'])
def generate_pre_class_recommendations_route(course_id):

    user_id = get_current_user().id

    if not user_id or not course_id:
        return jsonify({"error": "缺少必要的参数"}), 400

    try:
        # 调用函数生成并保存推荐内容
        recommendation = generate_and_save_pre_class_recommendations(db.session, user_id, course_id)
        return jsonify({"message": "推荐内容生成成功", "recommendation_id": recommendation.id}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def get_user_pre_class_recommendations_by_course(session: Session, user_id: int, course_id: int) -> List[Dict]:
    """
    根据用户 ID 和课程 ID 查询该用户在该课程中的课前预习推荐资源，并整理成字典列表。

    :param session: SQLAlchemy 的数据库会话
    :param user_id: 用户的 ID
    :param course_id: 课程的 ID
    :return: 包含课前预习推荐资源的字典列表
    """
    # 查询指定用户在指定课程中的所有课前预习推荐资源
    recommendations = (
        session.query(StudentRecommend)
        .filter_by(user_id=user_id, course_id=course_id, type='pre_class')
        .all()
    )

    # 初始化一个列表，用于存储处理后的数据
    processed_recommendations = []

    # 遍历每个推荐资源，提取关键信息并封装为字典
    for recommendation in recommendations:
        processed_recommendation = {
            "type": recommendation.type,
            "content": recommendation.content
        }
        processed_recommendations.append(processed_recommendation)

    return processed_recommendations

@student_recommend_bp.route('/get_user_pre_class_recommendations/<int:course_id>', methods=['GET'])
def get_user_pre_class_recommendations_route(course_id):
    """
    根据课程 ID 查询当前登录用户的课前预习推荐资源的接口。
    """
    # 检查用户是否登录
    if not is_logged_in():
        return jsonify({'error': '未登录'}), 401

    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': '用户不存在'}), 404

    try:
        # 调用函数查询当前登录用户的课前预习推荐资源
        recommendations = get_user_pre_class_recommendations_by_course(db.session, current_user.id, course_id)
        return jsonify({"data": recommendations}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

def save_student_post_class_recommendation(session: Session, user_id: int, course_id: int, report):
    """
    根据用户 ID 和课程 ID 查询课后习题分析报告，生成推荐内容，并存储到 student_recommend 表中。

    :param session: SQLAlchemy 的数据库会话
    :param user_id: 用户的 ID
    :param course_id: 课程的 ID
    :param report: 课后习题分析报告
    """
    try:
        # 调用生成推荐内容的函数
        keywords = extract_keywords_from_report(report)
        recommendations_content =generate_final_json(keywords)

        # 创建 StudentRecommend 记录
        student_recommend = StudentRecommend(
            user_id=user_id,
            course_id=course_id,
            type='post_class',
            content=recommendations_content
        )

        # 将记录保存到数据库
        session.add(student_recommend)
        session.commit()

        return student_recommend

    except Exception as e:
        session.rollback()
        raise e
    
def get_post_class_analysis_report_by_course(session: Session, user_id: int, course_id: int) -> List[Dict]:
    """
    根据用户 ID 和课程 ID 查询该用户在该课程中的课后习题分析报告，并整理成字典列表。

    :param session: SQLAlchemy 的数据库会话
    :param user_id: 用户的 ID
    :param course_id: 课程的 ID
    :return: 包含课后习题分析报告的字典列表
    """
    # 查询指定用户在指定课程中的课后习题分析报告
    reports = (
        session.query(StudentAnalysisReport)
        .filter_by(student_id=user_id, course_id=course_id)
        .all()
    )

    # 初始化一个列表，用于存储处理后的数据
    processed_reports = []

    # 遍历每个报告，提取关键信息并封装为字典
    for report in reports:
        processed_report = {
            "id": report.id,
            "student_id": report.student_id,
            "course_id": report.course_id,
            "report_content": report.report_content,
            "created_at": report.created_at.isoformat() if report.created_at else None
        }
        processed_reports.append(processed_report)

    return processed_reports

def generate_and_save_post_class_recommendations(session: Session, user_id: int, course_id: int):
    """
    根据用户 ID 和课程 ID 查询课后习题分析报告，生成推荐内容，并存储到 student_recommend 表中。

    :param session: SQLAlchemy 的数据库会话
    :param user_id: 用户的 ID
    :param course_id: 课程的 ID
    """
    # 查询课后习题分析报告
    reports = get_post_class_analysis_report_by_course(session, user_id, course_id)

    # 如果没有报告，返回 None
    if not reports:
        return None

    # 保存推荐内容
    student_recommend = save_student_post_class_recommendation(session, user_id, course_id, reports)

    return student_recommend

@student_recommend_bp.route('/generate_post_class_recommendations/<int:course_id>', methods=['POST'])
def generate_post_class_recommendations_route(course_id):
    """
    根据课程 ID 查询当前登录用户的课后习题分析报告，生成推荐内容，并存储到 student_recommend 表中的接口。
    """
    # 检查用户是否登录
    if not is_logged_in():
        return jsonify({'error': '未登录'}), 401

    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': '用户不存在'}), 404

    try:
        # 调用函数生成并保存推荐内容
        recommendation = generate_and_save_post_class_recommendations(db.session, current_user.id, course_id)
        if recommendation:
            return jsonify({"message": "推荐内容生成成功", "recommendation_id": recommendation.id}), 201
        else:
            return jsonify({"message": "没有找到课后习题分析报告"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def get_user_post_class_recommendations_by_course(session: Session, user_id: int, course_id: int) -> List[Dict]:
    """
    根据用户 ID 和课程 ID 查询该用户在该课程中的课后推荐资源，并整理成字典列表。

    :param session: SQLAlchemy 的数据库会话
    :param user_id: 用户的 ID
    :param course_id: 课程的 ID
    :return: 包含课后推荐资源的字典列表
    """
    # 查询指定用户在指定课程中的所有课后推荐资源
    recommendations = (
        session.query(StudentRecommend)
        .filter_by(user_id=user_id, course_id=course_id, type='post_class')
        .all()
    )

    # 初始化一个列表，用于存储处理后的数据
    processed_recommendations = []

    # 遍历每个推荐资源，提取关键信息并封装为字典
    for recommendation in recommendations:
        processed_recommendation = {
            "course_id": recommendation.course_id,
            "type": recommendation.type,
            "content": recommendation.content
        }
        processed_recommendations.append(processed_recommendation)

    return processed_recommendations


@student_recommend_bp.route('/get_user_post_class_recommendations/<int:course_id>', methods=['GET'])
def get_user_post_class_recommendations_route(course_id):
    """
    根据课程 ID 查询当前登录用户的课后推荐资源的接口。
    """
    # 检查用户是否登录
    if not is_logged_in():
        return jsonify({'error': '未登录'}), 401

    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': '用户不存在'}), 404

    try:
        # 调用函数查询当前登录用户的课后推荐资源
        recommendations = get_user_post_class_recommendations_by_course(db.session, current_user.id, course_id)
        return jsonify({"data": recommendations}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500