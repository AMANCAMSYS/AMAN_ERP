"""Pydantic schemas for Employee Self-Service (US6)."""
from pydantic import BaseModel, ConfigDict
from typing import Optional, Any
from datetime import date, datetime
from decimal import Decimal


# --- Leave Request ---

class LeaveRequestCreate(BaseModel):
    leave_type: str
    start_date: date
    end_date: date
    reason: Optional[str] = None


class LeaveRequestRead(BaseModel):
    id: int
    employee_id: int
    employee_name: Optional[str] = None
    leave_type: str
    start_date: date
    end_date: date
    days: Optional[int] = None
    reason: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# --- Profile Update ---

class ProfileUpdateRequest(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    emergency_contact: Optional[str] = None
    address: Optional[str] = None


# --- Self-Service Request wrapper ---

class SelfServiceRequestRead(BaseModel):
    id: int
    employee_id: int
    employee_name: Optional[str] = None
    request_type: str
    details: Optional[dict[str, Any]] = None
    status: str
    approver_id: Optional[int] = None
    approver_name: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# --- Payslip ---

class PayslipRead(BaseModel):
    id: int
    employee_id: int
    employee_name: Optional[str] = None
    period_name: Optional[str] = None
    month: Optional[int] = None
    year: Optional[int] = None
    basic_salary: Optional[Decimal] = None
    housing_allowance: Optional[Decimal] = None
    transport_allowance: Optional[Decimal] = None
    other_allowances: Optional[Decimal] = None
    total_earnings: Optional[Decimal] = None
    total_deductions: Optional[Decimal] = None
    net_salary: Optional[Decimal] = None
    status: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


# --- Leave Balance ---

class LeaveBalanceRead(BaseModel):
    annual_entitlement: int = 21
    used_days: int = 0
    pending_days: int = 0
    remaining_days: int = 0
    carry_over: int = 0
