# Tasks: Subscriptions, Services & Expenses — Audit & Bug Fixes

**Input**: Design documents from `specs/021-audit-subscriptions-services/`
**Prerequisites**: plan.md (required), spec.md (required), data-model.md, contracts/, research.md, quickstart.md

**Tests**: Not requested for this audit.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 2: Foundational — Database Schema & Migration (US8)

**Purpose**: All schema changes must be in place before backend code changes can reference new columns, indexes, and tables. This phase is a prerequisite for US1 (journal_entry_id, deferred_revenue_schedules), US3 (is_deleted columns), US6 (partial unique index), US9 (branch_id on service_requests), and US11 (policy_id on expenses).

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T001 [US8] Update subscription table DDLs (subscription_plans, subscription_enrollments, subscription_invoices) in backend/database.py — change created_by/updated_by from VARCHAR(100) to INTEGER REFERENCES company_users(id), add trial_end_date/cancelled_at/cancellation_reason to enrollments, add journal_entry_id/tax_rate/tax_amount/currency to invoices, add partial unique index on enrollments(customer_id, plan_id) WHERE status IN ('active','paused')
- [x] T002 [US8] Update expense and policy DDLs in backend/database.py — add updated_at/updated_by/is_deleted to expense_policies, add currency/exchange_rate/policy_id/updated_by/is_deleted to expenses, add indexes on expense_date/approval_status/branch_id/created_by
- [x] T003 [US8] Update document and service DDLs in backend/database.py — add is_deleted/updated_by to documents, change tags from TEXT to JSONB DEFAULT '[]', add composite index on (related_module, related_id) and index on created_by, add is_deleted/branch_id/updated_by to service_requests, add is_deleted/updated_by to service_request_costs
- [x] T004 [US8] Create deferred_revenue_schedules table DDL in backend/database.py — columns: id, subscription_invoice_id FK, enrollment_id FK, recognition_date, amount NUMERIC(18,4), journal_entry_id FK, status with CHECK, audit columns as INTEGER FK
- [x] T005 [US8] Create Alembic migration for all schema changes in backend/migrations/versions/fix_sub_svc_exp_schema.py — ALTER subscription tables (VARCHAR→INTEGER with data migration), ADD columns to expense_policies/expenses/documents/service_requests/service_request_costs, CREATE deferred_revenue_schedules, CREATE all indexes, migrate tags TEXT→JSONB

**Checkpoint**: All database schema changes in place. Fresh company DB (database.py) and migrated DB (Alembic) produce identical schemas.

---

## Phase 3: User Story 1 — Connect Subscription Billing to GL (Priority: P1) 🎯 MVP

**Goal**: Every subscription invoice generates a balanced GL journal entry with VAT, and multi-month prepaid subscriptions use deferred revenue with monthly amortization.

**Independent Test**: Enroll a customer in a monthly plan, trigger billing, and verify a balanced journal entry is posted (DR Accounts Receivable, CR Revenue, CR VAT Payable). For annual plans, verify Deferred Revenue is credited and an amortization schedule is created.

### Implementation for User Story 1

- [x] T006 [US1] Add GL journal entry posting, VAT calculation, fiscal period check, and validate_je_lines to generate_subscription_invoice in backend/services/subscription_service.py — import create_journal_entry from services.gl_service, check_fiscal_period_open from utils.fiscal_lock; compute tax at configured rate; post balanced entry (DR Receivable, CR Revenue or Deferred Revenue, CR VAT Payable); use idempotency_key=f"sub-{enrollment_id}-{billing_period_start}"; store journal_entry_id, tax_rate, tax_amount, currency on subscription_invoices record
- [x] T007 [US1] Add deferred revenue schedule creation for annual/multi-month subscriptions in backend/services/subscription_service.py — when billing_frequency is not 'monthly' and payment is upfront, credit Deferred Revenue instead of Revenue; insert rows into deferred_revenue_schedules with straight-line monthly amounts and recognition_date for each month in the subscription period
- [x] T008 [US1] Add fiscal period check to enroll and change_plan endpoints in backend/routers/finance/subscriptions.py — import and call check_fiscal_period_open(db, start_date) before creating invoices; reject with 400 if period is closed

**Checkpoint**: Subscription billing now produces GL entries. Trial balance reflects subscription revenue. Annual plans use deferred revenue.

