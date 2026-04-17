# Implementation Plan: audit-treasury — الخزينة والبنوك

**Branch**: `007-audit-treasury` | **Date**: 2026-04-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/007-audit-treasury/spec.md`

## Summary

Comprehensive audit and remediation of the treasury & banking module. The audit addresses 20+ identified issues across 5 backend routers (treasury, checks, notes, reconciliation, cashflow), 17 frontend pages, and 9 key entities. Critical fixes include: reordering GL-before-balance in expense/transfer flows, adding `SELECT FOR UPDATE` for concurrency safety, enforcing fiscal period locks on all treasury operations, implementing check re-presentation (bounced → pending), adding overdraft policy (reject on cash / allow on bank), auto-creating missing GL accounts, configurable reconciliation tolerance, and duplicate check number detection.

## Technical Context

**Language/Version**: Python 3.12 (backend), React 18 / Vite (frontend)  
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 (SQL-first via `text()`), Pydantic, openpyxl, i18next, React Router  
**Storage**: PostgreSQL 15 (multi-tenant `aman_{company_id}` + system `aman_system`), Redis (rate limiting/cache)  
**Testing**: pytest (backend/tests/)  
**Target Platform**: Linux server (backend), browser SPA (frontend)  
**Project Type**: Web service (ERP audit/remediation)  
**Performance Goals**: <2s individual transactions, <10s batch operations (reconciliation import, forecast generation)  
**Constraints**: Multi-tenant isolation mandatory, double-entry GL balance enforcement, NUMERIC(18,4) precision for all monetary values  
**Scale/Scope**: 5 backend routers, 17 frontend pages, 9 data models impacted

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Financial Precision | ⚠️ FIX | TreasuryAccount.current_balance typed as `float` in model — must use `Decimal`. Exchange rate not persisted in TreasuryTransaction. |
| II | Multi-Tenant Isolation | ✅ PASS | All queries route through `get_db_connection(company_id)`. |
| III | Double-Entry Integrity | ⚠️ FIX | Treasury expense/transfer update balance BEFORE GL entry — must reorder to GL-first. GL service correctly validates balance. |
| IV | Security & Access Control | ✅ PASS | All endpoints use `require_permission()` and `require_module("treasury")`. |
| V | Regulatory Compliance | ✅ PASS | No direct ZATCA/VAT impact in treasury module. |
| VI | Concurrency Safety | ❌ FAIL | No `SELECT FOR UPDATE` on treasury balance operations. Check collection lacks atomic state transition. |
| VII | Simplicity & Maintainability | ✅ PASS | Follows SQL-first `text()` pattern. Uses GL service for all journal entries. |
| XVII | Observability & Audit Trail | ⚠️ FIX | Treasury router calls `log_activity()` but check/note GL account auto-creation is not logged. |
| XIX | Calculation Centralization | ✅ PASS | All GL posting goes through centralized `create_journal_entry()`. |
| XX | Report Consistency | ⚠️ FIX | Treasury `current_balance` can drift from GL balance due to ordering bug. No reconciliation check. |

**Gate Result**: CONDITIONAL PASS — all violations have identified fixes within this audit scope. No unjustified complexity.

### Post-Design Re-Check

| # | Principle | Pre-Design | Post-Design | Resolution |
|---|-----------|-----------|-------------|------------|
| I | Financial Precision | ⚠️ FIX | ✅ RESOLVED | R-010: float→Numeric(20,4) in data-model.md. R-009: exchange_rate column added to all entities. |
| III | Double-Entry Integrity | ⚠️ FIX | ✅ RESOLVED | R-001: GL-before-balance reorder documented in quickstart.md Step 3. |
| VI | Concurrency Safety | ❌ FAIL | ✅ RESOLVED | R-002: SELECT FOR UPDATE on all treasury/check/note balance mutations. Documented in contracts and quickstart. |
| XVII | Observability & Audit Trail | ⚠️ FIX | ✅ RESOLVED | R-005: ensure_treasury_gl_accounts() logs auto-creation via log_activity(). |
| XX | Report Consistency | ⚠️ FIX | ✅ RESOLVED | R-001 (GL-first) eliminates root cause of balance drift. |

**Post-Design Gate**: ✅ PASS — all 5 violations resolved via research decisions R-001, R-002, R-005, R-009, R-010.

## Project Structure

### Documentation (this feature)

```text
specs/007-audit-treasury/
├── plan.md              # This file
├── spec.md              # Feature specification (completed)
├── research.md          # Phase 0: Research findings
├── data-model.md        # Phase 1: Entity model documentation
├── quickstart.md        # Phase 1: Implementation quickstart
├── contracts/           # Phase 1: API contracts
│   └── treasury-api.md
├── checklists/          # Quality checklists
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── routers/finance/
│   ├── treasury.py          # Treasury accounts, expenses, transfers
│   ├── checks.py            # Checks receivable & payable
│   ├── notes.py             # Notes receivable & payable
│   ├── reconciliation.py    # Bank reconciliation
│   └── cashflow.py          # Cash flow forecasting
├── services/
│   ├── gl_service.py        # Central GL posting (existing, used by treasury)
│   └── forecast_service.py  # Cash flow forecast generation
├── models/domain_models/
│   ├── core_business.py            # TreasuryAccount model
│   ├── operations_financial_support.py  # Check/Note models
│   └── finance_treasury_tax.py     # BankReconciliation, TreasuryTransaction
├── utils/
│   ├── fiscal_lock.py       # Fiscal period lock check
│   └── audit.py             # Audit trail logging
└── tests/
    ├── test_06_treasury.py
    ├── test_14_treasury_scenarios.py
    ├── test_19_checks_notes.py
    └── test_33_checks_notes_due_alerts.py

frontend/src/pages/
├── Treasury/
│   ├── TreasuryHome.jsx
│   ├── TreasuryAccountList.jsx
│   ├── ReconciliationList.jsx
│   ├── ReconciliationForm.jsx
│   ├── TransferForm.jsx
│   ├── ExpenseForm.jsx
│   ├── BankImport.jsx
│   ├── ChecksPayable.jsx
│   ├── ChecksReceivable.jsx
│   ├── ChecksAgingReport.jsx
│   ├── NotesReceivable.jsx
│   ├── NotesPayable.jsx
│   ├── TreasuryCashflowReport.jsx
│   └── TreasuryBalancesReport.jsx
└── CashFlow/
    ├── ForecastList.jsx
    ├── ForecastDetail.jsx
    └── ForecastGenerate.jsx
```

**Structure Decision**: Existing web application layout with backend/frontend split. All changes are remediation within existing files — no new directories needed. New test files will be added to `backend/tests/`.
