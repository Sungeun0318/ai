"""예산 위험도 예측 feature 생성."""

from collections import defaultdict

from app.domains.predictions.schema import BudgetRiskReceiptItem, BudgetRiskRoomItem


def aggregate_receipts_by_room(receipts: list[BudgetRiskReceiptItem]) -> dict[int, dict]:
    grouped: dict[int, dict] = defaultdict(
        lambda: {
            "spent_amount": 0,
            "receipt_count": 0,
            "max_receipt_amount": 0,
            "good_price_count": 0,
        }
    )

    for receipt in receipts:
        amount = max(receipt.amount, 0)
        row = grouped[receipt.room_no]
        row["spent_amount"] += amount
        row["receipt_count"] += 1
        row["max_receipt_amount"] = max(row["max_receipt_amount"], amount)
        if receipt.good_price_matched:
            row["good_price_count"] += 1

    for row in grouped.values():
        count = row["receipt_count"]
        row["avg_receipt_amount"] = int(row["spent_amount"] / count) if count else 0
        row["good_price_usage_rate"] = round((row["good_price_count"] / count) * 100, 1) if count else 0.0

    return grouped


def build_room_features(room: BudgetRiskRoomItem, receipt_stats: dict) -> dict:
    total_budget = room.total_budget or 0
    spent_amount = receipt_stats.get("spent_amount", 0)
    remaining_budget = max(total_budget - spent_amount, 0)
    budget_usage_rate = round((spent_amount / total_budget) * 100, 1) if total_budget > 0 else 0.0

    return {
        "room_no": room.room_no,
        "room_name": room.room_name,
        "total_budget": total_budget,
        "member_count": room.member_count or 1,
        "spent_amount": spent_amount,
        "remaining_budget": remaining_budget,
        "receipt_count": receipt_stats.get("receipt_count", 0),
        "avg_receipt_amount": receipt_stats.get("avg_receipt_amount", 0),
        "max_receipt_amount": receipt_stats.get("max_receipt_amount", 0),
        "good_price_usage_rate": receipt_stats.get("good_price_usage_rate", 0.0),
        "budget_usage_rate": budget_usage_rate,
    }
