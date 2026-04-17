# Tasks: Audit Sales Module — تدقيق وحدة المبيعات

**Input**: Design documents from `/specs/012-audit-sales/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested — no test tasks generated.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1–US12)
- Exact file paths included in all descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No new project setup needed — all changes are in-place edits to existing files.

- [X] T001 Verify branch `012-audit-sales` is checked out and all target files exist per plan.md project structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Audit infrastructure changes that MUST complete before user story work — AuditMixin on domain models and audit columns on database tables.

**⚠️ CRITICAL**: These changes affect the schema layer; user story tasks (Phase 3+) depend on these being in place.

- [X] T002 Add AuditMixin to all sales-exclusive models in `backend/models/domain_models/sales_rfq.py` — SalesCommission, SalesOpportunity, SalesOrder, SalesOrderLine, SalesQuotation, SalesQuotationLine, SalesReturn, SalesReturnLine, SalesTarget, RequestForQuotation, RfqLine, RfqResponse (import AuditMixin from models.base; add to class inheritance; remove any manually-defined created_at/updated_at/created_by where AuditMixin covers them)
- [X] T003 Verify AuditMixin status on shared models in `backend/models/domain_models/sales_customers_delivery.py` — Customer, CustomerBalance, DeliveryOrder, DeliveryOrderLine (verify existing audit columns; do NOT add AuditMixin if already present or if shared with other modules)
- [X] T004 Add missing audit columns to `invoices` table in `backend/database.py` — add `updated_by` column (VARCHAR(100))
- [X] T005 [P] Add missing audit columns to `invoice_lines` table in `backend/database.py` — add `updated_at`, `created_by`, `updated_by`
- [X] T006 [P] Add missing audit columns to `sales_quotations` table in `backend/database.py` — add `updated_at`, `updated_by`
- [X] T007 [P] Add missing audit columns to `sales_quotation_lines` table in `backend/database.py` — add `created_at`, `updated_at`, `created_by`, `updated_by`
- [X] T008 [P] Add missing audit columns to `sales_orders` table in `backend/database.py` — add `updated_at`, `updated_by`
- [X] T009 [P] Add missing audit columns to `sales_order_lines` table in `backend/database.py` — add `created_at`, `updated_at`, `created_by`, `updated_by`
- [X] T010 [P] Add missing audit columns to `sales_returns` table in `backend/database.py` — add `updated_at`, `updated_by`
- [X] T011 [P] Add missing audit columns to `sales_return_lines` table in `backend/database.py` — add `created_at`, `updated_at`, `created_by`, `updated_by`
- [X] T012 [P] Add missing audit columns to `payment_vouchers` table in `backend/database.py` — add `updated_at`, `created_by`, `updated_by`
- [X] T013 [P] Add missing audit columns to `sales_commissions` table in `backend/database.py` — add `updated_at`, `created_by`, `updated_by`
- [X] T014 Change Pydantic `float` fields to `Decimal` in `backend/schemas/sales_credit_notes.py` — change `quantity: float = 1` to `quantity: Decimal = Decimal("1")` in SalesNoteLine; verify all other fields already use Decimal
- [X] T015 [P] Audit and fix any remaining `float` fields in `backend/schemas/sales_improvements.py` — change all monetary/quantity/rate fields to `Decimal`
- [X] T016 [P] Audit and fix any remaining `float` fields in `backend/routers/sales/schemas.py` — change all monetary/quantity/rate/percentage fields to `Decimal`; add `from decimal import Decimal` if missing
- [X] T017 [P] Verify `backend/schemas/cpq.py` has no remaining `float` fields — already mostly Decimal; fix any remaining float fields

**Checkpoint**: Foundation ready — all schema, model, and database infrastructure in place. User story implementation can begin.

---

## Phase 3: User Story 1 — Numeric Precision Across All Sales Endpoints (Priority: P1) 🎯 MVP

**Goal**: Replace all `float()` serialization with `str()` in backend sales router and service files so API responses return exact string values for monetary fields.

**Independent Test**: `grep -rn "float(" backend/routers/sales/ backend/routers/delivery_orders.py backend/services/cpq_service.py | grep -v "#" | wc -l` → must return 0

- [X] T018 [P] [US1] Replace all `float()` calls with `str()` in `backend/routers/sales/customers.py` — pattern: `float(value)` → `str(value or 0)` for all monetary response fields (total_revenue, total_receivables, monthly_sales, balances, etc.)
- [X] T019 [P] [US1] Replace all `float()` calls with `str()` in `backend/routers/sales/quotations.py` — all monetary serialization in response dicts
- [X] T020 [P] [US1] Replace all `float()` calls with `str()` in `backend/routers/sales/orders.py` — all monetary serialization in response dicts
- [X] T021 [P] [US1] Replace all `float()` calls with `str()` in `backend/routers/sales/invoices.py` — all monetary serialization in response dicts; verify fiscal check at line 194 remains correct
- [X] T022 [P] [US1] Replace all `float()` calls with `str()` in `backend/routers/sales/returns.py` — all monetary serialization; verify fiscal check at lines 104-105 remains correct
- [X] T023 [P] [US1] Replace all `float()` calls with `str()` in `backend/routers/sales/credit_notes.py` — all monetary serialization; verify fiscal checks at lines 195-197 and 538-540 remain correct
- [X] T024 [P] [US1] Replace all `float()` calls with `str()` in `backend/routers/sales/vouchers.py` — all monetary serialization; verify fiscal checks at lines 34-36 and 266-268 remain correct
- [X] T025 [P] [US1] Replace all `float()` calls with `str()` in `backend/routers/sales/cpq.py` — all monetary serialization in response dicts
- [X] T026 [P] [US1] Replace all `float()` calls with `str()` in `backend/routers/sales/sales_improvements.py` — all monetary serialization EXCEPT commission calculation (handled in US10)
- [X] T027 [P] [US1] Replace all `float()` calls with `str()` in `backend/routers/delivery_orders.py` — all quantity and amount serialization
- [X] T028 [P] [US1] Replace all `float()` calls with `str()` in `backend/services/cpq_service.py` — all price calculation serialization; use `Decimal` for intermediate computation
- [X] T029 [US1] Run `py_compile` on all 12 modified backend files to verify no syntax errors

**Checkpoint**: Zero `float()` calls remain in sales backend. SC-001 verified.

---

## Phase 4: User Story 2 — Frontend Sends Correct Data Types to Backend (Priority: P1)

**Goal**: Replace all `parseFloat()` with `Number()` for local calculations and `String()` for API payloads in all 38 frontend files.

**Independent Test**: `grep -rn "parseFloat" frontend/src/pages/Sales/ frontend/src/pages/CPQ/ | wc -l` → must return 0

- [X] T030 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/Sales/InvoiceForm.jsx` — local calc: `Number()`, API payload: `String()`
- [X] T031 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/Sales/InvoiceList.jsx`
- [X] T032 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/Sales/InvoiceDetails.jsx`
- [X] T033 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/Sales/SalesQuotationForm.jsx`
- [X] T034 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/Sales/SalesQuotations.jsx`
- [X] T035 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/Sales/SalesQuotationDetails.jsx`
- [X] T036 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/Sales/SalesOrderForm.jsx`
- [X] T037 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/Sales/SalesOrders.jsx`
- [X] T038 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/Sales/SalesOrderDetails.jsx`
- [X] T039 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/Sales/SalesReturnForm.jsx`
- [X] T040 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/Sales/SalesReturns.jsx`
- [X] T041 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/Sales/SalesReturnDetails.jsx`
- [X] T042 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/Sales/SalesCreditNotes.jsx`
- [X] T043 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/Sales/SalesDebitNotes.jsx`
- [X] T044 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/Sales/ReceiptForm.jsx`
- [X] T045 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/Sales/ReceiptDetails.jsx`
- [X] T046 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/Sales/CustomerReceipts.jsx`
- [X] T047 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/Sales/CustomerForm.jsx`
- [X] T048 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/Sales/CustomerDetails.jsx`
- [X] T049 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/Sales/CustomerList.jsx`
- [X] T050 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/Sales/CustomerGroups.jsx`
- [X] T051 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/Sales/CustomerStatement.jsx`
- [X] T052 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/Sales/DeliveryOrderForm.jsx`
- [X] T053 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/Sales/DeliveryOrders.jsx`
- [X] T054 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/Sales/DeliveryOrderDetails.jsx`
- [X] T055 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/Sales/AgingReport.jsx`
- [X] T056 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/Sales/SalesCommissions.jsx`
- [X] T057 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/Sales/SalesReports.jsx`
- [X] T058 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/Sales/SalesHome.jsx`
- [X] T059 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/Sales/ContractForm.jsx`
- [X] T060 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/Sales/ContractList.jsx`
- [X] T061 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/Sales/ContractDetails.jsx`
- [X] T062 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/Sales/ContractAmendments.jsx`
- [X] T063 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/Sales/InvoicePrintModal.jsx`
- [X] T064 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/CPQ/Configurator.jsx`
- [X] T065 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/CPQ/QuoteDetail.jsx`
- [X] T066 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/CPQ/QuoteList.jsx`
- [X] T067 [P] [US2] Replace parseFloat→Number/String in `frontend/src/pages/CPQ/ConfigurableProducts.jsx`

