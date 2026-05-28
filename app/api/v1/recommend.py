"""추천 라우터 — 백엔드 RecommendationService 가 호출.

엔드포인트 (구현 예정):
  GET /api/v1/recommend
    Query: room_no, budget, tags(콤마 구분, 중식/한식/일식/양식/기타요식업), lat, lng
    Response: schemas.recommend.RecommendResponse
"""

from fastapi import APIRouter

router = APIRouter()


# TODO: @router.get("/recommend", response_model=RecommendResponse)
#       def recommend(
#           room_no: int,
#           budget: int,
#           tags: str,           # "한식,카페,놀거리"
#           lat: float | None = None,
#           lng: float | None = None,
#       ) -> RecommendResponse:
#           return recommend_service.recommend(...)
