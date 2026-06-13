# beggar-ai 구조

> 기준일: 2026-06-13  
> 기준 코드: `ai/sungeun`

## 전체 구조

```text
ai/
├── README.md
├── STRUCTURE.md
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   ├── health.py
│   │   └── logging.py
│   └── domains/
│       ├── __init__.py
│       ├── ocr/
│       │   ├── __init__.py
│       │   ├── router.py
│       │   ├── schema.py
│       │   └── service.py
│       └── recommend/
│           ├── __init__.py
│           ├── router.py
│           ├── schema.py
│           └── service.py
└── tests/
    ├── __init__.py
    └── test_health.py
```

## app/main.py

FastAPI 앱 진입점이다.

역할:

- `.env` 로드.
- `FastAPI(title=settings.app_name)` 생성.
- CORS 전체 허용. 현재는 로컬 디버깅 편의용이다.
- `/api/v1` prefix로 health, recommend, ocr 라우터 등록.

등록 라우터:

```text
/api/v1/health
/api/v1/recommend
/api/v1/ocr
```

## core

### `core/config.py`

`pydantic-settings` 기반 설정.

주요 설정:

- `app_name`
- `app_env`
- `host`
- `port`
- `backend_base_url`
- `backend_api_key`
- `kakao_rest_api_key`
- `naver_client_id`
- `naver_client_secret`
- `aws_access_key_id`
- `aws_secret_access_key`
- `aws_region`
- `s3_bucket`
- `log_level`

현재 OCR service는 `backend_base_url`을 아직 사용하지 않고 하드코딩 URL을 사용한다.

### `core/health.py`

```text
GET /api/v1/health
```

응답:

```json
{"status":"ok"}
```

### `core/exceptions.py`

AI 서버 공통 예외 후보를 정의한다.

- `AIServerError`
- `OcrFailed`
- `RecommendationFailed`

현재 OCR service는 예외를 던지기보다 `success=false` 응답을 반환한다.

### `core/logging.py`

로그 설정 함수가 있는 공통 모듈이다.

## domains/ocr

OCR 도메인이다. 현재 실제 로직이 들어가 있다.

### `ocr/router.py`

```text
POST /api/v1/ocr
```

요청 body는 `OcrRequest`, 응답은 `OcrResponse`다.

### `ocr/schema.py`

#### OcrRequest

| 필드 | JSON alias | 설명 |
|---|---|---|
| `receipt_id` | `receiptId` | 백엔드 영수증 ID |
| `image_url` | `imageUrl` | OCR 대상 이미지 URL |
| `room_no` | `roomNo` | 방 번호 |

#### ReceiptAnalysis

| 필드 | 설명 |
|---|---|
| `store_name` | 상호명 |
| `address` | 주소 |
| `total_amount` | 총액 |
| `date` | 결제 일시 후보 |
| `category` | `한식/양식/중식/일식/기타 요식업` |
| `products` | 품목 목록. JSON alias는 `items` |

#### OcrResponse

| 필드 | 설명 |
|---|---|
| `receipt_id` | 영수증 ID |
| `success` | OCR/분석 성공 여부 |
| `analysis` | 분석 결과. 실패 시 null |

### `ocr/service.py`

현재 구현 흐름:

1. Google Vision service account key 로드.
2. `image_url`을 Vision `image.source.image_uri`에 넣어 `text_detection` 실행.
3. 추출 텍스트를 Groq `llama-3.3-70b-versatile`에 전달.
4. Groq 응답을 JSON으로 파싱.
5. 주소에서 괄호 뒤 문자열을 제거.
6. 백엔드 `PUT /rooms/{roomNo}/receipts/{receiptId}/ocr` 호출.
7. `OcrResponse` 반환.

현재 하드코딩/주의점:

- Google key path: `ai/service-account-key.json` 기준.
- 백엔드 URL: `http://localhost:8080` 하드코딩.
- Groq API key: `GROQ_API_KEY`.
- 백엔드 반영 실패 시 로그만 찍고 OCR 응답 자체는 성공으로 반환될 수 있다.

## domains/recommend

추천 도메인이다. 현재는 후속 고도화용 스텁이다.

### `recommend/router.py`

라우터 객체만 있고 실제 `GET /recommend` 핸들러는 TODO 주석 상태다.

### `recommend/schema.py`

Spring `RecommendationResponse`와 맞추기 위한 Pydantic 모델 후보가 있다.

- `RecommendResponse`
- `Place`

### `recommend/service.py`

추천 알고리즘 구현 TODO만 있다.

현재 실제 추천은 백엔드 `RecommendationService`가 처리한다.

## tests

### `tests/test_health.py`

`GET /api/v1/health`가 200과 `{"status":"ok"}`를 반환하는지 확인한다.

실행:

```bash
pytest -v
```

## 후속 정리 필요

- OCR 백엔드 URL을 `settings.backend_base_url`로 변경.
- OCR 실패/백엔드 반영 실패를 공통 예외 구조로 통일.
- Google service account key 경로를 환경변수화.
- `recommend/router.py` 실제 API를 만들지 않으면 README에서 명확히 스텁으로 유지.
- 응답 JSON 필드명을 백엔드 DTO와 맞출지, Python snake_case로 유지할지 확정.
