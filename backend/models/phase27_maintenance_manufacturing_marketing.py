"""Compatibility wrapper for phase 27.

Physical model definitions have been moved to domain-owned modules.
Keep this file to preserve stable imports.
"""

from .domain_models.manufacturing_execution import ManufacturingEquipment, ManufacturingOperation, ManufacturingRoute
from .domain_models.operations_support import MaintenanceLog, MarketingCampaign


__all__ = [
    "MaintenanceLog",
    "ManufacturingEquipment",
    "ManufacturingOperation",
    "ManufacturingRoute",
    "MarketingCampaign",
]
