# Feature Specification: Subscriptions, Services & Expenses — Audit & Bug Fixes

**Feature Branch**: `021-audit-subscriptions-services`  
**Created**: 2026-04-20  
**Status**: Draft  
**Input**: Full code audit of Subscriptions (router 372 lines + service 500 lines), Services (router 635 lines), Expenses (router 948 lines), 13 frontend pages, and database schema. Audit scope includes cross-module integration with GL, invoicing, approval workflow, and tax/VAT systems.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Connect Subscription Billing to GL (Priority: P1)

The subscription service creates invoices when billing customers, but **no journal entries are posted to the General Ledger**. Revenue recognition is completely missing — the system records billing events but the accounting books are unaffected. Deferred revenue (Constitution I) is also unimplemented: annual subscriptions paid upfront have no liability-to-revenue amortization schedule. Additionally, no VAT/tax is applied to subscription invoices despite Saudi 15% VAT requirements (Constitution V).

**Why this priority**: An ERP that bills without booking GL entries produces financial statements that understate revenue and receivables. This is an integrity failure — the trial balance will never reconcile with actual subscription activity. Every subscription invoice generated since go-live is missing from the books.

**Independent Test**: Enroll a customer in a monthly plan, trigger billing, and verify a balanced journal entry is posted (DR Accounts Receivable, CR Revenue/Deferred Revenue) with correct VAT line items.

**Acceptance Scenarios**:

1. **Given** a customer is enrolled in a monthly subscription plan, **When** `generate_subscription_invoice` runs, **Then** a balanced journal entry is posted via `gl_service.py` debiting Accounts Receivable and crediting Subscription Revenue, with a separate VAT payable line at the configured rate.
2. **Given** a customer pays for an annual subscription upfront, **When** the invoice is created, **Then** the GL entry credits Deferred Revenue (not Revenue), and the system records a schedule to amortize the deferred amount to Revenue monthly over the subscription period.
3. **Given** a subscription invoice is generated, **When** the amount is computed, **Then** Saudi 15% VAT is applied to the base amount and the tax breakdown is stored per Constitution XXVI (tax_rate, taxable_base, tax_amount).
4. **Given** `generate_subscription_invoice` is called for a fiscal period that is closed, **When** the invoice creation is attempted, **Then** the operation is rejected with a fiscal period error (not silently created outside the period).

---

### User Story 2 — Fix Float for Money Across All Three Modules (Priority: P1)

All three backend modules use Python `float` for monetary values in violation of Constitution I:
- **Subscriptions router**: `float(body.base_amount)` (line 101), `float(value)` (line 136)
- **Subscription service**: `float(amount)` (line 166), `float(net)` (line 296)
- **Expenses router**: 15+ occurrences of `float()` casts on monetary values throughout the 948-line file
- **Expense frontend**: `parseFloat(formData.amount)` in ExpenseForm.jsx (line 109)

**Why this priority**: Float arithmetic produces rounding errors in financial calculations. Subscription billing, expense totals, and proration calculations that use float can accumulate errors that misstate amounts on invoices, journal entries, and reports. This is a Constitution I critical defect.

**Independent Test**: Create a subscription plan with amount 99.99, enroll a customer, and verify all internal calculations and stored values use exact decimal arithmetic with no floating-point artifacts.

**Acceptance Scenarios**:

1. **Given** a subscription plan is created with base_amount 99.99, **When** the amount is processed in the router and service, **Then** it is handled as `Decimal("99.99")` throughout — no `float()` cast at any point.
2. **Given** a prorated subscription amount is calculated (e.g., 15 days of a 30-day billing cycle at 99.99), **When** the proration runs, **Then** the result uses `Decimal` arithmetic with `ROUND_HALF_UP` (not float division).
3. **Given** an expense with amount 1234.56 is created, **When** the amount is processed in the router, **Then** all 15+ locations that currently use `float()` use `Decimal` instead.
4. **Given** a user enters an expense amount in ExpenseForm.jsx, **When** the form submits, **Then** the amount is sent as a string (not `parseFloat`), and the backend handles it as `Decimal`.

---

### User Story 3 — Eliminate Hard Deletes in Expenses and Services (Priority: P1)

