# app/schemas/forbidden_schema.py
from pydantic import BaseModel
from typing import List

class ForbiddenWord(BaseModel):
    word: str

class ForbiddenWordList(BaseModel):
    words: List[str]