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
│       ├── insights/
│       │   ├── __init__.py
│       │   ├── router.py
│       │   ├── schema.py
│       │   └── service.py
│       ├── predictions/
│       │   ├── __init__.py
│       │   ├── router.py
│       │   ├── schema.py
│       │   ├── features.py
│       │   ├── model.py
│       │   └── service.py
│       └── recommend/
│           ├── __init__.py
│           ├── router.py
│           ├── schema.py
│           └── service.py
├── data/
│   ├── sample/
│   └── models/
├── scripts/
│   ├── generate_sample_receipts.py
│   └── train_budget_risk_model.py
└── tests/
    ├── __init__.py
    ├── test_health.py
    ├── test_insights.py
    └── test_predictions.py
```

> OCR은 이 서버에서 처리하지 않는다. 영수증 OCR은 Spring 백엔드가 자체(Google Vision + Groq)로 수행한다. 과거 `domains/ocr`는 미사용으로 제거됨.

## app/main.py

FastAPI 앱 진입점이다.

역할:

- `.env` 로드.
- `FastAPI(title=settings.app_name)` 생성.
- CORS 전체 허용. 현재는 로컬 디버깅 편의용이다.
- `/api/v1` prefix로 health, recommend 라우터 등록.

등록 라우터:

```text
/api/v1/health
/api/v1/recommend
/api/v1/insights/spending-summary
/api/v1/predictions/budget-risk
```

## core

### `core/config.py`

`pydantic-settings` 기반 설정.

주요 설정:

- `app_name`, `app_env`, `host`, `port`
- `backend_base_url`, `backend_api_key` — 향후 모델→백엔드 연동 후보
- `kakao_rest_api_key`, `naver_client_id`, `naver_client_secret`
- `aws_access_key_id`, `aws_secret_access_key`, `aws_region`, `s3_bucket`
- `log_level`

### `core/health.py`

```text
GET /api/v1/health
```

응답:

```json
{"status":"ok"}
```

### `core/exceptions.py`

AI 서버 공통 예외를 정의한다.

- `AIServerError`
- `RecommendationFailed`

### `core/logging.py`

로그 설정 함수가 있는 공통 모듈이다.

## domains/recommend

추천 도메인이다. 현재는 후속 고도화용 스텁이다.

### `recommend/router.py`

라우터 객체만 있고 실제 `GET /recommend` 핸들러는 TODO 주석 상태다.

### `recommend/schema.py`

Spring `RecommendationResponse`와 맞추기 위한 Pydantic 모델 후보가 있다.

- `RecommendResponse`
- `Place`

### `recommend/service.py`

추천 알고리즘 구현 TODO만 있다. 현재 실제 추천은 백엔드 `RecommendationService`가 처리한다.

## domains/insights

관리자 소비 인사이트 도메인이다.

### `insights/router.py`

```text
POST /api/v1/insights/spending-summary
```

역할:

- 방/영수증/추천 로그 데이터를 입력받는다.
- `service.build_spending_summary()`로 통계를 계산한다.

### `insights/schema.py`

역할:

- 요청 스키마
  - `SpendingInsightRequest`
  - `RoomInsightItem`
  - `ReceiptInsightItem`
  - `RecommendationInteractionItem`
- 응답 스키마
  - `SpendingInsightResponse`
  - `SpendingSummary`
  - `RegionSpending`
  - `TagClickCount`
  - `HighBudgetUsageRoom`

### `insights/service.py`

초기 버전은 순수 Python으로 기본 통계를 계산한다.
후속 구현에서 pandas 기반 분석으로 확장한다.

## domains/predictions

예산 초과 위험도 예측 도메인이다.

### `predictions/router.py`

```text
POST /api/v1/predictions/budget-risk
```

### `predictions/schema.py`

방/영수증/예산 입력과 위험도 응답 모델을 정의한다.

### `predictions/features.py`

방별 feature를 만든다.

feature는 모델이 예측에 사용하는 입력값이다.

예:

- 현재 지출 합계
- 영수증 개수
- 평균 결제 금액
- 예산 사용률
- 착한가격업소 이용률

### `predictions/model.py`

초기 버전은 규칙 기반 위험도 모델이다.

후속 구현에서 scikit-learn 모델로 교체하거나 병행한다.

### `predictions/service.py`

feature 생성과 모델 예측 결과를 조립한다.

## data / scripts

### `data/sample`

샘플 JSON, CSV, SQL 결과물을 두는 후보 폴더다.
대용량 데이터는 git에 올리지 않는다.

### `data/models`

학습된 모델 파일 후보 폴더다.
대용량 모델 파일은 git에 올리지 않는다.

### `scripts/generate_sample_receipts.py`

영수증 샘플 SQL 생성 스크립트 자리다.

### `scripts/train_budget_risk_model.py`

예산 위험도 ML 모델 학습 스크립트 자리다.

## tests

### `tests/test_health.py`

`GET /api/v1/health`가 200과 `{"status":"ok"}`를 반환하는지 확인한다.

실행:

```bash
pytest -v
```

주의:

```text
현재 requirements는 Python 3.11~3.13 권장.
Python 3.14 가상환경에서는 pydantic-core 빌드가 실패할 수 있다.
```

## 방향 / 후속

- OCR은 백엔드 내장으로 확정(이 서버에서 미처리).
- 이 서버의 향후 목적은 학습시킨 Python 모델을 FastAPI로 제공하는 것이다. 신규 도메인은 `app/domains/` 아래에 추가한다.
- `recommend` 도메인은 학습 모델 기반 추천을 붙일 때 실제 구현하거나 정리한다.