Both the expenses and services routers use `DELETE FROM` SQL statements that permanently destroy records, violating Constitution XVII (SoftDeleteMixin):
- **Expenses**: `DELETE FROM expense_policies` and `DELETE FROM expenses`
- **Services**: 3 locations — `DELETE FROM service_requests`, `DELETE FROM service_request_costs`, `DELETE FROM documents`

**Why this priority**: Hard deletes destroy audit trail and make data unrecoverable. In a financial system, deleting expense records or service costs eliminates evidence needed for audits, compliance, and dispute resolution. This is a Constitution XVII critical defect.

**Independent Test**: Delete an expense policy via the API and verify the record is soft-deleted (`is_deleted = true`) and excluded from normal queries but still present in the database.

**Acceptance Scenarios**:

1. **Given** a user deletes an expense policy, **When** the delete operation executes, **Then** the record is updated with `is_deleted = true` and `updated_at = NOW()` (not physically removed from the table).
2. **Given** a user deletes a service request, **When** the delete operation executes, **Then** the record is soft-deleted and all related costs are also soft-deleted (cascade soft-delete).
3. **Given** soft-deleted records exist, **When** list endpoints query the table, **Then** results are filtered by `is_deleted = false` and soft-deleted records are excluded.
4. **Given** a document is soft-deleted, **When** the physical file exists on disk, **Then** the file is retained (not orphaned or deleted).

---

### User Story 4 — Replace Raw Dict Endpoints with Pydantic Schemas (Priority: P2)

Eight endpoints across two routers accept raw `dict` instead of Pydantic schemas, bypassing all input validation:
- **Expenses (3)**: `create_expense_policy`, `update_expense_policy`, `validate_expense_against_policy`
- **Services (5)**: create/update service request, assign technician, add cost, update document meta

**Why this priority**: Unvalidated input allows malformed data into the database, causes cryptic runtime errors instead of clear 422 responses, and bypasses the Transaction Validation Pipeline (Constitution XXII step 1). Users receive 500 errors instead of actionable validation messages.

**Independent Test**: Submit a create_expense_policy request with missing required fields and verify a 422 response with specific field-level errors.

**Acceptance Scenarios**:

1. **Given** a user creates an expense policy with a missing `policy_name` field, **When** the request is submitted, **Then** the server returns 422 with a validation error specifying the missing field (not 500 Internal Server Error).
2. **Given** a user creates a service request with an invalid `priority` value, **When** the request is submitted, **Then** the server returns 422 with an error indicating valid options (not silently accepted).
3. **Given** all 8 raw-dict endpoints are converted, **When** any of them receive valid input, **Then** the behavior is identical to before the change (no functional regression).

---

### User Story 5 — Add Missing Fiscal Period and Approval Checks (Priority: P2)

Subscription plan creation, enrollment, and plan changes create invoices without checking whether the fiscal period is open (Constitution III). Expense creation (`create_expense`) also imports `check_fiscal_period_open` but never calls it. Subscription operations have no approval workflow integration at all — a high-value annual subscription can be enrolled without any approval.

**Why this priority**: Transactions created outside an open fiscal period corrupt period-end financial statements and break trial balance reconciliation. Missing approval workflow on subscriptions means high-value commitments bypass governance controls (Constitution XIV).

**Independent Test**: Close the current fiscal period, then attempt to enroll a customer in a subscription plan and verify the operation is rejected.

**Acceptance Scenarios**:

1. **Given** the current fiscal period is closed, **When** a subscription enrollment creates an invoice, **Then** the operation is rejected with a fiscal period error before any records are created.
2. **Given** the current fiscal period is closed, **When** an expense is created, **Then** the operation is rejected with a fiscal period error (the imported but unused `check_fiscal_period_open` is actually called).
3. **Given** a subscription enrollment exceeds the approval threshold, **When** the enrollment is submitted, **Then** it is routed through the approval workflow via `try_submit_for_approval` (matching the pattern used by expenses).

---

### User Story 6 — Fix Race Conditions and Concurrency Issues (Priority: P2)

