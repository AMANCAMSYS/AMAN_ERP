# Tasks: audit-taxes — الضرائب والزكاة

**Input**: Design documents from `/specs/008-audit-taxes/`
**Prerequisites**: plan.md, spec.md, research.md (R-01–R-10), data-model.md (13 entities), contracts/taxes-api.md, contracts/tax-compliance-api.md, contracts/external-wht-zatca-api.md, quickstart.md

**Tests**: Not explicitly requested — test tasks omitted.

**Organization**: Tasks grouped by user story. 6 user stories mapped from spec.md (US1–US6).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Maps to user story (US1–US6)
- Exact file paths included in all descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No schema migrations are required — this is an audit of existing code. Setup involves reading all design documents and confirming the source file inventory.

- [X] T001 Confirm inventory of source files to audit: `backend/routers/finance/taxes.py`, `backend/routers/finance/tax_compliance.py`, `backend/routers/external.py`, `backend/routers/system_completion.py`, `backend/models/domain_models/finance_treasury_tax.py`, `backend/models/domain_models/finance_fiscal_zakat.py`, `backend/models/domain_models/finance_recognition_tax.py`, `frontend/src/pages/Taxes/` (6 pages), `frontend/src/pages/Accounting/ZakatCalculator.jsx`, `frontend/src/services/taxes.js`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Repair the frontend service layer and branch validation gap — these are cross-cutting fixes that affect multiple user stories. All user story work depends on an accurate `taxes.js` service layer.

**⚠️ CRITICAL**: No frontend-related user story work can begin until this phase is complete

- [X] T002 Add `getSummary(params)` function to `frontend/src/services/taxes.js` mapping to `GET /taxes/summary` — needed by TaxHome dashboard (R-05 gap)
- [X] T003 [P] Add `getVATReport(params)` function to `frontend/src/services/taxes.js` mapping to `GET /taxes/reports/vat` — needed by VAT report (R-05 gap)
- [X] T004 [P] Add `getTaxAudit(params)` function to `frontend/src/services/taxes.js` mapping to `GET /taxes/reports/audit` — needed by audit report (R-05 gap)
- [X] T005 [P] Add `getBranchAnalysis(params)` function to `frontend/src/services/taxes.js` mapping to `GET /taxes/reports/branch-analysis` — needed by branch analysis (R-05 gap)
- [X] T006 [P] Add `getEmployeeTaxes(params)` function to `frontend/src/services/taxes.js` mapping to `GET /taxes/reports/employee-taxes` — needed by employee taxes report (R-05 gap)
- [X] T007 [P] Add `getCalendarSummary(params)` function to `frontend/src/services/taxes.js` mapping to `GET /taxes/calendar/summary` — needed by TaxCalendar (R-05 gap)
- [X] T008 Add `country_code NOT NULL` validation in branch creation endpoint: query branch payload; if `country_code` is `None` or empty string, return 422 with message "Branch country_code is required for tax calculation" before inserting — in `backend/routers/branches.py` (R-10 risk)

**Checkpoint**: Service layer complete and branch validation in place — all user stories can now use correct service functions and branch scoping.

---

## Phase 3: User Story 1 — VAT Calculation, Rates & GL Posting (Priority: P1) 🎯 MVP

**Goal**: TaxHome dashboard and VAT reports load real data; VAT rates CRUD works correctly; GL entries are posted with correct double-entry structure; Tax Home summary card reflects accurate output/input/net VAT figures.

**Independent Test**: Create a 15% VAT rate via `POST /taxes/rates` → apply to a 1,000 SAR sales invoice → verify system calculates 150 SAR VAT and posts GL entry (Dr. AR 1,150 / Cr. Revenue 1,000 / Cr. Output VAT 150) → open Tax Home (`/taxes`) → confirm summary card shows correct totals.

### Implementation for User Story 1