**Checkpoint**: Zero `parseFloat()` calls remain in sales/CPQ frontend files. SC-002 verified.

---

## Phase 5: User Story 3 — User-Visible Error Handling via Toast Notifications (Priority: P1)

**Goal**: Replace all `console.error` and `toastEmitter` with `useToast`/`showToast` in all 38 frontend files.

**Independent Test**: `grep -rn "console\.error\|toastEmitter" frontend/src/pages/Sales/ frontend/src/pages/CPQ/ | wc -l` → must return 0

- [X] T068 [P] [US3] Replace console.error→showToast and toastEmitter→useToast in `frontend/src/pages/Sales/InvoiceForm.jsx` — add `import { useToast } from '../../context/ToastContext'`; add `const { showToast } = useToast()`; replace all console.error catch blocks with `showToast(t('common.error'), 'error')`; remove toastEmitter import if present
- [X] T069 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/Sales/InvoiceList.jsx`
- [X] T070 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/Sales/InvoiceDetails.jsx`
- [X] T071 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/Sales/SalesQuotationForm.jsx`
- [X] T072 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/Sales/SalesQuotations.jsx`
- [X] T073 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/Sales/SalesQuotationDetails.jsx`
- [X] T074 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/Sales/SalesOrderForm.jsx`
- [X] T075 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/Sales/SalesOrders.jsx`
- [X] T076 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/Sales/SalesOrderDetails.jsx`
- [X] T077 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/Sales/SalesReturnForm.jsx`
- [X] T078 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/Sales/SalesReturns.jsx`
- [X] T079 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/Sales/SalesReturnDetails.jsx`
- [X] T080 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/Sales/SalesCreditNotes.jsx`
- [X] T081 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/Sales/SalesDebitNotes.jsx`
- [X] T082 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/Sales/ReceiptForm.jsx`
- [X] T083 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/Sales/ReceiptDetails.jsx`
- [X] T084 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/Sales/CustomerReceipts.jsx`
- [X] T085 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/Sales/CustomerForm.jsx`
- [X] T086 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/Sales/CustomerDetails.jsx`
- [X] T087 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/Sales/CustomerList.jsx`
- [X] T088 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/Sales/CustomerGroups.jsx`
- [X] T089 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/Sales/CustomerStatement.jsx`
- [X] T090 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/Sales/DeliveryOrderForm.jsx`
- [X] T091 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/Sales/DeliveryOrders.jsx`
- [X] T092 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/Sales/DeliveryOrderDetails.jsx`
- [X] T093 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/Sales/AgingReport.jsx`
- [X] T094 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/Sales/SalesCommissions.jsx`
- [X] T095 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/Sales/SalesReports.jsx`
- [X] T096 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/Sales/SalesHome.jsx`
- [X] T097 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/Sales/ContractForm.jsx`
- [X] T098 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/Sales/ContractList.jsx`
- [X] T099 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/Sales/ContractDetails.jsx`
- [X] T100 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/Sales/ContractAmendments.jsx`
- [X] T101 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/Sales/InvoicePrintModal.jsx`
- [X] T102 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/CPQ/Configurator.jsx`
- [X] T103 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/CPQ/QuoteDetail.jsx`
- [X] T104 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/CPQ/QuoteList.jsx`
- [X] T105 [P] [US3] Replace console.error/toastEmitter→useToast in `frontend/src/pages/CPQ/ConfigurableProducts.jsx`

