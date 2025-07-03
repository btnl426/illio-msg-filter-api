# app/api.py
from fastapi import APIRouter
from app.database import db_session

router = APIRouter()


@router.get("/ping-db")
def ping_db():
    try:
        with db_session() as session:
            result = session.execute(text("SELECT GETDATE();")).fetchone()
            return {"message": "✅ DB 연결 성공!", "db_time": str(result[0])}
    except Exception as e:
        return {"message": "❌ DB 연결 실패", "error": str(e)}

