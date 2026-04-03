"""Domain-owned ORM model definitions.

These modules hold the physical class definitions grouped by business domain.
Phase files can re-export from here as compatibility wrappers.
"""

from .matching import MatchTolerance, ThreeWayMatch, ThreeWayMatchLine
from .sso import SsoConfiguration, SsoGroupRoleMapping, SsoFallbackAdmin
from .inventory_costing import CostLayer, CostLayerConsumption
from .intercompany import EntityGroup, IntercompanyTransactionV2, IntercompanyAccountMapping
from .mobile_sync import SyncQueue

__all__ = [
    "MatchTolerance", "ThreeWayMatch", "ThreeWayMatchLine",
    "SsoConfiguration", "SsoGroupRoleMapping", "SsoFallbackAdmin",
    "CostLayer", "CostLayerConsumption",
    "EntityGroup", "IntercompanyTransactionV2", "IntercompanyAccountMapping",
    "SyncQueue",
]
