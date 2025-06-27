# ✅ routers/similarity.py
from fastapi import APIRouter
from app.schemas.similarity_schema import (
    SensitiveWordRequest,
    SimilarityCheckRequest,
    SimilarityCheckResponse
)
from app.filter_utils.similarity_utils import (
    insert_sensitive_word,
    get_sensitive_words_by_user,
    check_message_similarity,
    remove_user_sensitive_word
)

router = APIRouter()

@router.post("/register")
def register_sensitive_word(request: SensitiveWordRequest):
    return insert_sensitive_word(
        user_id=request.user_id,
        sentence=request.sentence
    )
    
@router.get("/sensitive-words/{user_id}")
def get_user_sensitive_words(user_id: str):
    words = get_sensitive_words_by_user(user_id)
    print(f"Retrieved sensitive words for user {user_id}: {words}")
    return {"user_id": user_id, "sensitive_words": words}


@router.post("/check", response_model=SimilarityCheckResponse)
def check_sensitive_message(request: SimilarityCheckRequest):
    return check_message_similarity(request.user_id, request.message)


@router.delete("/sensitive-word")
def delete_sensitive_word(request: SensitiveWordRequest):
    success = remove_user_sensitive_word(request.user_id, request.sentence)
    if success:
        return {
            "status": "deleted",
            "user_id": request.user_id,
            "deleted_word": request.sentence
        }
    else:
        return {
            "status": "not_found",
            "user_id": request.user_id,
            "target_word": request.sentence
        }