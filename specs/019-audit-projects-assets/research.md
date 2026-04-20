# Research: Projects, Contracts & Fixed Assets — Audit & Bug Fixes

**Feature**: 019-audit-projects-assets  
**Date**: 2026-04-20  
**Phase**: 0 — Code Discovery

---

## Files In Scope

### Backend

| File | Role | Size |
|------|------|------|
| `backend/routers/projects.py` | Projects endpoints (59 endpoints) | 3429 lines |
| `backend/routers/contracts.py` | Contracts endpoints (12 endpoints) | 672 lines |
| `backend/routers/finance/assets.py` | Fixed Assets endpoints (31 endpoints) | 1353 lines |
| `backend/schemas/projects.py` | Pydantic models for projects | 144 lines |
| `backend/schemas/contracts.py` | Pydantic models for contracts | 46 lines |
| `backend/schemas/assets.py` | Pydantic models for assets | 29 lines |
| `backend/database.py` | DDL for all project/asset tables | 6162 lines |
| `backend/models/domains/projects_core.py` | SQLAlchemy models — projects, tasks | — |
| `backend/models/domains/projects_execution.py` | SQLAlchemy models — risks, timesheets | — |
| `backend/models/domains/projects_contracts_expenses.py` | SQLAlchemy models — contracts | — |
| `backend/services/gl_service.py` | `create_journal_entry()` — GL integration | — |

### Frontend

| File | Role |
|------|------|
| `frontend/src/pages/Projects/ProjectDetails.jsx` | Project overview + tabs |
| `frontend/src/pages/Projects/Timesheets.jsx` | Timesheet entry |
| `frontend/src/pages/Projects/ProjectRisks.jsx` | Risk register |
| `frontend/src/pages/Projects/GanttChart.jsx` | Task Gantt visualization |
| `frontend/src/pages/Projects/ResourceUtilizationReport.jsx` | Utilization ranges |
| `frontend/src/pages/Projects/ProjectList.jsx` | Project listing |
| `frontend/src/pages/Assets/AssetManagement.jsx` | Transfers + revaluations |
| `frontend/src/pages/Assets/AssetDetails.jsx` | Asset detail view |
| `frontend/src/pages/Assets/AssetForm.jsx` | Create/edit asset |
| `frontend/src/pages/Assets/AssetReports.jsx` | Depreciation reports |
| `frontend/src/pages/Assets/ImpairmentTest.jsx` | IAS 36 impairment |
| `frontend/src/pages/Assets/LeaseContracts.jsx` | IFRS 16 leases |
| `frontend/src/pages/Assets/AssetList.jsx` | Asset listing |
| `frontend/src/services/projects.js` | `projectsAPI` service |
| `frontend/src/services/assets.js` | `assetsAPI` service |
| `frontend/src/utils/dateUtils.js` | Date formatting helpers |

---

## Critical Bug: Wrong Column Names in Task Dependencies (FR-001)

**Severity**: Critical  
**Location**: `backend/routers/projects.py`

### Root Cause

The task dependencies SQL JOIN queries `t.name` but the `project_tasks` table column is `task_name`. This causes a SQL error (column does not exist) or returns NULL.

### Fix

Replace `t.name` with `t.task_name` in all task dependency queries.

---

## Critical Bug: Wrong Table `users` Instead of `company_users` (FR-002)

**Severity**: Critical  
**Location**: `backend/routers/projects.py` (risk listing), `backend/routers/contracts.py` (amendments)

### Root Cause

Risk listing and contract amendment listing JOIN against the `users` table. In the AMAN multi-tenant architecture, user data in tenant DBs is in `company_users`. The `users` table is in `aman_system` only.

### Fix

Replace `JOIN users u ON ...` with `JOIN company_users cu ON ...` and update column references accordingly.

---

## Critical Bug: ProjectRisk Type Mismatch (FR-003)

**Severity**: Critical  
**Location**: `backend/routers/projects.py`

### Root Cause

