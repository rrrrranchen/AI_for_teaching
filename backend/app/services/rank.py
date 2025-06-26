from datetime import datetime, timedelta
from app.utils.database import db
from sqlalchemy import distinct, func
from app.models.courseclass import Courseclass
from app.models.question import Question
from app.models.studentanswer import StudentAnswer
from app.models.relationship import course_courseclass,student_class,teacher_class
from app.models.course import Course

def generate_class_recommend_ranking(class_id):
    """
    生成课程班学生推荐排行榜（增强版）
    增加了进步指标、难度加权、努力程度等因素
    
    参数:
        class_id: 课程班ID
    返回:
        按综合评分排序的学生排行榜列表，包含学生信息和评分数据
    """
    # 获取课程班信息
    courseclass = Courseclass.query.get(class_id)
    if not courseclass:
        return {"error": "Course class not found"}, 404
    
    # 获取课程班关联的所有课程
    courses = courseclass.courses
    course_ids = [course.id for course in courses]
    
    # 获取课程班所有学生
    students = courseclass.students
    
    # 收集所有相关题目ID及其难度
    questions = Question.query.filter(Question.course_id.in_(course_ids)).all()
    question_difficulty = {q.id: q.difficulty or 1 for q in questions}
    total_questions = len(questions)
    
    # 如果没有题目，直接返回空列表
    if total_questions == 0:
        return []
    
    # 时间范围定义
    now = datetime.utcnow()
    one_week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)
    
    # 计算每个学生的答题情况
    student_stats = []
    
    for student in students:
        # 获取学生在课程班的所有答题记录
        answers = StudentAnswer.query.filter_by(
            class_id=class_id,
            student_id=student.id
        ).all()
        
        if not answers:
            # 没有答题记录的学生
            student_stats.append({
                "student_id": student.id,
                "student_name": student.username,
                "completion_rate": 0,
                "weighted_accuracy": 0,
                "progress": 0,
                "effort": 0,
                "latest_activity": None,
                "composite_score": 0
            })
            continue
        
        # 按题目分组，只取每个题目的最新作答
        latest_answers = {}
        for answer in answers:
            if (answer.question_id not in latest_answers or 
                answer.answered_at > latest_answers[answer.question_id].answered_at):
                latest_answers[answer.question_id] = answer
        
        # 计算作答率（完成率）
        answered_questions = set(latest_answers.keys())
        completion_rate = len(answered_questions) / total_questions
        
        # 计算难度加权的平均正确率
        total_weighted_correctness = 0
        total_difficulty = 0
        
        # 分时间段统计正确率（用于计算进步）
        recent_correctness = []  # 最近一周
        older_correctness = []   # 1-2周前
        
        for qid, answer in latest_answers.items():
            difficulty = question_difficulty.get(qid, 1)
            correctness = answer.correct_percentage
            
            # 难度加权计算
            total_weighted_correctness += correctness * difficulty
            total_difficulty += difficulty
            
            # 时间分段统计
            if answer.answered_at > one_week_ago:
                recent_correctness.append((correctness, difficulty))
            elif answer.answered_at > two_weeks_ago:
                older_correctness.append((correctness, difficulty))
        
        # 计算加权平均正确率
        if total_difficulty > 0:
            weighted_accuracy = total_weighted_correctness / total_difficulty
        else:
            weighted_accuracy = 0
        
        # 计算进步指标
        recent_avg = (sum(c * d for c, d in recent_correctness) / 
                      sum(d for c, d in recent_correctness)) if recent_correctness else 0
        older_avg = (sum(c * d for c, d in older_correctness) / 
                     sum(d for c, d in older_correctness)) if older_correctness else 0
        
        # 避免除零错误
        progress = 0
        if older_avg > 0:
            progress = (recent_avg - older_avg) / older_avg * 100  # 百分比进步
        elif recent_avg > 0:
            progress = 100  # 从零基础到有成绩
        
        # 计算努力程度（答题次数/题目数）
        effort = min(1.0, len(answers) / total_questions * 2)  # 努力程度上限为100%
        
        # 计算活跃度（最近答题时间）
        latest_activity = max(answer.answered_at for answer in latest_answers.values())
        activity_days = (now - latest_activity).days
        activity_factor = max(0, 1 - min(1, activity_days / 14))  # 两周内活跃度满分
        
        # ====== 综合评分 ======
        # 权重分配：
        # - 完成率: 20%
        # - 加权正确率: 30%
        # - 进步指标: 25%
        # - 努力程度: 15%
        # - 活跃度: 10%
        composite_score = (
            0.20 * completion_rate +
            0.30 * (weighted_accuracy / 100) +
            0.25 * min(1.0, max(0, progress / 100)) +  # 进步指标归一化到0-1
            0.15 * effort +
            0.10 * activity_factor
        )
        
        student_stats.append({
            "student_id": student.id,
            "student_name": student.username,
            "completion_rate": completion_rate,
            "weighted_accuracy": weighted_accuracy,
            "progress": progress,
            "effort": effort,
            "latest_activity": latest_activity,
            "composite_score": composite_score
        })
    
    # 按综合评分排序
    ranked_students = sorted(
        student_stats, 
        key=lambda x: x["composite_score"], 
        reverse=True
    )
    
    # 添加排名信息
    for i, student in enumerate(ranked_students):
        student["rank"] = i + 1
    
    return ranked_students


