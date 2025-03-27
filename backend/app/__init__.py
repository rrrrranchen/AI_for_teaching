from bson import ObjectId
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from .utils.database import init_db
from app.routes.auth import auth_bp
from app.routes.courseclass import courseclass_bp
from app.routes.course import course_bp
from app.routes.forum import forum_bp
from app.routes.question import question_bp
from app.routes.teachingdesign import teachingdesign_bp
from app.routes.studentanswer import studentanswer_bp
# 初始化 Flask 应用
def create_app():
    app = Flask(__name__, static_folder='static')


    app.config["JWT_SECRET_KEY"] = "sadfasdfgghgafdshg"
    app.secret_key = "jskldjflksdjlfksjd"
    JWTManager(app)

    # 初始化数据库
    init_db(app)

    # 注册蓝图
    app.register_blueprint(auth_bp)
    app.register_blueprint(courseclass_bp)
    app.register_blueprint(course_bp)
    app.register_blueprint(forum_bp)
    app.register_blueprint(question_bp)
    app.register_blueprint(teachingdesign_bp)
    app.register_blueprint(studentanswer_bp)
    return app
