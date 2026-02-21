"""Assets module Pydantic schemas."""
from pydantic import BaseModel
from typing import Optional
from datetime import date


class AssetCreate(BaseModel):
    name: str
    code: Optional[str] = None
    type: str
    purchase_date: date
    cost: float
    residual_value: float = 0
    life_years: int
    branch_id: Optional[int] = None
    currency: str = ""
    depreciation_method: str = "straight_line"


class AssetUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None


class AssetDisposal(BaseModel):
    disposal_date: date
    disposal_price: float = 0
    notes: Optional[str] = None
    payment_method: str = "cash"
