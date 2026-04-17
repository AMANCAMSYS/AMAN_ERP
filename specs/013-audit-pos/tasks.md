# Tasks: Audit POS Module — تدقيق وحدة نقاط البيع

**Input**: Design documents from `/specs/013-audit-pos/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api-contracts.md, quickstart.md

**Tests**: Not requested — no test tasks included.

**Organization**: Tasks grouped by user story. 8 user stories (5×P1, 2×P2, 1×P3).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Establish baseline violation counts for verification

- [x] T001 Record baseline grep counts for all success criteria (float in pos.py, parseFloat/console.error/console.log/toLocaleString in frontend, AuditMixin count, fiscal check count)

---

## Phase 2: Foundational — Pydantic Schema Decimal Types (US5, Priority: P1)

**Purpose**: Convert all 23 `: float` fields to `Decimal` in Pydantic schemas — this is the API entry point and BLOCKS backend serialization (US1)

**⚠️ CRITICAL**: No US1 work can begin until this phase is complete

- [x] T002 [US5] Add `from decimal import Decimal` import and convert all 23 float fields to Decimal across 8 schema classes in `backend/schemas/pos.py`

**Checkpoint**: `grep -rn ": float" backend/schemas/pos.py | wc -l` → 0

---

## Phase 3: User Story 1 — Numeric Precision Across All POS Endpoints (Priority: P1) 🎯 MVP

**Goal**: Replace all `float()` serialization in POS router with `str()` to preserve exact decimal values

**Independent Test**: `grep -rn "float(" backend/routers/pos.py | grep -v "#" | grep -v "import" | grep -v "_dec" | wc -l` → 0

### Implementation for User Story 1

- [x] T003 [US1] Replace Category A float() calls (11) with str() in response dictionaries in `backend/routers/pos.py` (lines 167-171, 766, 1108, 1381, 1415)
- [x] T004 [US1] Replace Category B float() calls (5) — remove float() wrapper from SQL parameters, pass Decimal directly in `backend/routers/pos.py` (lines 233-235, 255, 443)
- [x] T005 [US1] Replace Category C float() calls (13) with str() in error messages and log_activity detail strings in `backend/routers/pos.py` (lines 92, 284, 445, 532, 759, 929, 1102, 1377, 1411)
- [x] T006 [US1] Remove Category D float() wrapper on CostingService.consume_layers() quantity parameter in `backend/routers/pos.py` (line 543)

**Checkpoint**: `grep -c "float(" backend/routers/pos.py` → only `_dec()` helper and import remain

---

## Phase 4: User Story 2 — Frontend Sends Correct Data Types (Priority: P1)

**Goal**: Replace `parseFloat()` with `Number()` for local calc / `String()` for API payloads in all POS frontend files

**Independent Test**: `grep -rn "parseFloat" frontend/src/pages/POS/ | wc -l` → 0

### Implementation for User Story 2

- [x] T007 [P] [US2] Replace parseFloat (1 call) with Number()/String() in `frontend/src/pages/POS/POSHome.jsx`
- [x] T008 [P] [US2] Replace parseFloat (2 calls) with Number()/String() in `frontend/src/pages/POS/POSInterface.jsx`
- [x] T009 [P] [US2] Replace parseFloat (2 calls) with Number()/String() in `frontend/src/pages/POS/LoyaltyPrograms.jsx`
- [x] T010 [P] [US2] Replace parseFloat (2 calls) with Number()/String() in `frontend/src/pages/POS/Promotions.jsx`

**Checkpoint**: `grep -rn "parseFloat" frontend/src/pages/POS/ | wc -l` → 0

---

## Phase 5: User Story 3 — User-Visible Error Handling via Toast (Priority: P1)

**Goal**: Replace all `console.error` with `showToast` and remove all `console.log` debug statements from POS frontend

**Independent Test**: `grep -rn "console\.error\|console\.log" frontend/src/pages/POS/ | wc -l` → 0

### Implementation for User Story 3

- [x] T011 [P] [US3] Replace 3 console.error calls with showToast in `frontend/src/pages/POS/POSHome.jsx`
- [x] T012 [P] [US3] Replace 4 console.error calls with showToast in `frontend/src/pages/POS/POSInterface.jsx`
- [x] T013 [P] [US3] Replace 2 console.error calls with showToast and add useToast import in `frontend/src/pages/POS/POSOfflineManager.jsx`
- [x] T014 [P] [US3] Replace 1 console.error call with showToast in `frontend/src/pages/POS/TableManagement.jsx`
- [x] T015 [P] [US3] Replace 1 console.error call with showToast in `frontend/src/pages/POS/KitchenDisplay.jsx`
- [x] T016 [P] [US3] Replace 1 console.error call with showToast in `frontend/src/pages/POS/LoyaltyPrograms.jsx`
- [x] T017 [P] [US3] Replace 1 console.error call with showToast in `frontend/src/pages/POS/Promotions.jsx`
- [x] T018 [P] [US3] Replace 2 console.error with showToast and remove 5 console.log debug statements in `frontend/src/pages/POS/components/HeldOrders.jsx`

**Checkpoint**: `grep -rn "console\.error\|console\.log" frontend/src/pages/POS/ | wc -l` → 0

---

## Phase 6: User Story 4 — Correct Display Formatting with formatNumber (Priority: P1)

**Goal**: Replace all monetary `.toLocaleString()` with `formatNumber()` in POS frontend (keep date `.toLocaleString()` unchanged)

**Independent Test**: `grep -rn "\.toLocaleString()" frontend/src/pages/POS/ | grep -v "// date"` → only date-related calls remain

### Implementation for User Story 4

- [x] T019 [P] [US4] Replace 14 monetary .toLocaleString() calls with formatNumber() and add formatNumber import in `frontend/src/pages/POS/POSInterface.jsx`
- [x] T020 [P] [US4] Replace 1 monetary .toLocaleString() call with formatNumber() and add formatNumber import in `frontend/src/pages/POS/components/POSReturns.jsx`
- [x] T021 [P] [US4] Replace 1 monetary .toLocaleString() call with formatNumber() and add formatNumber import in `frontend/src/pages/POS/components/HeldOrders.jsx`

**Checkpoint**: Monetary `.toLocaleString()` → 0; date `.toLocaleString('ar-SA')` in POSOfflineManager.jsx and ThermalPrintSettings.jsx remain

---

## Phase 7: User Story 6 — Audit Trail Columns on All POS Tables (Priority: P2)

**Goal**: Add AuditMixin to all 16 POS models and add audit column entries in sync_essential_columns()

**Independent Test**: `grep -c "AuditMixin" backend/models/domain_models/sales_pos.py` → 16; all POS tables in sync_essential_columns

### Implementation for User Story 6

- [x] T022 [P] [US6] Add AuditMixin import and inheritance to all 16 models, remove overlapping manual columns (created_at, updated_at, created_by where they conflict) in `backend/models/domain_models/sales_pos.py`
- [x] T023 [P] [US6] Add audit column entries (created_at, updated_at, created_by, updated_by) for all 14 POS tables in `backend/database.py` sync_essential_columns()

**Checkpoint**: All 16 models inherit AuditMixin; `sync_essential_columns()` covers all POS tables

---

## Phase 8: User Story 7 — Fiscal Period Validation on GL-Posting Endpoints (Priority: P2)

**Goal**: Add `check_fiscal_period_open()` to `close_session` and `create_return` before GL entry creation

**Independent Test**: `grep -c "check_fiscal_period_open" backend/routers/pos.py` → 3

### Implementation for User Story 7

- [x] T024 [US7] Add check_fiscal_period_open() call to close_session endpoint before GL entry creation (around line 197-240) in `backend/routers/pos.py`
- [x] T025 [US7] Add check_fiscal_period_open() call to create_return endpoint before GL reversal entry creation (around line 907-1030) in `backend/routers/pos.py`

**Checkpoint**: `grep -c "check_fiscal_period_open" backend/routers/pos.py` → 3 (create_order + close_session + create_return)

---

## Phase 9: User Story 8 — Commission-Free POS Order Verification (Priority: P3)

**Goal**: Verify no commission calculation logic exists in POS flow

**Independent Test**: `grep -rn "commission" backend/routers/pos.py` → 0

- [x] T026 [US8] Verify no commission references exist in POS router via grep on `backend/routers/pos.py` — document result (no code change expected)

**Checkpoint**: `grep -rn "commission" backend/routers/pos.py` → 0 matches confirmed

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Final verification of all success criteria

- [x] T027 Run py_compile on all modified backend files (`backend/routers/pos.py`, `backend/schemas/pos.py`, `backend/models/domain_models/sales_pos.py`, `backend/database.py`) to verify zero syntax errors
- [x] T028 Run `npx vite build` in frontend/ to verify zero compilation errors
- [x] T029 Run all success criteria grep commands (SC-001 through SC-010) and confirm zero violations

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2 / US5)**: No dependencies — BLOCKS Phase 3 (US1)
- **US1 (Phase 3)**: Depends on US5 (Pydantic schemas must be Decimal before router serialization changes)
- **US2 (Phase 4)**: Independent of backend — can start after Phase 1
- **US3 (Phase 5)**: Independent — can start after Phase 1
- **US4 (Phase 6)**: Independent — can start after Phase 1
- **US6 (Phase 7)**: Independent — can start after Phase 1
- **US7 (Phase 8)**: Depends on US1 (same file — pos.py must be stabilized first)
- **US8 (Phase 9)**: Independent — can start after Phase 1
- **Polish (Phase 10)**: Depends on ALL previous phases

### User Story Dependencies

```
US5 (Pydantic Decimal) ──► US1 (float→str) ──► US7 (Fiscal checks)
                                                     │
