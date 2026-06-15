"""소비 인사이트 라우터 테스트."""

from fastapi.testclient import TestClient

from app.main import app
from app.domains.insights.schema import SpendingInsightRequest

client = TestClient(app)


def test_spending_insight_schema_accepts_backend_json_aliases():
    request = SpendingInsightRequest.model_validate(
        {
            "rooms": [
                {
                    "roomNo": 1,
                    "roomName": "강남 점심방",
                    "location": "서울 강남구",
                    "tag": "한식",
                    "totalBudget": 60000,
                    "memberCount": 3,
                    "status": "ENDED",
                }
            ],
            "receipts": [
                {
                    "receiptId": 10,
                    "roomNo": 1,
                    "amount": 8500,
                    "storeName": "국밥집",
                    "receiptType": "COMBINED",
                    "goodPriceMatched": True,
                    "receiptIssuedAt": "2026-06-15T12:10:00",
                }
            ],
            "recommendationInteractions": [
                {
                    "roomNo": 1,
                    "requestedTag": "한식",
                    "action": "CLICK",
                    "expectedPrice": 8500,
                    "createdAt": "2026-06-15T12:00:00",
                }
            ],
        }
    )

    assert request.rooms[0].room_no == 1
    assert request.rooms[0].total_budget == 60000
    assert request.receipts[0].receipt_id == 10
    assert request.receipts[0].good_price_matched is True
    assert request.recommendation_interactions[0].requested_tag == "한식"


def test_spending_summary_empty_payload():
    response = client.post(
        "/api/v1/insights/spending-summary",
        json={"rooms": [], "receipts": [], "recommendationInteractions": []},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["totalSpentAmount"] == 0
    assert body["summary"]["averageReceiptAmount"] == 0
    assert body["topRegions"] == []


def test_spending_summary_accepts_nullable_operating_fields():
    response = client.post(
        "/api/v1/insights/spending-summary",
        json={
            "rooms": [
                {
                    "roomNo": 1,
                    "roomName": None,
                    "location": None,
                    "totalBudget": None,
                }
            ],
            "receipts": [
                {
                    "receiptId": 1,
                    "roomNo": 1,
                    "amount": 1000,
                    "goodPriceMatched": False,
                }
            ],
            "recommendationInteractions": [
                {
                    "roomNo": 1,
                    "requestedTag": None,
                    "action": None,
                    "expectedPrice": None,
                }
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["totalSpentAmount"] == 1000
    assert body["topRegions"] == [{"region": "미분류", "spentAmount": 1000}]
    assert body["tagClicks"] == []


def test_spending_summary_calculates_basic_metrics():
    response = client.post(
        "/api/v1/insights/spending-summary",
        json={
            "rooms": [
                {
                    "roomNo": 1,
                    "roomName": "강남 점심방",
                    "location": "서울 강남구",
                    "tag": "한식",
                    "totalBudget": 10000,
                    "memberCount": 2,
                    "status": "ACTIVE",
                }
            ],
            "receipts": [
                {
                    "receiptId": 1,
                    "roomNo": 1,
                    "amount": 8000,
                    "storeName": "강남국밥",
                    "receiptType": "COMBINED",
                    "goodPriceMatched": True,
                },
                {
                    "receiptId": 2,
                    "roomNo": 1,
                    "amount": 5000,
                    "storeName": "강남카페",
                    "receiptType": "COMBINED",
                    "goodPriceMatched": False,
                },
            ],
            "recommendationInteractions": [
                {
                    "roomNo": 1,
                    "requestedTag": "한식",
                    "action": "CLICK",
                    "expectedPrice": 8000,
                }
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["totalSpentAmount"] == 13000
    assert body["summary"]["averageReceiptAmount"] == 6500
    assert body["summary"]["budgetOverRoomRate"] == 100.0
    assert body["summary"]["goodPriceUsageRate"] == 50.0
    assert body["topRegions"][0]["region"] == "서울 강남구"
    assert body["tagClicks"][0]["tag"] == "한식"


def test_spending_summary_groups_regions_tags_and_budget_usage():
    response = client.post(
        "/api/v1/insights/spending-summary",
        json={
            "rooms": [
                {
                    "roomNo": 1,
                    "roomName": "강남 점심방",
                    "location": "서울 강남구",
                    "totalBudget": 20000,
                },
                {
                    "roomNo": 2,
                    "roomName": "종로 저녁방",
                    "location": "서울 종로구",
                    "totalBudget": 10000,
                },
                {
                    "roomNo": 3,
                    "roomName": "예산 없는 방",
                    "location": "",
                    "totalBudget": 0,
                },
            ],
            "receipts": [
                {"receiptId": 1, "roomNo": 1, "amount": 5000, "goodPriceMatched": True},
                {"receiptId": 2, "roomNo": 1, "amount": 15000, "goodPriceMatched": True},
                {"receiptId": 3, "roomNo": 2, "amount": 12000, "goodPriceMatched": False},
                {"receiptId": 4, "roomNo": 99, "amount": 7000, "goodPriceMatched": False},
            ],
            "recommendationInteractions": [
                {"roomNo": 1, "requestedTag": "한식", "action": "CLICK"},
                {"roomNo": 1, "requestedTag": "한식", "action": "CLICK"},
                {"roomNo": 2, "requestedTag": "카페", "action": "CLICK"},
                {"roomNo": 2, "requestedTag": "카페", "action": "VIEW"},
                {"roomNo": 3, "requestedTag": None, "action": "CLICK"},
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["summary"]["totalSpentAmount"] == 39000
    assert body["summary"]["budgetOverRoomRate"] == 33.3
    assert body["topRegions"] == [
        {"region": "서울 강남구", "spentAmount": 20000},
        {"region": "서울 종로구", "spentAmount": 12000},
        {"region": "미분류", "spentAmount": 7000},
    ]
    assert body["tagClicks"] == [
        {"tag": "한식", "clickCount": 2},
        {"tag": "미분류", "clickCount": 1},
        {"tag": "카페", "clickCount": 1},
    ]
    assert body["highBudgetUsageRooms"][0]["roomNo"] == 2
    assert body["highBudgetUsageRooms"][0]["usageRate"] == 120.0
