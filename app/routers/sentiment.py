# app/routers/sentiment.py

from fastapi import APIRouter

router = APIRouter()

@router.post("/analyze")
def analyze_sentiment(text: str):
    # 실제 감성 분석 로직 연결 예정
    return {"message": "감성 분석 결과 예시", "text": text}