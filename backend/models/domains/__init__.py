"""Domain-first facades for ORM model discovery.

These modules provide a stable navigation layer grouped by business domains.
"""

from . import (
    core,
    finance,
    hr,
    inventory,
    manufacturing,
    operations,
    procurement,
    projects_crm,
    sales,
    security_reporting,
)

__all__ = [
    "core",
    "sales",
    "procurement",
    "inventory",
    "manufacturing",
    "finance",
    "hr",
    "projects_crm",
    "operations",
    "security_reporting",
]
