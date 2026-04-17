# Tasks: Audit Purchases Module — تدقيق وحدة المشتريات

**Input**: Design documents from `/specs/011-audit-purchases/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Not requested — no test tasks included.

**Organization**: Tasks grouped by user story. US10 (Pydantic schemas) and US11 (audit columns) are foundational prerequisites placed in Phase 2 since they block or support all other stories.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Verify working environment and baseline

- [X] T001 Verify branch `011-audit-purchases` is checked out, Python venv active, and `npm install` completed in `frontend/`

---

## Phase 2: Foundational — Pydantic Schemas (US10) + Audit Columns (US11)

**Purpose**: Schema type safety (API boundary) and database audit trail completeness. These MUST complete before user story implementation begins.

**⚠️ CRITICAL**: Pydantic float→Decimal changes must land first — they ensure the validation pipeline enforces precision from the API boundary. Audit columns are independent but should be done early.

### Pydantic Schema Decimal Enforcement (US10)

- [X] T002 [P] Change 16 `float` fields to `Decimal` in `backend/schemas/purchases.py` — PurchaseLineItem (quantity, unit_price, tax_rate, discount, markup), PurchaseCreate (paid_amount, effect_percentage, markup_amount, exchange_rate), SupplierGroupCreate (discount_percentage), POCreate (effect_percentage, markup_amount, exchange_rate), ReceiveItem (received_quantity), PaymentAllocationSchema (allocated_amount), SupplierPaymentCreate (amount). Add `from decimal import Decimal` import.
- [X] T003 [P] Change 12 `float` fields to `Decimal` in `backend/schemas/matching.py` — MatchToleranceCreate (4 fields), MatchToleranceRead (4 fields), ThreeWayMatchLineRead (4 fields). Add `from decimal import Decimal` import.
- [X] T004 [P] Change 4 `float` fields to `Decimal` in inline `ToleranceSave` schema at `backend/routers/matching.py` L39-42 — quantity_percent, quantity_absolute, price_percent, price_absolute. Add `from decimal import Decimal` import.

### Audit Column Completeness (US11)

- [X] T005 [P] Create Alembic migration `add_purchases_audit_columns.py` in `backend/migrations/` using `ADD COLUMN IF NOT EXISTS` for all missing columns across 11 procurement tables: purchase_orders (updated_by), purchase_order_lines (updated_at, created_by, updated_by), request_for_quotations (updated_by), rfq_lines (all 4), rfq_responses (created_at, updated_at, created_by, updated_by), supplier_ratings (created_at, updated_at, updated_by), purchase_agreements (updated_at, updated_by), purchase_agreement_lines (all 4), landed_costs (updated_by), landed_cost_items (updated_at, created_by, updated_by), landed_cost_allocations (updated_at, created_by, updated_by)
- [X] T006 [P] Update `backend/database.py` CREATE TABLE definitions for all 11 tables to include missing audit columns — match exact column specs from data-model.md: `created_at TIMESTAMP DEFAULT NOW()`, `updated_at TIMESTAMP DEFAULT NOW()`, `created_by INTEGER REFERENCES users(id)`, `updated_by INTEGER REFERENCES users(id)`
- [X] T007 Add `AuditMixin` to 8 domain models: PurchaseOrder + PurchaseOrderLine in `backend/models/domain_models/procurement_orders.py`, LandedCost + LandedCostItem + PurchaseAgreement + PurchaseAgreementLine in `backend/models/domain_models/procurement_costs.py`, SupplierRating in `backend/models/domain_models/procurement_suppliers.py`, LandedCostAllocation in `backend/models/domain_models/shared_dashboard_fiscal_intercompany.py` — change from `ModelBase` to `ModelBase, AuditMixin` and add `from models.base import AuditMixin` import if missing

**Checkpoint**: Foundational phase complete — all Pydantic schemas enforce Decimal, all procurement tables have full audit columns. User story implementation can begin.

---

## Phase 3: User Story 1 — Purchase Order CRUD (Priority: P1) 🎯 MVP

**Goal**: All PO creation, listing, editing, and submission operations use Decimal/str precision and proper toast error handling.

**Independent Test**: Create a PO with 3 line items → verify API returns all monetary values as strings → verify frontend sends values as strings → verify toast errors on failures → verify amounts render via `formatNumber()`.

- [X] T008 [US1] Replace all `float()` → `str()` in PO-related functions in `backend/routers/purchases.py` — PO CRUD, listing, and submission functions covering lines L402-403, L406, L431, L449, L473-477, L536. Preserve inner expressions (e.g., `float(_dec(x))` → `str(_dec(x))`).
- [X] T009 [US1] Replace 22 `parseFloat()` calls in `frontend/src/pages/Buying/BuyingOrderForm.jsx` — payload construction (L225-228): use `String(value)`, local calculations (L89-92, L95, L111, L139-146, L168-171, L297-300): use `Number(value)`. Add `useToast` import and replace any `console.error` with `showToast()`.
- [X] T010 [P] [US1] Migrate `toastEmitter` → `useToast` in `frontend/src/pages/Buying/BuyingOrders.jsx` — remove toastEmitter import, add `import { useToast } from '../../context/ToastContext'`, destructure `const { showToast } = useToast()`, replace all `toastEmitter.emit()` with `showToast()`.
- [X] T011 [P] [US1] Add `useToast` and replace `console.error` with `showToast()` in `frontend/src/pages/Buying/BuyingOrderDetails.jsx` and `frontend/src/pages/Buying/BuyingHome.jsx`.

**Checkpoint**: PO CRUD is fully functional with Decimal precision, string serialization, and toast error handling.

---

## Phase 4: User Story 2 — Purchase Invoices (Priority: P1)

**Goal**: Invoice creation, listing, and detail display use Decimal precision with string serialization. Fiscal period check already exists (L1157) — no addition needed.

**Independent Test**: Create a purchase invoice → verify response amounts are strings → verify frontend sends amounts as strings → verify toast errors on failures.

- [X] T012 [US2] Replace all `float()` → `str()` in invoice-related functions in `backend/routers/purchases.py` — covering lines L1088, L1090, L1102-1103, L1297, L1309.
- [X] T013 [US2] Replace 18 `parseFloat()` calls in `frontend/src/pages/Purchases/PurchaseInvoiceForm.jsx` — payload (L288, L291, L301-304, L316-318): use `String()`, local calc (L83-85, L93, L139, L218-221, L224, L236): use `Number()`. Add `useToast` import and replace `console.error` with `showToast()`.
- [X] T014 [P] [US2] Add `useToast` and replace `console.error` with `showToast()` in `frontend/src/pages/Purchases/PurchaseInvoiceList.jsx` and `frontend/src/pages/Purchases/PurchaseInvoiceDetails.jsx`.

**Checkpoint**: Purchase invoices are fully functional with Decimal precision, string serialization, and toast error handling.

---

## Phase 5: User Story 3 — PO Receiving / GRN (Priority: P1)

**Goal**: GRN operations use Decimal precision and enforce fiscal period validation before GL posting.

**Independent Test**: Receive 50 units against a PO line → verify fiscal period is checked → verify inventory updates → verify GL entry posts → verify all quantities in response are strings.

- [X] T015 [US3] Replace `float()` → `str()` in `receive_purchase_order` function in `backend/routers/purchases.py` (L829, L907-909) AND add `check_fiscal_period_open(db, date_value)` call before GL posting at L869 — following the existing pattern from `create_purchase_invoice` (L1157).
- [X] T016 [US3] Replace `parseFloat()` calls and migrate `toastEmitter` → `useToast` in `frontend/src/pages/Buying/PurchaseOrderReceive.jsx` — remove toastEmitter import, add useToast, replace all `toastEmitter.emit()` and `console.error` with `showToast()`, replace parseFloat with `String()`/`Number()` as appropriate.
- [X] T017 [P] [US3] Migrate `toastEmitter` → `useToast` in `frontend/src/pages/Buying/PurchaseOrderDetails.jsx` — remove toastEmitter import, add useToast hook, replace all `toastEmitter.emit()` calls with `showToast()`.

**Checkpoint**: GRN operations enforce fiscal period, use Decimal precision, and show toast errors.

---

## Phase 6: User Story 4 — Purchase Returns (Priority: P1)

**Goal**: Purchase returns enforce fiscal period validation, use Decimal precision, and display proper toast errors.

**Independent Test**: Create a return for 10 units → verify fiscal period is checked before GL posting → verify response amounts are strings → verify frontend sends quantities as strings → verify toast errors.

- [X] T018 [US4] Replace `float()` → `str()` in return-related functions in `backend/routers/purchases.py` (L2677 area) AND add `check_fiscal_period_open(db, date_value)` call before GL posting at L1913 in `create_purchase_return` — hard block HTTP 400 on closed period.
- [X] T019 [US4] Replace 11 `parseFloat()` calls in `frontend/src/pages/Buying/BuyingReturnForm.jsx` — payload (L232-235): use `String()`, local calc (L157, L169-172, L175): use `Number()`. Migrate `toastEmitter` → `useToast` — remove toastEmitter import, add useToast, replace all emit calls with `showToast()`.
- [X] T020 [P] [US4] Add `useToast` and replace `console.error` with `showToast()` in `frontend/src/pages/Buying/BuyingReturnDetails.jsx` and `frontend/src/pages/Buying/BuyingReturns.jsx`.

**Checkpoint**: Purchase returns enforce fiscal period, use Decimal precision, and show toast errors.

---

## Phase 7: User Story 5 — Credit Notes & Debit Notes (Priority: P1)

**Goal**: Credit/debit notes enforce fiscal period validation and use Decimal precision with string serialization.

**Independent Test**: Create a credit note → verify fiscal period checked → verify GL entry posts → create a debit note → verify fiscal period checked → verify all amounts are strings → verify toast errors on failures.

- [X] T021 [US5] Replace `float()` → `str()` in credit note and debit note functions in `backend/routers/purchases.py` (L2927 area) AND add `check_fiscal_period_open(db, date_value)` before GL posting at L2644 (`create_purchase_credit_note`) and at L2902 (`create_purchase_debit_note`) — hard block HTTP 400 on closed period.
- [X] T022 [P] [US5] Replace `parseFloat()` calls and fix remaining `console.error` → `showToast()` in `frontend/src/pages/Purchases/PurchaseCreditNotes.jsx` (already has useToast — 4 parseFloat, 4 console.error to fix).
- [X] T023 [P] [US5] Replace `parseFloat()` calls and fix remaining `console.error` → `showToast()` in `frontend/src/pages/Purchases/PurchaseDebitNotes.jsx` (already has useToast — 4 parseFloat, 4 console.error to fix).

**Checkpoint**: Credit/debit notes enforce fiscal period, use Decimal precision, and show toast errors.

---

## Phase 8: User Story 6 — Suppliers (Priority: P2)

**Goal**: All supplier-related pages (CRUD, statements, payments, groups, ratings) use proper toast errors, string-based amounts, and `formatNumber()` display.

**Independent Test**: View supplier statement → verify running balance rendered via `formatNumber()` → process a payment → verify amounts sent as strings → verify all pages show toast on errors.

- [X] T024 [US6] Replace `float()` → `str()` in supplier/payment/statement functions in `backend/routers/purchases.py` — covering lines L3086, L3154 and any supplier-related float() calls in the L3000-3260 range.
- [X] T025 [US6] Migrate `toastEmitter` → `useToast` in `frontend/src/pages/Buying/SupplierGroups.jsx` (fix parseFloat if present) and `frontend/src/pages/Purchases/SupplierPayments.jsx` and `frontend/src/pages/Purchases/PaymentForm.jsx` (replace 7 parseFloat, migrate toastEmitter) — remove toastEmitter imports, add useToast, replace all emit calls and console.error with `showToast()`.
- [X] T026 [P] [US6] Fix remaining `console.error` → `showToast()` in `frontend/src/pages/Buying/SupplierForm.jsx` and `frontend/src/pages/Buying/SupplierRatings.jsx` (both already have useToast). Add `useToast` and replace `console.error` in `frontend/src/pages/Buying/SupplierDetails.jsx`, `frontend/src/pages/Buying/SupplierList.jsx`, `frontend/src/pages/Buying/SupplierStatement.jsx`, `frontend/src/pages/Purchases/PaymentDetails.jsx`, and `frontend/src/pages/Buying/SupplierPayments.jsx`.

**Checkpoint**: All supplier pages use useToast, string amounts, and formatNumber display.

---

## Phase 9: User Story 7 — Three-Way Matching (Priority: P2)

**Goal**: Matching router, service, and frontend use Decimal precision with string serialization throughout the validation pipeline.

**Independent Test**: Configure tolerances → run a three-way match → verify all match line values are strings → verify tolerance saves as strings → verify toast errors on failures.

- [X] T027 [US7] Replace 13 `float()` → `str()` in `backend/routers/matching.py` (L170-178, L270-273) — preserve inner Decimal expressions.
- [X] T028 [P] [US7] Replace 2 `float()` → `str()` in `backend/services/matching_service.py` (L196-197) — variance output serialization only, internal Decimal computation remains unchanged.
- [X] T029 [US7] Fix `parseFloat()` → `String()`/`Number()` in `frontend/src/pages/Matching/ToleranceConfig.jsx` (4 calls, already has useToast). Fix remaining `console.error` in `frontend/src/pages/Matching/MatchDetail.jsx` (already has useToast). Add `useToast` and replace `console.error` in `frontend/src/pages/Matching/MatchList.jsx`.

**Checkpoint**: Three-way matching uses Decimal precision end-to-end with string serialization.

---

## Phase 10: User Story 8 — Landed Costs (Priority: P2)

**Goal**: Landed cost allocation uses Decimal precision with largest-remainder rounding. No new fiscal check needed (already present at L357).

**Independent Test**: Create a landed cost with 3 items → allocate to 3 PO lines → verify allocations sum exactly to total (largest-remainder rounding) → verify all amounts are strings → verify toast errors.

- [X] T030 [US8] Replace 6 `float()` → `str()` in `backend/routers/landed_costs.py` (L193, L311-312, L322, L464, L470) AND implement largest-remainder rounding in allocation logic (L280-312): after computing all `share = Decimal(...)` values with `quantize()`, compare `sum(shares)` vs `total_cost` and add/subtract the remainder to the largest share line.
- [X] T031 [P] [US8] Fix any remaining `console.error` patterns in `frontend/src/pages/Purchases/LandedCosts.jsx` and `frontend/src/pages/Purchases/LandedCostDetails.jsx` (both already have useToast) — replace with `showToast()`.

**Checkpoint**: Landed cost allocations are precise with correct rounding and string serialization.

---

## Phase 11: User Story 9 — RFQ, Agreements & Blanket POs (Priority: P3)

**Goal**: RFQ, purchase agreements, and blanket PO pages use Decimal precision, string serialization, and toast errors.

**Independent Test**: Create RFQ → convert to PO → verify amounts preserved as strings → create agreement → release against it → verify consumed/remaining as strings → verify frontend uses `formatNumber()`.

- [X] T032 [US9] Replace `float()` → `str()` in RFQ, agreement, and blanket PO functions in `backend/routers/purchases.py` — covering lines L3264, L3268, L3309-3311, L3381-3382, L3405-3406, L3481, L3496-3497, L3514-3515, L3522, L3528-3531, L3571-3572, L3584-3585, L3594, L3600-3603.
- [X] T033 [P] [US9] Fix remaining `console.error` and `parseFloat()` in `frontend/src/pages/Buying/RFQList.jsx` and `frontend/src/pages/Purchases/PurchaseAgreements.jsx` (both already have useToast) — replace console.error with `showToast()`, replace parseFloat with `String()`/`Number()`.
- [X] T034 [P] [US9] Fix `parseFloat()` in `frontend/src/pages/BlanketPO/BlanketPOForm.jsx` (4 calls, already has useToast — fix console.error too), `frontend/src/pages/BlanketPO/BlanketPODetail.jsx` (2 parseFloat, already has useToast), and `frontend/src/pages/BlanketPO/BlanketPOList.jsx` (fix console.error, already has useToast).

**Checkpoint**: All RFQ, agreement, and blanket PO workflows use Decimal precision and toast errors.

---

## Phase 12: User Story 12 — Reports & Aging (Priority: P2)

**Goal**: Purchase report pages display amounts via `formatNumber()` and show toast errors on failures.

**Independent Test**: Open purchases aging report → verify amounts rendered via `formatNumber()` → trigger error → verify toast appears.

- [X] T035 [P] [US12] Add `useToast` and replace `console.error` with `showToast()` in `frontend/src/pages/Buying/BuyingReports.jsx` and `frontend/src/pages/Purchases/PurchasesAgingReport.jsx` — ensure all monetary display values use `formatNumber()`.

**Checkpoint**: All report pages display precise amounts and show toast errors.

---

## Phase 13: Polish & Verification

**Purpose**: Validate all changes compile and no violations remain.

- [X] T036 Run `python3 -m py_compile` on all modified backend files: `backend/routers/purchases.py`, `backend/routers/landed_costs.py`, `backend/routers/matching.py`, `backend/services/matching_service.py`, `backend/schemas/purchases.py`, `backend/schemas/matching.py`, `backend/database.py`, and all modified domain model files — fix any syntax errors
- [X] T037 Run `cd frontend && npx vite build` — fix any compilation errors until build succeeds with zero errors
- [X] T038 Run grep verification to confirm zero remaining violations: `grep -rn "float(" backend/routers/purchases.py backend/routers/landed_costs.py backend/routers/matching.py backend/services/matching_service.py`, `grep -rn "parseFloat" frontend/src/pages/Buying/ frontend/src/pages/Purchases/ frontend/src/pages/Matching/ frontend/src/pages/BlanketPO/`, `grep -rn "toastEmitter" frontend/src/pages/Buying/ frontend/src/pages/Purchases/ frontend/src/pages/Matching/ frontend/src/pages/BlanketPO/` — fix any remaining violations found

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — **BLOCKS all user stories**
  - T002, T003, T004 (schemas) can run in parallel
  - T005, T006 can run in parallel with schemas
  - T007 depends on T006 (database.py defines the structure, models must match)
- **User Stories (Phases 3-12)**: All depend on Phase 2 completion
  - P1 stories (US1-US5) should execute sequentially for single-developer workflow
  - P2 stories (US6-US8, US12) can start after Phase 2 if parallelized
  - P3 story (US9) can start after Phase 2
- **Polish (Phase 13)**: Depends on ALL user stories being complete

### User Story Dependencies

| Story | Phase | Can start after | Notes |
|-------|-------|----------------|-------|
| US1 (PO CRUD) | 3 | Phase 2 | 🎯 MVP — No dependencies on other stories |
| US2 (Invoices) | 4 | Phase 2 | Independent of US1 |
| US3 (GRN) | 5 | Phase 2 | Independent but logically follows PO (US1) |
| US4 (Returns) | 6 | Phase 2 | Independent but logically follows GRN (US3) |
| US5 (CN/DN) | 7 | Phase 2 | Independent but logically follows Invoices (US2) |
| US6 (Suppliers) | 8 | Phase 2 | Fully independent |
| US7 (Matching) | 9 | Phase 2 | Fully independent |
| US8 (Landed Costs) | 10 | Phase 2 | Fully independent |
| US9 (RFQ/Agreements) | 11 | Phase 2 | Fully independent |
| US12 (Reports) | 12 | Phase 2 | Fully independent |

### Within Each User Story

- Backend changes before frontend changes (API contract must be stable)
- Router float→str before frontend parseFloat fixes
- Fiscal period checks alongside float→str (same file, same function)
- Frontend files marked [P] within a story can run in parallel

### Parallel Opportunities

- **Phase 2**: T002 ‖ T003 ‖ T004 ‖ T005 ‖ T006 (5 tasks in parallel)
- **Each story**: Backend task → Frontend tasks (marked [P]) in parallel
- **Across stories**: All user stories are independent after Phase 2 — can be parallelized if staffing allows

---

## Parallel Example: User Story 7 (Matching)

```text
Sequential:  T027 ──────── T028 ──────── T029
                                         
