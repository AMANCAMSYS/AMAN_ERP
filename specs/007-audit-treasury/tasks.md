# Tasks: audit-treasury — الخزينة والبنوك

**Input**: Design documents from `/specs/007-audit-treasury/`
**Prerequisites**: plan.md, spec.md, research.md (R-001–R-010), data-model.md (9 entities), contracts/treasury-api.md, quickstart.md

**Tests**: Not explicitly requested — test tasks omitted.

**Organization**: Tasks grouped by user story. 8 user stories mapped from spec.md (US1–US8).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Maps to user story (US1–US8)
- Exact file paths included in all descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database migration and schema changes required by all user stories

- [x] T001 Create Alembic migration for all audit-treasury schema changes per data-model.md: ALTER treasury_accounts.current_balance to NUMERIC(20,4), ADD allow_overdraft BOOLEAN; ADD exchange_rate/currency to treasury_transactions; ADD exchange_rate, re_presentation_date, re_presentation_count, re_presentation_journal_id to checks_receivable and checks_payable; ADD exchange_rate to notes_receivable and notes_payable — in backend/alembic/versions/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Model updates and shared utilities that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T002 [P] Fix TreasuryAccount model: change current_balance from Float to Numeric(20,4) with Decimal type annotation, add allow_overdraft = Column(Boolean, nullable=True) in backend/models/domain_models/core_business.py (R-010, R-004)
- [x] T003 [P] Add exchange_rate Column(Numeric(18,6), default=1.0) and currency Column(String(3)) to TreasuryTransaction model in backend/models/domain_models/finance_treasury_tax.py (R-009)
- [x] T004 [P] Add exchange_rate, re_presentation_date, re_presentation_count, re_presentation_journal_id columns to CheckReceivable and CheckPayable models; add exchange_rate to NoteReceivable and NotePayable models in backend/models/domain_models/operations_financial_support.py (R-003, R-009)
- [x] T005 [P] Create ensure_treasury_gl_accounts() utility that auto-creates missing GL accounts (1205, 2105, 1210, 2110) under correct parents with audit logging in backend/utils/treasury_gl.py (R-005)

**Checkpoint**: All models updated, migration ready, utility available. User story implementation can begin.

---

## Phase 3: User Story 1 — Treasury Account Management & GL Integrity (Priority: P1) 🎯 MVP

**Goal**: Treasury accounts correctly linked to GL, opening balances respect fiscal locks, overdraft policy configurable per account.

**Independent Test**: Create a treasury account with opening balance → verify GL account auto-created → verify journal entry posted → verify balances match → attempt creation in locked period → verify rejection.

### Implementation for User Story 1

- [x] T006 [US1] Add check_fiscal_period_open() call before opening balance GL posting in treasury account creation endpoint in backend/routers/finance/treasury.py (R-008)
- [x] T007 [US1] Add allow_overdraft field handling to create and update treasury account endpoints (accept from request, persist to DB, return in response) in backend/routers/finance/treasury.py (R-004)
- [x] T008 [US1] Integrate ensure_treasury_gl_accounts() call on treasury account creation to auto-create required GL accounts if missing in backend/routers/finance/treasury.py (R-005)
- [x] T009 [US1] Add audit trail logging for GL account linkage changes (before/after gl_account_id) on treasury account update in backend/routers/finance/treasury.py (FR-032)
- [x] T010 [P] [US1] Add allow_overdraft toggle to treasury account create/edit form in frontend/src/pages/Treasury/TreasuryAccountList.jsx

**Checkpoint**: Treasury accounts respect fiscal locks, overdraft policy is configurable, GL auto-creation works. US1 independently testable.

---

## Phase 4: User Story 2 — Expense and Transfer Transactions (Priority: P1)

**Goal**: All treasury mutations follow GL-first ordering, use SELECT FOR UPDATE for concurrency, enforce overdraft policy, and persist exchange rates.

**Independent Test**: Record an expense → verify GL entry created BEFORE balance update → send concurrent expense requests → verify only one succeeds → attempt overdraft on cash account → verify rejection → check exchange_rate stored in transaction record.

