# Feature Specification: Projects, Contracts & Fixed Assets — Audit & Bug Fixes

**Feature Branch**: `019-audit-projects-assets`  
**Created**: 2026-04-20  
**Status**: Draft  
**Input**: Full code audit of Projects (59 endpoints), Contracts (12 endpoints), and Fixed Assets (31 endpoints) — backend routers, Pydantic schemas, SQLAlchemy models, and 16 frontend pages. Audit scope includes cross-module integration with GL, HR, Sales, Budgets, and Approvals.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Fix Critical Runtime Crashes in Projects Frontend (Priority: P1)

Several Project pages crash immediately on load due to missing imports and undeclared state variables, making the Projects module partially unusable.

**Why this priority**: Users cannot use Project Details, Timesheets, or Risk Management at all — these pages throw unrecoverable JavaScript errors on mount.

**Independent Test**: Navigate to each fixed page and verify it loads without console errors, displays data correctly, and all interactive features (forms, buttons) function.

**Acceptance Scenarios**:

1. **Given** a user opens Project Details for any project, **When** the page renders, **Then** no runtime error occurs and the overview tab displays formatted dates and all project info correctly.
2. **Given** a user opens the Timesheets page for any project, **When** the user attempts to save a timesheet entry, **Then** the save operation works without a "setSubmitting is not defined" crash.
3. **Given** a user opens the Project Risks page, **When** the user selects a project from the dropdown, **Then** the project name appears (not blank/undefined) and task dependency dropdowns are populated using the correct API method.

---

### User Story 2 — Fix Critical Backend SQL Errors and Data Corruption (Priority: P1)

Multiple backend endpoints reference wrong column names, wrong table names, or have type mismatches that cause SQL errors or silent data corruption at runtime.

**Why this priority**: These are runtime failures that prevent core operations — task dependencies fail silently, contract KPIs return errors, risk creation stores wrong data types, and the impairment test calculates incorrect losses.

**Independent Test**: Call each affected endpoint and verify it returns correct data without SQL errors. Verify data types stored in the database match the column definitions.

**Acceptance Scenarios**:

1. **Given** a project with task dependencies exists, **When** a user fetches task dependencies via the API, **Then** the response includes correct task names (querying `task_name` column, not `name`).
2. **Given** a user creates a project risk with probability "high" and impact "medium", **When** the risk is saved, **Then** the database stores string values "high"/"medium" (not Decimal numbers) matching the `String(20)` column type.
3. **Given** an active asset exists, **When** a user runs an impairment test, **Then** the carrying amount is correctly computed from the `cost` column (not the nonexistent `purchase_cost` column) and the `journal_entry_id` is returned in the response (not always `None`).
4. **Given** a user approves timesheets for a project, **When** the approval runs, **Then** no `AttributeError` occurs for `project.branch_id` because the SELECT query includes the `branch_id` column.
5. **Given** a user posts depreciation for an asset, **When** the GL journal entry is created, **Then** the `user_id` parameter receives the current user's numeric ID (not their username string).

---

### User Story 3 — Fix Constitution I Violations: Float for Money (Priority: P2)

All three modules (Projects, Contracts, Assets) use Python `float` type for monetary fields in Pydantic schemas, SQLAlchemy model type hints, and GL service calls. This violates Constitution I (no float for money) and causes precision loss in financial calculations.

**Why this priority**: Financial precision errors accumulate silently and affect project profitability reports, contract totals, asset book values, and GL entries. This is a systemic issue across ~30+ fields.

**Independent Test**: Verify all monetary fields in schemas use `Decimal`, all GL calls pass `Decimal` for `exchange_rate`, and all monetary calculations use `Decimal` arithmetic.

**Acceptance Scenarios**:

