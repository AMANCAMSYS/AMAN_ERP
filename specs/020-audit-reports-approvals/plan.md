# Implementation Plan: Reports & Analytics, Approvals & Workflow — Audit & Bug Fixes

**Branch**: `020-audit-reports-approvals` | **Date**: 2026-04-20 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/020-audit-reports-approvals/spec.md`

---

## Summary

Fix ~43 confirmed bugs and issues across two ERP modules — Reports & Analytics (financial reports, KPI dashboards, scheduled reports, analytics — 5 backend files, 15 frontend pages) and Approvals & Workflow (workflow CRUD, approval chain, utilities — 2 backend files, 2 frontend pages). Changes include: fixing a guaranteed runtime crash in `approval_utils.py` (references nonexistent table), wiring up dead frontend controls (export button, view button, dashboard filters), converting all monetary fields from `float` to `Decimal` (Constitution I), replacing hardcoded `'SAR'` currency with `getCurrency()` (Constitution XVIII), fixing Tailwind→Bootstrap CSS, adding i18n for hardcoded strings, adding missing FK constraints and `updated_at` columns, implementing `SELECT ... FOR UPDATE` concurrency protection on approval actions, implementing scheduled report execution (currently a TODO stub), and migrating `recipients` from TEXT to JSONB array. One new table (`scheduled_report_results`) and 3-4 internal helper function extractions in `reports.py`. No existing API URL changes.

---

## Technical Context

**Language/Version**: Python 3.12 (backend) · React 18 / Vite (frontend)  
**Primary Dependencies**: FastAPI · SQLAlchemy 2.0 · Pydantic v2 · Alembic · APScheduler · i18next  
**Storage**: PostgreSQL 15 — one DB per tenant  
**Testing**: pytest (backend) · Vitest + React Testing Library (frontend)  
**Target Platform**: Linux server (backend) · Browser (frontend)  
**Project Type**: Web application (ERP)  
**Constraints**: No URL/method changes (backwards compat); Constitution XXVIII — schema change dual-update  
**Scale/Scope**: All existing company tenants affected by migrations

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|------|--------|-------|
| I — No float for money ⛔ | ✅ Addressed | FR-008..FR-012a: All `float` → `Decimal` across report schemas, KPI services, approval schemas |
| II — Multi-tenant isolation | ✅ Pass | All DB calls via `get_db_connection(company_id)` |
| III — Double-entry integrity | ✅ Pass | No JE changes — reports are read-only from GL |
| IV — Security (no `detail=str(e)`) | ✅ Pass | Validation errors return Pydantic 422; no raw exception exposure |
| VII — SQL-first | ✅ Pass | All fixes use `db.execute(text(…))` with parameterized queries |
| XIV — Approval workflow governance | ✅ Addressed | FR-024..FR-026b: Schema validation, JSONB alignment, concurrency locking, empty-steps rejection |
| XVII — AuditMixin | ✅ Addressed | FR-027..FR-028: 3 tables get missing `updated_at`; `created_by` added to `report_templates` |
| XVIII — Session contract / currency | ✅ Addressed | FR-013..FR-014: Hardcoded `'SAR'` replaced with `getCurrency()` from auth context |
| XIX — Calculation centralization ⛔ | ✅ Addressed | FR-039: Scheduled reports call extracted internal helpers, not duplicate SQL |
| XX — Report consistency ⛔ | ✅ Pass | Report queries unchanged; Decimal conversion prevents rounding drift |
| XXV — No N+1 | ✅ Pass | No N+1 patterns found in reports/approvals |
| XXVII — UI consistency ⛔ | ✅ Addressed | FR-015..FR-023: Bootstrap classes, i18n, date utils, error handling |
| XXVIII — Schema sync ⛔ | ✅ Addressed | FR-034: Every DDL change has matching migration AND `database.py` update |

**Complexity violations**: None.

---

## Project Structure

### Documentation (this feature)

```text
specs/020-audit-reports-approvals/
├── plan.md              ← this file
├── spec.md
├── research.md
├── data-model.md
├── contracts/
│   └── api-contracts.md
├── checklists/
│   └── requirements.md
└── tasks.md             ← created by /speckit.tasks (next phase)
```

### Source Code (affected files only)

```text
backend/
├── routers/
│   ├── reports.py               ← FR-008..FR-010, FR-039 (helper extraction)
│   ├── scheduled_reports.py     ← FR-039, FR-040
│   ├── role_dashboards.py       ← (no changes — delegates to kpi_service)
│   └── approvals.py             ← FR-024..FR-026b
├── services/
│   ├── kpi_service.py           ← FR-012, FR-012a
│   └── industry_kpi_service.py  ← FR-012, FR-012a
├── utils/
│   └── approval_utils.py        ← FR-001..FR-003
├── database.py                  ← FR-026..FR-034 (DDL fixes)
└── migrations/versions/
    ├── <ts>_fix_approval_reports_schema.py
    ├── <ts>_add_scheduled_report_results.py
    └── <ts>_migrate_recipients_to_jsonb.py