Multiple concurrency vulnerabilities exist:
- **Expenses**: Treasury balance check uses plain `SELECT` without `FOR UPDATE`, allowing two concurrent approvals to both pass the balance check and overdraw the account.
- **Subscriptions**: No concurrency guard on `enroll_customer` — simultaneous requests can double-enroll the same customer in the same plan.
- **Subscriptions**: `generate_subscription_invoice` has no idempotency check — if the billing scheduler runs twice for the same period, duplicate invoices are created.

**Why this priority**: Race conditions in financial operations cause real monetary damage — double charges to customers, treasury overdrafts, and duplicate GL entries. Constitution VI and XXIII require protection against these scenarios.

**Independent Test**: Simulate concurrent enrollment requests for the same customer and plan, and verify only one enrollment succeeds.

**Acceptance Scenarios**:

1. **Given** two concurrent expense approval requests both check the treasury balance, **When** the balance is sufficient for only one, **Then** only one approval succeeds (the SELECT uses `FOR UPDATE` to lock the balance row).
2. **Given** two concurrent enrollment requests for the same customer and plan, **When** both reach the database, **Then** only one enrollment is created (duplicate prevention via unique constraint or `FOR UPDATE` check).
3. **Given** `generate_subscription_invoice` runs for a billing period that already has an invoice, **When** the function executes, **Then** it detects the existing invoice and skips creation (idempotency check on customer + plan + billing period).

---

### User Story 7 — Fix Frontend showToast Signature and Hardcoded Strings (Priority: P2)

Multiple frontend bugs affect user experience:
- **ServiceRequests.jsx**: `showToast` called with wrong signature in 7+ locations — toast type is passed as the i18n fallback parameter, producing incorrect error messages.
- **DocumentManagement.jsx**: Same `showToast` wrong signature (2 locations) plus missing React `key` prop on Fragment in `.map()`.
- **PlanForm.jsx**: Hardcoded `'SAR'` currency (2 locations) — Constitution XVIII violation.
- **SubscriptionHome.jsx**: Hardcoded Arabic fallback strings (2).
- **EnrollmentForm.jsx**: Hardcoded Arabic fallback strings (3).
- **ExpensePolicies.jsx**: Hardcoded `'Error'` strings (2), silent error on policy fetch.
- **ExpenseDetails.jsx**: Raw `toLocaleString()` dates (2 locations), `<a>` instead of `<Link>` for journal entry navigation.

**Why this priority**: Wrong showToast signatures produce confusing error messages for users across the entire Services module. Hardcoded currency and language strings break multi-tenant and multi-locale support. These are systematic UI bugs affecting daily operations.

**Independent Test**: Trigger an error condition in ServiceRequests (e.g., failed status update) and verify the toast shows the correct translated error message with the correct toast type (error/success).

**Acceptance Scenarios**:

1. **Given** a service request operation fails, **When** `showToast` is called, **Then** the correct signature is used: `showToast(translatedMessage, toastType)` — not `showToast(i18nKey, toastType)` where the type is misplaced.
2. **Given** a user views PlanForm.jsx with company currency "USD", **When** the form renders, **Then** the currency displays as "USD" (via `getCurrency()`, not hardcoded 'SAR').
3. **Given** a user switches locale to English, **When** SubscriptionHome and EnrollmentForm render, **Then** all text displays in English through i18n (no hardcoded Arabic fallbacks).
4. **Given** a user views ExpenseDetails, **When** dates are displayed, **Then** they use the project's `formatDate` utility (not raw `toLocaleString()`).
5. **Given** a `.map()` renders document fragments in DocumentManagement.jsx, **When** the list renders, **Then** each Fragment has a unique `key` prop (no React key warnings).

---

### User Story 8 — Fix Database Schema Deficiencies (Priority: P2)

Multiple tables have schema violations:
- **subscription_plans/enrollments/invoices**: `created_by`/`updated_by` are `VARCHAR(100)` instead of `INTEGER REFERENCES company_users(id)` — violates Constitution XVII AuditMixin.
- **expense_policies**: Missing `updated_at` and `updated_by` columns.
- **expenses**: Missing `currency` column, missing `exchange_rate`, missing indexes on `expense_date`/`approval_status`/`branch_id`/`created_by`, no `policy_id` FK to expense_policies.
- **documents**: Missing `is_deleted` (no soft-delete support), `tags` as TEXT instead of JSONB, missing `updated_by`, no indexes on `(related_module, related_id)` or `created_by`.

