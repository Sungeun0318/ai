"""예산 위험도 예측 라우터 테스트."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_budget_risk_empty_payload():
    response = client.post(
        "/api/v1/predictions/budget-risk",
        json={"rooms": [], "receipts": [], "budgets": []},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["modelVersion"] == "rule-v1"
    assert body["items"] == []


def test_budget_risk_marks_over_budget_room_high():
    response = client.post(
        "/api/v1/predictions/budget-risk",
        json={
            "rooms": [
                {
                    "roomNo": 1,
                    "roomName": "강남 점심방",
                    "totalBudget": 10000,
                    "memberCount": 2,
                    "status": "ACTIVE",
                }
            ],
            "receipts": [
                {"roomNo": 1, "amount": 9000, "receiptType": "COMBINED", "goodPriceMatched": False},
                {"roomNo": 1, "amount": 5000, "receiptType": "COMBINED", "goodPriceMatched": False},
            ],
            "budgets": [],
        },
    )

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["riskLevel"] == "HIGH"
    assert item["riskScore"] >= 70
    assert item["recommendedNextSpendLimit"] == 0
