"""Compatibility wrapper for phase 31.

Physical model definitions have been moved to domain-owned modules.
Keep this file to preserve stable imports.
"""

from .domain_models.finance_cashflow import RecurringJournalLine, RecurringJournalTemplate
from .domain_models.manufacturing_execution import ProductionOrder, ProductionOrderOperation
from .domain_models.procurement_costs import PurchaseAgreement, PurchaseAgreementLine
from .domain_models.projects_execution import ProjectRisk, ProjectTimesheet
from .domain_models.sales_pos import (
    PosOrder,
    PosOrderPayment,
    PosPayment,
    PosPromotion,
    PosReturn,
    PosReturnItem,
    PosSession,
    PosTable,
    PosTableOrder,
    Receipt,
)
from .domain_models.security_comms import PrintTemplate, ReportTemplate


__all__ = [
    "PosOrderPayment",
    "PosOrder",
    "PosPayment",
    "PosPromotion",
    "PosReturnItem",
    "PosReturn",
    "PosSession",
    "PosTableOrder",
    "PosTable",
    "PrintTemplate",
    "ProductionOrderOperation",
    "ProductionOrder",
    "ProjectRisk",
    "ProjectTimesheet",
    "PurchaseAgreementLine",
    "PurchaseAgreement",
    "Receipt",
    "RecurringJournalLine",
    "RecurringJournalTemplate",
    "ReportTemplate",
]
