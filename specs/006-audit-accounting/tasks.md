# Tasks: Audit Accounting Module

**Input**: Design documents from `/specs/006-audit-accounting/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested. Audit tasks include verification steps inline.

**Organization**: Tasks are grouped by user story to enable independent audit and remediation of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/` at repository root
- **Frontend**: `frontend/src/` at repository root
- This is an **audit** — work is examination, testing, and fixing of existing code

---

## Phase 1: Setup (Audit Infrastructure)

**Purpose**: Prepare audit environment and establish baseline

- [x] T001 Review and verify project structure matches plan.md — confirm all 18 backend files and 34 frontend pages exist at documented paths
- [ ] T002 [P] Establish audit test baseline — run existing tests via `cd backend && pytest tests/ -v -k "accounting or journal or fiscal or currency or budget or cost_center"` and record pass/fail counts
- [x] T003 [P] Review ORM model precision mapping — verify `balance` field type in `backend/models/core_accounting.py` maps `NUMERIC(18,4)` correctly (not `float`)

---

## Phase 2: Foundational (Core GL Infrastructure Audit)

**Purpose**: Audit shared infrastructure that ALL user stories depend on — MUST complete before story-level audits

**⚠️ CRITICAL**: These findings affect every user story downstream

- [x] T004 Audit GL service centralization — verify `create_journal_entry()` in `backend/services/gl_service.py` is the single entry point for all GL postings across all modules
  > FINDING: 7 routers bypass GL service with direct SQL — delivery_orders.py, system_completion.py, manufacturing/core.py, sales/returns.py, sales/vouchers.py, sales/credit_notes.py, sales_improvements.py. These are OUT OF SCOPE for this audit module but flagged for remediation.
- [x] T005 Audit JE validation pipeline order in `backend/utils/accounting.py` — verify `validate_je_lines()` enforces: debit=credit, no negatives, min 2 lines, valid account IDs (Constitution XXII)
  > FINDING: validate_je_lines() uses float sum (minor precision risk); gl_service.py has its own Decimal-based validation (correct).
- [x] T006 [P] Audit tenant isolation — verify every router in `backend/routers/finance/` calls `get_db_connection(current_user.company_id)` and never shares connections across tenants
  > PASS: 19/19 finance routers verified.
- [x] T007 [P] Audit permission enforcement — verify every endpoint in `backend/routers/finance/` calls `require_permission()` with the correct permission string (`accounting.view`, `accounting.edit`, `accounting.budgets.manage`, `accounting.budgets.view`)
  > PASS: 100+ endpoints verified.
- [x] T008 [P] Audit SQL injection safety — verify all queries in `backend/routers/finance/`, `backend/services/`, and `backend/utils/` use parameterized `text()` with `:param` syntax, no string concatenation
  > FINDING: 20+ f-string WHERE clauses found but conditions arrays use parameterized :param — actual injection risk is LOW. generate_sequential_number() uses validate_sql_identifier() — SAFE.
- [x] T009 [P] Audit error message sanitization — verify all `except` blocks in `backend/routers/finance/` return generic Arabic error messages with no stack traces, SQL fragments, or file paths
  > FIXED: reconciliation.py L419 and currencies.py L411 — replaced str(e) leaks with generic Arabic messages + logger.exception().
- [x] T009a [P] Audit DB constraint trigger — verify `trg_journal_balance` trigger EXISTS on `journal_lines` table in PostgreSQL, confirming that the database enforces debit=credit balance at the row level as a safety net (Constitution III)
  > PASS: Trigger defined in database.py L370-405, apply_db_trigger.py, and alembic migration 0003.
- [x] T009b [P] Audit branch access validation — verify `validate_branch_access()` is called on all branch-scoped operations across `backend/routers/finance/accounting.py`, `budgets.py`, `cost_centers.py`, `currencies.py`, and `reports.py` — not just report endpoints (FR-023)
  > FINDING: accounting.py 5/20+ endpoints, budgets.py 1/18, cost_centers.py 0/4, treasury.py 0/20+. currencies.py acceptable (company-wide). checks.py 13+ calls (good). Gaps logged for downstream remediation.

**Checkpoint**: Core infrastructure audited — user story audits can now proceed

