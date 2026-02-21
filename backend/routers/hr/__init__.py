"""
AMAN ERP - Human Resources Module
الموارد البشرية

Sub-modules:
  core (/hr) — employees, departments, payroll, attendance, leaves, etc.
  advanced (/hr-advanced) — performance, training, violations, custody, recruitment
"""

from fastapi import APIRouter

from .core import router as hr_router
from .advanced import router as hr_advanced_router

# Combined router — each sub-module keeps its own prefix
router = APIRouter()
router.include_router(hr_router)
router.include_router(hr_advanced_router)
