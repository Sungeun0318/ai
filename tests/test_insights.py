"""소비 인사이트 라우터 테스트."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


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
