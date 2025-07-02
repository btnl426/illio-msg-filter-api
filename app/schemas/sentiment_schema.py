from pydantic import BaseModel

class SentimentRequest(BaseModel):
    message: str

class SentimentResult(BaseModel):
    sentiment: str
    confidence: float
    inference_time: float 