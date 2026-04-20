# Feature Specification: Reports & Analytics, Approvals & Workflow — Audit & Bug Fixes

**Feature Branch**: `020-audit-reports-approvals`  
**Created**: 2026-04-20  
**Status**: Draft  
**Input**: Full code audit of Reports (financial reports, KPI dashboards, scheduled reports, analytics — 5 backend files), Approvals (workflow CRUD, approval chain, utilities — 2 backend files), and 17 frontend pages. Audit scope includes cross-module integration with GL, company settings, and notification systems.

---

## Clarifications

### Session 2026-04-20

- Q: Should `recipients` in `scheduled_reports` be migrated from TEXT to JSONB array? → A: Yes, migrate to JSONB array (convert existing data in migration). Likely minimal data since execution was a TODO stub.
- Q: What happens when an approval workflow has an empty `steps` JSONB array? → A: Reject submission with error — workflow is misconfigured. Prevents documents from silently bypassing approval controls.
- Q: How to handle concurrent approval actions on the same request? → A: First-write-wins with optimistic locking. Second action gets "already actioned" error.
- Q: Does scheduled report implementation (FR-039) include email delivery? → A: Generate and store only. Email delivery deferred to a future spec.
- Q: What should KPI calculations return on division by zero? → A: Return 0 (zero). Standard ERP convention for ratio KPIs when denominator is zero.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Fix Approval Utils Runtime Crash (Priority: P1)

The `approval_utils.py` helper function `auto_submit_for_approval` references a nonexistent `approval_workflow_steps` table and treats `min_amount`/`max_amount` as direct columns on `approval_workflows` when they are actually stored inside the `conditions` JSONB column. Any code path that triggers automatic approval submission will crash at runtime with a SQL error.

**Why this priority**: This is a guaranteed runtime crash — the function cannot execute successfully because the table it queries does not exist in the database schema. Any module calling this utility (purchase orders, invoices, etc.) will fail silently or raise an unhandled exception.

**Independent Test**: Trigger the auto-approval flow for any document type that calls `auto_submit_for_approval` and verify it completes without SQL errors, correctly matching workflows by amount thresholds from the `conditions` JSONB.

**Acceptance Scenarios**:

1. **Given** a purchase order exceeding the approval threshold is created, **When** `auto_submit_for_approval` is called, **Then** the function finds the matching workflow by querying `approval_workflows` with steps from the `steps` JSONB column and amount thresholds from the `conditions` JSONB — no reference to a nonexistent `approval_workflow_steps` table.
2. **Given** an approval workflow with `conditions: {"min_amount": 1000, "max_amount": 50000}`, **When** a document with amount 25000 triggers auto-submission, **Then** the workflow is correctly matched based on the JSONB conditions (not nonexistent direct columns).
3. **Given** the `amount` parameter is passed to the function, **When** it is compared against workflow thresholds, **Then** the comparison uses `Decimal` type (not `float`) for monetary precision.

---

### User Story 2 — Fix Non-Functional Frontend Controls in Reports & Approvals (Priority: P1)

Several critical UI controls are completely non-functional: the ReportBuilder export button has no click handler (dead button), the DashboardView date/branch filters capture state but never send values to the API, and the ApprovalsPage View button has no click handler. Additionally, the ApprovalsPage triggers a double-fetch on mount.

**Why this priority**: Users interact with these controls expecting functionality — clicking an export button that does nothing, applying filters that have no effect, or clicking a View button that does nothing are all broken user experiences that undermine trust in the application.

**Independent Test**: Click each affected button/control and verify it performs its intended action. Apply dashboard filters and verify API requests include the filter parameters.

**Acceptance Scenarios**:

1. **Given** a user builds a report in ReportBuilder and clicks the Export button, **When** the click event fires, **Then** the export function executes and produces the report output (not silently ignored).
2. **Given** a user sets date range and branch filters on DashboardView, **When** the filters are applied, **Then** the API request includes the selected date and branch parameters and the dashboard data reflects the filtered results.
3. **Given** a user views the approvals list and clicks the View button on a request, **When** the click event fires, **Then** the approval request details are displayed (not silently ignored).
4. **Given** a user navigates to the ApprovalsPage, **When** the component mounts, **Then** the approval list is fetched exactly once (not twice).

---

### User Story 3 — Fix Constitution I Violations: Float for Money in Reports & Approvals (Priority: P2)

