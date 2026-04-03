"""Checks module Pydantic schemas."""
from decimal import Decimal
from pydantic import BaseModel
from typing import Optional


class CheckReceivableCreate(BaseModel):
    check_number: str
    amount: Decimal
    due_date: str
    branch_id: Optional[int] = None
    issue_date: Optional[str] = None
    drawer_name: str = ""
    bank_name: str = ""
    branch_name: str = ""
    currency: Optional[str] = None
    party_id: Optional[int] = None
    treasury_account_id: Optional[int] = None
    receipt_id: Optional[int] = None
    notes: str = ""


class CheckCollectParams(BaseModel):
    collection_date: Optional[str] = None
    treasury_account_id: Optional[int] = None


class CheckBounceParams(BaseModel):
    bounce_reason: str = ""
    bounce_date: Optional[str] = None


class CheckPayableCreate(BaseModel):
    check_number: str
    amount: Decimal
    due_date: str
    issue_date: str
    branch_id: Optional[int] = None
    beneficiary_name: str = ""
    bank_name: str = ""
    branch_name: str = ""
    currency: Optional[str] = None
    party_id: Optional[int] = None
    treasury_account_id: Optional[int] = None
    payment_voucher_id: Optional[int] = None
    notes: str = ""


class CheckClearParams(BaseModel):
    clearance_date: Optional[str] = None
    treasury_account_id: Optional[int] = None