**Checkpoint**: Zero `console.error` and zero `toastEmitter` in sales/CPQ frontend. SC-003, SC-004 verified.

---

## Phase 6: User Story 4 — Pydantic Schema Decimal Types (Priority: P1)

**Goal**: Already handled in Phase 2 foundational tasks (T014–T017). This phase is a verification pass.

**Independent Test**: `grep -rn ": float" backend/schemas/sales_credit_notes.py backend/schemas/sales_improvements.py backend/schemas/cpq.py backend/routers/sales/schemas.py | wc -l` → must return 0

- [X] T106 [US4] Verify all Pydantic float→Decimal changes from T014–T017 are complete — run grep across all 4 schema files; confirm zero `float` type annotations remain for monetary/quantity fields; run py_compile on each file

**Checkpoint**: SC-005 verified — all Pydantic schemas use Decimal.

---

## Phase 7: User Story 5 — Audit Trail Columns on All Sales Tables (Priority: P2)

**Goal**: Already handled in Phase 2 foundational tasks (T002–T013). This phase is a verification pass.

**Independent Test**: Inspect database.py for all 10 sales tables; each must have all four audit columns.

- [X] T107 [US5] Verify all audit column additions from T004–T013 are complete — run grep for each of the 10 tables in database.py; confirm all four columns present in each; verify AuditMixin additions from T002 are correct in sales_rfq.py

