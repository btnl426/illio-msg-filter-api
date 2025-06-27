# app/routers/sentiment.py

from fastapi import APIRouter
from app.filter_utils.sentiment_utils import predict_sentiment
from app.schemas.sentiment_schema import (
    SentimentRequest,
    SentimentResponse
)

router = APIRouter()

@router.post("/analyze", response_model=SentimentResponse)
def analyze_sentiment(request: SentimentRequest):
    sentiment = predict_sentiment(request.message)
    return SentimentResponse(
        message=request.message,
        sentiment=sentiment["label"],
        confidence=sentiment["confidence"],
        elapsed=sentiment["elapsed"]
    )