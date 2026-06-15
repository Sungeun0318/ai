# 2차 기능 기획 - 예산 초과 위험도 예측 모델

## 담당/난이도

- 담당: 본인
- 난이도: 중간
- 핵심 기술: FastAPI, pandas, scikit-learn
- 목적: 방의 현재 지출 흐름을 기반으로 예산 초과 위험도를 예측한다.

## 기능 요약

관리자 소비 인사이트 화면에서 각 방의 예산 초과 위험도를 함께 보여준다.
Python AI 서버는 방별 예산, 현재 지출, 영수증 개수, 평균 결제 금액, 경과 시간 등을 feature로 만들어 위험도를 계산한다.

기술 용어:

- feature: 모델이 예측에 사용하는 입력 값이다. 예를 들면 `예산`, `현재 지출`, `영수증 개수`가 feature다.
- classification: 분류 모델이다. 결과를 `LOW`, `MEDIUM`, `HIGH`처럼 그룹으로 예측한다.
- regression: 회귀 모델이다. 결과를 숫자로 예측한다. 여기서는 `예상 최종 지출 금액`을 예측할 수 있다.

## 예측 결과

방마다 아래 값을 반환한다.

```text
예산 초과 위험도: LOW / MEDIUM / HIGH
예상 최종 지출 금액
예상 예산 사용률
권장 다음 소비 금액
위험 사유
```

예시:

```json
{
  "roomNo": 1,
  "roomName": "강남 점심방",
  "riskLevel": "HIGH",
  "riskScore": 87.2,
  "predictedFinalSpentAmount": 72000,
  "predictedBudgetUsageRate": 120.0,
  "recommendedNextSpendLimit": 2500,
  "reason": "현재 예산 사용률이 높고 평균 결제 금액 대비 남은 예산이 부족합니다."
}
```

## 데이터 준비

필수 데이터:

- rooms
  - roomNo
  - roomName
  - totalBudget
  - location
  - tag
  - memberCount
  - status
  - roomCreated
  - endedAt
- receipts
  - roomNo
  - amount
  - receiptType
  - goodPriceMatched
  - receiptIssuedAt
- budgets
  - roomNo
  - budgetAmount
  - submittedAt

샘플 데이터 권장:

```text
rooms: 1000개 이상
receipts: 5000개 이상
budgets: 2500개 이상
```

## Feature 설계

방별로 아래 feature를 만든다.

| feature | 설명 |
|---|---|
| `total_budget` | 방 전체 예산 |
| `member_count` | 방 참여 인원 |
| `spent_amount` | 현재까지 지출 합계 |
| `remaining_budget` | 남은 예산 |
| `receipt_count` | 영수증 개수 |
| `avg_receipt_amount` | 평균 결제 금액 |
| `max_receipt_amount` | 최대 결제 금액 |
| `good_price_usage_rate` | 착한가격업소 이용 비율 |
| `budget_usage_rate` | 현재 예산 사용률 |
| `elapsed_hours` | 방 생성 후 경과 시간 |
| `receipts_per_hour` | 시간당 영수증 등록 수 |

정답 라벨 후보:

```text
is_over_budget = spent_amount > total_budget
```

위험도 변환:

```text
LOW: riskScore < 40
MEDIUM: 40 <= riskScore < 70
HIGH: riskScore >= 70
```

## 모델 전략

### 1차 모델

빠르게 구현하기 위해 규칙 기반 점수 모델로 시작한다.

```text
riskScore =
  예산 사용률 점수 50점
  + 평균 결제 금액 대비 남은 예산 점수 25점
  + 지출 속도 점수 15점
  + 착한가격업소 미사용 점수 10점
```

장점:

- 데이터가 부족해도 동작한다.
- 결과 이유를 설명하기 쉽다.
- 발표에서 예측 로직을 설명하기 쉽다.

### 2차 모델

샘플 데이터가 충분해지면 scikit-learn 분류 모델을 붙인다.

후보:

```text
RandomForestClassifier
LogisticRegression
```

추천:

```text
RandomForestClassifier
```

이유:

- 숫자 feature 여러 개를 다루기 쉽다.
- feature 중요도를 확인할 수 있다.
- 규칙 기반보다 ML 모델 느낌이 잘 난다.

## AI 서버 API

### POST `/api/v1/predictions/budget-risk`

요청:

```json
{
  "rooms": [],
  "receipts": [],
  "budgets": []
}
```

응답:

```json
{
  "modelVersion": "rule-v1",
  "generatedAt": "2026-06-15T12:00:00",
  "items": [
    {
      "roomNo": 1,
      "roomName": "강남 점심방",
      "riskLevel": "HIGH",
      "riskScore": 87.2,
      "predictedFinalSpentAmount": 72000,
      "predictedBudgetUsageRate": 120.0,
      "recommendedNextSpendLimit": 2500,
      "reason": "현재 예산 사용률이 높고 평균 결제 금액 대비 남은 예산이 부족합니다."
    }
  ]
}
```

## 관리자 화면 반영

1차 소비 인사이트 화면 안에 `예산 초과 위험 방` 섹션을 추가한다.

