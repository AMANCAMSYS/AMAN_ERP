# Research: Audit Inventory Module

**Feature**: 009-audit-inventory
**Date**: 2026-04-15

## Research Tasks & Findings

### R1: Backend float() violations — Exact scope

**Decision**: Fix all 20 `float()` occurrences across 5 router files to return `str()` for monetary/quantity fields in API responses.

**Rationale**: Constitution §I mandates no float/double for monetary values. All 20 occurrences will produce floating-point precision artifacts in JSON responses (e.g., `1250.7500000000002`).

**Findings**:

| File | Count | Lines | Fields |
|------|-------|-------|--------|
| `products.py` | 9 | 37, 54, 55, 138, 139, 140, 141, 144, 145, 207 | cost_price, average_cost, quantity, selling_price, buying_price, last_buying_price, tax_rate, current_stock, reserved_quantity, total_qty |
| `stock_movements.py` | 2 | 51, 151 | unit_cost, quantity |
| `reports.py` | 3 | 303, 304, 305 | total_quantity, moving_avg_cost, total_valuation |
| `batches.py` | 4 | 1255, 1256, 1329, 1330 | quantity, cost, system_quantity, unit_cost |
| `warehouses.py` | 2 | 172, 254 | stock, quantity |

**Pattern**: Replace `float(x or 0)` → `str(x or 0)` for all monetary/cost fields. For pure quantity fields that are always integers (e.g., count), use `str(int(x or 0))`. For quantity fields that can be fractional (e.g., kg), use `str(x or 0)`.

**Alternatives considered**: Leave float for non-monetary fields → rejected because Constitution §I applies to "any monetary value" and Numeric(18,4) fields include quantities.

---

### R2: Frontend parseFloat() violations — Exact scope

**Decision**: Fix all 26 `parseFloat()` occurrences across 7 files. Two categories: (A) API payload values → send as `String(value)`, (B) display/comparison values → use `formatNumber()` or `Number()` for local-only comparisons.

**Rationale**: Constitution §I+§XIX: frontend must not do monetary calculations; API payloads must use string amounts.

**Findings**:

| File | Count | Category | Fix |
|------|-------|----------|-----|
| `StockTransferForm.jsx` | 1 | A (payload) | `parseFloat(item.quantity)` → `String(item.quantity)` |
| `StockShipmentForm.jsx` | 1 | A (payload) | `parseFloat(currentItem.quantity)` → `String(currentItem.quantity)` |
| `StockAdjustmentForm.jsx` | 1 | A (payload) | `parseFloat(formData.new_quantity)` → `String(formData.new_quantity)` |
| `BatchList.jsx` | 3 | A+B | L86-87 payload→String; L146 display→`formatNumber()` |
| `CycleCounts.jsx` | 5 | A+B | L131 payload→String; L407 comparison→`Number()`; L411,419 display→`formatNumber()` |
| `QualityInspections.jsx` | 2 | A (payload) | `parseFloat(c.min_value)` → `String(c.min_value)` |
| `PriceListItems.jsx` | 1 | A (payload) | `parseFloat(newPrice)` → `String(newPrice)` |
| `ProductForm.jsx` | 2 | B (local) | L106 VAT calc (backend should provide), L165 local comparison OK with `Number()` |
| `ForecastDetail.jsx` | 10 | B (display) | All display/comparison — use `formatNumber()` or `Number()` |

**Alternatives considered**: Use a fixed-point library (decimal.js) → rejected, overkill for an audit; backend already handles precision.

---

### R3: Frontend error handling — Standardization pattern

**Decision**: All inventory pages must use `useToast` from `../../context/ToastContext` with `showToast(message, 'error'|'success')`. Remove `toastEmitter.emit()` and `console.error`-only patterns.

**Rationale**: Constitution §XXVII mandates translated error messages via consistent patterns. `console.error` alone gives no user feedback; `toastEmitter.emit()` is a legacy pattern.

**Reference pattern** (from ProductList.jsx):
```jsx
import { useToast } from '../../context/ToastContext'
const { showToast } = useToast()
// On error:
showToast(err.response?.data?.detail || t('module.action.error_key'), 'error')
```

**Pages needing fix** (17 pages lack useToast or use alternative patterns):
StockAdjustmentForm, StockTransferForm, StockAdjustments, ShipmentList, ShipmentDetails, CategoryList, WarehouseList, PriceLists, PriceListItems, StockReports, StockMovements, StockHome, ProductForm, InventoryValuation, ForecastDetail, ForecastList, ForecastGenerate

**Alternatives considered**: Keep toastEmitter.emit() where already used → rejected, constitution requires consistency.

---

### R4: Dead notification functions — Cleanup approach

**Decision**: Remove the 4 dead functions from `services/inventory.js`. No callers exist.

