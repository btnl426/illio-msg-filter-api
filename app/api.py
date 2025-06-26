# app/api.py
from fastapi import APIRouter
from app.database import get_connection

router = APIRouter()

@router.get("/ping-db")
def ping_db():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT GETDATE();")  # 현재 DB 시간 가져오기
        result = cursor.fetchone()
        return {"message": "✅ DB 연결 성공!", "db_time": str(result[0])}
    except Exception as e:
        return {"message": "❌ DB 연결 실패", "error": str(e)}