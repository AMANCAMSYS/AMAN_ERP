"""
AMAN ERP - Manufacturing Module
التصنيع

Sub-modules:
  core (/manufacturing) — work centers, BOMs, production orders, job cards, MRP
"""

from fastapi import APIRouter

from .core import router as manufacturing_router
from .routing import routing_router
from .shopfloor import shopfloor_router

# Combined router
router = APIRouter()
router.include_router(manufacturing_router)
router.include_router(routing_router)
router.include_router(shopfloor_router)