`project_risks.probability` and `project_risks.impact` are `String(20)` columns expecting values like `"high"`, `"medium"`, `"low"`, `"critical"`. The endpoint handler stores `Decimal` values instead — causing silent type coercion or constraint violations.

### Fix

Accept string enum values and validate against allowed set: `{"low", "medium", "high", "critical"}`. Create a Pydantic schema for risk creation with `Literal` type.

---

## Critical Bug: Missing `branch_id` in Timesheet Approval SELECT (FR-004)

**Severity**: Critical  
**Location**: `backend/routers/projects.py` — `approve_timesheets`

### Root Cause

The SELECT query in `approve_timesheets` does not include `branch_id`, but subsequent code accesses `project.branch_id`. This causes an `AttributeError` at runtime.

### Fix

Add `p.branch_id` to the SELECT column list.

---

## Critical Bug: Wrong Column `purchase_cost` in Impairment Test (FR-005)

**Severity**: Critical  
**Location**: `backend/routers/finance/assets.py`

### Root Cause

The impairment test endpoint computes carrying amount using `asset.purchase_cost`, but the `assets` table column is `cost`. This causes an `AttributeError` crash.

### Fix

Replace `asset.purchase_cost` with `asset.cost`.

---

## Critical Bug: `journal_entry_id` Always Returns None (FR-006)

**Severity**: Critical  
**Location**: `backend/routers/finance/assets.py`

### Root Cause

Variable shadowing — the `journal_entry_id` result from `gl_create_journal_entry()` is assigned inside a nested scope but the outer variable (initialized to `None`) is what gets returned in the response.

### Fix

Assign the GL service return value to the correct variable in the outer scope.

---

## Critical Bug: Username Passed as `user_id` to GL Service (FR-007)

**Severity**: Critical  
**Location**: `backend/routers/finance/assets.py` — `post_depreciation`

### Root Cause

The call `gl_create_journal_entry(..., user_id=current_user.username)` passes a string username. The GL service signature expects `user_id: int`.

### Fix

Change to `user_id=current_user.id`.

---

## Critical Bug: `create_project` Drops `branch_id` and `contract_type` (FR-008)

**Severity**: Critical  
**Location**: `backend/routers/projects.py` — `create_project`

### Root Cause

`ProjectCreate` schema includes `branch_id` and `contract_type` fields, but the INSERT statement in `create_project` omits them. The values are silently dropped, causing new projects to have NULL `branch_id` and `contract_type`.

### Fix

Add both columns to the INSERT column list and values.

---

## Bug: `generate_retainer_invoices` Uses `customers` Table (FR-009)

**Severity**: High  
**Location**: `backend/routers/projects.py`

### Root Cause (Corrected from spec)

The spec originally stated `customers` table doesn't exist — **this is WRONG**. The `customers` table DOES exist in `database.py` (lines 603–632) and `projects.customer_id REFERENCES customers(id)` is valid. The `generate_retainer_invoices` JOIN `LEFT JOIN customers c ON p.customer_id = c.id` is actually correct.

**However**, the `projects` table DDL is **missing three columns** that the retainer code depends on: `retainer_amount`, `billing_cycle`, `next_billing_date`. This means the retainer endpoints will crash on fresh tenant DBs.

### Fix

Add the missing columns to the `projects` table in `database.py` and create an Alembic migration.

---

## Bug: Contract KPI Wrong Column Names (FR-010)

**Severity**: High  
**Location**: `backend/routers/contracts.py`

### Root Cause

The KPI endpoint queries `total_amount` but the column is `total`. It also references a nonexistent `balance_due` column — the balance must be computed from `total - paid_amount`.

### Fix

Replace `total_amount` with `total` and compute balance server-side.

---

## Frontend Crash: Missing `useRef` Import in ProjectDetails (FR-011)

**Severity**: Critical  
**Location**: `frontend/src/pages/Projects/ProjectDetails.jsx`

### Root Cause

Component uses `useRef` but does not import it from React. JavaScript crash on mount.

