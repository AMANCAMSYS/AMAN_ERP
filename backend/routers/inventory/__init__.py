"""
AMAN ERP - Inventory Module (Split Package)
Originally routers/inventory.py (2,755 lines) → split into sub-modules
"""

from fastapi import APIRouter

router = APIRouter(prefix="/inventory", tags=["المخزون"])

# Import and include all sub-routers
from .products import products_router
from .suppliers import suppliers_router
from .categories import categories_router
from .warehouses import warehouses_router
from .transfers import transfers_router
from .price_lists import price_lists_router
from .stock_movements import stock_movements_router
from .shipments import shipments_router
from .notifications import notifications_router
from .adjustments import adjustments_router
from .reports import reports_router
from .batches import batches_router
from .advanced import advanced_router

router.include_router(products_router)
router.include_router(suppliers_router)
router.include_router(categories_router)
router.include_router(warehouses_router)
router.include_router(transfers_router)
router.include_router(price_lists_router)
router.include_router(stock_movements_router)
router.include_router(shipments_router)
router.include_router(notifications_router)
router.include_router(adjustments_router)
router.include_router(reports_router)
router.include_router(batches_router)
router.include_router(advanced_router)
