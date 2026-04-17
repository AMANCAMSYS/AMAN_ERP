# Research: Audit Purchases Module

**Feature**: 011-audit-purchases | **Date**: 2026-04-15

## Research Tasks & Findings

### R1: Backend `float()` violations — exhaustive inventory

**Decision**: All `float()` calls in purchases/landed_costs/matching routers are output serialization only — they serialize `Decimal` values into JSON responses. Replace with `str()` to preserve precision per Constitution §I.

**Rationale**: `float()` introduces IEEE 754 rounding artifacts (e.g., 1250.75 → 1250.7499999...). Using `str()` preserves the exact Decimal representation sent to the frontend.

**Findings**:

| File | Count | Lines |
|------|-------|-------|
| `routers/purchases.py` | 55 | L402-403, L406, L431, L449, L473-477, L536, L829, L907-909, L1088, L1090, L1102-1103, L1297, L1309, L2677, L2927, L3086, L3154, L3264, L3268, L3309-3311, L3381-3382, L3405-3406, L3481, L3496-3497, L3514-3515, L3522, L3528-3531, L3571-3572, L3584-3585, L3594, L3600-3603 |
| `routers/landed_costs.py` | 6 | L193, L311-312, L322, L464, L470 |
| `routers/matching.py` | 13 | L170-178, L270-273 |
| `services/matching_service.py` | 2 | L196-197 |

**Total**: 76 `float()` calls → all become `str()`

**Pattern**: Existing code uses `_dec()` helper (null-safe Decimal converter), quantize to `_D2`/`_D4`, then wraps with `float()`. Fix: replace `float(...)` with `str(...)` preserving the inner expression.

---

### R2: Pydantic schema `float` fields — exhaustive inventory

**Decision**: Change all `float` type annotations to `Decimal` in Pydantic schemas. Pydantic 2.x natively supports `Decimal` and will accept both string and numeric JSON input.

**Rationale**: The Pydantic schema is the API boundary — if it accepts `float`, precision is lost before business logic runs.

**Findings**:

| File | Count | Fields |
|------|-------|--------|
| `schemas/purchases.py` | 16 | `PurchaseLineItem`: quantity, unit_price, tax_rate, discount, markup · `PurchaseCreate`: paid_amount, effect_percentage, markup_amount, exchange_rate · `SupplierGroupCreate`: discount_percentage · `POCreate`: effect_percentage, markup_amount, exchange_rate · `ReceiveItem`: received_quantity · `PaymentAllocationSchema`: allocated_amount · `SupplierPaymentCreate`: amount |
| `schemas/matching.py` | 12 | `MatchToleranceCreate`: 4 fields · `MatchToleranceRead`: 4 fields · `ThreeWayMatchLineRead`: 4 fields (po_quantity thru price_variance_abs) |
| `routers/matching.py` (inline) | 4 | `ToleranceSave` (L39-42): quantity_percent, quantity_absolute, price_percent, price_absolute |

**Total**: 32 `float` fields → all become `Decimal`

**Import needed**: `from decimal import Decimal` in each schema file.

---

### R3: Fiscal period check gaps

**Decision**: Add `check_fiscal_period_open()` to 4 endpoints. The import already exists at L23 of `purchases.py`. Pattern matches existing usage in `create_purchase_invoice` (L1157).

**Rationale**: Constitution §III and §XXII mandate fiscal period validation at Step 3 of the transaction pipeline for ALL financial mutations.

**Findings**:

| Endpoint | Function start | Has check? | Insertion point |
|----------|---------------|:---:|----------------|
| `create_purchase_invoice` | L1110 | ✅ L1157 | Already present |
| `post_landed_cost` | L340 | ✅ L357 | Already present |
| `receive_purchase_order` | L719 | ❌ | Before GL posting at L869 |
| `create_purchase_return` | L1720 | ❌ | Before GL posting at L1913 |
| `create_purchase_credit_note` | L2529 | ❌ | Before GL posting at L2644 |
| `create_purchase_debit_note` | L2794 | ❌ | Before GL posting at L2902 |

**Pattern**: `check_fiscal_period_open(db, date_value)` — raises HTTPException 400 if period is closed (hard block).

**GL posting call sites** (all use `gl_create_journal_entry`): L869, L1540, L1913, L1977, L2238, L2644, L2902

