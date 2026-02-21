from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime

class ContractItemBase(BaseModel):
    product_id: int
    description: Optional[str] = None
    quantity: float
    unit_price: float
    tax_rate: float = 15.0

class ContractItemCreate(ContractItemBase):
    pass

class ContractItemResponse(ContractItemBase):
    id: int
    contract_id: int
    total: float
    created_at: datetime

    class Config:
        from_attributes = True

class ContractBase(BaseModel):
    contract_number: str
    party_id: int
    contract_type: str = "subscription"
    start_date: date
    end_date: Optional[date] = None
    billing_interval: str = "monthly"
    total_amount: float = 0
    currency: str = "SAR"
    notes: Optional[str] = None

class ContractCreate(ContractBase):
    items: List[ContractItemCreate]

class ContractResponse(ContractBase):
    id: int
    status: str
    next_billing_date: Optional[date] = None
    created_by: Optional[int] = None
    created_at: datetime
    items: List[ContractItemResponse]
    party_name: Optional[str] = None

    class Config:
        from_attributes = True
