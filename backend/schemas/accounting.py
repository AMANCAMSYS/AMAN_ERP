"""Accounting module Pydantic schemas."""
from pydantic import BaseModel
from typing import Optional, List
from datetime import date


class AccountCreate(BaseModel):
    name: str
    name_en: Optional[str] = None
    account_number: str
    account_code: Optional[str] = None
    account_type: str
    parent_id: Optional[int] = None
    currency: str = ""
    is_header: bool = False


# --- Fiscal Year / Year-End Closing ---
class FiscalYearCreate(BaseModel):
    year: int
    start_date: date
    end_date: date
    retained_earnings_account_id: Optional[int] = None


class FiscalYearClose(BaseModel):
    """Request body for year-end closing."""
    retained_earnings_account_id: Optional[int] = None  # Override default if needed
    close_periods: bool = True  # Also close all fiscal periods for this year


class FiscalYearReopen(BaseModel):
    """Request body for reopening a closed year."""
    reason: Optional[str] = None
