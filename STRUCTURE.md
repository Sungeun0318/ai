# Python AI 서버 파일 구조 & 기능 설명

> `ai/` 디렉터리의 모든 파일이 어떤 역할인지, 어떤 내용을 담아야 하는지 정리.
> **2026-05-28 기준**: 서비스 / 라우터 본체 코드는 비어있음. 본 문서가 그 빈 파일들의 "구현 계약서".

---

## 전체 구조

```
ai/
├── .gitignore              Python + IDE + OS + 비밀 파일 차단
├── .gitattributes          라인엔딩 LF 정규화 (Mac/Windows 협업)
├── README.md               실행 방법 + API 계약 요약
├── STRUCTURE.md            (본 문서) 파일별 상세 설명
├── requirements.txt        런타임 의존성 (fastapi, pydantic, httpx 등)
├── requirements-dev.txt    개발 의존성 (pytest, ruff, mypy)
├── .env.example            환경변수 템플릿 (.env 는 gitignored)
├── app/
│   ├── __init__.py
│   ├── main.py             FastAPI 진입점 + CORS + 라우터 등록
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py       pydantic-settings — .env 자동 로드
│   │   └── logging.py      로깅 설정
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── health.py       GET /api/v1/health
│   │       ├── recommend.py    ⚠ 비어있음 — GET /api/v1/recommend
│   │       └── ocr.py          ⚠ 비어있음 — POST /api/v1/ocr
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── recommend.py    Pydantic — RecommendResponse / Place
│   │   └── ocr.py          Pydantic — OcrRequest / OcrResponse
│   ├── services/
│   │   ├── __init__.py
│   │   ├── recommend_service.py    ⚠ 비어있음 — 추천 알고리즘
│   │   └── ocr_service.py          ⚠ 비어있음 — OCR 호출 + 파싱
│   └── common/
│       ├── __init__.py
│       └── exceptions.py    AIServerError / OcrFailed / RecommendationFailed
└── tests/
    ├── __init__.py
    └── test_health.py       헬스 체크 라우터 테스트
```

---

## 루트 파일

### `requirements.txt`
런타임 의존성. 현재 포함:
- `fastapi==0.115.5`, `uvicorn[standard]==0.32.1` — 웹 서버
- `pydantic==2.9.2`, `pydantic-settings==2.6.1` — DTO + 환경 설정
- `httpx==0.27.2` — 비동기 HTTP 클라이언트
- `python-multipart==0.0.17` — 파일 업로드

주석 처리된 후보:
- OCR: `pytesseract` / `easyocr` / `Pillow`
- 추천 알고리즘: `numpy` / `pandas` / `scikit-learn`
- 크롤링: `beautifulsoup4` / `selenium` (백엔드에 이미 있으면 불필요)

### `requirements-dev.txt`
`-r requirements.txt` 로 런타임 의존성 포함 + 개발 도구:
- `pytest==8.3.4`, `pytest-asyncio==0.24.0`
- `ruff==0.8.4` — 린터/포매터 (black 대체)
- `mypy==1.13.0` — 정적 타입 체크

### `.env.example`
실제 `.env` 파일 만들기 위한 템플릿. 키:
- 서버: `APP_NAME`, `APP_ENV`, `HOST`, `PORT`
- 백엔드 연동: `BACKEND_BASE_URL`, `BACKEND_API_KEY`
- 외부 API: `KAKAO_REST_API_KEY`, `NAVER_CLIENT_ID/SECRET`
- AWS S3: `AWS_ACCESS_KEY_ID/SECRET_ACCESS_KEY`, `AWS_REGION`, `S3_BUCKET`
- 로깅: `LOG_LEVEL`
- (주석) OCR: `CLOVA_OCR_URL/SECRET`
- (주석) LLM: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`

### `README.md`
실행 방법, API 엔드포인트, 백엔드 ↔ Python 계약(JSON 예시).

---

## app/ — 메인 패키지

### `app/main.py`
FastAPI 진입점. **하는 일**:
1. `FastAPI()` 인스턴스 생성 (title/version)
2. CORS 미들웨어 등록 (개발용 전체 허용)
3. v1 라우터 3개 등록 (`health`, `recommend`, `ocr`) — 모두 `/api/v1` 접두사
- 실행: `uvicorn app.main:app --reload --port 8000`

---

## app/core/ — 공통 인프라

### `app/core/config.py`
`Settings(BaseSettings)` 클래스. `pydantic-settings`로 `.env` 자동 로드.
- 클래스 속성으로 정의된 키만 `.env`에서 읽음 (case_sensitive=False)
- `extra="ignore"` — 정의 안 된 키는 무시
- 사용: `from app.core.config import settings; settings.kakao_rest_api_key`

### `app/core/logging.py`
`configure_logging()` 함수. `settings.log_level` 기반 표준 로깅 설정.
> 운영 단계에서 `structlog` / `loguru` 도입 고려.

---

## app/api/v1/ — REST 라우터

### `app/api/v1/health.py`
헬스 체크. **구현 완료**.
- `GET /api/v1/health` → `{"status": "ok"}`

### `app/api/v1/recommend.py` ⚠ 비어있음
추천 라우터. **TODO**:
```python
@router.get("/recommend", response_model=RecommendResponse)
def recommend(
    room_no: int,
    budget: int,
    tags: str,                 # "중식,한식,일식,양식,기타요식업" 중 콤마 분리
    lat: float | None = None,
    lng: float | None = None,
) -> RecommendResponse:
    return recommend_service.recommend(...)