### Implementation for User Story 2

- [x] T011 [US2] Fix expense endpoint: reorder to GL-first then balance-update, add SELECT FOR UPDATE on treasury row, add overdraft validation per account policy, persist exchange_rate in transaction record in backend/routers/finance/treasury.py (R-001, R-002, R-004, R-009)
- [x] T012 [US2] Fix transfer endpoint: reorder to GL-first then balance-update, add SELECT FOR UPDATE on both source and target treasury rows, add overdraft validation, persist exchange_rate in transaction record in backend/routers/finance/treasury.py (R-001, R-002, R-004, R-009)
- [x] T013 [P] [US2] Add exchange_rate input field to expense form in frontend/src/pages/Treasury/ExpenseForm.jsx
- [x] T014 [P] [US2] Add exchange_rate input field to transfer form in frontend/src/pages/Treasury/TransferForm.jsx

**Checkpoint**: Expense and transfer operations are concurrency-safe, GL-consistent, and exchange rates are tracked. US2 independently testable.

---

## Phase 5: User Story 3 — Checks Receivable Lifecycle (Priority: P1)

**Goal**: Full check receivable lifecycle including re-presentation (bounced → pending), duplicate detection, concurrency safety, and exchange rate tracking.

**Independent Test**: Create a check receivable → verify GL entry (Dr. 1205 / Cr. AR) → collect it → verify GL and treasury balance → bounce it → verify reversal GL → re-present it → verify status returns to pending with new GL entry and incremented re_presentation_count.

### Implementation for User Story 3

- [x] T015 [US3] Add duplicate check number warning: query existing checks by check_number + branch_id before creation, return 409 with existing check details if found in backend/routers/finance/checks.py (R-007)
- [x] T016 [US3] Integrate ensure_treasury_gl_accounts() call in check receivable creation to auto-create 1205 if missing in backend/routers/finance/checks.py (R-005)
- [x] T017 [US3] Add SELECT FOR UPDATE on check receivable row in collect and bounce endpoints to prevent concurrent state transitions in backend/routers/finance/checks.py (R-002)
- [x] T018 [US3] Persist exchange_rate from request body on check receivable creation in backend/routers/finance/checks.py (R-009)
- [x] T019 [US3] Add POST /checks/receivable/{id}/represent endpoint: validate status=bounced, lock row FOR UPDATE, post GL entry (Dr. 1205 / Cr. AR), reset status to pending, set re_presentation_date, increment re_presentation_count, store re_presentation_journal_id in backend/routers/finance/checks.py (R-003)
- [x] T020 [P] [US3] Add "Re-present" action button for bounced checks in ChecksReceivable page, calling POST /checks/receivable/{id}/represent in frontend/src/pages/Treasury/ChecksReceivable.jsx

**Checkpoint**: Checks receivable lifecycle complete with re-presentation, duplicate warning, and concurrency safety. US3 independently testable.

---

## Phase 6: User Story 4 — Checks Payable Lifecycle (Priority: P2)

**Goal**: Full check payable lifecycle including re-presentation (bounced → issued), duplicate detection, concurrency safety, and exchange rate tracking.

**Independent Test**: Create a check payable → verify GL entry (Dr. AP / Cr. 2105) → clear it → verify GL and treasury balance → bounce a different check → re-present it → verify status returns to issued.

### Implementation for User Story 4

- [x] T021 [US4] Add duplicate check number warning on check payable creation: query existing by check_number + branch_id, return 409 if found in backend/routers/finance/checks.py (R-007)
- [x] T022 [US4] Add SELECT FOR UPDATE on check payable row in clear and bounce endpoints in backend/routers/finance/checks.py (R-002)
- [x] T023 [US4] Persist exchange_rate from request body on check payable creation in backend/routers/finance/checks.py (R-009)
- [x] T024 [US4] Add POST /checks/payable/{id}/represent endpoint: validate status=bounced, lock row FOR UPDATE, post GL entry (Dr. AP / Cr. 2105), reset status to issued, set re_presentation_date, increment re_presentation_count in backend/routers/finance/checks.py (R-003)
- [x] T025 [P] [US4] Add "Re-present" action button for bounced checks in ChecksPayable page, calling POST /checks/payable/{id}/represent in frontend/src/pages/Treasury/ChecksPayable.jsx

