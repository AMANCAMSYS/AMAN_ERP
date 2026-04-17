# Implementation Plan: Audit Manufacturing Module — تدقيق وحدة التصنيع

**Branch**: `016-audit-manufacturing` | **Date**: 2026-04-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/016-audit-manufacturing/spec.md`

## Summary

Audit and fix the manufacturing module across 3 backend routers, 1 schema file, 9 model files, and 22+ frontend pages to enforce financial precision (Decimal instead of float for 20+ monetary/quantity fields), SoftDeleteMixin compliance (9 models missing), branch validation (16+ endpoints missing), pagination (6 list endpoints), error message sanitization, and console.error → toast migration (22 instances). This is an audit/fix — no new features, no new tables.

## Technical Context

**Language/Version**: Python 3.12 (backend), React 18 / Vite (frontend)  
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 (SQL-first via `text()`), Pydantic, i18next, React Router  
**Storage**: PostgreSQL 15 (multi-tenant `aman_{company_id}` + system `aman_system`), Redis (rate limiting/cache)  
**Testing**: pytest (backend), Vitest (frontend)  
**Target Platform**: Linux server (Docker + Nginx)  
**Project Type**: Web application (ERP)  
**Performance Goals**: N/A — this is an audit/fix spec, not new functionality  
**Constraints**: Zero breaking changes to existing API contracts; Decimal serialization as strings preserves backward compatibility  
**Scale/Scope**: 3 backend router files (~4800 lines), 1 schema file, 9 model files, 22+ frontend pages across Manufacturing/, ShopFloor/, Routing/

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Rule | Status | Notes |
|---|---|---|
| I. Financial Precision ⛔ | **VIOLATION → FIX** | `schemas/manufacturing_advanced.py` uses `float` for all monetary/quantity fields (20+ instances); `core.py` uses `float()` conversions in `calculate_production_cost()` and cost calculations; `routing.py` uses `float` for quantity param; `shopfloor.py` uses `float()` for cycle_time and quantity |
| II. Multi-Tenant Isolation ⛔ | ✅ PASS | All routers use `get_db_connection(company_id)` via dependencies |
| III. Double-Entry Integrity ⛔ | ✅ PASS | Production order start/complete creates balanced GL journal entries via `gl_service.py` (DEBIT WIP / CREDIT Raw Materials on start; DEBIT FG / CREDIT WIP on complete) |
| IV. Security & Access Control ⛔ | **VIOLATION → FIX** | 16+ endpoints missing `validate_branch_access()` — only work_centers list and production_orders list have it. HTTPException details expose internal state via f-strings (e.g., `f"Cannot start order with status {order.status}"`) |
| V. Regulatory Compliance — Saudi ⛔ | ✅ PASS | Manufacturing module does not handle tax/ZATCA/GOSI directly |
| VI. Concurrency Safety | ✅ PASS | BOM component reservation uses atomic transactions; inventory deduction is transactional |
| VII. Simplicity & Maintainability | **VIOLATION → FIX** | 6 list endpoints return all rows without pagination (LIMIT/OFFSET). Constitution requires default 25, max 100 |
| VIII. Inventory Integrity | ✅ PASS | BOM consumption auto-reduces components; scrap tracked; WAC updated on FG receipt |
| X. Manufacturing Execution | ✅ PASS | BOM consumption, routing sequence enforcement, capacity validation, job cards, MO state machine all implemented |
| XVII. Observability & Audit Trail | **VIOLATION → FIX** | 9 domain models missing `SoftDeleteMixin` — physical DELETE operations with no recovery. `AuditMixin` present, but soft-delete absent. `log_activity()` is compliant on all write endpoints. |
| XIX. Calculation Centralization ⛔ | ✅ PASS | `calculate_production_cost()` is the single cost calculation entry point; BOM explosion centralized |
| XXVII. UI/UX Behavioral Consistency ⛔ | **VIOLATION → FIX** | 22 `console.error` instances across 15 frontend files (should use toast). No `toLocaleString` violations (formatNumber properly used). |

## Project Structure

### Documentation (this feature)

```text
specs/016-audit-manufacturing/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (files to modify)

```text
backend/
├── schemas/
│   └── manufacturing_advanced.py       # 20+ float → Decimal conversions
├── routers/
│   └── manufacturing/
│       ├── core.py                     # float() → Decimal, branch validation (16 endpoints),
│       │                               #   pagination (6 endpoints), error sanitization
│       ├── routing.py                  # float quantity param → Decimal, branch validation
│       └── shopfloor.py               # float() → Decimal, error message sanitization
└── models/
    └── domain_models/
        ├── manufacturing_bom_capacity.py   # Add SoftDeleteMixin to BillOfMaterial, BomComponent, BomOutput, CapacityPlan
        ├── manufacturing_execution.py      # Add SoftDeleteMixin to ManufacturingEquipment, ManufacturingOperation,
        │                                   #   ManufacturingRoute, MfgQcCheck
        └── manufacturing_resources.py      # Add SoftDeleteMixin to WorkCenter

frontend/src/
├── pages/
│   ├── Manufacturing/                 # 20 pages — console.error → toast
│   │   ├── ProductionOrders.jsx       # 2 console.error
│   │   ├── Routings.jsx               # 2 console.error
│   │   ├── BOMs.jsx                   # 2 console.error
│   │   ├── DirectLaborReport.jsx      # 2 console.error
│   │   ├── CapacityPlanning.jsx       # 1 console.error
│   │   ├── ProductionOrderDetails.jsx # 1 console.error
│   │   ├── EquipmentMaintenance.jsx   # 3 console.error
│   │   ├── WorkCenters.jsx            # 2 console.error
│   │   ├── ManufacturingCosting.jsx   # 1 console.error
│   │   ├── ProductionSchedule.jsx     # 2 console.error
│   │   ├── ProductionAnalytics.jsx    # 1 console.error
│   │   ├── WorkOrderStatusReport.jsx  # 1 console.error
│   │   └── JobCards.jsx               # 1 console.error (≈ 1 more page)
│   └── ShopFloor/                     # 2 pages — console.error → toast
│       ├── ShopFloorDashboard.jsx     # 1 console.error
│       └── OperationEntry.jsx         # 1 console.error
└── services/
    └── manufacturing.js               # No changes needed (clean)
```

**Structure Decision**: This is an audit-fix affecting existing files only — no new files, directories, or modules are created. SoftDeleteMixin additions may require a migration for `is_deleted` columns.

## Complexity Tracking

No constitution violations requiring justification — all violations are being **fixed** (not justified) by this audit.
