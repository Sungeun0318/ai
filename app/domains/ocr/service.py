"""영수증 OCR 로직.

입력: receipt_id, image_url (S3 등)
출력: OcrResponse (상호명, 금액, 주소, 좌표)

구현 단계 (예시):
  1) image_url 에서 이미지 다운로드 (httpx)
  2) OCR 엔진 호출 (CLOVA OCR / Tesseract / EasyOCR / etc.)
  3) 텍스트에서 상호명/금액 정규식·룰 기반 추출
  4) 주소 → 카카오 좌표 변환 API 호출
"""
import os
from google.cloud import vision
from google.oauth2 import service_account
from app.domains.ocr.schema import OcrRequest, OcrResponse

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # app/domains/ocr/
KEY_PATH = os.path.join(BASE_DIR, "..", "..", "..", "service-account-key.json")

def detect_all_text_from_url(image_url: str):
    credentials = service_account.Credentials.from_service_account_file(KEY_PATH)
    client = vision.ImageAnnotatorClient(credentials=credentials)
    
    image = vision.Image()
    image.source.image_uri = image_url

    response = client.text_detection(image=image)
    texts = response.text_annotations

    if not texts:
        return "텍스트를 찾을 수 없습니다."
    return texts[0].description

async def parse(request: OcrRequest) -> OcrResponse:
    try:
        all_text = detect_all_text_from_url(request.image_url)
        
        return OcrResponse(
            receipt_id=request.receipt_id,
            success=True,
            full_text=all_text
        )
    except Exception as e:
        return OcrResponse(receipt_id=request.receipt_id, success=False, error_message=str(e))