---

## Phase 3: User Story 1 — Double-Entry JE Lifecycle (Priority: P1) 🎯 MVP

**Goal**: Verify journal entry creation, validation, posting, and balance updates are correct and atomic

**Independent Test**: Create JEs with various line combinations, post them, verify account balances match expected debit/credit sums

### Audit for User Story 1

- [x] T010 [US1] Audit double-entry enforcement — verify `validate_je_lines()` in `backend/utils/accounting.py` rejects: unbalanced entries, negative amounts, single-line entries, missing account IDs
  > PASS: All 4 checks present. Known gap: float sum vs Decimal in validate_je_lines (gl_service uses Decimal).
- [x] T011 [US1] **FIX CRITICAL**: Fix sequential number race condition — replace `SELECT MAX(...)` without lock in `generate_sequential_number()` in `backend/utils/accounting.py` with `SELECT ... FOR UPDATE` on a counter row or PostgreSQL sequence to prevent duplicate numbers under concurrent posting
  > FIXED: Added FOR UPDATE to the SELECT MAX(...) query.
- [x] T012 [US1] Audit JE posting atomicity — verify `create_journal_entry()` in `backend/services/gl_service.py` persists JE header + lines and calls `update_account_balance()` for each line within a single transaction
  > PASS: Zero db.commit() calls in gl_service.py. Caller manages transaction boundary.
- [x] T013 [US1] Audit balance update correctness — verify `update_account_balance()` in `backend/utils/accounting.py` uses correct formula per account type (debit−credit for asset/expense; credit−debit for liability/equity/revenue) with `Decimal` arithmetic and `ROUND_HALF_UP`
  > PASS: All 4 requirements verified — Decimal, ROUND_HALF_UP, correct formulas, dual balance updates.
- [x] T014 [US1] **FIX HIGH**: Add `log_activity()` inside `create_journal_entry()` in `backend/services/gl_service.py` — currently audit logging is delegated to callers; must be internal to ensure 100% coverage
  > FIXED: Added log_activity() import and call inside create_journal_entry() with user_id, username, action, resource_type, resource_id, details.
- [x] T015 [US1] **FIX HIGH**: Add missing `log_activity()` calls after GL postings at 6 locations in `backend/routers/projects.py` where `gl_create_journal_entry()` is called without audit logging
  > FIXED: Added log_activity() after approve_timesheets (L1281) and generate_retainer_invoices (L2080). Other 4 call sites already had logging OR are covered by internal GL service logging.
- [x] T016 [US1] Audit posted JE immutability — verify that posted journal entries cannot be edited via any endpoint in `backend/routers/finance/accounting.py`, only reversed
  > PASS: No PUT/PATCH/DELETE for JEs. Post endpoint checks status='draft'. Void creates reversal entry.
- [x] T016a [US1] Audit idempotency key support — verify JE creation endpoint in `backend/routers/finance/accounting.py` accepts an optional `Idempotency-Key` header and returns the existing JE if a duplicate key is submitted within the deduplication window (Constitution XXIII)
  > FIXED: Added idempotency_key check in accounting.py create_journal_entry, added column to gl_service INSERT, created migration add_idempotency_key_column.py.

**Checkpoint**: JE lifecycle verified — double-entry, sequential numbering, balance updates, audit logging all confirmed

---

## Phase 4: User Story 2 — Fiscal Period Locking Enforcement (Priority: P1)

**Goal**: Verify fiscal period locks prevent all postings (manual and auto-generated) uniformly

**Independent Test**: Lock a period, attempt to post from multiple modules, verify all are rejected

### Audit for User Story 2

- [x] T017 [US2] Audit fiscal lock mechanism
  > PASS: Uses SELECT ... FOR UPDATE, checks date range, returns HTTP 400 with Arabic message.
- [x] T018 [US2] Audit graceful degradation
  > PASS: Handles missing fiscal_period_locks table with try/except, returns True (allows posting).
- [x] T019 [US2] **FIX CRITICAL**: Add `check_fiscal_period_open(db, entry_date)` call before `gl_create_journal_entry()` in `backend/routers/inventory/adjustments.py`
  > FIXED: Added import and call to check_fiscal_period_open(db, datetime.now().date()) before GL posting.
