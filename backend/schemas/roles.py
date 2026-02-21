"""Roles module Pydantic schemas."""
from pydantic import BaseModel
from typing import List, Optional


class RoleCreate(BaseModel):
    role_name: str
    role_name_ar: Optional[str] = None
    description: Optional[str] = None
    permissions: List[str] = []


class RoleUpdate(BaseModel):
    role_name: Optional[str] = None
    role_name_ar: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None
