"""Cash-flow forecast Pydantic schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# ── Request ──

class ForecastGenerateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    horizon_days: int = Field(default=90, ge=1, le=365)
    mode: Literal["contractual", "expected"] = "contractual"


# ── Line read ──

class ForecastLineRead(BaseModel):
    id: int
    forecast_id: int
    date: date
    bank_account_id: Optional[int] = None
    source_type: str
    source_document_id: Optional[int] = None
    projected_inflow: Decimal
    projected_outflow: Decimal
    projected_balance: Decimal

    model_config = {"from_attributes": True}


# ── Forecast read ──

class ForecastRead(BaseModel):
    id: int
    name: str
    forecast_date: date
    horizon_days: int
    mode: str
    generated_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ForecastDetailRead(ForecastRead):
    lines: List[ForecastLineRead] = []


# ── List response ──

class ForecastListResponse(BaseModel):
    items: List[ForecastRead]
    total: int
