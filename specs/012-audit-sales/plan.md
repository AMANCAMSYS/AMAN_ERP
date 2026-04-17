# Implementation Plan: Audit Sales Module — تدقيق وحدة المبيعات

**Branch**: `012-audit-sales` | **Date**: 2026-04-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/012-audit-sales/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Audit the entire sales module (backend + frontend) for financial precision violations, missing audit infrastructure, and deprecated error-handling patterns. Backend: replace all `float()` serialization with `str()`, migrate Pydantic schemas from `float` to `Decimal`, add `AuditMixin` to sales-exclusive domain models, add audit columns to sales tables, and verify existing fiscal period checks. Frontend: replace all `parseFloat()` with `Number()`/`String()`, replace `console.error` with `useToast`/`showToast`, replace `toastEmitter` with `useToast`, and ensure `formatNumber()` for display. Verify commission calculation correctness with functional test scenarios. Cross-module files are out of scope for code changes — boundary verification only.

## Technical Context

**Language/Version**: Python 3.12 (backend), React 18 / Vite (frontend)
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 (SQL-first via `text()`), Pydantic, i18next, React Router
**Storage**: PostgreSQL 15 (multi-tenant `aman_{company_id}` + system `aman_system`), Redis (rate limiting/cache)
**Testing**: py_compile (backend), vite build (frontend), manual API verification
**Target Platform**: Linux server (backend), browser (frontend)
**Project Type**: Web application (ERP)
**Performance Goals**: N/A — audit refactoring, no new features
**Constraints**: Zero regressions — all existing functionality must continue working after audit fixes
**Scale/Scope**: 38 frontend files (34 Sales + 4 CPQ), 12 backend files (11 routers + 1 service), 4 schema files, domain models

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Constitution Section | Requirement | Status | Notes |
|---|---------------------|-------------|--------|-------|
| 1 | I. Financial Precision ⛔ | `float`/`double`/JS `Number` forbidden for monetary values; `Decimal` + `ROUND_HALF_UP` in Python; string-based amounts in JS | **REMEDIATING** | This is the primary goal of the audit — 38 backend `float()`, 26 Pydantic `float` fields, 95 frontend `parseFloat` to fix |
| 2 | III. Double-Entry Integrity ⛔ | All entries via `gl_service.py`; `check_fiscal_period_open()` gates all transactions | **VERIFY** | 7 fiscal checks already exist in 4 files — verify correctness, add if missing |
| 3 | VII. Simplicity & Maintainability | `db.execute(text(…))` SQL-first; Pydantic at API boundary; `logger.error()` not `print()` | **PASS** | No structural changes — only type corrections |
| 4 | XIII. Sales & CRM Workflow | State machine `Quotation→SO→Delivery→Invoice→Receipt`; credit limit; commissions per invoice | **VERIFY** | Commission calculation correctness to be verified with functional tests |
| 5 | XVII. Observability & Audit Trail | `AuditMixin` on ALL domain models; `SoftDeleteMixin` on business entities | **REMEDIATING** | AuditMixin missing from sales-exclusive models — to be added |
| 6 | XIX. Calculation Centralization ⛔ | No duplicate calc logic; tax via shared utility; `compute_invoice_totals()` for all invoice types; frontend: NO monetary calcs, `formatNumber()` display only | **VERIFY** | Ensure `float()` fixes don't duplicate logic; verify `formatNumber()` usage |
| 7 | XXII. Transaction Validation Pipeline | Pydantic→Permission→Fiscal→Business Rules→Calc→Persist→Post-persist | **VERIFY** | Verify existing pipeline order in sales endpoints |

**Gate Result**: **PASS** — No blocking violations. Items 1 and 5 are the audit's remediation targets. Items 2, 4, 6, 7 require verification during implementation.

### Post-Design Re-evaluation

