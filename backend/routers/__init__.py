"""
AMAN ERP - Router Package
نظام أمان — تسجيل جميع الراوترات

Structure:
  routers/
  ├── auth.py, companies.py, roles.py, ...   (core & admin)
  ├── finance/                               (accounting, treasury, taxes, ...)
  ├── hr/                                    (core + advanced)
  ├── manufacturing/                         (production, BOM, MRP, ...)
  ├── inventory/                             (products, warehouses, transfers, ...)
  └── sales/                                 (customers, invoices, orders, ...)
"""

# ── Core & Admin (top-level) ───────────────────────────────────────────────────
from . import (
    auth, companies, roles, branches, settings,
    audit, notifications, approvals, security, data_import,
)

# ── Grouped packages ──────────────────────────────────────────────────────────
from . import finance, hr, manufacturing, inventory, sales

# ── Remaining top-level routers ────────────────────────────────────────────────
from . import (
    purchases, parties, projects, reports, scheduled_reports,
    dashboard, pos, contracts, crm, external,
)

# ── Additional modules ──────────────────────────────────────────────
from . import (
    services, role_dashboards, delivery_orders,
    landed_costs, hr_wps_compliance, system_completion,
    sso, matching,
)

__all__ = [
    # Core & Admin
    "auth", "companies", "roles", "branches", "settings",
    "audit", "notifications", "approvals", "security", "data_import",
    # Grouped packages
    "finance", "hr", "manufacturing", "inventory", "sales",
    # Remaining top-level
    "purchases", "parties", "projects", "reports", "scheduled_reports",
    "dashboard", "pos", "contracts", "crm", "external",
    # Additional modules
    "services", "role_dashboards", "delivery_orders",
    "landed_costs", "hr_wps_compliance", "system_completion",
    "sso", "matching",
]
