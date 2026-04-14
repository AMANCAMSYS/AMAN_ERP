# Implementation Plan: Audit Accounting Module

**Branch**: `006-audit-accounting` | **Date**: 2026-04-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/006-audit-accounting/spec.md`

## Summary

Comprehensive audit of the accounting module — chart of accounts, journal entries (double-entry lifecycle), financial reports, budgets, currencies, fiscal period locking, recurring journals, cost centers, intercompany transactions, costing policies, and balance reconciliation. The audit examines all backend routers, services, utilities, and models, plus all 34 frontend pages. Cross-module tracing verifies that GL postings from sales, purchases, treasury, payroll, inventory, assets, and POS all flow through the centralized GL service and respect fiscal locks.

## Technical Context

**Language/Version**: Python 3.12 (backend), React 18 / Vite (frontend)  
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 (SQL-first via `text()`), Pydantic, APScheduler, openpyxl, ReportLab, i18next, React Router  
**Storage**: PostgreSQL 15 (multi-tenant `aman_{company_id}` + system `aman_system`), Redis (caching)  
**Testing**: pytest (backend), vitest (frontend)  
**Target Platform**: Linux server (Docker), modern browsers  
**Project Type**: Web application (ERP audit)  
**Performance Goals**: Dashboard < 3s for 100k+ transactions; trial balance generation < 2s  
**Constraints**: Decimal-only arithmetic for all financial calculations; tenant isolation on every query; fiscal period lock enforcement across all sub-ledgers  
**Scale/Scope**: 18 backend files (8 routers, 4 services, 4 utils, 2 models), 34 frontend pages, 9 cross-module integration points

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Constitution Principle | Relevant to Audit? | Status |
|---|----------------------|-------------------|--------|
| I | Financial Precision | **YES** — core focus. Verify Decimal usage, no float math in calculations | ✅ PASS — GL service uses `Decimal("0.01")` with `ROUND_HALF_UP` throughout. Float used only in JSON serialization (display-only). |
| II | Multi-Tenant Isolation | **YES** — every accounting endpoint must scope to tenant DB | ✅ PASS — `get_db_connection(current_user.company_id)` on every request |
| III | Double-Entry Integrity | **YES** — primary audit target. Verify debit=credit enforcement | ✅ PASS — `validate_je_lines()` enforces balance; `create_journal_entry()` is centralized in `gl_service.py` |
| IV | Security & Access Control | **YES** — verify permissions, branch access, error sanitization | ✅ PASS — `require_permission()` on all endpoints; `validate_branch_access()` for branch-scoped ops |
| V | Regulatory Compliance | **YES** — SOCPA/IFRS COA structure, ZATCA integration points | ✅ PASS — COA follows 1xxxx-5xxxx numbering; tax integration delegated to tax module |
| VI | Concurrency Safety | **YES** — sequential numbering under concurrent posting, balance updates | ⚠️ AUDIT — verify `SELECT ... FOR UPDATE` on sequence counter; verify atomic balance updates |
| VII | Simplicity & Maintainability | **YES** — SQL-first pattern, no ORM query-building | ✅ PASS — all queries use `text()` with parameterized `:param` syntax |
| VIII | Inventory Integrity | **PARTIAL** — costing policy management touches inventory | ✅ PASS — costing policy switch creates snapshots and history |
| XVII | Observability & Audit Trail | **YES** — verify `log_activity()` on all state changes | ⚠️ AUDIT — GL service does not call `log_activity()` internally; relies on caller |
| XIX | Calculation Centralization | **YES** — verify single canonical balance calculation | ⚠️ AUDIT — `update_account_balance()` is canonical but balance reconciliation checks for drift |
| XX | Report Consistency | **YES** — trial balance = GL, balance sheet balances | ⚠️ AUDIT — verify reports query `journal_lines` directly, not cached summaries |
| XXI | Cross-Module Data Consistency | **YES** — account references via FK, exchange rates from single table | ✅ PASS — modules store `account_id` FK only |
| XXII | Transaction Validation Pipeline | **YES** — verify validation order on JE creation | ✅ PASS — gl_service validates: fiscal period → line validation → persist → balance update |
| XXIII | Idempotency & Duplicate Prevention | **YES** — sequential numbering, no duplicate JE numbers | ⚠️ AUDIT — verify atomicity of sequence number generation |
| XXVI | Calculation Traceability | **YES** — exchange rate audit trail on multi-currency JEs | ✅ PASS — JE stores currency, exchange_rate, source, source_id per entry |

**Gate Result**: ✅ **PASS** — No blocking violations. 5 items marked ⚠️ AUDIT require verification during implementation (not design blockers).

### Post-Phase 1 Re-evaluation

After research (Phase 0) and design (Phase 1), the 5 ⚠️ AUDIT items are now characterized:

| # | Principle | Phase 0 Finding | Severity | Action |
|---|-----------|-----------------|----------|--------|
| VI | Concurrency Safety | **CONFIRMED DEFECT**: `generate_sequential_number()` uses `SELECT MAX(...)` without `FOR UPDATE`. Race condition under concurrent posting. | CRITICAL | Task: Add `FOR UPDATE` lock or `INSERT ... RETURNING` with DB sequence |
| XVII | Observability | **CONFIRMED GAP**: `gl_service.create_journal_entry()` does NOT call `log_activity()` internally. 6 call sites in `projects.py` skip logging. | HIGH | Task: Add `log_activity()` inside GL service; audit all callers |
| XIX | Calculation Centralization | **CONFIRMED BYPASS**: `scripts/populate_company_data.py` and `scripts/reconcile_balances.py` update balances via direct SQL, bypassing canonical `update_account_balance()` | MEDIUM | Task: Route balance updates through canonical function |
| XX | Report Consistency | **MINOR**: Cash flow report uses `float()` before aggregation → precision loss. All other reports query `journal_lines` directly (correct). | LOW | Task: Replace `float()` with `Decimal` in cash flow report |
| XXIII | Idempotency | Same as VI — sequential numbering atomicity. Additionally: inventory adjustments bypass fiscal lock (CRITICAL). | CRITICAL | Task: Add fiscal lock check to inventory adjustments |

**Post-Design Gate**: ✅ **PASS** — All issues are implementation tasks, not design blockers. 2 CRITICAL defects require immediate remediation in tasks.

## Project Structure

### Documentation (this feature)

```text
specs/006-audit-accounting/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── api-contracts.md
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── routers/
│   └── finance/
│       ├── accounting.py          # Core GL & COA endpoints
│       ├── budgets.py             # Budget management
│       ├── cost_centers.py        # Cost center CRUD
│       ├── currencies.py          # Currency management
│       ├── intercompany.py        # Intercompany v1 (deprecated)
│       ├── intercompany_v2.py     # Intercompany v2 (reciprocal)
│       ├── advanced_workflow.py   # Approval workflow SLA
│       └── costing_policies.py    # Costing method management
├── services/
│   ├── gl_service.py              # Central journal entry creation
│   ├── intercompany_service.py    # Reciprocal posting service
│   ├── industry_coa_templates.py  # COA templates by industry
│   └── industry_gl_rules.py      # Auto-posting rules by industry
├── utils/
│   ├── accounting.py              # JE validation, balance update, sequential numbering
│   ├── fiscal_lock.py             # Fiscal period locking
│   ├── balance_reconciliation.py  # Balance verification
│   └── optimistic_lock.py        # Concurrent edit protection
├── models/
│   ├── core_accounting.py         # ORM models (Account, JournalEntry, JournalLine)
│   └── domains/
│       └── finance.py             # Finance domain re-exports
└── tests/

frontend/src/pages/
├── Accounting/                    # 26 pages (COA, GL, JE, reports, budgets, fiscal, recurring, closing, currencies, opening balances, tax audit, cost centers)
├── Intercompany/                  # 5 pages (transactions, mappings, entity tree, consolidation)
└── Costing/                       # 3 pages (cost layers, method form, valuation report)
```

**Structure Decision**: Existing web application structure (backend + frontend). This is an audit — no new directories are created. All work is examination, testing, and fixing of existing code.

## Complexity Tracking

> No constitution violations requiring justification. All 5 ⚠️ AUDIT items are verification tasks, not design trade-offs.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