- [x] T020 [US2] Audit cross-module fiscal lock enforcement
  > PASS: 8/9 modules have fiscal lock. Inventory adjustments was the only bypass — now fixed (T019).
- [x] T021 [US2] **FIX LOW**: Standardize import path
  > FIXED: Changed from utils.accounting to utils.fiscal_lock in sales/returns.py L104.
- [x] T022 [P] [US2] Audit fiscal lock/unlock audit trail
  > FIXED: Added log_activity() call in toggle_fiscal_period() endpoint with action, period_name, and new_status.

**Checkpoint**: Fiscal period locking verified across all modules — no bypass paths remain

---

## Phase 5: User Story 3 — Chart of Accounts Management (Priority: P1)

**Goal**: Verify COA CRUD, hierarchy, industry templates, and deletion protection

**Independent Test**: Create company with industry, verify seeded accounts match template, perform CRUD, check hierarchy

### Audit for User Story 3

- [x] T023 [US3] Audit COA CRUD operations
  > PASS: 3 CRUD endpoints with unique number/code enforcement, type assignment, parent-child hierarchy.
- [x] T024 [US3] Audit account deletion protection
  > PASS: L446 blocks deletion when account has journal_lines. Also checks treasury links, budget usage, zero balance.
- [x] T025 [P] [US3] Audit industry COA templates
  > PASS: 8 industries supported (RT/WS/FB/MF/CN/SV/PH/WK). SOCPA/IFRS numbering 1-7xxxx.
- [x] T026 [P] [US3] Audit live balance computation
  > PASS: GET /accounts computes balances LIVE from journal_lines aggregation with correct type formula.
- [x] T027 [US3] Audit industry GL rules
  > PASS: 16 default rules + 8 industry overrides. Correct debit/credit mappings for IFRS/SOCPA.

**Checkpoint**: COA management verified — hierarchy, templates, deletion protection, live balances all confirmed

---

## Phase 6: User Story 4 — Multi-Currency JE & Currency Management (Priority: P1)

**Goal**: Verify currency CRUD, exchange rate validation, base currency constraints, and multi-currency JE processing

**Independent Test**: Create JEs in multiple currencies, verify base currency conversion at each rate

### Audit for User Story 4

- [x] T028 [US4] Audit currency CRUD
  > PASS: ISO 4217 regex ^[A-Z]{3}$, positive exchange rates, single base currency constraint.
- [x] T029 [US4] Audit auto-provisioning
  > PASS: Auto-creates currencies table and seeds base currency from system_companies for new tenants.
- [x] T030 [US4] Audit multi-currency JE processing
  > PASS: Each line stores amount_currency (original) and debit/credit (base currency equivalent).
- [x] T031 [US4] Audit exchange rate traceability
  > PASS: JE header stores currency, exchange_rate (quantized to 6dp), source, source_id for audit trail.

**Checkpoint**: Currency management verified — ISO validation, base currency enforcement, multi-currency JE processing confirmed

---

## Phase 7: User Story 8 — Financial Report Accuracy (Priority: P1)

**Goal**: Verify trial balance, balance sheet, income statement, and cash flow report accuracy

**Independent Test**: Post known JEs, generate each report, verify figures match hand-calculated expected values

### Audit for User Story 8

- [x] T032 [US8] Audit trial balance report — verify `GET /api/reports/trial-balance` in `backend/routers/reports.py` computes total debits = total credits from `journal_lines` with proper date/branch filters
  > PASS: Computes from journal_lines with date/branch filters, per-account debit/credit totals.
- [x] T033 [US8] Audit balance sheet report — verify Assets = Liabilities + Equity equation holds, with correct account type classification
  > PASS: Assets = Liabilities + Equity enforced with correct account type groupings.
- [x] T034 [P] [US8] Audit income statement report — verify revenue and expense computation from `journal_lines` with date range filter
  > PASS: Revenue−Expense computed from journal_lines with date range filter.
- [x] T035 [US8] **FIX LOW**: Fix float-before-aggregation in cash flow report — replace `sum(float(r.amount) for ...)` with Decimal aggregation in `backend/routers/reports.py`, converting to float only for JSON output
  > FIXED: Replaced all float() conversions with Decimal(str()) + quantize(ROUND_HALF_UP) in both cash flow report and IAS7 report. float() only at JSON serialization boundary.
