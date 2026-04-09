"""Subscription billing Pydantic schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# ── Plan schemas ──

class PlanCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    billing_frequency: Literal["monthly", "quarterly", "annual"] = "monthly"
    base_amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="SAR", min_length=3, max_length=3)
    trial_period_days: int = Field(default=0, ge=0)
    auto_renewal: bool = True


class PlanUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    billing_frequency: Optional[Literal["monthly", "quarterly", "annual"]] = None
    base_amount: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    trial_period_days: Optional[int] = Field(None, ge=0)
    auto_renewal: Optional[bool] = None
    is_active: Optional[bool] = None


class PlanRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    billing_frequency: str
    base_amount: Decimal
    currency: str
    trial_period_days: int
    auto_renewal: bool
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Enrollment schemas ──

class EnrollmentCreate(BaseModel):
    customer_id: int
    plan_id: int
    enrollment_date: Optional[date] = None  # defaults to today


class EnrollmentRead(BaseModel):
    id: int
    customer_id: int
    plan_id: int
    enrollment_date: date
    trial_end_date: Optional[date] = None
    next_billing_date: date
    status: str
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    failed_payment_count: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class EnrollmentDetailRead(EnrollmentRead):
    plan_name: Optional[str] = None
    customer_name: Optional[str] = None
    invoices: List["SubscriptionInvoiceRead"] = []


class PlanChangeRequest(BaseModel):
    new_plan_id: int


class CancelRequest(BaseModel):
    reason: Optional[str] = None


# ── Invoice schemas ──

class SubscriptionInvoiceRead(BaseModel):
    id: int
    enrollment_id: int
    invoice_id: Optional[int] = None
    billing_period_start: date
    billing_period_end: date
    is_prorated: bool
    proration_details: Optional[dict] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── List responses ──

class PlanListResponse(BaseModel):
    items: List[PlanRead]
    total: int


class EnrollmentListResponse(BaseModel):
    items: List[EnrollmentRead]
    total: int
