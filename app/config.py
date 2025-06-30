# app/config.py

from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

print("✅ 환경변수 확인:", os.getenv("DB_DRIVER"))  

DB_CONFIG = {
    "server": os.getenv("DB_SERVER"),
    "port": os.getenv("DB_PORT", "1433"),
    "database": os.getenv("DB_NAME"),
    "username": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "driver": os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
}