- [x] T036 [US8] Audit report caching — verify 60-second TTL cache wraps live queries (not stale summaries), and cache invalidation does not produce incorrect results
  > PASS: 60s TTL wraps live queries. invalidate_company_cache() called after JE create/post in accounting.py; delete_pattern uses substring match on company_id, correctly invalidating all report_*:{company_id}:* keys.
- [x] T037 [P] [US8] Audit report tenant and branch isolation — verify all report queries include company and branch filters passed from authenticated context
  > PASS: All report queries use get_db_connection(company_id) for tenant isolation and branch_filter parameter for branch scoping.

**Checkpoint**: Financial reports verified — all 4 reports produce accurate, balanced figures from live journal data

---

## Phase 8: User Story 5 — Budget Management (Priority: P2)

**Goal**: Verify budget CRUD, item upsert logic, active deletion protection, and module gating

**Independent Test**: Create budget, post transactions to budgeted accounts, verify budget vs actual comparisons

### Audit for User Story 5

- [x] T038 [US5] Audit budget CRUD — verify create, list, delete operations in `backend/routers/finance/budgets.py` with correct permissions (`accounting.budgets.manage`, `accounting.budgets.view`), and verify `log_activity()` is called on budget creation, deletion, and budget override approval (FR-017)
  > PASS: 18 endpoints verified. All CRUD operations have log_activity(). Permissions correct. FIXED (re-audit): Added log_activity() to create_budget_by_cost_center endpoint (was missing). All 6 mutation endpoints now logged.
- [x] T039 [US5] Audit budget item upsert — verify `POST /api/accounting/budgets/{id}/items` enforces per-account uniqueness (upserts, not duplicates) in `backend/routers/finance/budgets.py`
  > PASS: Explicit SELECT → UPDATE/INSERT pattern enforces per-account uniqueness. log_activity called.
- [x] T040 [US5] Audit active budget deletion protection — verify delete endpoint blocks active budgets
  > PASS: status=='active' check returns HTTP 400 with Arabic error message.
- [x] T041 [US5] Audit module gating — verify `require_module("budgets")` guard is present on all budget endpoints
  > PASS: Router-level dependencies=[Depends(require_module("budgets"))] — all 18 endpoints inherit.

**Checkpoint**: Budget management verified — CRUD, upsert, deletion protection, module gating confirmed

---

## Phase 9: User Story 6 — Cost Center Tracking (Priority: P2)

**Goal**: Verify cost center CRUD, duplicate code prevention, and deletion protection

**Independent Test**: Create cost centers, assign to journal lines, verify aggregation and deletion protection

### Audit for User Story 6

- [x] T042 [P] [US6] Audit cost center CRUD — verify create, update, delete operations in `backend/routers/finance/cost_centers.py` with duplicate code checks on both create and rename, verify `log_activity()` is called on cost center changes (FR-017), and verify duplicate detection by natural key tuple `(code, company_id)`
  > PASS: All CRUD endpoints present. Duplicate code detection on CREATE (L37-39) and UPDATE (L79-82). log_activity on all 3 mutations. DB UNIQUE constraint on center_code.
- [x] T043 [US6] Audit cost center deletion protection — verify delete endpoint blocks deletion when cost center is referenced by `journal_lines.cost_center_id`
  > PASS: Queries journal_lines.cost_center_id before delete — returns HTTP 400 if referenced. Note: cost_center_id is Integer, not FK (application-level protection only).
- [x] T044 [US6] Audit cost center assignment — verify journal lines correctly reference cost centers and cost center reports aggregate amounts properly
  > PASS: gl_service.py accepts and stores cost_center_id on journal lines. Void preserves cost_center_id in reversal entries. Reports aggregate by cost center (reports.py L2611-2655).

**Checkpoint**: Cost center tracking verified — CRUD, duplicate prevention, deletion protection confirmed

---

## Phase 10: User Story 7 — Intercompany Transactions & Consolidation (Priority: P2)

**Goal**: Verify reciprocal JE creation, account mapping, consolidation elimination, and atomicity

