from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TransactionBase(BaseModel):
    amount: float
    currency: str
    card_last4: Optional[str] = None
    datetime: datetime
    transaction_type: str
    direction: Optional[str] = None
    bank: str


class TransactionCreate(TransactionBase):
    raw_message: str
    vendor_id: Optional[int] = None
    source_account: Optional[str] = None
    destination_account: Optional[str] = None
    fees: Optional[float] = 0


class Transaction(TransactionBase):
    id: int
    raw_message: str
    vendor_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class VendorCreate(BaseModel):
    raw_vendor_name: str


class Vendor(BaseModel):
    id: int
    raw_vendor_name: str
    real_name: Optional[str] = None
    classification: Optional[str] = None
    logo_url: Optional[str] = None

    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    total_messages: int
    parsed_successfully: int
    failed: int
    errors: list[dict]
    created_vendors: list[str]