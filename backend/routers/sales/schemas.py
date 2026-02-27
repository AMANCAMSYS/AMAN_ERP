"""Sales module Pydantic schemas."""
from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional
from datetime import date


# --- Customer Groups ---
class CustomerGroupCreate(BaseModel):
    group_name: str
    group_name_en: Optional[str] = None
    description: Optional[str] = None
    discount_percentage: float = 0.0
    effect_type: str = "discount"
    application_scope: str = "total"
    payment_days: int = 30
    status: str = "active"


# --- Customer ---
class CustomerCreate(BaseModel):
    name: str
    name_en: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    tax_number: Optional[str] = None
    contact_person: Optional[str] = None
    credit_limit: float = 0
    payment_terms: Optional[int] = 30
    notes: Optional[str] = None
    group_id: Optional[int] = None
    branch_id: Optional[int] = None
    currency: Optional[str] = None
    status: str = "active"


class CustomerResponse(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    current_balance: float = 0


# --- Invoice ---
class InvoiceLineItem(BaseModel):
    product_id: int
    description: Optional[str] = None
    quantity: float
    unit_price: float
    tax_rate: float = 15.0
    discount: float = 0
    markup: float = 0

    @validator("quantity")
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("الكمية يجب أن تكون أكبر من صفر")
        return v

    @validator("unit_price")
    def price_must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError("سعر الوحدة لا يمكن أن يكون سالباً")
        return v

    @validator("discount")
    def discount_must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError("الخصم لا يمكن أن يكون سالباً")
        return v


class InvoiceCreate(BaseModel):
    customer_id: int
    invoice_date: date
    due_date: Optional[date] = None
    items: List[InvoiceLineItem]
    notes: Optional[str] = None
    payment_method: Optional[str] = None
    paid_amount: Optional[float] = 0
    down_payment_method: Optional[str] = None   # method used when payment_method='credit' + partial down payment
    branch_id: Optional[int] = None
    warehouse_id: Optional[int] = None
    treasury_id: Optional[int] = None
    currency: Optional[str] = None
    exchange_rate: Optional[float] = 1.0
    cost_center_id: Optional[int] = None
    sales_order_id: Optional[int] = None

    # Group effects
    effect_type: str = "discount"
    effect_percentage: float = 0.0
    markup_amount: float = 0.0


class InvoiceResponse(BaseModel):
    id: int
    invoice_number: str
    customer_name: Optional[str] = None
    invoice_date: date
    total: float
    status: str


# --- Sales Order ---
class SOLineItem(BaseModel):
    product_id: int
    description: Optional[str] = None
    quantity: float
    unit_price: float
    tax_rate: float = 15.0
    discount: float = 0


class SOCreate(BaseModel):
    customer_id: int
    order_date: date
    expected_delivery_date: Optional[date] = None
    items: List[SOLineItem]
    notes: Optional[str] = None
    branch_id: Optional[int] = None
    warehouse_id: Optional[int] = None
    quotation_id: Optional[int] = None
    currency: Optional[str] = None
    exchange_rate: Optional[float] = 1.0


# --- Quotation ---
class QuotationLineItem(BaseModel):
    product_id: int
    description: Optional[str] = None
    quantity: float
    unit_price: float
    tax_rate: float = 15.0
    discount: float = 0


class QuotationCreate(BaseModel):
    customer_id: int
    quotation_date: date
    expiry_date: Optional[date] = None
    items: List[QuotationLineItem]
    notes: Optional[str] = None
    terms_conditions: Optional[str] = None
    branch_id: Optional[int] = None
    currency: Optional[str] = None
    exchange_rate: Optional[float] = 1.0


# --- Sales Return ---
class SalesReturnLineItem(BaseModel):
    product_id: int
    description: Optional[str] = None
    quantity: float
    unit_price: float
    tax_rate: Optional[float] = 15.0
    reason: Optional[str] = None


class SalesReturnCreate(BaseModel):
    customer_id: int
    invoice_id: Optional[int] = None
    return_date: date
    items: List[SalesReturnLineItem]
    notes: Optional[str] = None
    refund_method: Optional[str] = None
    refund_amount: Optional[float] = 0
    bank_account_id: Optional[int] = None
    check_number: Optional[str] = None
    check_date: Optional[date] = None
    branch_id: Optional[int] = None
    warehouse_id: Optional[int] = None
    currency: Optional[str] = None
    exchange_rate: Optional[float] = 1.0


# --- Payment Vouchers ---
class PaymentAllocation(BaseModel):
    invoice_id: int
    allocated_amount: float


class CustomerReceiptCreate(BaseModel):
    customer_id: int
    voucher_date: date
    amount: float
    payment_method: str
    bank_account_id: Optional[int] = None
    check_number: Optional[str] = None
    check_date: Optional[date] = None
    reference: Optional[str] = None
    notes: Optional[str] = None
    allocations: List[PaymentAllocation] = []
    branch_id: Optional[int] = None
    treasury_id: Optional[int] = None
    currency: Optional[str] = None
    exchange_rate: Optional[float] = 1.0


class CustomerPaymentCreate(BaseModel):
    customer_id: int
    voucher_date: date
    amount: float
    payment_method: str
    bank_account_id: Optional[int] = None
    check_number: Optional[str] = None
    check_date: Optional[date] = None
    reference: Optional[str] = None
    notes: Optional[str] = None
    allocations: List[PaymentAllocation] = []
    branch_id: Optional[int] = None
    currency: Optional[str] = None
    exchange_rate: Optional[float] = 1.0