### Fix

Add `useRef` to the React import destructuring.

---

## Frontend Crash: Missing `formatDate` Import in ProjectDetails (FR-012)

**Severity**: Critical  
**Location**: `frontend/src/pages/Projects/ProjectDetails.jsx`

### Root Cause (Corrected from spec)

The spec said `formatDate` doesn't exist — **this is WRONG**. `formatDate` IS exported from `frontend/src/utils/dateUtils.js`. The actual bug is that `ProjectDetails.jsx` imports `formatShortDate` and `formatDateTime` but NOT `formatDate`. Adding `formatDate` to the import fixes the crash.

### Fix

Add `formatDate` to the import from `../../utils/dateUtils`.

---

## Frontend Crash: Missing `submitting` State in Timesheets (FR-013)

**Severity**: Critical  
**Location**: `frontend/src/pages/Projects/Timesheets.jsx`

### Root Cause

Component references `submitting` and `setSubmitting` but never declares the state variable. Crash on first render.

### Fix

Add `const [submitting, setSubmitting] = useState(false);` to the component.

---

## Frontend Bug: Wrong API Method in ProjectRisks (FR-014, FR-015, FR-016)

**Severity**: Critical  
**Location**: `frontend/src/pages/Projects/ProjectRisks.jsx`

### Root Cause

Three issues:
1. Calls `projectsAPI.listTasks()` which does not exist — should be `projectsAPI.getTasks()`
2. Renders `p.name` for project dropdown — should be `p.project_name`
3. Renders `t.name` for task dropdown — should be `t.task_name`

### Fix

Fix all three field references.

---

## Frontend Bug: Tailwind CSS in Bootstrap Project (FR-018)

**Severity**: High  
**Location**: `frontend/src/pages/Assets/AssetManagement.jsx`

### Root Cause

**Confirmed**: The project uses Bootstrap, not Tailwind CSS. No `tailwind.config.js` or `tailwindcss` dependency exists. `AssetManagement.jsx` uses Tailwind classes like `bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs` for badges and layout — these render as unstyled text.

### Fix

Replace all Tailwind CSS classes with Bootstrap equivalents (`badge bg-success`, `badge bg-warning`, etc.).

---

## Frontend Bug: Asset Import Path (FR-017)

**Severity**: Low (non-issue)  
**Location**: `frontend/src/pages/Assets/AssetManagement.jsx`

### Root Cause (Corrected from spec)

`AssetManagement.jsx` imports from `../../services` — but `frontend/src/services/index.js` exists and exports both `assetsAPI` and `branchesAPI`. The import may work correctly. This is a consistency concern only.

### Fix

Verify import works. If it does, mark as no-op. If not, update to `../../services/assets`.

---

## database.py Critical Findings

### Missing Columns on `projects` Table

The `projects` table DDL is missing 3 columns that router code uses:
- `retainer_amount` — used by `setup_retainer` endpoint
- `billing_cycle` — used by `setup_retainer` endpoint
- `next_billing_date` — used by `generate_retainer_invoices` endpoint

Fresh tenant DBs will crash on these endpoints.

### Missing `updated_at` on 15 Tables (Constitution XVII)

Constitution XVII requires `AuditMixin` (`created_at`, `updated_at`, `created_by`, `updated_by`) on ALL domain models. The following 15 tables lack `updated_at`:

1. `project_tasks`
2. `project_budgets`
3. `project_expenses`
4. `project_revenues`
5. `project_documents`
6. `task_dependencies`
7. `contract_items`
8. `contract_amendments`
9. `asset_depreciation_schedule`
10. `asset_transfers`
11. `asset_revaluations`
12. `asset_maintenance`
13. `asset_insurance`
14. `lease_contracts`
15. `asset_impairments`

### Type Inconsistencies (Constitution I)

Several asset-related tables use `NUMERIC(15,2)` instead of `DECIMAL(18,4)`:

