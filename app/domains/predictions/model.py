"""예산 초과 위험도 모델.

초기 버전은 설명 가능한 규칙 기반 모델이다.
scikit-learn 모델은 샘플 데이터가 충분해진 뒤 같은 인터페이스로 교체한다.
"""


def predict_budget_risk(features: dict) -> dict:
    budget_usage_rate = features["budget_usage_rate"]
    remaining_budget = features["remaining_budget"]
    avg_receipt_amount = features["avg_receipt_amount"]
    receipt_count = features["receipt_count"]
    good_price_usage_rate = features["good_price_usage_rate"]

    score = base_budget_usage_score(budget_usage_rate)

    if avg_receipt_amount > 0 and remaining_budget < avg_receipt_amount:
        score += 4
    elif avg_receipt_amount > 0 and remaining_budget < avg_receipt_amount * 2:
        score += 2

    if receipt_count >= 10:
        score += 3
    elif receipt_count >= 5:
        score += 1.5

    if good_price_usage_rate < 20:
        score += 2

    risk_score = round(min(score, 95), 1)
    risk_level = risk_level_from_score(risk_score)
    predicted_final_spent = predict_final_spent(features, risk_score)
    predicted_usage_rate = (
        round((predicted_final_spent / features["total_budget"]) * 100, 1)
        if features["total_budget"] > 0
        else 0.0
    )

    return {
        "risk_level": risk_level,
        "risk_score": risk_score,
        "predicted_final_spent_amount": predicted_final_spent,
        "predicted_budget_usage_rate": predicted_usage_rate,
        "recommended_next_spend_limit": recommended_next_spend_limit(features),
        "reason": risk_reason(features, risk_level),
    }


def base_budget_usage_score(budget_usage_rate: float) -> float:
    if budget_usage_rate <= 0:
        return 5
    if budget_usage_rate < 60:
        return 10 + (budget_usage_rate / 60) * 25
    if budget_usage_rate < 100:
        return 40 + ((budget_usage_rate - 60) / 40) * 25
    if budget_usage_rate < 150:
        return 70 + ((budget_usage_rate - 100) / 50) * 8
    if budget_usage_rate < 250:
        return 78 + ((budget_usage_rate - 150) / 100) * 10
    return 88 + min(((budget_usage_rate - 250) / 500) * 7, 7)


def risk_level_from_score(score: float) -> str:
    if score >= 70:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    return "LOW"


def predict_final_spent(features: dict, risk_score: float) -> int:
    spent = features["spent_amount"]
    avg_receipt = features["avg_receipt_amount"]
    multiplier = 1 + (risk_score / 250)
    return int(spent * multiplier + avg_receipt)


def recommended_next_spend_limit(features: dict) -> int:
    remaining = features["remaining_budget"]
    member_count = max(features["member_count"], 1)
    if remaining <= 0:
        return 0
    return int(remaining / member_count)


def risk_reason(features: dict, risk_level: str) -> str:
    if risk_level == "HIGH":
        return "현재 예산 사용률이 높고 평균 결제 금액 대비 남은 예산이 부족합니다."
    if risk_level == "MEDIUM":
        return "지출 속도가 빠른 편이라 다음 소비 금액을 조절하는 것이 좋습니다."
    return "현재 지출 흐름은 예산 안에서 안정적으로 유지되고 있습니다."
