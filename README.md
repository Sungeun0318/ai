# beggar-ai

거지 우정 수호대 — **AI 추천 / OCR 서버** (FastAPI)

## 현재 상태 (2026-05-28)
**스캐폴딩 완료**. FastAPI 0.115 + Python 3.11+ 권장. 라우터/스키마/서비스/공통 패키지 골격만 들어 있고, 추천 알고리즘과 OCR 본체는 비어있음 (구현 예정).

## 기술 스택
- **웹**: FastAPI + Uvicorn
- **DTO**: Pydantic v2 + pydantic-settings
- **HTTP 클라이언트**: httpx (카카오 API, S3 다운로드)
- **OCR / 추천**: 구현 단계에서 결정 (CLOVA OCR / Tesseract / EasyOCR / 자체 알고리즘)
- **DB 직접 접근 없음** — 백엔드(Spring)가 호출, Python 은 stateless

## 아키텍처 위치
```
[Flutter] ──HTTP──▶ [Spring Boot]  ──HTTP──▶ [beggar-ai (8000)]
                    (백엔드가 중계)              (이 프로젝트)
```
- 백엔드 `RecommendationService` 와 `ReceiptService` 가 본 서버를 호출
- 본 서버는 **stateless** — DB 적재 없음, 호출 시점에만 처리

## 패키지 구조
```
ai/
├── requirements.txt          런타임 의존성
├── requirements-dev.txt      pytest, ruff, mypy
├── .env.example              환경변수 템플릿
├── app/
│   ├── main.py               FastAPI 진입점 + 라우터 등록
│   ├── core/                 설정 (config) + 로깅
│   ├── api/v1/               라우터 (recommend, ocr, health)
│   ├── schemas/              Pydantic DTO (백엔드 Java record 와 1:1)
│   ├── services/             비즈니스 로직 (추천, OCR)
│   └── common/               공통 예외
└── tests/                    pytest
```

## 실행 방법

### 1. 가상환경 + 의존성
```bash
cd ai
python3 -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
```

### 2. 환경변수
```bash
cp .env.example .env
# .env 편집 (KAKAO_REST_API_KEY 등)
```

### 3. 서버 실행
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- API 문서: http://localhost:8000/docs (Swagger UI 자동 생성)
- 헬스 체크: http://localhost:8000/api/v1/health

### 4. 테스트
```bash
pytest -v
```

## API 엔드포인트 (예정)

| Method | Path | 설명 | 호출자 |
|---|---|---|---|
| GET  | `/api/v1/health` | 헬스 체크 | (외부) |
| GET  | `/api/v1/recommend` | 추천 (가게 3곳) | Spring `RecommendationService` |
| POST | `/api/v1/ocr` | 영수증 OCR | Spring `ReceiptService` |

## 백엔드 연동 계약

### 추천 — Spring → Python
**Spring 호출:**
```
GET http://localhost:8000/api/v1/recommend
  ?room_no=1&budget=60000&tags=한식,일식&lat=37.5&lng=126.9
```

**Python 응답** (`schemas/recommend.py` 의 `RecommendResponse`):
```json
{
  "roomNo": 1,
  "totalBudget": 60000,
  "places": [
    {
      "name": "정성 한식 세트",
      "category": "한식",
      "expectedPrice": 38000,
      "walkTime": "도보 5분",
      "rating": 4.6,
      "thumbnailUrl": "https://...",
      "address": "...",
      "lat": 37.5012,
      "lng": 126.9876
    }
  ]
}
```

### OCR — Spring → Python
**Spring 호출:**
```
POST http://localhost:8000/api/v1/ocr
Content-Type: application/json

{ "receiptId": 42, "imageUrl": "https://s3.../receipt.jpg" }
```

**Python 응답** (`schemas/ocr.py` 의 `OcrResponse`):
```json
{
  "receiptId": 42,
  "success": true,
  "storeName": "정성한식",
  "totalAmount": 35000,
  "address": "...",
  "centerLat": 37.5012,
  "centerLng": 126.9876
}
```

## 참고 문서
- 파일별 상세: [`STRUCTURE.md`](./STRUCTURE.md)
- 기능 명세 전체: [`../docs/PYTHON_AI_FEATURES.md`](../docs/PYTHON_AI_FEATURES.md)
- 백엔드 매핑: [`../backend/STRUCTURE.md`](../backend/STRUCTURE.md) (RecommendationService / ReceiptService 섹션)
