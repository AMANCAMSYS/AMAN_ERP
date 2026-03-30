"""Compatibility wrapper for phase 29.

Physical model definitions have been moved to domain-owned modules.
Keep this file to preserve stable imports.
"""

from .domain_models.finance_cashflow import PartyTransaction, PaymentAllocation
from .domain_models.hr_workforce import OvertimeRequest
from .domain_models.projects_execution import OpportunityActivity
from .domain_models.security_comms import PasswordHistory


__all__ = [
    "OpportunityActivity",
    "OvertimeRequest",
    "PartyTransaction",
    "PasswordHistory",
    "PaymentAllocation",
]
