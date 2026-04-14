"""Routing / RoutingOperation Pydantic schemas."""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class OperationCreate(BaseModel):
    sequence: int
    name: Optional[str] = None
    work_center_id: Optional[int] = None
    description: Optional[str] = None
    setup_time: Decimal = Decimal("0")
    cycle_time: Decimal = Decimal("0")
    labor_rate_per_hour: Decimal = Decimal("0")


class OperationRead(BaseModel):
    id: int
    route_id: Optional[int] = None
    sequence: int
    name: Optional[str] = None
    work_center_id: Optional[int] = None
    work_center_name: Optional[str] = None
    description: Optional[str] = None
    setup_time: Decimal = Decimal("0")
    cycle_time: Decimal = Decimal("0")
    labor_rate_per_hour: Decimal = Decimal("0")
    created_at: Optional[datetime] = None


class RoutingCreate(BaseModel):
    name: str
    product_id: Optional[int] = None
    bom_id: Optional[int] = None
    is_default: bool = False
    is_active: bool = True
    description: Optional[str] = None
    operations: List[OperationCreate] = []


class RoutingRead(BaseModel):
    id: int
    name: str
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    bom_id: Optional[int] = None
    is_default: bool = False
    is_active: bool = True
    description: Optional[str] = None
    operations: List[OperationRead] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class RoutingEstimate(BaseModel):
    """Calculated time/cost estimate for a routing at a given quantity."""
    routing_id: int
    routing_name: str
    total_setup_minutes: Decimal = Decimal("0")
    total_run_minutes: Decimal = Decimal("0")
    total_time_minutes: Decimal = Decimal("0")
    total_labor_cost: Decimal = Decimal("0")