---

## Phase 4: User Story 2 — Fix Float for Money (Priority: P1)

**Goal**: Zero float usage for monetary values across subscriptions, expenses backend, and expense frontend.

**Independent Test**: Create a subscription plan with amount 99.99, verify all internal calculations use Decimal. Create an expense and verify no float casts.

### Implementation for User Story 2

- [x] T009 [P] [US2] Replace float() with Decimal() in backend/routers/finance/subscriptions.py — 2 locations: float(body.base_amount) at line 101 → Decimal(str(body.base_amount)), float(value) at line 136 → Decimal(str(value)); add from decimal import Decimal if not already imported
- [x] T010 [P] [US2] Replace float() with Decimal() in backend/services/subscription_service.py — 2 locations: float(amount) at line 166 → Decimal(str(amount)), float(net) at line 296 → Decimal(str(net)); ensure all proration arithmetic uses Decimal with ROUND_HALF_UP
- [x] T011 [US2] Replace all float() with Decimal() in backend/routers/finance/expenses.py — 15+ locations throughout the 948-line file; search for all float( occurrences on monetary values and replace with Decimal(str(...)); add from decimal import Decimal if not already imported
- [x] T012 [P] [US2] Remove parseFloat(formData.amount) in frontend/src/pages/Expenses/ExpenseForm.jsx — line 109: change parseFloat(formData.amount) to formData.amount (send as string); backend already handles Decimal conversion

**Checkpoint**: Zero float casts on monetary values in subscriptions, subscription_service, expenses, and expense frontend.

---

## Phase 5: User Story 3 — Eliminate Hard Deletes (Priority: P1)

**Goal**: All DELETE FROM statements replaced with soft-delete (UPDATE SET is_deleted = true). All SELECT queries filter by is_deleted = false.

**Independent Test**: Delete an expense policy and verify the record still exists in DB with is_deleted = true.

### Implementation for User Story 3

- [x] T013 [P] [US3] Replace DELETE FROM with soft-delete in backend/routers/finance/expenses.py — change DELETE FROM expense_policies to UPDATE SET is_deleted=true, updated_at=NOW(), updated_by=user_id; change DELETE FROM expenses to UPDATE SET is_deleted=true; add WHERE is_deleted = false to all SELECT queries on expense_policies and expenses tables
- [x] T014 [US3] Replace DELETE FROM with soft-delete in backend/routers/services.py — change DELETE FROM service_requests to UPDATE SET is_deleted=true (cascade to service_request_costs); change DELETE FROM service_request_costs to UPDATE SET is_deleted=true; change DELETE FROM documents to UPDATE SET is_deleted=true; add WHERE is_deleted = false to all SELECT queries on these tables

**Checkpoint**: Zero hard DELETE FROM statements. All deletions are soft-deletes. Deleted records are excluded from list queries.

---

## Phase 6: User Story 4 — Pydantic Schemas for Raw Dict Endpoints (Priority: P2)

**Goal**: All 8 raw-dict endpoints accept Pydantic schemas with proper validation, returning 422 on invalid input.

**Independent Test**: Submit create_expense_policy with missing name field and verify 422 (not 500).

### Implementation for User Story 4

- [x] T015 [P] [US4] Create Pydantic schemas and apply to expense policy endpoints in backend/routers/finance/expenses.py — define ExpensePolicyCreateSchema (name: str required, expense_type: str required, department_id: Optional[int], daily_limit/monthly_limit/annual_limit: Decimal default 0, requires_receipt/requires_approval: bool, auto_approve_below: Decimal, is_active: bool), ExpensePolicyUpdateSchema (all Optional), ExpenseValidationSchema (expense_type: str, amount: Decimal, department_id: Optional[int]); replace dict parameter with schema in create_expense_policy, update_expense_policy, validate_expense_against_policy
- [x] T016 [US4] Create Pydantic schemas and apply to service request endpoints in backend/routers/services.py — define ServiceRequestCreateSchema (title: str max 255, description: Optional[str], category: str default 'maintenance', priority: Literal['low','medium','high','critical'], customer_id/asset_id/branch_id: Optional[int], estimated_hours/estimated_cost: Optional[Decimal], scheduled_date: Optional[date], location/notes: Optional[str]), ServiceRequestUpdateSchema (all Optional + status), TechnicianAssignSchema (assigned_to: int), ServiceCostSchema (description: str, amount: Decimal, cost_type: Optional[str]), DocumentMetaUpdateSchema (title/description/category: Optional[str], tags: Optional[List[str]], access_level: Optional[Literal]); replace dict with schema in 5 endpoints

**Checkpoint**: All 8 endpoints validate input via Pydantic. Invalid input returns 422 with field-level errors.

---

## Phase 7: User Story 5 — Fiscal Period & Approval Checks (Priority: P2)

**Goal**: Financial transactions check fiscal period before creation. Subscription enrollment integrates with approval workflow.

**Independent Test**: Close fiscal period, attempt to create expense → verify rejection.

### Implementation for User Story 5

- [x] T017 [US5] Wire check_fiscal_period_open() call in create_expense in backend/routers/finance/expenses.py — add check_fiscal_period_open(db, expense.expense_date) before the INSERT; the import already exists but is unused
- [x] T018 [US5] Add try_submit_for_approval to subscription enrollment in backend/routers/finance/subscriptions.py — import try_submit_for_approval from utils.approval_utils; after enrollment creation, call try_submit_for_approval(db, document_type="subscription", document_id=enrollment_id, document_number=f"SUB-{enrollment_id}", amount=plan.base_amount, submitted_by=current_user.id) in a try/except block
- [x] T019 [US5] Replace raw English error strings with http_error() pattern in backend/routers/finance/subscriptions.py — import http_error from utils.i18n; replace all raise HTTPException(status_code=X, detail="English string") with raise HTTPException(**http_error(X, "error_key"))

**Checkpoint**: Fiscal period enforcement active on expenses and subscriptions. Approval workflow triggered for subscription enrollments.

---

## Phase 8: User Story 6 — Concurrency & Idempotency (Priority: P2)

**Goal**: Race conditions eliminated in expense approval and subscription enrollment. Duplicate invoice prevention.

**Independent Test**: Simulate concurrent enrollment for same customer/plan — verify only one succeeds.

### Implementation for User Story 6

- [x] T020 [P] [US6] Add FOR UPDATE to treasury balance check in expense approval in backend/routers/finance/expenses.py — find the SELECT query that checks treasury balance before approval and add FOR UPDATE clause to lock the row during the transaction
- [x] T021 [P] [US6] Add duplicate enrollment prevention in enroll_customer in backend/services/subscription_service.py — before INSERT, SELECT ... FOR UPDATE on subscription_enrollments WHERE customer_id=X AND plan_id=Y AND status IN ('active','paused'); if exists, raise error "Customer already enrolled in this plan"
- [x] T022 [US6] Add idempotency check to generate_subscription_invoice in backend/services/subscription_service.py — before creating invoice, SELECT from subscription_invoices WHERE enrollment_id=X AND billing_period_start=Y; if exists, return existing invoice instead of creating duplicate

**Checkpoint**: Treasury overdrafts prevented. Double-enrollment prevented. Duplicate subscription invoices prevented.

---

## Phase 9: User Story 7 — Frontend showToast & Hardcoded Strings (Priority: P2)

**Goal**: All showToast calls use correct signature. Zero hardcoded currency or language strings.

**Independent Test**: Trigger error in ServiceRequests and verify toast shows error type (red), not info type (blue).

### Implementation for User Story 7

- [x] T023 [P] [US7] Fix showToast signature in frontend/src/pages/Services/ServiceRequests.jsx — 7+ locations: move closing paren of t() before the comma so toast type is second arg to showToast, not fallback to t(); change showToast(err.response?.data?.detail || t('common.error', 'error')) to showToast(err.response?.data?.detail || t('common.error'), 'error'); similarly fix all success toast calls
- [x] T024 [P] [US7] Fix showToast signature (2 locations) and add React key prop to Fragment in .map() in frontend/src/pages/Services/DocumentManagement.jsx — same paren fix as T023; find .map() that renders Fragment without key and add key={item.id} or key={index}
- [x] T025 [P] [US7] Replace hardcoded 'SAR' with getCurrency() in frontend/src/pages/Subscription/PlanForm.jsx — 2 locations: line 19 (currency: 'SAR' default) → currency: getCurrency(), line 40 (plan.currency || 'SAR') → plan.currency || getCurrency(); add import { getCurrency } from '../../utils/auth'
- [x] T026 [P] [US7] Replace hardcoded Arabic fallback strings with i18n keys in frontend/src/pages/Subscription/SubscriptionHome.jsx — find 2 hardcoded Arabic strings and replace with t('subscription.key_name')
- [x] T027 [P] [US7] Replace hardcoded Arabic fallback strings with i18n keys in frontend/src/pages/Subscription/EnrollmentForm.jsx — find 3 hardcoded Arabic strings and replace with t('subscription.key_name')
- [x] T028 [P] [US7] Replace hardcoded 'Error' strings with i18n keys and add error handling for policy fetch in frontend/src/pages/Expenses/ExpensePolicies.jsx — 2 hardcoded 'Error' → t('common.error'); add catch handler for policy fetch that shows toast
- [x] T029 [P] [US7] Replace toLocaleString() with formatDate and replace <a> with React Router <Link> in frontend/src/pages/Expenses/ExpenseDetails.jsx — 2 date locations: import formatDate from utils/dateUtils, replace toLocaleString() calls; replace <a href=...> for journal entry with <Link to=...> from react-router-dom
- [x] T030 [US7] Add new i18n keys to frontend/src/locales/en.json and frontend/src/locales/ar.json — add keys used by T023-T029 for subscription, services, and expenses sections; ensure both en.json and ar.json have matching keys

**Checkpoint**: All showToast calls use correct (message, type) signature. Zero hardcoded 'SAR', Arabic strings, or 'Error' strings. Dates use formatDate. Navigation uses <Link>.

---

## Phase 10: User Story 9 — Services Module Security & Audit (Priority: P2)

**Goal**: Branch access enforced, audit logging active, status transitions validated, file paths hidden, pagination on lists.

**Independent Test**: User with Branch A access attempts to view Branch B service request → denied.

### Implementation for User Story 9

- [x] T031 [US9] Add validate_branch_access and log_activity to all endpoints in backend/routers/services.py — import validate_branch_access from utils.permissions; import log_activity from utils.audit; add Request parameter to all endpoints; call validate_branch_access(current_user, branch_id) on all endpoints that access service_requests; call log_activity(db, user_id=current_user.id, username=current_user.username, action="service_request.{action}", ...) on all state-changing endpoints (create, update, delete, assign, add cost)
- [x] T032 [US9] Add status transition state machine to service request update in backend/routers/services.py — define VALID_TRANSITIONS dict: {'pending': ['assigned','cancelled'], 'assigned': ['in_progress','cancelled'], 'in_progress': ['on_hold','completed','cancelled'], 'on_hold': ['in_progress','cancelled']}; on status change, check current_status → new_status is in VALID_TRANSITIONS; reject invalid transitions with 400 error
- [x] T033 [US9] Add file download endpoint and remove file_path from API responses in backend/routers/services.py — add GET /services/documents/{document_id}/download endpoint using FileResponse; validate access_level against current user; return 404 if file missing; in all document list/detail responses, exclude file_path field and add download_url field pointing to the new endpoint
- [x] T034 [US9] Add pagination to all list endpoints in backend/routers/services.py — add page: int = 1 and per_page: int = 25 query params (max 100); apply LIMIT/OFFSET to queries; return response with items, total, page, per_page, pages fields

**Checkpoint**: Branch access enforced. All changes logged. Invalid status transitions rejected. File paths hidden. Lists paginated.

---

## Phase 11: User Story 10 — Subscription Billing & Proration Bugs (Priority: P3)

**Goal**: Billing dates handle all month lengths correctly. Resume doesn't trigger immediate billing. JSON properly serialized. Batch errors handled gracefully.

**Independent Test**: Plan starting on 31st, bill for February → billing period ends Feb 28/29, next billing March 31.

### Implementation for User Story 10

- [x] T035 [US10] Fix billing period date calculation and resume billing in backend/services/subscription_service.py — replace min(start.day, 28) with calendar-aware logic using calendar.monthrange() to get last day of month; store original billing day on enrollment and use min(original_day, last_day_of_month) for each cycle; fix resume: set next_billing_date to end of pre-paid period (not CURRENT_DATE) by calculating remaining days from pause date
- [x] T036 [US10] Fix proration JSON, updated_by, currency, and batch error handling in backend/services/subscription_service.py — replace f-string proration_details with json.dumps(); add updated_by=user_id (or system user) to handle_failed_payment and check_trial_expirations UPDATE statements; pass plan.currency when creating subscription invoices; wrap check_billing_due individual invoice processing in try/except with logger.error(), continue to next subscription on failure

**Checkpoint**: Billing dates correct for all month lengths. Resume respects pre-paid period. JSON valid. Batch failures logged and non-blocking.

---

## Phase 12: User Story 11 — Expense Policy Enforcement & Type Unification (Priority: P3)

**Goal**: Policies enforced during expense creation. Expense types unified between policies and forms.

**Independent Test**: Create policy with 1000 SAR travel limit, then create 5000 SAR travel expense → system warns/blocks.

### Implementation for User Story 11

- [x] T037 [US11] Add inline policy enforcement to create_expense, remove company_id=1 fallback, validate approval_status enum in backend/routers/finance/expenses.py — define EXPENSE_TYPES = ['travel','meals','supplies','transportation','entertainment','materials','labor','services','rent','utilities','salaries','other']; during create_expense, query expense_policies for matching type/department; if policy found and amount exceeds limit, return warning or block; replace company_id=expense_data.get("company_id", 1) with current_user.company_id; validate approval_status against Literal['pending','approved','rejected','submitted']
- [x] T038 [P] [US11] Unify expense type dropdown options in frontend/src/pages/Expenses/ExpenseForm.jsx and frontend/src/pages/Expenses/ExpensePolicies.jsx — update both files to use the same unified type list matching the backend EXPENSE_TYPES constant; ensure both dropdowns show identical options with proper i18n labels

**Checkpoint**: Policy enforcement active during expense creation. Type lists match across backend and both frontend forms.

---

## Phase 13: User Story 12 — Frontend UX Fixes (Priority: P3)

**Goal**: useEffect dependencies correct, monetary values formatted, customer selection improved.

**Independent Test**: Navigate between enrollments in EnrollmentDetail and verify data refreshes.

### Implementation for User Story 12

- [x] T039 [P] [US12] Fix useEffect dependency array in frontend/src/pages/Subscription/EnrollmentDetail.jsx — add fetchData (or the enrollment ID param) to the useEffect dependency array so data re-fetches when navigating between enrollments
- [x] T040 [P] [US12] Format monetary values with formatNumber and getCurrency in frontend/src/pages/Subscription/PlanList.jsx — import formatNumber from utils/format and getCurrency from utils/auth; wrap plan amount displays with formatNumber(amount) and append getCurrency()
- [x] T041 [P] [US12] Replace raw customer_id number input with customer select dropdown in frontend/src/pages/Subscription/EnrollmentForm.jsx — fetch customers from /api/parties?party_type=customer; render as searchable select/dropdown instead of raw <input type="number">

**Checkpoint**: Data refreshes on navigation. Amounts properly formatted. Customer selection uses dropdown.

---

## Phase 14: Polish & Verification

**Purpose**: Validate all changes across modules

- [x] T042 Verify all modified Python files pass syntax check — run python -m py_compile on backend/services/subscription_service.py, backend/routers/finance/subscriptions.py, backend/routers/finance/expenses.py, backend/routers/services.py, backend/database.py, and the migration file
- [x] T043 Verify Constitution XXVIII schema parity — compare all affected table DDLs in database.py CREATE TABLE against Alembic migration ALTER TABLE for matching column types, defaults, nullability, indexes, and FK constraints; verify a fresh company DB would match a migrated DB

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 2 — US8)**: No dependencies — start immediately. BLOCKS all user stories.
- **US1 (Phase 3)**: Depends on Phase 2 (needs journal_entry_id, deferred_revenue_schedules table)
- **US2 (Phase 4)**: Depends on Phase 2. Can start after US1 for subscription files.
- **US3 (Phase 5)**: Depends on Phase 2 (needs is_deleted columns)
- **US4 (Phase 6)**: Depends on Phase 2. Edits same files as US3 — run after US3.
- **US5 (Phase 7)**: Depends on Phase 2. Edits expenses.py — run after US4.
- **US6 (Phase 8)**: Depends on Phase 2. Edits subscription_service.py — run after US1.
- **US7 (Phase 9)**: No backend dependencies. Frontend-only. Can run in parallel with any backend phase.
- **US9 (Phase 10)**: Depends on Phase 2. Edits services.py — run after US4.
- **US10 (Phase 11)**: Edits subscription_service.py — run after US6.
- **US11 (Phase 12)**: Edits expenses.py — run after US5.
- **US12 (Phase 13)**: Frontend-only. Can run in parallel with backend phases.
- **Polish (Phase 14)**: Depends on all phases complete.

