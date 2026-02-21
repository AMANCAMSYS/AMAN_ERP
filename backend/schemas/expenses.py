"""Expenses module Pydantic schemas."""
from pydantic import BaseModel
from typing import Optional
from datetime import date


class ExpenseCreate(BaseModel):
    expense_date: date
    expense_type: str
    amount: float
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
    amount: Optional[float] = None
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
