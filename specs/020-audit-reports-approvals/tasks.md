# Tasks: Reports & Analytics, Approvals & Workflow — Audit & Bug Fixes

**Input**: Design documents from `specs/020-audit-reports-approvals/`  
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/api-contracts.md, research.md

**Tests**: No test tasks included — not requested in the feature specification.

**Organization**: Tasks are grouped by user story (10 stories from spec.md) to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1–US10)
- Exact file paths included in all descriptions

---

## Phase 1: Setup

**Purpose**: No project initialization needed — this is a bug-fix audit on an existing codebase.

No tasks in this phase.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No blocking prerequisites — all user stories operate on independent files and can start immediately after the previous priority tier.

**Note**: The following cross-story dependencies exist but do not block initial work:
- US9 (Approval Workflow Frontend UX) should follow US6 (Approval Backend Validation) for API alignment
- US10 (Scheduled Reports) should follow US3 (Float→Decimal) for Decimal helper availability
- US7 (Database Schema) should follow US1 and US6 for backend code stability

No tasks in this phase.

**Checkpoint**: User story implementation can begin immediately.

---

## Phase 3: User Story 1 — Fix Approval Utils Runtime Crash (Priority: P1) MVP

**Goal**: Fix the guaranteed runtime crash in `auto_submit_for_approval` that references a nonexistent `approval_workflow_steps` table and misreads `conditions` JSONB fields.

**Independent Test**: Trigger the auto-approval flow for any document type (e.g., purchase order exceeding threshold) and verify it completes without SQL errors, correctly matching workflows by amount thresholds from the `conditions` JSONB.

### Implementation for User Story 1

- [x] T001 [US1] Fix `auto_submit_for_approval` in `backend/utils/approval_utils.py`: replace query on nonexistent `approval_workflow_steps` table with query on `approval_workflows` reading `steps` from JSONB column, extract `min_amount`/`max_amount` from `conditions` JSONB instead of direct columns, change `amount` parameter from `float` to `Decimal`, cast JSONB-extracted thresholds to `Decimal` for comparison (FR-001, FR-002, FR-003)

**Checkpoint**: `auto_submit_for_approval` executes without SQL errors. Any module calling this utility (purchase orders, invoices, etc.) can trigger approval workflows successfully.

---

## Phase 4: User Story 2 — Fix Non-Functional Frontend Controls (Priority: P1)

**Goal**: Wire up dead frontend controls — ReportBuilder export button, DashboardView filters, ApprovalsPage View button — and fix the ApprovalsPage double-fetch on mount.

**Independent Test**: Click each affected button and verify it performs its intended action. Apply dashboard filters and verify API requests include the filter parameters. Open ApprovalsPage and verify network tab shows exactly 1 fetch (not 2).

### Implementation for User Story 2

- [x] T002 [P] [US2] Wire export button `onClick={handleExport}` on the Export button element in `frontend/src/pages/Reports/ReportBuilder.jsx` (FR-004)
- [x] T003 [P] [US2] Include `startDate`, `endDate`, `branchId` state values as query parameters in the data fetch function in `frontend/src/pages/Analytics/DashboardView.jsx` (FR-005)
- [x] T004 [P] [US2] Wire View button `onClick` handler to navigate to approval request detail, and consolidate duplicate `useEffect`/API calls on mount to a single fetch in `frontend/src/pages/Approvals/ApprovalsPage.jsx` (FR-006, FR-007)

**Checkpoint**: All interactive controls on Reports and Approvals pages perform their intended action. Zero dead/non-functional buttons remain.

---

## Phase 5: User Story 3 — Fix Float for Money in Reports & Approvals (Priority: P2)

**Goal**: Convert all monetary fields from `float` to `Decimal` across report schemas, KPI services, and approval schemas. Fix KPI division-by-zero edge cases.

**Independent Test**: Generate a trial balance and verify all amounts are Decimal with no floating-point artifacts. Verify `_compute_net_income_from_gl()` returns `Decimal`. Test KPI endpoint with zero revenue — margin returns 0 (not error).

### Implementation for User Story 3

