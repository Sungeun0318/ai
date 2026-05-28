"""OCR 요청/응답 스키마."""

from pydantic import BaseModel, ConfigDict, Field


class OcrRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    receipt_id: int = Field(alias="receiptId")
    image_url: str  = Field(alias="imageUrl")


class OcrResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    receipt_id: int      = Field(alias="receiptId")
    success: bool
    store_name: str | None = Field(default=None, alias="storeName")
    total_amount: int | None = Field(default=None, alias="totalAmount")
    address: str | None  = None
    lat: float | None    = Field(default=None, alias="centerLat")
    lng: float | None    = Field(default=None, alias="centerLng")
    error_message: str | None = Field(default=None, alias="errorMessage")
