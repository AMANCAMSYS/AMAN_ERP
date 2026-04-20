# Tasks: Projects, Contracts & Fixed Assets — Audit & Bug Fixes

**Input**: Design documents from `/specs/019-audit-projects-assets/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api-contracts.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. No test tasks included (not requested by spec).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Exact file paths included in descriptions

## FR Coverage

All 52 FRs from spec.md are covered. FR-017 (AssetManagement import path) is omitted — research confirmed `services/index.js` exports both `assetsAPI` and `branchesAPI`, making the current import valid (see `research.md`).

---

## Phase 1: Foundational — Database Schema & Migrations

**Purpose**: DDL and migration fixes that MUST be complete before backend story work. Every change updates BOTH `backend/database.py` AND creates an Alembic migration (Constitution XXVIII).

**CRITICAL**: US6 and US8 depend on T004 (revaluation columns). US3 depends on T003 (money column widening).

- [ ] T001 [P] Add `retainer_amount DECIMAL(18,4) DEFAULT 0`, `billing_cycle VARCHAR(20)`, `next_billing_date DATE` to `projects` table in `backend/database.py` + create Alembic migration `backend/migrations/versions/<ts>_add_project_retainer_columns.py` (FR-009, data-model Change 1)
- [ ] T002 [P] Add `updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP` to 15 tables in `backend/database.py` + create Alembic migration `backend/migrations/versions/<ts>_add_updated_at_to_project_asset_tables.py` (Constitution XVII, data-model Change 2)
- [ ] T003 [P] Change 7 money columns from `NUMERIC(15,2)` to `DECIMAL(18,4)` across 4 tables (`asset_transfers`, `asset_revaluations`, `asset_maintenance`, `asset_insurance`) in `backend/database.py` + create Alembic migration `backend/migrations/versions/<ts>_widen_asset_money_columns.py` (Constitution I, data-model Change 3)
- [ ] T004 [P] Add `current_value DECIMAL(18,4)` and `revaluation_surplus DECIMAL(18,4) DEFAULT 0` to `assets` table in `backend/database.py` + create Alembic migration with backfill `current_value = cost` in `backend/migrations/versions/<ts>_add_asset_revaluation_columns.py` (data-model Change 4)
- [ ] T005 [P] Add 12 missing `CREATE INDEX IF NOT EXISTS` statements to `backend/database.py` + create Alembic migration `backend/migrations/versions/<ts>_add_project_asset_indexes.py` (data-model Change 5)

**Checkpoint**: All schema changes applied. Backend story implementation can now begin.

---

## Phase 2: User Story 1 — Fix Critical Runtime Crashes in Projects Frontend (Priority: P1) 🎯 MVP

**Goal**: Make ProjectDetails, Timesheets, and ProjectRisks pages load without JavaScript errors.

**Independent Test**: Navigate to each page and verify it renders without console errors and all interactive features function.

- [ ] T006 [P] [US1] Add `useRef` to React import and add `formatDate` to dateUtils import in `frontend/src/pages/Projects/ProjectDetails.jsx` (FR-011, FR-012)
- [ ] T007 [P] [US1] Add `const [submitting, setSubmitting] = useState(false)` state declaration in `frontend/src/pages/Projects/Timesheets.jsx` (FR-013)
- [ ] T008 [P] [US1] Fix `projectsAPI.listTasks` → `getTasks`, `p.name` → `p.project_name`, `t.name` → `t.task_name` in `frontend/src/pages/Projects/ProjectRisks.jsx` (FR-014, FR-015, FR-016)

**Checkpoint**: All 3 Projects frontend pages load and function without crashes.

---

## Phase 3: User Story 2 — Fix Critical Backend SQL Errors and Data Corruption (Priority: P1) 🎯 MVP

**Goal**: Eliminate all runtime SQL errors, type mismatches, and silent data loss in Projects, Contracts, and Assets endpoints.

**Independent Test**: Call each affected endpoint and verify correct data without SQL errors. Verify data types in DB match column definitions.

- [ ] T009 [US2] Fix `t.name` → `t.task_name` in task dependency JOIN queries in `backend/routers/projects.py` (FR-001)
- [ ] T010 [US2] Fix `JOIN users u` → `JOIN company_users cu` and update column references in risk listing in `backend/routers/projects.py` and amendment listing in `backend/routers/contracts.py` (FR-002)
- [ ] T011 [US2] Create `ProjectRiskCreate` schema with `Literal["low","medium","high","critical"]` for `probability`/`impact` in `backend/schemas/projects.py`; replace raw `dict` parameter in risk creation endpoint in `backend/routers/projects.py` (FR-003)
- [ ] T012 [US2] Add `p.branch_id` to SELECT column list in `approve_timesheets` query in `backend/routers/projects.py` (FR-004)
- [ ] T013 [P] [US2] Fix `asset.purchase_cost` → `asset.cost` in impairment test carrying amount computation in `backend/routers/finance/assets.py` (FR-005)
- [ ] T014 [US2] Fix `journal_entry_id` variable shadowing — assign GL service return value to the outer-scope variable in impairment test in `backend/routers/finance/assets.py` (FR-006)
- [ ] T015 [US2] Fix `user_id=current_user.username` → `user_id=current_user.id` in `post_depreciation` GL call in `backend/routers/finance/assets.py` (FR-007)
- [ ] T016 [US2] Add `branch_id` and `contract_type` to INSERT column list, VALUES, and parameter dict in `create_project` in `backend/routers/projects.py` (FR-008)
- [ ] T017 [P] [US2] Fix `total_amount` → `total` and replace nonexistent `balance_due` with `total - COALESCE(paid_amount, 0)` in contract KPI queries in `backend/routers/contracts.py` (FR-010)

**Checkpoint**: All critical backend endpoints return correct data without SQL errors or type mismatches.

---

## Phase 4: User Story 3 — Fix Constitution I Violations: Float for Money (Priority: P2)

**Goal**: Replace all Python `float` with `Decimal` for monetary fields across Pydantic schemas, SQLAlchemy model hints, and GL service calls.

**Independent Test**: Create entities with precise monetary values (e.g., 1,234,567.89) and verify exact precision on round-trip with no floating-point artifacts.

- [ ] T018 [P] [US3] Convert all monetary `float` fields to `Decimal` in `backend/schemas/projects.py` (9 fields), `backend/schemas/contracts.py` (5 fields), and `backend/schemas/assets.py` (4 fields); add `from decimal import Decimal` to each (FR-019, FR-020, FR-021)
- [ ] T019 [P] [US3] Replace all `exchange_rate=1.0` float literals with `exchange_rate=Decimal("1")` in `backend/routers/projects.py`, `backend/routers/contracts.py`, and `backend/routers/finance/assets.py`; add `from decimal import Decimal` to each router (FR-022)
- [ ] T020 [P] [US3] Replace `Mapped[float]` with `Mapped[Decimal]` for all `Numeric` columns in `backend/models/domains/projects_core.py`, `backend/models/domains/projects_execution.py`, and `backend/models/domains/projects_contracts_expenses.py`; add `from decimal import Decimal` (FR-023)

**Checkpoint**: Zero `float` usage for monetary values across all three modules.

---

## Phase 5: User Story 4 — Fix Frontend Field Name Mismatches in Assets Pages (Priority: P2)

**Goal**: Standardize asset field names across all Assets frontend pages and replace Tailwind CSS with Bootstrap.

**Independent Test**: Navigate to each asset page and verify all data columns display correctly with proper Bootstrap styling.

- [ ] T021 [P] [US4] Replace all Tailwind CSS classes (`bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs` etc.) with Bootstrap equivalents (`badge bg-success`, `badge bg-warning`, `badge bg-danger`, `badge bg-info`) in `frontend/src/pages/Assets/AssetManagement.jsx` (FR-018)
- [ ] T022 [P] [US4] Standardize field names to match API response (`code`/`name` not `asset_code`/`asset_name`, consistent `branch_name`) across `frontend/src/pages/Assets/AssetList.jsx`, `frontend/src/pages/Assets/AssetDetails.jsx`, `frontend/src/pages/Assets/AssetForm.jsx`, and `frontend/src/pages/Assets/AssetManagement.jsx` (FR-042, FR-043)
- [ ] T023 [P] [US4] Replace hardcoded `"SAR"` currency with company's configured currency from `AuthContext` (`user.currency`) in `frontend/src/pages/Assets/ImpairmentTest.jsx` (FR-049)

**Checkpoint**: All asset pages display correct field values with proper Bootstrap styling and correct currency.

---

## Phase 6: User Story 5 — Fix Contract Router Error Handling and Validation (Priority: P2)

**Goal**: Fix error handling, add Pydantic validation schemas, optimize query performance, and enable partial updates in contract endpoints.

**Independent Test**: Trigger validation errors and verify correct HTTP status codes (400/422 not 500). List 50+ contracts and verify batched queries.

- [ ] T024 [US5] Add `except HTTPException: raise` before generic `except Exception` handler in `create_contract` in `backend/routers/contracts.py` (FR-024)
- [ ] T025 [US5] Create `ContractAmendmentCreate` schema (`amendment_type`, `effective_date`, `description`, `amount_change: Optional[Decimal]`) in `backend/schemas/contracts.py`; replace raw `dict` in `create_amendment` in `backend/routers/contracts.py` (FR-025)
- [ ] T026 [US5] Add server-side `total` recalculation from `contract_items` (`SUM(quantity * unit_price)`) after update in `update_contract` in `backend/routers/contracts.py` (FR-026)
- [ ] T027 [US5] Replace N+1 per-contract item query loop with single batched query `SELECT * FROM contract_items WHERE contract_id IN (:ids)` and group in Python in `list_contracts` in `backend/routers/contracts.py` (FR-027)
- [ ] T028 [US5] Create `ContractUpdate` schema (all fields `Optional`) in `backend/schemas/contracts.py`; replace `ContractCreate` parameter in `update_contract` with `ContractUpdate` and build dynamic SET clause from non-None fields in `backend/routers/contracts.py` (FR-028)

**Checkpoint**: Contract endpoints return correct error codes, validate all input via Pydantic, use batched queries, and support partial updates.

---

## Phase 7: User Story 6 — Fix Asset Depreciation and IFRS Compliance (Priority: P2)

**Goal**: Persist depreciation schedules for all methods (not just straight-line) and implement IFRS 16 lease compliance (ROU depreciation + payment posting).

**Independent Test**: Create assets with each depreciation method and verify schedules are persisted in `asset_depreciation_schedule`. Create lease contract and verify ROU depreciation schedule generated and payment posting works.

**Depends on**: T003 (money column widening), T004 (revaluation columns)

- [ ] T029 [US6] Persist depreciation schedules for declining balance, sum-of-years, and units-of-production methods in `create_asset` — INSERT into `asset_depreciation_schedule` with method-specific amounts in `backend/routers/finance/assets.py` (FR-029)
- [ ] T030 [US6] Generate straight-line ROU depreciation schedule over lease term after ROU asset recognition in lease creation endpoint in `backend/routers/finance/assets.py` (FR-030)
- [ ] T031 [US6] Add `POST /api/assets/leases/{lease_id}/post-payment` endpoint with interest/principal split per IFRS 16 in `backend/routers/finance/assets.py`; create `LeasePaymentCreate` schema (`payment_date`, `amount: Decimal`) in `backend/schemas/assets.py` (FR-031)

**Checkpoint**: All depreciation methods persist schedules; IFRS 16 lease workflows (ROU depreciation + payment posting) are functional.

---

## Phase 8: User Story 7 — Fix Route Ordering and Missing Validations (Priority: P3)

**Goal**: Move static routes before parameter routes to eliminate confusing 422 errors. Add input validation and replace remaining raw `dict` inputs with Pydantic schemas.

**Independent Test**: Access each static route and verify correct response. Submit invalid input (negative amounts, self-dependencies, reversed dates) and verify rejection with clear errors.

- [ ] T032 [P] [US7] Move all static routes (`/resources/allocation`, `/reports/*`, `/alerts/*`, `/retainer/*`, `/summary`) before `/{project_id}` catch-all in `backend/routers/projects.py` (FR-036)
- [ ] T033 [P] [US7] Move static routes (`/alerts/*`, `/stats/*`) before `/{contract_id}` catch-all in `backend/routers/contracts.py` (FR-037)
- [ ] T034 [US7] Add `start_date <= end_date` validation in `create_project` and `task_id != depends_on_task_id` validation in `create_task_dependency` in `backend/routers/projects.py` (FR-038, FR-039)
- [ ] T035 [US7] Create `ProjectRiskUpdate` and `TaskDependencyCreate` schemas in `backend/schemas/projects.py`; replace raw `dict` in risk update and task dependency endpoints in `backend/routers/projects.py` (FR-040)
- [ ] T036 [P] [US7] Create `AssetTransferCreate`, `AssetRevaluationCreate`, `LeaseContractCreate`, and `ImpairmentTestInput` schemas in `backend/schemas/assets.py`; expand `AssetUpdate` to include all mutable fields; replace raw `dict` in corresponding endpoints in `backend/routers/finance/assets.py` (FR-041)

**Checkpoint**: All static routes resolve correctly; all endpoints validate input via Pydantic schemas.

---

## Phase 9: User Story 8 — Fix Asset Disposal and Revaluation Accounting (Priority: P3)

**Goal**: Preserve historical cost on revaluation, implement IAS 16.40 revaluation surplus tracking, and handle disposal with partial-year depreciation and schedule cancellation.

**Independent Test**: Revalue an asset upward/downward and verify `cost` is preserved, `current_value` updated, and surplus tracked. Dispose mid-year and verify partial depreciation posted + future entries cancelled.

**Depends on**: T004 (revaluation columns `current_value`, `revaluation_surplus` must exist)

- [ ] T037 [US8] Fix revaluation endpoint to update `current_value` instead of `cost` — preserve historical purchase cost in `backend/routers/finance/assets.py` (FR-032)
- [ ] T038 [US8] Implement IAS 16.40 revaluation surplus check — on downward revaluation, reduce existing `revaluation_surplus` first before recognizing excess in P&L in `backend/routers/finance/assets.py` (FR-033)
- [ ] T039 [US8] Cancel un-posted future depreciation schedule entries (`UPDATE ... SET status='cancelled' WHERE status='pending' AND period_start > :disposal_date`) on disposal in `backend/routers/finance/assets.py` (FR-034)
- [ ] T040 [US8] Calculate pro-rata depreciation from period start to disposal date and post partial entry to GL on disposal in `backend/routers/finance/assets.py` (FR-035)

**Checkpoint**: Revaluation preserves cost and tracks surplus per IAS 16; disposal handles partial depreciation and cancels future schedule entries.

---

## Phase 10: User Story 9 — Fix GanttChart Weekend Detection and Report Bugs (Priority: P3)

**Goal**: Fix weekend highlighting in Gantt chart, utilization range labels, project summary params, and asset report count metric.

**Independent Test**: Render Gantt for known date range and verify Saturday/Sunday highlighted. Check utilization labels and asset report counts.

- [ ] T041 [P] [US9] Replace `index % 7` weekend detection with `date.getDay() === 0 || date.getDay() === 6` in `frontend/src/pages/Projects/GanttChart.jsx` (FR-044)
- [ ] T042 [P] [US9] Fix duplicated utilization range — add distinct labels for <50% ("Light"), 50-79% ("Moderate"), >=80% ("Heavy") in `frontend/src/pages/Projects/ResourceUtilizationReport.jsx` (FR-045)
- [ ] T043 [P] [US9] Update `summary()` method to accept and forward query parameters (`{ params }`) in `frontend/src/services/projects.js`; pass `branch_id` from caller in `frontend/src/pages/Projects/ProjectList.jsx` (FR-047)
- [ ] T044 [P] [US9] Fix summary metric to show individual asset count instead of category count in depreciation tab in `frontend/src/pages/Assets/AssetReports.jsx` (FR-048)

**Checkpoint**: Gantt weekends are calendar-correct; all report metrics display accurate data.

---

## Phase 11: User Story 10 — Fix Missing Error Toasts, Security Hardening (Priority: P3)

**Goal**: Add user-visible error feedback on asset pages, fix path traversal vulnerability, and clean up exception handling.

**Independent Test**: Trigger API errors on asset pages and verify toast appears. Attempt path traversal in document deletion and verify blocked. Trigger HTTPException in asset endpoints and verify correct status code (not 500).

- [ ] T045 [P] [US10] Add `toast.error()` notifications to all `catch` blocks that only use `console.log`/`console.error` in `frontend/src/pages/Assets/AssetDetails.jsx` and `frontend/src/pages/Assets/LeaseContracts.jsx` (FR-046)
- [ ] T046 [P] [US10] Add path traversal validation — `os.path.realpath()` + prefix check against configured uploads directory before `os.remove()` in document deletion in `backend/routers/projects.py` (FR-050)
- [ ] T047 [P] [US10] Add `except HTTPException: raise` before generic `except Exception` handler in `post_depreciation` and `create_asset` in `backend/routers/finance/assets.py` (FR-051)
- [ ] T048 [P] [US10] Remove duplicate `check_fiscal_period_open` call in `revalue_asset` in `backend/routers/finance/assets.py` (FR-052)

**Checkpoint**: All errors show user-visible feedback; path traversal blocked; HTTPExceptions propagate correctly.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: No dependencies — start immediately. BLOCKS US6 (T003, T004) and US8 (T004).
- **US1 (Phase 2)**: No backend dependencies — start immediately, parallel with Phase 1.
- **US2 (Phase 3)**: T001 enables retainer endpoint fixes; other tasks can start immediately.
- **US3 (Phase 4)**: Independent — can start immediately.
- **US4 (Phase 5)**: Frontend-only — start immediately, parallel with all backend work.
- **US5 (Phase 6)**: Independent — can start immediately.
- **US6 (Phase 7)**: Depends on T003 + T004 from Phase 1.
- **US7 (Phase 8)**: Independent — can start immediately.
- **US8 (Phase 9)**: Depends on T004 from Phase 1.
- **US9 (Phase 10)**: Frontend-only — start immediately, parallel with all backend work.
- **US10 (Phase 11)**: Independent — can start immediately.

### Parallel Opportunities

- **All Phase 1 tasks** (T001-T005): Different tables/columns, fully parallel.
- **All US1 tasks** (T006-T008): Different files, fully parallel.
- **Frontend stories US1 + US4 + US9**: Fully parallel with each other and with all backend work.
- **Backend stories US2 + US3 + US5 + US7 + US10**: Largely parallel — different files/functions.
- **US6 + US8**: Both modify `assets.py` — run sequentially after Phase 1.

### MVP Scope (P1 Stories Only)

Phase 1 (T001-T005) + US1 (T006-T008) + US2 (T009-T017) = **17 tasks**.  
Delivers: crash-free frontend + error-free backend for all critical operations.

### Incremental Delivery

1. **Phase 1** → Foundation ready (schema + migrations)
2. **US1 + US2** → MVP: no frontend crashes, no backend SQL errors
3. **US3 + US4 + US5** → Financial precision + UI consistency + contract validation
4. **US6 + US7 + US8** → IFRS compliance + route ordering + disposal/revaluation
5. **US9 + US10** → Report accuracy + security + error feedback polish

---

## Task Summary

| Phase | Story | Priority | Tasks | Files |
|-------|-------|----------|-------|-------|
| 1 | Foundation | — | T001-T005 (5) | `database.py`, 5 migrations |
| 2 | US1 | P1 | T006-T008 (3) | 3 frontend pages |
| 3 | US2 | P1 | T009-T017 (9) | `projects.py`, `contracts.py`, `assets.py`, `schemas/projects.py` |
| 4 | US3 | P2 | T018-T020 (3) | 3 schema files, 3 routers, 3 model files |
| 5 | US4 | P2 | T021-T023 (3) | 5 frontend pages |
| 6 | US5 | P2 | T024-T028 (5) | `contracts.py`, `schemas/contracts.py` |
| 7 | US6 | P2 | T029-T031 (3) | `assets.py`, `schemas/assets.py` |
| 8 | US7 | P3 | T032-T036 (5) | `projects.py`, `contracts.py`, `assets.py`, 2 schema files |
| 9 | US8 | P3 | T037-T040 (4) | `assets.py` |
| 10 | US9 | P3 | T041-T044 (4) | 4 frontend pages + `projects.js` |
| 11 | US10 | P3 | T045-T048 (4) | 2 frontend pages, `projects.py`, `assets.py` |
| **Total** | | | **48 tasks** | |