def generate_public_courseclass_ranking():
    """
    生成公开课程班推荐指数排行榜
    综合考虑课程班质量、活跃度、教学资源等因素
    返回:
        按推荐指数排序的公开课程班排行榜
    """
    # 获取所有公开课程班
    public_classes = Courseclass.query.filter_by(is_public=True).all()
    
    # 如果没有公开课程班，返回空列表
    if not public_classes:
        return []
    
    class_ids = [c.id for c in public_classes]
    
    # 预计算基础指标
    # 1. 学生数量
    student_counts = (
        db.session.query(
            Courseclass.id,
            func.count(distinct(student_class.c.student_id)).label('student_count')
        )
        .join(student_class, Courseclass.id == student_class.c.courseclass_id)
        .group_by(Courseclass.id)
        .filter(Courseclass.id.in_(class_ids))
        .all()
    )
    student_count_dict = {c.id: c.student_count for c in student_counts}

    # 2. 教师数量
    teacher_counts = (
        db.session.query(
            Courseclass.id,
            func.count(distinct(teacher_class.c.teacher_id)).label('teacher_count')
        )
        .join(teacher_class, Courseclass.id == teacher_class.c.courseclass_id)
        .group_by(Courseclass.id)
        .filter(Courseclass.id.in_(class_ids))
        .all()
    )
    teacher_count_dict = {c.id: c.teacher_count for c in teacher_counts}

    # 3. 课程数量
    course_counts = (
        db.session.query(
            Courseclass.id,
            func.count(distinct(course_courseclass.c.course_id)).label('course_count')
        )
        .join(course_courseclass, Courseclass.id == course_courseclass.c.courseclass_id)
        .group_by(Courseclass.id)
        .filter(Courseclass.id.in_(class_ids))
        .all()
    )
    course_count_dict = {c.id: c.course_count for c in course_counts}
    
    # 4. 题目数量
    question_counts = (
    db.session.query(
        Courseclass.id,
        func.count(distinct(Question.id)).label('question_count')
    )
    .join(course_courseclass, Courseclass.id == course_courseclass.c.courseclass_id)
    .join(Course, course_courseclass.c.course_id == Course.id)
    .join(Question, Course.id == Question.course_id)
    .group_by(Courseclass.id)
    .filter(Courseclass.id.in_(class_ids))
    .all()
    )
    question_count_dict = {c.id: c.question_count for c in question_counts}
    
    # 5. 最近活跃度（过去7天答题数量）
    one_week_ago = datetime.utcnow() - timedelta(days=7)
    recent_activity = db.session.query(
        StudentAnswer.class_id,
        func.count(StudentAnswer.id).label('recent_answers')
    ).filter(
        StudentAnswer.class_id.in_(class_ids),
        StudentAnswer.answered_at >= one_week_ago
    ).group_by(StudentAnswer.class_id).all()
    activity_dict = {r.class_id: r.recent_answers for r in recent_activity}
    
    # 6. 平均正确率（所有学生的最新答题记录）
    # 使用子查询获取每个学生每个题目的最新答题记录
    latest_answers_subq = db.session.query(
        StudentAnswer.student_id,
        StudentAnswer.question_id,
        func.max(StudentAnswer.answered_at).label('latest_time')
    ).filter(
        StudentAnswer.class_id.in_(class_ids)
    ).group_by(
        StudentAnswer.student_id,
        StudentAnswer.question_id
    ).subquery()
    
    # 计算平均正确率
    avg_accuracy = db.session.query(
        StudentAnswer.class_id,
        func.avg(StudentAnswer.correct_percentage).label('avg_accuracy')
    ).join(
        latest_answers_subq,
        (StudentAnswer.student_id == latest_answers_subq.c.student_id) &
        (StudentAnswer.question_id == latest_answers_subq.c.question_id) &
        (StudentAnswer.answered_at == latest_answers_subq.c.latest_time)
    ).group_by(StudentAnswer.class_id).all()
    accuracy_dict = {a.class_id: a.avg_accuracy for a in avg_accuracy}
    
    # 7. 教学资源丰富度（图片、描述等）
    resource_score = db.session.query(
        Courseclass.id,
        func.coalesce(func.length(Courseclass.description), 0).label('desc_length'),
        func.case(
            (Courseclass.image_path.isnot(None), 1),
            else_=0
        ).label('has_image')
    ).filter(Courseclass.id.in_(class_ids)).all()
    resource_dict = {}
    for r in resource_score:
        # 描述长度(0-1) + 是否有图片(0或1) = 总分(0-2)
        resource_dict[r.id] = min(1, r.desc_length / 500) + r.has_image
    
    # 计算每个课程班的推荐指数
    class_rankings = []
    
    for courseclass in public_classes:
        cid = courseclass.id
        
        # 获取指标值（如果缺失则设为0）
        student_count = student_count_dict.get(cid, 0)
        teacher_count = teacher_count_dict.get(cid, 0)
        course_count = course_count_dict.get(cid, 0)
        question_count = question_count_dict.get(cid, 0)
        recent_activity = activity_dict.get(cid, 0)
        avg_accuracy = accuracy_dict.get(cid, 0)
        resource_score = resource_dict.get(cid, 0)
        
        # 活跃学生比例（最近一周有答题的学生比例）
        active_students = db.session.query(
            func.count(distinct(StudentAnswer.student_id))
        ).filter(
            StudentAnswer.class_id == cid,
            StudentAnswer.answered_at >= one_week_ago
        ).scalar() or 0
        student_count_val = student_count or 1  # 避免除零
        activity_ratio = active_students / student_count_val
        
        # ====== 计算推荐指数 ======
        # 权重分配：
        # - 学生规模: 15% (log10缩放)
        # - 师生比: 10% (教师/学生)
        # - 课程资源: 20% (课程+题目数量)
        # - 活跃度: 20% (活跃学生比例+近期答题数)
        # - 学习效果: 25% (平均正确率)
        # - 教学资源: 10% (描述、图片等)
        
        # 1. 学生规模指标（使用对数缩放）
        size_score = min(1.0, (student_count ** 0.5) / 10)
        
        # 2. 师生比指标
        teacher_ratio = min(1.0, teacher_count / (student_count_val / 20))  # 1:20为基准
        
        # 3. 课程资源指标
        resource_quantity = min(1.0, (course_count + question_count / 10) / 10)
        
        # 4. 活跃度指标
        activity_score = min(1.0, activity_ratio * 0.7 + min(1.0, recent_activity / 100) * 0.3)
        
        # 5. 学习效果指标
        learning_score = avg_accuracy / 100  # 正确率转为0-1
        
        # 6. 教学资源丰富度
        teaching_resource = resource_score / 2  # 归一化到0-1
        
        # 计算综合推荐指数
        recommend_index = (
            0.15 * size_score +
            0.10 * teacher_ratio +
            0.20 * resource_quantity +
            0.20 * activity_score +
            0.25 * learning_score +
            0.10 * teaching_resource
        )
        
        # 收集课程班信息
        class_rankings.append({
            "class_id": cid,
            "class_name": courseclass.name,
            "invite_code": courseclass.invite_code,
            "image_path": courseclass.image_path,
            "description": courseclass.description[:100] + "..." if courseclass.description else "",
            "student_count": student_count,
            "teacher_count": teacher_count,
            "course_count": course_count,
            "question_count": question_count,
            "avg_accuracy": avg_accuracy,
            "activity_ratio": activity_ratio * 100,  # 转为百分比
            "recommend_index": recommend_index * 100  # 转为0-100分
        })
    
    # 按推荐指数排序
    sorted_classes = sorted(
        class_rankings, 
        key=lambda x: x["recommend_index"], 
        reverse=True
    )
    
    # 添加星级评价（1-5星）
    max_index = max(c["recommend_index"] for c in sorted_classes) or 100
    for c in sorted_classes:
        # 计算星级（0-5）
        stars = round(c["recommend_index"] / max_index * 5, 1)
        c["stars"] = min(5.0, stars)  # 不超过5星
    
    return sorted_classes