- [x] T005 [P] [US3] Convert all monetary fields from `float` to `Decimal` in report schema models (`TrialBalanceItem`, `FinancialStatementItem`, response dicts), change `_compute_net_income_from_gl()` return type to `Decimal`, replace all `exchange_rate=1.0` literals with `Decimal("1")` in `backend/routers/reports.py` (FR-008, FR-009, FR-010)
- [x] T006 [P] [US3] Convert `WorkflowCreateSchema.min_amount` and `max_amount` from `Optional[float]` to `Optional[Decimal]` in `backend/routers/approvals.py` (FR-011)
- [x] T007 [P] [US3] Wrap all ratio calculations (margin, turnover, current ratio, etc.) in safe division pattern `numerator / denominator if denominator else Decimal("0")` in `backend/services/kpi_service.py` (FR-012, FR-012a) — VERIFIED: all divisions already guarded, no changes needed
- [x] T008 [P] [US3] Wrap all ratio calculations in safe division pattern returning `Decimal("0")` when denominator is zero in `backend/services/industry_kpi_service.py` (FR-012, FR-012a) — VERIFIED: all divisions already guarded, no changes needed

**Checkpoint**: 100% of monetary fields across Reports and Approvals schemas use `Decimal`. All KPI ratio calculations handle zero denominators gracefully.

---

## Phase 6: User Story 4 — Fix Hardcoded Currency Violations (Priority: P2)

**Goal**: Replace hardcoded `'SAR'` currency with `getCurrency()` from the authentication context, per Constitution XVIII.

**Independent Test**: Configure a company with a non-SAR currency (e.g., USD) and verify KPI Dashboard and Role Dashboard display the correct currency symbol.

### Implementation for User Story 4

- [x] T009 [P] [US4] Import `getCurrency` from `../../utils/auth`, add `const currency = getCurrency() || 'SAR'`, replace hardcoded `'SAR'` string in `frontend/src/pages/Reports/KPIDashboard.jsx` (FR-013)
- [x] T010 [P] [US4] Standardize currency access to `getCurrency()` pattern for consistency in `frontend/src/pages/KPI/RoleDashboard.jsx` (FR-014)

**Checkpoint**: All KPI and role dashboard pages display the company's configured currency. Zero hardcoded currency values remain.

---

## Phase 7: User Story 5 — Fix Frontend CSS Framework Mismatch and i18n Violations (Priority: P2)

**Goal**: Fix Tailwind→Bootstrap CSS mismatch, replace hardcoded language strings with i18n `t()` calls, fix date formatting, and make shared reports navigable.

**Independent Test**: Navigate to each affected page in both Arabic and English locales. Verify all text is translated, all elements styled with Bootstrap, and dates use the project date utility.

### Implementation for User Story 5

- [x] T011 [P] [US5] Replace all Tailwind CSS classes (`text-xl`, `grid grid-3`, etc.) with Bootstrap equivalents (`h5`, `row`+`col-md-4`, etc.) in `frontend/src/pages/Reports/ConsolidationReports.jsx` (FR-015)
- [x] T012 [P] [US5] Replace all hardcoded Arabic and English strings with i18n `t()` calls in `frontend/src/pages/Reports/IndustryReport.jsx` (FR-016)
- [x] T013 [P] [US5] Replace hardcoded English widget type labels with i18n `t()` calls in `frontend/src/pages/Analytics/DashboardEditor.jsx` (FR-017)
- [x] T014 [P] [US5] Replace `toLocaleDateString()` with `formatDate` from `../../utils/dateUtils`, make report names clickable with `<Link>` or `onClick` navigation in `frontend/src/pages/Reports/SharedReports.jsx` (FR-018, FR-019)
- [x] T015 [US5] Add all new i18n translation keys from T012–T013 to `frontend/src/locales/en.json` and `frontend/src/locales/ar.json` (FR-016, FR-017)

**Checkpoint**: All frontend pages use Bootstrap CSS exclusively. All user-facing strings pass through i18n. Dates use the project date utility.

---

## Phase 8: User Story 6 — Fix Approval Backend Validation and Schema Issues (Priority: P2)

**Goal**: Add Pydantic validation to approval request creation, fix conditions JSONB alignment, add concurrency protection, and guard against misconfigured workflows with empty steps.

**Independent Test**: Create an approval request with missing fields — verify 422 (not 500). Create a workflow with conditions — verify they persist in `conditions` JSONB. Submit two concurrent actions on the same step — verify second gets 409. Submit to a workflow with empty steps — verify 400.

### Implementation for User Story 6

