"""예산 초과 위험도 예측 API 스키마."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class BudgetRiskRoomItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    room_no: int = Field(alias="roomNo")
    room_name: str = Field(default="", alias="roomName")
    total_budget: Optional[int] = Field(default=None, alias="totalBudget")
    location: Optional[str] = None
    tag: Optional[str] = None
    member_count: Optional[int] = Field(default=None, alias="memberCount")
    status: Optional[str] = None
    room_created: Optional[Any] = Field(default=None, alias="roomCreated")
    ended_at: Optional[Any] = Field(default=None, alias="endedAt")


class BudgetRiskReceiptItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    room_no: int = Field(alias="roomNo")
    amount: int
    receipt_type: Optional[str] = Field(default=None, alias="receiptType")
    good_price_matched: bool = Field(default=False, alias="goodPriceMatched")
    receipt_issued_at: Optional[Any] = Field(default=None, alias="receiptIssuedAt")


class BudgetRiskBudgetItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    room_no: int = Field(alias="roomNo")
    budget_amount: int = Field(alias="budgetAmount")
    submitted_at: Optional[Any] = Field(default=None, alias="submittedAt")


class BudgetRiskRequest(BaseModel):
    rooms: list[BudgetRiskRoomItem] = []
    receipts: list[BudgetRiskReceiptItem] = []
    budgets: list[BudgetRiskBudgetItem] = []


class BudgetRiskItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    room_no: int = Field(alias="roomNo")
    room_name: str = Field(alias="roomName")
    risk_level: str = Field(alias="riskLevel")
    risk_score: float = Field(alias="riskScore")
    predicted_final_spent_amount: int = Field(alias="predictedFinalSpentAmount")
    predicted_budget_usage_rate: float = Field(alias="predictedBudgetUsageRate")
    recommended_next_spend_limit: int = Field(alias="recommendedNextSpendLimit")
    reason: str


class BudgetRiskResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, protected_namespaces=())

    model_version: str = Field(alias="modelVersion")
    generated_at: datetime = Field(alias="generatedAt")
    items: list[BudgetRiskItem]