frontend/src/
├── pages/
│   ├── Reports/
│   │   ├── ReportBuilder.jsx        ← FR-004, FR-020, FR-021
│   │   ├── DetailedProfitLoss.jsx   ← FR-022
│   │   ├── FXGainLossReport.jsx     ← FR-023
│   │   ├── ConsolidationReports.jsx ← FR-015
│   │   ├── IndustryReport.jsx       ← FR-016
│   │   ├── KPIDashboard.jsx         ← FR-013
│   │   └── SharedReports.jsx        ← FR-018, FR-019
│   ├── KPI/
│   │   └── RoleDashboard.jsx        ← FR-014
│   ├── Analytics/
│   │   ├── DashboardView.jsx        ← FR-005
│   │   └── DashboardEditor.jsx      ← FR-017
│   └── Approvals/
│       ├── ApprovalsPage.jsx        ← FR-006, FR-007, FR-036, FR-037
│       └── WorkflowEditor.jsx       ← FR-035, FR-038
└── locales/
    ├── en.json                      ← new i18n keys
    └── ar.json                      ← new i18n keys
```

---

## Phase 0 — Research

**Status**: Complete. See [`research.md`](./research.md).

Key findings:
- Frontend currency: Use `getCurrency()` from `utils/auth.js` — established pattern
- Scheduled report execution: Call internal helpers directly (`_get_profit_loss_data`, etc.)
- Concurrency control: Use `SELECT ... FOR UPDATE` — the established codebase pattern (15+ sites)
- Database gaps confirmed: 3 tables missing `updated_at`, 4 columns missing FKs, `conditions` default conflict
- No `approval_workflow_steps` table exists — JSONB approach is by design

---

## Phase 1 — Implementation Tasks

Tasks are ordered by dependency. Items within the same group can be done in parallel.

### Group A — Critical Backend Runtime Fixes (no dependencies)

#### A1 — Fix `approval_utils.py` table reference crash (FR-001, FR-002, FR-003)

**File**: `backend/utils/approval_utils.py`

Steps:
1. Replace query on nonexistent `approval_workflow_steps` table with query on `approval_workflows` reading `steps` from JSONB column.
2. Replace direct column references `min_amount`/`max_amount` with JSONB extraction from `conditions` column: `conditions->>'min_amount'`, `conditions->>'max_amount'`.
3. Change `amount` parameter type from `float` to `Decimal`.
4. Add `from decimal import Decimal` import.
5. Cast JSONB-extracted threshold values to `Decimal` for comparison.

#### A2 — Add concurrency protection to approval actions (FR-026b)

**File**: `backend/routers/approvals.py`

Steps:
1. In `take_approval_action` (line ~479), change `SELECT * FROM approval_requests WHERE id = :id` to `SELECT * FROM approval_requests WHERE id = :id FOR UPDATE`.
2. After locking the row, check for existing action: `SELECT COUNT(*) FROM approval_actions WHERE request_id = :rid AND step = :step`.
3. If count > 0, raise `HTTPException(409, "already_actioned")`.

#### A3 — Add empty-steps validation to approval submission (FR-026a)

**File**: `backend/routers/approvals.py`

Steps:
1. In `create_approval_request`, after fetching the matched workflow, parse `steps` JSONB.
2. If `steps` is empty array or null, raise `HTTPException(400, "workflow_misconfigured_no_steps")`.

#### A4 — Replace raw dict with Pydantic schema for approval requests (FR-024)

**Files**: `backend/routers/approvals.py`

Steps:
1. Create `ApprovalRequestCreate` Pydantic schema with validated fields: `document_type`, `document_id`, `amount` (Decimal), `description` (Optional[str]).
2. Replace raw `dict` parameter in `create_approval_request` endpoint with `ApprovalRequestCreate`.

#### A5 — Fix conditions JSONB alignment (FR-025, FR-026)

**Files**: `backend/routers/approvals.py`, `backend/database.py`

Steps:
1. In `WorkflowCreateSchema`, ensure `min_amount` and `max_amount` (now `Decimal`) are mapped into `conditions` JSONB on save (not stored as root-level columns).
2. In `database.py`, fix ALTER TABLE to use `DEFAULT '{}'` (not `'[]'`) for `conditions` column — match CREATE TABLE.
3. Update workflow creation endpoint to wrap `min_amount`/`max_amount` into `{"min_amount": ..., "max_amount": ...}` JSONB.

---

### Group B — Constitution I: Decimal for Money (no dependencies)

#### B1 — Convert report schema models to Decimal (FR-008, FR-009, FR-010)

**File**: `backend/routers/reports.py`

Steps:
1. Find all inline schema/dict classes that use `float` for monetary fields (`TrialBalanceItem`, `FinancialStatementItem`, response dicts).
2. Replace `float` with `Decimal` for all monetary fields.
3. Change `_compute_net_income_from_gl()` return type from `float` to `Decimal`.
4. Replace all `exchange_rate=1.0` literals with `exchange_rate=Decimal("1")`.
5. Add `from decimal import Decimal` if not already imported.

#### B2 — Convert approval schemas to Decimal (FR-011)

**File**: `backend/routers/approvals.py`

Steps:
1. In `WorkflowCreateSchema`, change `min_amount: Optional[float]` and `max_amount: Optional[float]` to `Optional[Decimal]`.
2. Add `from decimal import Decimal` import.

#### B3 — Fix KPI division-by-zero handling (FR-012, FR-012a)

**Files**: `backend/services/kpi_service.py`, `backend/services/industry_kpi_service.py`

Steps:
1. Find all ratio calculations (margin, turnover, current ratio, etc.) that divide by a potentially-zero denominator.
2. Wrap each in a safe division pattern: `result = numerator / denominator if denominator else Decimal("0")`.
3. Ensure monetary values used in KPI calculations are `Decimal` (from GL query results which return `Numeric` → already Decimal in Python via psycopg2).

---

### Group C — Frontend Critical Fixes (no backend dependencies; parallel with A-B)

#### C1 — Wire ReportBuilder export button (FR-004)

**File**: `frontend/src/pages/Reports/ReportBuilder.jsx`

Steps:
1. Find the Export button element.
2. Add `onClick={handleExport}` (or the appropriate export handler function).

#### C2 — Wire DashboardView filters to API (FR-005)

**File**: `frontend/src/pages/Analytics/DashboardView.jsx`

Steps:
1. Find where `startDate`, `endDate`, `branchId` state variables are captured.
2. In the data fetch function (useEffect or fetch handler), include these as query parameters: `params: { start_date: startDate, end_date: endDate, branch_id: branchId }`.

#### C3 — Wire ApprovalsPage View button + fix double-fetch (FR-006, FR-007)

**File**: `frontend/src/pages/Approvals/ApprovalsPage.jsx`

Steps:
1. Find the View button and add `onClick` handler that navigates to or opens the approval request detail.
2. Find duplicate `useEffect` or duplicate API calls on mount — consolidate to a single fetch.

#### C4 — Fix ReportBuilder state and shadowing bugs (FR-020, FR-021)

**File**: `frontend/src/pages/Reports/ReportBuilder.jsx`

Steps:
1. Find `.map(t =>` that shadows the `t` translation function. Rename callback parameter to `item`, `col`, or similar.
2. Fix `loadReport` to use `useEffect` or callback pattern to preview after state update: use `useEffect` watching config changes, or pass the new config directly to `handlePreview(newConfig)`.

#### C5 — Fix hardcoded currency in KPI/Role dashboards (FR-013, FR-014)

**Files**: `frontend/src/pages/Reports/KPIDashboard.jsx`, `frontend/src/pages/KPI/RoleDashboard.jsx`

Steps:
1. KPIDashboard.jsx: Add `import { getCurrency } from '../../utils/auth'`. Add `const currency = getCurrency() || 'SAR'` in component body. Replace hardcoded `'SAR'` on line 34.
2. RoleDashboard.jsx: Optionally standardize to `getCurrency()` pattern for consistency (currently uses `user?.currency || 'SAR'` which is functionally correct).

---

### Group D — Frontend UI and i18n Fixes (parallel with C)

#### D1 — Fix ConsolidationReports Tailwind→Bootstrap (FR-015)

**File**: `frontend/src/pages/Reports/ConsolidationReports.jsx`

Steps:
1. Find all Tailwind CSS classes (`text-xl`, `grid grid-3`, etc.).
2. Replace with Bootstrap equivalents: `h5` for `text-xl`, `row`+`col-md-4` for grid.

#### D2 — Fix IndustryReport hardcoded strings (FR-016)

**File**: `frontend/src/pages/Reports/IndustryReport.jsx`

Steps:
1. Find all hardcoded Arabic and English strings.
2. Add corresponding keys to `en.json` and `ar.json`.
3. Replace hardcoded strings with `t('reports.industry.key_name')`.

#### D3 — Fix DashboardEditor hardcoded labels (FR-017)

**File**: `frontend/src/pages/Analytics/DashboardEditor.jsx`

Steps:
1. Find hardcoded English widget type labels.
2. Add i18n keys and replace with `t()` calls.

#### D4 — Fix SharedReports date formatting and navigation (FR-018, FR-019)

**File**: `frontend/src/pages/Reports/SharedReports.jsx`

Steps:
1. Replace `toLocaleDateString()` with project date utility: `import { formatDate } from '../../utils/dateUtils'`.
2. Make report names clickable: wrap in `<Link>` or add `onClick` that navigates to the report view.

#### D5 — Fix DetailedProfitLoss export error handling (FR-022)

**File**: `frontend/src/pages/Reports/DetailedProfitLoss.jsx`

Steps:
1. Wrap `handleExport` body in try/catch.
2. In catch: `toast.error(t('common.exportError'))` or similar.

#### D6 — Fix FXGainLossReport undefined values (FR-023)

**File**: `frontend/src/pages/Reports/FXGainLossReport.jsx`

Steps:
1. Find gain/loss calculation that may use undefined values.
2. Add null checks: `const gain = (value ?? 0) - (cost ?? 0)` or similar defensive pattern.

---

### Group E — Approval Workflow Frontend UX (depends on A2, A5 for API alignment)

#### E1 — Add step reordering to WorkflowEditor (FR-035)

**File**: `frontend/src/pages/Approvals/WorkflowEditor.jsx`

Steps:
1. Add Move Up / Move Down buttons next to each step in the steps list.
2. Implement `handleMoveUp(index)` and `handleMoveDown(index)` that swap array elements.
3. Update step `order` fields after reorder.

#### E2 — Fix WorkflowEditor conditions mapping (FR-038)

**File**: `frontend/src/pages/Approvals/WorkflowEditor.jsx`

Steps:
1. In the save/submit handler, wrap `min_amount` and `max_amount` into `conditions: { min_amount, max_amount }` in the API payload.
2. On load, extract `min_amount`/`max_amount` from `conditions` JSONB for editing.

#### E3 — Add visual approval chain to ApprovalsPage (FR-036)

**File**: `frontend/src/pages/Approvals/ApprovalsPage.jsx`

Steps:
1. Replace "Step X of Y" text with a visual stepper component.
2. For each step, show: step number, approver name, status (completed/current/pending), action date if completed.
3. Use Bootstrap `list-group` or a simple horizontal step indicator.

#### E4 — Fix inconsistent API route prefixes (FR-037)

**File**: `frontend/src/pages/Approvals/ApprovalsPage.jsx`

Steps:
1. Audit all API calls — find places using `/workflow/*` vs `/approvals/*`.
2. Standardize to a single prefix that matches the backend router prefix.

---

### Group F — Scheduled Reports Implementation (depends on B1 for Decimal helpers)

#### F1 — Extract report internal helpers (FR-039 prerequisite)

**File**: `backend/routers/reports.py`

Steps:
1. Extract `_get_trial_balance_data(db, start_date, end_date, branch_id)` from `get_trial_balance` endpoint.
2. Extract `_get_cashflow_data(db, start_date, end_date, branch_id)` from `get_cashflow_report` endpoint.
3. Extract `_get_general_ledger_data(db, account_id, start_date, end_date, branch_id)` from `get_general_ledger` endpoint.
4. Existing helpers `_get_profit_loss_data` and `_get_balance_sheet_data` remain as-is.

#### F2 — Implement `_execute_scheduled_report` (FR-039)

**File**: `backend/routers/scheduled_reports.py`

Steps:
1. Replace TODO stub with dispatcher mapping `report_type` → internal helper function.
2. Parse `report_config` JSONB for parameters (start_date, end_date, branch_id, account_id).
3. Call appropriate helper: `_get_profit_loss_data(db, ...)`, `_get_balance_sheet_data(db, ...)`, etc.
4. Store result in `scheduled_report_results` table.
5. Update `last_run_at`, `last_status`, compute `next_run_at`.
6. On failure: set `last_status = 'failed'`, log error.

#### F3 — Migrate recipients to JSONB (FR-040)

**Files**: `backend/routers/scheduled_reports.py`, `backend/database.py`

Steps:
1. In `database.py`: Change `recipients TEXT NOT NULL` to `recipients JSONB DEFAULT '[]'`.
2. In `scheduled_reports.py`: Update all reads/writes of `recipients` to use JSONB array instead of comma-separated parsing.
3. Create migration that converts existing TEXT data: `UPDATE scheduled_reports SET recipients = to_jsonb(string_to_array(recipients, ','))`.

---

### Group G — Database Schema Fixes (Constitution XXVIII — do after backend code is working)

#### G1 — Add missing audit columns and FKs (FR-027..FR-032)

**File**: `backend/database.py`  
**Migration**: `<ts>_fix_approval_reports_schema.py`

Steps:
1. `shared_reports`: Add `updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP`.
2. `report_templates`: Add `updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP`, `created_by INTEGER REFERENCES company_users(id)`.
3. `approval_requests.current_approver_id`: Add FK constraint to `company_users(id)`.
4. `approval_requests.escalated_to`: Add FK constraint to `company_users(id)`.
5. `approval_actions.actioned_by`: Add FK constraint to `company_users(id)`.
6. `analytics_dashboards.created_by`: Change from `VARCHAR(100)` to `INTEGER REFERENCES company_users(id)`.
7. `analytics_dashboards.updated_by`: Change from `VARCHAR(100)` to `INTEGER REFERENCES company_users(id)`.
8. Fix `approval_workflows` ALTER to use `DEFAULT '{}'` (not `'[]'`).
9. Create matching Alembic migration for all changes.

#### G2 — Add missing indexes (FR-033)

**File**: `backend/database.py`  
**Migration**: (same migration as G1 or separate)

Steps:
1. Add `CREATE INDEX IF NOT EXISTS idx_approval_requests_workflow ON approval_requests(workflow_id)`.
2. Add `CREATE INDEX IF NOT EXISTS idx_approval_requests_requested_by ON approval_requests(requested_by)`.
3. Add `CREATE INDEX IF NOT EXISTS idx_report_templates_type ON report_templates(template_type)`.
4. Add `CREATE INDEX IF NOT EXISTS idx_approval_workflows_doc_type ON approval_workflows(document_type)`.

#### G3 — Add `scheduled_report_results` table (FR-039 dependency)

**File**: `backend/database.py`  
**Migration**: `<ts>_add_scheduled_report_results.py`

Steps:
1. Add CREATE TABLE:
   ```sql
   CREATE TABLE IF NOT EXISTS scheduled_report_results (
       id SERIAL PRIMARY KEY,
       scheduled_report_id INTEGER REFERENCES scheduled_reports(id) ON DELETE CASCADE,
       report_data JSONB NOT NULL,
       generated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
       status VARCHAR(20) DEFAULT 'completed'
   );
   CREATE INDEX IF NOT EXISTS idx_report_results_schedule ON scheduled_report_results(scheduled_report_id);
   ```
2. Create matching Alembic migration.

#### G4 — Recipients TEXT→JSONB migration (FR-040)

**Migration**: `<ts>_migrate_recipients_to_jsonb.py`

Steps:
1. `ALTER TABLE scheduled_reports ALTER COLUMN recipients TYPE JSONB USING to_jsonb(string_to_array(recipients, ','))`.
2. `ALTER TABLE scheduled_reports ALTER COLUMN recipients SET DEFAULT '[]'::jsonb`.

---

## Phase 2 — Verification

### Backend Verification

| Check | Command / Method |
|-------|-----------------|
| Import check | `python -c "from routers.reports import router; from routers.approvals import router; from routers.scheduled_reports import router"` |
| approval_utils | `POST /api/purchases/orders` with amount > threshold — auto_submit_for_approval completes without SQL error |
| Approval create | `POST /api/approvals/requests` with missing fields — returns 422 (not 500) |
| Approval concurrency | Two simultaneous `POST /api/approvals/{id}/action` on same step — second gets 409 |
| Empty steps | Create workflow with `steps: []`, submit approval request — returns 400 |
| Decimal precision | Generate trial balance — all amounts are Decimal, debits = credits exactly |
| Net income | `_compute_net_income_from_gl()` returns `Decimal` type |
| Exchange rate | No `1.0` float literal in reports.py — all `Decimal("1")` |
| KPI zero-div | KPI endpoint with zero revenue — returns 0 for margin (not error) |
| Scheduled report | Trigger scheduled report execution — generates and stores result |
| Recipients JSONB | Create scheduled report with recipients — stored as JSONB array |
| Migration | `alembic upgrade head` on test DB — all migrations apply cleanly |
| Schema parity | Fresh `database.py` create vs. migrated DB — identical column list |
| Conditions default | New `approval_workflows` row — `conditions` defaults to `'{}'` |

### Frontend Verification

| Check | Method |
|-------|--------|
| ReportBuilder export | Click Export button — export function fires |
| DashboardView filters | Set date/branch filters — API request includes parameters |
| ApprovalsPage View | Click View button — navigates to/shows detail |
| ApprovalsPage mount | Open page — network tab shows 1 fetch (not 2) |
| KPIDashboard currency | Company with USD currency — KPI shows "USD" |
| RoleDashboard currency | Company with EUR currency — dashboard shows "EUR" |
| ConsolidationReports | Open page — all elements styled with Bootstrap |
| IndustryReport i18n | Switch to Arabic — all labels translated |
| DashboardEditor i18n | Open editor — widget types translated |
| SharedReports dates | Open page — dates use project date utility format |
| ReportBuilder shadow | Open ReportBuilder — no translation errors in column mappings |
| ReportBuilder load | Load saved report — preview shows loaded config |
| DetailedProfitLoss | Trigger export error — toast shown |
| FXGainLossReport | Report with no FX data — no NaN values |
| WorkflowEditor reorder | Create 3-step workflow, move step 2 up — step order updates |
| WorkflowEditor conditions | Set min/max amount — saved inside conditions JSONB |
| Approval chain visual | View pending approval — visual chain shows step status |
| API route consistency | All approval API calls use same prefix |

---

## Implementation Order (suggested)

```
Day 1 — Critical backend fixes:
  A1 (approval_utils crash)            ← P1 runtime crash fix
  A2 (concurrent approval locking)     ← P1 race condition fix
  A3 (empty steps validation)          ← P1 misconfigured workflow guard
  A4 (approval request schema)         ← P2 raw dict → Pydantic
  A5 (conditions JSONB alignment)      ← P2 schema-to-DB mismatch
  C1 (ReportBuilder export button)     ← P1 frontend dead button (parallel)
  C3 (ApprovalsPage view + fetch)      ← P1 frontend dead button (parallel)

Day 2 — Decimal conversion + frontend critical:
  B1 (report schemas float→Decimal)    ← P2 Constitution I
  B2 (approval schemas float→Decimal)  ← P2 Constitution I
  B3 (KPI zero-div handling)           ← P2 edge case
  C2 (DashboardView filters)           ← P1 non-functional filters
  C4 (ReportBuilder shadow + state)    ← P3 stale state bug
  C5 (currency hardcode fix)           ← P2 Constitution XVIII

Day 3 — Frontend i18n + CSS fixes:
  D1 (ConsolidationReports Bootstrap)  ← P2 Tailwind→Bootstrap
  D2 (IndustryReport i18n)            ← P2 hardcoded strings
  D3 (DashboardEditor i18n)           ← P2 hardcoded labels
  D4 (SharedReports dates + links)    ← P2/P3 date formatting
  D5 (DetailedProfitLoss error)       ← P3 missing try/catch
  D6 (FXGainLossReport NaN)           ← P3 undefined values

Day 4 — Approval frontend UX:
  E1 (step reordering)                ← P3 workflow editor UX
  E2 (conditions mapping)            ← P3 frontend-backend alignment
  E3 (visual approval chain)         ← P3 approval UX
  E4 (API prefix consistency)        ← P3 cleanup

Day 5 — Scheduled reports + schema:
  F1 (extract report helpers)        ← prerequisite for F2
  F2 (implement execution)           ← P3 TODO stub
  G1 (audit columns + FKs)           ← P2 schema integrity
  G2 (indexes)                       ← P2 performance
  G3 (report_results table)          ← P3 scheduled reports storage

Day 6 — Recipients migration + verification:
  F3 (recipients TEXT→JSONB router)   ← P3 data format
  G4 (recipients migration)          ← P3 migration
  Full verification pass
```

---

## Risks

| Risk | Mitigation |
|------|-----------|
| `analytics_dashboards.created_by` VARCHAR→INT migration loses data | Migration converts existing username strings to user IDs via lookup query; null if no match found; backup before migration |
| `SELECT ... FOR UPDATE` on approvals may cause brief contention | Approval actions are low-frequency (seconds, not milliseconds); lock duration is minimal |
| Extracting report helpers changes function boundaries in 2400-line file | Extract into clearly-named `_get_*_data()` functions; existing endpoints call them — no API change |
| Scheduled report execution adds background DB load | Reports run every 15 min max (APScheduler interval); individual report queries are already optimized for interactive use |
| Recipients TEXT→JSONB migration may fail on malformed data | Migration uses `string_to_array` with comma delimiter; add `COALESCE` for null handling; test on staging first |
| i18n key additions require both `en.json` and `ar.json` updates | Arabic translations for new keys may need review; add English fallback initially |
| Decimal conversion changes JSON serialization format | Pydantic v2 serializes Decimal as string by default; verify frontend `formatNumber()` handles both string and number inputs |