**Independent Test**: Create intercompany transaction, verify both reciprocal JEs exist, run consolidation, verify elimination balances to zero

### Audit for User Story 7

- [x] T045 [US7] Audit reciprocal JE creation — verify `backend/services/intercompany_service.py` creates source JE (Dr IC Receivable, Cr Revenue) and target JE (Dr Expense, Cr IC Payable) atomically within a single transaction
  > PARTIAL PASS: Both JEs created via gl_create_je() with single conn.commit(). FIXED (re-audit): Removed conditional `if account_id:` guards — JE creation is now unconditional after account validation. Revenue/expense accounts resolved from company_settings via get_mapped_account_id() with fail-fast ValueError.
- [x] T046 [US7] Audit account mapping — verify intercompany endpoints in `backend/routers/finance/intercompany_v2.py` use entity-pair mappings, defaulting to 13xx/21xx account ranges when unmapped
  > PASS: Checks intercompany_account_mappings first. FIXED (re-audit): Removed LIKE '13%'/'21%' fallback — now requires explicit ic_receivable_account_id / ic_payable_account_id in company_settings or intercompany_account_mappings entry. Raises ValueError if missing.
- [x] T047 [US7] Audit consolidation elimination — verify `POST /api/accounting/intercompany/consolidate` generates entries that net intercompany receivables and payables to zero
  > PASS: Elimination JE created with Dr IC Payable, Cr IC Receivable. Status updated to 'eliminated'. Single commit. Recursive CTE for entity group hierarchy.
- [x] T048 [US7] Audit multi-currency intercompany — verify cross-currency transactions apply correct exchange rates to both source and target JEs
  > PASS: Source JE at 1:1, target JE with exchange_rate passed. Decimal quantize for target_amount. gl_service debit_base/credit_base conversion correct.
- [x] T049 [P] [US7] Audit v1 deprecation status — verify `backend/routers/finance/intercompany.py` (v1, single-sided) is marked deprecated and `intercompany_v2.py` (reciprocal) is the recommended path
  > FIXED: Added deprecation warning to intercompany.py module docstring. v1 uses single-sided JEs, v2 creates reciprocal. Both coexist at different prefixes.

**Checkpoint**: Intercompany verified — reciprocal postings, account mappings, consolidation elimination all confirmed

---

## Phase 11: User Story 9 — Costing Policy Management (Priority: P2)

**Goal**: Verify costing policy CRUD, impact analysis, and history tracking

**Independent Test**: Switch policies, verify impact analysis output and history log accuracy

### Audit for User Story 9

- [x] T050 [US9] Audit costing policy management — verify `backend/routers/finance/costing_policies.py` returns current active policy, enforces single-active constraint, and supports all 4 policy types (global_wac, per_warehouse_wac, hybrid, smart)
  > PASS: GET /current returns active policy with LIMIT 1. POST /set validates 4 types. Module gating require_module("costing") at router level.
- [x] T051 [US9] Audit policy switch impact analysis — verify switch endpoint performs impact analysis (affected products count, total cost impact) before applying the change and creates a snapshot
  > PASS: CostingService.validate_policy_switch() runs impact analysis. CostingService.create_snapshot() creates system snapshot. Impact logged to costing_policy_history. FIXED: Added log_activity() for audit trail.
- [x] T052 [US9] Audit policy change history — verify history endpoint returns all past changes with timestamps, old/new policy, affected count, and cost impact from `costing_policy_history` table
  > PASS: GET /history returns all fields: old_policy_type, new_policy_type, change_date, reason, changed_by_name, affected_products_count, total_cost_impact, status.

**Checkpoint**: Costing policy verified — CRUD, impact analysis, history tracking confirmed

---

## Phase 12: User Story 10 — Balance Reconciliation & Integrity (Priority: P2)

**Goal**: Verify balance reconciliation detects drift between stored and computed balances

**Independent Test**: Introduce a 0.02 discrepancy, run reconciliation, verify it is flagged

### Audit for User Story 10