1. **Given** a user creates a project with a budget of 1,234,567.89, **When** the project is saved and re-fetched, **Then** the budget retains exact precision without floating-point rounding artifacts.
2. **Given** a user creates a contract with line items, **When** the server calculates the total, **Then** all intermediate and final calculations use `Decimal` arithmetic and the total matches manual calculation to the cent.
3. **Given** an asset depreciation schedule is generated, **When** the annual amounts are summed, **Then** the total equals `cost - residual_value` exactly, with no rounding discrepancies from float math.

---

### User Story 4 — Fix Frontend Field Name Mismatches in Assets Pages (Priority: P2)

Multiple Asset frontend pages use inconsistent field names (`code` vs `asset_code`, `name` vs `asset_name`, `branch_name` vs `name`) and one page uses Tailwind CSS classes in a Bootstrap project, rendering badges and layouts unstyled.

**Why this priority**: Asset pages display blank/missing data in columns and have unstyled UI elements, degrading the user experience for asset management workflows.

**Independent Test**: Navigate to each asset page and verify all data columns display correctly. Verify all badges and layout elements are properly styled.

**Acceptance Scenarios**:

1. **Given** a user opens the Asset List page, **When** assets are loaded, **Then** all columns (code, name, type, cost, status) display correct values using consistent field names from the API.
2. **Given** a user opens Asset Management, **When** transfers and revaluations are listed, **Then** status badges are styled with the project's CSS framework (Bootstrap), not Tailwind classes.
3. **Given** a user opens the Impairment Test page, **When** monetary values are displayed, **Then** the currency symbol matches the company's configured currency (not hardcoded SAR).

---

### User Story 5 — Fix Contract Router Error Handling and Validation (Priority: P2)

The `create_contract` endpoint swallows `HTTPException` and returns 500 for all errors (including 400 validation errors). Multiple contract endpoints accept raw `dict` without validation. The `update_contract` endpoint does not recalculate totals from line items.

**Why this priority**: Users receive unhelpful "Internal Server Error" messages for simple validation failures (duplicate contract number, end date before start date), and unvalidated input can cause data integrity issues.

**Independent Test**: Trigger each validation error and verify the correct HTTP status code and error message are returned. Submit invalid contract amendments and verify they are rejected.

**Acceptance Scenarios**:

1. **Given** a user attempts to create a contract with a duplicate contract number, **When** the request is sent, **Then** the server returns 400 (not 500) with a meaningful error message.
2. **Given** a user creates a contract amendment, **When** the amendment payload is missing required fields (`amendment_type`, `effective_date`), **Then** the server returns 422 with validation errors.
3. **Given** a user updates a contract's line items, **When** the update is saved, **Then** the contract total is recalculated server-side from the items (not accepted from the client payload).

---

### User Story 6 — Fix Asset Depreciation and IFRS Compliance Gaps (Priority: P2)

Only straight-line depreciation schedules are persisted on asset creation. Declining balance, sum-of-years, and units-of-production methods return read-only JSON but do not create schedule entries. IFRS 16 lease contracts lack ROU asset depreciation and periodic payment posting.

**Why this priority**: Assets using non-straight-line methods cannot have depreciation posted to the GL. IFRS 16 compliance is incomplete — ROU assets are recognized but never depreciated, and lease payments are not journalized.

**Independent Test**: Create assets with each depreciation method and verify schedules are persisted. Create a lease contract and verify ROU depreciation schedule is generated and payment posting works.

**Acceptance Scenarios**:

1. **Given** a user creates an asset with "declining_balance" depreciation method, **When** the asset is saved, **Then** a depreciation schedule is generated and persisted in `asset_depreciation_schedule`, allowing each period to be posted to the GL.
2. **Given** a lease contract is created, **When** initial recognition is complete, **Then** a depreciation schedule for the right-of-use asset is created over the lease term.
3. **Given** a lease payment is due, **When** the user posts the payment, **Then** a GL entry splits the payment into interest expense and lease liability reduction per IFRS 16.

---

### User Story 7 — Fix Route Ordering and Missing Validations in Projects Router (Priority: P3)

