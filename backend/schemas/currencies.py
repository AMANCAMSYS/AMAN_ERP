"""Currencies module Pydantic schemas."""
from pydantic import BaseModel
from typing import Optional
from datetime import date


class RevaluationRequest(BaseModel):
    currency_id: int
    rate_date: date
    new_rate: float
    description: Optional[str] = None
