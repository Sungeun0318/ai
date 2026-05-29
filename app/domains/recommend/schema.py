"""추천 응답 스키마.

백엔드 `RecommendationResponse` (Java record) 와 1:1 매핑.
JSON 필드명을 카멜케이스로 맞추기 위해 alias 사용.
"""

from pydantic import BaseModel, ConfigDict, Field


class Place(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    category: str                          # 식사 / 카페 / 놀거리 / 기타
    expected_price: int = Field(alias="expectedPrice")
    walk_time: str       = Field(alias="walkTime")         # "도보 5분"
    rating: float
    thumbnail_url: str   = Field(alias="thumbnailUrl")
    address: str
    lat: float
    lng: float


class RecommendResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    room_no: int       = Field(alias="roomNo")
    total_budget: int  = Field(alias="totalBudget")
    places: list[Place]
