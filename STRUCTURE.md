# Python AI 서버 파일 구조 & 기능 설명

> `ai/` 디렉터리의 모든 파일이 어떤 역할인지, 어떤 내용을 담아야 하는지 정리.
> **2026-05-30 기준**: 도메인 기반(domain-based) 구조로 재배치. 추천은 착한가격업소 API 기준, OCR은 영수증 파싱 + 착한가격업소 매칭 후보 반환 기준.

---

## 전체 구조

```
ai/
├── .gitignore
├── .gitattributes
├── README.md
├── STRUCTURE.md               (본 문서)
├── requirements.txt           런타임 의존성
├── requirements-dev.txt       pytest, ruff, mypy
├── .env.example
├── app/
│   ├── __init__.py
│   ├── main.py                FastAPI 진입점 + CORS + 도메인 라우터 등록
│   │
│   ├── core/                  ⭐ 전 도메인 공용 인프라
│   │   ├── __init__.py
│   │   ├── config.py          pydantic-settings — .env 자동 로드
│   │   ├── logging.py         로깅 설정
│   │   ├── exceptions.py      AIServerError / OcrFailed / RecommendationFailed
│   │   └── health.py          GET /api/v1/health  (구현 완료)
│   │
│   ├── domains/               ⭐ 도메인 폴더 — 5인 협업 시 각자 1개씩 owner
│   │   ├── __init__.py
│   │   │
│   │   ├── recommend/         👤 착한가격업소 추천 담당
│   │   │   ├── __init__.py    → from .router import router
│   │   │   ├── router.py      ⚠ GET /api/v1/recommend  (구현 예정)
│   │   │   ├── service.py     ⚠ 추천 알고리즘 (구현 예정)
│   │   │   ├── schema.py      Pydantic — RecommendResponse / Place
│   │   │   └── repository.py  (옵션) 착한가격업소 API 클라이언트
│   │   │
│   │   └── ocr/               👤 OCR 담당
│   │       ├── __init__.py    → from .router import router
│   │       ├── router.py      ⚠ POST /api/v1/ocr  (구현 예정)
│   │       ├── service.py     ⚠ OCR 오케스트레이션 (구현 예정)
│   │       ├── schema.py      Pydantic — OcrRequest / OcrResponse
│   │       └── parser.py      (옵션) 정규식·룰 기반 텍스트 추출
│   │
│   └── shared/                (옵션, 첫 사용 시 생성) 도메인 간 공유 유틸
│       ├── good_price_client.py 착한가격업소 API httpx 클라이언트
│       ├── kakao_client.py    지오코딩 후보 API 클라이언트
│       ├── s3_client.py       S3 다운로드
│       └── geo_utils.py       Haversine 거리 등
│
└── tests/
    ├── __init__.py
    └── test_health.py         GET /api/v1/health 통합 테스트
```

---

## 의존성 방향 (import 규칙)

```
domains/*  →  shared/  →  core/
   ↑
   └─ domains끼리 직접 import 금지
      공통 호출 필요 시 shared/ 로 빼서 재사용
```

- `domains/recommend/` ↔ `domains/ocr/` 직접 호출 ❌
- `core/`는 누구나 import 가능
- `shared/`는 도메인이 공유 가능, 도메인을 import ❌
- 외부 패키지(`fastapi`, `httpx`, `pydantic`)는 어디서나 OK

---

## 라우터 등록 흐름

`app/main.py`가 각 도메인의 `__init__.py`에서 `router`를 가져와 `/api/v1` prefix로 등록.

```python
# app/main.py
from app.core import health
from app.domains import recommend, ocr

app.include_router(health.router,    prefix="/api/v1", tags=["health"])
app.include_router(recommend.router, prefix="/api/v1", tags=["recommend"])
app.include_router(ocr.router,       prefix="/api/v1", tags=["ocr"])
```

도메인을 추가하려면:
1. `app/domains/<new_domain>/` 폴더 생성
2. `router.py`, `service.py`, `schema.py` 작성
3. `__init__.py`에 `from .router import router`
4. `app/main.py`에 한 줄 추가

---

## 루트 파일

### `requirements.txt`
런타임 의존성:
- `fastapi==0.115.5`, `uvicorn[standard]==0.32.1`
- `pydantic==2.9.2`, `pydantic-settings==2.6.1`
- `httpx==0.27.2`
- `python-multipart==0.0.17`

주석 처리된 후보:
- OCR: `pytesseract` / `easyocr` / `Pillow`
- 추천 알고리즘: `numpy` / `pandas` / `scikit-learn`

### `requirements-dev.txt`
- `pytest==8.3.4`, `pytest-asyncio==0.24.0`
- `ruff==0.8.4` — 린터/포매터
- `mypy==1.13.0` — 정적 타입 체크

### `.env.example`
서버 / 백엔드 연동 / 외부 API / AWS S3 / 로깅 키.

---

## app/main.py
FastAPI 진입점. **하는 일**:
1. `FastAPI()` 인스턴스 생성 (title/version)
2. CORS 미들웨어 등록 (개발용 전체 허용)
3. 도메인 라우터 등록 (`health`, `recommend`, `ocr`) — 모두 `/api/v1` prefix
- 실행: `uvicorn app.main:app --reload --port 8000`

---

## app/core/ — 전 도메인 공용 인프라

### `core/config.py`
`Settings(BaseSettings)` 클래스. `pydantic-settings`로 `.env` 자동 로드.
- `extra="ignore"` — 정의 안 된 키는 무시
- 사용: `from app.core.config import settings; settings.kakao_rest_api_key`

