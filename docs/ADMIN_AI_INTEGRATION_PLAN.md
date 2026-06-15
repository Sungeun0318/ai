# 관리자 AI 기능 연동 기획

## 목표

AI 서버에 구현된 1차/2차 기능을 관리자 웹에서 확인할 수 있게 연결한다.

- 1차 기능: 소비 인사이트 통계 화면
- 2차 기능: 예산 초과 위험 방 분석 화면

기술 용어:

- API gateway 역할: 관리자 웹이 직접 AI 서버를 부르지 않고, 백엔드가 중간에서 데이터를 모아 AI 서버에 전달하는 구조다.
- DTO: 화면 또는 API 응답에 맞춰 데이터를 담는 객체다.
- 서버 투 서버 호출: 브라우저가 아닌 서버가 다른 서버 API를 호출하는 방식이다.

## 전체 흐름

```text
관리자 JSP
→ beggar-admin
→ beggar-backend /admin/ai/**
→ beggar-ai /api/v1/**
→ 분석/예측 결과 반환
→ 관리자 JSP 렌더링
```

관리자 웹은 DB를 직접 분석하지 않는다.
운영 DB 조회와 AI 서버 호출은 백엔드가 담당한다.

## 화면 구성

### 1차: 소비 인사이트

관리자 메뉴:

```text
대시보드 → 통계 보기
```

관리자 URL:

```text
GET /admin/insights
```

화면 구성:

- 요약 카드
  - 총 지출 금액
  - 평균 결제 금액
  - 예산 초과 방 비율
  - 착한가격업소 이용률
- 차트
  - 지역별 지출 TOP 5
  - 태그별 추천 클릭 수
- 표
  - 예산 사용률 높은 방 TOP 10

백엔드 API:

```text
GET /admin/ai/insights/spending-summary
```

AI API:

```text
POST /api/v1/insights/spending-summary
```

### 2차: 예산 초과 위험 방 분석

관리자 메뉴:

```text
대시보드 → 예측 분석
```

관리자 URL:

```text
GET /admin/budget-risk
```

화면 구성:

- 요약 카드
  - HIGH 위험 방 수
  - MEDIUM 위험 방 수
  - LOW 위험 방 수
  - 평균 예산 사용률
- 필터
  - 위험도
  - 지역
  - 방 상태
- 표
  - 방 번호
  - 방 이름
  - 지역
  - 총 예산
  - 현재 지출
  - 예상 최종 지출
  - 예측 예산 사용률
  - 위험도
  - 권장 다음 소비 금액
  - 위험 사유

백엔드 API:

```text
GET /admin/ai/predictions/budget-risk
```

AI API:

```text
POST /api/v1/predictions/budget-risk
```

## 백엔드 작업 계획

### Step 1. AI 서버 URL 설정

추가 설정:

```properties
ai.server.url=http://localhost:8000
```

배포 환경에서는 Elastic Beanstalk 환경 변수로 주입한다.

검증:

```bash
curl http://localhost:8000/api/v1/health
```

### Step 2. AI WebClient 추가

작업:

- `AiClientConfig` 생성
- `WebClient aiWebClient` 빈 등록
- timeout 설정

검증:

- 백엔드 기동 시 빈 생성 오류가 없는지 확인

### Step 3. 1차 통계용 데이터 조회

작업:

- rooms 조회
- receipts 조회
- recommendation_interactions 조회
- AI 요청 DTO로 변환

주의:

- 삭제된 방이나 숨김 멤버 정책은 기존 관리자 조회 기준을 따른다.
- `receiptIssuedAt`이 없으면 `createdAt`을 임시로 사용할 수 있다.

검증:

- 백엔드 단위 테스트 또는 로그로 AI 요청 JSON 확인

### Step 4. 1차 백엔드 API 추가

추가:

```text
GET /admin/ai/insights/spending-summary
```

작업:

- 관리자 JWT 보호 유지
- DB 데이터 조회
- AI 서버 `POST /api/v1/insights/spending-summary` 호출
- AI 응답 그대로 반환

검증:

```bash
curl -H "Authorization: Bearer {ADMIN_TOKEN}" \
  http://localhost:8080/admin/ai/insights/spending-summary
```

### Step 5. 2차 예측용 데이터 조회

작업:

- rooms 조회
- receipts 조회
- budgets 조회
- AI 요청 DTO로 변환

주의:

- 예산이 없는 방은 예측 대상에서 제외하거나 LOW로 처리한다.
- 운영 화면에서는 진행 중인 방을 우선 표시한다.

검증:

- 방별 `totalBudget`, `spentAmount`, `budgetAmount`가 맞는지 샘플 3개 방으로 확인

### Step 6. 2차 백엔드 API 추가

추가:

```text
GET /admin/ai/predictions/budget-risk
```

작업:

- 관리자 JWT 보호 유지
- DB 데이터 조회
- AI 서버 `POST /api/v1/predictions/budget-risk` 호출
- AI 응답 그대로 반환

검증:

```bash
curl -H "Authorization: Bearer {ADMIN_TOKEN}" \
  http://localhost:8080/admin/ai/predictions/budget-risk
```

## 관리자 JSP 작업 계획

### Step 7. 1차 소비 인사이트 화면 추가

작업:

- 대시보드에 `통계 보기` 버튼 추가
- `AdminInsightController` 추가
- `/admin/insights` JSP 추가
- 카드/차트/표 렌더링

검증:

- 관리자 로그인
- 대시보드에서 `통계 보기` 클릭
- 소비 인사이트 화면 표시

### Step 8. 2차 위험 방 분석 화면 추가

작업:

- 대시보드에 `예측 분석` 버튼 추가
- `AdminBudgetRiskController` 추가
- `/admin/budget-risk` JSP 추가
- 위험도 필터와 테이블 렌더링

검증:

- 관리자 로그인
- 대시보드에서 `예측 분석` 클릭
- HIGH/MEDIUM/LOW 방 목록 표시

## 검증 순서

1. AI 서버 단독 검증
2. 백엔드에서 AI 서버 호출 검증
3. 관리자 웹에서 백엔드 API 호출 검증
4. JSP 화면 렌더링 검증
5. 배포 환경 변수 확인
6. 운영 DB 샘플 데이터 기준 결과 확인

## 완료 기준

### 1차

- 관리자 화면에서 소비 인사이트 카드 4개가 보인다.
- 지역별 지출 TOP 5가 보인다.
- 태그별 추천 클릭 수가 보인다.
- 예산 사용률 높은 방 TOP 10이 보인다.

### 2차

- 관리자 화면에서 위험도별 방 개수가 보인다.
- HIGH/MEDIUM/LOW 위험 방 목록이 보인다.
- 방별 위험 사유가 보인다.
- 위험도 필터가 동작한다.

## 발표 포인트

1차:

```text
운영자가 전체 소비 흐름을 확인할 수 있도록 방, 영수증, 추천 로그 데이터를 pandas로 집계했습니다.
```

2차:

```text
방별 예산, 지출, 영수증 패턴을 feature로 변환하고 예산 초과 위험도를 예측해 관리자가 위험 방을 먼저 확인할 수 있게 했습니다.
```
