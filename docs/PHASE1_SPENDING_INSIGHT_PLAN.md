# 1차 기능 기획 - 관리자 소비 인사이트 분석

## 담당/난이도

- 담당: 다른 팀원
- 난이도: 쉬움
- 핵심 기술: FastAPI, pandas, 기본 통계
- 목적: 관리자 페이지에서 전체 서비스 소비 현황을 한눈에 확인한다.

## 기능 요약

관리자 대시보드에서 `통계 보기` 버튼을 누르면 소비 인사이트 화면으로 이동한다.
백엔드는 방/예산/영수증/추천 로그 데이터를 수집해 AI 서버로 전달하고, AI 서버는 pandas로 통계를 계산해 반환한다.

```text
관리자 JSP
→ beggar-admin
→ beggar-backend /admin/insights/summary
→ beggar-ai /api/v1/insights/spending-summary
→ pandas 통계 계산
→ 관리자 화면 렌더링
```

## 화면 목표

관리자 페이지에 신규 화면을 만든다.

```text
GET /admin/insights
```

화면 구성:

- 요약 카드 4개
  - 총 지출 금액
  - 평균 결제 금액
  - 예산 초과 방 비율
  - 착한가격업소 이용률
- 차트 2개
  - 지역별 총 지출 TOP 5
  - 태그별 추천 클릭 수
- 표 1개
  - 예산 사용률 높은 방 TOP 10

## 입력 데이터

백엔드가 AI 서버에 JSON으로 전달한다.

```json
{
  "rooms": [
    {
      "roomNo": 1,
      "roomName": "강남 점심방",
      "location": "서울 강남구",
      "tag": "한식",
      "totalBudget": 60000,
      "memberCount": 3,
      "status": "ENDED"
    }
  ],
  "receipts": [
    {
      "receiptId": 10,
      "roomNo": 1,
      "amount": 8500,
      "storeName": "국밥집",
      "receiptType": "COMBINED",
      "goodPriceMatched": true,
      "receiptIssuedAt": "2026-06-15T12:10:00"
    }
  ],
  "recommendationInteractions": [
    {
      "roomNo": 1,
      "requestedTag": "한식",
      "action": "CLICK",
      "expectedPrice": 8500,
      "createdAt": "2026-06-15T12:00:00"
    }
  ]
}
```

## AI 서버 API

### POST `/api/v1/insights/spending-summary`

요청:

```json
{
  "rooms": [],
  "receipts": [],
  "recommendationInteractions": []
}
```

응답:

```json
{
  "summary": {
    "totalSpentAmount": 12500000,
    "averageReceiptAmount": 8750,
    "budgetOverRoomRate": 18.5,
    "goodPriceUsageRate": 42.3
  },
  "topRegions": [
    {
      "region": "서울 강남구",
      "spentAmount": 3200000
    }
  ],
  "tagClicks": [
    {
      "tag": "한식",
      "clickCount": 320
    }
  ],
  "highBudgetUsageRooms": [
    {
      "roomNo": 1,
      "roomName": "강남 점심방",
      "totalBudget": 60000,
      "spentAmount": 58000,
      "usageRate": 96.7
    }
  ]
}
```

## 분석 로직

### 총 지출 금액

```text
receipts.amount 합계
```

### 평균 결제 금액

```text
receipts.amount 평균
```

### 예산 초과 방 비율

```text
방별 지출 합계 > rooms.totalBudget 인 방 수 / 전체 방 수 * 100
```

### 착한가격업소 이용률

```text
goodPriceMatched=true 영수증 수 / 전체 영수증 수 * 100
```

### 지역별 총 지출

```text
rooms.location 기준으로 receipts.amount 그룹 합계
```

### 태그별 추천 클릭 수

```text
recommendationInteractions.action = CLICK
requestedTag 기준 count
```

## 구현 스텝

### Step 1. AI 도메인 구조 추가

추가 위치:

```text
app/domains/insights/
  __init__.py
  router.py
  schema.py
  service.py
```

작업:

- `insights` 라우터 생성
- `app/main.py`에 `/api/v1` prefix로 등록
- 기본 응답 스텁 작성

검증:

```bash
curl -X POST http://localhost:8000/api/v1/insights/spending-summary
```

### Step 2. Pydantic 스키마 작성

작업:

- `RoomInsightItem`
- `ReceiptInsightItem`
- `RecommendationInteractionItem`
- `SpendingInsightRequest`
- `SpendingInsightResponse`

검증:

- Swagger에서 request/response 스키마 확인

### Step 3. pandas 분석 로직 작성

작업:

- 입력 리스트를 `DataFrame`으로 변환
- 빈 데이터 방어 처리
- 요약 카드 값 계산
- 지역별/태그별/방별 통계 계산

검증:

- 테스트 JSON으로 API 호출
- 계산 결과가 수기로 계산한 값과 일치하는지 확인

### Step 4. 백엔드 admin API 추가

추가 후보:

```text
GET /admin/insights/summary
```

작업:

- 운영 DB에서 rooms/receipts/recommendation_interactions 조회
- AI 서버 `POST /api/v1/insights/spending-summary` 호출
- AI 응답을 그대로 관리자 웹에 반환

검증:

```bash
curl -H "Authorization: Bearer {ADMIN_TOKEN}" \
  http://localhost:8080/admin/insights/summary
```

### Step 5. 관리자 JSP 화면 추가

작업:

- 대시보드에 `통계 보기` 버튼 추가
- `GET /admin/insights` 화면 추가
- 카드/차트/표 렌더링

검증:

- 관리자 로그인
- 대시보드에서 `통계 보기` 클릭
- 소비 인사이트 화면 표시 확인

## 완료 기준

- AI 서버 `POST /api/v1/insights/spending-summary` 정상 응답
- 백엔드 `GET /admin/insights/summary` 정상 응답
- 관리자 JSP에서 통계 카드 4개 표시
- 지역별 TOP 5, 태그별 클릭 수, 예산 사용률 높은 방 TOP 10 표시
- 데이터가 비어 있어도 500 오류 없이 0 또는 빈 배열 반환

## 발표 포인트

```text
Python pandas를 사용해 서비스의 영수증/예산/추천 로그 데이터를 분석하고,
관리자가 전체 소비 흐름을 확인할 수 있는 인사이트 대시보드를 구현했습니다.
```