All financial report schema models (`TrialBalanceItem`, `FinancialStatementItem`, etc.) use Python `float` for monetary fields. The `_compute_net_income_from_gl()` helper returns `float`. The `exchange_rate` defaults to `1.0` (float literal) throughout sales queries in reports. In approvals, `WorkflowCreateSchema.min_amount` and `max_amount` use `float`, and `approval_utils.py` accepts `amount` as `float`.

**Why this priority**: Financial reports are the primary output of an ERP system — trial balances, profit & loss, and balance sheets with floating-point rounding errors produce audit findings and misstatements. Approval thresholds compared with float arithmetic may incorrectly approve or reject transactions near boundary amounts.

**Independent Test**: Generate a trial balance and verify all amounts use exact decimal arithmetic with no floating-point artifacts. Create a workflow with a threshold at a boundary amount and verify correct matching.

**Acceptance Scenarios**:

1. **Given** a trial balance is generated with many GL entries, **When** debits and credits are summed, **Then** the total uses exact decimal arithmetic and debits equal credits without floating-point rounding discrepancies.
2. **Given** a profit & loss report includes net income computation, **When** the `_compute_net_income_from_gl()` helper runs, **Then** it returns a `Decimal` value (not `float`).
3. **Given** an approval workflow has `min_amount` of 999.99 and a document has amount 999.99, **When** the threshold comparison runs, **Then** the exact match succeeds without float comparison issues.

---

### User Story 4 — Fix Hardcoded Currency Violations (Priority: P2)

KPIDashboard.jsx hardcodes `'SAR'` as the currency (line 34). RoleDashboard.jsx has a hardcoded `'SAR'` fallback (line 56). This violates Constitution XVIII — the system must use the company's configured currency, not assume Saudi Riyal.

**Why this priority**: Tenants using currencies other than SAR (USD, EUR, EGP, etc.) see incorrect currency symbols throughout KPI and role dashboards, misleading users about the values displayed.

**Independent Test**: Configure a company with a non-SAR currency and verify all KPI and role dashboard pages display the correct currency symbol.

**Acceptance Scenarios**:

1. **Given** a company configured with currency "USD", **When** a user opens the KPI Dashboard, **Then** all monetary KPI values display with the "USD" currency symbol (not "SAR").
2. **Given** a company configured with currency "EUR", **When** a user opens a Role Dashboard, **Then** all monetary metrics display with "EUR" (not "SAR" as fallback).

---

### User Story 5 — Fix Frontend CSS Framework Mismatch and i18n Violations (Priority: P2)

ConsolidationReports.jsx uses Tailwind CSS classes (`text-xl`, `grid grid-3`) in a Bootstrap-based project, resulting in completely unstyled elements. IndustryReport.jsx contains hardcoded Arabic and English strings that bypass the i18n translation system. DashboardEditor.jsx uses hardcoded English labels for widget types. SharedReports.jsx uses raw `toLocaleDateString()` instead of the project's date formatting utility.

**Why this priority**: Unstyled elements and hardcoded language strings degrade the user experience and break the application for users in different locales. All user-facing text must go through i18n for proper RTL/LTR and locale support.

**Independent Test**: Navigate to each affected page in both Arabic and English locales and verify all text is properly translated and all elements are correctly styled.

**Acceptance Scenarios**:

1. **Given** a user opens Consolidation Reports, **When** the page renders, **Then** all elements are styled using the project's CSS framework (Bootstrap), with no unstyled Tailwind classes.
2. **Given** a user switches the application to Arabic locale, **When** Industry Report is viewed, **Then** all labels and headings display translated Arabic text from the i18n system (not hardcoded strings).
3. **Given** a user opens DashboardEditor, **When** widget type options are displayed, **Then** labels are rendered through the translation function (not hardcoded English).
4. **Given** a user opens Shared Reports, **When** dates are displayed, **Then** they use the project's standard date formatting utility (not raw `toLocaleDateString()`).

---

### User Story 6 — Fix Approval Backend Validation and Schema Issues (Priority: P2)

The `create_approval_request` endpoint accepts a raw `dict` instead of a Pydantic schema, bypassing input validation. The `WorkflowCreateSchema` stores `min_amount`/`max_amount` at the schema root but the database stores them inside the `conditions` JSONB column — a structural mismatch. The `approval_workflows` table has conflicting defaults for the `conditions` column (`'{}'` in CREATE vs `'[]'` in ALTER).

**Why this priority**: Unvalidated approval request input can cause data integrity issues and runtime errors. The schema-to-database mismatch means workflow conditions may not be stored or retrieved correctly, potentially allowing unauthorized approvals or blocking valid ones.