---

### R4: Audit column gaps — DDL and model analysis

**Decision**: Create Alembic migration + update `database.py` CREATE TABLE + add `AuditMixin` to domain models (triple-update per Constitution §XXVIII).

**Rationale**: Constitution §XVII requires `created_at`, `updated_at`, `created_by`, `updated_by` on ALL domain models. 11 procurement tables are non-compliant.

**Findings — `database.py` CREATE TABLE gaps**:

| Table | `created_at` | `updated_at` | `created_by` | `updated_by` |
|-------|:---:|:---:|:---:|:---:|
| `purchase_orders` (L885) | ✅ | ✅ | ✅ | ❌ |
| `purchase_order_lines` (L906) | ✅ | ❌ | ❌ | ❌ |
| `request_for_quotations` (L1147) | ✅ | ✅ | ✅ | ❌ |
| `rfq_lines` (L1160) | ❌ | ❌ | ❌ | ❌ |
| `rfq_responses` (L1170) | alias | ❌ | ❌ | ❌ |
| `supplier_ratings` (L1184) | alias | ❌ | alias | ❌ |
| `purchase_agreements` (L1199) | ✅ | ❌ | ✅ | ❌ |
| `purchase_agreement_lines` (L1215) | ❌ | ❌ | ❌ | ❌ |
| `landed_costs` (L5172) | ✅ | ✅ | ✅ | ❌ |
| `landed_cost_items` (L5192) | ✅ | ❌ | ❌ | ❌ |
| `landed_cost_allocations` (L5203) | ✅ | ❌ | ❌ | ❌ |

**Domain model gaps** — Only `BlanketPurchaseOrder` and `BlanketPOReleaseOrder` inherit `AuditMixin`. All other procurement models inherit only `ModelBase`:
- `procurement_orders.py`: PurchaseOrder, PurchaseOrderLine
- `procurement_costs.py`: LandedCost, LandedCostItem, PurchaseAgreement, PurchaseAgreementLine
- `procurement_suppliers.py`: SupplierRating, Supplier, SupplierGroup, SupplierPayment, SupplierTransaction

**Migration approach**: `IF NOT EXISTS` / `ADD COLUMN IF NOT EXISTS` for idempotency across tenants.

---

### R5: Frontend parseFloat patterns — categorization

**Decision**: Replace each `parseFloat()` based on its context:
1. **Payload construction** (sending to API): `String(value)` or pass raw string
2. **Local comparison/calculation** (UI subtotals): `Number(value)` 
3. **Display rendering**: `formatNumber(value)`

**Rationale**: Constitution §I forbids JS `Number` for monetary values in API payloads. Local UI subtotals use `Number()` as a display-only shortcut (final calculation always on backend).

**Findings by file (top 5)**:

| File | Total | Payload | Local calc | Display |
|------|-------|---------|-----------|---------|
| BuyingOrderForm.jsx | 22 | 4 (L225-228) | 18 (L89-92, L95, L111, L139-146, L168-171, L297-300) | 0 |
| PurchaseInvoiceForm.jsx | 18 | 7 (L288, L291, L301-304, L316-318) | 11 (L83-85, L93, L139, L218-221, L224, L236) | 0 |
| BuyingReturnForm.jsx | 11 | 4 (L232-235) | 7 (L157, L169-172, L175) | 0 |
| PaymentForm.jsx | 7 | 3 (L313, L316, L318) | 4 (L83, L198, L217, L523) | 0 |
| BlanketPOForm.jsx | 4 | 2 (L51-52) | 2 (L38) | 0 |

**Other files**: ToleranceConfig (4), PurchaseCreditNotes (4), PurchaseDebitNotes (4), PurchaseOrderReceive (2), BlanketPODetail (2), SupplierGroups (1), PurchaseAgreements (1), Buying/SupplierPayments (1)

---

### R6: Frontend error handling patterns — useToast vs toastEmitter vs console.error

**Decision**: 
- Files with `toastEmitter`: Replace import + all calls with `useToast`/`showToast()`
- Files with `console.error` only: Add `useToast` import, wrap catch blocks with `showToast()`
- Files already having `useToast`: Fix any remaining `console.error` patterns

**Rationale**: Constitution §XXVII requires translated error messages via i18n keys. `console.error` is invisible to users. `toastEmitter` is a legacy pattern being phased out.

