# app/config.py

from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

#print("✅ loaded from env:", os.getenv("DB_PASSWORD"))  

DB_CONFIG = {
    "server": os.getenv("DB_SERVER"),
    "database": os.getenv("DB_NAME"),
    "username": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "driver": "ODBC Driver 17 for SQL Server"
}