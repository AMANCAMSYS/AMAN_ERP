# Implementation Plan: Audit Inventory Module — تدقيق وحدة المخزون

**Branch**: `009-audit-inventory` | **Date**: 2026-04-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/009-audit-inventory/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Audit the existing inventory module (15 backend routers, 22 frontend pages, 3 services) to fix constitution violations: `float()` → `str()` in API responses, `parseFloat()` → string in 6 frontend forms, missing GL entries on cycle count completion, dead notification endpoints (404), inconsistent error handling (`console.error` → `useToast`), missing audit columns on 2 tables, and hard-block negative stock. No new features — purely correctional.

## Technical Context

**Language/Version**: Python 3.12 (backend), React 18 / Vite (frontend)
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 (`text()` SQL-first), Pydantic, i18next, React Router
**Storage**: PostgreSQL 15 (multi-tenant `aman_{company_id}` + `aman_system`), Redis (rate limiting/cache)
**Testing**: Manual verification via vite build + py_compile; existing test infrastructure
**Target Platform**: Linux server (Docker/Nginx) + browser SPA
**Project Type**: Web application (ERP multi-tenant)
**Performance Goals**: N/A (audit — no new endpoints, fixing existing)
**Constraints**: No new features; scope limited to inventory module files only; cross-module files excluded
**Scale/Scope**: 15 backend routers, 22 frontend pages, 3 backend services, 5 domain model groups, 1 frontend service file

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution § | Rule | Status | Notes |
|---|---|---|---|
| I. Financial Precision ⛔ | No float for monetary values | 🔴 VIOLATION | Backend `products.py` L129: `float(row.selling_price)`. Frontend: 6 files use `parseFloat()` for qty/cost payloads |
| II. Multi-Tenant Isolation ⛔ | All ops via `get_db_connection(company_id)` | ✅ PASS | All routers use tenant-scoped DB |
| III. Double-Entry Integrity ⛔ | Every transaction → balanced JEs | 🔴 VIOLATION | Cycle count completion (`batches.py` L1355-1375) creates inventory_transactions but NO GL entry for variance |
| IV. Security & Access Control ⛔ | `require_permission` + `validate_branch_access` | ✅ PASS | All routers checked — branch access enforced |
| VI. Concurrency Safety | Row-level locking on transfers | ✅ PASS | `transfers.py` uses `SELECT … FOR UPDATE` |
| VII. Simplicity | SQL-first, parameterized queries | ✅ PASS | All queries use `text()` with `:param` |
| VIII. Inventory Integrity | Available qty formula; costing consistency | 🟡 PARTIAL | Negative stock not consistently hard-blocked across all deduction endpoints |
| XVII. Observability & Audit Trail | AuditMixin on ALL domain models | 🔴 VIOLATION | `product_categories` missing `created_by`/`updated_by`; `stock_adjustments` missing `updated_at`/`updated_by` |
| XIX. Calculation Centralization ⛔ | Frontend NO monetary calculations | ✅ PASS | Frontend uses `formatNumber()` display-only |
| XXVII. UI/UX Consistency ⛔ | Error messages via i18n; loading states | 🔴 VIOLATION | Some pages use `console.error` or `toastEmitter.emit()` instead of `useToast` |
| XXVIII. Schema Sync ⛔ | Migration + database.py in sync | 🟡 PENDING | Will need dual-update for audit column migration |

**GATE RESULT**: 4 violations identified. All are fixable without architectural changes. Proceeding to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/009-audit-inventory/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── models/domain_models/
│   ├── inventory_core.py         # products, inventory, transactions, adjustments, categories, units
│   ├── inventory_transfers.py    # shipments, shipment_items, transfer_log
│   ├── inventory_advanced.py     # batches, serials, cycle counts, bins, variants, kits, QC
│   └── inventory_costing.py      # cost_layers, cost_layer_consumptions
├── routers/inventory/
│   ├── __init__.py               # Router mount (notifications.py removed)
│   ├── products.py               # Product CRUD + stock endpoints
│   ├── warehouses.py             # Warehouse CRUD + current-stock
│   ├── stock_movements.py        # Receipt/delivery endpoints
│   ├── adjustments.py            # Stock adjustment + GL posting
│   ├── transfers.py              # Inter-warehouse transfer (row locking)
│   ├── shipments.py              # Multi-item shipment lifecycle
│   ├── batches.py                # Batch, serial, QC, cycle count endpoints
│   ├── categories.py             # Product category CRUD
│   ├── price_lists.py            # Price list CRUD + bulk update
│   ├── costing.py                # Cost layers, method change, valuation
│   ├── forecast.py               # Demand forecast generation
│   ├── notifications.py          # DEPRECATED — unmounted from __init__.py
│   ├── advanced.py               # Variants, bins, kits, costing policies
│   ├── reports.py                # Summary, warehouse-stock, movements, valuation
│   └── suppliers.py              # Supplier view on parties table
├── services/
│   ├── costing_service.py        # CostingService (WAC, FIFO, LIFO)
│   ├── forecast_service.py       # Forecast generation
│   ├── demand_forecast_service.py # Demand forecasting
│   └── gl_service.py             # GL journal entry posting (shared)
└── migrations/                   # Alembic migrations

