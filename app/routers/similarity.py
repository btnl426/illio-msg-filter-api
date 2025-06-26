# app/routers/similarity.py
from fastapi import APIRouter

router = APIRouter()

@router.post("/compare")
def compare_similarity(text1: str, text2: str):
    return {"message": "유사도 비교 결과 예시", "input": [text1, text2]}