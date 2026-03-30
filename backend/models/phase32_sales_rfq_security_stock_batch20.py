"""Compatibility wrapper for phase 32.

Physical model definitions have been moved to domain-owned modules.
Keep this file to preserve stable imports.
"""

from .domain_models.finance_recognition_tax import RevenueRecognitionSchedule
from .domain_models.inventory_transfers import StockShipment, StockShipmentItem, StockTransferLog
from .domain_models.sales_rfq import (
    RequestForQuotation,
    RfqLine,
    RfqResponse,
    SalesCommission,
    SalesOpportunity,
    SalesOrder,
    SalesOrderLine,
    SalesQuotation,
    SalesQuotationLine,
    SalesReturn,
    SalesReturnLine,
    SalesTarget,
)
from .domain_models.security_reporting import Role, ScheduledReport, SecurityEvent, SharedReport


__all__ = [
    "RequestForQuotation",
    "RevenueRecognitionSchedule",
    "RfqLine",
    "RfqResponse",
    "Role",
    "SalesCommission",
    "SalesOpportunity",
    "SalesOrderLine",
    "SalesOrder",
    "SalesQuotationLine",
    "SalesQuotation",
    "SalesReturnLine",
    "SalesReturn",
    "SalesTarget",
    "ScheduledReport",
    "SecurityEvent",
    "SharedReport",
    "StockShipmentItem",
    "StockShipment",
    "StockTransferLog",
]