```
- 백엔드 `RecommendationService.recommend()`가 `aiServerWebClient.get()`으로 호출
- 응답은 `schemas/recommend.py`의 `RecommendResponse` (Java `RecommendationResponse`와 1:1)

### `app/api/v1/ocr.py` ⚠ 비어있음
OCR 라우터. **TODO**:
```python
@router.post("/ocr", response_model=OcrResponse)
async def parse_receipt(request: OcrRequest) -> OcrResponse:
    return await ocr_service.parse(request)
```
- 백엔드 `ReceiptService.create()`/`updateAmount()` 처리 후 비동기 호출
- 또는 백엔드가 webhook URL을 알려주고 Python이 끝나면 callback 하는 패턴도 가능

---

## app/schemas/ — Pydantic DTO

JSON 직렬화 시 카멜케이스 (`expectedPrice`, `roomNo` 등) — 백엔드 Java record와 매칭.
`ConfigDict(populate_by_name=True)` + `Field(alias=...)` 패턴 사용.

### `app/schemas/recommend.py`
- `Place` — 가게 1곳 (name, category, expectedPrice, walkTime, rating, thumbnailUrl, address, lat, lng)
- `RecommendResponse` — 응답 전체 (roomNo, totalBudget, places: list[Place])
- **백엔드 매핑**: `com.beggar.api.dto.recommendation.RecommendationResponse` 와 동일 구조

### `app/schemas/ocr.py`
- `OcrRequest` — 요청 (receiptId, imageUrl)
- `OcrResponse` — 응답 (receiptId, success, storeName, totalAmount, address, centerLat, centerLng, errorMessage)
- **백엔드 매핑**: `Receipt` 엔티티의 `applyOcrResult(...)` 메서드 파라미터와 매칭

---

## app/services/ — 비즈니스 로직 (전부 비어있음)

### `app/services/recommend_service.py` ⚠ 비어있음
**구현 가이드**:
1. 위치 기준 카테고리별 후보 가게 수집
   - 카카오 로컬 API (`https://dapi.kakao.com/v2/local/search/keyword.json`)
   - `httpx.AsyncClient` 로 비동기 호출
2. 가격대 필터 (가게별 평균가 추정 — 카테고리별 룰 또는 학습된 모델)
3. 조합 최적화: 예산 안에서 별점/거리 가중치 합 최대화
4. 도보 시간 계산 (단순 거리 → 분 환산, 또는 카카오 Directions API)

### `app/services/ocr_service.py` ⚠ 비어있음
**구현 가이드**:
1. `image_url`에서 이미지 다운로드 (`httpx.AsyncClient`)
2. OCR 엔진 호출
   - **CLOVA OCR** (네이버, 한글 영수증 잘함, 유료)
   - **Tesseract** (오픈소스, 한글 학습 데이터 필요)
   - **EasyOCR** (PyTorch 기반)
3. 텍스트에서 상호명/금액 추출 (정규식 + 룰 기반)
4. 주소 → 좌표 변환 (카카오 Geocoding API)
5. 실패 시 `OcrFailed(message=...)` 예외 발생

---

## app/common/

### `app/common/exceptions.py`
HTTP 예외 클래스. FastAPI `HTTPException` 상속:
- `AIServerError(code, message, http_status)` — 기본
- `OcrFailed(message)` — 422
- `RecommendationFailed(message)` — 502

응답 바디 형태: `{"detail": {"code": "OCR_001", "message": "..."}}`

> 백엔드의 `CustomException` + `ErrorCode` 구조와 의도적으로 비슷하게 맞춤 (디버깅 일관성).

---

## tests/

### `tests/test_health.py`
헬스 체크 라우터 통합 테스트. `TestClient(app)` 사용 — 실제 서버 안 띄움.
- `GET /api/v1/health` → 200 + `{"status": "ok"}` 검증

추가 테스트는 같은 패턴으로 `tests/test_recommend.py`, `tests/test_ocr.py` 생성하면 됨.

---

## 구현 순서 권장

1. **`.env` 작성** + `pip install -r requirements-dev.txt`
2. **`uvicorn app.main:app --reload`** 로 띄워서 `/docs` Swagger 확인
3. **`tests/test_health.py`** 통과 확인 (`pytest -v`)
4. **`recommend_service.recommend()`** 본체 — 더미 데이터 먼저 반환 → 백엔드 연결 확인
5. **카카오 로컬 API 연동** — 실제 가게 데이터 받아오기
6. **조합 최적화** — 예산 안에서 최적 조합 알고리즘
7. **`ocr_service.parse()`** 본체 — OCR 엔진 결정 후 구현
8. **에러 처리** — 외부 API 실패 / 타임아웃 / 이미지 다운로드 실패 케이스
9. **로깅 강화** — 요청 ID 추적, 외부 호출 응답 시간 등

각 단계마다 백엔드의 `RecommendationService` / `ReceiptService`에서 실제로 호출해서 end-to-end 확인하면 빠름.