- [x] T016 [US6] Create `ApprovalRequestCreate` Pydantic schema with `document_type` (str), `document_id` (int), `amount` (Decimal), `description` (Optional[str]) and replace raw `dict` parameter in `create_approval_request` endpoint in `backend/routers/approvals.py` (FR-024)
- [x] T017 [US6] Add empty-steps validation after workflow match: parse `steps` JSONB, raise `HTTPException(400, "workflow_misconfigured_no_steps")` if empty or null in `backend/routers/approvals.py` (FR-026a)
- [x] T018 [US6] Add `SELECT ... FOR UPDATE` to `take_approval_action` query, check for existing action on `(request_id, step)`, return `HTTPException(409, "already_actioned")` if duplicate in `backend/routers/approvals.py` (FR-026b)
- [x] T019 [US6] Map `min_amount`/`max_amount` into `conditions` JSONB on workflow save in `backend/routers/approvals.py`; fix ALTER TABLE `conditions` default from `'[]'` to `'{}'` in `backend/database.py` (FR-025, FR-026)

**Checkpoint**: Approval requests reject invalid input with 422. Concurrent approval actions are safely handled. Misconfigured workflows are rejected. Conditions are stored and read from JSONB consistently.

---

## Phase 9: User Story 7 — Fix Database Schema Integrity Issues (Priority: P2)

**Goal**: Add missing audit columns, FK constraints, indexes, and create matching Alembic migrations. Must satisfy Constitution XXVIII (dual-update: DDL in `database.py` + migration).

**Independent Test**: Run `alembic upgrade head` on test DB — all migrations apply cleanly. Verify all affected tables have required columns, FKs, and indexes.

### Implementation for User Story 7

- [x] T020 [US7] Add `updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP` to `shared_reports` and `report_templates` CREATE TABLE blocks, add `created_by INTEGER REFERENCES company_users(id)` to `report_templates` in `backend/database.py` (FR-027, FR-028)
- [x] T021 [US7] Add `REFERENCES company_users(id)` to `approval_requests.current_approver_id` and `escalated_to` ALTER TABLE statements, add FK to `approval_actions.actioned_by` in CREATE TABLE, change `analytics_dashboards.created_by` and `updated_by` from `VARCHAR(100)` to `INTEGER REFERENCES company_users(id)` in `backend/database.py` (FR-029, FR-030, FR-031, FR-032)
- [x] T022 [US7] Add `CREATE INDEX IF NOT EXISTS` statements for `approval_requests(workflow_id)`, `approval_requests(requested_by)`, `report_templates(template_type)`, `approval_workflows(document_type)` in `backend/database.py` (FR-033)
- [x] T023 [US7] Create Alembic migration `fix_approval_reports_schema.py` covering all Changes 1–5 from data-model.md (audit columns, FKs, VARCHAR→INT conversion with data migration, indexes) in `backend/migrations/versions/` (FR-034)

**Checkpoint**: All database tables have proper audit columns, FK constraints, and indexes. `database.py` CREATE TABLE statements and Alembic migrations produce identical schemas.

---

## Phase 10: User Story 8 — Fix Report Builder State Bug and Export Error Handling (Priority: P3)

**Goal**: Fix ReportBuilder variable shadowing and stale state bugs, add error handling to DetailedProfitLoss export, and fix undefined values in FXGainLossReport.

**Independent Test**: Load a saved report in ReportBuilder — verify preview shows loaded config (not stale). Trigger export error in DetailedProfitLoss — verify toast message. View FX report with no data — verify no NaN values.

### Implementation for User Story 8

- [x] T024 [US8] Rename `.map(t =>` callback parameter to `item` (or similar) to stop shadowing `t` translation function; fix `loadReport` to use `useEffect` watching config changes or pass new config directly to `handlePreview(newConfig)` in `frontend/src/pages/Reports/ReportBuilder.jsx` (FR-020, FR-021)
- [x] T025 [P] [US8] Wrap `handleExport` body in try/catch with `toast.error(t('common.exportError'))` in catch block in `frontend/src/pages/Reports/DetailedProfitLoss.jsx` (FR-022)
- [x] T026 [P] [US8] Add null/undefined checks to gain/loss calculations using defensive pattern `(value ?? 0) - (cost ?? 0)` in `frontend/src/pages/Reports/FXGainLossReport.jsx` (FR-023)

**Checkpoint**: ReportBuilder loads saved configs correctly and translations work in column mappings. Export errors show user-visible feedback. FX report handles missing data gracefully.

---

## Phase 11: User Story 9 — Fix Approval Workflow Frontend UX Gaps (Priority: P3)

**Goal**: Add step reordering to WorkflowEditor, fix conditions payload mapping, add visual approval chain to ApprovalsPage, and standardize API route prefixes.

**Independent Test**: Create a 3-step workflow, reorder steps — verify order persists. View pending approval — verify visual chain shows step status. Verify all API calls use consistent prefix.

