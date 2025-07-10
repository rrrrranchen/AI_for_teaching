from datetime import datetime
from venv import logger
from flask import Blueprint, render_template, request, jsonify, session
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func, select
from werkzeug.security import check_password_hash
from app.utils.database import db
from app.models.question import Question
from app.models.course import Course
from app.models.user import User
from app.models.courseclass import Courseclass
from app.models.relationship import teacher_class
from app.models.studentanswer import StudentAnswer
from app.models.relationship import student_class
from app.models import course
from app.services.autogra_service import ChineseGrader
from app.routes.teaching_design import get_question_type_name, is_teacher_of_course
from app.services.analysis_report import generate_study_report, generate_study_report_overall
from app.models.studentanalysisreport import StudentAnalysisReport
from app.models.classanalysisreport import ClassAnalysisReport
from app.services.get_answer import get_class_student_answers, get_course_student_answers, get_student_answers_in_course, get_student_answers_with_question_and_course_details

studentanswer_bp=Blueprint('studentanswer',__name__)
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



# 检查用户是否登录
def is_logged_in():
    return 'user_id' in session

def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None
# 检查当前用户是否为课程班的创建老师
def is_teacher_of_courseclass(courseclass_id):
    current_user = get_current_user()
    if not current_user or current_user.role != 'teacher':
        return False
    
    # 查询 teacher_class 表，检查当前用户是否为课程班的老师
    association = db.session.scalar(
        select(func.count()).where(
            teacher_class.c.teacher_id == current_user.id,
            teacher_class.c.class_id == courseclass_id
        )
    )
    return association > 0

#验证是否为指定课程班的学生
def is_student_of_courseclass(courseclass_id):
    current_user = get_current_user()
    if not current_user or current_user.role != 'student':
        return False

    # 查询 student_class 表，检查当前用户是否为课程班的学生
    association = db.session.scalar(
        select(func.count()).where(
            student_class.c.student_id == current_user.id,
            student_class.c.class_id == courseclass_id
        )
    )
    return association > 0

#学生作答
@studentanswer_bp.route('/add_answers', methods=['POST'])
def add_answers():
    if not is_logged_in():
        return jsonify({'error': '未登录'}), 401

    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': '用户不存在'}), 404

    data = request.get_json()
    courseclass_id = data.get('courseclass_id')
    if not data or not courseclass_id:
        return jsonify({'error': '缺少数据或课程班级 ID'}), 400

    answers_data = data.get('answers')
    if not answers_data:
        return jsonify({'error': '缺少作答记录数组'}), 400

    try:
        results = []
        for answer_data in answers_data:
            question_id = answer_data.get('question_id')
            answer = answer_data.get('answer')

            if not all([question_id, answer]):
                results.append({
                    'question_id': question_id,
                    'error': '缺少必要参数'
                })
                continue

            # 获取题目信息
            question = Question.query.get(question_id)
            if not question:
                results.append({
                    'question_id': question_id,
                    'error': 'Question not found'
                })
                continue

            # 获取课程信息
            course = Course.query.get(question.course_id)
            if not course:
                results.append({
                    'question_id': question_id,
                    'error': 'Course not found'
                })
                continue

            # 检查截止时间
            now = datetime.utcnow()
            if question.timing == 'pre_class' and course.preview_deadline and now > course.preview_deadline:
                results.append({
                    'question_id': question_id,
                    'error': '预习题目已过截止时间'
                })
                continue
            elif question.timing == 'post_class' and course.post_class_deadline and now > course.post_class_deadline:
                results.append({
                    'question_id': question_id,
                    'error': '课后题目已过截止时间'
                })
                continue

            # 根据题目类型评分
            if question.type in ['choice', 'fill']:
                # 选择题和填空题：直接对比答案
                correct_percentage = 100 if answer.strip() == question.correct_answer.strip() else 0
            elif question.type == 'short_answer':
                # 简答题：使用 ChineseGrader 评估
                grader = ChineseGrader()
                grading_result = grader.grade(question.correct_answer, answer, max_score=10)
                correct_percentage = grading_result['score'] * 10  # 转换为百分比
            else:
                results.append({
                    'question_id': question_id,
                    'error': 'Unsupported question type'
                })
                continue

            # 检查是否已经存在该学生的答题记录
            existing_answer = StudentAnswer.query.filter_by(
                student_id=current_user.id,
                question_id=question_id
            ).first()

            if existing_answer:
                existing_answer.answer = answer
                existing_answer.correct_percentage = correct_percentage
                existing_answer.answered_at = datetime.utcnow()
                existing_answer.class_id = courseclass_id  # 更新 courseclass_id
            else:
                new_answer = StudentAnswer(
                    student_id=current_user.id,
                    question_id=question_id,
                    course_id=question.course_id,
                    class_id=courseclass_id,  # 添加 courseclass_id
                    answer=answer,
                    correct_percentage=correct_percentage
                )
                db.session.add(new_answer)

            db.session.commit()

            results.append({
                'question_id': question_id,
                'message': '答题记录处理成功',
                'answer_id': existing_answer.id if existing_answer else new_answer.id,
                'correct_percentage': correct_percentage
            })

        return jsonify(results), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'添加失败：{str(e)}'}), 500
    