**File categorization**:

| Category | Files | Count |
|----------|-------|-------|
| Has `useToast` already | LandedCostDetails, LandedCosts, PurchaseAgreements, PurchaseCreditNotes, PurchaseDebitNotes, RFQList, SupplierForm, SupplierRatings, MatchDetail, ToleranceConfig, BlanketPODetail, BlanketPOForm, BlanketPOList | 13 |
| Has `toastEmitter` (migrate) | BuyingOrders, BuyingReturnForm, PurchaseOrderDetails, PurchaseOrderReceive, SupplierGroups, Purchases/SupplierPayments, Purchases/PaymentForm | 7 |
| Has neither (add `useToast`) | BuyingHome, BuyingOrderDetails, BuyingOrderForm, BuyingReports, BuyingReturnDetails, BuyingReturns, PurchaseInvoiceDetails, PurchaseInvoiceForm, PurchaseInvoiceList, PurchasesAgingReport, SupplierDetails, SupplierList, Buying/SupplierPayments, SupplierStatement, Purchases/PaymentDetails, Matching/MatchList | 16 |

**useToast import pattern** (from LandedCosts.jsx):
```js
import { useToast } from '../../context/ToastContext'
const { showToast } = useToast()
showToast(t('key'), 'error')  // or 'success'
```

**Total console.error occurrences**: 47 across 31 files (the 13 files with useToast have 0 console.error except PurchaseAgreements:2, PurchaseCreditNotes:4, PurchaseDebitNotes:4, SupplierForm:1, SupplierRatings:1, BlanketPOForm:1 = 13 in useToast files)

---

### R7: GL posting verification — completeness

**Decision**: No GL posting gaps. All 6 financial endpoints already post balanced journal entries. Only precision needs fixing.

**Findings**:

| Endpoint | GL call line | Entry type |
|----------|-------------|-----------|
| `receive_purchase_order` | L869 | Dr. Inventory Asset, Cr. GRN Accrual |
| `create_purchase_invoice` | L1540 | Dr. Expense/Asset, Cr. AP |
| `create_purchase_return` | L1913, L1977 | Reversal entries + refund |
| Supplier payment | L2238 | Dr. AP, Cr. Cash/Bank |
| `create_purchase_credit_note` | L2644 | Dr. AP, Cr. Expense |
| `create_purchase_debit_note` | L2902 | Dr. Expense, Cr. AP |

All use `gl_create_journal_entry` (imported at L24).

---

### R8: Matching service precision analysis

**Decision**: The matching service computations are already in `Decimal`. Only the output serialization (`float()` at L196-197) needs to change to `str()`.

**Rationale**: The `_pct()` helper (L24) computes variance as `Decimal`. The `_within_tolerance()` comparisons (L48-55) use `Decimal` operators. Changing output to `str()` does not affect matching logic.

**Alternatives considered**: Converting the entire matching service to use `str()` internally was rejected — `Decimal` is the correct internal representation per Constitution §I.

---

### R9: Landed cost allocation rounding

**Decision**: Implement "largest remainder" method for allocation rounding. After computing each share with `Decimal.quantize()`, sum all shares and assign any remainder (positive or negative) to the line with the largest allocation.

**Rationale**: This is the standard accounting convention that minimizes relative impact of the rounding adjustment.

**Current implementation** (L280-312 of `landed_costs.py`): Computes `share = (basis / total_basis) * total_cost`, then `allocated = float(share.quantize(_D2, ROUND_HALF_UP))`. The `float()` destroys precision AND there's no remainder handling — allocations may not sum exactly to `total_cost`.

**Fix**: 
1. Remove `float()` wrapper → keep as `Decimal`
2. After computing all shares, compare `sum(shares)` vs `total_cost`
3. Add/subtract difference on the largest share line

---

### R10: formatNumber utility analysis

**Decision**: `formatNumber()` from `frontend/src/utils/format.js` is available and suitable. Files missing the import need it added where monetary values are displayed.

**Current signature**: `formatNumber(value, overridePrecision = null)` — reads user's `decimal_places` from auth context, formats with `toLocaleString()`.

**Files needing `formatNumber` import added**: 19 files across the 4 directories that currently lack the import but render monetary values.