Static routes like `/projects/resources/allocation`, `/projects/reports/profitability`, and `/projects/alerts/*` are defined after the `/{project_id}` parameter route. While FastAPI's type validation prevents silent mismatches, users get confusing 422 errors. Additionally, multiple endpoints lack input validation (date ranges, positive amounts, enum values).

**Why this priority**: Users encounter unhelpful error messages when accessing report/alert URLs. Missing validations allow invalid data (negative amounts, end dates before start dates, self-referencing task dependencies).

**Independent Test**: Access each static route and verify it returns correct data. Submit invalid input to each endpoint and verify it is rejected with clear error messages.

**Acceptance Scenarios**:

1. **Given** a user requests `/projects/reports/profitability`, **When** the request is processed, **Then** the profitability report is returned (not a 422 error about invalid project_id).
2. **Given** a user creates a project with `end_date` before `start_date`, **When** the request is submitted, **Then** the server returns a validation error.
3. **Given** a user creates a task dependency where `task_id` equals `depends_on_task_id`, **When** the request is submitted, **Then** the server rejects it as a self-dependency.

---

### User Story 8 — Fix Asset Disposal and Revaluation Accounting (Priority: P3)

Asset disposal does not create a disposal record, does not cancel future depreciation entries, and does not handle partial-year depreciation. Revaluation overwrites historical cost instead of tracking revalued amounts separately. Revaluation decreases do not check for prior surplus per IAS 16.

**Why this priority**: Disposal and revaluation are less frequent operations but when they occur, incorrect accounting causes audit findings and misstated financial statements.

**Independent Test**: Dispose of an asset mid-year and verify partial depreciation is posted, future schedule entries are cancelled, and the GL entry correctly records gain/loss. Revalue an asset and verify historical cost is preserved.

**Acceptance Scenarios**:

1. **Given** an asset is disposed mid-year, **When** the disposal is processed, **Then** depreciation for the partial period up to the disposal date is calculated and posted, and all future schedule entries are marked as cancelled.
2. **Given** an asset is revalued upward, **When** the revaluation is posted, **Then** the original `cost` is preserved and a separate `revalued_amount` or `current_value` field is updated.
3. **Given** an asset was previously revalued upward (creating a surplus), **When** a subsequent downward revaluation occurs, **Then** the decrease first reduces the existing revaluation surplus before any excess is recognized in profit/loss.

---

### User Story 9 — Fix GanttChart Weekend Detection and Report Bugs (Priority: P3)

The Gantt chart marks weekends based on array index (`index % 7`) rather than actual calendar day, producing incorrect weekend highlighting. The Resource Utilization report has a duplicated range check. The Asset Reports page shows category count as asset count.

**Why this priority**: Incorrect weekend highlighting misleads project managers during scheduling. Report bugs show wrong metrics.

**Independent Test**: Render the Gantt chart for a known date range and verify weekends are correctly highlighted. Check utilization report labels and asset report counts.

**Acceptance Scenarios**:

1. **Given** a project with tasks spanning multiple weeks, **When** the Gantt chart renders, **Then** Saturday and Sunday columns are highlighted as weekends based on `getDay()`, regardless of the start date's day of week.
2. **Given** employees with 50-79% utilization, **When** the Resource Utilization report renders, **Then** they are labeled as "moderate" (not "light") with a distinct label from the <50% range.
3. **Given** an asset depreciation summary report, **When** the summary metrics display, **Then** the "asset count" shows the total number of individual assets, not the number of asset categories.

---

### User Story 10 — Fix N+1 Queries, Missing Error Toasts, and Security Hardening (Priority: P3)

The `list_contracts` endpoint executes N+1 queries (1 query per contract for items). Multiple frontend pages silently swallow errors without showing user-facing toasts. The document deletion endpoint has a path traversal risk.

**Why this priority**: N+1 queries degrade performance with scale. Silent errors leave users confused. Path traversal is a security risk.

**Independent Test**: Run `list_contracts` with 50+ contracts and verify a single batched query is used. Trigger errors in each frontend page and verify toast notifications appear. Attempt path traversal in document deletion and verify it is blocked.