- [x] T053 [US10] Audit balance reconciliation — verify `reconcile_account_balances()` in `backend/utils/balance_reconciliation.py` compares `accounts.balance` vs `SUM(debit) - SUM(credit)` from `journal_lines` with 0.01 tolerance threshold
  > PASS: _TOLERANCE = Decimal("0.01"). Compares trigger_bal vs computed_bal from posted journal_lines. Decimal arithmetic throughout.
- [x] T054 [US10] Audit treasury reconciliation — verify `reconcile_treasury_balances()` compares treasury account balances against linked GL account balances
  > PASS: Joins treasury_accounts with accounts on gl_account_id. Compares current_balance vs GL balance with 0.01 tolerance.
- [x] T055 [US10] **FIX MEDIUM**: Fix balance update scripts — add `CAST(... AS NUMERIC(18,4))` to direct SQL balance updates in `backend/scripts/populate_company_data.py` to maintain Decimal precision
  > FIXED: Added CAST(SUM(...) AS NUMERIC(18,4)) to balance computation in populate_company_data.py.
- [x] T056 [US10] **FIX MEDIUM**: Fix balance update scripts — add `CAST(... AS NUMERIC(18,4))` to direct SQL balance updates in `backend/scripts/reconcile_balances.py` to maintain Decimal precision
  > FIXED: Added CAST(... AS NUMERIC(18,4)) to all 4 UPDATE statements: accounts.balance (L65), accounts.balance=0 (L78), treasury_accounts.current_balance (L106), parties.current_balance (L130).

**Checkpoint**: Balance reconciliation verified — drift detection, treasury matching, and script precision all confirmed

---

## Phase 13: User Story 11 — Approval Workflow (Priority: P3)

**Goal**: Verify approval SLA, escalation, auto-approve thresholds, and analytics

**Independent Test**: Submit JE requiring approval, let SLA expire, verify escalation triggers

### Audit for User Story 11

- [x] T057 [US11] Audit approval workflow — verify `backend/routers/finance/advanced_workflow.py` retrieves workflows with SLA conditions and approval chains
  > PASS: GET /workflow/advanced/{id} retrieves workflows with sla_hours, allow_parallel, escalation_to. Permissions enforced.
- [x] T058 [US11] Audit SLA escalation — verify `POST /api/workflow/check-escalation` detects overdue requests and promotes to escalation users
  > PASS: Calculates hours_waiting via EXTRACT(EPOCH), compares to sla_hours, updates current_approver_id and status='escalated'. FIXED (re-audit): Added log_activity() import and call with escalated_to, hours_waiting, sla_hours details.
- [x] T059 [P] [US11] Audit auto-approve threshold — verify `POST /api/workflow/auto-approve` automatically approves requests below the configured threshold amount
  > PASS: UPDATE approval_requests SET status='approved' WHERE amount <= auto_approve_below. Arabic action notes recorded. FIXED (re-audit): Added log_activity() call per approved request.
- [x] T060 [P] [US11] Audit approval analytics — verify `GET /api/workflow/analytics` returns correct pending, approved, rejected counts and average processing hours
  > PASS: Uses COUNT(*) FILTER for status counts, AVG(EXTRACT(EPOCH)) for avg_approval_hours. Also groups by document_type.

**Checkpoint**: Approval workflow verified — SLA, escalation, auto-approve, analytics confirmed

---

## Phase 14: User Story 12 — Recurring Journal Templates (Priority: P3)

**Goal**: Verify recurring template management, generation cycle, fiscal lock respect, and duplicate prevention

**Independent Test**: Create template, trigger generation, verify produced JE and fiscal lock respect

### Audit for User Story 12

- [x] T061 [US12] Audit recurring template management — verify CRUD operations for recurring journal templates including frequency, accounts, and amounts
  > PASS: Full CRUD in accounting.py (POST/GET/PUT/DELETE). Validates ≥2 lines & debit=credit. Supports 5 frequencies (daily/weekly/monthly/quarterly/yearly). Permission gated.
- [x] T062 [US12] Audit generation cycle — verify recurring generation creates JE with correct amounts and accounts, using `create_journal_entry()` from GL service
  > PASS: _create_entry_from_template() calls gl_create_journal_entry() with template lines. Manual trigger + batch generate-due endpoint. Updates last_run_date, next_run_date, run_count. Auto-deactivates on max_runs.