**Checkpoint**: SC-006 verified — all sales tables have complete audit columns.

---

## Phase 8: User Story 6 — Fiscal Period Validation on GL-Posting Endpoints (Priority: P2)

**Goal**: Verify all existing fiscal checks are correct and check if delivery_orders.py or orders.py need fiscal checks.

**Independent Test**: Search each GL-posting endpoint for `check_fiscal_period_open` call before any GL/journal entry creation.

- [X] T108 [US6] Verify fiscal period check in `backend/routers/sales/invoices.py` at line 194 — confirm check_fiscal_period_open is called before GL posting block
- [X] T109 [P] [US6] Verify fiscal period checks in `backend/routers/sales/credit_notes.py` at lines 195-197 and 538-540 — confirm both credit note and debit note paths have fiscal check before GL posting
- [X] T110 [P] [US6] Verify fiscal period check in `backend/routers/sales/returns.py` at lines 104-105 — confirm check is placed before GL reversal
- [X] T111 [P] [US6] Verify fiscal period checks in `backend/routers/sales/vouchers.py` at lines 34-36 and 266-268 — confirm both receipt and payment paths have fiscal check
- [X] T112 [US6] Check if `backend/routers/delivery_orders.py` creates GL entries — if yes, add `check_fiscal_period_open()` before GL posting; if no GL posting, document why fiscal check is not needed
- [X] T113 [US6] Check if `backend/routers/sales/orders.py` creates GL entries on order confirmation — if yes, add fiscal check; if no (orders are non-financial until invoiced), document

**Checkpoint**: SC-007 verified — all GL-posting endpoints have fiscal period validation.

---

## Phase 9: User Story 7 — Correct Display Formatting in Sales Frontend (Priority: P2)

**Goal**: Ensure all monetary values in sales pages use `formatNumber()` for display instead of raw `.toLocaleString()`.

**Independent Test**: `grep -rn "toLocaleString\|\.toFixed" frontend/src/pages/Sales/ frontend/src/pages/CPQ/ | wc -l` → ideally 0 for monetary display

- [X] T114 [US7] Audit all 34 Sales JSX files for raw `.toLocaleString()` or `.toFixed()` on monetary values — replace with `formatNumber()` from `../../utils/format`; add import if missing; this can be done alongside US2/US3 edits for efficiency

**Checkpoint**: All monetary display values use `formatNumber()`.

---

