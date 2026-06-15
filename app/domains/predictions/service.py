"""예산 초과 위험도 예측 서비스."""

from datetime import datetime, timezone

from app.domains.predictions.features import aggregate_receipts_by_room, build_room_features
from app.domains.predictions.model import predict_budget_risk
from app.domains.predictions.schema import BudgetRiskItem, BudgetRiskRequest, BudgetRiskResponse


def predict_budget_risks(request: BudgetRiskRequest) -> BudgetRiskResponse:
    receipt_stats_by_room = aggregate_receipts_by_room(request.receipts)
    items = []

    for room in request.rooms:
        features = build_room_features(room, receipt_stats_by_room.get(room.room_no, {}))
        prediction = predict_budget_risk(features)
        items.append(
            BudgetRiskItem(
                roomNo=room.room_no,
                roomName=room.room_name,
                riskLevel=prediction["risk_level"],
                riskScore=prediction["risk_score"],
                predictedFinalSpentAmount=prediction["predicted_final_spent_amount"],
                predictedBudgetUsageRate=prediction["predicted_budget_usage_rate"],
                recommendedNextSpendLimit=prediction["recommended_next_spend_limit"],
                reason=prediction["reason"],
            )
        )

    return BudgetRiskResponse(
        modelVersion="rule-v1",
        generatedAt=datetime.now(timezone.utc),
        items=sorted(items, key=lambda item: item.risk_score, reverse=True),
    )
