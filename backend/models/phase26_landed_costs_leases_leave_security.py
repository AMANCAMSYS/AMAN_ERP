"""Compatibility wrapper for phase 26.

Physical model definitions have been moved to domain-owned modules.
Keep this file to preserve stable imports.
"""

from .domain_models.hr_workforce import LeaveCarryover
from .domain_models.operations_support import LeaseContract
from .domain_models.procurement_costs import LandedCost, LandedCostItem
from .domain_models.security_comms import LoginAttempt


__all__ = [
    "LandedCost",
    "LandedCostItem",
    "LeaseContract",
    "LeaveCarryover",
    "LoginAttempt",
]