## Phase 10: User Story 8 — CPQ Pricing Engine Numeric Correctness (Priority: P2)

**Goal**: Ensure CPQ service uses Decimal for computation and str for serialization.

**Independent Test**: `grep -rn "float(" backend/services/cpq_service.py | wc -l` → must return 0

- [X] T115 [US8] Already covered by T028 (cpq_service.py float→str) and T064–T067 (CPQ frontend parseFloat). Verify CPQ pricing calculations use `Decimal` for intermediate math — if `cpq_service.py` contains arithmetic operations, ensure they use `Decimal` not `float` for computation

**Checkpoint**: CPQ pricing engine is numerically correct.

---

## Phase 11: User Story 9 — Delivery Order Audit Completeness (Priority: P3)

**Goal**: Delivery orders have correct numeric types, audit columns, and error handling.

**Independent Test**: Verify delivery_orders.py has str() serialization, DeliveryOrderForm.jsx uses String() payloads, DeliveryOrders.jsx uses showToast.

- [X] T116 [US9] Already covered by T027 (delivery_orders.py float→str), T052–T054 (frontend parseFloat), T090–T092 (frontend toast). Verify completeness of delivery order audit — confirm all three files are correct after prior phases

**Checkpoint**: Delivery orders are fully audit-compliant.

---

## Phase 12: User Story 10 — Contract and Commission Numeric Precision (Priority: P3)

**Goal**: Fix commission calculation to use Decimal arithmetic and verify functional correctness.

**Independent Test**: Commission of 7.5% on invoice total 10000.00 = exactly 750.00.

- [X] T117 [US10] Fix commission calculation logic in `backend/routers/sales/sales_improvements.py` — replace `float(rule.rate)` with `Decimal(str(rule.rate))`; replace `float(getattr(inv, ...))` with `Decimal(str(...))`; replace `round(total * rate / 100, 2)` with `(total * rate / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)`; add `from decimal import Decimal, ROUND_HALF_UP` import
- [X] T118 [US10] Verify commission functional correctness — manually trace: invoice_total=10000, rate=7.5 → commission must be exactly Decimal("750.00"); verify str() serialization of commission_amount in INSERT statement

**Checkpoint**: Commission calculation uses Decimal arithmetic and produces correct results. SC-010 partially verified.

---

## Phase 13: User Story 11 — Customer Groups and Pricing Lists (Priority: P3)

**Goal**: Customer group discount percentages use correct types.

**Independent Test**: Verify CustomerGroups.jsx sends discount as String(), backend stores/returns as str/Decimal.

- [X] T119 [US11] Already covered by T050 (CustomerGroups.jsx parseFloat→Number/String) and T018 (customers.py float→str). Verify discount percentage handling is correct — confirm String() in frontend payload and str() in backend response for discount_percentage fields

**Checkpoint**: Customer group discounts use correct types.

---

## Phase 14: User Story 12 — Sales Pipeline Flow Integrity (Priority: P3)

**Goal**: Verify the full quote→order→invoice→delivery pipeline preserves numeric precision end-to-end.

**Independent Test**: Trace a value through quotation → order → invoice → delivery in the code; confirm no float conversion at any stage.

- [X] T120 [US12] Trace numeric values through the conversion pipeline: verify `backend/routers/sales/quotations.py` conversion-to-order logic uses str() for amounts; verify `backend/routers/sales/orders.py` conversion-to-invoice logic uses str(); verify `backend/routers/sales/invoices.py` delivery creation uses str() — if any float() calls remain in conversion logic, fix them

**Checkpoint**: SC-010 fully verified — full pipeline preserves exact numeric values.

---

## Phase 15: Polish & Cross-Cutting Concerns

**Purpose**: Final verification across all user stories