- [X] T009 [US1] Verify `TaxHome.jsx` calls `taxesAPI.getSummary()` (from T002) for the summary card — if currently calling `api.get(...)` inline, replace with the service function in `frontend/src/pages/Taxes/TaxHome.jsx`
- [X] T010 [P] [US1] Add loading state (`isLoading` guard + spinner) and error state (`try/catch` + toast notification) around all API calls in `frontend/src/pages/Taxes/TaxHome.jsx` — verify `listRates()`, `listReturns()`, and `getSummary()` are all wrapped (R-06)
- [X] T011 [P] [US1] Add loading and error states around all API calls in `frontend/src/pages/Taxes/TaxReturnForm.jsx`: `createReturn()` pre-fill call and any supporting list fetches — wrap in `try/catch` with user-visible toast error (R-06)
- [X] T012 [US1] Verify `GET /taxes/rates` response returns `rate` field as string not float (Constitution §I) — check serialization in `backend/routers/finance/taxes.py`; if float, wrap with `str()` or ensure Pydantic schema uses `Decimal` type with JSON serialization
- [X] T013 [P] [US1] Verify VAT rate CRUD endpoints (`POST /taxes/rates`, `PUT /taxes/rates/{id}`, `DELETE /taxes/rates/{id}`) all accept `Authorization: Bearer` header and reject 401 without token — confirm `require_permission` present on each in `backend/routers/finance/taxes.py` (R-02)
- [X] T014 [US1] Verify Tax Home VAT summary card (`getSummary` response) shows three values: `total_output_vat`, `total_input_vat`, `net_vat_liability` — if `GET /taxes/summary` does not return these fields, add them to the endpoint response in `backend/routers/finance/taxes.py`
- [X] T015 [P] [US1] Verify `GET /taxes/reports/vat` (mapped via T003 `getVATReport()`) returns correct field structure per `contracts/taxes-api.md` — test with a date range that covers posted invoices and confirm output matches expected VAT amounts in `backend/routers/finance/taxes.py`

**Checkpoint**: Tax Home dashboard loads real data, VAT rates CRUD works correctly, monetary precision is enforced, all API calls have loading/error states. US1 independently testable.

---

## Phase 4: User Story 2 — Tax Returns: Filing, Tracking & Status (Priority: P1)

**Goal**: Tax return creation pre-populates from posted invoices only; filing changes status to "filed" correctly; Tax Returns list page shows all returns with correct pagination; Tax Return Details page shows no undefined/null fields.

**Independent Test**: Create a VAT return for Q1 2026 via `POST /taxes/returns` → verify pre-populated `output_vat` matches sum of posted invoice VAT → file it via `PUT /taxes/returns/{id}/file` → verify status = "filed" and filed date recorded → view Tax Return Details page → confirm all fields visible and no "undefined" text.

### Implementation for User Story 2

- [X] T016 [US2] Verify `TaxReturnForm.jsx` POSTs to `taxesAPI.createReturn()` and displays pre-populated amounts from the backend response — if page uses inline `api.post(...)`, switch to the service function in `frontend/src/pages/Taxes/TaxReturnForm.jsx`
- [X] T017 [US2] Verify `TaxReturnDetails.jsx` renders all fields from the return record without showing "undefined", "null", or empty labels — check: `period`, `taxable_amount`, `tax_amount`, `filed_date`, `payment_status`, `return_type`, `branch_id`; add null-safe rendering (`field ?? '-'`) in `frontend/src/pages/Taxes/TaxReturnDetails.jsx`
- [X] T018 [P] [US2] Add loading and error states to `TaxReturnDetails.jsx`: wrap the initial data fetch in `try/catch` with a spinner during load and a toast error on failure in `frontend/src/pages/Taxes/TaxReturnDetails.jsx` (R-06)
- [X] T019 [P] [US2] Add loading and error states to Tax Returns list table in `TaxHome.jsx` or dedicated returns page: wrap `listReturns()` call in `try/catch` with visible error when empty or failed in `frontend/src/pages/Taxes/TaxHome.jsx`
- [X] T020 [US2] Verify `PUT /taxes/returns/{id}/file` response returns status 200 with `{"status": "filed", "filed_date": "..."}` — if currently returning 204 or omitting fields, update endpoint response in `backend/routers/finance/taxes.py` per `contracts/taxes-api.md`
- [X] T021 [US2] Verify duplicate return prevention: `POST /taxes/returns` with same `period` + `return_type` + `branch_id` as an existing filed return must return HTTP 409 with `{"detail": "A filed return already exists for this period and type"}` — test the query in `backend/routers/finance/taxes.py` (US2 acceptance scenario 4)
- [X] T022 [P] [US2] Add payment status display on `TaxReturnDetails.jsx`: if `linked_payments` list is empty, show "No payments recorded" instead of empty table; each payment row should show amount, paid_date, reference in `frontend/src/pages/Taxes/TaxReturnDetails.jsx`

