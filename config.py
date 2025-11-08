# import pymysql
import psycopg
from psycopg.rows import dict_row 

SECRET_KEY = "55a084ecc8d46bef8ee5070e0e9204c89af7b754145a52669281a0656c169c27"

AWS_REGION = "us-east-2"
AWS_ACCESS_KEY = "AKIAVTJABL27KS5SA6WT"
AWS_SECRET_KEY = "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"
SES_SENDER = "noreply@skylar27.com"

OAUTH_CREDENTIALS = {
    "google": {
        "client_id": "305136952975-4m6co6aq28qvkr97ri7ijd7d8ggcvu9f.apps.googleusercontent.com",
        "client_secret": "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",
    }
}

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
        host="ep-long-glitter-a8i7t160-pooler.eastus2.azure.neon.tech",
        dbname="neondb",
        user="neondb_owner",
        password="npg_0v8JkWHesVTq",
        sslmode="require"
    )

def cursor(conn):
    return conn.cursor(row_factory=dict_row)