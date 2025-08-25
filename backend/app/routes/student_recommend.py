import json
import math
import os
from typing import Dict, List
import uuid
from flask import Blueprint, jsonify, request, session
import jieba
from openai import OpenAI
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
from app.utils.create_cat import EMBED_MODEL
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
    # 查询最新的课后推荐资源
    recommendation = (
        session.query(StudentRecommend)
        .filter_by(user_id=user_id, course_id=course_id, type='post_class')
        .order_by(StudentRecommend.created_at.desc())  # 按创建时间降序
        .first()  # 只获取第一条
    )
    # 如果没有找到推荐资源，返回 None
    if not recommendation:
        return None
    # 初始化一个列表，用于存储处理后的数据
    processed_recommendations = recommendation.content

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
        if recommendations is None:
            return jsonify({"video_recommendations": None, "message": "尚未生成课后推荐资源"}), 200
        
        return jsonify({"video_recommendations": recommendations}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

def _get_student_class_info(student_id: int):
    """
    返回 List[Dict] : [{"name":"xx班","description":"xxx"}, ...]
    """
    student = User.query.get(student_id)
    if not student or student.role != 'student':
        return []
    # 通过多对多关系直接拿 Courseclass 对象
    classes = student.student_courseclasses
    return [{"name": c.name, "description": c.description or ""} for c in classes]
import sqlalchemy as sa
from app.config import Config
@student_recommend_bp.route('/generate_learn', methods=['GET'])
def generate_learning_route():
    """
    Body:
        {
          "target": "前端开发"
        }
    需要登录态携带 student_id（可从 token/Session 里取）
    """
    # 1. 获取学生 id（示例：从 g.user）
    student_id = session.get('user_id')  # 根据你鉴权方式调整
    if not student_id:
        return jsonify(code=401, msg="未登录"), 401

    target_topic = request.args.get("target")
    if not target_topic:
        return jsonify(code=400, msg="target 不能为空"), 400

    # 2. 拉取课程班信息
    class_info = _get_student_class_info(student_id)

    class_text = "\n".join([f"- {c['name']}：{c['description']}" for c in class_info])

    # 3. 组装 DeepSeek prompt
    system_prompt = (
        "你是教学规划专家，请根据学生已学过的课程班，为其制定个性化学习路线，"
        "要求：\n"
        "1. 学习路线层级不超过3层（根节点→阶段→具体知识课程）\n"
        "2. 每个阶段下的知识课程控制在3-5个\n"
        "3. 总节点数不超过15个\n"
        "4. 输出严格 JSON（不要 markdown 代码块）"
    )
    user_prompt = (
        f"已学过的课程班：\n{class_text}\n\n"
        f"接下来想学习的内容：{target_topic}\n\n"
        "请按以下示例格式返回：\n"
        "{\n"
        '  "name": "前端学习路线",\n'
        '  "itemStyle": { "color": "#5470c6" },\n'
        '  "children": [\n'
        '    {\n'
        '      "name": "基础阶段",\n'
        '      "itemStyle": { "color": "#91cc75" },\n'
        '      "children": [\n'
        '        { "name": "HTML 语义化标签" },\n'
        '        { "name": "CSS 布局与响应式" }\n'
        '      ]\n'
        '    }\n'
        '  ]\n'
        "}"
    )

    # 4. 调用 DeepSeek
    client = OpenAI(
        api_key=Config.DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com/v1"
    )
    try:
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        route_str = resp.choices[0].message.content.strip()
        route_json = json.loads(route_str)
    except Exception as e:
        return jsonify(code=500, msg=f"生成学习路线失败：{e}"), 500
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # 5. 写文件
    storage_dir = os.path.join(project_root, 'static', 'learn') 
    os.makedirs(storage_dir, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.json"
    filepath = os.path.join(storage_dir, filename)
    stpath = os.path.join('static','learn',filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(route_json, f, ensure_ascii=False, indent=2)

    # 6. 更新用户表
    user = User.query.get(student_id)
    user.learning_path_file = stpath
    db.session.commit()

    # 7. 返回
    return jsonify(code=0, msg="success", data=route_json)


def _cosine_sim(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    return dot / (norm_a * norm_b + 1e-8)
from dashscope import TextEmbedding   
from sqlalchemy.orm import joinedload
@student_recommend_bp.route('/generate_learn/search', methods=['GET'])
def search_public_classes():
    kw = request.args.get("q", "").strip()
    page = max(int(request.args.get("page", 1)), 1)
    per = max(min(int(request.args.get("per", 10)), 50), 1)

    if not kw:
        return jsonify(code=400, msg="缺少查询关键词 q"), 400

    # 1) 更灵活的模糊搜索 - 拆分关键词为多个部分
    keywords = [w for w in jieba.lcut(kw) if len(w) >= 2]
    conditions = []
    
    # 为每个关键词部分创建模糊匹配条件
    for keyword in keywords:
        if not keyword:
            continue
            
        like_kw = f"%{keyword}%"
        conditions.extend([
            Courseclass.name.ilike(like_kw),
            Courseclass.description.ilike(like_kw),
            Courseclass.courses.any(Course.name.ilike(like_kw)),
            Courseclass.courses.any(Course.description.ilike(like_kw))
        ])
    
    # 如果没有有效关键词，返回空结果
    if not conditions:
        return jsonify(code=0, msg="success", data={"total": 0, "results": []})
    
    # 使用OR连接所有条件，实现部分匹配
    base_q = (
        db.session.query(Courseclass)
        .filter(Courseclass.is_public.is_(True))
        .options(joinedload(Courseclass.courses))
        .filter(sa.or_(*conditions))
        .distinct()
    )

    total = base_q.count()
    # 限制获取最多3个候选结果
    candidates = base_q.offset((page - 1) * per).limit(min(per, 3)).all()

    if not candidates:
        return jsonify(code=0, msg="success", data={"total": 0, "results": []})

    # 2) 用 dashscope 原生 SDK 获取向量
    kw_resp = TextEmbedding.call(
        model="text-embedding-v4",
        input=kw,
        text_type="query",
        api_key=os.getenv("DASHSCOPE_API_KEY", "")
    )
    kw_vec = kw_resp.output["embeddings"][0]["embedding"]

    # 3) 向量重排
    scored = []
    for cls in candidates:
        full_text = " ".join(
            [cls.name or "", cls.description or ""] +
            [c.name or "" for c in cls.courses] +
            [c.description or "" for c in cls.courses]
        )
        cls_resp = TextEmbedding.call(
            model="text-embedding-v4",
            input=full_text,
            text_type="document",
            api_key=os.getenv("DASHSCOPE_API_KEY", "")
        )
        cls_vec = cls_resp.output["embeddings"][0]["embedding"]
        score = _cosine_sim(kw_vec, cls_vec)
        scored.append((score, cls))

    scored.sort(key=lambda x: x[0], reverse=True)

    # 4) 序列化返回，最多返回3个结果
    results = [
        {
            "id": cls.id,
            "name": cls.name,
            "description": cls.description,
            "image_path": cls.image_path,
            "invite_code": cls.invite_code,
            "courses": [
                {"id": c.id, "name": c.name, "description": c.description}
                for c in cls.courses
            ],
            "score": round(score, 3)
        }
        for score, cls in scored[:3]  # 确保最多返回3个结果
    ]

    return jsonify(code=0, msg="success", data={
        "total": min(total, 3),  # 总数为实际匹配数，但最多显示3
        "page": page,
        "per": min(per, 3),     # 每页数量最多为3
        "results": results
    })

# 在 student_recommend.py 中添加以下路由
@student_recommend_bp.route('/get_user_learning_path', methods=['GET'])
def get_user_learning_path_route():
    """
    获取当前用户已生成的学习路径
    """
    # 检查用户是否登录
    if not is_logged_in():
        return jsonify({'error': '未登录'}), 401

    student_id = session.get('user_id')
    user = User.query.get(student_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    # 检查用户是否有学习路径文件
    if not user.learning_path_file:
        return jsonify(code=404, msg="尚未生成学习路径", data=None)
    
    try:
        # 读取学习路径文件
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filepath = os.path.join(project_root, user.learning_path_file)
        
        if not os.path.exists(filepath):
            return jsonify(code=404, msg="学习路径文件不存在", data=None)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            learning_path_data = json.load(f)
        
        return jsonify(code=0, msg="success", data=learning_path_data)
        
    except Exception as e:
        return jsonify(code=500, msg=f"读取学习路径失败：{e}", data=None), 500
