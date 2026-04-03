"""Approvals module Pydantic schemas."""
from decimal import Decimal
from pydantic import BaseModel
from typing import Optional


class ApprovalRequestCreate(BaseModel):
    document_type: Optional[str] = None
    document_id: Optional[int] = None
    amount: Optional[Decimal] = None
    description: Optional[str] = None