**Checkpoint**: Tax return lifecycle (create → pre-fill → file → view details) works end-to-end. Duplicate prevention returns 409. Details page shows no broken fields. US2 independently testable.

---

## Phase 5: User Story 3 — ZATCA E-Invoicing Compliance (Priority: P1)

**Goal**: Tax Compliance page loads/saves company settings without exposing private key; ZATCA phase change is persisted and reflected; branch tax settings save independently; QR code appears on invoices automatically.

**Independent Test**: Open Tax Compliance page → verify `zatca_private_key` field is absent from `GET /tax-compliance/company-settings` response → update ZATCA phase to Phase 2 → verify `PUT` saves successfully → verify `GET` returns `zatca_phase: "phase2"` and `has_zatca_key: true` (not the actual key).

### Implementation for User Story 3

- [X] T023 [US3] Verify `GET /tax-compliance/company-settings` never returns `zatca_private_key` in response — confirm Pydantic response schema in `backend/routers/finance/tax_compliance.py` uses `has_zatca_key: bool` instead; if key leaks, remove from schema and add the boolean flag (Constitution §V, data-model.md)
- [X] T024 [P] [US3] Verify `TaxCompliance.jsx` save/load round-trip: `getCompanySettings()` loads current values into form fields; `updateCompanySettings(data)` saves and page refreshes with updated values — trace through `frontend/src/pages/Taxes/TaxCompliance.jsx` and `frontend/src/services/taxes.js`
- [X] T025 [P] [US3] Add loading and error states to `TaxCompliance.jsx`: settings load wrapped in spinner; save action shows success toast on 200 or error toast on 4xx/5xx in `frontend/src/pages/Taxes/TaxCompliance.jsx` (R-06)
- [X] T026 [US3] Verify `PUT /tax-compliance/company-settings` validates `vat_number` format (15-digit starting with "3" for Saudi) — if no validation present, add Pydantic validator to the request schema in `backend/routers/finance/tax_compliance.py` (ZATCA mandate)
- [X] T027 [P] [US3] Verify branch tax settings round-trip: `PUT /tax-compliance/branch-settings/{branch_id}` saves independently per branch and does not overwrite company-level settings — test with two branch IDs and confirm isolation in `backend/routers/finance/tax_compliance.py`
- [X] T028 [US3] Verify `TaxCompliance.jsx` hides ZATCA configuration section for non-Saudi companies: check component renders based on `companySettings.country_code === 'SA'` check; if missing, add conditional render in `frontend/src/pages/Taxes/TaxCompliance.jsx` (US3 acceptance scenario 5)
- [X] T029 [P] [US3] Verify `GET /external/zatca/generate-qr` returns `zatca_qr` as a non-empty Base64 string for any valid invoice — confirm endpoint exists and properly encodes seller name, VAT number, timestamp, total, VAT amount per ZATCA TLV standard in `backend/routers/external.py` (R-04)

**Checkpoint**: ZATCA private key never exposed, company and branch settings save/load correctly, ZATCA UI gates non-Saudi companies. US3 independently testable.

---

## Phase 6: User Story 4 — Zakat Calculation & GL Posting (Priority: P2)

**Goal**: Zakat Calculator loads only for Saudi companies; calculation produces 2.5% of net Zakat base; GL posting creates balanced journal entry; duplicate posting is prevented; posted state disables re-post button.

**Independent Test**: Open Zakat Calculator (SA company) → enter net assets → verify computed amount = net_assets × 0.025 → click "Post to GL" → verify journal entry created (Dr. Zakat Expense / Cr. Zakat Payable) → attempt to post again → verify 400 with duplicate message.

### Implementation for User Story 4

