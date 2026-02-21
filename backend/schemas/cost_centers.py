"""Cost Centers module Pydantic schemas."""
from pydantic import BaseModel
from typing import Optional


class CostCenterCreate(BaseModel):
    center_code: Optional[str] = None
    center_name: str
    center_name_en: Optional[str] = None
    department_id: Optional[int] = None
    manager_id: Optional[int] = None
    is_active: bool = True


class CostCenterUpdate(BaseModel):
    center_code: Optional[str] = None
    center_name: Optional[str] = None
    center_name_en: Optional[str] = None
    department_id: Optional[int] = None
    manager_id: Optional[int] = None
    is_active: Optional[bool] = None


class CostCenterResponse(BaseModel):
    id: int
    center_code: Optional[str]
    center_name: str
    center_name_en: Optional[str]
    department_id: Optional[int]
    manager_id: Optional[int]
    is_active: bool
