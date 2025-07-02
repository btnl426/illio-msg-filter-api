# ✅ routers/similarity.py
from fastapi import APIRouter
from app.schemas.common import StandardResponse, StatusEnum
from app.schemas.similarity_schema import (
    SensitiveWordRequest,
    SimilarityCheckRequest,
    SimilarityResult
)
from app.filter_utils.similarity_utils import (
    insert_sensitive_word,
    get_sensitive_words_by_user,
    check_message_similarity,
    remove_user_sensitive_word
)

router = APIRouter()

@router.post("/register", response_model=StandardResponse)
def register_sensitive_word(request: SensitiveWordRequest):
    result = insert_sensitive_word(request.user_id, request.sentence)

    message = (
        "새로운 민감 단어가 등록되었습니다."
        if result.get("created")
        else "이미 등록된 민감 단어입니다."
    )

    return StandardResponse(
        status=StatusEnum.SUCCESS,
        message=message,
        data={"word_id": result["word_id"]}
    )
    
@router.get("/sensitive-words/{user_id}", response_model=StandardResponse)
def get_user_sensitive_words(user_id: str):
    words = get_sensitive_words_by_user(user_id)

    return StandardResponse(
        status=StatusEnum.SUCCESS,
        message="민감 단어 목록 조회 성공" if words else "등록된 민감 단어가 없습니다.",
        data={"user_id": user_id, "sensitive_words": words}
    )


@router.post("/check", response_model=StandardResponse)
def check_sensitive_message(request: SimilarityCheckRequest):
    result = check_message_similarity(
        user_id=request.user_id,
        message=request.message,
        threshold=request.threshold  
    )

    if result is None:
        return StandardResponse(
            status=StatusEnum.NOT_FOUND,
            message="수신받는 셀럽이 등록한 민감 단어가 없습니다.",
            detected=False,
            data=None
        )

    return StandardResponse(
        status=StatusEnum.SUCCESS,
        message="유사도 분석 완료",
        detected=result["match"],
        data=SimilarityResult(**result)
    )


@router.delete("/sensitive-word", response_model=StandardResponse)
def delete_sensitive_word(request: SensitiveWordRequest):
    result = remove_user_sensitive_word(request.user_id, request.sentence)

    if result["deleted"]:
        return StandardResponse(
            status=StatusEnum.SUCCESS,
            message="민감 단어 삭제 완료",
            data={"deleted_word": result["word"]}
        )
    elif result.get("reason") == "not_found":
        return StandardResponse(
            status=StatusEnum.NOT_FOUND,
            message="해당 단어가 등록되어 있지 않습니다.",
            data=None
        )
    else:
        return StandardResponse(
            status=StatusEnum.ERROR,
            message="민감 단어 삭제 중 오류 발생",
            data={"error": result.get("reason")}
        )