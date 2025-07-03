# app/db_models/similarity.py

from sqlalchemy import Column, Integer, Unicode, LargeBinary, ForeignKey, UniqueConstraint
from app.database import Base

class SensitiveWord(Base):
    __tablename__ = "sensitive_words"

    word_id = Column(Integer, primary_key=True, index=True)
    word = Column(Unicode(100), nullable=False, unique=True)        
    embedding = Column(LargeBinary, nullable=False)
    model_name = Column(Unicode(100), nullable=False)                

class UserSensitiveWord(Base):
    __tablename__ = "user_sensitive_words"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Unicode(100), nullable=False)
    word_id = Column(Integer, ForeignKey("sensitive_words.word_id"), nullable=False)  

    __table_args__ = (
        UniqueConstraint("user_id", "word_id", name="uq_user_word_pair"),  
    )