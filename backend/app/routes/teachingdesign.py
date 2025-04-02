import os
import uuid
from venv import logger
from bson import ObjectId
from flask import Blueprint, app, current_app, make_response, redirect, render_template, request, jsonify, send_file, session
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
from app.services.lesson_plan import generate_lesson_plans
from app.models.teachingdesignversion import TeachingDesignVersion

teachingdesign_bp=Blueprint('teachingdesign',__name__)

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
    
@teachingdesign_bp.route('/courses/<int:course_id>/designs', methods=['POST'])
def create_teaching_design(course_id):
    """
    创建新的教学设计（自动创建初始版本）
    权限要求：必须是该课程的任课老师
    """
    if not is_teacher_of_course(course_id):
        logger.warning(f"Unauthorized attempt to create design for course {course_id} by user {session.get('user_id')}")
        return make_response(code=403, message="只有课程任课老师可以创建教学设计")
    
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')
    objectives = data.get('objectives')
    course_content = data.get('course_content')
    student_feedback = data.get('student_feedback', '')
    
    if not all([title, content, objectives, course_content]):
        return make_response(code=400, message="标题、内容、目标和课程内容不能为空")
    
    current_user = get_current_user()
    
    try:
        # 创建教学设计
        new_design = TeachingDesign(
            course_id=course_id,
            title=title,
            creator_id=current_user.id
        )
        db.session.add(new_design)
        db.session.flush()
        
        # 生成差异化教案
        lesson_plans = generate_lesson_plans(objectives, course_content, student_feedback)
        version_content = {
            "manual_content": content,
            "generated_plans": lesson_plans,
            "objectives": objectives,
            "course_content": course_content,
            "student_feedback": student_feedback
        }
        
        # 创建初始版本
        initial_version = TeachingDesignVersion(
            design_id=new_design.id,
            version=1,
            content=version_content,
            author_id=current_user.id
        )
        db.session.add(initial_version)
        
        # 设置当前版本
        new_design.current_version_id = initial_version.id
        
        db.session.commit()
        
        logger.info(f"New teaching design created for course {course_id} by user {current_user.id}")
        return make_response(
            code=201, 
            message="教学设计和初始版本创建成功", 
            data={
                "design_id": new_design.id,
                "version_id": initial_version.id
            }
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to create teaching design: {str(e)}")
        return make_response(code=500, message="教学设计创建失败")