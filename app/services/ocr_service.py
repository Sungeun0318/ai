"""영수증 OCR 로직.

입력: receipt_id, image_url (S3 등)
출력: OcrResponse (상호명, 금액, 주소, 좌표)

구현 단계 (예시):
  1) image_url 에서 이미지 다운로드 (httpx)
  2) OCR 엔진 호출 (CLOVA OCR / Tesseract / EasyOCR / etc.)
  3) 텍스트에서 상호명/금액 정규식·룰 기반 추출
  4) 주소 → 카카오 좌표 변환 API 호출
"""


# TODO: async def parse(request: OcrRequest) -> OcrResponse:
#           ...
