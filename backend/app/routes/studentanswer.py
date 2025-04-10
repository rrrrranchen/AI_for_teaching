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
from app.routes.teachingdesign import get_question_type_name, is_teacher_of_course
from app.services.analysis_report import generate_study_report, generate_study_report_overall
from app.models.studentanalysisreport import StudentAnalysisReport
from app.models.classanalysisreport import ClassAnalysisReport

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

def get_post_class_questions_as_feedback(course_id):
    """
    提取指定课程的课后习题及学生答题情况，作为反馈信息
    :param course_id: 课程ID
    :return: 格式化后的学生反馈字符串，包含题目和答题情况
    """
    # 查询该课程的所有课后习题及相关学生答案（单次查询优化）
    post_class_questions = (Question.query
                            .filter_by(course_id=course_id, timing='post_class', is_public=True)
                            .options(db.joinedload(Question.answers))
                            .all())

    if not post_class_questions:
        return "该课程暂无课后习题"

    feedback_lines = ["课后习题及学生答题情况汇总:"]
    all_answers = []
    question_stats = []

    for question in post_class_questions:
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
        total_questions = len(post_class_questions)
        total_attempts = len(all_answers)
        overall_avg = sum(a.correct_percentage for a in all_answers) / total_attempts

        feedback_lines.append("\n总体统计:")
        feedback_lines.append(f"- 课后习题数量: {total_questions}题")
        feedback_lines.append(f"- 学生答题人次: {total_attempts}次")
        feedback_lines.append(f"- 平均正确率: {overall_avg:.1f}%")

        # 找出最难和最易的题目
        if len(question_stats) > 1:
            hardest = min(question_stats, key=lambda x: x['avg_correct'])
            easiest = max(question_stats, key=lambda x: x['avg_correct'])
            
            feedback_lines.append(f"- 最难题目: 题目ID {hardest['question'].id} (平均正确率: {hardest['avg_correct']:.1f}%)")
            feedback_lines.append(f"- 最易题目: 题目ID {easiest['question'].id} (平均正确率: {easiest['avg_correct']:.1f}%)")

    return "\n".join(feedback_lines)

def get_course_student_answers(session: Session, course_id: int) -> List[Dict]:
    """
    获取单个课程中所有学生的答题记录，并提取对应的题目内容、正确答案以及学生信息

    :param session: SQLAlchemy 的数据库会话
    :param course_id: 课程的 ID
    :return: 包含答题记录及其对应题目内容、正确答案和学生信息的字典列表
    """
    # 查询指定课程中所有学生的答题记录，并关联题目表、学生表和课程表获取题目内容、正确答案、学生信息和课程名称
    student_answers = (
        session.query(
            StudentAnswer.id,
            StudentAnswer.student_id,
            StudentAnswer.question_id,
            StudentAnswer.class_id,
            StudentAnswer.answer,
            StudentAnswer.correct_percentage,
            StudentAnswer.answered_at,
            StudentAnswer.modified_by,
            StudentAnswer.modified_at,
            Question.content.label("question_content"),
            Question.correct_answer,
            User.username.label("student_username"),  # 添加学生用户名字段
            Course.name.label("course_name")  # 添加课程名称字段
        )
        .join(Question, StudentAnswer.question_id == Question.id)
        .join(User, StudentAnswer.student_id == User.id)  # 关联学生表
        .join(Course, Question.course_id == Course.id)  # 关联课程表
        .filter(Question.course_id == course_id)  # 仅选择指定课程的答题记录
        .filter(Question.timing == 'post_class')  # 仅选择课后习题
        .all()
    )

    # 初始化一个列表，用于存储处理后的数据
    processed_answers = []

    # 遍历每个答题记录，提取关键信息并封装为字典
    for answer in student_answers:
        processed_answer = {
            "id": answer.id,  # 答题记录的 ID
            "student_id": answer.student_id,  # 学生的 ID
            "question_id": answer.question_id,  # 对应的题目 ID
            "class_id": answer.class_id,  # 对应的课程班级 ID
            "answer": answer.answer,  # 学生的答案
            "correct_percentage": answer.correct_percentage,  # 答题正确率
            "answered_at": answer.answered_at,  # 答题时间
            "modified_by": answer.modified_by,  # 修改人
            "modified_at": answer.modified_at,  # 修改时间
            "question_content": answer.question_content,  # 题目内容
            "correct_answer": answer.correct_answer,  # 正确答案
            "student_username": answer.student_username,  # 学生用户名
            "course_name": answer.course_name  # 课程名称
        }
        processed_answers.append(processed_answer)

    return processed_answers