### `core/logging.py`
`configure_logging()` 함수. `settings.log_level` 기반 표준 로깅 설정.

### `core/exceptions.py`
공통 예외 (이전 `common/exceptions.py`에서 이동).
- `AIServerError(code, message, http_status)` — 기본
- `OcrFailed(message)` — 422
- `RecommendationFailed(message)` — 502
- 응답 바디: `{"detail": {"code": "OCR_001", "message": "..."}}`
- 백엔드의 `CustomException + ErrorCode` 구조와 의도적으로 비슷하게 맞춤.

### `core/health.py`
헬스 체크 라우터. **구현 완료**.
- `GET /api/v1/health` → `{"status": "ok"}`

---

## app/domains/ — 도메인별 비즈니스 로직

각 도메인은 동일한 패턴: **router.py + service.py + schema.py** (+ 선택적 repository/parser).

### `domains/recommend/`
- **`router.py`** ⚠ — `GET /api/v1/recommend` 엔드포인트
  - Query: `room_no, budget, tags(콤마 구분), lat, lng`
- **`service.py`** ⚠ — 추천 오케스트레이션
  1. 지역/좌표 기준 착한가격업소 후보 수집
  2. 앱 태그(`한식 / 양식 / 일식 / 중식 / 기타 요식업`)와 업종 매핑
  3. 남은 예산 기준 가격대 필터
  4. 거리/가격/태그 적합도 기반 정렬
  5. 도보 시간 계산
- **`schema.py`** — `RecommendResponse(roomNo, totalBudget, places: list[Place])`
  - `populate_by_name=True` + `Field(alias=...)` 으로 camelCase JSON ↔ snake_case 파이썬
  - 백엔드 `RecommendationResponse` (Java record) 와 1:1 매핑
  - `Place.category`는 `한식 / 양식 / 일식 / 중식 / 기타 요식업` 중 하나를 우선 사용

### `domains/ocr/`
- **`router.py`** ⚠ — `POST /api/v1/ocr`
  - Body: `OcrRequest(receiptId, imageUrl)`
- **`service.py`** ⚠ — OCR 처리
  1. `image_url`에서 이미지 다운로드 (httpx)
  2. OCR 엔진 호출 (CLOVA / Tesseract / EasyOCR — 선택)
  3. 텍스트 → 상호명/금액 정규식 추출
  4. 주소 → 좌표 변환 (카카오 Geocoding)
  5. 상호명/주소를 착한가격업소 데이터와 비교해 매칭 후보 생성
  6. 실패 시 `OcrFailed(message=...)` 발생
- **`schema.py`** — `OcrRequest` / `OcrResponse`
  - 백엔드 `Receipt.applyOcrResult(...)` 파라미터와 매칭
  - 착한가격업소 매칭 필드는 백엔드 `receipts.good_price_*` 컬럼과 매칭

---

## app/shared/ — 도메인 공유 유틸 (옵션)

처음엔 비어있어도 됨. 도메인끼리 같은 외부 호출이 중복되기 시작하면 옮긴다.

권장 분리 시점:
- 착한가격업소 API 클라이언트가 recommend + ocr 둘 다에서 호출됨
- 카카오 지오코딩 클라이언트가 ocr + 추천 기준 좌표 보정에 같이 쓰임
- S3 다운로드가 ocr + future analysis 양쪽에서 필요
- 위경도 계산이 recommend + future analysis 양쪽

---

## tests/

### `tests/test_health.py`
헬스 체크 라우터 통합 테스트. `TestClient(app)` 사용.
- `GET /api/v1/health` → 200 + `{"status": "ok"}`

도메인 테스트는 `tests/recommend/test_*.py`, `tests/ocr/test_*.py` 패턴으로 분리 권장.

---

## 5명 협업 규칙

### 1. 도메인 오너
- `domains/recommend/` → 착한가격업소 추천 담당
- `domains/ocr/` → OCR 담당
- `core/`, `shared/` → 모두 가능, PR은 최소 2명 승인

### 2. PR 범위
- 1 PR = 1 도메인 (도메인 넘나드는 변경 금지 — 자르거나 shared/ 분리)

### 3. 코드 스타일 (강제)
- `ruff check .` + `ruff format .`
- `mypy app/`
- pre-commit hook 으로 자동 실행 권장

### 4. 테스트 의무
- 도메인 PR엔 `tests/<domain>/` 추가 필수
- `pytest -v` 통과 안 하면 merge 금지

### 5. 커밋 컨벤션
- `backend/COMMIT_CONVENTION.md` 동일 적용
- 예: `Feat: recommend 도메인 스코어링 모델 추가`

---

## 구현 순서 권장

1. **`.env` 작성** + `pip install -r requirements-dev.txt`
2. **`uvicorn app.main:app --reload`** 로 띄워서 `/docs` Swagger 확인
3. **`tests/test_health.py`** 통과 확인 (`pytest -v`)
4. **`domains/recommend/service.py`** 본체 — 착한가격업소 더미 데이터 먼저 반환 → 백엔드 연결 확인
5. **착한가격업소 API 연동** — `shared/good_price_client.py` 생성 시점
6. **`domains/ocr/service.py`** 본체 — OCR 엔진 결정 후 구현
7. **OCR 결과와 착한가격업소 매칭** — 상호명/주소 유사도 기준
8. **에러 처리** — 외부 API 실패 / 타임아웃 / 이미지 다운로드 실패
9. **로깅 강화** — 요청 ID 추적, 외부 호출 응답 시간 등
