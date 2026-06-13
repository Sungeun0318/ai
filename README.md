# beggar-ai

거지 우정 수호대 FastAPI AI 서버다.

## 현재 상태

- FastAPI + Uvicorn 기반.
- `/api/v1/health` 구현 완료.
- `/api/v1/ocr` 구현 중이며 현재 Google Cloud Vision으로 텍스트를 읽고 Groq LLM으로 영수증 JSON을 분석한다.
- OCR 분석 후 백엔드 `PUT /rooms/{roomNo}/receipts/{receiptId}/ocr`를 호출해 결과를 반영한다.
- `/api/v1/recommend` 도메인은 라우터/스키마/서비스 골격만 있고 실제 추천은 Spring 백엔드가 직접 처리한다.

## 실행

```bash
cd ai
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

주소:

```text
http://localhost:8000
```

Swagger:

```text
http://localhost:8000/docs
```

## 환경 변수

`.env.example`을 참고해 `.env`를 만든다.

주요 값:

```text
GROQ_API_KEY=Groq API key
BACKEND_BASE_URL=http://localhost:8080
KAKAO_REST_API_KEY=후속 추천/지오코딩 후보
AWS_*=S3 다운로드 후보
```

현재 `ocr/service.py`에는 백엔드 URL이 `http://localhost:8080`로 직접 들어가 있다. 배포 전에는 `settings.backend_base_url` 사용으로 바꿔야 한다.

Google Vision은 `service-account-key.json` 파일을 기준으로 인증한다.

## 구조

```text
ai/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   ├── health.py
│   │   └── logging.py
│   └── domains/
│       ├── ocr/
│       │   ├── router.py
│       │   ├── schema.py
│       │   └── service.py
│       └── recommend/
│           ├── router.py
│           ├── schema.py
│           └── service.py
└── tests/
    └── test_health.py
```

## API

| Method | Path | 상태 | 설명 |
|---|---|---|---|
| `GET` | `/api/v1/health` | 구현 완료 | `{"status":"ok"}` |
| `POST` | `/api/v1/ocr` | 구현 중 | 영수증 이미지 OCR/분석 후 백엔드에 반영 |
| `GET` | `/api/v1/recommend` | 스텁 | 후속 AI 추천 고도화 후보 |

## OCR 요청/응답

요청:

```json
{
  "receiptId": 42,
  "roomNo": 1,
  "imageUrl": "https://..."
}
```

응답:

```json
{
  "receipt_id": 42,
  "success": true,
  "analysis": {
    "store_name": "상호명",
    "address": "주소",
    "total_amount": 30000,
    "date": "2026-06-13 12:00:00",
    "category": "한식",
    "items": [
      {
        "name": "메뉴",
        "price": 10000,
        "quantity": 1,
        "amount": 10000
      }
    ]
  }
}
```

## OCR 내부 흐름

```text
POST /api/v1/ocr
  -> Google Vision text_detection(imageUrl)
  -> Groq llama-3.3-70b-versatile JSON 분석
  -> 주소 괄호 내용 제거
  -> PUT http://localhost:8080/rooms/{roomNo}/receipts/{receiptId}/ocr
  -> OcrResponse 반환
```

백엔드 반영 payload:

```json
{
  "storeName": "상호명",
  "address": "정제 주소",
  "totalAmount": 30000,
  "amount": 30000
}
```

## 추천 도메인

현재 추천은 AI 서버가 아니라 Spring 백엔드 `RecommendationService`가 맡는다.

Spring API:

```text
GET /rooms/{roomNo}/recommend?tag=&region=&lat=&lng=&radius=
```

AI `recommend` 도메인은 후속 작업에서 다음 태그/소비 흐름 추천, AI Hub 데이터 기반 고도화 등을 붙이는 후보 영역이다.

## 테스트

```bash
pytest -v
```

## 참고

- 전체 기능 명세: `../docs/APP_FEATURES.md`
- 백엔드 README: `../backend/README.md`