- [X] T121 Run `py_compile` on ALL modified backend files — `backend/routers/sales/customers.py`, `quotations.py`, `orders.py`, `invoices.py`, `returns.py`, `credit_notes.py`, `vouchers.py`, `cpq.py`, `sales_improvements.py`, `schemas.py`, `backend/routers/delivery_orders.py`, `backend/services/cpq_service.py`, `backend/schemas/sales_credit_notes.py`, `backend/schemas/sales_improvements.py`, `backend/schemas/cpq.py`, `backend/models/domain_models/sales_rfq.py`, `backend/database.py`
- [X] T122 Run `npx vite build` in `frontend/` directory — verify zero build errors
- [X] T123 Run full violation count verification — `grep -rn "float(" backend/routers/sales/ backend/routers/delivery_orders.py backend/services/cpq_service.py` → 0; `grep -rn "parseFloat" frontend/src/pages/Sales/ frontend/src/pages/CPQ/` → 0; `grep -rn "console\.error" frontend/src/pages/Sales/ frontend/src/pages/CPQ/` → 0; `grep -rn "toastEmitter" frontend/src/pages/Sales/ frontend/src/pages/CPQ/` → 0
- [X] T124 Verify ZATCA boundary precision — check that any calls from sales routers to `utils/zatca.py` pass string/Decimal values, not float

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — verification only
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user stories
- **Phases 3–5 (US1, US2, US3)**: All depend on Phase 2; can run in PARALLEL with each other (different file layers: backend routers vs frontend parseFloat vs frontend toast)
- **Phase 6 (US4)**: Verification only — depends on Phase 2 completion
- **Phase 7 (US5)**: Verification only — depends on Phase 2 completion
- **Phase 8 (US6)**: Independent of US1–US5; can run in parallel
- **Phase 9 (US7)**: Can run alongside US2/US3 (same frontend files)
- **Phase 10 (US8)**: Depends on US1 (T028) and US2 (T064–T067)
- **Phase 11 (US9)**: Depends on US1 (T027), US2 (T052–T054), US3 (T090–T092)
- **Phase 12 (US10)**: Independent; can run after Phase 2
- **Phase 13 (US11)**: Depends on US1 (T018), US2 (T050)
- **Phase 14 (US12)**: Depends on US1 (all backend files fixed)
- **Phase 15 (Polish)**: Depends on ALL prior phases

### Parallel Opportunities

**Maximum parallelism** (after Phase 2):
- **Stream A** (Backend): T018–T029 (US1 — all backend files, all [P])
- **Stream B** (Frontend parseFloat): T030–T067 (US2 — all frontend files, all [P])
- **Stream C** (Frontend toast): T068–T105 (US3 — all frontend files, all [P])
- **Stream D** (Fiscal verification): T108–T113 (US6 — independent)
- **Stream E** (Commission fix): T117–T118 (US10 — independent)

### Within Each Frontend File

US2 and US3 tasks for the same file can be combined into a single edit session for efficiency:
- Example: `InvoiceForm.jsx` → T030 (parseFloat) + T068 (toast) done together
- But tracked as separate tasks for audit traceability

---

## Implementation Strategy

### MVP: Phase 1 + Phase 2 + Phase 3 (US1)
Backend numeric precision — the highest-impact, lowest-risk change. Delivers SC-001.

### Second increment: Phase 4 (US2) + Phase 5 (US3)
Frontend fixes — high volume (38 files × 2 task types) but mechanical. Delivers SC-002, SC-003, SC-004.

### Third increment: Phase 6–14 (US4–US12)
Verification passes and commission fix. Mostly confirmation that earlier phases are complete.

### Final: Phase 15 (Polish)
Full verification sweep — py_compile, vite build, grep counts.

### Total Task Count: 124
- Phase 1: 1 task
- Phase 2: 16 tasks (foundational)
- Phase 3 (US1): 12 tasks (backend float→str)
- Phase 4 (US2): 38 tasks (frontend parseFloat)
- Phase 5 (US3): 38 tasks (frontend toast)
- Phase 6 (US4): 1 task (verification)
- Phase 7 (US5): 1 task (verification)
- Phase 8 (US6): 6 tasks (fiscal checks)
- Phase 9 (US7): 1 task (formatNumber)
- Phase 10 (US8): 1 task (CPQ verification)
- Phase 11 (US9): 1 task (delivery verification)
- Phase 12 (US10): 2 tasks (commission fix + verify)
- Phase 13 (US11): 1 task (customer groups verification)
- Phase 14 (US12): 1 task (pipeline trace)
- Phase 15: 4 tasks (polish)
