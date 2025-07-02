# app/schemas/forbidden_schema.py
from pydantic import BaseModel
from typing import List

class ForbiddenWord(BaseModel):
    word: str

class ForbiddenWordList(BaseModel):
    words: List[str]
    
class MessageInput(BaseModel):
    message: str
    
class ForbiddenCheckResult(BaseModel):
    message: str
    result: str
    detected_words: List[str]
    method: str
    inference_time: float