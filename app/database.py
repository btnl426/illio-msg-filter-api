# app/database.py

import pyodbc
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from urllib.parse import quote_plus

from app.config import DB_CONFIG

driver = quote_plus(DB_CONFIG["driver"])  # ← 핵심: 값 + 중괄호 + 인코딩

DATABASE_URL = (
    f"mssql+pyodbc://{DB_CONFIG['username']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['server']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    f"?driver={driver}&TrustServerCertificate=yes&charset=utf8&autocommit=true"
)

# ✅ SQLAlchemy 엔진 및 세션
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# ✅ ORM 모델 정의용 Base 클래스
Base = declarative_base()

# ✅ 세션 컨텍스트 매니저
@contextmanager 
def db_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        
        

