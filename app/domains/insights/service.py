"""관리자 소비 인사이트 계산 로직.

초기 버전은 추가 의존성 없이 순수 Python으로 계산한다.
pandas 기반 상세 분석은 PHASE1 기획 문서 Step 3에서 확장한다.
"""

from collections import Counter, defaultdict

from app.domains.insights.schema import (
    HighBudgetUsageRoom,
    RegionSpending,
    SpendingInsightRequest,
    SpendingInsightResponse,
    SpendingSummary,
    TagClickCount,
)


def build_spending_summary(request: SpendingInsightRequest) -> SpendingInsightResponse:
    room_by_no = {room.room_no: room for room in request.rooms}
    spent_by_room: dict[int, int] = defaultdict(int)

    total_spent = 0
    for receipt in request.receipts:
        amount = max(receipt.amount, 0)
        total_spent += amount
        spent_by_room[receipt.room_no] += amount

    average_receipt = int(total_spent / len(request.receipts)) if request.receipts else 0
    budget_over_count = sum(
        1
        for room in request.rooms
        if room.total_budget and spent_by_room.get(room.room_no, 0) > room.total_budget
    )
    budget_over_rate = round((budget_over_count / len(request.rooms)) * 100, 1) if request.rooms else 0.0

    good_price_count = sum(1 for receipt in request.receipts if receipt.good_price_matched)
    good_price_rate = round((good_price_count / len(request.receipts)) * 100, 1) if request.receipts else 0.0

    region_spending: dict[str, int] = defaultdict(int)
    for room_no, spent in spent_by_room.items():
        region = room_by_no.get(room_no).location if room_no in room_by_no else "미분류"
        region_spending[region or "미분류"] += spent

    tag_click_counter = Counter(
        interaction.requested_tag or "미분류"
        for interaction in request.recommendation_interactions
        if interaction.action.upper() == "CLICK"
    )

    usage_rooms = []
    for room in request.rooms:
        total_budget = room.total_budget or 0
        spent = spent_by_room.get(room.room_no, 0)
        usage_rate = round((spent / total_budget) * 100, 1) if total_budget > 0 else 0.0
        usage_rooms.append(
            HighBudgetUsageRoom(
                roomNo=room.room_no,
                roomName=room.room_name,
                totalBudget=total_budget,
                spentAmount=spent,
                usageRate=usage_rate,
            )
        )

    return SpendingInsightResponse(
        summary=SpendingSummary(
            totalSpentAmount=total_spent,
            averageReceiptAmount=average_receipt,
            budgetOverRoomRate=budget_over_rate,
            goodPriceUsageRate=good_price_rate,
        ),
        topRegions=[
            RegionSpending(region=region, spentAmount=spent)
            for region, spent in sorted(region_spending.items(), key=lambda item: item[1], reverse=True)[:5]
        ],
        tagClicks=[
            TagClickCount(tag=tag, clickCount=count)
            for tag, count in tag_click_counter.most_common()
        ],
        highBudgetUsageRooms=sorted(usage_rooms, key=lambda room: room.usage_rate, reverse=True)[:10],
    )
