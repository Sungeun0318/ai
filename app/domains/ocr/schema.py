"""OCR 요청/응답 스키마."""

from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List

class OcrRequest(BaseModel):
    receipt_id: int = Field(alias="receiptId")
    image_url: str = Field(alias="imageUrl")
    room_no: int = Field(alias="roomNo")

class Product(BaseModel):
    model_config = ConfigDict(extra='ignore')
    name: str
    price: int
    quantity: int
    amount: int

class ReceiptAnalysis(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    store_name: Optional[str] = None
    address: Optional[str] = None
    total_amount: Optional[int] = None
    date: Optional[str] = None
    category: Optional[str] = None
    products: Optional[List[Product]] = Field(default=None, alias="items")

class OcrResponse(BaseModel):
    receipt_id: int
    success: bool
    analysis: Optional[ReceiptAnalysis] = None

ReceiptAnalysis.model_rebuild()
OcrResponse.model_rebuild()