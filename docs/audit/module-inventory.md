# Module Inventory — Aman ERP

**Task**: T016 | **Phase**: 3.2 Setup | **Generated**: 2026-04-20
**Source**: `backend/routers/` tree + permission-string namespaces from `require_permission(...)` call sites.

This inventory enumerates the ERP's top-level functional modules and the router files that realise them. It is the canonical module list referenced by downstream artefacts (severity-matrix.md, rbac-matrix.md, findings `module` field, baseline-report.md).

## Methodology

1. Enumerate `backend/routers/*.py` (flat) and `backend/routers/*/` (subpackages).
2. Cross-reference with 32 module namespaces extracted from 153 distinct `require_permission("<module>.<action>")` strings (see `/tmp/rbac_permissions.txt`).
3. Group routers under the dominant domain module; note cross-cutting / platform concerns separately.

## Core Business Modules

| Module         | Router file(s)                                                                                                                             | Permission namespace(s)                                | Notes |
|----------------|--------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------|-------|
| Accounting / GL | `finance/accounting.py`, `finance/advanced_workflow.py`, `finance/notes.py`                                                                | `accounting.*`                                          | Single posting path via `services/gl_service.py` (Principle I). |
| Budgets        | `finance/budgets.py`                                                                                                                        | `accounting.budgets.*`                                  | |
| Cost Centers   | `finance/cost_centers.py`, `finance/costing_policies.py`                                                                                    | `accounting.cost_centers.*`                             | |
| Cashflow       | `finance/cashflow.py`                                                                                                                       | `finance.cashflow_*`                                    | |
| Subscriptions  | `finance/subscriptions.py`                                                                                                                  | `finance.subscription_*`                                | |
| Treasury / Checks | `finance/treasury.py`, `finance/checks.py`                                                                                               | `treasury.*`                                            | |
| Reconciliation | `finance/reconciliation.py`, `matching.py`                                                                                                  | `reconciliation.*`                                      | |
| Intercompany   | `finance/intercompany.py`, `finance/intercompany_v2.py`                                                                                     | (uses `accounting.*`)                                   | v1+v2 coexist — dual-stack risk flag (see severity-matrix). |
| Tax            | `finance/taxes.py`, `finance/tax_compliance.py`                                                                                             | `taxes.*`                                               | |
| Currencies / FX | `finance/currencies.py`                                                                                                                    | `currencies.*`                                          | |
| Fixed Assets   | `finance/assets.py`, `landed_costs.py`                                                                                                      | `assets.*`                                              | |
| Expenses       | `finance/expenses.py`                                                                                                                       | `expenses.*`                                            | |
| Sales          | `sales/orders.py`, `sales/invoices.py`, `sales/quotations.py`, `sales/customers.py`, `sales/credit_notes.py`, `sales/returns.py`, `sales/vouchers.py`, `sales/cpq.py`, `sales/sales_improvements.py` | `sales.*`                                               | |
| POS            | `pos.py`                                                                                                                                    | `pos.*`                                                 | |
| CRM            | `crm.py`                                                                                                                                    | `crm.campaign_*`                                        | |
| Purchases / Buying | `purchases.py`, `delivery_orders.py`                                                                                                    | `purchases.*`, `buying.*`                               | Note: two namespaces (`purchases.*`, `buying.*`) overlap — RBAC consolidation candidate. |
| Inventory      | `inventory/products.py`, `inventory/stock_movements.py`, `inventory/adjustments.py`, `inventory/transfers.py`, `inventory/warehouses.py`, `inventory/batches.py`, `inventory/categories.py`, `inventory/price_lists.py`, `inventory/shipments.py`, `inventory/suppliers.py`, `inventory/costing.py`, `inventory/forecast.py`, `inventory/reports.py`, `inventory/notifications.py`, `inventory/advanced.py` | `inventory.*`, `stock.*`, `products.*`                  | Three overlapping namespaces — RBAC consolidation candidate. |
| Manufacturing  | `manufacturing/core.py`, `manufacturing/routing.py`, `manufacturing/shopfloor.py`                                                           | `manufacturing.*`                                       | |
| HR             | `hr/core.py`, `hr/advanced.py`, `hr/performance.py`, `hr/self_service.py`, `hr_wps_compliance.py`                                           | `hr.*`                                                  | `hr.pii` permission gates PII views. WPS = UAE Wage Protection System. |
| Projects       | `projects.py`                                                                                                                               | `projects.*`                                            | |
| Services       | `services.py`                                                                                                                               | `services.*`                                            | |
| Contracts      | `contracts.py`                                                                                                                              | `contracts.*`                                           | |
| Approvals      | `approvals.py`                                                                                                                              | `approvals.*`                                           | Cross-cutting workflow. |
| Parties        | `parties.py`                                                                                                                                | `parties.view`                                          | Unified customer/supplier entity. |

## Platform / Cross-Cutting Modules

| Module         | Router file(s)                                       | Permission namespace(s)                  | Notes |
|----------------|------------------------------------------------------|------------------------------------------|-------|
| Auth / SSO     | `auth.py`, `sso.py`                                  | `auth.sso_manage`                        | |
| Security / RBAC | `security.py`, `roles.py`, `role_dashboards.py`     | `security.*`, `admin.roles`              | Roles are DB-driven (see `models/domain_models/security_reporting.py::Role`). |
| Companies / Branches | `companies.py`, `branches.py`                  | `admin.companies`, `admin.branches`, `branches.*` | Multi-tenant anchors. |
| Settings       | `settings.py`                                        | `settings.*`                             | |
| Dashboard      | `dashboard.py`                                       | `dashboard.*`                            | |
| Reports        | `reports.py`, `scheduled_reports.py`                 | `reports.*`                              | |
| Audit Log      | `audit.py`                                           | `audit.view`                             | |
| Notifications  | `notifications.py`                                   | `notifications.*`                        | |
| Data Import    | `data_import.py`                                     | `data_import.*`                          | |
| Mobile         | `mobile.py`                                          | `mobile.*`                               | |
| External / API | `external.py`                                        | (mixed)                                  | Third-party integration surface. |
| System         | `system_completion.py`                               | (admin)                                  | |

## Metrics

- **Router files**: 57 (32 flat + 25 across 5 subpackages).
- **Distinct endpoint paths**: 624 (see `baseline/endpoints.txt`).
- **Permission strings**: 153 distinct across 181 `require_permission(...)` call sites (see `rbac-matrix.md`).
- **Module namespaces**: 32.

## Consolidation / Risk Flags (for Phase 2 findings)

1. **Overlapping namespaces** — `purchases.*` vs `buying.*`, and `inventory.*` vs `stock.*` vs `products.*`. Candidate P2 finding (RBAC clarity).
2. **Intercompany v1 + v2 coexist** (`intercompany.py` + `intercompany_v2.py`). Candidate P1/P2 finding (dual posting paths risk — cross-check against Principle I).
3. **`system_completion.py`** — name suggests bootstrap/seed router; review for production exposure (P1 candidate).