#教师更新作答成绩
@studentanswer_bp.route('/update_score/<int:studentanswer_id>', methods=['POST'])
def update_score(studentanswer_id):
    # 身份验证
    if not is_logged_in():
        return jsonify({'error': '未登录'}), 401
    
    current_user = get_current_user()
    if not current_user or current_user.role != 'teacher':
        return jsonify({'error': '无权限操作'}), 403

    # 数据验证
    data = request.get_json()
    if not data:
        return jsonify({'error': '缺少数据'}), 400

    new_score = data.get('new_score')

    if new_score is None:
        return jsonify({'error': '缺少必要参数'}), 400

    try:
        # 获取答题记录
        student_answer = StudentAnswer.query.get(studentanswer_id)
        if not student_answer:
            return jsonify({'error': '答题记录不存在'}), 404

        # 权限验证
        if not is_teacher_of_course(student_answer.course_id):
            return jsonify({'error': '您不是该课程的老师'}), 403

        # 分数范围验证
        if not 0 <= new_score <= 100:
            return jsonify({'error': '分数必须在0-100之间'}), 400

        # 更新记录
        student_answer.correct_percentage = new_score
        student_answer.modified_by = current_user.id
        student_answer.modified_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'message': '分数修改成功',
            'data': {
                'answer_id': student_answer.id,
                'new_score': new_score,
                'modified_at': student_answer.modified_at.isoformat()
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500
    
#查询单个作答记录
@studentanswer_bp.route('/<int:answer_id>', methods=['GET'])
def get_answer(answer_id):
    if not is_logged_in():
        return jsonify({'error': '未登录'}), 401

    answer = StudentAnswer.query.get(answer_id)
    if not answer:
        return jsonify({'error': '答题记录不存在'}), 404

    # 权限检查：学生本人或班级老师
    current_user = get_current_user()
    if not (current_user.id == answer.student_id or 
            (current_user.role == 'teacher' and 
             is_teacher_of_courseclass(answer.class_id))):
        return jsonify({'error': '无权查看此记录'}), 403

    response_data = {
        'id': answer.id,
        'student_id': answer.student_id,
        'question_id': answer.question_id,
        'class_id': answer.class_id,
        'answer': answer.answer,
        'score': answer.correct_percentage,
        'answered_at': answer.answered_at.isoformat(),
        'is_modified': answer.modified_at is not None
    }

    if response_data['is_modified']:
        # 直接查询用户表获取修改者信息
        modifier = User.query.get(answer.modified_by)
        response_data.update({
            'modified_at': answer.modified_at.isoformat(),
            'modified_by': modifier.username if modifier else None
        })

    return jsonify(response_data), 200


#教师查询单个课程的所有题目学生作答情况
@studentanswer_bp.route('/course/<int:course_id>/answers', methods=['GET'])
def get_course_answers(course_id):
    # 验证登录状态
    if not is_logged_in():
        return jsonify({'error': '未登录'}), 401

    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': '用户不存在'}), 404

    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    if page < 1 or per_page < 1:
        return jsonify({'error': '无效的分页参数'}), 400

    # 获取学生ID参数
    student_id = request.args.get('student_id', type=int)

    try:
        # 验证课程是否存在
        course = Course.query.get(course_id)
        if not course:
            return jsonify({'error': '课程不存在'}), 404

        # 构建基础查询
        query = db.session.query(
            StudentAnswer,
            Question,
            User.username.label('student_name')
        ).join(
            Question, StudentAnswer.question_id == Question.id
        ).join(
            User, StudentAnswer.student_id == User.id
        ).filter(
            StudentAnswer.course_id == course_id
        )

        # 权限过滤
        if current_user.role == 'student':
            query = query.filter(StudentAnswer.student_id == current_user.id)
        elif current_user.role == 'teacher':
            # 验证是否是课程的老师
            if not is_teacher_of_course(course_id):
                return jsonify({'error': '无权限访问该课程数据'}), 403
        else:
            return jsonify({'error': '无效的用户角色'}), 403

        # 学生ID过滤（如果提供了学生ID）
        if student_id is not None:
            query = query.filter(StudentAnswer.student_id == student_id)

        # 执行分页查询
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        answers = pagination.items

        # 构建按题目分类的响应数据
        result = {}
        for answer, question, student_name in answers:
            question_id = question.id
            if question_id not in result:
                result[question_id] = {
                    'question_id': question_id,
                    'question_content': question.content,
                    'answers': [],
                    'average_score': 0  # 初始化平均正确率
                }

            answer_data = {
                'answer_id': answer.id,
                'student_id': answer.student_id,
                'student_name': student_name,
                'answer_content': answer.answer,
                'score': answer.correct_percentage,
                'answered_at': answer.answered_at.isoformat(),
                'is_modified': answer.modified_at is not None
            }
            if answer_data['is_modified']:
                modifier = User.query.get(answer.modified_by)
                answer_data.update({
                    'modified_at': answer.modified_at.isoformat(),
                    'modified_by': modifier.username if modifier else None
                })
            result[question_id]['answers'].append(answer_data)

        # 计算每个题目的平均正确率
        for question_id, question_data in result.items():
            scores = [answer['score'] for answer in question_data['answers']]
            if scores:
                question_data['average_score'] = sum(scores) / len(scores)

        # 将结果转换为列表
        result_list = list(result.values())

        return jsonify({
            'items': result_list,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }), 200

    except Exception as e:
        logger.error(f"查询失败: {str(e)}")
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500

#查询单个题目的所有学生作答记录
@studentanswer_bp.route('/question/<int:question_id>/answers', methods=['GET'])
def get_question_answers(question_id):
    # 验证登录状态
    if not is_logged_in():
        return jsonify({'error': '未登录'}), 401

    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': '用户不存在'}), 404

    try:
        # 验证题目是否存在
        question = Question.query.get(question_id)
        if not question:
            return jsonify({'error': '题目不存在'}), 404

        # 验证教师是否是该题目所属课程的老师
        if current_user.role == 'teacher' and not is_teacher_of_course(question.course_id):
            return jsonify({'error': '无权限访问该题目数据'}), 403

        # 构建基础查询
        query = db.session.query(
            StudentAnswer,
            User.username.label('student_name')
        ).join(
            User, StudentAnswer.student_id == User.id
        ).filter(
            StudentAnswer.question_id == question_id
        )

        # 执行查询
        answers = query.all()

        # 构建响应数据
        result = {
            'question_id': question_id,
            'question_content': question.content,
            'answers': []
        }

        total_score = 0
        for answer, student_name in answers:
            answer_data = {
                'answer_id': answer.id,
                'student_id': answer.student_id,
                'student_name': student_name,
                'answer_content': answer.answer,
                'score': answer.correct_percentage,
                'answered_at': answer.answered_at.isoformat(),
                'is_modified': answer.modified_at is not None
            }
            if answer_data['is_modified']:
                modifier = User.query.get(answer.modified_by)
                answer_data.update({
                    'modified_at': answer.modified_at.isoformat(),
                    'modified_by': modifier.username if modifier else None
                })
            result['answers'].append(answer_data)
            total_score += answer.correct_percentage

        if answers:
            result['average_score'] = total_score / len(answers)
        else:
            result['average_score'] = 0

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"查询失败: {str(e)}")
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500
    