| Table | Column | Current | Required |
|-------|--------|---------|----------|
| `asset_transfers` | `book_value_at_transfer` | `NUMERIC(15,2)` | `DECIMAL(18,4)` |
| `asset_revaluations` | `old_value`, `new_value`, `difference` | `NUMERIC(15,2)` | `DECIMAL(18,4)` |
| `asset_maintenance` | `cost` | `NUMERIC(15,2)` | `DECIMAL(18,4)` |
| `asset_insurance` | `premium_amount`, `coverage_amount` | `NUMERIC(15,2)` | `DECIMAL(18,4)` |

### Missing Indexes

FK and filter columns across ~12 tables lack indexes. Key examples:
- `project_tasks.project_id`
- `project_expenses.project_id`
- `project_revenues.project_id`
- `project_timesheets.project_id`, `project_timesheets.employee_id`
- `asset_depreciation_schedule.asset_id`
- `asset_transfers.asset_id`
- `contract_items.contract_id`

### Missing Asset Columns

The `assets` table design is missing several columns needed by router logic:
- `current_value` — for revaluation tracking (preserve `cost`)
- `revaluation_surplus` — for IAS 16.40 surplus tracking
- `category_id` FK — `asset_categories` table exists but no FK link
- `location` — referenced in some queries
- GL account linkage columns (`asset_account_id`, `depreciation_account_id`, `expense_account_id`)

---

## Backend Audit Summary: Projects Router

**File**: `backend/routers/projects.py` (3429 lines, 59 endpoints)

### Issues Found

| ID | Description | Severity |
|----|------------|----------|
| P-01 | Float for money everywhere — schemas, models, GL calls | High (Constitution I) |
| P-02 | Wrong column `name` vs `task_name` in task_dependencies query | Critical |
| P-03 | Wrong table `users` vs `company_users` in risk listing | Critical |
| P-04 | ProjectRisk type mismatch — String column gets Decimal | Critical |
| P-05 | `approve_timesheets` missing `branch_id` in SELECT | Critical |
| P-06 | `create_project` drops `branch_id` and `contract_type` | Critical |
| P-07 | Route shadowing — static routes after `/{project_id}` | Medium |
| P-08 | Raw `dict` inputs for risks, dependencies, amendments | Medium |
| P-09 | Path traversal risk in document deletion | Medium |
| P-10 | Profitability report double-counts expenses | Medium |
| P-11 | Missing retainer columns in DDL | High |
| P-12 | `exchange_rate=1.0` float literal in GL calls | High |

---

## Backend Audit Summary: Contracts Router

**File**: `backend/routers/contracts.py` (672 lines, 12 endpoints)

### Issues Found

| ID | Description | Severity |
|----|------------|----------|
| C-01 | `create_contract` swallows HTTPException → returns 500 | High |
| C-02 | N+1 query in `list_contracts` | Medium |
| C-03 | Wrong table `users` vs `company_users` in amendments | Critical |
| C-04 | KPI endpoint uses wrong column names | High |
| C-05 | `update_contract` doesn't recalculate total | Medium |
| C-06 | Uses `ContractCreate` for updates (requires all fields) | Medium |
| C-07 | `exchange_rate=1.0` float literal in GL calls | High |

---

## Backend Audit Summary: Assets Router

**File**: `backend/routers/finance/assets.py` (1353 lines, 31 endpoints)

### Issues Found

| ID | Description | Severity |
|----|------------|----------|
| A-01 | Impairment test uses nonexistent `purchase_cost` (should be `cost`) | Critical |
| A-02 | `journal_entry_id` always returns `None` (variable shadowing) | Critical |
| A-03 | `post_depreciation` passes username instead of user_id | Critical |
| A-04 | Non-straight-line depreciation methods don't persist schedules | High |
| A-05 | IFRS 16 gaps — no ROU depreciation, no payment posting | High |
| A-06 | Revaluation overwrites historical cost | High |
| A-07 | HTTPException swallowed in `post_depreciation` and `create_asset` | High |
| A-08 | Duplicate/conflicting transfer and revaluation endpoints | Medium |
| A-09 | Many raw `dict` inputs | Medium |
| A-10 | Missing IAS 16.40 revaluation surplus check | High |
| A-11 | No partial-year depreciation on disposal | Medium |
| A-12 | Disposal doesn't cancel future schedule entries | Medium |

