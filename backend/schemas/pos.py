"""POS module Pydantic schemas."""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class SessionCreate(BaseModel):
    pos_profile_id: Optional[int] = None
    warehouse_id: Optional[int] = None
    opening_balance: float = 0.0
    notes: Optional[str] = None
    branch_id: Optional[int] = None
    treasury_account_id: Optional[int] = None


class SessionClose(BaseModel):
    closing_balance: float
    cash_register_balance: float
    notes: Optional[str] = None


class SessionResponse(BaseModel):
    id: int
    session_code: Optional[str] = None
    user_id: int
    warehouse_id: Optional[int] = None
    warehouse_name: Optional[str] = None
    treasury_account_id: Optional[int] = None
    cashier_name: Optional[str] = None
    status: str
    opened_at: datetime
    opening_balance: float = 0.0
    closing_balance: Optional[float] = 0.0
    total_sales: Optional[float] = 0.0
    total_cash: Optional[float] = 0.0
    total_bank: Optional[float] = 0.0
    total_returns: Optional[float] = 0.0
    total_returns_cash: Optional[float] = 0.0
    order_count: Optional[int] = 0
    difference: Optional[float] = 0.0


class POSProductResponse(BaseModel):
    id: int
    name: str
    code: Optional[str]
    barcode: Optional[str]
    price: float
    stock_quantity: float
    category_id: Optional[int]
    image_url: Optional[str]
    tax_rate: Optional[float] = 0.0


class OrderLineCreate(BaseModel):
    product_id: int
    quantity: float
    unit_price: float
    discount_amount: float = 0
    tax_rate: float = 0
    notes: Optional[str] = None


class OrderPaymentCreate(BaseModel):
    method: str
    amount: float
    reference: Optional[str] = None


class OrderCreate(BaseModel):
    session_id: int
    customer_id: Optional[int] = None
    walk_in_customer_name: Optional[str] = None
    warehouse_id: Optional[int] = None
    branch_id: Optional[int] = None
    items: List[OrderLineCreate]
    discount_amount: float = 0
    paid_amount: float = 0
    payments: List[OrderPaymentCreate] = []
    status: str = "paid"
    note: Optional[str] = None


class OrderResponse(BaseModel):
    id: int
    order_number: str
    total_amount: float
    status: str
    created_at: datetime


class ReturnItemCreate(BaseModel):
    item_id: int
    quantity: float
    reason: Optional[str] = None


class ReturnCreate(BaseModel):
    order_id: int
    items: List[ReturnItemCreate]
    refund_method: str = "cash"
    notes: Optional[str] = None