#获取单个课程班的某一个学生的markdown形式课后习题答题记录分析报告
@studentanswer_bp.route('/getstudentanswerreport/<int:student_id>/<int:courseclass_id>', methods=['GET'])
def get_student_answerreport(student_id, courseclass_id):
    # 检查用户是否登录
    if not is_logged_in():
        return jsonify({'error': '未登录'}), 401

    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': '用户不存在'}), 404

    # 检查权限：学生本人或课程班的老师
    if not (current_user.id == student_id or is_teacher_of_courseclass(courseclass_id)):
        return jsonify({'error': '无权查看此报告'}), 403

    try:
        # 获取当前的数据库会话
        session = db.session

        # 检查是否存在报告
        report = session.query(StudentAnalysisReport).filter_by(student_id=student_id, courseclass_id=courseclass_id).first()
        if report:
            return jsonify({'markdown_report': report.report_content}), 200
        else:
            # 如果报告不存在，返回 null
            return jsonify({'markdown_report': None}), 200

    except Exception as e:
        # 如果发生错误，返回错误信息
        return jsonify({"error": str(e)}), 500

#获取单个教学班的答题分析报告
@studentanswer_bp.route('/getclassanswerreport/<int:courseclass_id>', methods=['GET'])
def get_class_answerreport(courseclass_id):
    # 检查用户是否登录
    if not is_logged_in():
        return jsonify({'error': '未登录'}), 401

    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': '用户不存在'}), 404

    # 检查权限：课程班的老师
    if not is_teacher_of_courseclass(courseclass_id):
        return jsonify({'error': '无权查看此报告'}), 403

    try:
        # 获取当前的数据库会话
        session = db.session

        # 检查是否存在报告
        report = session.query(ClassAnalysisReport).filter_by(courseclass_id=courseclass_id).first()
        if report:
            return jsonify({'markdown_report': report.report_content}), 200
        else:
            # 如果报告不存在，返回 null
            return jsonify({'markdown_report': None}), 200

    except Exception as e:
        # 如果发生错误，返回错误信息
        return jsonify({"error": str(e)}), 500
    