**Independent Test**: Create an approval request with missing/invalid fields and verify proper validation errors are returned. Create a workflow with amount conditions and verify they persist and match correctly.

**Acceptance Scenarios**:

1. **Given** a user creates an approval request with missing required fields, **When** the request is submitted, **Then** the server returns 422 with specific validation errors (not a 500 from unhandled dict access).
2. **Given** a user creates a workflow with `min_amount: 5000` and `max_amount: 50000`, **When** the workflow is saved and retrieved, **Then** the amounts are correctly stored in and read from the `conditions` JSONB column.
3. **Given** an existing workflow has no conditions set, **When** the conditions column is read, **Then** the default is a consistent type (either empty object `{}` or empty array `[]`, not conflicting between create and alter paths).

---

### User Story 7 — Fix Database Schema Integrity Issues (Priority: P2)

Multiple tables have missing audit columns, missing foreign key constraints, and inconsistent data types: `shared_reports` lacks `updated_at` and has no FK on `report_id`; `report_templates` lacks `updated_at` and `created_by`; `approval_requests` has `current_approver_id` and `escalated_to` without FK constraints; `approval_actions` has `actioned_by` without FK; `analytics_dashboards` uses `VARCHAR(100)` for `created_by`/`updated_by` instead of integer FK references. Missing indexes on `approval_requests(workflow_id)` and `approval_requests(requested_by)`.

**Why this priority**: Missing FKs allow orphaned references and data integrity violations. Missing audit columns violate the Constitution's AuditMixin requirements. Missing indexes degrade query performance as data grows. Inconsistent types (`VARCHAR` vs `INT` for user references) prevent JOIN operations and complicate queries.

**Independent Test**: Verify all affected tables have the required columns, FKs, and indexes after migration. Verify orphaned reference scenarios are blocked by FK constraints.

**Acceptance Scenarios**:

1. **Given** a shared report is created, **When** the `shared_reports` record is inspected, **Then** it has an `updated_at` timestamp that auto-updates on modification.
2. **Given** an approval action is recorded, **When** the `actioned_by` value references a non-existent user, **Then** the database rejects the insert with a foreign key violation.
3. **Given** a large number of approval requests exist, **When** requests are queried by `workflow_id` or `requested_by`, **Then** the query uses an index (not a sequential scan).
4. **Given** a `report_templates` record is created, **When** the record is inspected, **Then** it has `updated_at` and `created_by` columns populated.

---

### User Story 8 — Fix Report Builder State Bug and Export Error Handling (Priority: P3)

In ReportBuilder.jsx, the `loadReport` function calls `handlePreview()` immediately after `setConfig()` but because React state updates are asynchronous, `handlePreview` executes with the old config. The variable `t` from `useTranslation()` is shadowed by a `.map(t =>` callback, breaking translation calls inside the map. DetailedProfitLoss.jsx `handleExport` lacks try/catch error handling. FXGainLossReport.jsx gain/loss calculation may use undefined values.

**Why this priority**: Report loading shows stale data on first load. Shadowed translation variable causes untranslated text in report columns. Missing error handling leaves users without feedback when exports fail.

**Independent Test**: Load a saved report and verify the preview reflects the loaded config. Trigger an export error and verify the user sees an error message.

**Acceptance Scenarios**:

1. **Given** a user loads a saved report in ReportBuilder, **When** the config is applied, **Then** the preview refreshes with the loaded config (not the previous/stale config).
2. **Given** the ReportBuilder renders column mappings, **When** the `.map()` callback iterates, **Then** the translation function `t()` from `useTranslation()` is not shadowed by the callback parameter.
3. **Given** a user exports a Detailed Profit & Loss report and the API fails, **When** the error occurs, **Then** the user sees an error message (not a silent failure).
4. **Given** an FX Gain/Loss report is generated for a period with no FX transactions, **When** the calculation runs, **Then** it handles undefined/null values gracefully without NaN results.

---

### User Story 9 — Fix Approval Workflow Frontend UX Gaps (Priority: P3)

WorkflowEditor.jsx has no step reordering capability (no drag-and-drop or move up/down buttons). There are no per-step SLA or escalation configuration fields. The `min_amount`/`max_amount` fields are sent at the payload root but the database stores them inside `conditions` JSONB — the frontend and backend may be misaligned. ApprovalsPage.jsx shows no visual approval chain (only text "Step X of Y") and has inconsistent API route prefixes (`/approvals/*` vs `/workflow/*`).