def get_class_student_answers(session: Session, class_id: int) -> List[Dict]:
    """
    获取单个课程班中所有学生的答题记录，并提取对应的题目内容、正确答案以及学生信息

    :param session: SQLAlchemy 的数据库会话
    :param class_id: 课程班的 ID
    :return: 包含答题记录及其对应题目内容、正确答案和学生信息的字典列表
    """
    # 查询指定课程班中所有学生的答题记录，并关联题目表、学生表和课程表获取题目内容、正确答案、学生信息和课程名称
    student_answers = (
        session.query(
            StudentAnswer.id,
            StudentAnswer.student_id,
            StudentAnswer.question_id,
            StudentAnswer.class_id,
            StudentAnswer.answer,
            StudentAnswer.correct_percentage,
            StudentAnswer.answered_at,
            StudentAnswer.modified_by,
            StudentAnswer.modified_at,
            Question.content.label("question_content"),
            Question.correct_answer,
            User.username.label("student_username"),  # 添加学生用户名字段
            Course.name.label("course_name")  # 添加课程名称字段
        )
        .join(Question, StudentAnswer.question_id == Question.id)
        .join(User, StudentAnswer.student_id == User.id)  # 关联学生表
        .join(Course, Question.course_id == Course.id)  # 关联课程表
        .filter(StudentAnswer.class_id == class_id)  # 仅选择指定课程班的答题记录
        .filter(Question.timing == 'post_class')  # 仅选择课后习题
        .all()
    )

    # 初始化一个列表，用于存储处理后的数据
    processed_answers = []

    # 遍历每个答题记录，提取关键信息并封装为字典
    for answer in student_answers:
        processed_answer = {
            "id": answer.id,  # 答题记录的 ID
            "student_id": answer.student_id,  # 学生的 ID
            "question_id": answer.question_id,  # 对应的题目 ID
            "class_id": answer.class_id,  # 对应的课程班级 ID
            "answer": answer.answer,  # 学生的答案
            "correct_percentage": answer.correct_percentage,  # 答题正确率
            "answered_at": answer.answered_at,  # 答题时间
            "modified_by": answer.modified_by,  # 修改人
            "modified_at": answer.modified_at,  # 修改时间
            "question_content": answer.question_content,  # 题目内容
            "correct_answer": answer.correct_answer,  # 正确答案
            "student_username": answer.student_username,  # 学生用户名
            "course_name": answer.course_name  # 课程名称
        }
        processed_answers.append(processed_answer)

    return processed_answers

def get_student_answers_in_course(session: Session, student_id: int, course_id: int) -> List[Dict]:
    """
    获取单个学生在指定课程中的答题记录，并提取对应的题目内容、正确答案以及课程名称

    :param session: SQLAlchemy 的数据库会话
    :param student_id: 学生的 ID
    :param course_id: 课程的 ID
    :return: 包含答题记录及其对应题目内容、正确答案和课程名称的字典列表
    """
    # 查询指定学生在指定课程中的答题记录，并关联题目表和课程表获取题目内容、正确答案和课程名称
    student_answers = (
        session.query(
            StudentAnswer.id,
            StudentAnswer.question_id,
            StudentAnswer.class_id,
            StudentAnswer.answer,
            StudentAnswer.correct_percentage,
            StudentAnswer.answered_at,
            StudentAnswer.modified_by,
            StudentAnswer.modified_at,
            Question.content.label("question_content"),
            Question.correct_answer,
            Course.name.label("course_name")  # 添加课程名称字段
        )
        .join(Question, StudentAnswer.question_id == Question.id)
        .join(Course, Question.course_id == Course.id)  # 关联课程表
        .filter(StudentAnswer.student_id == student_id)
        .filter(Question.course_id == course_id)  # 仅选择指定课程的答题记录
        .filter(Question.timing == 'post_class')  # 仅选择课后习题
        .all()
    )

    # 初始化一个列表，用于存储处理后的数据
    processed_answers = []

    # 遍历每个答题记录，提取关键信息并封装为字典
    for answer in student_answers:
        processed_answer = {
            "id": answer.id,  # 答题记录的 ID
            "question_id": answer.question_id,  # 对应的题目 ID
            "class_id": answer.class_id,  # 对应的课程班级 ID
            "answer": answer.answer,  # 学生的答案
            "correct_percentage": answer.correct_percentage,  # 答题正确率
            "answered_at": answer.answered_at,  # 答题时间
            "modified_by": answer.modified_by,  # 修改人
            "modified_at": answer.modified_at,  # 修改时间
            "question_content": answer.question_content,  # 题目内容
            "correct_answer": answer.correct_answer,  # 正确答案
            "course_name": answer.course_name  # 课程名称
        }
        processed_answers.append(processed_answer)

    return processed_answers

