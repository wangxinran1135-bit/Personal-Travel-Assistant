# db.py
import psycopg2

def get_db_connection():
    conn = psycopg2.connect(
        dbname="PTA",   # 改成你自己的
        user="postgres",          # 改成你自己的
        password="LANGlang45683968",      # 改成你自己的
        host="localhost",              # 如果数据库在本机就是 localhost
        port="5432"                    # PostgreSQL 默认端口
    )
    return conn
