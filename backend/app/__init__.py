import os
from bson import ObjectId
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from .utils.database import init_db
from app.routes.auth import auth_bp
from app.routes.courseclass import courseclass_bp
from app.routes.course import course_bp
from app.routes.question import question_bp
from app.routes.studentanswer import studentanswer_bp
from app.routes.resource import resource_bp
from app.routes.forum import forum_bp
from app.routes.teachingdesign import teachingdesign_bp
from app.routes.ppts import ppts_bp
from app.routes.teacher_recommend import teacher_recommend_bp
from app.routes.student_recommend import student_recommend_bp
from app.routes.human_management import human_management_bp
from app.routes.mindmap import mindmap_bp
from app.routes.resource_management import resource_management_bp
from app.routes.courseclass_management import courseclass_management_bp
from app.routes.sreen import sreen_bp
from app.utils.database import init_db
from config import Config
from flask_jwt_extended import JWTManager
# 初始化 Flask 应用
def create_app():
    app = Flask(__name__, static_folder='static')
    app.config.from_object(Config)
    print("ALLOWED_EXTENSIONS:", app.config.get('ALLOWED_EXTENSIONS', set()))
    app.config["JWT_SECRET_KEY"] = "sadfasdfgghgafdshg"
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600
    app.secret_key = "jskldjflksdjlfksjd"
    jwt = JWTManager(app)

    # 初始化数据库
    init_db(app)
    # 注册蓝图
    app.register_blueprint(auth_bp)
    app.register_blueprint(courseclass_bp)
    app.register_blueprint(course_bp)
    app.register_blueprint(question_bp)
    app.register_blueprint(studentanswer_bp)
    app.register_blueprint(resource_bp)
    app.register_blueprint(forum_bp)
    app.register_blueprint(teachingdesign_bp)
    app.register_blueprint(ppts_bp)
    app.register_blueprint(teacher_recommend_bp)
    app.register_blueprint(student_recommend_bp)
    app.register_blueprint(mindmap_bp)
    app.register_blueprint(human_management_bp)
    app.register_blueprint(resource_management_bp)
    app.register_blueprint(sreen_bp)
    app.register_blueprint(courseclass_management_bp)
    return app
