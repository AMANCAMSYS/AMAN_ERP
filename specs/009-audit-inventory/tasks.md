# Tasks: Audit Inventory Module — تدقيق وحدة المخزون

**Input**: Design documents from `/specs/009-audit-inventory/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/api-changes.md, quickstart.md

**Tests**: Not requested — no test tasks included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing. This is a code-audit feature — no new endpoints or pages, only fixes to existing code.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup

**Purpose**: Create the audit column migration — the only structural change in this audit.

- [x] T001 Create Alembic migration for missing audit columns in backend/migrations/add_inventory_audit_columns.py — add `created_by`, `updated_at`, `updated_by` to `product_categories` and `updated_at`, `updated_by` to `stock_adjustments` (Constitution §XVII)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Update schema definitions and domain models to match the migration. Must complete before user story work to keep §XXVIII triple-update atomic.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T002 Update database.py CREATE TABLE definitions for `product_categories` (add `created_by INTEGER REFERENCES company_users(id)`, `updated_at TIMESTAMPTZ`, `updated_by INTEGER REFERENCES company_users(id)`) and `stock_adjustments` (add `updated_at TIMESTAMPTZ`, `updated_by INTEGER REFERENCES company_users(id)`) in backend/database.py
- [x] T003 [P] Update domain model classes for `product_categories` and `stock_adjustments` to include the new audit columns in backend/models/domain_models/inventory_core.py

**Checkpoint**: Migration + database.py + model in sync (§XXVIII). User story implementation can now begin.

---

## Phase 3: User Story 1 — Product CRUD, Cost Display & Stock Visibility (Priority: P1) 🎯 MVP

**Goal**: Fix float precision violations in product API responses and standardize error handling on product/category pages.

**Independent Test**: Create a product with selling_price 1250.75 → verify API returns `"1250.7500"` (string, not `1250.75` float) → verify ProductForm shows toast on error (not console.error) → verify CategoryList shows toast on error.

### Implementation for User Story 1

- [x] T004 [US1] Fix 9 float→str conversions in backend/routers/inventory/products.py at lines 37, 54, 55, 138, 139, 140, 141, 144, 145, 207 — change `float(row.field or 0)` → `str(row.field or 0)` for selling_price, cost_price, buying_price, last_buying_price, tax_rate, current_stock, reserved_quantity, average_cost, total_qty
- [x] T005 [P] [US1] Fix 2 parseFloat violations in frontend/src/pages/Stock/ProductForm.jsx — L106: replace parseFloat VAT calc with `Number()` for local comparison; L165: replace `parseFloat()` with `Number()` for local comparison
- [x] T006 [P] [US1] Add useToast error handling in frontend/src/pages/Stock/ProductForm.jsx — import `useToast` from `../../context/ToastContext`, replace any `console.error`-only patterns with `showToast(err.response?.data?.detail || t('stock.products.error'), 'error')`
- [x] T007 [P] [US1] Add useToast error handling in frontend/src/pages/Stock/CategoryList.jsx — import `useToast` from `../../context/ToastContext`, replace any `console.error`-only patterns with `showToast()` calls

**Checkpoint**: Product CRUD returns string monetary values, ProductForm/CategoryList show toast errors.

---

## Phase 4: User Story 2 — Stock Movements (Priority: P1)

**Goal**: Fix float precision in movement API responses and standardize error handling on the movements page.

**Independent Test**: Create a stock receipt → verify API returns `unit_cost` and `quantity` as strings → view Stock Movements page → trigger an error → verify toast appears.

### Implementation for User Story 2

- [x] T008 [US2] Fix 2 float→str conversions in backend/routers/inventory/stock_movements.py at lines 51, 151 — change `float(row.unit_cost or 0)` → `str(row.unit_cost or 0)` and `float(row.quantity or 0)` → `str(row.quantity or 0)`
- [x] T009 [P] [US2] Add useToast error handling in frontend/src/pages/Stock/StockMovements.jsx — import `useToast` from `../../context/ToastContext`, replace any `console.error`-only patterns with `showToast()` calls

**Checkpoint**: Movement endpoints return string values, movements page shows toast errors.

---

## Phase 5: User Story 3 — Stock Transfers & Shipments Lifecycle (Priority: P1)

**Goal**: Fix parseFloat in transfer/shipment form payloads and standardize error handling on transfer/shipment pages.

**Independent Test**: Submit a stock transfer → verify API payload sends `quantity` as string (not number) → trigger a shipment error → verify toast appears on ShipmentList/ShipmentDetails.

### Implementation for User Story 3

- [x] T010 [US3] Fix parseFloat→String in frontend/src/pages/Stock/StockTransferForm.jsx at L100 — change `parseFloat(item.quantity)` → `String(item.quantity)` in the API payload
- [x] T011 [P] [US3] Fix parseFloat→String in frontend/src/pages/Stock/StockShipmentForm.jsx at L60 — change `parseFloat(currentItem.quantity)` → `String(currentItem.quantity)` in the API payload
- [x] T012 [P] [US3] Add useToast error handling in frontend/src/pages/Stock/StockTransferForm.jsx — import `useToast` from `../../context/ToastContext`, replace any `console.error`-only patterns with `showToast()` calls
- [x] T013 [P] [US3] Add useToast error handling in frontend/src/pages/Stock/ShipmentList.jsx — import `useToast`, replace `console.error`/`toastEmitter.emit()` with `showToast()` calls
- [x] T014 [P] [US3] Add useToast error handling in frontend/src/pages/Stock/ShipmentDetails.jsx — import `useToast`, replace `console.error`/`toastEmitter.emit()` with `showToast()` calls

**Checkpoint**: Transfer/shipment forms send string payloads, all transfer/shipment pages show toast errors.

---

## Phase 6: User Story 4 — Stock Adjustments with GL Posting (Priority: P1)

**Goal**: Fix parseFloat in adjustment form payload and standardize error handling on adjustment pages.

**Independent Test**: Submit a stock adjustment → verify API payload sends `new_quantity` as string → trigger an error on StockAdjustments list → verify toast appears.

### Implementation for User Story 4

- [x] T015 [US4] Fix parseFloat→String in frontend/src/pages/Stock/StockAdjustmentForm.jsx at L63 — change `parseFloat(formData.new_quantity)` → `String(formData.new_quantity)` in the API payload
- [x] T016 [P] [US4] Add useToast error handling in frontend/src/pages/Stock/StockAdjustmentForm.jsx — import `useToast`, replace any `console.error`-only patterns with `showToast()` calls
- [x] T017 [P] [US4] Add useToast error handling in frontend/src/pages/Stock/StockAdjustments.jsx — import `useToast`, replace any `console.error`-only patterns with `showToast()` calls

**Checkpoint**: Adjustment form sends string payload, both adjustment pages show toast errors.

---

## Phase 7: User Story 9 — Dead Notification Endpoints & Service Cleanup (Priority: P1)

**Goal**: Remove 4 dead notification functions from the inventory service that call unmounted backend endpoints (404).

**Independent Test**: Verify no frontend file imports `getNotifications`, `getUnreadCount`, `markNotificationRead`, or `markAllNotificationsRead` from inventory service → verify `vite build` succeeds after removal.

### Implementation for User Story 9

- [x] T018 [US9] Remove 4 dead notification functions (`getNotifications`, `getUnreadCount`, `markNotificationRead`, `markAllNotificationsRead`) from frontend/src/services/inventory.js — these have zero callers and hit unmounted 404 endpoints

**Checkpoint**: No dead notification code in inventory service. Build succeeds.

---

## Phase 8: User Story 5 — Batch & Serial Tracking (Priority: P2)

**Goal**: Fix parseFloat violations in batch list form payloads.

**Independent Test**: Create a batch with quantity "100" and unit_cost "45.50" → verify API payload sends these as strings → verify batch list renders correctly.

### Implementation for User Story 5

- [x] T019 [US5] Fix 3 parseFloat violations in frontend/src/pages/Stock/BatchList.jsx — L86: `parseFloat(form.quantity)` → `String(form.quantity)`; L87: `parseFloat(form.unit_cost)` → `String(form.unit_cost)` (payload); L146: `parseFloat()` display → `formatNumber()` or `Number()` for comparison

**Checkpoint**: Batch forms send string payloads.

---

## Phase 9: User Story 6 — Cycle Counts & Quality Inspections (Priority: P2)

**Goal**: Fix cycle count GL gap (Constitution §III), add negative stock check (§VIII), fix float/parseFloat violations in cycle count and QC endpoints/forms.

**Independent Test**: Complete a cycle count with variances → verify GL journal entries are posted (Dr/Cr based on surplus/shortage) → verify negative stock is hard-blocked → verify API returns cycle count values as strings → verify CycleCounts form sends `counted_quantity` as string.

### Implementation for User Story 6

- [x] T020 [US6] Fix 4 float→str conversions in backend/routers/inventory/batches.py at lines 1255, 1256, 1329, 1330 — change `float()` → `str()` for system_quantity, unit_cost, quantity, cost in cycle count item responses
- [x] T021 [P] [US6] Fix 5 parseFloat violations in frontend/src/pages/Stock/CycleCounts.jsx — L131: payload `parseFloat(item.counted_quantity)` → `String(item.counted_quantity)`; L407: comparison → `Number()`; L411, L419: display → `formatNumber()`
- [x] T022 [P] [US6] Fix 2 parseFloat violations in frontend/src/pages/Stock/QualityInspections.jsx — L108: `parseFloat(c.min_value)` → `String(c.min_value)`; L109: `parseFloat(c.max_value)` → `String(c.max_value)` in API payload
- [x] T023 [US6] Add GL journal entry posting to cycle count completion in backend/routers/inventory/batches.py (around L1305-1410) — follow adjustments.py pattern: check fiscal period open, build GL lines (surplus: Dr. Inventory Asset / Cr. Inventory Variance; shortage: reversed), call `gl_create_journal_entry()` for each variance with non-zero value
- [x] T024 [US6] Add negative stock check in cycle count auto-adjust in backend/routers/inventory/batches.py (around L1355) — before overwriting quantity, verify that the new counted_quantity minus reserved quantity is not negative; reject with 400 error if it would create negative available stock

**Checkpoint**: Cycle count completion posts GL entries, negative stock is blocked, all values returned/sent as strings.

---

## Phase 10: User Story 7 — Inventory Reports, Valuation & Dashboard (Priority: P2)

**Goal**: Fix float precision in report/warehouse API responses, fix parseFloat in forecast pages, and standardize error handling across all report/dashboard pages.

**Independent Test**: Open valuation report → verify `total_quantity`, `moving_avg_cost`, `total_valuation` are strings in API response → open StockHome → trigger error → verify toast appears → open ForecastDetail → verify no parseFloat artifacts.

### Implementation for User Story 7

- [x] T025 [US7] Fix 3 float→str conversions in backend/routers/inventory/reports.py at lines 303, 304, 305 — change `float()` → `str()` for total_quantity, moving_avg_cost, total_valuation
- [x] T026 [P] [US7] Fix 2 float→str conversions in backend/routers/inventory/warehouses.py at lines 172, 254 — change `float()` → `str()` for stock, quantity
- [x] T027 [P] [US7] Fix 10 parseFloat violations in frontend/src/pages/Forecast/ForecastDetail.jsx at lines 27, 45, 74, 111, 112, 113, 149, 150, 151, 163 — replace `parseFloat()` with `Number()` for local comparisons or `formatNumber()` for display rendering
- [x] T028 [P] [US7] Add useToast error handling in frontend/src/pages/Stock/StockHome.jsx — import `useToast`, replace `console.error`-only patterns with `showToast()` calls
- [x] T029 [P] [US7] Add useToast error handling in frontend/src/pages/Stock/StockReports.jsx — import `useToast`, replace `console.error`-only patterns with `showToast()` calls
- [x] T030 [P] [US7] Add useToast error handling in frontend/src/pages/Stock/InventoryValuation.jsx — import `useToast`, replace `console.error`-only patterns with `showToast()` calls
- [x] T031 [P] [US7] Add useToast error handling in frontend/src/pages/Stock/WarehouseList.jsx — import `useToast`, replace `console.error`-only patterns with `showToast()` calls
- [x] T032 [P] [US7] Add useToast error handling in frontend/src/pages/Forecast/ForecastDetail.jsx — import `useToast`, replace `console.error`-only patterns with `showToast()` calls
- [x] T033 [P] [US7] Add useToast error handling in frontend/src/pages/Forecast/ForecastList.jsx — import `useToast`, replace `console.error`-only patterns with `showToast()` calls
- [x] T034 [P] [US7] Add useToast error handling in frontend/src/pages/Forecast/ForecastGenerate.jsx — import `useToast`, replace `console.error`-only patterns with `showToast()` calls

**Checkpoint**: All report/dashboard/forecast pages return string monetary values and show toast errors.

---

## Phase 11: User Story 8 — Costing Methods, Price Lists & Advanced Features (Priority: P3)

**Goal**: Fix parseFloat in price list form and standardize error handling on price list pages.

**Independent Test**: Bulk-update a price list → verify API payload sends prices as strings → trigger error on PriceLists page → verify toast appears.

### Implementation for User Story 8

- [x] T035 [US8] Fix parseFloat→String in frontend/src/pages/Stock/PriceListItems.jsx at L43 — change `parseFloat(newPrice)` → `String(newPrice)` in the API payload
- [x] T036 [P] [US8] Add useToast error handling in frontend/src/pages/Stock/PriceLists.jsx — import `useToast`, replace `console.error`-only patterns with `showToast()` calls
- [x] T037 [P] [US8] Add useToast error handling in frontend/src/pages/Stock/PriceListItems.jsx — import `useToast`, replace `console.error`-only patterns with `showToast()` calls

**Checkpoint**: Price list pages send string payloads and show toast errors.

---

## Phase 12: Polish & Cross-Cutting Concerns

**Purpose**: Verify all changes compile and build correctly.

- [x] T038 Run `python -m py_compile` on all 5 modified backend router files (products.py, stock_movements.py, batches.py, reports.py, warehouses.py) and verify zero syntax errors
- [x] T039 Run `npx vite build` in frontend/ to verify all frontend changes compile without errors
- [x] T040 Run quickstart.md validation — verify start-local.sh succeeds and smoke-test product CRUD, stock movement, cycle count GL posting, and toast error display

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup (T001) — BLOCKS all user stories
- **User Stories (Phases 3–11)**: All depend on Foundational (Phase 2) completion
  - P1 stories (US1–US4, US9) can proceed in parallel or sequentially
  - P2 stories (US5–US7) can proceed in parallel after P1
  - P3 story (US8) can proceed after P2
- **Polish (Phase 12)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: No dependencies on other stories — MVP target
- **US2 (P1)**: No dependencies on other stories
- **US3 (P1)**: No dependencies on other stories
- **US4 (P1)**: No dependencies on other stories
- **US9 (P1)**: No dependencies on other stories
- **US5 (P2)**: Independent — batch forms only
- **US6 (P2)**: Independent — cycle count GL fix requires understanding adjustments.py pattern but no code dependency
- **US7 (P2)**: Independent — report/dashboard pages only
- **US8 (P3)**: Independent — price list pages only

### Within Each User Story

- Backend fixes before frontend fixes (API response format must change first for frontend to consume strings)
- parseFloat fixes and useToast fixes are independent within the same story (can run in parallel)
- All [P]-marked tasks within a story can run in parallel

### Parallel Opportunities

Within each phase, all tasks marked [P] can run in parallel. Example for Phase 10 (US7):

```text
# Sequential:
T025 Fix reports.py float→str

