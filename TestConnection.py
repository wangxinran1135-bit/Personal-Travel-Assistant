# test_db_connection.py
from Database import get_db_connection

def test_connection():
    try:
        conn = get_db_connection()
        print("数据库连接成功")
        conn.close()
    except Exception as e:
        print(f"数据库连接失败: {e}")

if __name__ == "__main__":
    test_connection()