### User Story Dependencies

- **US8 (Schema)**: FOUNDATIONAL — must complete first
- **US1 (GL)**: Depends on US8 only — highest priority, start immediately after schema
- **US2 (Decimal)**: Independent of other stories (different concern per file)
- **US3 (Soft-delete)**: Depends on US8 (is_deleted columns)
- **US4 (Pydantic)**: Independent (adds schemas, no structural deps)
- **US5 (Fiscal/Approval)**: Independent (calls existing utilities)
- **US6 (Concurrency)**: Independent (adds guards/checks)
- **US7 (Frontend strings)**: Fully independent — different file set from backend stories
- **US9 (Services security)**: Independent (adds guards/logging)
- **US10 (Billing bugs)**: Independent (fixes existing logic)
- **US11 (Policy enforcement)**: Independent (wires existing validation)
- **US12 (Frontend UX)**: Fully independent — different file set from backend stories

### Within Each User Story

- Schema changes before code changes
- Backend before frontend (where both exist)
- Core logic before integration points

### Parallel Opportunities

**Backend parallelism** (different files):
- T009 (subscriptions.py), T010 (subscription_service.py), T011 (expenses.py), T012 (ExpenseForm.jsx) — all in US2, all different files
- T013 (expenses.py) and T014 (services.py) — US3, different files
- T015 (expenses.py) and T016 (services.py) — US4, different files
- T020 (expenses.py) and T021/T022 (subscription_service.py) — US6, different files