**Why this priority**: Approval workflow configuration is cumbersome without step reordering. Missing SLA fields mean escalation timeouts cannot be configured through the UI. The visual approval chain is important for users to understand where a request sits in the process.

**Independent Test**: Create a multi-step workflow, reorder steps, and verify the order persists. View a pending approval request and verify the approval chain is visually represented.

**Acceptance Scenarios**:

1. **Given** a user creates a workflow with 3 approval steps, **When** the user wants to change the order, **Then** the UI provides a mechanism to reorder steps (move up/down or drag-and-drop).
2. **Given** a user views a pending approval request, **When** the approval details render, **Then** the full approval chain is displayed visually showing completed, current, and pending steps (not just "Step 2 of 3" text).
3. **Given** the ApprovalsPage makes API calls, **When** different operations are performed, **Then** all API routes use a consistent prefix pattern (not mixing `/approvals/*` and `/workflow/*`).

---

### User Story 10 — Fix Scheduled Reports Incomplete Implementation (Priority: P3)

The scheduled reports module has a functional CRUD and scheduler, but the actual report generation and email delivery is a TODO stub (line 453 of `scheduled_reports.py`: "Actual report generation + email would be called here"). The `recipients` field is stored as comma-separated TEXT instead of a structured format, making it difficult to query and validate individual recipients.

**Why this priority**: Users can schedule reports and configure recipients but never actually receive them — the entire delivery pipeline is unimplemented. This is a feature that appears complete in the UI but delivers no value.

**Independent Test**: Schedule a report and verify the report is generated and stored when the schedule triggers.

**Acceptance Scenarios**:

1. **Given** a user schedules a weekly profit & loss report, **When** the scheduled time arrives and the background job runs, **Then** the report is actually generated (not a TODO stub) and the result is stored and accessible from the UI.
2. **Given** a scheduled report has multiple recipients, **When** the recipients are stored, **Then** they are stored as a JSONB array that can be individually queried and validated (not comma-separated text).
3. **Given** a scheduled report generation fails, **When** the error occurs, **Then** the failure is logged and the report status reflects the error (not silently skipped).

---

### Edge Cases

- What happens when a trial balance has zero GL entries for a period? (Empty report vs. error)
- What happens when `_compute_net_income_from_gl()` is called for a period with no revenue or expense accounts? (Should return zero, not null/error)
- What happens when an approval workflow has an empty `steps` JSONB array? → Reject submission with error; workflow is misconfigured.
- What happens when two users take action on the same approval request simultaneously? → First-write-wins with optimistic locking; second action receives "already actioned" error.
- What happens when a dashboard filter selects a branch with no data? (Empty state vs. error)
- What happens when IAS 7 cash flow heuristic classification encounters an account name that matches multiple categories? (Misclassification risk — known limitation, deferred to future spec)
- What happens when `recipients` contains an invalid email in the comma-separated TEXT field? → Migrating to JSONB array; individual recipient validation will be possible.
- What happens when `min_amount` equals `max_amount` in a workflow condition? (Boundary: should it match exact amounts?)
- What happens when a KPI calculation divides by zero (e.g., zero revenue for margin calculations)? → Return 0 (zero), standard ERP convention.

---

## Requirements *(mandatory)*

### Functional Requirements

**A — Critical Runtime Fixes**

- **FR-001**: `approval_utils.py` MUST query workflow steps from the `steps` JSONB column on `approval_workflows` (not from a nonexistent `approval_workflow_steps` table)
- **FR-002**: `approval_utils.py` MUST read `min_amount`/`max_amount` from the `conditions` JSONB column on `approval_workflows` (not as direct table columns)
- **FR-003**: `approval_utils.py` MUST accept and compare `amount` as `Decimal` type (not `float`)
- **FR-004**: ReportBuilder.jsx export button MUST have a functional click handler that triggers the export operation
- **FR-005**: DashboardView.jsx MUST send date range and branch filter values as API request parameters when fetching dashboard data
- **FR-006**: ApprovalsPage.jsx View button MUST have a functional click handler that navigates to or displays the approval request details
- **FR-007**: ApprovalsPage.jsx MUST fetch the approval list exactly once on mount (not double-fetch)

**B — Constitution I: Decimal for Money**

