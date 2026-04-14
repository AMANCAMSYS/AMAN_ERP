"""Demand forecast Pydantic schemas."""
from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class ForecastGenerateRequest(BaseModel):
    product_id: int
    warehouse_id: Optional[int] = None
    horizon_months: int = Field(default=3, ge=1, le=24)


class ForecastPeriodRead(BaseModel):
    id: int
    forecast_id: int
    period_start: date
    period_end: date
    projected_quantity: Decimal
    confidence_lower: Decimal
    confidence_upper: Decimal
    manual_adjustment: Decimal = Decimal("0")
    adjusted_quantity: Decimal


class ForecastRead(BaseModel):
    id: int
    product_id: int
    warehouse_id: Optional[int] = None
    forecast_method: str
    generated_date: date
    generated_by: int
    history_months_used: int
    periods: List[ForecastPeriodRead] = []


class PeriodAdjustment(BaseModel):
    period_id: int
    manual_adjustment: Decimal


class ForecastAdjustRequest(BaseModel):
    adjustments: List[PeriodAdjustment]
