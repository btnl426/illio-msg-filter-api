# app/routers/sentiment.py

from fastapi import APIRouter
from app.filter_utils.sentiment_utils import predict_sentiment
from app.schemas.sentiment_schema import SentimentRequest, SentimentResult
from app.schemas.common import StandardResponse, StatusEnum

router = APIRouter()

@router.post("/analyze", response_model=StandardResponse)
def analyze_sentiment(request: SentimentRequest):
    result = predict_sentiment(request.message)

    return StandardResponse(
        status=StatusEnum.SUCCESS,
        message="감성 분석 완료",
        detected = result["label"] == "negative",
        data=SentimentResult(
            sentiment=result["label"],
            confidence=result["confidence"],
            inference_time=result["inference_time"]
        )
    )