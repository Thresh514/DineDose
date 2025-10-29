from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def db_init(app):
    """
    Initialize database connection with Flask app.
    """
    # 这里配置 RDS 连接字符串
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        'mysql+pymysql://admin:8Q8aA18WrlwUmnDPwnGh@'
        'dinedose.cds2osi82wxl.us-east-1.rds.amazonaws.com:3306/db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 初始化 db
    db.init_app(app)
    return db