# Then parallel:
T026 Fix warehouses.py float→str
T027 Fix ForecastDetail.jsx parseFloat
T028 Add useToast in StockHome.jsx
T029 Add useToast in StockReports.jsx
T030 Add useToast in InventoryValuation.jsx
T031 Add useToast in WarehouseList.jsx
T032 Add useToast in ForecastDetail.jsx
T033 Add useToast in ForecastList.jsx
T034 Add useToast in ForecastGenerate.jsx
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Migration file (T001)
2. Complete Phase 2: database.py + model update (T002–T003)
3. Complete Phase 3: US1 — Product CRUD fixes (T004–T007)
4. **STOP and VALIDATE**: Verify products API returns strings, ProductForm/CategoryList show toasts
5. Deploy/demo if ready — products are the foundation

### Incremental Delivery

1. Setup + Foundational → Schema in sync
2. Add US1 (Products) → Test independently → Deploy (MVP!)
3. Add US2 (Movements) → Test independently → Deploy
4. Add US3 (Transfers/Shipments) → Test independently → Deploy
5. Add US4 (Adjustments) → Test independently → Deploy
6. Add US9 (Dead code cleanup) → Test independently → Deploy
7. Add US5 (Batches) → Test independently → Deploy
8. Add US6 (Cycle Counts + GL fix) → Test independently → Deploy ← Key constitutional fix
9. Add US7 (Reports/Dashboard) → Test independently → Deploy
10. Add US8 (Price Lists) → Test independently → Deploy
11. Polish → Final validation → Done

### Audit Scope Summary

| Category | Count | Files |
|----------|-------|-------|
| Backend float→str | 20 fixes | 5 router files |
| Frontend parseFloat→String/Number | 26 fixes | 8 page files |
| Frontend useToast standardization | 17 pages | 17 page files |
| Dead notification removal | 4 functions | 1 service file |
| Cycle count GL posting | 1 new GL call | 1 router file |
| Negative stock check | 1 new check | 1 router file |
| Audit column migration | 5 columns | 3 files (migration + database.py + model) |
| **Total tasks** | **40** | |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- No test tasks generated — tests were not requested in the specification
