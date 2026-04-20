# Implementation Plan: Projects, Contracts & Fixed Assets — Audit & Bug Fixes

**Branch**: `019-audit-projects-assets` | **Date**: 2026-04-20 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/019-audit-projects-assets/spec.md`

---

## Summary

Fix ~50 confirmed bugs and issues across three ERP modules — Projects (59 endpoints), Contracts (12 endpoints), and Fixed Assets (31 endpoints). Changes include: fixing 6 frontend runtime crashes, correcting wrong SQL column/table names in ~10 backend queries, converting all monetary fields from `float` to `Decimal` (Constitution I), adding missing DDL columns to `database.py` with matching Alembic migrations (Constitution XXVIII), replacing raw `dict` inputs with Pydantic schemas, fixing asset depreciation persistence for non-straight-line methods, implementing IAS 16 revaluation surplus tracking, and fixing IFRS 16 lease payment posting. No new endpoints except one lease payment endpoint (FR-031). No API URL changes.

---

## Technical Context

**Language/Version**: Python 3.12 (backend) · React 18 / Vite (frontend)  
**Primary Dependencies**: FastAPI · SQLAlchemy 2.0 · Pydantic v2 · Alembic · i18next  
**Storage**: PostgreSQL 15 — one DB per tenant  
**Testing**: pytest (backend) · Vitest + React Testing Library (frontend)  
**Target Platform**: Linux server (backend) · Browser (frontend)  
**Project Type**: Web application (ERP)  
**Constraints**: No URL/method changes (backwards compat); Constitution XXVIII — schema change dual-update  
**Scale/Scope**: All existing company tenants affected by migrations

---

## Constitution Check

| Gate | Status | Notes |
|------|--------|-------|
| I — No float for money ⛔ | ✅ Addressed | FR-019..FR-023: All `float` → `Decimal` across 3 schema files + model hints + GL calls |
| II — Multi-tenant isolation | ✅ Pass | All DB calls via `get_db_connection(company_id)` |
| III — Double-entry integrity | ✅ Pass | GL entries via `gl_service.create_journal_entry()` only |
| IV — Security (no `detail=str(e)`) | ✅ Addressed | FR-050: path traversal fix; FR-051: re-raise HTTPException; FR-024: contract error handling |
| VII — SQL-first | ✅ Pass | All fixes use `db.execute(text(...))` with parameterized queries |
| XII — Asset lifecycle | ✅ Addressed | FR-029..FR-035: depreciation schedules, disposal, revaluation, IFRS 16 |
| XV — Project & contract mgmt | ✅ Pass | Bug fixes only; no workflow changes |
| XVII — AuditMixin | ✅ Addressed | 15 tables get missing `updated_at` |
| XXV — No N+1 | ✅ Addressed | FR-027: `list_contracts` batched query |
| XXVII — UI consistency | ✅ Addressed | Bootstrap classes replace Tailwind; error toasts added |
| XXVIII — Schema sync ⛔ | ✅ Addressed | Every DDL change has matching migration AND `database.py` update |

**Complexity violations**: None.

---

## Project Structure

### Documentation (this feature)

```text
specs/019-audit-projects-assets/
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
│   ├── projects.py              ← FR-001..FR-009, FR-036..FR-040, FR-050
│   ├── contracts.py             ← FR-010, FR-024..FR-028, FR-037
│   └── finance/
│       └── assets.py            ← FR-005..FR-007, FR-029..FR-035, FR-041, FR-051..FR-052
├── schemas/
│   ├── projects.py              ← FR-019 (float→Decimal) + new risk/dep schemas
│   ├── contracts.py             ← FR-020 (float→Decimal) + ContractUpdate + AmendmentCreate
│   └── assets.py                ← FR-021 (float→Decimal) + expand AssetUpdate + new schemas
├── models/domains/
│   ├── projects_core.py         ← FR-023 (Mapped[float]→Mapped[Decimal])
│   ├── projects_execution.py    ← FR-023 (risk model types)
│   └── projects_contracts_expenses.py ← FR-023 (contract model types)
├── database.py                  ← DDL fixes: missing columns, types, indexes, updated_at
└── migrations/versions/
    ├── <ts>_add_project_retainer_columns.py
    ├── <ts>_add_updated_at_to_project_asset_tables.py
    ├── <ts>_widen_asset_money_columns.py
    ├── <ts>_add_asset_revaluation_columns.py
    └── <ts>_add_project_asset_indexes.py