**Why this priority**: VARCHAR audit columns prevent JOIN operations with `company_users`, break FK integrity, and violate the AuditMixin requirement. Missing indexes degrade query performance as data grows. Missing `is_deleted` on documents makes soft-delete impossible. Missing `currency` on expenses means all expenses are implicitly assumed to be in one currency.

**Independent Test**: Verify all affected tables have the required columns, FKs, and indexes after migration. Verify VARCHAR audit columns are migrated to INTEGER with FK constraints.

**Acceptance Scenarios**:

1. **Given** a subscription plan is created, **When** the `created_by` value references a non-existent user, **Then** the database rejects the insert with a foreign key violation (not silently stored as VARCHAR text).
2. **Given** an expense policy is updated, **When** the record is inspected, **Then** it has `updated_at` and `updated_by` columns populated.
3. **Given** a large number of expenses exist, **When** expenses are queried by `expense_date` range and `approval_status`, **Then** the query uses indexes (not sequential scans).
4. **Given** the documents table is inspected, **When** a soft-delete is attempted, **Then** the `is_deleted` column exists and can be set to `true`.
5. **Given** all schema changes are applied, **When** a fresh company DB is created via `database.py`, **Then** its schema matches an existing company DB that has run all migrations (Constitution XXVIII).

---

### User Story 9 — Fix Services Module Security and Audit Gaps (Priority: P2)

The services router (`routers/services.py`) has multiple security and governance issues:
- **No branch access validation** — any user can access service requests from any branch.
- **No audit logging** — no `log_activity()` calls anywhere in 635 lines.
- **No status transition validation** — a service request can go from `completed` back to `pending`.
- **Internal server file paths leaked** in API responses via `file_path` field.
- **`access_level` stored but never enforced** — documents have access control metadata that is ignored on retrieval.
- **No file download endpoint** — documents can be uploaded but never downloaded.
- **No pagination** on any list endpoint.

**Why this priority**: Missing branch access validation is a Constitution IV violation — users from Branch A can view and modify Branch B's service requests. No audit logging means service request changes are invisible to administrators. Path leakage exposes server internals.

**Independent Test**: Log in as a user with Branch A access, attempt to view a Branch B service request, and verify the request is denied.

**Acceptance Scenarios**:

1. **Given** a user with `allowed_branches = [1]` accesses a service request for branch 2, **When** the request is processed, **Then** it is rejected with a branch access error.
2. **Given** a service request status is changed, **When** the update completes, **Then** a `log_activity()` call records the change with user, timestamp, and before/after values.
3. **Given** a service request is in `completed` status, **When** a user attempts to change it to `pending`, **Then** the transition is rejected (only valid backward transitions are allowed, if any).
4. **Given** a document is retrieved via the API, **When** the response is sent, **Then** the `file_path` field is excluded or replaced with a download URL (no server path leakage).
5. **Given** a user requests the service request list, **When** no pagination params are provided, **Then** results default to 25 rows with pagination metadata (not unbounded).

---

### User Story 10 — Fix Subscription Billing and Proration Bugs (Priority: P3)

Several billing logic bugs exist in `subscription_service.py`:
- **Billing period bug**: `min(start.day, 28)` clips all billing dates to the 28th, losing 1-2 days for months with 30/31 days, causing underbilling.
- **Resume billing bug**: Sets `next_billing_date = CURRENT_DATE`, triggering immediate billing even if the customer has pre-paid through the pause period.
- **JSON via string interpolation**: `proration_details` built via f-string instead of `json.dumps()`, risking malformed JSON.
- **Missing `updated_by`** on `handle_failed_payment` and `check_trial_expirations`.
- **No batch atomicity**: `check_billing_due` commits each invoice individually — partial failures leave inconsistent state.
- **Hardcoded currency**: Invoice created without specifying plan currency (Constitution XVIII).
- **Auto-renewal stored but never executed**: `auto_renewal` flag exists but no code implements actual renewal logic.

**Why this priority**: These bugs cause incorrect billing amounts (underbilling by 1-2 days), unexpected charges on resume, and potential data corruption from malformed JSON. While lower priority than the missing GL integration, they affect billing accuracy for active customers.

