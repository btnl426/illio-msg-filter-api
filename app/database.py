# app/database.py

import pyodbc
from app.config import DB_CONFIG

def get_connection():
    try:
        conn_str = (
            f"DRIVER={{{DB_CONFIG['driver']}}};"
            f"SERVER={DB_CONFIG['server']};"
            f"DATABASE={DB_CONFIG['database']};"
            f"UID={DB_CONFIG['username']};"
            f"PWD={DB_CONFIG['password']}"
        )
        connection = pyodbc.connect(conn_str)
        return connection
    except Exception as e:
        print("❌ DB 연결 실패:", e)
        raise