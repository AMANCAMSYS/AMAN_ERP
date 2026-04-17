# Implementation Plan: Audit POS Module — تدقيق وحدة نقاط البيع

**Branch**: `013-audit-pos` | **Date**: 2026-04-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/013-audit-pos/spec.md`

## Summary

Apply the established audit pattern (from 009-inventory, 011-purchases, 012-sales) to the POS module: replace `float()` with `str()` in backend serialization, change Pydantic schemas from `float` to `Decimal`, add `AuditMixin` to all 13 POS models, add missing fiscal period checks on GL-posting endpoints (`close_session`, `create_return`), replace `parseFloat` with `Number()`/`String()` in frontend, replace `console.error`/`console.log` with `showToast`, and replace `.toLocaleString()` with `formatNumber()` on monetary values.

## Technical Context

**Language/Version**: Python 3.12 (backend), React 18 / Vite (frontend)
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 (SQL-first via `text()`), Pydantic, i18next, React Router
**Storage**: PostgreSQL 15 (multi-tenant `aman_{company_id}` + system `aman_system`), Redis (rate limiting/cache)
**Testing**: py_compile (backend syntax), vite build (frontend compilation), grep (violation counts)
**Target Platform**: Linux server (backend), Browser (frontend)
**Project Type**: Web application (ERP system)
**Performance Goals**: N/A for audit — correctness-focused, not performance
**Constraints**: Zero `float()` in POS backend, zero `parseFloat` / `console.error` / `console.log` in POS frontend
**Scale/Scope**: 1 backend router (~1700 lines), 1 schema file (23 float fields), 13 domain models, 11 frontend files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Gate | Status | Evidence |
|---|------|--------|----------|
| I | Financial Precision ⛔ | **PASS** | This audit enforces `Decimal` everywhere — eliminates all `float` from POS |
| II | Multi-Tenant Isolation ⛔ | **PASS** | No tenant routing changes; all ops already use `get_db_connection(company_id)` |
| III | Double-Entry Integrity ⛔ | **PASS** | Adding `check_fiscal_period_open` to `close_session` and `create_return` strengthens GL integrity |
| VII | Simplicity & Maintainability | **PASS** | In-place edits only; no new abstractions; follows established pattern from 012-sales |
| XVI | POS Operations | **PASS** | All POS rules preserved; audit columns enhance traceability |
| XVII | Observability & Audit Trail | **PASS** | Adding `AuditMixin` to all 13 POS models satisfies "ALL domain models" mandate |
| XIX | Calculation Centralization ⛔ | **PASS** | No calculation logic changes; only serialization and type fixes |

## Project Structure

### Documentation (this feature)

```text
specs/013-audit-pos/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── api-contracts.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── routers/
│   └── pos.py                          # Main POS router (~1700 lines, 31 float() calls)
├── schemas/
│   └── pos.py                          # Pydantic schemas (23 float fields)
├── models/
│   └── domain_models/
│       └── sales_pos.py                # 13 POS models (0/13 have AuditMixin)
└── database.py                         # sync_essential_columns (0 POS audit columns)

frontend/src/pages/POS/
├── POSHome.jsx                         # 1 parseFloat, 3 console.error
├── POSInterface.jsx                    # 2 parseFloat, 4 console.error, 14 toLocaleString (monetary)
├── POSOfflineManager.jsx               # 2 console.error, 1 toLocaleString (date — keep)
├── TableManagement.jsx                 # 1 console.error
├── KitchenDisplay.jsx                  # 1 console.error
├── CustomerDisplay.jsx                 # CLEAN (already uses formatNumber)
├── ThermalPrintSettings.jsx            # CLEAN (already uses formatNumber, toLocaleString on dates)
├── LoyaltyPrograms.jsx                 # 2 parseFloat, 1 console.error
├── Promotions.jsx                      # 2 parseFloat, 1 console.error
└── components/
    ├── POSReturns.jsx                  # 1 toLocaleString (monetary)
    └── HeldOrders.jsx                  # 2 console.error, 5 console.log, 1 toLocaleString (monetary)
```

**Structure Decision**: In-place edits to existing files. No new files created except documentation.

## Complexity Tracking

No constitution violations — no complexity justification needed.
