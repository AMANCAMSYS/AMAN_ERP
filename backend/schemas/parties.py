"""Parties module Pydantic schemas - unified Customer/Supplier model."""
from pydantic import BaseModel
from typing import Optional


class PartyCreate(BaseModel):
    """Unified create schema for both customers and suppliers.
    Both are stored in the `parties` table with different `party_type` values.
    """
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


class PartyResponse(BaseModel):
    id: int
    name: str
    name_en: Optional[str] = None
    party_type: str
    email: Optional[str] = None
    phone: Optional[str] = None
    tax_number: Optional[str] = None
    address: Optional[str] = None
    balance: float
    credit_limit: Optional[float] = None
    is_active: bool

    class Config:
        from_attributes = True


# Backward-compatible aliases
CustomerCreate = PartyCreate
SupplierCreate = PartyCreate