**Checkpoint**: Checks payable lifecycle mirrors receivable with full re-presentation support. US4 independently testable.

---

## Phase 7: User Story 5 — Notes Receivable & Payable Lifecycle (Priority: P2)

**Goal**: Notes lifecycle with concurrency safety, exchange rate tracking, and GL account auto-creation. Protest remains terminal (no re-presentation).

**Independent Test**: Create a note receivable → verify GL entry (Dr. 1210 / Cr. AR) → collect at maturity → verify GL and treasury balance → create another note → protest it → verify protest is terminal and reversal GL is posted.

### Implementation for User Story 5

- [x] T026 [US5] Integrate ensure_treasury_gl_accounts() call in note receivable and payable creation to auto-create 1210/2110 if missing in backend/routers/finance/notes.py (R-005)
- [x] T027 [US5] Add SELECT FOR UPDATE on note row in collect, pay, and protest endpoints to prevent concurrent state transitions in backend/routers/finance/notes.py (R-002)
- [x] T028 [US5] Persist exchange_rate from request body on note receivable and payable creation in backend/routers/finance/notes.py (R-009)

**Checkpoint**: Notes lifecycle is concurrency-safe with exchange rate tracking. Protest confirmed terminal. US5 independently testable.

---

## Phase 8: User Story 6 — Bank Reconciliation (Priority: P2)

**Goal**: Reconciliation auto-match respects branch isolation, finalization uses configurable tolerance, tolerance seeded in company settings.

**Independent Test**: Import a bank statement CSV → run auto-match with branch_id filter → verify matches don't cross branches → set tolerance to 1.00 → finalize with difference of 0.50 → succeeds → attempt finalize with difference of 2.00 → rejected.

### Implementation for User Story 6

- [x] T029 [US6] Add branch_id filter to auto-match SQL query to prevent cross-branch matching in backend/routers/finance/reconciliation.py (R-002)
- [x] T030 [US6] Read reconciliation_tolerance from company_settings in finalize endpoint; compare abs(difference) <= tolerance; seed default 1.00 on first read if key missing in backend/routers/finance/reconciliation.py (R-006)
- [x] T031 [P] [US6] Display reconciliation tolerance on finalization confirmation dialog in frontend/src/pages/Treasury/ReconciliationForm.jsx

**Checkpoint**: Bank reconciliation respects branch boundaries and configurable tolerance. US6 independently testable.

---

## Phase 9: User Story 7 — Cash Flow Forecasting (Priority: P3)

**Goal**: Verify forecast generation works correctly with Decimal-typed treasury balances after R-010 fix.

**Independent Test**: Generate a 30-day forecast with open AR/AP invoices → verify projected inflows/outflows match invoice amounts → verify running balance computation is accurate.

### Implementation for User Story 7

- [x] T032 [US7] Verify and fix any float-to-Decimal incompatibilities in forecast balance calculations after R-010 model change in backend/services/forecast_service.py and backend/routers/finance/cashflow.py

**Checkpoint**: Cash flow forecasting produces correct projections with Decimal-typed balances. US7 independently testable.

---

## Phase 10: User Story 8 — Treasury Reporting & Dashboards (Priority: P3)

**Goal**: Treasury reports correctly reflect GL balance alongside treasury balance to surface discrepancies, and checks aging groups overdue items accurately.

**Independent Test**: Populate treasury accounts with transactions → view balances report → verify GL balance shown alongside treasury balance → view checks aging report → verify overdue checks are correctly bucketed.

### Implementation for User Story 8

