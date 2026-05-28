"""OCR 라우터 — 백엔드가 영수증 등록 후 호출 / 또는 콜백.

엔드포인트 (구현 예정):
  POST /api/v1/ocr
    Body: schemas.ocr.OcrRequest (receipt_id, image_url)
    Response: schemas.ocr.OcrResponse (store_name, total_amount, address, lat, lng)
"""

from fastapi import APIRouter

router = APIRouter()


# TODO: @router.post("/ocr", response_model=OcrResponse)
#       async def parse_receipt(request: OcrRequest) -> OcrResponse:
#           return await ocr_service.parse(request)