frontend/src/
├── pages/
│   ├── Projects/
│   │   ├── ProjectDetails.jsx   ← FR-011, FR-012
│   │   ├── Timesheets.jsx       ← FR-013
│   │   ├── ProjectRisks.jsx     ← FR-014..FR-016
│   │   ├── GanttChart.jsx       ← FR-044
│   │   ├── ResourceUtilizationReport.jsx ← FR-045
│   │   └── ProjectList.jsx      ← FR-047
│   └── Assets/
│       ├── AssetManagement.jsx  ← FR-017, FR-018
│       ├── AssetDetails.jsx     ← FR-042, FR-043, FR-046
│       ├── AssetForm.jsx        ← FR-043
│       ├── AssetReports.jsx     ← FR-048
│       ├── ImpairmentTest.jsx   ← FR-049
│       ├── LeaseContracts.jsx   ← FR-046
│       └── AssetList.jsx        ← FR-042
└── services/
    └── projects.js              ← FR-047 (summary params)
```

---

## Phase 0 — Research

**Status**: Complete. See [`research.md`](./research.md) and [`data-model.md`](./data-model.md).

Key findings:
- 3 columns missing from `projects` DDL (`retainer_amount`, `billing_cycle`, `next_billing_date`)
- 15 tables missing `updated_at` (Constitution XVII)
- 7 money columns using `NUMERIC(15,2)` instead of `DECIMAL(18,4)` (Constitution I)
- `customers` table DOES exist — spec FR-009 corrected
- `formatDate` DOES exist in `dateUtils.js` — spec FR-012 corrected
- Tailwind CSS confirmed NOT used — `AssetManagement.jsx` classes are definitely bugs
- All 3 routers import `http_error` — available for use
- `notification_service` not imported in any of the 3 routers (out of scope)

---

## Phase 1 — Implementation Tasks

Tasks are ordered by dependency. Items within the same group can be done in parallel.

### Group A — Critical Backend Runtime Fixes (no dependencies)

#### A1 — Fix task dependency column name (FR-001)

**File**: `backend/routers/projects.py`

Steps:
1. Find all task dependency queries that reference `t.name` or `name` for task names.
2. Replace with `t.task_name` / `task_name`.

#### A2 — Fix `users` → `company_users` table references (FR-002)

**Files**: `backend/routers/projects.py`, `backend/routers/contracts.py`

Steps:
1. In project risk listing, replace `JOIN users u ON ...` with `JOIN company_users cu ON ...`.
2. In contract amendment listing, apply same fix.
3. Update column references from `u.username` / `u.full_name` to `cu.username` / `cu.full_name`.

#### A3 — Fix ProjectRisk type mismatch (FR-003)

**File**: `backend/routers/projects.py`

Steps:
1. Create `ProjectRiskCreate` Pydantic schema in `schemas/projects.py`:
   ```python
   class ProjectRiskCreate(BaseModel):
       risk_name: str
       probability: Literal["low", "medium", "high", "critical"]
       impact: Literal["low", "medium", "high", "critical"]
       mitigation_strategy: Optional[str] = None
       risk_owner_id: Optional[int] = None
   ```
2. Replace raw `dict` parameter in risk creation endpoint with `ProjectRiskCreate`.
3. Store string values directly (not Decimal).

#### A4 — Fix missing `branch_id` in timesheet approval (FR-004)

**File**: `backend/routers/projects.py` — `approve_timesheets`

Steps:
1. Add `p.branch_id` to the SELECT column list in the query.

#### A5 — Fix impairment test `purchase_cost` → `cost` (FR-005)

**File**: `backend/routers/finance/assets.py`

Steps:
1. Replace `asset.purchase_cost` with `asset.cost` in the carrying amount computation.

#### A6 — Fix `journal_entry_id` variable shadowing (FR-006)

**File**: `backend/routers/finance/assets.py`

Steps:
1. Identify the variable shadowing — the outer `journal_entry_id = None` is returned while the inner scope assigns the GL result to a different or shadowed variable.
2. Ensure the GL service return value is assigned to the variable that gets included in the response.

#### A7 — Fix `user_id` parameter in `post_depreciation` (FR-007)

**File**: `backend/routers/finance/assets.py` — `post_depreciation`

Steps:
1. Change `user_id=current_user.username` to `user_id=current_user.id`.

#### A8 — Fix `create_project` missing INSERT columns (FR-008)

**File**: `backend/routers/projects.py` — `create_project`

Steps:
1. Add `branch_id` and `contract_type` to the INSERT column list.
2. Add corresponding `:branch_id` and `:contract_type` to VALUES.
3. Add both to the parameter dict from `project.branch_id` and `project.contract_type`.

#### A9 — Fix contract KPI column names (FR-010)

**File**: `backend/routers/contracts.py`

Steps:
1. Replace `total_amount` with `total` in KPI queries.
2. Remove reference to nonexistent `balance_due` — compute as `total - COALESCE(paid_amount, 0)`.

---

### Group B — Contract Router Fixes (no dependencies)

#### B1 — Fix `create_contract` HTTPException swallowing (FR-024)

**File**: `backend/routers/contracts.py`

Steps:
1. Add `except HTTPException: raise` before the generic `except Exception` handler.

#### B2 — Create `ContractAmendmentCreate` schema (FR-025)

**Files**: `backend/schemas/contracts.py`, `backend/routers/contracts.py`

Steps:
1. Add to `schemas/contracts.py`:
   ```python
   class ContractAmendmentCreate(BaseModel):
       amendment_type: str
       effective_date: date
       description: str
       amount_change: Optional[Decimal] = None
   ```
2. Replace raw `dict` parameter in `create_amendment` with `ContractAmendmentCreate`.

#### B3 — Fix `update_contract` total recalculation (FR-026)

**File**: `backend/routers/contracts.py`

Steps:
1. After updating contract fields, recalculate `total_amount` from `contract_items`:
   ```sql
   UPDATE contracts SET total = (
       SELECT COALESCE(SUM(quantity * unit_price), 0)
       FROM contract_items WHERE contract_id = :id
   ) WHERE id = :id
   ```

#### B4 — Fix `list_contracts` N+1 query (FR-027)

**File**: `backend/routers/contracts.py`

Steps:
1. Remove per-contract item query loop.
2. Fetch all items in a single query: `SELECT * FROM contract_items WHERE contract_id IN (:ids)`.
3. Group items by `contract_id` in Python and attach to each contract dict.

#### B5 — Create `ContractUpdate` schema for partial updates (FR-028)

**Files**: `backend/schemas/contracts.py`, `backend/routers/contracts.py`

Steps:
1. Add to `schemas/contracts.py`:
   ```python
   class ContractUpdate(BaseModel):
       contract_number: Optional[str] = None
       party_id: Optional[int] = None
       contract_type: Optional[str] = None
       start_date: Optional[date] = None
       end_date: Optional[date] = None
       notes: Optional[str] = None
       status: Optional[str] = None
   ```
2. Replace `ContractCreate` parameter in `update_contract` with `ContractUpdate`.
3. Build dynamic SET clause from non-None fields (with whitelist).

---

### Group C — Asset Depreciation & IFRS Compliance

#### C1 — Persist non-straight-line depreciation schedules (FR-029)

**File**: `backend/routers/finance/assets.py`

Steps:
1. In `create_asset`, after generating depreciation schedule entries for declining balance, sum-of-years, or units-of-production methods, INSERT them into `asset_depreciation_schedule` (currently only straight-line entries are persisted).
2. Use the same INSERT pattern as straight-line but with method-specific amounts.

#### C2 — Generate ROU depreciation schedule on lease creation (FR-030)

**File**: `backend/routers/finance/assets.py`

Steps:
1. In the lease contract creation endpoint, after recognizing the ROU asset, generate a straight-line depreciation schedule over the lease term.
2. INSERT schedule entries into `asset_depreciation_schedule` with `asset_id` = the ROU asset ID.

#### C3 — Add lease payment posting endpoint (FR-031)

**File**: `backend/routers/finance/assets.py`

Steps:
1. Add new endpoint `POST /api/assets/leases/{lease_id}/post-payment`.
2. Accept `LeasePaymentCreate` schema with `payment_date` and `amount`.
3. Calculate interest portion: `remaining_liability * (discount_rate / 12 / 100)`.
4. Calculate principal portion: `amount - interest_portion`.
5. Create GL journal entry:
   - Debit: Interest Expense (interest portion)
   - Debit: Lease Liability (principal portion)
   - Credit: Cash/Bank (total amount)
6. Update `remaining_liability` on lease contract.

#### C4 — Fix revaluation to preserve historical cost (FR-032)

**File**: `backend/routers/finance/assets.py`

Steps:
1. In revaluation endpoint, update `current_value` (not `cost`).
2. `cost` must remain the original purchase cost.
3. Requires `current_value` column on `assets` table (see Group E migration).

#### C5 — Implement IAS 16.40 revaluation surplus check (FR-033)

**File**: `backend/routers/finance/assets.py`

Steps:
1. On downward revaluation, check existing `revaluation_surplus` for the asset.
2. If surplus exists, reduce it first: `decrease = min(surplus, revaluation_decrease)`.
3. Excess beyond surplus → recognize in profit/loss via GL entry.
4. On upward revaluation, increase `revaluation_surplus`.
5. Requires `revaluation_surplus` column on `assets` table (see Group E migration).

#### C6 — Cancel future schedule entries on disposal (FR-034)

**File**: `backend/routers/finance/assets.py`

Steps:
1. In disposal endpoint, after processing disposal, update un-posted future schedule entries:
   ```sql
   UPDATE asset_depreciation_schedule
   SET status = 'cancelled'
   WHERE asset_id = :asset_id
     AND status = 'pending'
     AND period_start > :disposal_date
   ```

#### C7 — Calculate partial-year depreciation on disposal (FR-035)

**File**: `backend/routers/finance/assets.py`

Steps:
1. In disposal endpoint, find the current period schedule entry.
2. Calculate pro-rata depreciation from period start to disposal date.
3. Create a partial depreciation entry and post it to GL.

---

### Group D — Frontend Crash Fixes (no backend dependencies; parallel with Groups A-C)

#### D1 — Fix ProjectDetails.jsx imports (FR-011, FR-012)

**File**: `frontend/src/pages/Projects/ProjectDetails.jsx`

Steps:
1. Add `useRef` to the React import: `import { useState, useEffect, useRef, ... } from 'react'`.
2. Add `formatDate` to the dateUtils import: `import { formatShortDate, formatDateTime, formatDate } from '../../utils/dateUtils'`.

#### D2 — Fix Timesheets.jsx missing state (FR-013)

**File**: `frontend/src/pages/Projects/Timesheets.jsx`

Steps:
1. Add `const [submitting, setSubmitting] = useState(false);` in the component body alongside other state declarations.

#### D3 — Fix ProjectRisks.jsx API method and field names (FR-014, FR-015, FR-016)

**File**: `frontend/src/pages/Projects/ProjectRisks.jsx`

Steps:
1. Replace `projectsAPI.listTasks(...)` with `projectsAPI.getTasks(...)`.
2. Replace `p.name` with `p.project_name` in project dropdown rendering.
3. Replace `t.name` with `t.task_name` in task dropdown rendering.

#### D4 — Fix AssetManagement.jsx Tailwind → Bootstrap (FR-018)

**File**: `frontend/src/pages/Assets/AssetManagement.jsx`

Steps:
1. Find all Tailwind CSS classes (e.g., `bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs`).
2. Replace with Bootstrap equivalents:
   - Status badges: `badge bg-success`, `badge bg-warning`, `badge bg-danger`, `badge bg-info`
   - Layout: `p-1`, `rounded`, `small`
3. Verify all status badge variants are covered.

#### D5 — Fix asset field name consistency (FR-042, FR-043)

**Files**: `frontend/src/pages/Assets/AssetList.jsx`, `AssetDetails.jsx`, `AssetForm.jsx`, `AssetManagement.jsx`

Steps:
1. Determine which field names the API actually returns (check `assets` table columns: `code`, `name`, `branch_id`).
2. Standardize all frontend references to match API response.
3. Fix `branch_name` vs `name` inconsistency for branch display.

#### D6 — Fix GanttChart weekend detection (FR-044)

**File**: `frontend/src/pages/Projects/GanttChart.jsx`

Steps:
1. Replace `index % 7 === 5 || index % 7 === 6` (or similar) with actual date check:
   ```javascript
   const dayOfWeek = date.getDay();
   const isWeekend = dayOfWeek === 0 || dayOfWeek === 6; // Sunday = 0, Saturday = 6
   ```

#### D7 — Fix ResourceUtilizationReport range labels (FR-045)

**File**: `frontend/src/pages/Projects/ResourceUtilizationReport.jsx`

Steps:
1. Find the duplicated range check where 50-79% has the same label as <50%.
2. Fix to have three distinct labels:
   - `<50%` → "Light" (or "منخفض")
   - `50-79%` → "Moderate" (or "متوسط")
   - `>=80%` → "Heavy" (or "مرتفع")

#### D8 — Fix `projectsAPI.summary()` params (FR-047)

**File**: `frontend/src/services/projects.js`

Steps:
1. Update `summary()` method to accept and forward query parameters:
   ```javascript
   summary(params = {}) {
       return api.get('/projects/summary', { params });
   }
   ```
2. Update callers in `ProjectList.jsx` to pass `branch_id` if selected.

#### D9 — Fix AssetReports asset count metric (FR-048)

**File**: `frontend/src/pages/Assets/AssetReports.jsx`

Steps:
1. Find the summary metric that shows category count as asset count.
2. Change to use the actual asset count field from the API response.

#### D10 — Fix ImpairmentTest hardcoded currency (FR-049)

**File**: `frontend/src/pages/Assets/ImpairmentTest.jsx`

Steps:
1. Replace hardcoded `"SAR"` with the company's configured currency.
2. Get currency from `AuthContext` → `user.currency` (per Constitution XVIII).

#### D11 — Add error toasts to asset pages (FR-046)

**Files**: `AssetDetails.jsx`, `LeaseContracts.jsx`, and other asset pages with `console.log`-only error handling

Steps:
1. Find all `catch` blocks that only `console.log` or `console.error`.
2. Add toast notification: `toast.error(t('common.error'))` or a more specific message.
3. Ensure `toast` is imported from the project's toast library.

---

### Group E — Schema Migrations (Constitution XXVIII — do after backend code is working)

#### E1 — Add retainer columns to `projects` (database.py + migration)

**File**: `backend/database.py` — `projects` CREATE TABLE  
**Migration**: `<ts>_add_project_retainer_columns.py`

Steps:
1. Add to `projects` DDL in `database.py`:
   ```sql
   retainer_amount DECIMAL(18,4) DEFAULT 0,
   billing_cycle VARCHAR(20),
   next_billing_date DATE,
   ```
2. Create Alembic migration with matching `ALTER TABLE ADD COLUMN` × 3.

#### E2 — Add `updated_at` to 15 tables (database.py + migration)

**File**: `backend/database.py` — 15 CREATE TABLE blocks  
**Migration**: `<ts>_add_updated_at_to_project_asset_tables.py`

Steps:
1. Add `updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP` to each of 15 tables in `database.py`.
2. Create single Alembic migration that adds the column to all 15 tables.

See [`data-model.md`](./data-model.md) Change 2 for full table list and migration template.

#### E3 — Widen asset money columns to DECIMAL(18,4) (database.py + migration)

**File**: `backend/database.py` — 4 CREATE TABLE blocks  
**Migration**: `<ts>_widen_asset_money_columns.py`

Steps:
1. Change `NUMERIC(15,2)` to `DECIMAL(18,4)` for 7 columns across 4 tables in `database.py`.
2. Create Alembic migration with `ALTER COLUMN ... TYPE DECIMAL(18,4)` × 7.

See [`data-model.md`](./data-model.md) Change 3 for full column list and migration template.

#### E4 — Add revaluation tracking columns to `assets` (database.py + migration)

**File**: `backend/database.py` — `assets` CREATE TABLE  
**Migration**: `<ts>_add_asset_revaluation_columns.py`

Steps:
1. Add `current_value DECIMAL(18,4)` and `revaluation_surplus DECIMAL(18,4) DEFAULT 0` to `assets` DDL.
2. Create Alembic migration with `ALTER TABLE ADD COLUMN` × 2 + backfill `current_value = cost`.

See [`data-model.md`](./data-model.md) Change 4 for migration template.

#### E5 — Add missing indexes (database.py + migration)

**File**: `backend/database.py` — index sections  
**Migration**: `<ts>_add_project_asset_indexes.py`

Steps:
1. Add `CREATE INDEX IF NOT EXISTS ...` for 12 indexes in `database.py`.
2. Create Alembic migration with `op.create_index(...)` × 12.

See [`data-model.md`](./data-model.md) Change 5 for full index list.

---

### Group F — Decimal Conversion & Route Ordering (parallel with other groups)

#### F1 — Convert schemas to Decimal (FR-019, FR-020, FR-021)

**Files**: `backend/schemas/projects.py`, `backend/schemas/contracts.py`, `backend/schemas/assets.py`

Steps:
1. Add `from decimal import Decimal` to each file.
2. Replace all `float` type annotations for monetary fields with `Decimal`.
3. Expand `AssetUpdate` schema to include all mutable asset fields.
4. Add new schemas: `ProjectRiskCreate`, `TaskDependencyCreate`, `AssetRevaluationCreate`, `AssetTransferCreate`, `LeaseContractCreate`, `LeasePaymentCreate`.

#### F2 — Fix `exchange_rate=1.0` → `Decimal("1")` (FR-022)

**Files**: `backend/routers/projects.py`, `backend/routers/contracts.py`, `backend/routers/finance/assets.py`

Steps:
1. Add `from decimal import Decimal` to each router.
2. Replace all `exchange_rate=1.0` literals with `exchange_rate=Decimal("1")`.

#### F3 — Fix model type hints (FR-023)

**Files**: `backend/models/domains/projects_core.py`, `projects_execution.py`, `projects_contracts_expenses.py`

Steps:
1. Replace `Mapped[float]` with `Mapped[Decimal]` for all `Numeric` columns.
2. Add `from decimal import Decimal` import.

#### F4 — Fix route ordering in projects.py (FR-036)

**File**: `backend/routers/projects.py`

Steps:
1. Move all static routes BEFORE `/{project_id}`:
   - `/projects/resources/allocation`
   - `/projects/reports/profitability`
   - `/projects/reports/*`
   - `/projects/alerts/*`
   - `/projects/retainer/*`
   - `/projects/summary`
2. Verify no route path conflicts after reordering.

#### F5 — Fix route ordering in contracts.py (FR-037)

**File**: `backend/routers/contracts.py`

Steps:
1. Move static routes (`/contracts/alerts/*`, `/contracts/stats/*`) before `/{contract_id}`.

#### F6 — Add input validations (FR-038, FR-039)

**File**: `backend/routers/projects.py`

Steps:
1. In `create_project`: validate `start_date <= end_date`, raise 400 if not.
2. In `create_task_dependency`: validate `task_id != depends_on_task_id`, raise 400 if equal.

---

### Group G — Security & Error Handling

#### G1 — Fix path traversal in document deletion (FR-050)

**File**: `backend/routers/projects.py`

Steps:
1. Before `os.remove(file_path)`, resolve the absolute path.
2. Verify it starts with the configured uploads directory:
   ```python
   resolved = os.path.realpath(file_path)
   if not resolved.startswith(os.path.realpath(UPLOAD_DIR)):
       raise HTTPException(**http_error(400, "invalid_file_path"))
   ```

#### G2 — Fix HTTPException swallowing in assets.py (FR-051)

**File**: `backend/routers/finance/assets.py`

Steps:
1. In `post_depreciation` and `create_asset`, add `except HTTPException: raise` before `except Exception`.

#### G3 — Remove duplicate `check_fiscal_period_open` (FR-052)

**File**: `backend/routers/finance/assets.py`

Steps:
1. Find the duplicate call in `revalue_asset`.
2. Remove the redundant invocation (keep only one call per endpoint).

#### G4 — Replace remaining raw `dict` inputs with Pydantic schemas (FR-040, FR-041)

**Files**: `backend/routers/projects.py`, `backend/routers/finance/assets.py`

Steps:
1. Create Pydantic schemas for: `ProjectRiskUpdate`, `TaskDependencyCreate`.
2. Create Pydantic schemas for: `AssetTransferCreate`, `AssetRevaluationCreate`, `LeaseContractCreate`, `ImpairmentTestInput`.
3. Replace raw `dict` parameters in all affected endpoints.

---

## Phase 2 — Verification

### Backend Verification

| Check | Command / Method |
|-------|-----------------|
| Import check | `python -c "from routers.projects import router; from routers.contracts import router; from routers.finance.assets import router"` |
| Task dependencies | `GET /api/projects/{id}/tasks/{tid}/dependencies` — returns `task_name` not null |
| Risk creation | `POST /api/projects/{id}/risks` with `probability: "high"` — stores string, not Decimal |
| Timesheet approval | `POST /api/projects/{id}/timesheets/approve` — no AttributeError |
| Impairment test | `POST /api/assets/{id}/impairment-test` — correct carrying amount from `cost`, non-null `journal_entry_id` |
| Depreciation post | `POST /api/assets/{id}/depreciation/{sid}/post` — GL entry created with `user_id` (int) |
| Project create | `POST /api/projects` with `branch_id=3` — verify `branch_id` persisted |
| Contract KPI | `GET /api/contracts/kpis` — no SQL error |
| Contract create error | `POST /api/contracts` with invalid data — returns 400 not 500 |
| Decimal precision | Create project with budget `1234567.89` — fetched value matches exactly |
| Route ordering | `GET /api/projects/reports/profitability` — returns report, not 422 |
| Path traversal | Attempt `DELETE /api/projects/{id}/documents/{doc_id}` with `../../etc/passwd` path — blocked |
| Migration | `alembic upgrade head` on test DB — all migrations apply cleanly |
| Schema parity | Fresh `database.py` create vs. migrated DB — identical column list |
| Non-SL depreciation | Create asset with `declining_balance` method — schedule persisted in DB |

### Frontend Verification

| Check | Method |
|-------|--------|
| ProjectDetails load | Navigate to any project — no console errors, dates formatted |
| Timesheets save | Save a timesheet entry — no crash on `setSubmitting` |
| ProjectRisks load | Select project from dropdown — name displays, tasks populate |
| Gantt weekends | Render chart for known date range — Saturday/Sunday highlighted correctly |
| Utilization ranges | Check report labels — three distinct ranges |
| Asset Management | Open page — badges styled with Bootstrap, no unstyled text |
| Asset field names | Asset list shows correct code, name, type columns |
| ImpairmentTest currency | Open page — currency matches company setting |
| AssetReports count | Open depreciation tab — asset count, not category count |
| Error toasts | Trigger API error on asset page — toast appears |

---

## Implementation Order (suggested)

```
Day 1 — Critical backend crashes:
  A1 (task dep column name)         ← SQL error fix
  A2 (users→company_users)          ← SQL error fix
  A4 (branch_id in timesheet)       ← AttributeError fix
  A5 (purchase_cost→cost)           ← AttributeError fix
  A6 (journal_entry_id shadowing)   ← data loss fix
  A7 (username→user_id)             ← type error fix
  A8 (create_project missing cols)  ← silent data loss fix
  D1 (ProjectDetails imports)       ← frontend crash fix (parallel)
  D2 (Timesheets state)             ← frontend crash fix (parallel)
  D3 (ProjectRisks API/fields)      ← frontend crash fix (parallel)

Day 2 — Contract + validation fixes:
  A3 (risk type mismatch)           ← needs schema first
  A9 (contract KPI columns)
  B1 (HTTPException swallowing)
  B2 (amendment schema)
  B3 (total recalculation)
  B4 (N+1 fix)
  B5 (ContractUpdate schema)
  F6 (input validations)

Day 3 — Decimal conversion + security:
  F1 (schemas float→Decimal)
  F2 (exchange_rate literals)
  F3 (model type hints)
  G1 (path traversal)
  G2 (HTTPException swallowing in assets)
  G3 (duplicate fiscal check)
  G4 (remaining dict→Pydantic)

Day 4 — Asset depreciation + IFRS:
  C1 (non-SL depreciation persist)
  C2 (ROU depreciation schedule)
  C3 (lease payment endpoint)
  C4 (revaluation preserve cost)
  C5 (IAS 16.40 surplus)
  C6 (cancel future schedules)
  C7 (partial-year depreciation)

Day 5 — Frontend polish + route ordering:
  D4 (Tailwind→Bootstrap)
  D5 (asset field consistency)
  D6 (Gantt weekends)
  D7 (utilization ranges)
  D8 (summary params)
  D9 (asset report count)
  D10 (hardcoded currency)
  D11 (error toasts)
  F4 (project route ordering)
  F5 (contract route ordering)

Day 6 — Schema migrations + verification:
  E1 (retainer columns)
  E2 (updated_at × 15)
  E3 (money column types)
  E4 (revaluation columns)
  E5 (indexes)
  Full verification pass
```

---

## Risks

| Risk | Mitigation |
|------|-----------|
| Decimal conversion breaks existing API consumers | Decimal serializes as string in JSON by default; add Pydantic `json_encoders` if needed. Frontend `formatNumber()` handles both |
| Migration widens NUMERIC(15,2)→DECIMAL(18,4) on large tables | ALTER COLUMN TYPE on PostgreSQL may rewrite table; schedule during low-traffic window for tenants with >100K asset records |
| Route reordering in 3400-line file may introduce merge conflicts | Reorder in a dedicated commit; merge promptly |
| Non-straight-line depreciation schedule generation changes asset creation behavior | Existing assets unaffected (no backfill); only new assets get schedules |
| `current_value` column needs backfill for existing assets | Migration sets `current_value = cost` for all existing records with `WHERE current_value IS NULL` |
| Lease payment endpoint is new functionality (not just a fix) | Scoped tightly per IFRS 16 requirements; no broad lease management changes |
| 15-table migration for `updated_at` may hit lock contention | Use `ADD COLUMN ... DEFAULT` which is instant in PostgreSQL 11+ (no table rewrite) |