Parallel:    T027 ─── T029
             T028 ───┘
             (T027 ‖ T028 → then T029)
```

```text
Sequential:  ~3 tasks × 1 unit = 3 units
Parallel:    2 units (T027 ‖ T028, then T029)
```

---

## Implementation Strategy

### MVP Scope
- **Phase 1 + Phase 2 + Phase 3 (US1)** = Minimum viable delivery
- Proves the pattern works end-to-end for PO CRUD
- Total: 12 tasks (T001-T011)

### Incremental Delivery
- After MVP: Add P1 stories one at a time (US2 → US3 → US4 → US5)
- Then P2 stories (US6, US7, US8, US12) — order flexible
- Finally P3 story (US9)
- Each story is independently testable after completion

### Key Risk: purchases.py Size
- The file is 3600+ lines with 55 float() calls across multiple functions
- Each story's backend task targets specific function ranges
- Use the line numbers from research.md as guides — verify before each edit since prior edits may shift line numbers

### Key Pattern Reference
```python
# Backend: float() → str()
# Before: "total": float(_dec(r.total).quantize(_D2))
# After:  "total": str(_dec(r.total).quantize(_D2))

# Fiscal period check (add before GL posting):
check_fiscal_period_open(db, transaction_date)
```
```javascript
// Frontend: parseFloat → String (payload) / Number (calc)
// Before: quantity: parseFloat(item.quantity) || 0,
// After:  quantity: String(item.quantity || 0),

// Frontend: console.error / toastEmitter → useToast
// Add: import { useToast } from '../../context/ToastContext'
// Add: const { showToast } = useToast()
// Replace: showToast(err.response?.data?.detail || t('common.error'), 'error')
```