#获取单个课程的答题分析报告
@studentanswer_bp.route('/getcourseanswersreport/<int:course_id>', methods=['GET'])
def get_course_answersreport(course_id):
    # 检查用户是否登录
    if not is_logged_in():
        return jsonify({'error': '未登录'}), 401

    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': '用户不存在'}), 404

    # 检查权限：课程的老师
    if not is_teacher_of_course(course_id):
        return jsonify({'error': '无权查看此报告'}), 403

    try:
        # 获取当前的数据库会话
        session = db.session

        # 检查是否存在报告
        report = session.query(ClassAnalysisReport).filter_by(course_id=course_id).first()
        if report:
            return jsonify({'markdown_report': report.report_content}), 200
        else:
            # 如果报告不存在，返回 null
            return jsonify({'markdown_report': None}), 200

    except Exception as e:
        # 如果发生错误，返回错误信息
        return jsonify({"error": str(e)}), 500

#获取单个学生的有关单个课程的答题分析报告
@studentanswer_bp.route('/getstudentincourseanswerreport/<int:student_id>/<int:course_id>', methods=['GET'])
def get_student_in_course_answerreport(student_id, course_id):
    if not is_logged_in():
        return jsonify({'error': '未登录'}), 401

    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': '用户不存在'}), 404

    if not (current_user.id == student_id or is_teacher_of_course(course_id)):
        return jsonify({'error': '无权查看此报告'}), 403

    try:
        session = db.session

        # 检查是否存在报告
        report = session.query(StudentAnalysisReport).filter_by(student_id=student_id, course_id=course_id).first()
        if report:
            return jsonify({'markdown_report': report.report_content}), 200
        else:
            # 如果报告不存在，返回 null
            return jsonify({'markdown_report': None}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

#更新单个课程班的某一个学生的 Markdown 形式课后习题答题记录分析报告
@studentanswer_bp.route('/updatestudentanswerreport/<int:student_id>/<int:courseclass_id>', methods=['POST'])
def update_student_answerreport(student_id, courseclass_id):
    # 检查用户是否登录
    if not is_logged_in():
        return jsonify({'error': '未登录'}), 401

    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': '用户不存在'}), 404

    # 检查权限：学生本人或课程班的老师
    if not (current_user.id == student_id or is_teacher_of_courseclass(courseclass_id)):
        return jsonify({'error': '无权查看此报告'}), 403

    try:
        # 获取当前的数据库会话
        session = db.session

        # 获取学生的答题记录及其相关题目和课程信息
        answers = get_student_answers_with_question_and_course_details(session=session, student_id=student_id, class_id=courseclass_id)

        # 生成报告内容
        content = generate_study_report(answers)

        # 检查是否存在报告
        report = session.query(StudentAnalysisReport).filter_by(student_id=student_id, courseclass_id=courseclass_id).first()
        if report:
            # 如果报告存在，更新报告内容
            report.report_content = content
        else:
            # 如果报告不存在，生成新的报告
            report = StudentAnalysisReport(
                student_id=student_id,
                courseclass_id=courseclass_id,
                report_content=content
            )
            session.add(report)

        # 提交更改
        session.commit()

        # 返回 Markdown 内容
        return jsonify({'markdown_report': content}), 200

    except Exception as e:
        # 如果发生错误，回滚数据库会话并返回错误信息
        session.rollback()
        return jsonify({"error": str(e)}), 500


#更新单个教学班的答题分析报告
@studentanswer_bp.route('/updateclassanswerreport/<int:courseclass_id>', methods=['POST'])
def update_class_answerreport(courseclass_id):
    # 检查用户是否登录
    if not is_logged_in():
        return jsonify({'error': '未登录'}), 401

    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': '用户不存在'}), 404

    # 检查权限：课程班的老师
    if not is_teacher_of_courseclass(courseclass_id):
        return jsonify({'error': '无权查看此报告'}), 403

    try:
        # 获取当前的数据库会话
        session = db.session

        # 检查是否存在报告
        report = session.query(ClassAnalysisReport).filter_by(courseclass_id=courseclass_id).first()
        if report:
            # 如果报告存在，更新报告内容
            answers = get_class_student_answers(session=session, class_id=courseclass_id)
            content = generate_study_report_overall(answers)
            report.report_content = content
        else:
            # 如果报告不存在，生成新的报告
            answers = get_class_student_answers(session=session, class_id=courseclass_id)
            content = generate_study_report_overall(answers)
            report = ClassAnalysisReport(
                courseclass_id=courseclass_id,
                report_content=content
            )
            session.add(report)

        # 提交更改
        session.commit()

        # 返回 Markdown 内容
        return jsonify({'markdown_report': content}), 200

    except Exception as e:
        # 如果发生错误，回滚数据库会话并返回错误信息
        session.rollback()
        return jsonify({"error": str(e)}), 500
    
#更新单个课程的答题分析报告
@studentanswer_bp.route('/updatecourseanswersreport/<int:course_id>', methods=['POST'])
def update_course_answersreport(course_id):
    # 检查用户是否登录
    if not is_logged_in():
        return jsonify({'error': '未登录'}), 401

    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': '用户不存在'}), 404

    # 检查权限：课程的老师
    if not is_teacher_of_course(course_id):
        return jsonify({'error': '无权查看此报告'}), 403

    try:
        # 获取当前的数据库会话
        session = db.session

        # 检查是否存在报告
        report = session.query(ClassAnalysisReport).filter_by(course_id=course_id).first()
        if report:
            # 如果报告存在，更新报告内容
            answers = get_course_student_answers(session=session, course_id=course_id)
            content = generate_study_report_overall(answers)
            report.report_content = content
        else:
            # 如果报告不存在，生成新的报告
            answers = get_course_student_answers(session=session, course_id=course_id)
            content = generate_study_report_overall(answers)
            report = ClassAnalysisReport(
                course_id=course_id,
                report_content=content
            )
            session.add(report)

        # 提交更改
        session.commit()

        # 返回 Markdown 内容
        return jsonify({'markdown_report': content}), 200

    except Exception as e:
        # 如果发生错误，回滚数据库会话并返回错误信息
        session.rollback()
        return jsonify({"error": str(e)}), 500
    
#更新单个学生的有关单个课程的答题分析报告
@studentanswer_bp.route('/updatestudentincourseanswerreport/<int:student_id>/<int:course_id>', methods=['POST'])
def update_student_in_course_answerreport(student_id, course_id):
    # 检查用户是否登录
    if not is_logged_in():
        return jsonify({'error': '未登录'}), 401

    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': '用户不存在'}), 404

    # 检查权限：学生本人或课程的老师
    if not (current_user.id == student_id or is_teacher_of_course(course_id)):
        return jsonify({'error': '无权查看此报告'}), 403

    try:
        # 获取当前的数据库会话
        session = db.session

        # 检查是否存在报告
        report = session.query(StudentAnalysisReport).filter_by(student_id=student_id, course_id=course_id).first()
        if report:
            # 如果报告存在，更新报告内容
            answers = get_student_answers_in_course(session=session, student_id=student_id, course_id=course_id)
            content = generate_study_report(answers)
            report.report_content = content
        else:
            # 如果报告不存在，生成新的报告
            answers = get_student_answers_in_course(session=session, student_id=student_id, course_id=course_id)
            content = generate_study_report(answers)
            report = StudentAnalysisReport(
                student_id=student_id,
                course_id=course_id,
                report_content=content
            )
            session.add(report)

        # 提交更改
        session.commit()

        # 返回 Markdown 内容
        return jsonify({'markdown_report': content}), 200

    except Exception as e:
        # 如果发生错误，回滚数据库会话并返回错误信息
        session.rollback()
        return jsonify({"error": str(e)}), 500