- [X] T030 [US4] Verify `ZakatCalculator.jsx` renders "Coming Soon" screen for non-Saudi companies (`ZAKAT_SUPPORTED_COUNTRIES.includes(country)` check) and full calculator for SA — confirm `getCountry()` is called correctly and handles `undefined` without throwing in `frontend/src/pages/Accounting/ZakatCalculator.jsx` (R-08)
- [X] T031 [US4] Verify `POST /accounting/zakat/calculate` returns `zakat_amount` as a string representation of `Decimal` (not float) and that the calculation is `net_zakat_base × 0.025` — cross-check: `400,000 SAR → 10,000 SAR Zakat` in `backend/routers/system_completion.py` (Constitution §I)
- [X] T032 [US4] Verify `POST /accounting/zakat/post` creates a balanced GL journal entry (Dr. Zakat Expense account / Cr. Zakat Payable account) following the `gl_service.py` pattern — confirm no raw INSERT; check for matching debit/credit amounts in `backend/routers/system_completion.py` (R-03, Constitution §III)
- [X] T033 [P] [US4] Verify duplicate Zakat post prevention: second `POST /accounting/zakat/post` for same fiscal year + branch returns HTTP 400 with `{"detail": "Zakat already posted for this fiscal year"}` — confirm the `is_posted` check query and the UNIQUE constraint (`fiscal_year + branch_id`) in `backend/routers/system_completion.py` (data-model.md)
- [X] T034 [US4] After successful GL posting, `ZakatCalculator.jsx` must disable the "Post to GL" button and show the calculation as read-only with GL reference number — verify the component updates `is_posted` state from the response and disables the button in `frontend/src/pages/Accounting/ZakatCalculator.jsx` (US4 acceptance scenario 3)
- [X] T035 [P] [US4] Add loading and error states to `ZakatCalculator.jsx`: calculation call wrapped in spinner; post action shows success toast with GL reference or error toast with detail message in `frontend/src/pages/Accounting/ZakatCalculator.jsx` (R-06)

**Checkpoint**: Zakat is SA-only, calculation is accurate, GL posting creates balanced JE, duplicate prevention works, UI disables re-post. US4 independently testable.

---

## Phase 7: User Story 5 — Withholding Tax (WHT) Rates & Certificate Tracking (Priority: P2)

**Goal**: WHT certificate creation correctly calculates net payment (gross − WHT); `wht_amount` returned as string not float; WHT Transactions list filters by supplier and date; all certificate fields render correctly.

**Independent Test**: Select Professional Services (5% WHT) → enter gross 20,000 SAR → verify WHT = 1,000 SAR, net = 19,000 SAR → create certificate → confirm it appears in `GET /external/wht/transactions` list → filter by supplier → verify list narrows correctly.

### Implementation for User Story 5

- [X] T036 [US5] Verify `POST /external/wht/transactions` calculates `wht_amount = gross_amount × (rate / 100)` using `Decimal` arithmetic and returns `wht_amount`, `net_amount` as strings — check for any `float()` conversion in `backend/routers/external.py` (Constitution §I, R-01)
- [X] T037 [P] [US5] Verify `WithholdingTax.jsx` displays all certificate fields without "undefined" or empty values: `supplier`, `gross_amount`, `category`, `rate_percent`, `wht_amount`, `net_payment`, `reference_number`, `created_at` — add null-safe rendering for each field in `frontend/src/pages/Taxes/WithholdingTax.jsx`
- [X] T038 [US5] Verify `GET /external/wht/transactions` filters work correctly: `supplier_id`, `from_date`, `to_date` query params applied in SQL WHERE clause with parameterized queries — confirm `text()` usage and correct date comparison in `backend/routers/external.py` (R-01)
- [X] T039 [P] [US5] Add loading and error states to `WithholdingTax.jsx`: wrap `listWhtRates()` and `listWhtTransactions()` calls in `try/catch` with spinner during load and toast on error in `frontend/src/pages/Taxes/WithholdingTax.jsx` (R-06)
- [X] T040 [US5] Verify WHT rate selection in certificate form: when the accountant selects a WHT rate from the dropdown, the `rate_percent` value pre-fills in the form and the `wht_amount` auto-calculates client-side before submission — confirm the `onChange` handler performs `gross_amount × (rate_percent / 100)` in `frontend/src/pages/Taxes/WithholdingTax.jsx`
- [X] T041 [P] [US5] Verify `GET /external/wht/rates` returns active rates with `effective_date` and `category` — confirm endpoint exists and returns the correct fields per `contracts/external-wht-zatca-api.md` in `backend/routers/external.py`
- [X] T042 [US5] Verify the WHT summary dashboard on Tax Home shows total WHT collected for the current period broken down by category — if `getSummary()` (T002) does not include `wht_breakdown`, check if a separate endpoint is needed and wire accordingly in `backend/routers/finance/taxes.py` and `frontend/src/pages/Taxes/TaxHome.jsx` (US5 acceptance scenario 5)

