# beggar-ai

거지 우정 수호대 FastAPI AI 서버다.

## 현재 상태

- FastAPI + Uvicorn 기반.
- `/api/v1/health` 구현 완료.
- `/api/v1/recommend` 도메인은 라우터/스키마/서비스 골격만 있는 스텁이다. 실제 추천은 현재 Spring 백엔드가 직접 처리한다.
- **OCR은 이 서버에서 처리하지 않는다.** 영수증 OCR(Google Vision + Groq)은 Spring 백엔드가 자체적으로 수행하고 결과를 DB에 직접 반영한다. (과거에 있던 AI OCR 도메인/콜백은 사용하지 않기로 하여 제거됨)

## 방향 (예정)

- 이 서버의 향후 목적은 **학습시킨 Python 모델을 FastAPI로 제공**하는 것이다 (추천 고도화 또는 별도 예측 모델).
- 백엔드가 이 서버를 호출하는 형태가 되면 백엔드의 `aiServerWebClient`(base-url = `ai-server.base-url`)로 연동한다.

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
BACKEND_BASE_URL=http://localhost:8080   # 향후 모델→백엔드 연동 후보
KAKAO_REST_API_KEY=후속 추천/지오코딩 후보
AWS_*=S3 접근 후보
```

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
| `GET` | `/api/v1/recommend` | 스텁 | 후속 AI 모델 도메인 후보 |

## 추천 도메인

현재 추천은 AI 서버가 아니라 Spring 백엔드 `RecommendationService`가 맡는다.

Spring API:

```text
GET /rooms/{roomNo}/recommend?tag=&region=&lat=&lng=&radius=
```

AI `recommend` 도메인은 후속 작업에서 학습 모델 기반 추천 등을 붙일 후보 영역이다.

## 테스트

```bash
pytest -v
```

## 참고

- 전체 기능 명세: `../docs/APP_FEATURES.md`
- 백엔드 README: `../backend/README.md` (OCR은 백엔드 내장)