**Acceptance Scenarios**:

1. **Given** 50 contracts exist, **When** a user lists all contracts, **Then** the server executes at most 2 SQL queries (one for contracts, one for all items) instead of 51.
2. **Given** a user's API call fails on the Asset Details page (revalue, transfer, depreciate), **When** the error occurs, **Then** a user-visible error toast is shown (not just console.log).
3. **Given** an attacker tampers with a document's `file_url` in the database to `../../etc/passwd`, **When** a delete request is made, **Then** the server validates the path is within the uploads directory before deletion.

---

### Edge Cases

- What happens when a project has 0 tasks and the Gantt chart is rendered? (Empty state handling)
- What happens when an asset with posted depreciation entries is disposed? (Must not allow re-posting cancelled entries)
- What happens when a contract's line items sum to zero? (Division by zero in KPI percentage calculation)
- What happens when a lease has a 0% discount rate? (Division by zero in PV calculation)
- What happens when `create_project` is called with `branch_id` — is it silently dropped? (Currently yes — bug)
- What happens when two users approve the same timesheet batch simultaneously? (Race condition)
- What happens when `generate_retainer_invoices` runs but `customers` table doesn't exist? (Currently crashes — uses wrong table name)

---

## Requirements *(mandatory)*

### Functional Requirements

**A — Critical Backend Fixes (Runtime Crashes & Data Corruption)**

- **FR-001**: System MUST query `task_name` (not `name`) in the task dependencies SQL JOIN in `projects.py`
- **FR-002**: System MUST JOIN `company_users` (not `users`) in project risk listing and contract amendment listing
- **FR-003**: System MUST accept and store `probability` and `impact` as string enum values ("low", "medium", "high", "critical") matching the `String(20)` column type in `project_risks`
- **FR-004**: System MUST include `branch_id` in the SELECT query within `approve_timesheets` to prevent `AttributeError`
- **FR-005**: System MUST compute carrying amount from the `cost` column (not `purchase_cost`) in the impairment test endpoint
- **FR-006**: System MUST assign the journal entry ID to the `journal_entry_id` variable (not leave it as `None`) in the impairment test response
- **FR-007**: System MUST pass `current_user.id` (not `current_user.username`) as `user_id` to `gl_create_journal_entry` in `post_depreciation`
- **FR-008**: System MUST include `branch_id` and `contract_type` in the `create_project` INSERT statement
- **FR-009**: System MUST use `parties` table (not `customers`) in `generate_retainer_invoices` JOIN
- **FR-010**: System MUST use correct column names in contract KPI queries (`total` not `total_amount`, compute balance instead of using nonexistent `balance_due`)

**B — Frontend Runtime Crash Fixes**

- **FR-011**: ProjectDetails.jsx MUST import `useRef` from React
- **FR-012**: ProjectDetails.jsx MUST import and use the correct date formatting function (`formatShortDate` instead of undefined `formatDate`)
- **FR-013**: Timesheets.jsx MUST declare `submitting` state variable via `useState`
- **FR-014**: ProjectRisks.jsx MUST use the existing `projectsAPI.getTasks` method (not nonexistent `listTasks`)
- **FR-015**: ProjectRisks.jsx MUST use `p.project_name` (not `p.name`) for project dropdown display
- **FR-016**: ProjectRisks.jsx MUST use `t.task_name` (not `t.name`) for task dropdown display
- **FR-017**: AssetManagement.jsx MUST import from the correct service path (`../../utils/api`)
- **FR-018**: AssetManagement.jsx MUST use Bootstrap CSS classes (not Tailwind) for badges and layout

**C — Constitution I: Decimal for Money**

