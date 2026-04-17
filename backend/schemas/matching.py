"""Pydantic schemas for 3-way matching."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


# --- Tolerance schemas ---

class MatchToleranceCreate(BaseModel):
    name: str = Field(..., max_length=100)
    quantity_percent: Decimal = Decimal("0")
    quantity_absolute: Decimal = Decimal("0")
    price_percent: Decimal = Decimal("0")
    price_absolute: Decimal = Decimal("0")
    supplier_id: Optional[int] = None
    product_category_id: Optional[int] = None


class MatchToleranceRead(BaseModel):
    id: int
    name: str
    quantity_percent: Decimal
    quantity_absolute: Decimal
    price_percent: Decimal
    price_absolute: Decimal
    supplier_id: Optional[int] = None
    product_category_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# --- Match line schemas ---

class ThreeWayMatchLineRead(BaseModel):
    id: int
    match_id: int
    po_line_id: int
    grn_ids: Optional[list] = None
    invoice_line_id: Optional[int] = None
    po_quantity: Decimal
    received_quantity: Decimal
    invoiced_quantity: Decimal
    po_unit_price: Decimal
    invoiced_unit_price: Decimal
    quantity_variance_pct: Decimal
    quantity_variance_abs: Decimal
    price_variance_pct: Decimal
    price_variance_abs: Decimal
    tolerance_id: Optional[int] = None
    line_status: str

    model_config = {"from_attributes": True}


# --- Match header schemas ---

class ThreeWayMatchRead(BaseModel):
    id: int
    purchase_order_id: int
    invoice_id: int
    match_status: str
    matched_at: Optional[datetime] = None
    matched_by: Optional[int] = None
    exception_approved_by: Optional[int] = None
    exception_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ThreeWayMatchDetail(ThreeWayMatchRead):
    lines: List[ThreeWayMatchLineRead] = []
    po_number: Optional[str] = None
    invoice_number: Optional[str] = None
    supplier_name: Optional[str] = None


# --- Approve / reject ---

class MatchApproveRequest(BaseModel):
    exception_notes: Optional[str] = None