**Rationale**: Research confirmed ZERO imports/calls of these functions anywhere in the frontend. They call endpoints that are unmounted (404). The unified notification system in `services/notifications.js` handles all notifications via `Topbar.jsx` and `NotificationCenter.jsx`.

**Functions to remove**:
```javascript
getNotifications: () => api.get('/inventory/notifications'),
getUnreadCount: () => api.get('/inventory/notifications/unread-count'),
markNotificationRead: (id) => api.post(`/inventory/notifications/${id}/read`),
markAllNotificationsRead: () => api.post('/inventory/notifications/read-all'),
```

**Alternatives considered**: Redirect to unified endpoints → rejected, no callers exist so redirect adds dead code.

---

### R5: Cycle count GL gap — Implementation approach

**Decision**: Add GL journal entry posting to the cycle count completion path in `batches.py`, following the exact pattern from `adjustments.py`.

**Rationale**: Constitution §III mandates every transaction creates balanced JEs. §VIII specifically calls out "Cycle count variances → auto-adjustment entries."

**Implementation pattern** (from adjustments.py):
1. Look up `acc_inventory` and `acc_adjustment` (or `acc_variance`) GL accounts
2. Calculate `variance_value = abs(system_qty - counted_qty) * unit_cost`
3. Call `check_fiscal_period_open(db, date)`
4. Build GL lines: surplus → Dr. Inventory / Cr. Variance; shortage → Dr. Variance / Cr. Inventory
5. Call `gl_create_journal_entry(db, company_id, date, description, lines, user_id, branch_id, reference, currency)`

**Location**: `batches.py` lines 1355-1375 in `complete_cycle_count()` endpoint, inside the `auto_adjust=true` branch.

**Alternatives considered**: Post GL after cycle count (separate endpoint) → rejected, must be atomic with inventory update.

---

### R6: Missing audit columns — Migration approach

**Decision**: Create a single Alembic migration + update `database.py` CREATE TABLE definitions for both tables.

**Rationale**: Constitution §XVII requires AuditMixin on ALL domain models. §XXVIII requires dual-update (migration + database.py).

**Columns to add**:

| Table | Column | Type | Default |
|-------|--------|------|---------|
| `product_categories` | `created_by` | `INTEGER REFERENCES company_users(id)` | `NULL` |
| `product_categories` | `updated_by` | `INTEGER REFERENCES company_users(id)` | `NULL` |
| `product_categories` | `updated_at` | `TIMESTAMPTZ` | `NULL` |
| `stock_adjustments` | `updated_at` | `TIMESTAMPTZ` | `NULL` |
| `stock_adjustments` | `updated_by` | `INTEGER REFERENCES company_users(id)` | `NULL` |

Also update `inventory_core.py` domain model to add the mapped columns.

**Alternatives considered**: Document as known gaps → rejected per clarification session decision.

---

### R7: Negative stock hard-block — Scope check

**Decision**: Verify and enforce negative stock checks on all stock-deducting endpoints. Most already check — only cycle count auto-adjust is missing.

**Rationale**: Clarification session decision: hard-block all transactions that would make available quantity negative.

**Current state**:

| Endpoint | Has Check? | Notes |
|----------|-----------|-------|
| POST `/delivery` | ✅ | Row lock + qty check at L151 |
| POST `/transfer` | ✅ | Row lock + qty check at L76 |
| POST `/shipments` (confirm) | ✅ | Qty check at L77 |
| POST `/adjustments` | ✅ | Rejects negative at L114 |
| PUT `/cycle-counts/{id}/complete` | ❌ | Direct overwrite at L1355 — no check |

**Fix needed**: In cycle count auto-adjust, if counted_qty < system_qty (shortage), verify that the resulting quantity would not go negative considering reserved stock.

**Alternatives considered**: Allow cycle count to override since it's a physical verification → rejected, hard-block policy applies universally.

---

### R8: Backend str() conversion — Best practice

**Decision**: Use `str(Decimal(x) if x is not None else Decimal('0'))` pattern. For fields already in Decimal (from Numeric columns), simply `str(x or 0)`.

**Rationale**: No existing inventory router uses `str()` for monetary returns. The pattern must be established. Other audited modules (e.g., taxes.py) use `str()`.

**Pattern**:
```python
# Before (violation):
"selling_price": float(row.selling_price or 0),

# After (compliant):
"selling_price": str(row.selling_price or 0),
```

This works because SQLAlchemy returns `Decimal` objects from `NUMERIC` columns, and `str(Decimal('1250.7500'))` → `"1250.7500"` (preserves precision).

---

### R9: useBranch pattern — Verification

**Decision**: No action needed — all inventory pages already import and use `useBranch` from `BranchContext`. Verified in research phase.

**Rationale**: FR-021 is already satisfied. No changes required.

---

### R10: SQL parameterization — Verification

**Decision**: No action needed — all inventory routers use `text()` with `:param` syntax. No f-string SQL interpolation found.

**Rationale**: FR-019 is already satisfied. No changes required.