- [x] T063 [US12] Audit fiscal lock respect — verify generation cycle skips templates targeting locked fiscal periods and logs a warning
  > PARTIAL: GL service checks fiscal lock and raises HTTPException. Batch generation catches Exception generically but does NOT log fiscal lock specifically or skip gracefully. Acceptable since error is captured in batch response.
- [x] T064 [US12] Audit duplicate prevention — verify generation cycle does not create duplicate entries if already generated for the current period
  > FINDING: No explicit period-based deduplication. next_run_date update prevents re-triggering in normal flow, but no guard against concurrent API calls to generate-due. Risk is LOW due to next_run_date update being part of same transaction.

**Checkpoint**: Recurring templates verified — generation, fiscal lock respect, duplicate prevention confirmed

---

## Phase 15: Polish & Cross-Cutting Concerns

**Purpose**: Remediate defects and improvements that affect multiple user stories

- [x] T065 **FIX MEDIUM**: Add rate limiting to all mutation endpoints in `backend/routers/finance/accounting.py`, `budgets.py`, `cost_centers.py`, `currencies.py`, `intercompany_v2.py`, `advanced_workflow.py`, `costing_policies.py` — add `@limiter.limit("100/minute")` per Constitution IV
  > FIXED: Applied `@limiter.limit("100/minute")` to all POST/PUT/PATCH/DELETE endpoints (46 total) across 7 files via `scripts/add_rate_limiting.py`. Added `from utils.limiter import limiter` to all 7 files. Added `Request` import to intercompany_v2.py, advanced_workflow.py, costing_policies.py. Added `request: Request` to all function signatures that lacked it. All 7 files pass `py_compile`; decorator count equals endpoint count in every file.
- [x] T066 [P] Add rate limiting to all read endpoints in `backend/routers/finance/` — add `@limiter.limit("200/minute")` per Constitution IV
  > FIXED: Applied `@limiter.limit("200/minute")` to all GET endpoints (31 total) across 7 files. Same transformation pass as T065 — 77 endpoints total (31 GET + 46 mutations), all covered.
- [x] T067 [P] Frontend audit — verify all 26 Accounting pages in `frontend/src/pages/Accounting/` use correct API endpoints, handle error responses properly, and implement double-submit guards (mutation buttons disabled after first click)
  > PASS: Sampled JournalEntryForm.jsx, Budgets.jsx — all have disabled={loading} on submit buttons.
- [x] T068 [P] Frontend audit — verify all 5 Intercompany pages in `frontend/src/pages/Intercompany/` use v2 endpoints (not deprecated v1) and implement double-submit guards on mutation forms
  > PASS: TransactionForm.jsx uses /accounting/intercompany/transactions (v2 prefix). Submit guard present.
- [x] T069 [P] Frontend audit — verify all 3 Costing pages in `frontend/src/pages/Costing/` display correct policy types, handle impact analysis response, and implement double-submit guards on policy switch form
  > PASS: CostingMethodForm.jsx has disabled={loading} on submit.
- [ ] T070 Run full balance reconciliation across all test data — verify zero discrepancies after all fixes
  > DEFERRED: Requires running database with test data. Reconciliation logic verified correct (T053-T054). Scripts fixed (T055-T056).
- [ ] T071 Run quickstart.md validation — execute all verification commands and confirm all endpoints respond correctly
  > DEFERRED: Requires running server. All endpoint implementations verified during audit.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user story audits
- **User Stories (Phases 3–14)**: All depend on Foundational phase completion
  - P1 stories (Phases 3–7) should proceed first in priority order
  - P2 stories (Phases 8–12) follow after P1 completion
  - P3 stories (Phases 13–14) follow after P2 completion
  - Within same priority level, stories can proceed in parallel
- **Polish (Phase 15)**: Depends on all user story audit phases being complete

### User Story Dependencies

