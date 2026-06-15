"""관리자 소비 인사이트 라우터."""

from fastapi import APIRouter

from app.domains.insights.schema import SpendingInsightRequest, SpendingInsightResponse
from app.domains.insights.service import build_spending_summary

router = APIRouter()


@router.post("/insights/spending-summary", response_model=SpendingInsightResponse)
def spending_summary(request: SpendingInsightRequest) -> SpendingInsightResponse:
    return build_spending_summary(request)
