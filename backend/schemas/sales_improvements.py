"""Sales improvements module Pydantic schemas."""
from decimal import Decimal
from pydantic import BaseModel
from typing import Optional, List


class CommissionRuleCreate(BaseModel):
    name: str
    salesperson_id: Optional[int] = None
    product_id: Optional[int] = None
    category_id: Optional[int] = None
    rate_type: Optional[str] = None
    rate: Optional[Decimal] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    branch_id: Optional[int] = None


class CommissionCalculateRequest(BaseModel):
    invoice_id: Optional[int] = None
    salesperson_id: Optional[int] = None
    salesperson_name: Optional[str] = None
    rate: Optional[Decimal] = None


class CommissionPayRequest(BaseModel):
    commission_ids: List[int] = []
    payment_date: Optional[str] = None


class PartialInvoiceLine(BaseModel):
    order_line_id: int
    quantity: Decimal


class PartialInvoiceCreate(BaseModel):
    lines: List[PartialInvoiceLine] = []


class CreditLimitUpdate(BaseModel):
    credit_limit: Decimal


class CreditCheckRequest(BaseModel):
    party_id: int
    amount: Decimal