**Checkpoint**: WHT calculation is Decimal-correct, certificate creation works, filters apply correctly, all UI fields rendered. US5 independently testable.

---

## Phase 8: User Story 6 — Tax Calendar: Deadlines & Reminders (Priority: P3)

**Goal**: Tax Calendar page loads recurring deadlines for the next 12 months; mark-complete creates the next recurrence; overdue items are visually highlighted; calendar filters by obligation type; `getCalendarSummary()` wired correctly.

**Independent Test**: Open Tax Calendar → verify VAT monthly deadlines appear for next 12 months → mark one as complete → verify status updates and `next_recurrence_id` returned in response → verify new recurring item appears → filter by "VAT" → verify list narrows.

### Implementation for User Story 6

- [X] T043 [US6] Verify `TaxCalendar.jsx` calls `taxesAPI.listCalendar()` (from `frontend/src/services/taxes.js`) and renders all upcoming items with `due_date`, `tax_type`, `days_remaining`, `is_completed`, `is_overdue` fields — if inline `api.get(...)` used, switch to service function in `frontend/src/pages/Taxes/TaxCalendar.jsx`
- [X] T044 [US6] Verify mark-complete flow: `taxesAPI.completeCalendarItem(id)` is called on button click, the response `next_recurrence_id` is used to update the list (add the new recurring item, mark current as complete), and the UI reflects the change without full page reload in `frontend/src/pages/Taxes/TaxCalendar.jsx` (R-07)
- [X] T045 [P] [US6] Wire `taxesAPI.getCalendarSummary()` (T007) to the calendar summary section — if `TaxCalendar.jsx` shows a summary count or totals section, update it to call the service function instead of inline API or static values in `frontend/src/pages/Taxes/TaxCalendar.jsx`
- [X] T046 [P] [US6] Add visual indicator for overdue items: if `is_overdue = true` or `days_remaining < 0`, apply a red/warning CSS class or badge to the calendar row; if `days_remaining` between 1–7, apply amber/warning indicator in `frontend/src/pages/Taxes/TaxCalendar.jsx` (US6 acceptance scenario 3)
- [X] T047 [P] [US6] Add obligation type filter to `TaxCalendar.jsx`: render a filter dropdown with options from the unique `tax_type` values; filter the displayed list client-side or via `listCalendar({tax_type})` param — confirm `GET /taxes/calendar?tax_type=...` filter is supported in backend in `frontend/src/pages/Taxes/TaxCalendar.jsx` (US6 acceptance scenario 5)
- [X] T048 [P] [US6] Add loading and error states to `TaxCalendar.jsx`: wrap `listCalendar()` call in `try/catch` with spinner and toast error on failure; show "No deadlines found" empty state when list is empty in `frontend/src/pages/Taxes/TaxCalendar.jsx` (R-06)
- [X] T049 [US6] Verify `GET /taxes/calendar` backend endpoint supports `tax_type`, `from_date`, `to_date` filter params and returns `is_overdue` boolean computed from current date vs `due_date` — if `is_overdue` not computed, add: `is_overdue = due_date < CURRENT_DATE AND NOT is_completed` in `backend/routers/finance/taxes.py`

**Checkpoint**: Tax Calendar loads recurring deadlines, mark-complete creates next recurrence, overdue items highlighted, filters work. US6 independently testable.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final validation of security, precision, i18n, and audit trail across all user stories

