"""
AMAN ERP - Manufacturing Module
التصنيع

Sub-modules:
  core (/manufacturing) — work centers, BOMs, production orders, job cards, MRP
"""

from fastapi import APIRouter

from .core import router as manufacturing_router

# Combined router
router = APIRouter()
router.include_router(manufacturing_router)
