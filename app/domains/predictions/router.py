"""예산 초과 위험도 예측 라우터."""

from fastapi import APIRouter

from app.domains.predictions.schema import BudgetRiskRequest, BudgetRiskResponse
from app.domains.predictions.service import predict_budget_risks

router = APIRouter()


@router.post("/predictions/budget-risk", response_model=BudgetRiskResponse)
def budget_risk(request: BudgetRiskRequest) -> BudgetRiskResponse:
    return predict_budget_risks(request)