def get_student_answers_with_question_and_course_details(session: Session, student_id: int, class_id: int) -> List[Dict]:
    """
    获取单个学生在指定课程班中的答题记录，并提取对应的题目内容、正确答案以及课程名称

    :param session: SQLAlchemy 的数据库会话
    :param student_id: 学生的 ID
    :param class_id: 课程班的 ID
    :return: 包含答题记录及其对应题目内容、正确答案和课程名称的字典列表
    """
    # 查询指定学生的答题记录，并关联题目表和课程表获取题目内容、正确答案和课程名称
    student_answers = (
        session.query(
            StudentAnswer.id,
            StudentAnswer.question_id,
            StudentAnswer.class_id,
            StudentAnswer.answer,
            StudentAnswer.correct_percentage,
            StudentAnswer.answered_at,
            StudentAnswer.modified_by,
            StudentAnswer.modified_at,
            Question.content.label("question_content"),
            Question.correct_answer,
            Course.name.label("course_name")  # 添加课程名称字段
        )
        .join(Question, StudentAnswer.question_id == Question.id)
        .join(Course, Question.course_id == Course.id)  # 关联课程表
        .filter(StudentAnswer.student_id == student_id)
        .filter(StudentAnswer.class_id == class_id)  # 仅选择指定课程班的答题记录
        .filter(Question.timing == 'post_class')  # 仅选择课后习题
        .all()
    )

    # 初始化一个列表，用于存储处理后的数据
    processed_answers = []

    # 遍历每个答题记录，提取关键信息并封装为字典
    for answer in student_answers:
        processed_answer = {
            "id": answer.id,  # 答题记录的 ID
            "question_id": answer.question_id,  # 对应的题目 ID
            "class_id": answer.class_id,  # 对应的课程班级 ID
            "answer": answer.answer,  # 学生的答案
            "correct_percentage": answer.correct_percentage,  # 答题正确率
            "question_content": answer.question_content,  # 题目内容
            "correct_answer": answer.correct_answer,  # 正确答案
            "course_name": answer.course_name  # 课程名称
        }
        processed_answers.append(processed_answer)

    return processed_answers

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
    if not data:
        return jsonify({'error': '缺少数据'}), 400

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
            else:
                new_answer = StudentAnswer(
                    student_id=current_user.id,
                    question_id=question_id,
                    course_id=question.course_id,
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

        # 如果没有报告，生成报告
        answers = get_student_answers_with_question_and_course_details(session=session, student_id=student_id, class_id=courseclass_id)
        content = generate_study_report(answers)

        # 创建一个新的 StudentAnalysisReport 实例
        report = StudentAnalysisReport(
            student_id=student_id,
            courseclass_id=courseclass_id,
            report_content=content
        )

        # 将报告保存到数据库
        session.add(report)
        session.commit()

        # 返回 Markdown 内容
        return jsonify({'markdown_report': content}), 200

    except Exception as e:
        # 如果发生错误，回滚数据库会话并返回错误信息
        session.rollback()
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

        # 如果没有报告，生成报告
        answers = get_class_student_answers(session=session, class_id=courseclass_id)
        content = generate_study_report_overall(answers)

        # 创建一个新的 ClassAnalysisReport 实例
        report = ClassAnalysisReport(
            courseclass_id=courseclass_id,
            report_content=content
        )

        # 将报告保存到数据库
        session.add(report)
        session.commit()

        # 返回 Markdown 内容
        return jsonify({'markdown_report': content}), 200

    except Exception as e:
        # 如果发生错误，回滚数据库会话并返回错误信息
        session.rollback()
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

        # 如果没有报告，生成报告
        answers = get_course_student_answers(session=session, course_id=course_id)
        content = generate_study_report_overall(answers)

        # 创建一个新的 ClassAnalysisReport 实例
        report = ClassAnalysisReport(
            course_id=course_id,
            report_content=content
        )

        # 将报告保存到数据库
        session.add(report)
        session.commit()

        # 返回 Markdown 内容
        return jsonify({'markdown_report': content}), 200

    except Exception as e:
        # 如果发生错误，回滚数据库会话并返回错误信息
        session.rollback()
        return jsonify({"error": str(e)}), 500

#获取单个学生的有关单个课程的答题分析报告
@studentanswer_bp.route('/getstudentincourseanswerreport/<int:student_id>/<int:course_id>', methods=['GET'])
def get_student_in_course_answerreport(student_id, course_id):
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
            return jsonify({'markdown_report': report.report_content}), 200

        # 如果没有报告，生成报告
        answers = get_student_answers_in_course(session=session, student_id=student_id, course_id=course_id)
        content = generate_study_report(answers)

        # 创建一个新的 StudentAnalysisReport 实例
        report = StudentAnalysisReport(
            student_id=student_id,
            course_id=course_id,
            report_content=content
        )

        # 将报告保存到数据库
        session.add(report)
        session.commit()

        # 返回 Markdown 内容
        return jsonify({'markdown_report': content}), 200

    except Exception as e:
        # 如果发生错误，回滚数据库会话并返回错误信息
        session.rollback()
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

        # 检查是否存在报告
        report = session.query(StudentAnalysisReport).filter_by(student_id=student_id, courseclass_id=courseclass_id).first()
        if report:
            # 如果报告存在，更新报告内容
            answers = get_student_answers_with_question_and_course_details(session=session, student_id=student_id, class_id=courseclass_id)
            content = generate_study_report(answers)
            report.report_content = content
        else:
            # 如果报告不存在，生成新的报告
            answers = get_student_answers_with_question_and_course_details(session=session, student_id=student_id, class_id=courseclass_id)
            content = generate_study_report(answers)
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