표 컬럼:

```text
방 이름
총 예산
현재 지출
예상 최종 지출
위험도
권장 다음 소비 금액
위험 사유
```

위험도 색상:

```text
LOW: 초록
MEDIUM: 노랑
HIGH: 빨강
```

## 구현 스텝

### Step 1. 기획/데이터 컬럼 확정

작업:

- 샘플 데이터 컬럼 확인
- `rooms`, `receipts`, `budgets`에서 필요한 값 확정
- 빈 값 처리 정책 결정

검증:

- 샘플 JSON 10개 방 기준으로 feature를 수기로 계산해본다.

### Step 2. AI 도메인 구조 추가

추가 위치:

```text
app/domains/predictions/
  __init__.py
  router.py
  schema.py
  service.py
```

작업:

- `/api/v1/predictions/budget-risk` 라우터 추가
- request/response 스키마 작성
- `app/main.py`에 라우터 등록

검증:

```bash
curl -X POST http://localhost:8000/api/v1/predictions/budget-risk
```

### Step 3. pandas feature 생성

작업:

- rooms/receipts/budgets를 DataFrame으로 변환
- roomNo 기준으로 집계
- feature 테이블 생성

검증:

- feature 결과에 아래 컬럼이 모두 있는지 확인
  - `spent_amount`
  - `remaining_budget`
  - `receipt_count`
  - `avg_receipt_amount`
  - `budget_usage_rate`

### Step 4. 규칙 기반 위험도 모델 구현

작업:

- riskScore 계산
- LOW/MEDIUM/HIGH 변환
- reason 문구 생성
- recommendedNextSpendLimit 계산

검증:

- 예산 사용률 100% 초과 방은 HIGH로 나온다.
- 예산 사용률 40% 이하 방은 대부분 LOW로 나온다.
- 남은 예산이 평균 결제 금액보다 작으면 위험도가 올라간다.

### Step 5. scikit-learn 모델 후보 구현

작업:

- `RandomForestClassifier` 학습 코드 작성
- 샘플 데이터에서 `is_over_budget` 라벨 생성
- train/test split
- accuracy, precision, recall 출력

주의:

- 실제 서비스에서는 데이터가 부족할 수 있으므로 규칙 기반 모델을 기본값으로 둔다.
- ML 모델은 샘플 데이터가 충분할 때만 활성화한다.

검증:

```text
accuracy 0.7 이상이면 발표용으로 사용
0.7 미만이면 규칙 기반 모델을 최종 사용
```

현재 구현 결과:

```text
seed CSV 기준
random_state=42
RandomForestClassifier
accuracy=0.9950
```

주의:

```text
이 정확도는 샘플 데이터 기준이다.
실제 운영 데이터에서도 동일 정확도를 보장한다는 의미는 아니다.
```

### Step 6. 백엔드 admin API 연동

추가 후보:

```text
GET /admin/insights/budget-risk
```

작업:

- 백엔드가 rooms/receipts/budgets 조회
- AI 서버에 `POST /api/v1/predictions/budget-risk` 요청
- 결과를 관리자 웹으로 반환

검증:

```bash
curl -H "Authorization: Bearer {ADMIN_TOKEN}" \
  http://localhost:8080/admin/insights/budget-risk
```

### Step 7. 관리자 JSP 화면 표시

작업:

- 소비 인사이트 화면에 위험도 테이블 추가
- HIGH 위험도 방을 상단에 정렬
- 위험도 배지 색상 표시

검증:

- 관리자 페이지에서 HIGH/MEDIUM/LOW가 표시된다.
- 위험 사유가 비어 있지 않다.

### Step 8. 테스트/발표 자료 정리

작업:

- 샘플 데이터 기준 요청/응답 캡처
- 위험도 계산 전/후 화면 캡처
- PPT용 설명 문구 작성

검증:

- AI 서버 테스트 통과
- 백엔드 연동 통과
- 관리자 화면 렌더링 통과

## 완료 기준

- AI 서버 `POST /api/v1/predictions/budget-risk` 정상 응답
- 방별 위험도 `LOW/MEDIUM/HIGH` 반환
- 예상 최종 지출 금액 반환
- 권장 다음 소비 금액 반환
- 관리자 화면에 예산 초과 위험 방 목록 표시
- 빈 데이터 또는 일부 누락 데이터에서도 500 오류 없이 응답

## 발표 포인트

```text
Python에서 방별 소비 데이터를 feature로 변환하고,
예산 사용률과 지출 속도를 기반으로 예산 초과 위험도를 예측했습니다.
관리자는 위험도가 높은 방을 우선 확인할 수 있어 서비스 소비 흐름을 더 쉽게 파악할 수 있습니다.
```

## 포트폴리오 문구

```text
FastAPI와 pandas로 서비스 데이터를 분석하고,
scikit-learn 기반 예산 초과 위험도 예측 모델을 설계했습니다.
관리자 대시보드에서 방별 위험도를 LOW/MEDIUM/HIGH로 시각화해 운영자가 소비 패턴을 빠르게 파악할 수 있도록 구현했습니다.
```
