# main.py
from fastapi import FastAPI
import app.state as state  
from app.routers import forbidden, sentiment, similarity, db
from app.filter_utils.forbidden_utils import load_automaton_from_db

# ✅ 추가: ORM 테이블 생성용 import
from app.database import engine
from db_models.similarity import SensitiveWord, UserSensitiveWord
from db_models.forbidden import ForbiddenWord

app = FastAPI()

app.include_router(forbidden.router, prefix="/forbidden")
app.include_router(sentiment.router, prefix="/sentiment")
app.include_router(similarity.router, prefix="/similarity")
app.include_router(db.router, prefix="/db")  

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!!!"}


@app.on_event("startup")
def on_startup():
    try:
        # ✅ 1단계: ORM 테이블 생성 (존재하지 않을 경우만)
        ForbiddenWord.metadata.create_all(bind=engine)
        SensitiveWord.metadata.create_all(bind=engine)
        UserSensitiveWord.metadata.create_all(bind=engine)

        state.forbidden_automaton = load_automaton_from_db()

        if state.forbidden_automaton:
            print("✅ 금칙어 로딩 완료.")
        else:
            print("⚠️ [주의] 금칙어가 DB에 존재하지 않아 트라이가 비어 있습니다. → 금칙어를 먼저 등록하세요.")
    except Exception as e:
        print(f"❌ [오류] 금칙어 로딩 중 예외 발생: {e}")