- [X] T050 Run `quickstart.md` verification checklist: execute all 8 curl-based test scenarios (VAT rate creation, return pre-population, duplicate prevention, WHT certificate, Zakat calculate+post+duplicate, ZATCA QR, private key not exposed, recurring calendar) and confirm all pass
- [X] T051 [P] Verify all monetary response fields from tax endpoints are returned as strings (not JSON numbers) — grep `backend/routers/finance/taxes.py` and `backend/routers/finance/tax_compliance.py` for any `float()` cast or `Decimal → float` coercion and fix (Constitution §I)
- [X] T052 [P] Verify all 40+ tax endpoints include `log_activity()` or equivalent audit trail call with `resource_type="tax_*"` and `action` set appropriately — check `backend/routers/finance/taxes.py` and `backend/routers/finance/tax_compliance.py` (FR-028 audit trail requirement)
- [X] T053 [P] Verify i18n coverage: all visible text strings in the 6 tax pages and `ZakatCalculator.jsx` use `t('key')` from i18next and have corresponding Arabic (`ar`) and English (`en`) translation keys — check `frontend/src/locales/` for any missing keys (FR-027)
- [X] T054 [P] Verify `validate_branch_access()` is called on all branch-scoped tax endpoints: `GET /tax-compliance/applicable-taxes/{branch_id}`, `PUT /tax-compliance/branch-settings/{branch_id}`, and `POST /taxes/returns` with `branch_id` — confirm guard present in `backend/routers/finance/tax_compliance.py` and `backend/routers/finance/taxes.py`
- [X] T055 [P] Verify no raw SQL string interpolation in any of the 4 audited backend files — all parameterized with `text()` and `:param` syntax; fail fast on any discovered f-string or `.format()` in SQL in `backend/routers/finance/taxes.py`, `tax_compliance.py`, `external.py`, `system_completion.py` (Constitution §VII)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (file inventory complete)
- **User Stories (Phase 3–8)**: All depend on Phase 2 (taxes.js service functions must exist before US wiring)
  - US1, US2, US3 are P1 — implement first; can be done in parallel across different page files
  - US4, US5 are P2 — implement after P1 stories (share some backend infrastructure)
  - US6 is P3 — implement last
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Depends on T002 (`getSummary`) from Phase 2 — independent otherwise
- **US2 (P1)**: Depends on Phase 2 foundation — independent of US1
- **US3 (P1)**: Depends on Phase 2 foundation — independent of US1 and US2
- **US4 (P2)**: Independent of US1–US3 (different files: `ZakatCalculator.jsx`, `system_completion.py`)
- **US5 (P2)**: Depends on T002 (`getSummary`) for WHT dashboard — otherwise independent
- **US6 (P3)**: Depends on T007 (`getCalendarSummary`) from Phase 2 — otherwise independent

### Parallel Execution Opportunities (per story)

| Story | Parallel Tasks |
|-------|---------------|
| US1 | T010 (TaxHome loading states) ‖ T011 (TaxReturnForm loading states) ‖ T012 (rate precision) ‖ T013 (permission audit) |
| US2 | T017 (Details null-safe) ‖ T018 (Details loading) ‖ T019 (Returns list loading) ‖ T022 (payment display) |
| US3 | T024 (TaxCompliance round-trip) ‖ T025 (TaxCompliance loading) ‖ T027 (branch isolation) ‖ T029 (QR verify) |
| US4 | T033 (duplicate check) ‖ T035 (ZakatCalculator loading) |
| US5 | T037 (field rendering) ‖ T039 (WHT loading) ‖ T041 (rates endpoint) |
| US6 | T045 (calendar summary) ‖ T046 (overdue indicator) ‖ T047 (type filter) ‖ T048 (calendar loading) |

---

## Implementation Strategy

### MVP Scope (US1 + US2 only)

Completing Phases 1–4 delivers:
- Functional Tax Home dashboard with real VAT summary data
- Working VAT rate management (CRUD)
- Tax return creation pre-filled from posted invoices
- Filing workflow (draft → filed) with duplicate prevention
- Tax Return Details page with no broken fields

**MVP Definition**: An accountant can manage VAT rates, file a tax return for a period, and view the return details — all with correct loading/error states and Decimal monetary precision.

### Incremental Delivery Order

1. **Phase 2** (Foundational): Add 6 missing `taxes.js` service functions + branch validation — 1 hour estimated
2. **Phase 3** (US1): TaxHome wiring + precision audit — 2 hours estimated
3. **Phase 4** (US2): Tax return lifecycle + Details page repair — 2 hours estimated
4. **Phase 5** (US3): ZATCA compliance page audit + private key check — 1.5 hours estimated
5. **Phase 6** (US4): Zakat GL posting verification + UI state — 1.5 hours estimated
6. **Phase 7** (US5): WHT certificate + Decimal precision — 1.5 hours estimated
7. **Phase 8** (US6): Calendar recurring + overdue indicators — 1 hour estimated
8. **Phase 9** (Polish): Cross-cutting audit pass — 1 hour estimated
