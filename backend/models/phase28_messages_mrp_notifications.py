"""Compatibility wrapper for phase 28.

Physical model definitions have been moved to domain-owned modules.
Keep this file to preserve stable imports.
"""

from .domain_models.manufacturing_execution import MfgQcCheck, MrpItem, MrpPlan
from .domain_models.security_comms import Message, Notification


__all__ = [
    "Message",
    "MfgQcCheck",
    "MrpPlan",
    "MrpItem",
    "Notification",
]
