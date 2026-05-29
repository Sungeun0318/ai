"""FastAPI 진입점.

uvicorn 실행:
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import health
from app.core.config import settings
from app.domains import ocr, recommend

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="거지 우정 수호대 — AI 추천/OCR 서버",
)

# CORS — 백엔드만 호출하면 사실 불필요하지만, 로컬 디버깅용으로 열어둠
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록 (도메인별, /api/v1 통합 prefix)
app.include_router(health.router,    prefix="/api/v1", tags=["health"])
app.include_router(recommend.router, prefix="/api/v1", tags=["recommend"])
app.include_router(ocr.router,       prefix="/api/v1", tags=["ocr"])