- [x] T033 [US8] Add GL account balance lookup alongside treasury current_balance in balances report endpoint to surface any discrepancy in backend/routers/finance/treasury.py (FR-028)
- [x] T034 [P] [US8] Display GL balance column next to treasury balance in balances report page in frontend/src/pages/Treasury/TreasuryBalancesReport.jsx (FR-028)

**Checkpoint**: Treasury reports surface balance discrepancies. Aging report works correctly. US8 independently testable.

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup across all user stories

- [x] T035 Run quickstart.md verification checklist: confirm all 10 items pass across backend routers
- [x] T036 Verify all treasury router endpoints include log_activity() audit trail calls with correct resource_type and action in backend/routers/finance/treasury.py, checks.py, notes.py (FR-032)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (migration must exist before model changes)
- **User Stories (Phase 3–10)**: All depend on Phase 2 completion
  - US1, US2, US3 are P1 — implement first (sequential, all touch treasury.py and checks.py)
  - US4, US5, US6 are P2 — implement after P1 stories
  - US7, US8 are P3 — implement last
- **Polish (Phase 11)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Independent — treasury account CRUD fixes
- **US2 (P1)**: Independent — expense/transfer fixes (same file as US1 but different endpoints)
- **US3 (P1)**: Independent — checks receivable fixes
- **US4 (P2)**: Independent — checks payable fixes (same file as US3 but different endpoints)
- **US5 (P2)**: Independent — notes fixes (different file from US3/US4)
- **US6 (P2)**: Independent — reconciliation fixes (different file)
- **US7 (P3)**: Depends on US1 (Decimal type change) — verification only
- **US8 (P3)**: Depends on US1/US2 (correct balances) — adds GL balance display

### Parallel Opportunities

Within each user story, tasks marked [P] can run in parallel with backend tasks (frontend work).

**Cross-story parallelism** (after Phase 2):
- US1 + US3 can be worked in parallel (treasury.py vs checks.py)
- US5 + US6 can be worked in parallel (notes.py vs reconciliation.py)
- All frontend [P] tasks can be worked in parallel with each other

---

## Parallel Example: User Story 3

```bash
# Sequential backend tasks (all in checks.py):
T015: Duplicate check warning
T016: ensure_treasury_gl_accounts() integration
T017: SELECT FOR UPDATE on collect/bounce
T018: Persist exchange_rate
T019: Add /represent endpoint

# Parallel frontend task (different file):
T020: Add Re-present button in ChecksReceivable.jsx  # can run alongside T015–T019
```

---

## Implementation Strategy

### MVP First (User Stories 1–3)

1. Complete Phase 1: Setup (migration)
2. Complete Phase 2: Foundational (models + utility)
3. Complete Phase 3: US1 — Treasury account integrity
4. Complete Phase 4: US2 — Expense/transfer GL-first fix
5. Complete Phase 5: US3 — Checks receivable lifecycle
6. **STOP and VALIDATE**: All P1 stories independently testable
7. Deploy/demo if ready — core treasury operations are safe

### Incremental Delivery

1. Setup + Foundational → Schema and models ready
2. US1 → Account management safe → Validate
3. US2 → Expense/transfer safe → Validate
4. US3 → Checks receivable complete → Validate (MVP!)
5. US4 → Checks payable complete → Validate
6. US5 → Notes lifecycle safe → Validate
7. US6 → Reconciliation improved → Validate
8. US7 + US8 → Forecasting/reporting verified → Validate
9. Polish → Full audit complete

### Parallel Team Strategy

With two developers after Phase 2:

- **Developer A**: US1 → US2 → US7 → US8 (treasury.py + reports)
- **Developer B**: US3 → US4 → US5 → US6 (checks.py + notes.py + reconciliation.py)

---

## Notes

- All backend router changes follow the SQL-first `text()` pattern per constitution §VII
- All GL operations use the centralized `create_journal_entry()` from `backend/services/gl_service.py`
- All fiscal period checks use `check_fiscal_period_open()` from `backend/utils/fiscal_lock.py`
- All audit logging uses `log_activity()` from `backend/utils/audit.py`
- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- Commit after each task or logical group
