"""OCR 라우터 — 백엔드가 영수증 등록 후 호출 / 또는 콜백.

엔드포인트 (구현 예정):
  POST /api/v1/ocr
    Body: app.domains.ocr.schema.OcrRequest (receipt_id, image_url)
    Response: app.domains.ocr.schema.OcrResponse (store_name, total_amount, address, lat, lng)
"""

from fastapi import APIRouter
from app.domains.ocr.schema import OcrRequest, OcrResponse
from app.domains.ocr import service as ocr_service
router = APIRouter()


# TODO: from app.domains.ocr.schema import OcrRequest, OcrResponse
#       from app.domains.ocr import service as ocr_service
#
#       @router.post("/ocr", response_model=OcrResponse)
#       async def parse_receipt(request: OcrRequest) -> OcrResponse:
#           return await ocr_service.parse(request)

@router.post("/ocr", response_model=OcrResponse)
async def parse_receipt(request: OcrRequest) -> OcrResponse:
    # 비동기로 service의 parse 함수를 호출합니다.
    return await ocr_service.parse(request)