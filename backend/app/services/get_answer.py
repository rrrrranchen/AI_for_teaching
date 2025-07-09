from app.utils.database import db
from typing import Dict, List
from requests import Session
from app.models.course import Course
from app.models.question import Question
from app.models.studentanswer import StudentAnswer
from app.models.user import User
from app.routes.teaching_design import get_question_type_name



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
            "answered_at": answer.answered_at.isoformat() if answer.answered_at else None,  # 将 datetime 转换为 ISO 8601 格式的字符串
            "modified_by": answer.modified_by,  # 修改人
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
    print(processed_answers)
    return processed_answers