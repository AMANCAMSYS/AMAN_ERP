"""Services module Pydantic schemas."""
from decimal import Decimal
from pydantic import BaseModel
from typing import Optional


class ServiceRequestCreate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    customer_id: Optional[int] = None
    asset_id: Optional[int] = None
    assigned_to: Optional[int] = None
    estimated_hours: Optional[float] = None
    estimated_cost: Optional[Decimal] = None
    scheduled_date: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None


class ServiceRequestUpdate(BaseModel):
    version: int
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    customer_id: Optional[int] = None
    asset_id: Optional[int] = None
    assigned_to: Optional[int] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    estimated_cost: Optional[Decimal] = None
    actual_cost: Optional[Decimal] = None
    scheduled_date: Optional[str] = None
    completion_date: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None


class TechnicianAssignRequest(BaseModel):
    assigned_to: Optional[int] = None


class ServiceCostCreate(BaseModel):
    quantity: Optional[float] = None
    unit_cost: Optional[Decimal] = None
    cost_type: Optional[str] = None
    description: Optional[str] = None


class DocumentMetaUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    access_level: Optional[str] = None