- **FR-008**: All monetary fields in report schema models (`TrialBalanceItem`, `FinancialStatementItem`, etc.) MUST use `Decimal` type (not `float`)
- **FR-009**: `_compute_net_income_from_gl()` in `reports.py` MUST return `Decimal` (not `float`)
- **FR-010**: All `exchange_rate` defaults in `reports.py` sales/purchase queries MUST use `Decimal("1")` (not `1.0` float literal)
- **FR-011**: `WorkflowCreateSchema.min_amount` and `max_amount` MUST use `Decimal` type (not `float`)
- **FR-012**: All KPI monetary calculations in `kpi_service.py` and `industry_kpi_service.py` MUST use `Decimal` arithmetic for monetary values
- **FR-012a**: All KPI ratio calculations MUST return 0 (not error or null) when the denominator is zero (e.g., profit margin with zero revenue, current ratio with zero liabilities)

**C — Constitution XVIII: Currency**

- **FR-013**: KPIDashboard.jsx MUST use the company's configured currency (not hardcoded `'SAR'`)
- **FR-014**: RoleDashboard.jsx MUST use the company's configured currency as the default (not hardcoded `'SAR'` fallback)

**D — Frontend UI Fixes**

- **FR-015**: ConsolidationReports.jsx MUST use Bootstrap CSS classes (not Tailwind classes like `text-xl`, `grid grid-3`)
- **FR-016**: IndustryReport.jsx MUST use the i18n translation system for all user-facing strings (not hardcoded Arabic/English)
- **FR-017**: DashboardEditor.jsx MUST use the i18n translation system for widget type labels (not hardcoded English)
- **FR-018**: SharedReports.jsx MUST use the project's date formatting utility for date display (not raw `toLocaleDateString()`)
- **FR-019**: SharedReports.jsx SHOULD make report names clickable/navigable to view the actual report
- **FR-020**: ReportBuilder.jsx MUST NOT shadow the `t` translation function from `useTranslation()` with `.map()` callback parameters
- **FR-021**: ReportBuilder.jsx `loadReport` MUST ensure the preview uses the newly loaded config (not stale state from the previous render)
- **FR-022**: DetailedProfitLoss.jsx `handleExport` MUST include error handling with user-visible feedback on failure
- **FR-023**: FXGainLossReport.jsx MUST handle undefined/null values in gain/loss calculations without producing NaN

**E — Approval Backend Validation**

- **FR-024**: `create_approval_request` MUST accept a Pydantic schema with validated fields instead of raw `dict`
- **FR-025**: `WorkflowCreateSchema` MUST store `min_amount`/`max_amount` inside the `conditions` JSONB structure to match the database schema (or the backend must map root-level fields into the JSONB on save)
- **FR-026**: `approval_workflows` table MUST have a single consistent default for the `conditions` column (resolve `'{}'` vs `'[]'` conflict — use `'{}'` as the canonical default since conditions contain named fields)
- **FR-026a**: System MUST reject approval request submission if the matched workflow has an empty `steps` array, returning a clear error that the workflow is misconfigured
- **FR-026b**: System MUST use optimistic locking (first-write-wins) on approval actions — if two users act on the same request concurrently, the second action MUST receive an "already actioned" error

**F — Database Schema Integrity**

- **FR-027**: `shared_reports` table MUST have an `updated_at` column with auto-update behavior
- **FR-028**: `report_templates` table MUST have `updated_at` and `created_by` columns
- **FR-029**: `approval_requests.current_approver_id` MUST have a foreign key constraint to `company_users`
- **FR-030**: `approval_requests.escalated_to` MUST have a foreign key constraint to `company_users`
- **FR-031**: `approval_actions.actioned_by` MUST have a foreign key constraint to `company_users`
- **FR-032**: `analytics_dashboards.created_by` and `updated_by` MUST use integer type with FK constraint to `company_users` (not `VARCHAR(100)`)
- **FR-033**: `approval_requests` table MUST have indexes on `workflow_id` and `requested_by` columns
- **FR-034**: All schema changes in `database.py` MUST have corresponding migration scripts

**G — Approval Workflow UX**