**Independent Test**: Create a monthly plan starting on the 31st, bill for February, and verify the billing period accounts for the correct number of days (not clipped to 28th).

**Acceptance Scenarios**:

1. **Given** a monthly plan with billing start on the 31st, **When** February billing is calculated, **Then** the billing period correctly ends on the last day of February (28th/29th) and the next billing date is March 31st (not permanently clipped to the 28th).
2. **Given** a paused subscription is resumed with pre-paid time remaining, **When** the resume operation runs, **Then** `next_billing_date` is set to the end of the pre-paid period (not `CURRENT_DATE`).
3. **Given** proration details are stored, **When** the JSON is generated, **Then** it uses `json.dumps()` (not f-string interpolation) to produce valid JSON.
4. **Given** `handle_failed_payment` updates a subscription, **When** the update runs, **Then** `updated_by` is set to the system user or the triggering user ID.
5. **Given** `check_billing_due` processes 10 subscriptions and the 5th fails, **When** the batch completes, **Then** the first 4 invoices are committed and the error is logged (not all-or-nothing, but each invoice is individually atomic with proper error handling).

---

### User Story 11 — Fix Expense Policy Enforcement and Type Mismatch (Priority: P3)

The expense policy system has a structural disconnect: `validate_expense_against_policy` exists as a standalone API endpoint but is **never enforced server-side during expense creation**. Policies are advisory-only — users can exceed limits without any warning or block. Additionally, expense type enums are mismatched: policies use `travel/meals/supplies/transportation/entertainment` while the expense form uses `materials/labor/services/travel/rent/utilities/salaries`, meaning policy matching will always fail for most categories.

**Why this priority**: Expense policies exist in the system but provide zero governance value because they are not enforced. The type mismatch means even if enforcement were added, policies would not match expenses correctly. This is a governance gap, not a data corruption issue, hence P3.

**Independent Test**: Create an expense policy with a limit of 1000 SAR for travel, then create a travel expense for 5000 SAR, and verify the system warns or blocks based on the policy.

**Acceptance Scenarios**:

1. **Given** an expense policy limits travel expenses to 1000 SAR, **When** a user creates a travel expense for 5000 SAR, **Then** the system validates against the policy during creation and either blocks or warns (not silently accepted).
2. **Given** the expense type list in policies and the expense form, **When** compared, **Then** both use the same canonical set of expense types from a shared enum/constant.
3. **Given** a policy exists for the `travel` expense type, **When** a user creates a `travel` expense, **Then** the policy is correctly matched by type (no mismatch between module and form type lists).

---

### User Story 12 — Fix Expense Frontend State and Navigation Issues (Priority: P3)

- **ExpenseForm.jsx**: Missing `department_id` dropdown and `is_active` toggle that policies reference.
- **ExpenseDetails.jsx**: Uses `<a>` instead of `<Link>` for journal entry navigation, causing full page reloads.
- **EnrollmentDetail.jsx**: Missing `useEffect` dependency (`fetchData` not in deps array), potentially stale data on navigation.
- **PlanList.jsx**: Monetary values displayed without proper currency formatting.
- **EnrollmentForm.jsx**: `customer_id` is a raw number input instead of a searchable customer dropdown.

**Why this priority**: These are UX issues that affect usability but not data integrity. Missing dropdowns make forms harder to use, full page reloads break SPA navigation, and stale data can mislead users.

**Independent Test**: Navigate from ExpenseDetails to a journal entry link and verify the navigation uses React Router (no full page reload).

**Acceptance Scenarios**:

1. **Given** a user views expense details with a linked journal entry, **When** they click the journal entry link, **Then** navigation happens via React Router `<Link>` (no full page reload).
2. **Given** a user views EnrollmentDetail and navigates to a different enrollment, **When** the component updates, **Then** `useEffect` re-fetches data for the new enrollment (dependency array includes `fetchData` or equivalent).
3. **Given** a user views PlanList, **When** plan amounts are displayed, **Then** they use `formatNumber` and `getCurrency()` for proper formatting.
4. **Given** a user creates an enrollment, **When** selecting a customer, **Then** a searchable dropdown is provided (not a raw number input).

---

### Edge Cases

