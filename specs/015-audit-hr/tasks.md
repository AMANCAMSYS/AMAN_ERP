# Tasks: Audit HR Module — تدقيق وحدة الموارد البشرية

**Input**: Design documents from `/specs/015-audit-hr/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Not requested — no test tasks included.

**Organization**: Tasks grouped by user story (10 stories from spec.md). Each story is independently testable after foundational phase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Exact file paths included in all descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create new utility files needed by multiple user stories

- [x] T001 Create PII masking utility with `mask_pii(value, visible_chars=4)` function in `backend/utils/masking.py`
- [x] T002 [P] Add `hr.pii` permission to `PERMISSION_ALIASES` in `backend/utils/permissions.py` — grant to admin, system_admin, manager, hr_admin, payroll_manager roles

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Schema type migration that ALL backend user stories depend on

**⚠️ CRITICAL**: No US1/US4/US5 work can begin until this phase is complete

- [x] T003 Migrate all 31 float fields to Decimal in `backend/schemas/hr.py` — LoanCreate/LoanResponse (amount, monthly_installment, paid_amount), EmployeeCreate/EmployeeUpdate (salary, housing_allowance, transport_allowance, other_allowances, hourly_cost), EmployeeResponse (hourly_cost), PayrollEntryResponse (basic_salary, housing_allowance, transport_allowance, other_allowances, deductions, net_salary, exchange_rate, net_salary_base, gosi_employee_share, gosi_employer_share, overtime_amount, violation_deduction, loan_deduction, salary_components_earning, salary_components_deduction), PayrollPeriodResponse (total_net). Add `from decimal import Decimal`. Use `Decimal("0")` for defaults.

**Checkpoint**: Schema foundation ready — backend story implementation can begin

---

## Phase 3: User Story 1 — Numeric Precision Across All HR/Payroll Endpoints (Priority: P1) 🎯 MVP

**Goal**: All HR API responses serialize monetary values as string Decimals instead of floats; PII fields are masked for unauthorized roles

**Independent Test**: `grep -n "float(" backend/routers/hr/core.py | grep -v "#\|import\|isinstance" | wc -l` → 0; employee API response returns `"salary": "5000.75"` not `5000.75`

### Implementation for User Story 1

- [x] T004 [US1] Replace all 18+ `float()` → `str()` calls in payroll entry and employee response dict construction in `backend/routers/hr/core.py` — lines building response dicts with `float(row.xxx)` change to `str(row.xxx or 0)`
- [x] T005 [US1] Apply PII masking in employee list/detail response construction in `backend/routers/hr/core.py` — check `hr.pii` permission via `get_field_restrictions()`, mask iban, national_id/social_security, gosi_number, passport_number, iqama_number using `mask_pii()` from `utils/masking.py`
- [x] T006 [P] [US1] Replace `float()` → `str()` serialization for monetary fields in WPS preview and saudization responses in `backend/routers/hr_wps_compliance.py`
- [x] T007 [P] [US1] Replace `float()` → `str()` serialization for monetary fields in EOS, overtime, and loan responses in `backend/routers/hr/advanced.py`

**Checkpoint**: All HR API monetary values return as string Decimals. PII is masked. Backend precision audit complete for MVP.

---

## Phase 4: User Story 4 — EOS Gratuity Calculation Precision (Priority: P1)

**Goal**: EOS gratuity calculation uses Decimal throughout with no float boundary conversions

**Independent Test**: `grep -n "float" backend/utils/hr_helpers.py | wc -l` → 0 for function signatures; EOS for 12 years service at 20000 salary returns exactly `Decimal("190000.00")`

### Implementation for User Story 4

- [x] T008 [US4] Migrate `calculate_eos_gratuity()` function signature from float to Decimal inputs/outputs in `backend/utils/hr_helpers.py` — change `total_salary: float` → `total_salary: Decimal`, `total_years: float` → `total_years: Decimal`, remove internal `Decimal(str(...))` wrappers, ensure return dict values are Decimal
- [x] T009 [US4] Update all callers of `calculate_eos_gratuity()` to pass Decimal values in `backend/routers/hr/core.py` (EOS endpoint) and `backend/routers/hr_wps_compliance.py` (EOS settlement)

**Checkpoint**: EOS calculations are fully Decimal — no float precision loss at any boundary

---

## Phase 5: User Story 2 — Frontend formatNumber for Monetary Display (Priority: P1)

**Goal**: All HR and TimeTracking pages use `formatNumber()` instead of `.toLocaleString()` / `.toFixed()` for monetary values

**Independent Test**: `grep -rn "toLocaleString\|\.toFixed" frontend/src/pages/HR/Employees.jsx frontend/src/pages/HR/EOSSettlement.jsx frontend/src/pages/HR/HRHome.jsx frontend/src/pages/HR/Violations.jsx frontend/src/pages/HR/SalaryStructures.jsx frontend/src/pages/TimeTracking/ | grep -v "date\|Date\|time\|Time" | wc -l` → 0

**Scope**: Main HR/ pages + TimeTracking/ (GOSISettings/WPSExport handled in US9, SelfService in US10)

### Implementation for User Story 2

- [x] T010 [P] [US2] Replace `toLocaleString()` → `formatNumber()` for monetary values in `frontend/src/pages/HR/Employees.jsx` (2 calls) — add `import { formatNumber } from '../../utils/format'` if missing
- [x] T011 [P] [US2] Replace `Number(result.xxx).toLocaleString()` → `formatNumber(result.xxx)` in `frontend/src/pages/HR/EOSSettlement.jsx` (5 calls)
- [x] T012 [P] [US2] Replace `toLocaleString()` → `formatNumber()` in `frontend/src/pages/HR/HRHome.jsx` (2 calls) and `frontend/src/pages/HR/SalaryStructures.jsx` (1 call)
- [x] T013 [P] [US2] Replace `toLocaleString()` → `formatNumber()` in `frontend/src/pages/TimeTracking/ProjectProfitability.jsx` (3 calls)
- [x] T014 [P] [US2] Replace `v.deduction_amount?.toLocaleString()` → `formatNumber(v.deduction_amount)` in `frontend/src/pages/HR/Violations.jsx` (1 call)

**Checkpoint**: Main HR and TimeTracking pages use consistent formatNumber() for all monetary display

---

## Phase 6: User Story 3 — User-Visible Error Handling via Toast (Priority: P1)

**Goal**: All `console.error` / `console.log` replaced with `toastEmitter.emit()` for user-visible error feedback

**Independent Test**: `grep -rn "console\.error\|console\.log" frontend/src/pages/HR/ frontend/src/pages/SelfService/ frontend/src/pages/Performance/ frontend/src/pages/TimeTracking/ | wc -l` → 0

### Implementation for User Story 3

- [x] T015 [P] [US3] Replace all `console.error` / `console.log` → `toastEmitter.emit(t('...'), 'error')` in `frontend/src/pages/HR/` (21 instances across 11 files) — add `import { toastEmitter } from '../../utils/toastEmitter'` where missing, use existing i18n keys or add new `hr.*.error_*` keys
- [x] T016 [P] [US3] Replace all `console.error` → `toastEmitter.emit()` in `frontend/src/pages/SelfService/` (5 instances across 5 files)
- [x] T017 [P] [US3] Replace all `console.error` → `toastEmitter.emit()` in `frontend/src/pages/Performance/` (6 instances across 6 files)
- [x] T018 [P] [US3] Replace all `console.error` → `toastEmitter.emit()` in `frontend/src/pages/TimeTracking/` (5 instances across 3 files)

**Checkpoint**: All HR-related frontend pages show toast notifications on errors — zero silent failures

---

## Phase 7: User Story 5 — Frontend Sends Correct Data Types (Priority: P1)

**Goal**: All HR form submissions send monetary values as strings (not parseFloat results) in API payloads

**Independent Test**: Review API payloads from employee create, loan create, GOSI settings — all monetary fields are string type

### Implementation for User Story 5

- [x] T019 [US5] Audit and fix all monetary form submissions in `frontend/src/pages/HR/Employees.jsx` — ensure salary, housing_allowance, transport_allowance, other_allowances, hourly_cost are sent as `String(value)` not `parseFloat(value)` in create/update API calls
- [x] T020 [P] [US5] Audit and fix monetary form submissions in HR loan pages, overtime request pages, and `frontend/src/pages/HR/GOSISettings.jsx` — ensure all monetary inputs use `String()` conversion before API submission

**Checkpoint**: Backend receives exact string values for all monetary fields — no floating-point loss at frontend→backend boundary

---

## Phase 8: User Story 6 — Consistent Toast Notification System (Priority: P2)

**Goal**: All HR pages use a single toast pattern (toastEmitter) — no mixed `toast()` / `toastEmitter` / `useToast` usage

**Independent Test**: No imports of `react-hot-toast` directly in HR pages; all toast calls use `toastEmitter.emit()`

### Implementation for User Story 6

- [x] T021 [US6] Normalize all mixed toast patterns across `frontend/src/pages/HR/`, `frontend/src/pages/SelfService/`, `frontend/src/pages/Performance/`, `frontend/src/pages/TimeTracking/` — replace any remaining direct `toast()` / `toast.success()` / `toast.error()` imports from `react-hot-toast` with `toastEmitter.emit(message, type)` pattern

**Checkpoint**: Single consistent notification pattern across all HR frontend pages

---

## Phase 9: User Story 7 — Branch Access Validation (Priority: P2)

**Goal**: All branch-scoped HR endpoints call `validate_branch_access()` — no cross-branch data leakage

**Independent Test**: Accessing performance/saudization/WPS endpoints with wrong branch returns 403

### Implementation for User Story 7

- [x] T022 [P] [US7] Add `validate_branch_access(current_user, branch_id)` to all 8 endpoints (create cycle, list cycles, launch cycle, list reviews, self-assessment, manager-assessment, get review, cycle stats) in `backend/routers/hr/performance.py`
- [x] T023 [P] [US7] Add `validate_branch_access()` to saudization dashboard, saudization report, WPS export, and WPS preview endpoints in `backend/routers/hr_wps_compliance.py` (4 endpoints)
- [x] T024 [P] [US7] Verify and add `validate_branch_access()` to overtime, document, training, and custody endpoints in `backend/routers/hr/advanced.py`

**Checkpoint**: All HR branch-scoped endpoints enforce branch access — 403 on unauthorized branch access

---

## Phase 10: User Story 8 — Audit Trail Completeness (Priority: P2)

**Goal**: All HR models inherit AuditMixin; all write operations call log_activity()

**Independent Test**: All HR models have created_at/updated_at/created_by/updated_by columns; every create/update/delete in HR routers produces an audit log entry

### Implementation for User Story 8

- [x] T025 [US8] Verify all 21 HR models inherit `AuditMixin` (and `SoftDeleteMixin` where applicable per data-model.md) in `backend/models/domain_models/hr_core_payroll.py` — add missing mixin inheritance
- [x] T026 [P] [US8] Add missing `log_activity()` calls to all write operations (create/update/delete) in `backend/routers/hr/performance.py` — import from `utils/audit.py`, log review submissions, cycle launches, assessments
- [x] T027 [P] [US8] Add missing `log_activity()` calls to write operations in `backend/routers/hr/advanced.py` — document CRUD, training CRUD, overtime, custody, violations
- [x] T028 [P] [US8] Add missing `log_activity()` calls to write operations in `backend/routers/hr/self_service.py` — profile updates, leave requests, document uploads

**Checkpoint**: Complete audit trail — every HR state change is logged with who/when/what

---

## Phase 11: User Story 9 — GOSI/WPS Monetary Formatting (Priority: P2)

**Goal**: GOSI and WPS regulatory displays use formatNumber() for consistent precision

**Independent Test**: `grep -rn "toLocaleString\|\.toFixed" frontend/src/pages/HR/GOSISettings.jsx frontend/src/pages/HR/WPSExport.jsx | wc -l` → 0

### Implementation for User Story 9

- [x] T029 [P] [US9] Replace all `toLocaleString()` and `.toFixed(2)` → `formatNumber()` for GOSI contribution displays in `frontend/src/pages/HR/GOSISettings.jsx` (4 toLocaleString + toFixed calls)
- [x] T030 [P] [US9] Replace all `Number(val).toLocaleString()` → `formatNumber()` for WPS salary column displays in `frontend/src/pages/HR/WPSExport.jsx` (4 calls)

**Checkpoint**: Regulatory displays (GOSI contributions, WPS salary preview) use consistent formatNumber() precision

---

## Phase 12: User Story 10 — Self-Service Portal Formatting (Priority: P3)

**Goal**: Employee self-service portal uses formatNumber() for all monetary displays

**Independent Test**: `grep -rn "toLocaleString" frontend/src/pages/SelfService/ | grep -v "date\|Date" | wc -l` → 0

### Implementation for User Story 10

- [x] T031 [P] [US10] Replace `Number(ps.net_salary).toLocaleString()` → `formatNumber(ps.net_salary)` in `frontend/src/pages/SelfService/EmployeeDashboard.jsx`
- [x] T032 [P] [US10] Replace `Number(ps.xxx).toLocaleString()` → `formatNumber()` in `frontend/src/pages/SelfService/PayslipList.jsx` (3 calls) and replace `const fmt = (v) => Number(v).toLocaleString()` → `const fmt = formatNumber` in `frontend/src/pages/SelfService/PayslipDetail.jsx`

**Checkpoint**: Self-service portal shows consistent monetary formatting matching the rest of the application

---

## Phase 13: Polish & Cross-Cutting Concerns

**Purpose**: Validation and final sweep

- [x] T033 Run all quickstart.md verification commands to validate zero float in schemas, zero float() in routers, zero console.error in frontend, zero toLocaleString for monetary values
- [x] T034 [P] Final backend sweep — grep for any remaining `float` types in `backend/schemas/hr.py`, `float()` calls in `backend/routers/hr/`, and missing `log_activity()` in write endpoints
- [x] T035 [P] Final frontend sweep — grep for any remaining `console.error`, `console.log`, raw `toLocaleString` (monetary), or direct `react-hot-toast` imports in HR/SelfService/Performance/TimeTracking pages

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: No dependencies — can start in parallel with Phase 1
- **US1 (Phase 3)**: Depends on Phase 1 (masking.py) + Phase 2 (Decimal schemas) — **BLOCKS MVP**
- **US4 (Phase 4)**: Depends on Phase 2 (Decimal schemas)
- **US2 (Phase 5)**: No backend dependency — can start after Phase 1 (independent frontend work)
- **US3 (Phase 6)**: No backend dependency — can start after Phase 1 (independent frontend work)
- **US5 (Phase 7)**: No hard dependency — Pydantic Decimal accepts both float and string
- **US6 (Phase 8)**: Depends on Phase 6 (US3 must be done first — US6 normalizes patterns US3 introduces)
- **US7 (Phase 9)**: No dependencies on other stories — independent backend work
- **US8 (Phase 10)**: No dependencies on other stories — independent backend work
- **US9 (Phase 11)**: No dependencies — independent frontend work (different files from US2)
- **US10 (Phase 12)**: No dependencies — independent frontend work (different files from US2)
- **Polish (Phase 13)**: Depends on all stories being complete

### Parallel Opportunities

**Backend parallel track** (after Phase 2):
- US1 (Phase 3) + US4 (Phase 4) can overlap — different files except advanced.py (sequential within that file)
- US7 (Phase 9) + US8 (Phase 10) fully parallel — different concerns in same files (branch validation vs audit logging)

**Frontend parallel track** (independent of backend):
- US2 (Phase 5) + US3 (Phase 6) + US5 (Phase 7) can all run in parallel — different code patterns in potentially overlapping files
- US9 (Phase 11) + US10 (Phase 12) can run in parallel — different directories

**Cross-track parallelism**:
- All frontend phases (5, 6, 7, 11, 12) can run in parallel with all backend phases (3, 4, 9, 10)

### Within Each User Story

- Models/schemas before routers
- Routers before frontend consumers
- Core implementation before integration
- Story complete before Polish phase

### Parallel Example: Maximum Parallelism After Phase 2

```
After Phase 2 (Foundational) completes:

