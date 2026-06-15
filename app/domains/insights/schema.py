"""관리자 소비 인사이트 API 스키마."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RoomInsightItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    room_no: int = Field(alias="roomNo")
    room_name: str = Field(default="", alias="roomName")
    location: str = ""
    tag: Optional[str] = None
    total_budget: Optional[int] = Field(default=None, alias="totalBudget")
    member_count: Optional[int] = Field(default=None, alias="memberCount")
    status: Optional[str] = None


class ReceiptInsightItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    receipt_id: int = Field(alias="receiptId")
    room_no: int = Field(alias="roomNo")
    amount: int
    store_name: Optional[str] = Field(default=None, alias="storeName")
    receipt_type: Optional[str] = Field(default=None, alias="receiptType")
    good_price_matched: bool = Field(default=False, alias="goodPriceMatched")
    receipt_issued_at: Optional[datetime] = Field(default=None, alias="receiptIssuedAt")


class RecommendationInteractionItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    room_no: int = Field(alias="roomNo")
    requested_tag: Optional[str] = Field(default=None, alias="requestedTag")
    action: str
    expected_price: Optional[int] = Field(default=None, alias="expectedPrice")
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")


class SpendingInsightRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    rooms: list[RoomInsightItem] = []
    receipts: list[ReceiptInsightItem] = []
    recommendation_interactions: list[RecommendationInteractionItem] = Field(
        default=[],
        alias="recommendationInteractions",
    )


class SpendingSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total_spent_amount: int = Field(alias="totalSpentAmount")
    average_receipt_amount: int = Field(alias="averageReceiptAmount")
    budget_over_room_rate: float = Field(alias="budgetOverRoomRate")
    good_price_usage_rate: float = Field(alias="goodPriceUsageRate")


class RegionSpending(BaseModel):
    region: str
    spent_amount: int = Field(alias="spentAmount")


class TagClickCount(BaseModel):
    tag: str
    click_count: int = Field(alias="clickCount")


class HighBudgetUsageRoom(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    room_no: int = Field(alias="roomNo")
    room_name: str = Field(alias="roomName")
    total_budget: int = Field(alias="totalBudget")
    spent_amount: int = Field(alias="spentAmount")
    usage_rate: float = Field(alias="usageRate")


class SpendingInsightResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    summary: SpendingSummary
    top_regions: list[RegionSpending] = Field(alias="topRegions")
    tag_clicks: list[TagClickCount] = Field(alias="tagClicks")
    high_budget_usage_rooms: list[HighBudgetUsageRoom] = Field(alias="highBudgetUsageRooms")
