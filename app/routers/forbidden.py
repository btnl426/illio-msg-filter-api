from fastapi import APIRouter
from app.schemas.common import StandardResponse, StatusEnum
from app.filter_utils.forbidden_utils import (
    register_forbidden_word,
    insert_bulk_forbidden_words,
    check_forbidden_message,
    delete_forbidden_word,
    get_all_forbidden_words,
    is_forbidden_word
)
from app.schemas.forbidden_schema import (
    ForbiddenWord, 
    ForbiddenWordList,
    ForbiddenCheckResult,
    MessageInput
)

router = APIRouter()

@router.post("", response_model=StandardResponse)
def register_forbidden(data: ForbiddenWord):
    try:
        result = register_forbidden_word(data.word)

        if result.get("created"):
            return StandardResponse(
                status=StatusEnum.SUCCESS,
                message="금칙어가 등록되었습니다.",
                data=result
            )
        else:
            return StandardResponse(
                status=StatusEnum.ALREADY_EXISTS,
                message="이미 등록된 금칙어입니다.",
                data={"word": data.word}
            )

    except Exception as e:
        return StandardResponse(
            status=StatusEnum.ERROR,
            message="금칙어 등록 중 오류가 발생했습니다.",
            data={"error": str(e)}
        )

@router.post("/bulk", response_model=StandardResponse)
def register_forbidden_bulk(data: ForbiddenWordList):
    try:
        result = insert_bulk_forbidden_words(data.words)

        message = f"{len(result['registered'])}개의 금칙어가 등록되었습니다."
        return StandardResponse(
            status=StatusEnum.SUCCESS,
            message=message,
            data=result
        )

    except Exception as e:
        return StandardResponse(
            status=StatusEnum.ERROR,
            message="금칙어 등록 중 오류 발생",
            data={"error": str(e)}
        )
        
@router.get("", response_model=StandardResponse)
def fetch_all_forbidden_words():
    try:
        result = get_all_forbidden_words()
        return StandardResponse(
            status=StatusEnum.SUCCESS,
            message="금칙어 전체 조회 성공",
            data={"count": len(result), "forbidden_words": result}
        )
    except Exception as e:
        return StandardResponse(
            status=StatusEnum.ERROR,
            message="금칙어 조회 중 오류 발생",
            data={"error": str(e)}
        )
        
        
@router.get("/check/{word}", response_model=StandardResponse)
def check_forbidden_word(word: str):
    try:
        is_forbidden = is_forbidden_word(word)
        return StandardResponse(
            status=StatusEnum.SUCCESS,
            message="금칙어 여부 확인 완료",
            data={"word": word, "is_forbidden": is_forbidden}
        )
    except Exception as e:
        return StandardResponse(
            status=StatusEnum.ERROR,
            message="금칙어 여부 확인 중 오류 발생",
            data={"error": str(e)}
        )

@router.post("/check-message", response_model=StandardResponse)
def check_message(data: MessageInput):
    result = check_forbidden_message(data.message)
    
    return StandardResponse(
        status=StatusEnum.SUCCESS,
        message="금칙어 검사 완료",
        detected=bool(result["detected_words"]),
        data=ForbiddenCheckResult(**result)
    )

@router.delete("/{word}", response_model=StandardResponse)
def remove_forbidden_word(word: str):
    try:
        success = delete_forbidden_word(word)

        if success:
            return StandardResponse(
                status=StatusEnum.SUCCESS,
                message=f"'{word}' 삭제 완료",
                data={"deleted_word": word}
            )
        else:
            return StandardResponse(
                status=StatusEnum.NOT_FOUND,
                message=f"'{word}' 삭제 실패 또는 존재하지 않음",
                data=None
            )

    except Exception as e:
        return StandardResponse(
            status=StatusEnum.ERROR,
            message="금칙어 삭제 중 오류 발생",
            data={"error": str(e)}
        )