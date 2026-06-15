"""관리자 소비 인사이트 계산 로직."""

from __future__ import annotations

import pandas as pd

from app.domains.insights.schema import (
    HighBudgetUsageRoom,
    RegionSpending,
    SpendingInsightRequest,
    SpendingInsightResponse,
    SpendingSummary,
    TagClickCount,
)


def build_spending_summary(request: SpendingInsightRequest) -> SpendingInsightResponse:
    rooms_df = _build_rooms_frame(request)
    receipts_df = _build_receipts_frame(request)
    interactions_df = _build_interactions_frame(request)

    total_spent = int(receipts_df["amount"].sum()) if not receipts_df.empty else 0
    average_receipt = int(receipts_df["amount"].mean()) if not receipts_df.empty else 0
    budget_over_rate = _calculate_budget_over_rate(rooms_df, receipts_df)
    good_price_rate = _calculate_good_price_usage_rate(receipts_df)

    return SpendingInsightResponse(
        summary=SpendingSummary(
            totalSpentAmount=total_spent,
            averageReceiptAmount=average_receipt,
            budgetOverRoomRate=budget_over_rate,
            goodPriceUsageRate=good_price_rate,
        ),
        topRegions=_build_top_regions(rooms_df, receipts_df),
        tagClicks=_build_tag_clicks(interactions_df),
        highBudgetUsageRooms=_build_high_budget_usage_rooms(rooms_df, receipts_df),
    )


def _build_rooms_frame(request: SpendingInsightRequest) -> pd.DataFrame:
    rows = [
        {
            "room_no": room.room_no,
            "room_name": room.room_name or "",
            "location": room.location or "미분류",
            "total_budget": _non_negative_int(room.total_budget),
        }
        for room in request.rooms
        if room.room_no is not None
    ]
    return pd.DataFrame(rows, columns=["room_no", "room_name", "location", "total_budget"])


def _build_receipts_frame(request: SpendingInsightRequest) -> pd.DataFrame:
    rows = [
        {
            "receipt_id": receipt.receipt_id,
            "room_no": receipt.room_no,
            "amount": _non_negative_int(receipt.amount),
            "good_price_matched": bool(receipt.good_price_matched),
        }
        for receipt in request.receipts
        if receipt.room_no is not None
    ]
    return pd.DataFrame(rows, columns=["receipt_id", "room_no", "amount", "good_price_matched"])


def _build_interactions_frame(request: SpendingInsightRequest) -> pd.DataFrame:
    rows = [
        {
            "room_no": interaction.room_no,
            "requested_tag": interaction.requested_tag or "미분류",
            "action": interaction.action or "",
        }
        for interaction in request.recommendation_interactions
        if interaction.room_no is not None
    ]
    return pd.DataFrame(rows, columns=["room_no", "requested_tag", "action"])


def _non_negative_int(value: int | None) -> int:
    return max(int(value or 0), 0)


def _room_spending_frame(receipts_df: pd.DataFrame) -> pd.DataFrame:
    if receipts_df.empty:
        return pd.DataFrame(columns=["room_no", "spent_amount"])

    return (
        receipts_df.groupby("room_no", as_index=False)["amount"]
        .sum()
        .rename(columns={"amount": "spent_amount"})
    )


def _rooms_with_spending(rooms_df: pd.DataFrame, receipts_df: pd.DataFrame) -> pd.DataFrame:
    spending_df = _room_spending_frame(receipts_df)
    merged_df = rooms_df.merge(spending_df, on="room_no", how="left")
    merged_df["spent_amount"] = merged_df["spent_amount"].fillna(0).astype(int)
    merged_df["usage_rate"] = 0.0

    has_budget = merged_df["total_budget"] > 0
    merged_df.loc[has_budget, "usage_rate"] = (
        merged_df.loc[has_budget, "spent_amount"] / merged_df.loc[has_budget, "total_budget"] * 100
    ).round(1)
    return merged_df


def _calculate_budget_over_rate(rooms_df: pd.DataFrame, receipts_df: pd.DataFrame) -> float:
    if rooms_df.empty:
        return 0.0

    usage_df = _rooms_with_spending(rooms_df, receipts_df)
    over_count = int(((usage_df["total_budget"] > 0) & (usage_df["spent_amount"] > usage_df["total_budget"])).sum())
    return round((over_count / len(rooms_df)) * 100, 1)


def _calculate_good_price_usage_rate(receipts_df: pd.DataFrame) -> float:
    if receipts_df.empty:
        return 0.0

    return round(float(receipts_df["good_price_matched"].mean() * 100), 1)


def _build_top_regions(rooms_df: pd.DataFrame, receipts_df: pd.DataFrame) -> list[RegionSpending]:
    if receipts_df.empty:
        return []

    spending_df = _room_spending_frame(receipts_df)
    region_df = spending_df.merge(rooms_df[["room_no", "location"]], on="room_no", how="left")
    region_df["location"] = region_df["location"].fillna("미분류")
    grouped_df = (
        region_df.groupby("location", as_index=False)["spent_amount"]
        .sum()
        .sort_values(["spent_amount", "location"], ascending=[False, True])
        .head(5)
    )

    return [
        RegionSpending(region=row.location, spentAmount=int(row.spent_amount))
        for row in grouped_df.itertuples(index=False)
    ]


def _build_tag_clicks(interactions_df: pd.DataFrame) -> list[TagClickCount]:
    if interactions_df.empty:
        return []

    click_df = interactions_df[interactions_df["action"].str.upper() == "CLICK"].copy()
    if click_df.empty:
        return []

    grouped_df = (
        click_df.groupby("requested_tag", as_index=False)
        .size()
        .rename(columns={"size": "click_count"})
        .sort_values(["click_count", "requested_tag"], ascending=[False, True])
    )

    return [
        TagClickCount(tag=row.requested_tag, clickCount=int(row.click_count))
        for row in grouped_df.itertuples(index=False)
    ]


def _build_high_budget_usage_rooms(
    rooms_df: pd.DataFrame,
    receipts_df: pd.DataFrame,
) -> list[HighBudgetUsageRoom]:
    if rooms_df.empty:
        return []

    usage_df = _rooms_with_spending(rooms_df, receipts_df).sort_values(
        ["usage_rate", "spent_amount", "room_no"],
        ascending=[False, False, True],
    )

    return [
        HighBudgetUsageRoom(
            roomNo=int(row.room_no),
            roomName=row.room_name,
            totalBudget=int(row.total_budget),
            spentAmount=int(row.spent_amount),
            usageRate=float(row.usage_rate),
        )
        for row in usage_df.head(10).itertuples(index=False)
    ]
