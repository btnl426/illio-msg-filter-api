from pydantic import BaseModel

class SentimentRequest(BaseModel):
    message: str

class SentimentResponse(BaseModel):
    message: str
    sentiment: str
    confidence: float
    elapsed: float