- **FR-019**: All monetary fields in `schemas/projects.py` MUST use `Decimal` type (budget, amount, hours, unit_price, tax_rate, discount, exchange_rate, cost_impact, retainer_amount)
- **FR-020**: All monetary fields in `schemas/contracts.py` MUST use `Decimal` type (quantity, unit_price, tax_rate, total, total_amount)
- **FR-021**: All monetary fields in `schemas/assets.py` MUST use `Decimal` type (cost, residual_value, disposal_price, new_value)
- **FR-022**: All `exchange_rate=1.0` literals MUST be changed to `Decimal("1")` in projects, contracts, and assets routers
- **FR-023**: All SQLAlchemy model type hints for `Numeric` columns MUST use `Mapped[Decimal]` (not `Mapped[float]`)

**D — Contract Router Fixes**

- **FR-024**: `create_contract` MUST re-raise `HTTPException` before the generic `except Exception` handler
- **FR-025**: `create_amendment` MUST accept a Pydantic schema with validated fields (amendment_type, effective_date, description) instead of raw `dict`
- **FR-026**: `update_contract` MUST recalculate `total_amount` from line items server-side (not accept client-provided total)
- **FR-027**: `list_contracts` MUST fetch contract items via a single batched query (not N+1)
- **FR-028**: `update_contract` MUST use a `ContractUpdate` schema allowing partial updates (not reuse `ContractCreate`)

**E — Asset Depreciation & IFRS Compliance**

- **FR-029**: System MUST persist depreciation schedules for declining balance, sum-of-years, and units-of-production methods on asset creation (not only straight-line)
- **FR-030**: System MUST create a depreciation schedule for right-of-use assets on lease contract creation per IFRS 16
- **FR-031**: System MUST provide an endpoint to post lease payments with interest/principal split per IFRS 16
- **FR-032**: System MUST preserve historical `cost` on revaluation (update `current_value` or a revalued amount field, not overwrite `cost`)
- **FR-033**: System MUST check and reduce existing revaluation surplus before recognizing downward revaluation in profit/loss per IAS 16.40
- **FR-034**: System MUST cancel un-posted future depreciation schedule entries on asset disposal
- **FR-035**: System MUST calculate and post partial-year depreciation up to the disposal date

**F — Route Ordering & Input Validation**

- **FR-036**: All static project routes (`/resources/*`, `/reports/*`, `/alerts/*`, `/retainer/*`) MUST be defined before the `/{project_id}` parameter route
- **FR-037**: All static contract routes (`/alerts/*`, `/stats/*`) MUST be defined before the `/{contract_id}` parameter route
- **FR-038**: `create_project` MUST validate that `start_date` <= `end_date`
- **FR-039**: `create_task_dependency` MUST validate that `task_id` != `depends_on_task_id`
- **FR-040**: `create_project_risk`, `update_project_risk`, and `create_task_dependency` MUST accept Pydantic schemas instead of raw `dict`
- **FR-041**: `create_asset_transfer`, `create_revaluation`, `create_lease_contract`, and `run_impairment_test` MUST accept Pydantic schemas instead of raw `dict`

**G — Frontend Consistency & Error Handling**

- **FR-042**: All Asset pages MUST use consistent field names for API data (`code`/`name` vs `asset_code`/`asset_name` — standardize to whichever the API returns)
- **FR-043**: All Asset pages MUST use consistent branch field name (`branch_name` — standardize across AssetForm, AssetDetails, AssetManagement)
- **FR-044**: GanttChart.jsx MUST detect weekends using `date.getDay()` (not `index % 7`)
- **FR-045**: ResourceUtilizationReport.jsx MUST have distinct labels for <50%, 50-79%, and >=80% utilization ranges
- **FR-046**: All frontend pages that catch API errors MUST display user-visible error feedback (toast or inline message), not only `console.log`
- **FR-047**: `projectsAPI.summary()` MUST accept and forward query parameters (branch_id) to the backend
- **FR-048**: AssetReports.jsx MUST show individual asset count (not category count) in the summary metric for the depreciation tab
- **FR-049**: ImpairmentTest.jsx MUST use the company's configured currency (not hardcoded SAR)

**H — Security & Error Swallowing**

