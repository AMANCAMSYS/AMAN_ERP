"""Expenses module Pydantic schemas."""
from decimal import Decimal
from pydantic import BaseModel
from typing import Optional
from datetime import date


class ExpenseCreate(BaseModel):
    expense_date: date
    expense_type: str
    amount: Decimal
    description: Optional[str] = None
    category: Optional[str] = "general"
    payment_method: str = "cash"
    treasury_id: Optional[int] = None
    expense_account_id: Optional[int] = None
    cost_center_id: Optional[int] = None
    project_id: Optional[int] = None
    branch_id: Optional[int] = None
    requires_approval: bool = True
    receipt_number: Optional[str] = None
    vendor_name: Optional[str] = None


class ExpenseUpdate(BaseModel):
    expense_date: Optional[date] = None
    expense_type: Optional[str] = None
    amount: Optional[Decimal] = None
    description: Optional[str] = None
    category: Optional[str] = None
    payment_method: Optional[str] = None
    treasury_id: Optional[int] = None
    expense_account_id: Optional[int] = None
    cost_center_id: Optional[int] = None
    project_id: Optional[int] = None
    receipt_number: Optional[str] = None
    vendor_name: Optional[str] = None


class ExpenseApproval(BaseModel):
    approval_status: str
    approval_notes: Optional[str] = None


class ExpensePolicyCreate(BaseModel):
    name: str
    expense_type: Optional[str] = None
    department_id: Optional[int] = None
    daily_limit: Optional[Decimal] = None
    monthly_limit: Optional[Decimal] = None
    annual_limit: Optional[Decimal] = None
    requires_receipt: bool = True
    requires_approval: bool = True
    auto_approve_below: Optional[Decimal] = None
    is_active: bool = True


class ExpensePolicyUpdate(BaseModel):
    name: Optional[str] = None
    expense_type: Optional[str] = None
    department_id: Optional[int] = None
    daily_limit: Optional[Decimal] = None
    monthly_limit: Optional[Decimal] = None
    annual_limit: Optional[Decimal] = None
    requires_receipt: Optional[bool] = None
    requires_approval: Optional[bool] = None
    auto_approve_below: Optional[Decimal] = None
    is_active: Optional[bool] = None


class ExpenseValidation(BaseModel):
    expense_type: Optional[str] = None
    amount: Decimal = Decimal("0")
    department_id: Optional[int] = None
    has_receipt: bool = False