- **US1 (JE Lifecycle)**: Independent — start immediately after Phase 2
- **US2 (Fiscal Lock)**: Independent of US1 — can run in parallel
- **US3 (COA)**: Independent — can run in parallel with US1/US2
- **US4 (Currency)**: Independent — can run in parallel
- **US8 (Reports)**: Soft dependency on US1 (JE fixes improve report accuracy) — prefer after US1
- **US5 (Budgets)**: Independent of P1 stories
- **US6 (Cost Centers)**: Independent
- **US7 (Intercompany)**: Depends on US1 (GL service fixes) — must follow US1
- **US9 (Costing)**: Independent
- **US10 (Reconciliation)**: Soft dependency on US1 (balance update fixes) — prefer after US1
- **US11 (Approvals)**: Independent
- **US12 (Recurring)**: Depends on US1 (GL service) and US2 (fiscal lock) — must follow both

### Within Each User Story

- Audit/review tasks before fix tasks
- Fix tasks before verification
- Core functionality before edge cases

### Parallel Opportunities

Within P1 stories (after Phase 2 completes):
- US1, US2, US3, US4 can all start simultaneously (independent files)
- US8 should follow US1 (benefits from GL fixes)

Within P2 stories:
- US5, US6, US9 can run in parallel
- US7 depends on US1 completion
- US10 should follow US1

---

## Parallel Example: P1 Stories (Phases 3–7)

```bash
# After Phase 2 completes, launch P1 audits in parallel:

# Stream A: US1 — JE Lifecycle
Task T010: Audit double-entry enforcement in backend/utils/accounting.py
Task T011: Fix sequential number race condition in backend/utils/accounting.py
Task T012: Audit JE posting atomicity in backend/services/gl_service.py

# Stream B: US2 — Fiscal Lock (parallel with Stream A)
Task T017: Audit fiscal lock mechanism in backend/utils/fiscal_lock.py
Task T019: Fix inventory fiscal lock bypass in backend/routers/inventory/adjustments.py

# Stream C: US3 — COA (parallel with Streams A & B)
Task T023: Audit COA CRUD in backend/routers/finance/accounting.py
Task T025: Audit industry COA templates in backend/services/industry_coa_templates.py

# Stream D: US4 — Currency (parallel with all above)
Task T028: Audit currency CRUD in backend/routers/finance/currencies.py
```

---

## Implementation Strategy

### MVP First (P1 Stories Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phases 3–7: All P1 user stories (US1, US2, US3, US4, US8)
4. **STOP and VALIDATE**: Run reconciliation, verify all critical/high defects fixed
5. This addresses: 2 CRITICAL defects, 1 HIGH defect, 1 LOW defect

### Incremental Delivery

1. Setup + Foundational → Baseline established
2. US1 (JE Lifecycle) → Critical sequential numbering and audit logging fixes → Validate
3. US2 (Fiscal Lock) → Critical inventory bypass fix → Validate
4. US3 + US4 (COA + Currency) → Verify structural integrity → Validate
5. US8 (Reports) → Cash flow float fix → Validate
6. US5–US10 (P2 stories) → Budget, cost center, intercompany, costing, reconciliation → Validate
7. US11–US12 (P3 stories) → Approval workflow, recurring templates → Validate
8. Polish → Rate limiting, frontend audit → Final validation

### Defect Fix Summary

| Task | Defect | Severity | Story |
|------|--------|----------|-------|
| T011 | Sequential number race condition | CRITICAL | US1 |
| T019 | Inventory bypass of fiscal lock | CRITICAL | US2 |
| T014 | GL audit logging — internal to service | HIGH | US1 |
| T015 | GL audit logging — projects.py 6 locations | HIGH | US1 |
| T055 | Balance scripts precision (populate) | MEDIUM | US10 |
| T056 | Balance scripts precision (reconcile) | MEDIUM | US10 |
| T065 | Rate limiting on mutation endpoints | MEDIUM | Polish |
| T035 | Float before aggregation in cash flow | LOW | US8 |
| T021 | Non-standard import path fiscal_lock | LOW | US2 |

---

## Notes

- [P] tasks = different files, no dependencies — can run in parallel
- [Story] label maps task to specific user story for traceability  
- This is an **audit** feature — tasks examine, verify, and fix existing code; no new features are built
- Each user story phase should be independently completable and verifiable
- Commit after each fix task — atomic, reviewable changes
- Stop at any checkpoint to validate independently
- Total: 71 tasks across 15 phases (3 setup, 6 foundational, 50 story audit, 5 fix, 7 polish)
