"""공통 예외 + FastAPI 핸들러."""

from fastapi import HTTPException, status


class AIServerError(HTTPException):
    """비즈니스 예외 기본."""

    def __init__(self, code: str, message: str, http_status: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=http_status, detail={"code": code, "message": message})


class RecommendationFailed(AIServerError):
    def __init__(self, message: str = "추천 생성에 실패했습니다."):
        super().__init__(code="RECO_001", message=message, http_status=status.HTTP_502_BAD_GATEWAY)
