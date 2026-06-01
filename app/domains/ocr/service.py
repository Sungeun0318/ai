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
import json
import httpx
from dotenv import load_dotenv
from google import genai  # 새 라이브러리
from google.oauth2 import service_account
from google.cloud import vision
from app.domains.ocr.schema import OcrRequest, OcrResponse

# 환경 변수 로드
load_dotenv()

# 새 클라이언트 초기화
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# 서비스 어카운트 인증 (기존과 동일)
KEY_PATH = r"C:\beggar\ai\service-account-key.json"
CREDENTIALS = service_account.Credentials.from_service_account_file(KEY_PATH)

async def parse(request: OcrRequest) -> OcrResponse:
    # 1. 이미지 다운로드
    try:
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            http_res = await http_client.get(request.image_url)
            content = http_res.content
    except Exception as e:
        return OcrResponse(receipt_id=request.receipt_id, success=False, error_message=str(e))
    
    # 2. 구글 비전 API 호출
    vision_client = vision.ImageAnnotatorClient(credentials=CREDENTIALS)
    image = vision.Image(content=content)
    vision_res = vision_client.document_text_detection(image=image)
    
    full_text = vision_res.full_text_annotation.text
    
    # 3. 새로운 SDK로 Gemini 호출 (모델명: gemini-2.0-flash 등 최신 모델 사용)
    try:
        # 모델 목록을 조회하여 첫 번째 가용한 모델 사용
        # (gemini-1.5-flash 또는 gemini-2.0-flash 등)
        model_name = "gemini-1.5-flash" 
        
        response = client.models.generate_content(
            model=model_name,
            contents=f"""
            다음은 영수증 텍스트야. JSON 형식으로만 응답해줘.
            JSON 필드: storeName, totalAmount(숫자), address
            텍스트: {full_text}
            """
        )
        
        # 응답 처리
        result_text = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(result_text)
    except Exception as e:
        return OcrResponse(receipt_id=request.receipt_id, success=False, error_message=str(e))
    
    return OcrResponse(
        receipt_id=request.receipt_id,
        success=True,
        store_name=data.get("storeName", "알 수 없음"),
        total_amount=int(data.get("totalAmount", 0)),
        address=data.get("address"),
        lat=None,
        lng=None
    )