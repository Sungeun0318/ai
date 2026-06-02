"""영수증 OCR 로직.

입력: receipt_id, image_url (S3 등)
출력: OcrResponse (상호명, 금액, 주소, 좌표)

구현 단계 (예시):
  1) image_url 에서 이미지 다운로드 (httpx)
  2) OCR 엔진 호출 (CLOVA OCR / Tesseract / EasyOCR / etc.)
  3) 텍스트에서 상호명/금액 정규식·룰 기반 추출
  4) 주소 → 카카오 좌표 변환 API 호출
"""
import os, json
from groq import Groq
from dotenv import load_dotenv
from google.cloud import vision
from google.oauth2 import service_account
from app.domains.ocr.schema import OcrRequest, OcrResponse, ReceiptAnalysis

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # app/domains/ocr/
KEY_PATH = os.path.join(BASE_DIR, "..", "..", "..", "service-account-key.json")
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

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

def analyze_with_groq(text: str):
    prompt = f"""
    당신은 영수증 분석 전문가입니다. 아래 텍스트를 분석하여 오직 JSON 형식으로만 응답하세요.
    JSON에는 반드시 아래의 모든 필드를 포함해야 합니다.

    [카테고리 분류 규칙]
    - 파리바게트, 뚜레쥬르, 베이커리 등은 무조건 '기타 요식업'으로 분류한다. (절대 양식으로 분류하지 말 것)
    - 한식, 양식, 중식, 일식에 해당하면 해당 명칭으로 분류한다.
    - 그외는 '기타 요식업'으로 분류한다.
    
    텍스트: {text}

    JSON 형식:
    {{
      "store_name": "상호명",
      "address": "주소",
      "total_amount": 0,
      "date": "YYYY-MM-DD HH:MM:SS",
      "category": "한식|양식|중식|일식|기타 요식업 중 택 1",,
      "items": [
        {{ "name": "상품명", "price": 0, "quantity": 0, "amount": 0 }}
      ]
    }}
    """
    
    response = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        response_format={"type": "json_object"}
    )
    raw_content=response.choices[0].message.content
    print("[GROQ RESPONSE]")
    print(raw_content)

    return json.loads(raw_content)

async def parse(request: OcrRequest) -> OcrResponse:
    try:
        all_text = detect_all_text_from_url(request.image_url)
        if not all_text:
            return OcrResponse(receipt_id=request.receipt_id, success=False, error_message="OCR 실패")
        
        data=analyze_with_groq(all_text)
        analysis = ReceiptAnalysis(**data)
        
        return OcrResponse(
            receipt_id=request.receipt_id,
            success=True,
            full_text=all_text,
            analysis=analysis
        )
    except Exception as e:
        return OcrResponse(receipt_id=request.receipt_id, success=False, error_message=str(e))