- What happens when `generate_subscription_invoice` is called for a customer whose subscription was cancelled mid-billing-cycle? (Prorated final invoice vs. no invoice)
- What happens when a subscription plan's price is changed while customers are actively enrolled? (Existing enrollments keep old price vs. auto-update)
- What happens when treasury balance is exactly zero and an expense approval is attempted? (Should reject — insufficient funds)
- What happens when two concurrent expense approvals draw from the same treasury account and the combined total exceeds the balance? (Only one should succeed — FOR UPDATE lock)
- What happens when a service request document upload fails mid-write? (File is written to disk before DB insert — orphaned file must be cleaned up)
- What happens when `check_billing_due` encounters a subscription with `next_billing_date = NULL`? (Should skip with warning, not crash)
- What happens when a subscription invoice is generated but VAT rate changes between enrollment and billing? (Use rate at billing date, not enrollment date)
- What happens when `auto_renewal` is true but the customer's payment method has expired? (Flag for manual review, do not silently drop)
- What happens when an expense policy's `max_amount` is set to 0? (Should block all expenses of that type, not be treated as "no limit")

---

## Requirements *(mandatory)*

### Functional Requirements

**A — Critical: Subscription GL Integration**

- **FR-001**: `generate_subscription_invoice` MUST post a balanced journal entry via `gl_service.py` (DR Accounts Receivable, CR Subscription Revenue or Deferred Revenue) for every invoice created
- **FR-002**: Annual/multi-month subscriptions paid upfront MUST credit Deferred Revenue and create a monthly amortization schedule to recognize revenue over the service period (Constitution I: deferred revenue)
- **FR-003**: Subscription invoices MUST include VAT at the configured tax rate (Saudi 15% standard) with tax breakdown stored per Constitution XXVI
- **FR-004**: `check_fiscal_period_open()` MUST be called before creating subscription invoices — reject if period is closed (Constitution III)
- **FR-005**: `validate_je_lines()` MUST be called on every subscription journal entry before persist (Constitution III)

**B — Critical: Float for Money (Constitution I)**

- **FR-006**: All `float()` casts in `routers/finance/subscriptions.py` MUST be replaced with `Decimal` (2 locations: lines 101, 136)
- **FR-007**: All `float()` casts in `services/subscription_service.py` MUST be replaced with `Decimal` (2 locations: lines 166, 296)
- **FR-008**: All `float()` casts in `routers/finance/expenses.py` MUST be replaced with `Decimal` (15+ locations)
- **FR-009**: `parseFloat(formData.amount)` in ExpenseForm.jsx MUST be removed — amount sent as string, backend handles as `Decimal`

**C — Critical: Soft Delete (Constitution XVII)**

- **FR-010**: `DELETE FROM expense_policies` MUST be replaced with `UPDATE SET is_deleted = true`
- **FR-011**: `DELETE FROM expenses` MUST be replaced with `UPDATE SET is_deleted = true`
- **FR-012**: `DELETE FROM service_requests` MUST be replaced with `UPDATE SET is_deleted = true`
- **FR-013**: `DELETE FROM service_request_costs` MUST be replaced with `UPDATE SET is_deleted = true`
- **FR-014**: `DELETE FROM documents` MUST be replaced with `UPDATE SET is_deleted = true`
- **FR-015**: All SELECT queries on soft-deletable tables MUST include `WHERE is_deleted = false` (or equivalent filter)

**D — Input Validation (Constitution XXII)**

- **FR-016**: `create_expense_policy` MUST accept a Pydantic schema (not raw `dict`)
- **FR-017**: `update_expense_policy` MUST accept a Pydantic schema (not raw `dict`)
- **FR-018**: `validate_expense_against_policy` MUST accept a Pydantic schema (not raw `dict`)
- **FR-019**: Service request create/update endpoints MUST accept Pydantic schemas (not raw `dict`)
- **FR-020**: Assign technician, add cost, update document meta endpoints MUST accept Pydantic schemas (not raw `dict`)

**E — Fiscal Period and Approval Workflow**

- **FR-021**: `create_expense` MUST call `check_fiscal_period_open()` before persisting (currently imported but unused)
- **FR-022**: Subscription enrollment MUST support approval workflow via `try_submit_for_approval` for plans exceeding configurable thresholds
- **FR-023**: Raw English error strings in `routers/finance/subscriptions.py` MUST be replaced with `http_error()` pattern