- **FR-035**: WorkflowEditor.jsx MUST provide a mechanism to reorder approval steps (move up/down buttons or drag-and-drop)
- **FR-036**: ApprovalsPage.jsx MUST display a visual approval chain showing completed, current, and pending steps
- **FR-037**: ApprovalsPage.jsx MUST use consistent API route prefixes for all approval-related operations
- **FR-038**: WorkflowEditor.jsx MUST correctly map `min_amount`/`max_amount` into the `conditions` object in the API payload (matching the backend's JSONB structure)

**H — Scheduled Reports**

- **FR-039**: `_execute_scheduled_report` MUST implement actual report generation by calling the appropriate report function and storing the result (not remain a TODO stub). Email delivery is out of scope for this audit and deferred to a future spec
- **FR-040**: `recipients` field in `scheduled_reports` MUST be migrated from comma-separated TEXT to JSONB array, with existing data converted in the migration script

### Key Entities

- **Report**: Generated financial statement (trial balance, P&L, balance sheet, cash flow, GL detail) produced from GL journal entries. Has configurable date ranges, branch filters, and export formats (PDF, Excel).
- **ScheduledReport**: Recurring report definition with schedule interval, report type, parameters, and recipient list. Executed by background scheduler.
- **SharedReport**: Report shared with specific users, linked by `report_id` (polymorphic reference to various report types) and `shared_with` user ID.
- **ReportTemplate**: Saved report configuration for reuse. Stores report type, filters, and layout preferences.
- **AnalyticsDashboard**: Custom dashboard with configurable widgets (charts, KPIs, tables). Has role-based access via `access_roles` JSONB.
- **ApprovalWorkflow**: Multi-step approval process definition with document type scope, approval steps stored as JSONB array, and conditions (amount thresholds) stored in JSONB.
- **ApprovalRequest**: Instance of a document submitted for approval, linked to a workflow. Tracks current step, status, and approver chain.
- **ApprovalAction**: Individual approval/rejection/return action taken by an approver at a specific step, with comments and timestamp.
- **KPI**: Calculated business metric derived from GL data and other module data. Organized by role (executive, financial, sales, etc.) and industry.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `auto_submit_for_approval` executes successfully without SQL errors when triggered by any document type — no references to nonexistent tables.
- **SC-002**: All interactive controls on Reports and Approvals pages (export buttons, filter controls, view buttons) perform their intended action when clicked — zero dead/non-functional buttons.
- **SC-003**: 100% of monetary fields across Reports schemas, KPI services, and Approvals schemas use `Decimal` type — zero `float` usage for money.
- **SC-004**: All KPI and role dashboard pages display the company's configured currency — zero hardcoded currency values.
- **SC-005**: All frontend pages use the project's CSS framework (Bootstrap) exclusively — zero Tailwind CSS classes in Reports or Approvals pages.
- **SC-006**: All user-facing strings in Reports and Approvals pages pass through the i18n translation system — zero hardcoded language strings.
- **SC-007**: All database tables in the Reports and Approvals modules have `updated_at` columns where required, and all user reference columns have proper FK constraints.
- **SC-008**: Approval requests submitted with invalid/missing fields receive 422 validation errors (not 500 Internal Server Error).
- **SC-009**: DashboardView filters produce different API responses when different filter values are selected — filters are demonstrably functional.
- **SC-010**: Scheduled report execution produces actual report output when the scheduler triggers — the TODO stub is replaced with working implementation.

---

## Assumptions

- The application uses Bootstrap (not Tailwind CSS) as its CSS framework — Tailwind classes in ConsolidationReports.jsx are accidental.
- The `company_users` table is the correct FK target for all user references in approval and analytics tables.
- Approval workflow steps are intentionally stored as a JSONB array on `approval_workflows.steps` — there is no separate `approval_workflow_steps` table and none should be created; the JSONB approach is by design.
- The `conditions` column on `approval_workflows` should default to an empty JSON object `'{}'` (not an empty array), since conditions contain named fields (`min_amount`, `max_amount`).
- KPI calculations in `kpi_service.py` already return numeric values that can be converted to `Decimal` — no fundamental redesign of the KPI calculation pipeline is needed.
- The existing report generation logic in `reports.py` (trial balance, P&L, etc.) can be called programmatically from the scheduled report executor without requiring HTTP self-calls.
- Company currency is available from the authentication context on the frontend (consistent with how other modules access it per Constitution XVIII).
- The `shared_reports.report_id` polymorphic reference pattern (no FK) is intentional due to multiple report types — the fix is to add documentation/validation, not to add a FK that would reference multiple tables.
- IAS 7 cash flow heuristic classification (account name keyword matching) is a known limitation that will be addressed in a future spec — this audit documents it but does not require a full reclassification engine.
- Delegation, escalation timeout enforcement, and SLA tracking in the approval workflow are enhancement features, not bugs — they are documented but out of scope for this bug-fix audit.