Backend Track A:  T004 → T005 → T006[P] + T007[P]     (US1: router precision)
Backend Track B:  T008 → T009                           (US4: EOS Decimal)
Backend Track C:  T022[P] + T023[P] + T024[P]           (US7: branch validation)
Backend Track D:  T025 → T026[P] + T027[P] + T028[P]    (US8: audit trails)

Frontend Track A: T010[P] + T011[P] + T012[P] + T013[P] + T014[P]  (US2: formatNumber)
Frontend Track B: T015[P] + T016[P] + T017[P] + T018[P]            (US3: toast errors)
Frontend Track C: T019 → T020[P]                                    (US5: form data types)
Frontend Track D: T029[P] + T030[P]                                 (US9: GOSI/WPS)
Frontend Track E: T031[P] + T032[P]                                 (US10: SelfService)
```

---

## Implementation Strategy

### MVP First (US1 Only — Backend Precision)

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phase 2: Foundational (T003)
3. Complete Phase 3: US1 — Numeric Precision (T004–T007)
4. **STOP and VALIDATE**: All API monetary values return as string Decimals, PII masked
5. This alone fixes the most critical constitution violation (Financial Precision)

### Incremental Delivery

1. Setup + Foundational → Schema foundation ready
2. US1 (backend precision) → **MVP deployed** — API returns exact Decimals
3. US4 (EOS precision) → EOS calculations fully Decimal
4. US2 + US3 (frontend formatting + errors) → Frontend displays correct values with user-visible errors
5. US5 (frontend data types) → Full precision round-trip (frontend→backend→frontend)
6. US6–US10 (P2/P3 stories) → Branch security, audit trails, regulatory formatting, self-service
7. Polish → Final validation sweep

### Single Developer Strategy

Execute phases sequentially in priority order:
1. Phase 1 + 2 (Setup + Foundational)
2. Phase 3 (US1 — MVP)
3. Phase 4 (US4 — EOS)
4. Phases 5 + 6 + 7 (US2 + US3 + US5 — frontend fixes)
5. Phase 8 (US6 — toast consistency)
6. Phases 9 + 10 (US7 + US8 — backend security + audit)
7. Phases 11 + 12 (US9 + US10 — regulatory + self-service formatting)
8. Phase 13 (Polish)

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [USx] label maps task to specific user story for traceability
- No test tasks included — not requested in specification
- All frontend changes are backward compatible with current string-or-number API responses
- Commit after each phase checkpoint for safe incremental delivery