US2 (parseFloat) ─────────────────────────────────── │ ──► Polish
US3 (console.error) ──────────────────────────────── │ ──►
US4 (formatNumber) ───────────────────────────────── │ ──►
US6 (AuditMixin) ─────────────────────────────────── │ ──►
US8 (Commission) ─────────────────────────────────── │ ──►
```

### Parallel Opportunities

- **After Phase 1**: US2, US3, US4, US5, US6, US8 can all start in parallel (different files)
- **After US5 completes**: US1 can start (same file concern cleared)
- **After US1 completes**: US7 can start (pos.py stabilized)
- **Within US2**: T007, T008, T009, T010 are all [P] (different files)
- **Within US3**: T011–T018 are all [P] (different files)
- **Within US4**: T019, T020, T021 are all [P] (different files)
- **Within US6**: T022, T023 are [P] (different files)

---

## Parallel Example: Maximum Parallelism After Phase 1

```
Worker A: T002 (US5 schemas) → T003-T006 (US1 router) → T024-T025 (US7 fiscal)
Worker B: T007-T010 (US2 parseFloat) → T019-T021 (US4 formatNumber)
Worker C: T011-T018 (US3 console.error) → T026 (US8 commission)
Worker D: T022-T023 (US6 AuditMixin + database.py)
All join: T027-T029 (Polish)
```

---

## Implementation Strategy

### MVP First (US5 + US1 Only)

1. Complete Phase 1: Setup (baseline)
2. Complete Phase 2: US5 (Pydantic Decimal)
3. Complete Phase 3: US1 (float→str)
4. **STOP and VALIDATE**: py_compile passes, grep shows zero float() in response serialization
5. This alone fixes the most critical audit deficiency — financial precision

### Incremental Delivery

1. US5 + US1 → Backend precision fixed → Validate
2. US2 → Frontend sends correct types → Validate
3. US3 → Error visibility for cashiers → Validate
4. US4 → Consistent number display → Validate
5. US6 → Audit trail on all POS tables → Validate
6. US7 → Fiscal integrity enforced → Validate
7. US8 → Commission verified → Validate
8. Polish → All success criteria pass

---

## Notes

- No new files are created — all changes are in-place edits to existing files
- 4 backend files + 9 frontend files affected (2 frontend files are already clean)
- Total: 29 tasks across 10 phases
- US2/US3/US4 overlap on some frontend files (e.g., POSInterface.jsx) but target different code patterns — no merge conflicts if done sequentially within a file
- Date `.toLocaleString('ar-SA')` calls in POSOfflineManager.jsx and ThermalPrintSettings.jsx must be preserved — they are NOT monetary formatting
