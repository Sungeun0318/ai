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
│       └── recommend/
│           ├── __init__.py
│           ├── router.py
│           ├── schema.py
│           └── service.py
└── tests/
    ├── __init__.py
    └── test_health.py
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

## tests

### `tests/test_health.py`

`GET /api/v1/health`가 200과 `{"status":"ok"}`를 반환하는지 확인한다.

실행:

```bash
pytest -v
```

## 방향 / 후속

- OCR은 백엔드 내장으로 확정(이 서버에서 미처리).
- 이 서버의 향후 목적은 학습시킨 Python 모델을 FastAPI로 제공하는 것이다. 신규 도메인은 `app/domains/` 아래에 추가한다.
- `recommend` 도메인은 학습 모델 기반 추천을 붙일 때 실제 구현하거나 정리한다.
