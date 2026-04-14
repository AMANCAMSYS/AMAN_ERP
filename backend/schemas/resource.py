"""Pydantic schemas for US18 — Resource Planning."""

from datetime import date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, field_validator, model_validator


class AllocationCreate(BaseModel):
    employee_id: int
    project_id: int
    role: str
    allocation_percent: Decimal
    start_date: date
    end_date: date

    @field_validator('allocation_percent')
    @classmethod
    def percent_range(cls, v: Decimal) -> Decimal:
        if v <= 0 or v > 100:
            raise ValueError('allocation_percent must be > 0 and <= 100')
        return v

    @model_validator(mode='after')
    def dates_valid(self):
        if self.start_date > self.end_date:
            raise ValueError('start_date must be <= end_date')
        return self


class AllocationUpdate(BaseModel):
    role: Optional[str] = None
    allocation_percent: Optional[Decimal] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    @field_validator('allocation_percent')
    @classmethod
    def percent_range(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and (v <= 0 or v > 100):
            raise ValueError('allocation_percent must be > 0 and <= 100')
        return v

    @model_validator(mode='after')
    def dates_valid(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError('start_date must be <= end_date')
        return self


class AllocationRead(BaseModel):
    id: int
    employee_id: int
    employee_name: Optional[str] = None
    project_id: int
    project_name: Optional[str] = None
    role: str
    allocation_percent: Decimal
    start_date: date
    end_date: date

    class Config:
        from_attributes = True


class EmployeeAvailability(BaseModel):
    employee_id: int
    employee_name: str
    total_allocation: Decimal
    is_over_allocated: bool
    allocations: List[AllocationRead]


class AvailabilityCalendarResponse(BaseModel):
    employees: List[EmployeeAvailability]
