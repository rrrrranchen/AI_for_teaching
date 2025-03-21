from flask_mongoengine import MongoEngine
from flask_sqlalchemy import SQLAlchemy


db_sql = SQLAlchemy()
db_mongo = MongoEngine()

def init_db(app):
    """初始化数据库"""
    # 初始化 MySQL 数据库
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost:3306/eduai'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_POOL_SIZE'] = 10
    app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30
    app.config['SQLALCHEMY_POOL_RECYCLE'] = 1800
    app.config['SQLALCHEMY_MAX_OVERFLOW'] = 5

    db_sql.init_app(app)

    # 在应用上下文中创建 MySQL 表
    with app.app_context():
        db_sql.create_all()

    # 初始化 MongoDB 数据库
    app.config['MONGODB_SETTINGS'] = {
        'db': 'eduai',  # MongoDB 数据库名称
        'host': 'localhost',  # MongoDB 数据库地址
        'port': 27017  # MongoDB 数据库端口
    }

    db_mongo.init_app(app)
    
    print("MySQL and MongoDB initialized successfully.")
