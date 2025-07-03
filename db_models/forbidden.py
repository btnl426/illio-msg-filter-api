# app/db_models/forbidden.py

from sqlalchemy import Column, Integer, DateTime, func, Unicode
from app.database import Base

class ForbiddenWord(Base):
    __tablename__ = "forbidden_words"

    id = Column(Integer, primary_key=True, index=True)
    word = Column(Unicode(100), nullable=False, unique=True)
    decomposed_word = Column(Unicode(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())