frontend/src/
├── pages/Stock/
│   ├── StockHome.jsx             # Inventory dashboard
│   ├── ProductList.jsx           # Product listing
│   ├── ProductForm.jsx           # Product create/edit
│   ├── CategoryList.jsx          # Category management
│   ├── WarehouseList.jsx         # Warehouse listing
│   ├── StockMovements.jsx        # Movement history
│   ├── StockTransferForm.jsx     # Transfer form (parseFloat violation)
│   ├── StockShipmentForm.jsx     # Shipment form (parseFloat violation)
│   ├── StockAdjustments.jsx      # Adjustment list (console.error violation)
│   ├── StockAdjustmentForm.jsx   # Adjustment form (parseFloat violation)
│   ├── BatchList.jsx             # Batch management (parseFloat violation)
│   ├── CycleCounts.jsx           # Cycle count workflow (parseFloat violation)
│   ├── QualityInspections.jsx    # QC workflow (parseFloat violation)
│   ├── InventoryValuation.jsx    # Valuation report
│   ├── StockReports.jsx          # Stock reports
│   ├── PriceLists.jsx            # Price list management
│   └── [5+ more pages]          # Variants, bins, kits, serials, etc.
├── pages/Forecast/
│   ├── ForecastGenerate.jsx      # Forecast generation
│   └── [more forecast pages]
└── services/
    └── inventory.js              # 65 API functions (4 dead notification functions)
```

**Structure Decision**: Existing web-application structure. No new files/directories needed except the Alembic migration for audit columns.

## Complexity Tracking

| Violation | Why Fix Needed | Approach |
|-----------|---------------|----------|
| §I float → str | Financial precision mandate; floating-point display artifacts | Change `float()` → `str()` in backend responses; `parseFloat()` → `String()` in frontend payloads |
| §III missing GL on cycle count | Variance adjustments must have double-entry backing | Add `gl_create_journal_entry()` call in cycle count completion path |
| §XVII missing audit columns | AuditMixin is mandatory on ALL domain models | Lightweight `ALTER TABLE ADD COLUMN` migration + update `database.py` |
| §XXVII inconsistent error handling | useToast is the standard; console.error provides no user feedback | Replace `console.error` / `toastEmitter.emit()` with `useToast` pattern |

## Post-Design Constitution Re-evaluation

*All violations identified in the initial gate check are resolved by the design artifacts.*

| Constitution § | Pre-Design | Post-Design | Resolution |
|---|---|---|---|
| I. Financial Precision ⛔ | 🔴 | ✅ RESOLVED | 20 backend float→str (R1) + 26 frontend parseFloat→String (R2) |
| III. Double-Entry ⛔ | 🔴 | ✅ RESOLVED | Cycle count GL entry added following adjustments.py pattern (R5) |
| VIII. Inventory Integrity | 🟡 | ✅ RESOLVED | Cycle count auto-adjust negative stock check added (R7) |
| XVII. Audit Trail | 🔴 | ✅ RESOLVED | 5 columns added to 2 tables via migration (R6) |
| XXVII. UI/UX Consistency ⛔ | 🔴 | ✅ RESOLVED | 17 pages standardized to useToast pattern (R3) |
| XXVIII. Schema Sync ⛔ | 🟡 | ✅ RESOLVED | Triple-update: migration + database.py + model (R6) |

**GATE RESULT**: All violations resolved. No new violations introduced.