**Frontend parallelism** (all different files):
- T023-T029 — all US7 tasks edit different frontend files, all parallelizable
- T039-T041 — all US12 tasks edit different frontend files, all parallelizable

**Cross-concern parallelism**:
- All frontend tasks (US7, US12) can run in parallel with all backend tasks

---

## Parallel Example: User Story 7

```text
# All frontend fixes can run in parallel (different files):
T023: Fix showToast in ServiceRequests.jsx
T024: Fix showToast + key in DocumentManagement.jsx
T025: Replace SAR in PlanForm.jsx
T026: i18n in SubscriptionHome.jsx
T027: i18n in EnrollmentForm.jsx
T028: i18n in ExpensePolicies.jsx
T029: formatDate + Link in ExpenseDetails.jsx
# Then sequentially:
T030: Add i18n keys to en.json and ar.json (depends on T023-T029 to know which keys)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 2: Schema & Migration (US8)
2. Complete Phase 3: GL Integration (US1)
3. **STOP and VALIDATE**: Subscription billing produces GL entries with VAT
4. This alone fixes the most critical defect (missing revenue recognition)

### Incremental Delivery

1. Schema + Migration → Foundation ready
2. US1 (GL) → Subscription revenue on the books (MVP!)
3. US2 (Decimal) → Financial precision guaranteed
4. US3 (Soft-delete) → Audit trail preserved
5. US4-US6 → Validation, fiscal checks, concurrency safety
6. US7 → Frontend bugs fixed
7. US8-US9 → Security and governance
8. US10-US12 → Billing accuracy and UX polish

### Sequential Developer Strategy

Since this is an audit with many tasks editing the same files:
1. Complete all backend phases in order (Phase 2 → 3 → 4 → 5 → 6 → 7 → 8 → 10 → 11 → 12)
2. Frontend phases (9, 13) can be interleaved at any point
3. Polish (Phase 14) at the end

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- No tests requested — verification is via syntax check and schema parity
- Several backend files are edited across multiple user stories (expenses.py: 6 stories, subscription_service.py: 5 stories, services.py: 4 stories) — execute in phase order to avoid conflicts
- Frontend tasks are fully independent of backend tasks and can be interleaved
- Commit after each phase completion for clean git history
