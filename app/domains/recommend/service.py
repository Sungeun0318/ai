"""추천 로직.

입력: room_no, budget, tags(중식/한식/일식/양식/기타요식업 중 N개), lat, lng
출력: RecommendResponse (요청된 카테고리별 후보 가게, 합이 budget 이하)

구현 단계 (예시):
  1) 위치 기준 카테고리별 후보 가게 수집
     - 카카오 로컬 API 호출 (kakao_rest_api_key 사용)
     - 또는 자체 크롤링 데이터
  2) 가격대 필터 (가게별 평균가 추정)
  3) 조합 최적화: 예산 안에서 별점/거리 가중치 합 최대화
  4) 도보 시간 계산 (단순 거리 → 분 환산)
"""


# TODO: def recommend(room_no: int, budget: int, tags: list[str],
#                     lat: float | None, lng: float | None) -> RecommendResponse:
#           ...