---

## Schema Audit Summary

### `schemas/projects.py` (144 lines, 14 models)

`ProjectCreate` includes `branch_id` and `contract_type`. ALL monetary fields use `float`:
- `budget`, `amount`, `hours`, `unit_price`, `tax_rate`, `discount`, `exchange_rate`, `cost_impact`, `retainer_amount`

### `schemas/contracts.py` (46 lines, 6 models)

ALL monetary fields use `float`:
- `quantity`, `unit_price`, `tax_rate`, `total`, `total_amount`

### `schemas/assets.py` (29 lines, 3 models)

`AssetCreate`, `AssetUpdate`, `AssetDisposal`. `AssetUpdate` only has `name` and `status` but is NEVER USED (endpoint accepts raw `dict`). ALL monetary fields use `float`:
- `cost`, `residual_value`, `disposal_price`, `new_value`

---

## Frontend Audit Summary

### Critical Runtime Crashes

| Page | Issue |
|------|-------|
| `ProjectDetails.jsx` | Missing `useRef` import; missing `formatDate` import |
| `Timesheets.jsx` | `submitting` state never declared |
| `ProjectRisks.jsx` | `projectsAPI.listTasks` doesn't exist, wrong field names |

### Asset Page Issues

| Page | Issue |
|------|-------|
| `AssetManagement.jsx` | Tailwind CSS classes in Bootstrap app |
| `AssetDetails.jsx` | Branch field name inconsistency, no error toasts |
| `AssetForm.jsx` | Branch field name inconsistency |
| `AssetReports.jsx` | Category count shown as asset count |
| `ImpairmentTest.jsx` | Hardcoded SAR currency |
| `LeaseContracts.jsx` | Form reset issues |
| `AssetList.jsx` | Field name inconsistencies (`code`/`name` vs `asset_code`/`asset_name`) |

### Report/Chart Bugs

| Page | Issue |
|------|-------|
| `GanttChart.jsx` | Weekend detection uses `index % 7` instead of `getDay()` |
| `ResourceUtilizationReport.jsx` | Duplicated range (50-79% labeled same as <50%) |
| `ProjectList.jsx` | `projectsAPI.summary()` doesn't accept params |

### General Frontend Issues

- Many pages silently swallow errors (console.log only, no toast)
- `projectsAPI.summary()` doesn't accept query parameters

---

## Cross-Cutting Findings

### GL Service Integration

`gl_create_journal_entry` signature: `exchange_rate: float = 1.0`, `user_id: int`. It internally converts `exchange_rate` to `Decimal` via `_dec()`. The parameter type hint is `float` in the service itself, but callers should still pass `Decimal("1")` per Constitution I.

### Notification Service

`notification_service` is NOT imported in any of the three routers. Neither Projects, Contracts, nor Assets modules send notifications. (Not in scope for this audit — flagged for future work.)

### Error Handling

`http_error` IS imported in all three routers. The helper is available but several endpoints still use raw `HTTPException(detail=str(e))` or swallow exceptions silently.

---

## Spec Corrections

Based on research findings, the following spec assumptions need correction:

| FR | Spec Assumption | Actual Finding | Corrected Action |
|----|----------------|----------------|-----------------|
| FR-009 | `customers` table doesn't exist | `customers` table EXISTS (`database.py:603-632`), JOIN is valid | Fix missing DDL columns on `projects` instead |
| FR-012 | Replace `formatDate` with `formatShortDate` | `formatDate` EXISTS in `dateUtils.js`, just not imported | Add `formatDate` to the import statement |
| FR-017 | Import path `../../services` is wrong | `services/index.js` exports `assetsAPI` — may be valid | Verify; likely no-op |
