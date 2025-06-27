# ✅ schemas/similarity_schema.py
from pydantic import BaseModel

class SensitiveWordRequest(BaseModel):
    user_id: str
    sentence: str
    
class SimilarityCheckRequest(BaseModel):
    user_id: str
    message: str
    
class SimilarityCheckResponse(BaseModel):
    status: str
    max_similarity: float
    most_similar_word: str
    threshold: float
    match: bool
    inference_time: float