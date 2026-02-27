"""Purchases module Pydantic schemas."""
from pydantic import BaseModel
from typing import List, Optional
from datetime import date


class PurchaseLineItem(BaseModel):
    product_id: Optional[int] = None
    description: str
    quantity: float
    unit_price: float
    tax_rate: float
    discount: float = 0.0
    markup: float = 0.0


class PurchaseCreate(BaseModel):
    supplier_id: int
    invoice_date: date
    due_date: Optional[date] = None
    items: List[PurchaseLineItem]
    notes: Optional[str] = None
    payment_method: str = "cash"
    down_payment_method: Optional[str] = None
    paid_amount: float = 0.0
    original_invoice_id: Optional[int] = None
    branch_id: Optional[int] = None
    warehouse_id: Optional[int] = None
    currency: Optional[str] = None
    exchange_rate: Optional[float] = None
    treasury_id: Optional[int] = None
    is_prepayment: bool = False

    # Group effects
    effect_type: str = "discount"
    effect_percentage: float = 0.0
    markup_amount: float = 0.0


class SupplierGroupCreate(BaseModel):
    group_name: str
    group_name_en: Optional[str] = None
    description: Optional[str] = None
    discount_percentage: float = 0.0
    effect_type: str = "discount"
    application_scope: str = "total"
    payment_days: int = 30
    branch_id: Optional[int] = None
    status: str = "active"


class POCreate(BaseModel):
    supplier_id: int
    order_date: date
    expected_date: Optional[date] = None
    items: List[PurchaseLineItem]
    notes: Optional[str] = None
    branch_id: Optional[int] = None
    currency: Optional[str] = None
    exchange_rate: Optional[float] = 1.0

    # Group effects
    effect_type: str = "discount"
    effect_percentage: float = 0.0
    markup_amount: float = 0.0


class ReceiveItem(BaseModel):
    line_id: int
    received_quantity: float


class POReceiveRequest(BaseModel):
    items: List[ReceiveItem]
    warehouse_id: int
    notes: Optional[str] = None


class SupplierCreate(BaseModel):
    supplier_name: str
    supplier_name_en: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    tax_number: Optional[str] = None
    branch_id: Optional[int] = None
    supplier_group_id: Optional[int] = None


class PaymentAllocationSchema(BaseModel):
    invoice_id: int
    allocated_amount: float


class SupplierPaymentCreate(BaseModel):
    supplier_id: int
    voucher_date: date
    amount: float
    payment_method: str
    bank_account_id: Optional[int] = None
    check_number: Optional[str] = None
    check_date: Optional[date] = None
    reference: Optional[str] = None
    notes: Optional[str] = None
    branch_id: Optional[int] = None
    voucher_type: Optional[str] = 'payment'
    currency: Optional[str] = None
    exchange_rate: Optional[float] = 1.0
    treasury_account_id: Optional[int] = None
    transaction_rate: Optional[float] = None
    allocations: List[PaymentAllocationSchema] = []
