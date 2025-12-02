# import pymysql
import psycopg
from psycopg.rows import dict_row 
import os

from dotenv import load_dotenv
load_dotenv() #解决 环境变量 加载失败问题


SECRET_KEY = os.getenv("SECRET_KEY")

# Flask Session 配置 - 确保 OAuth state 在进程间正确共享
SESSION_COOKIE_SECURE = False  # 开发环境设为 False，生产环境使用 HTTPS 时设为 True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
PERMANENT_SESSION_LIFETIME = 86400  # 24 小时

AWS_REGION = os.getenv("AWS_REGION")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
SES_SENDER = os.getenv("SES_SENDER")

FLASK_ENV= os.getenv("FLASK_ENV")
print("FLASK_ENV: ", FLASK_ENV)

OAUTH_CREDENTIALS = {
    "google": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
    }
}

# LLM API configuration
LLM_API_URL = os.getenv("LLM_API_URL", "https://api.openai.com/v1/chat/completions")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = "gpt-5-mini"

# Bing Images API Configuration (via SerpApi)
BING_IMAGES_API_KEY = os.getenv("BING_IMAGES_API_KEY", "")

# def mydb():
#     return pymysql.connect(
#         host='dinedose.cds2osi82wxl.us-east-1.rds.amazonaws.com',
#         user='admin',
#         password='8Q8aA18WrlwUmnDPwnGh',
#         database='db',
#         charset='utf8mb4',
#         port=3306,
#         cursorclass=pymysql.cursors.DictCursor
#     )

def mydb():
    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        sslmode=os.getenv("DB_SSLMODE")
    )

def cursor(conn):
    return conn.cursor(row_factory=dict_row)