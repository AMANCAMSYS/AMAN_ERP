"""Compatibility wrapper for phase 33.

Physical model definitions have been moved to domain-owned modules.
Keep this file to preserve stable imports.
"""

from .domain_models.finance_recognition_tax import TaxCalendar, WhtRate, WhtTransaction
from .domain_models.hr_training import TrainingParticipant, TrainingProgram
from .domain_models.manufacturing_resources import WorkCenter
from .domain_models.procurement_suppliers import (
    Supplier,
    SupplierBalance,
    SupplierBankAccount,
    SupplierContact,
    SupplierGroup,
    SupplierPayment,
    SupplierRating,
    SupplierTransaction,
)
from .domain_models.projects_dependencies import TaskDependency
from .domain_models.security_reporting import User2FASetting, UserSession, Webhook, WebhookLog


__all__ = [
    "SupplierBalance",
    "SupplierBankAccount",
    "SupplierContact",
    "SupplierGroup",
    "SupplierPayment",
    "SupplierRating",
    "SupplierTransaction",
    "Supplier",
    "TaskDependency",
    "TaxCalendar",
    "TrainingParticipant",
    "TrainingProgram",
    "User2FASetting",
    "UserSession",
    "WebhookLog",
    "Webhook",
    "WhtRate",
    "WhtTransaction",
    "WorkCenter",
]