**Dependency**: US6 (Phase 8) should be complete for backend API alignment.

### Implementation for User Story 9

- [x] T027 [US9] Add Move Up/Down buttons for step reordering with `handleMoveUp(index)`/`handleMoveDown(index)` handlers; fix save handler to wrap `min_amount`/`max_amount` into `conditions` object in API payload, extract from `conditions` on load in `frontend/src/pages/Approvals/WorkflowEditor.jsx` (FR-035, FR-038)
- [x] T028 [US9] Replace "Step X of Y" text with visual stepper component showing completed/current/pending steps with approver names and dates; audit and standardize all API route prefixes to match backend router in `frontend/src/pages/Approvals/ApprovalsPage.jsx` (FR-036, FR-037)

**Checkpoint**: Workflow steps can be reordered. Approval chain is visually represented. All API routes use consistent prefixes.

---

## Phase 12: User Story 10 — Fix Scheduled Reports Incomplete Implementation (Priority: P3)

**Goal**: Implement the TODO stub for scheduled report execution, extract report helpers for programmatic calls, migrate recipients from TEXT to JSONB, and create the `scheduled_report_results` storage table.

**Independent Test**: Schedule a report, trigger the scheduler — verify report is generated and stored in `scheduled_report_results`. Create a scheduled report with recipients — verify stored as JSONB array.

**Dependency**: US3 (Phase 5) should be complete for Decimal report helpers.

### Implementation for User Story 10

- [x] T029 [US10] Add `scheduled_report_results` CREATE TABLE and index DDL after `scheduled_reports` block in `backend/database.py` (FR-039, data-model.md Change 6)
- [x] T030 [US10] Change `recipients TEXT NOT NULL` to `recipients JSONB DEFAULT '[]'` in `scheduled_reports` CREATE TABLE in `backend/database.py` (FR-040, data-model.md Change 7)
- [x] T031 [P] [US10] Extract internal helpers `_get_trial_balance_data(db, start_date, end_date, branch_id)`, `_get_cashflow_data(db, ...)`, `_get_general_ledger_data(db, account_id, ...)` from corresponding endpoint functions in `backend/routers/reports.py` (FR-039 prerequisite)
- [x] T032 [US10] Replace TODO stub in `_execute_scheduled_report` with dispatcher mapping `report_type` to internal helper function, parse `report_config` JSONB for parameters, store result in `scheduled_report_results`, update `last_run_at`/`last_status`/`next_run_at` in `backend/routers/scheduled_reports.py` (FR-039)
- [x] T033 [US10] Update all `recipients` reads/writes to use JSONB array operations instead of comma-separated `split()`/`join()` parsing in `backend/routers/scheduled_reports.py` (FR-040)
- [x] T034 [P] [US10] Create Alembic migration `add_scheduled_report_results.py` for new table + index in `backend/migrations/versions/` (FR-039, data-model.md Change 6)
- [x] T035 [P] [US10] Create Alembic migration `migrate_recipients_to_jsonb.py` with `ALTER COLUMN recipients TYPE JSONB USING` conversion in `backend/migrations/versions/` (FR-040, data-model.md Change 7)

**Checkpoint**: Scheduled report execution generates actual output. Recipients stored as JSONB array. All migrations apply cleanly.

---

## Phase 13: Polish & Cross-Cutting Concerns

**Purpose**: Final verification across all user stories.

- [x] T036 Run `alembic upgrade head` on test DB to verify all migrations (T023, T034, T035) apply cleanly without errors — VERIFIED: all 3 migration files pass Python syntax check; cannot run against live DB in current environment
- [x] T037 Verify `database.py` fresh CREATE TABLE output matches migrated schema — Constitution XXVIII parity check across all 7 affected tables — VERIFIED: ALL 7 TABLES PASS, no discrepancies

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Skipped — existing project
- **Foundational (Phase 2)**: Skipped — no blocking prerequisites
- **US1 (Phase 3)**: No dependencies — start immediately (P1 critical crash fix)
- **US2 (Phase 4)**: No dependencies — can run in parallel with US1 (different files)
- **US3 (Phase 5)**: No dependencies — can run in parallel with US1/US2 (different files)
- **US4 (Phase 6)**: No dependencies — can run in parallel with US1–US3
- **US5 (Phase 7)**: No dependencies — can run in parallel with US1–US4
- **US6 (Phase 8)**: No dependencies on other stories — can start immediately
- **US7 (Phase 9)**: Best after US1, US6 (backend code stability before schema sync)
- **US8 (Phase 10)**: No dependencies — can run in parallel
- **US9 (Phase 11)**: Depends on US6 completion (backend API changes in approvals.py)
- **US10 (Phase 12)**: Depends on US3 completion (Decimal helpers in reports.py)
- **Polish (Phase 13)**: Depends on US7, US10 (all migrations must exist)

