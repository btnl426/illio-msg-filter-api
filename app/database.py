# app/database.py

import pyodbc
from app.config import DB_CONFIG

def get_connection():
    try:
        conn_str = (
            f"DRIVER={{{DB_CONFIG['driver']}}};"
            f"SERVER={DB_CONFIG['server']},{DB_CONFIG['port']};"
            f"DATABASE={DB_CONFIG['database']};"
            f"UID={DB_CONFIG['username']};"
            f"PWD={DB_CONFIG['password']}"
        )
        connection = pyodbc.connect(conn_str)
        return connection
    except Exception as e:
        print("❌ DB 연결 실패:", e)
        raise
    
if __name__ == "__main__":
    print("🔍 DB 연결 테스트 시작")
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sys.databases;")
        for row in cursor.fetchall():
            print("✅ DB 이름:", row[0])
        conn.close()
        print("🎉 DB 연결 성공 및 쿼리 수행 완료")
    except Exception as e:
        print("❌ DB 연결 테스트 실패:", e)