| # | Section | Pre-Design | Post-Design | Notes |
|---|---------|-----------|-------------|-------|
| 1 | I. Financial Precision ⛔ | REMEDIATING | **REMEDIATING** | Research confirmed: 38 backend float(), 1 Pydantic float field in sales_credit_notes, 95 frontend parseFloat. Patterns documented in research.md §6-7. |
| 2 | III. Double-Entry Integrity ⛔ | VERIFY | **PASS** | All 7 fiscal checks verified correct (research.md §4). delivery_orders.py needs runtime check during implementation. |
| 3 | VII. Simplicity & Maintainability | PASS | **PASS** | No structural changes. Type corrections only. |
| 4 | XIII. Sales & CRM Workflow | VERIFY | **VERIFY** | Commission formula identified: `round(total * rate / 100, 2)` — uses float, must be fixed to Decimal + ROUND_HALF_UP. Functional test scenarios defined. |
| 5 | XVII. Observability & Audit Trail | REMEDIATING | **REMEDIATING** | 12 models need AuditMixin additions; 10 database tables need column additions. Full gap analysis in data-model.md. |
| 6 | XIX. Calculation Centralization ⛔ | VERIFY | **PASS** | No duplicate logic introduced. `float→str` is a type change, not logic duplication. Commission calc is single location. |
| 7 | XXII. Transaction Validation Pipeline | VERIFY | **PASS** | Pipeline order verified in fiscal check research. All checks correctly placed before GL posting. |

**Post-Design Gate Result**: **PASS** — All constitution requirements either already satisfied or being remediated by this audit.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── routers/
│   ├── sales/
│   │   ├── customers.py          # float→str fixes
│   │   ├── quotations.py         # float→str fixes
│   │   ├── orders.py             # float→str fixes
│   │   ├── invoices.py           # float→str + fiscal check verify
│   │   ├── returns.py            # float→str + fiscal check verify
│   │   ├── credit_notes.py       # float→str + fiscal check verify
│   │   ├── vouchers.py           # float→str + fiscal check verify
│   │   ├── cpq.py                # float→str fixes
│   │   ├── sales_improvements.py # float→str + commission logic verify
│   │   └── schemas.py            # float→Decimal in Pydantic models
│   └── delivery_orders.py        # float→str fixes
├── services/
│   └── cpq_service.py            # float→str/Decimal fixes
├── schemas/
│   ├── cpq.py                    # float→Decimal
│   ├── sales_credit_notes.py     # float→Decimal
│   └── sales_improvements.py     # float→Decimal
├── models/
│   └── domains/
│       └── sales.py              # AuditMixin on sales-exclusive models
└── database.py                   # Audit columns for sales tables

frontend/src/pages/
├── Sales/
│   ├── AgingReport.jsx           # parseFloat→Number, console.error→showToast
│   ├── ContractAmendments.jsx
│   ├── ContractDetails.jsx
│   ├── ContractForm.jsx
│   ├── ContractList.jsx
│   ├── CustomerDetails.jsx
│   ├── CustomerForm.jsx
│   ├── CustomerGroups.jsx
│   ├── CustomerList.jsx
│   ├── CustomerReceipts.jsx
│   ├── CustomerStatement.jsx
│   ├── DeliveryOrderDetails.jsx
│   ├── DeliveryOrderForm.jsx
│   ├── DeliveryOrders.jsx
│   ├── InvoiceDetails.jsx
│   ├── InvoiceForm.jsx
│   ├── InvoiceList.jsx
│   ├── InvoicePrintModal.jsx
│   ├── ReceiptDetails.jsx
│   ├── ReceiptForm.jsx
│   ├── SalesCommissions.jsx
│   ├── SalesCreditNotes.jsx
│   ├── SalesDebitNotes.jsx
│   ├── SalesHome.jsx
│   ├── SalesOrderDetails.jsx
│   ├── SalesOrderForm.jsx
│   ├── SalesOrders.jsx
│   ├── SalesQuotationDetails.jsx
│   ├── SalesQuotationForm.jsx
│   ├── SalesQuotations.jsx
│   ├── SalesReports.jsx
│   ├── SalesReturnDetails.jsx
│   ├── SalesReturnForm.jsx
│   └── SalesReturns.jsx
└── CPQ/
    ├── ConfigurableProducts.jsx
    ├── Configurator.jsx
    ├── QuoteDetail.jsx
    └── QuoteList.jsx
```

**Structure Decision**: Existing web application structure (backend + frontend). No new files or directories created — all changes are in-place edits to existing files. The audit modifies 38 frontend JSX files, 11 backend router files, 1 service file, 4 schema files, domain models, and database.py.

## Complexity Tracking

> No constitution violations requiring justification. All changes are in-place type corrections and infrastructure additions following established patterns.