**F — Concurrency and Idempotency**

- **FR-024**: Expense approval treasury balance check MUST use `SELECT ... FOR UPDATE` to prevent concurrent overdraw (Constitution VI)
- **FR-025**: `enroll_customer` MUST prevent duplicate enrollment of the same customer in the same active plan (unique constraint or FOR UPDATE guard)
- **FR-026**: `generate_subscription_invoice` MUST check for existing invoice for the same customer + plan + billing period before creating a new one (idempotency — Constitution XXIII)

**G — Frontend Fixes**

- **FR-027**: All `showToast` calls in ServiceRequests.jsx (7+) and DocumentManagement.jsx (2) MUST use the correct signature: `showToast(translatedMessage, toastType)`
- **FR-028**: Hardcoded `'SAR'` in PlanForm.jsx (2 locations) MUST be replaced with `getCurrency()` (Constitution XVIII)
- **FR-029**: Hardcoded Arabic strings in SubscriptionHome.jsx (2) and EnrollmentForm.jsx (3) MUST use i18n translation keys
- **FR-030**: Hardcoded `'Error'` strings in ExpensePolicies.jsx (2) MUST use i18n translation keys
- **FR-031**: `toLocaleString()` dates in ExpenseDetails.jsx (2 locations) MUST use `formatDate` utility
- **FR-032**: `<a>` tag for journal entry in ExpenseDetails.jsx MUST be replaced with React Router `<Link>`
- **FR-033**: Missing React `key` prop on Fragment in DocumentManagement.jsx `.map()` MUST be added
- **FR-034**: `useEffect` in EnrollmentDetail.jsx MUST include `fetchData` (or equivalent) in dependency array
- **FR-035**: PlanList.jsx monetary values MUST use `formatNumber` and `getCurrency()`

**H — Database Schema Fixes**

- **FR-036**: `subscription_plans`, `subscription_enrollments`, `subscription_invoices` `created_by`/`updated_by` columns MUST be `INTEGER REFERENCES company_users(id)` (not `VARCHAR(100)`)
- **FR-037**: `expense_policies` table MUST have `updated_at TIMESTAMP DEFAULT NOW()` and `updated_by INTEGER REFERENCES company_users(id)` columns
- **FR-038**: `expenses` table MUST have `currency VARCHAR(3)`, `exchange_rate NUMERIC(18,6)`, and `policy_id INTEGER REFERENCES expense_policies(id)` columns
- **FR-039**: `expenses` table MUST have indexes on `expense_date`, `approval_status`, `branch_id`, and `created_by`
- **FR-040**: `documents` table MUST have `is_deleted BOOLEAN DEFAULT false`, `updated_by INTEGER REFERENCES company_users(id)`, and `tags` as JSONB (not TEXT)
- **FR-041**: `documents` table MUST have a composite index on `(related_module, related_id)` and an index on `created_by`
- **FR-042**: All schema changes MUST be applied to both `database.py` CREATE TABLE definitions and Alembic migration scripts (Constitution XXVIII)

**I — Services Module Security**

- **FR-043**: All service request endpoints MUST call `validate_branch_access(current_user, branch_id)` (Constitution IV)
- **FR-044**: All state-changing service request operations MUST call `log_activity()` for audit logging (Constitution XVII)
- **FR-045**: Service request status transitions MUST be validated against a defined state machine (e.g., `completed` cannot revert to `pending`)
- **FR-046**: API responses MUST NOT include internal `file_path` — provide a download URL or endpoint instead
- **FR-047**: A file download endpoint MUST be added for uploaded documents
- **FR-048**: All list endpoints in services router MUST support pagination (default 25, max 100 — Constitution VII/XXV)

**J — Subscription Billing Fixes**

- **FR-049**: Billing period calculation MUST correctly handle months with 29/30/31 days (not clip all dates to 28th)
- **FR-050**: Resume operation MUST set `next_billing_date` to the end of the pre-paid period (not `CURRENT_DATE`)
- **FR-051**: `proration_details` MUST be built via `json.dumps()` (not f-string interpolation)
- **FR-052**: `handle_failed_payment` and `check_trial_expirations` MUST set `updated_by` on records they modify
- **FR-053**: Subscription invoices MUST specify the plan's currency (not hardcoded or omitted — Constitution XVIII)
- **FR-054**: `check_billing_due` MUST handle individual invoice failures gracefully — log error, continue with remaining subscriptions