- **FR-050**: Document deletion in `projects.py` MUST validate that the resolved file path is within the configured uploads directory before calling `os.remove`
- **FR-051**: `post_depreciation` and `create_asset` in `assets.py` MUST re-raise `HTTPException` before the generic `except Exception` handler
- **FR-052**: Remove duplicate `check_fiscal_period_open` call in `revalue_asset`

### Key Entities

- **Project**: Central entity linking tasks, budgets, expenses, revenues, timesheets, risks, documents, and change orders. Has dual customer references (`customer_id` and `party_id`) that should be reconciled.
- **ProjectTask**: Hierarchical (via `parent_task_id`) work breakdown with assignments to employees. Supports dependencies via `TaskDependency`.
- **ProjectRisk**: Risk register entry with string-based probability/impact and numeric risk score. Linked to an owner via `company_users`.
- **ProjectTimesheet**: Time entry linking employee, project, and task. `employee_id` FK points to `company_users` but is sometimes JOINed as if it points to `employees` — semantics must be clarified.
- **Contract**: Party-linked agreement with line items, amendments, and billing intervals. Supports renewal and invoice generation.
- **Asset**: Fixed asset with purchase cost, residual value, useful life, and depreciation method. Supports transfers, revaluations, disposals, insurance, and maintenance.
- **AssetDepreciationSchedule**: Per-period depreciation entries that can be posted to GL via journal entries.
- **LeaseContract**: IFRS 16 lease with ROU asset recognition, lease liability, and payment schedule.
- **AssetImpairment**: IAS 36 impairment test record comparing carrying amount to recoverable amount.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 6 frontend pages with runtime crashes (ProjectDetails, Timesheets, ProjectRisks, AssetManagement, and 2 others with wrong imports) load without JavaScript errors on first render.
- **SC-002**: All backend endpoints that currently produce SQL errors (task dependencies, contract KPIs, impairment test, retainer invoices) return valid responses with correct data.
- **SC-003**: 100% of monetary fields across Projects, Contracts, and Assets schemas use `Decimal` type — zero `float` usage for money.
- **SC-004**: Users creating contracts with validation errors (duplicate number, invalid dates) receive the correct 4xx error code and message, not a 500 Internal Server Error.
- **SC-005**: Assets created with any depreciation method (straight-line, declining balance, sum-of-years, units-of-production) have persisted depreciation schedules that can be posted to the GL.
- **SC-006**: The Gantt chart correctly highlights actual weekend days (Saturday/Sunday) regardless of the project's start date.
- **SC-007**: All error conditions across frontend pages display user-visible feedback (toast notifications) rather than only logging to console.
- **SC-008**: Document deletion validates file paths are within the uploads directory, preventing path traversal.
- **SC-009**: Contract listing with 50+ records completes using batched queries (no N+1), measurable by query count.
- **SC-010**: Lease contracts have IFRS 16-compliant ROU depreciation schedules generated on creation.

---

## Assumptions

- The `company_users` table is the correct FK target for all user references (not the `users` table, which may be a separate auth table).
- The `employees` table is the correct FK target for task assignments (`assigned_to`), while `company_users` is correct for timesheet `employee_id` — this dual mapping is by design, but the JOIN conditions need to be consistent.
- The application uses Bootstrap (not Tailwind CSS) as its CSS framework — Tailwind classes in AssetManagement.jsx are accidental.
- The `projectsAPI` service file defines `getTasks` (not `listTasks`) as the method to fetch project tasks.
- Asset API responses use `code` and `name` as field names (based on the `assets` table column names) — frontend pages using `asset_code` or `asset_name` are wrong.
- The `customers` table does not exist as a standalone table — customer data is in the `parties` table.
- The existing `gl_create_journal_entry` service accepts `Decimal` values for `exchange_rate` and monetary amounts.
- IFRS 16 and IAS 16/36 compliance is a requirement for this ERP system based on the existing partial implementations.
- Route ordering fixes will not change any API URL paths — only the definition order in the router file.
- The `ContractAmendment` model exists elsewhere in the codebase and its schema needs to be formalized.
