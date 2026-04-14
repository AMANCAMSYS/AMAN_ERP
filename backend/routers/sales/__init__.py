"""Sales module - split into sub-modules for maintainability."""
from fastapi import APIRouter, Depends

from .customers import customers_router
from .invoices import invoices_router
from .orders import orders_router
from .quotations import quotations_router
from .returns import returns_router
from .vouchers import vouchers_router
from .credit_notes import credit_notes_router
from .sales_improvements import sales_improvements_router
from .cpq import cpq_router
from utils.permissions import require_module

router = APIRouter(prefix="/sales", tags=["المبيعات"], dependencies=[Depends(require_module("sales"))])

router.include_router(customers_router)
router.include_router(invoices_router)
router.include_router(orders_router)
router.include_router(quotations_router)
router.include_router(returns_router)
router.include_router(vouchers_router)
router.include_router(credit_notes_router)
router.include_router(sales_improvements_router)
router.include_router(cpq_router)
