
<<<<<<< HEAD
=======


>>>>>>> b8802e20571c49c94397670dc77df7fd59e65186
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
def init_db(app):
    """初始化数据库"""
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:767904rcnb@localhost:3306/eduai'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_POOL_SIZE'] = 10
    app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30
    app.config['SQLALCHEMY_POOL_RECYCLE'] = 1800
    app.config['SQLALCHEMY_MAX_OVERFLOW'] = 5

    db.init_app(app)
    
    # 在应用上下文中创建表
    with app.app_context():
        db.create_all()
    print(db)