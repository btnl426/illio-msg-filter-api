# app/schemas/common.py

from typing import Any, Optional
from pydantic import BaseModel
from enum import Enum
    
class StatusEnum(str, Enum):
    # ✅ 기본 응답 상태
    SUCCESS = "success"         # 요청이 정상적으로 처리됨
    ERROR = "error"             # 처리 중 예외 발생 (서버 내부 오류 등)
    WARNING = "warning"         # 예외는 없지만 주의가 필요한 응답

    # ✅ 리소스 상태 관련
    NOT_FOUND = "not_found"          # 대상 리소스가 존재하지 않음 (ex. 삭제된 데이터 요청 등)
    ALREADY_EXISTS = "already_exists" # 중복된 리소스 등록 시도

class StandardResponse(BaseModel):
    status: StatusEnum
    message: Optional[str] = None
    detected: Optional[bool] = None
    data: Optional[Any] = None