**K — Expense Policy Integration**

- **FR-055**: `create_expense` MUST call policy validation during creation (not available only as a separate endpoint)
- **FR-056**: Expense types MUST be unified between policies and the expense form — a single canonical set of types shared across both
- **FR-057**: `company_id` fallback to `1` in expenses router MUST be removed — use authenticated user's company_id exclusively
- **FR-058**: `approval_status` field MUST validate against a defined enum (not accept arbitrary strings)

### Key Entities

- **SubscriptionPlan**: Defines a recurring billing plan with base amount, billing interval, trial period, and currency. Serves as the template for customer enrollments.
- **SubscriptionEnrollment**: Links a customer to a plan with start/end dates, status (active/paused/cancelled), next billing date, and auto-renewal flag.
- **SubscriptionInvoice**: Individual billing event for an enrollment, recording amount, billing period, payment status, and linked GL journal entry.
- **DeferredRevenueSchedule**: Amortization schedule for prepaid subscriptions — tracks monthly revenue recognition from deferred revenue liability.
- **Expense**: Individual expense record with amount, type, date, approval status, linked policy, and GL journal entry reference.
- **ExpensePolicy**: Governance rule defining spending limits by expense type, department, or role. Enforced during expense creation.
- **ServiceRequest**: Work order for field service or maintenance, with status lifecycle, assigned technician, costs, and branch association.
- **Document**: File attachment linked to a service request or other entity, with access level, metadata, and soft-delete support.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every subscription invoice generates a balanced GL journal entry — zero subscription billing events without corresponding accounting records.
- **SC-002**: 100% of monetary calculations across subscriptions, expenses, and services use `Decimal` type — zero `float` usage for money.
- **SC-003**: Zero hard `DELETE FROM` statements in expenses and services routers — all deletions are soft-deletes.
- **SC-004**: All 8 previously raw-dict endpoints return 422 on invalid input (not 500) — Pydantic validation active on every endpoint.
- **SC-005**: `check_fiscal_period_open()` is called before every financial transaction creation in subscriptions and expenses — zero transactions posted to closed periods.
- **SC-006**: All `showToast` calls use the correct signature — zero misplaced parameters across Services and Documents pages.
- **SC-007**: Zero hardcoded currency values ('SAR') in subscription frontend — all use `getCurrency()`.
- **SC-008**: All affected database tables have correct column types, FK constraints, and indexes after migration — fresh and migrated schemas are identical (Constitution XXVIII).
- **SC-009**: All service request endpoints enforce branch access validation — zero cross-branch data leakage.
- **SC-010**: Subscription billing correctly handles months with 29/30/31 days — zero date-clipping to the 28th.

---

## Assumptions

- The GL accounts for Subscription Revenue, Deferred Revenue, and Accounts Receivable already exist in the chart of accounts (or will be seeded as part of the subscription module setup). If not, the implementation will create them as configurable settings.
- The `try_submit_for_approval` pattern used in expenses is the correct pattern for subscription approval integration.
- Expense type unification will use the policy types (`travel/meals/supplies/transportation/entertainment`) as the canonical set, potentially extended — the form types that don't overlap (`materials/labor/services/rent/utilities/salaries`) will be added to the unified list.
- The `company_users` table is the correct FK target for all `created_by`/`updated_by` audit columns.
- VARCHAR-to-INTEGER migration for audit columns in subscription tables will handle existing data by looking up user IDs from usernames, or setting to NULL where lookup fails (with a migration log).
- File download endpoint will serve files from the existing upload directory — no change to the file storage strategy.
- Service request status state machine follows the pattern: `pending → in_progress → completed → closed`, with `cancelled` available from any non-closed state.
- Deferred revenue amortization will use straight-line method (equal monthly amounts) unless the plan configuration specifies otherwise.
- The `documents.tags` TEXT-to-JSONB migration will parse existing comma-separated tags into JSON arrays, defaulting to empty array `[]` for NULL or unparseable values.
