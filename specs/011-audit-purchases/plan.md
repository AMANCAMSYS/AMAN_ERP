# Implementation Plan: Audit Purchases Module

**Branch**: `011-audit-purchases` | **Date**: 2026-04-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/011-audit-purchases/spec.md`

## Summary

Audit and fix the entire purchases module for constitution compliance: convert 76 backend `float()` to `str()`, 18+ Pydantic `float` fields to `Decimal`, 81 frontend `parseFloat()` to `String()`/`Number()`/`formatNumber()`, replace 47 `console.error` with `useToast`, migrate 7 files from `toastEmitter` to `useToast`, add fiscal period checks to 4 missing GL-posting endpoints, and add missing audit columns to 11 procurement tables via Alembic migration + database.py + domain model triple-update.

## Technical Context

**Language/Version**: Python 3.12 (backend), React 18 / Vite (frontend)
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 (SQL-first via `text()`), Pydantic, i18next, React Router
**Storage**: PostgreSQL 15 (multi-tenant `aman_{company_id}` + `aman_system`), Redis
**Testing**: `py_compile` + `vite build` (compile-time verification)
**Target Platform**: Linux server (Docker/Nginx)
**Project Type**: Web application (ERP)
**Constraints**: All monetary values as `Decimal`/`str` per Constitution §I; fiscal period hard-block per §III
**Scale/Scope**: 5 backend files, 36 frontend pages, 11 DB tables

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Section | Rule | Status | Notes |
|---------|------|--------|-------|
| §I Financial Precision ⛔ | No `float` for monetary values | VIOLATION — 76 backend `float()`, 18+ schema `float` fields | Fix: FR-001, FR-002, FR-003 |
| §III Double-Entry ⛔ | `check_fiscal_period_open()` gates all transactions | VIOLATION — 4 of 6 GL-posting endpoints lack the check | Fix: FR-007 |
| §VII Simplicity | SQL-first, `text()` queries | COMPLIANT | Existing code uses `text()` |
| §IX Procurement Discipline | Landed cost allocation, 3-way matching | COMPLIANT (logic correct, precision wrong) | Fix precision only |
| §XVII Observability ⛔ | `AuditMixin` on ALL domain models | VIOLATION — 11 tables missing audit columns | Fix: FR-008 |
| §XIX Calculation Centralization ⛔ | No frontend monetary calculations | PARTIAL — `parseFloat` in forms for local subtotals only | Fix: FR-004 (String for payloads, Number for local calc) |
| §XXII Transaction Pipeline | Pydantic → Permission → Fiscal → Rules → Calc → Persist → GL | VIOLATION — fiscal step skipped in 4 endpoints | Fix: FR-007 |
| §XXVII UI/UX Consistency ⛔ | Translated error messages, no raw strings | VIOLATION — `console.error` as sole feedback in 31 pages | Fix: FR-005, FR-006 |
| §XXVIII Schema Sync ⛔ | Migration + database.py + model triple-update | VIOLATION — audit columns missing from all 3 layers | Fix: FR-008 |

**Gate result**: 6 VIOLATIONS identified. All addressed by FR-001 through FR-010. No unjustified violations.

## Project Structure

### Documentation (this feature)

```text
specs/011-audit-purchases/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── database.py                          # CREATE TABLE definitions (audit column additions)
├── routers/
│   ├── purchases.py                     # 55 float→str, 3 fiscal period additions
│   ├── landed_costs.py                  # 6 float→str
│   └── matching.py                      # 13 float→str, 4 inline schema float→Decimal
├── schemas/
│   ├── purchases.py                     # 14 float→Decimal
│   └── matching.py                      # 12 float→Decimal
├── services/
│   └── matching_service.py              # 2 float→str
├── models/
│   └── domains/
│       ├── procurement_orders.py        # AuditMixin addition
│       ├── procurement_costs.py         # AuditMixin addition
│       └── procurement_suppliers.py     # AuditMixin addition
└── migrations/
    └── add_purchases_audit_columns.py   # New migration

frontend/src/pages/
├── Buying/          # 27 files (22 need useToast, 5 need toastEmitter→useToast)
├── Purchases/       # 3 files (all need useToast, 2 need toastEmitter→useToast)
├── Matching/        # 3 files (1 needs useToast)
└── BlanketPO/       # 3 files (all have useToast already)
```

**Structure Decision**: Existing web application structure — no new directories or files except the migration script.

## Complexity Tracking

No complexity violations. All changes are in-place fixes within existing files.
