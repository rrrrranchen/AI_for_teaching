from typing import List, Dict
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.question import Question
from app.models.studentanswer import StudentAnswer




def get_student_answers_with_question_and_course_details(session: Session, student_id: int) -> List[Dict]:
    """
    获取单个学生的答题记录，并提取对应的题目内容、正确答案以及课程名称（仅限课后习题）

    :param session: SQLAlchemy 的数据库会话
    :param student_id: 学生的 ID
    :return: 包含答题记录及其对应题目内容、正确答案和课程名称的字典列表
    """
    # 查询指定学生的答题记录，并关联题目表和课程表获取题目内容、正确答案和课程名称
    # 仅选择课后习题（timing == 'post_class'）
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
            "answered_at": answer.answered_at.strftime("%Y-%m-%d %H:%M:%S"),  # 答题时间，格式化为字符串
            "modified_by": answer.modified_by,  # 修改人 ID（如果有）
            "modified_at": answer.modified_at.strftime("%Y-%m-%d %H:%M:%S") if answer.modified_at else None,  # 修改时间
            "question_content": answer.question_content,  # 题目内容
            "correct_answer": answer.correct_answer,  # 正确答案
            "course_name": answer.course_name  # 课程名称
        }
        processed_answers.append(processed_answer)

    return processed_answers