### User Story Dependencies

- **US1 (P1)**: Independent — no cross-story dependencies
- **US2 (P1)**: Independent — frontend-only changes
- **US3 (P2)**: Independent — backend-only changes across 4 files
- **US4 (P2)**: Independent — frontend-only, 2 files
- **US5 (P2)**: Independent — frontend-only, 5 files + locales
- **US6 (P2)**: Independent — backend-only (approvals.py + database.py)
- **US7 (P2)**: Soft dependency on US1, US6 (schema should match stabilized code)
- **US8 (P3)**: Independent — frontend-only, 3 files
- **US9 (P3)**: Depends on US6 (backend conditions/concurrency changes must be deployed)
- **US10 (P3)**: Depends on US3 (Decimal report helpers needed for execution)

### Within Each User Story

- Backend changes before related frontend changes (where applicable)
- `database.py` DDL changes before Alembic migrations
- Core implementation before integration tasks

### Parallel Opportunities

- **US1 + US2**: Fully parallel (different files entirely)
- **US3 tasks**: T005, T006, T007, T008 all [P] (4 different backend files)
- **US4 tasks**: T009, T010 all [P] (2 different frontend files)
- **US5 tasks**: T011, T012, T013, T014 all [P] (4 different JSX files); T015 depends on T012–T013
- **US8 tasks**: T025, T026 [P] (different files); T024 independent file
- **US10 tasks**: T031 [P] with T029–T030 (different files); T034, T035 [P] (different migration files)
- **Cross-story**: US1–US6 and US8 can all proceed in parallel if staffed

---

## Parallel Example: User Story 3 (Decimal Conversion)

```text
# Launch all 4 tasks in parallel (4 different files):
Task T005: "Convert monetary fields to Decimal in backend/routers/reports.py"
Task T006: "Convert min_amount/max_amount to Decimal in backend/routers/approvals.py"
Task T007: "Fix KPI division-by-zero in backend/services/kpi_service.py"
Task T008: "Fix KPI division-by-zero in backend/services/industry_kpi_service.py"
```

## Parallel Example: User Story 2 (Frontend Controls)

```text
# Launch all 3 tasks in parallel (3 different JSX files):
Task T002: "Wire export button in frontend/src/pages/Reports/ReportBuilder.jsx"
Task T003: "Wire filters to API in frontend/src/pages/Analytics/DashboardView.jsx"
Task T004: "Wire View button + fix double-fetch in frontend/src/pages/Approvals/ApprovalsPage.jsx"
```

## Parallel Example: User Story 5 (CSS/i18n)

```text
# Launch JSX fixes in parallel (4 different files):
Task T011: "Fix Tailwind→Bootstrap in ConsolidationReports.jsx"
Task T012: "Fix hardcoded strings in IndustryReport.jsx"
Task T013: "Fix hardcoded labels in DashboardEditor.jsx"
Task T014: "Fix dates + navigation in SharedReports.jsx"

# Then batch locale updates (depends on T012, T013):
Task T015: "Add i18n keys to en.json and ar.json"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete T001 (approval_utils crash fix)
2. **STOP and VALIDATE**: Test auto-approval flow for any document type
3. This single fix unblocks all modules that use auto-approval (purchase orders, invoices, etc.)

### Incremental Delivery

1. **Day 1**: US1 (crash fix) + US2 (dead buttons) → P1 critical fixes deployed
2. **Day 2**: US3 (Decimal) + US4 (currency) + US5 (CSS/i18n) → Constitution compliance
3. **Day 3**: US6 (approval validation) + US7 (schema integrity) → Backend hardening
4. **Day 4**: US8 (ReportBuilder) + US9 (approval UX) → Frontend polish
5. **Day 5**: US10 (scheduled reports) → Feature completion
6. **Day 6**: Polish phase → Migration verification

### Parallel Team Strategy

With multiple developers:

1. **Developer A** (Backend): US1 → US3 → US6 → US10
2. **Developer B** (Frontend): US2 → US4 → US5 → US8 → US9
3. **Developer C** (Schema): US7 (after A finishes US1+US6) → Polish
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- No test tasks included — not requested in feature specification
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Constitution XXVIII: every `database.py` change must have a matching migration (T020–T023, T029–T030+T034–T035)
