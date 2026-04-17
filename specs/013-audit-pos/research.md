# Research: Audit POS Module — تدقيق وحدة نقاط البيع

**Feature**: 013-audit-pos | **Date**: 2026-04-15

## R-001: float() Serialization Pattern in pos.py

**Decision**: Replace all 31 `float()` calls with `str()` for response/log serialization, keep `Decimal` for SQL parameters.

**Rationale**: The `_dec()` helper already converts values to `Decimal` with proper quantization. The `float()` wrapper at serialization re-introduces IEEE 754 imprecision. Using `str()` preserves exact decimal representation.

**Categories identified**:
- **Category A (11 calls)**: Response dict values → `float(x)` → `str(x)` — lines 167-171, 766, 1108, 1381, 1415
- **Category B (5 calls)**: SQL parameters → `float(x)` → remove wrapper, pass `Decimal` directly (SQLAlchemy handles it) — lines 233-235, 255, 443
- **Category C (13 calls)**: Error messages and `log_activity` details → `float(x)` → `str(x)` — lines 92, 284, 445, 532, 759, 929, 1102, 1377, 1411
- **Category D (1 call)**: Computation intermediate (CostingService) → needs verification if service accepts `Decimal` — line 543

**Alternatives considered**: Using `json.dumps` with custom encoder — rejected (over-engineered for in-place audit).

## R-002: Pydantic float→Decimal Migration

**Decision**: Change all 23 `: float` annotations in `backend/schemas/pos.py` to `: Decimal`. Add `from decimal import Decimal` import.

**Rationale**: Database columns are `DECIMAL(18,4)`. Using `float` in Pydantic loses precision at the API boundary. The same pattern was applied in 012-audit-sales across 4 schema files.

**Fields affected** (8 classes, 23 fields):
- `SessionCreate`: opening_balance
- `SessionClose`: closing_balance, cash_register_balance
- `SessionResponse`: 9 monetary fields (opening_balance through difference)
- `POSProductResponse`: price, stock_quantity, tax_rate
- `OrderLineCreate`: quantity, unit_price, discount_amount, tax_rate
- `OrderPaymentCreate`: amount
- `OrderCreate`: discount_amount, paid_amount
- `OrderResponse`: total_amount
- `ReturnItemCreate`: quantity

## R-003: AuditMixin on POS Models

**Decision**: Add `AuditMixin` to all 13 POS models in `sales_pos.py`. Remove manually-defined `created_at`, `updated_at`, `created_by` columns where they overlap with AuditMixin's columns.

**Rationale**: Constitution XVII mandates "ALL domain models" must have AuditMixin. Currently 0/13 POS models have it.

**Conflict resolution**: Some models have `created_by` as `INTEGER` FK (e.g., `PosOrder.created_by` → `company_users.id`). AuditMixin provides `created_by` as `String(100)`. The AuditMixin version should take precedence for consistency — the user_id is stored as a string identifier, matching all other modules.

**Models**: PosSession, PosOrder, PosOrderLine, PosPayment, PosOrderPayment, PosReturn, PosReturnItem, PosPromotion, PosLoyaltyProgram, PosLoyaltyPoint, PosLoyaltyTransaction, PosTable, PosTableOrder, PosKitchenOrder (14 models — 13 POS + PendingReceivable)

**Note**: `PendingReceivable` and `Receipt` models are also in this file but are not POS-specific. They should still get AuditMixin for consistency.

## R-004: Fiscal Period Checks

**Decision**: Add `check_fiscal_period_open(db, datetime.now().date())` to `close_session` and `create_return` before any GL posting.

**Rationale**: Constitution III (Double-Entry Integrity) and XXII (Transaction Validation Pipeline) require fiscal period check before all GL entries. Currently only `create_order` (line 423) has this check.

**Insertion points**:
- `close_session`: After session status validation (around line 197), before GL entry creation (line 240)
- `create_return`: After order validation (around line 907), before mutations begin

**Alternatives considered**: Adding fiscal check inside `gl_create_journal_entry` centrally — rejected (would change shared utility affecting all modules).

## R-005: Frontend parseFloat Replacement

**Decision**: Replace `parseFloat()` with `Number()` for local calculations and `String()` for API payloads.

**Rationale**: Same pattern applied in 012-audit-sales across 38 files. `parseFloat` introduces IEEE 754 imprecision. `Number()` is equivalent for local display math. `String()` preserves user input exactly for API transmission.

**Files affected** (4 files, 7 calls):
- POSHome.jsx L84: `parseFloat(openingBalance)` → `String(openingBalance)` (API payload)
- POSInterface.jsx L300-301: 2 calls → context-dependent (String for payload, Number for calc)
- LoyaltyPrograms.jsx L30: 2 calls → `String()` (API payload)
- Promotions.jsx L38: 2 calls → `String()` (API payload)

## R-006: console.error and console.log Replacement

**Decision**: Replace all `console.error` with `showToast(t('common.error'), 'error')` and remove all `console.log` debug statements.

**Rationale**: Constitution VII mandates no `print()` in production; `console.error`/`console.log` are the JavaScript equivalent. Users need visible feedback via toast notifications.

**Files affected** (8 files):
- POSHome.jsx: 3 console.error → showToast (useToast already imported)
- POSInterface.jsx: 4 console.error → showToast (useToast already imported)
- POSOfflineManager.jsx: 2 console.error → showToast (need to add useToast import)
- TableManagement.jsx: 1 console.error → showToast (useToast already imported)
- KitchenDisplay.jsx: 1 console.error → showToast (useToast already imported)
- LoyaltyPrograms.jsx: 1 console.error → showToast (useToast already imported)
- Promotions.jsx: 1 console.error → showToast (useToast already imported)
- HeldOrders.jsx: 2 console.error → showToast + 5 console.log → remove (useToast already imported)

## R-007: toLocaleString → formatNumber Replacement

**Decision**: Replace `.toLocaleString()` with `formatNumber()` on monetary values only. Keep date `.toLocaleString()` calls unchanged.

**Rationale**: `formatNumber()` respects company-configured decimal precision. Raw `.toLocaleString()` uses browser defaults.

**Files affected** (3 files, 16 monetary calls + 2 date calls to keep):
- POSInterface.jsx: 14 monetary `.toLocaleString()` → `formatNumber()` (add import)
- POSReturns.jsx: 1 monetary `.toLocaleString()` → `formatNumber()` (add import)
- HeldOrders.jsx: 1 monetary `.toLocaleString()` → `formatNumber()` (add import)
- POSOfflineManager.jsx: 1 date `.toLocaleString('ar-SA')` → **KEEP** (not monetary)
- ThermalPrintSettings.jsx: 2 date `.toLocaleString('ar-SA')` → **KEEP** (not monetary)

## R-008: Audit Columns in database.py

**Decision**: Add audit column entries for all POS tables in `sync_essential_columns()`.

**Rationale**: Models will inherit AuditMixin columns, but existing database tables need the physical columns added. Same pattern from 012-audit-sales where 28 column entries were added for 10 tables.

**Tables needing audit columns** (14 tables):
- pos_sessions: updated_at, created_by, updated_by
- pos_orders: updated_by (already has created_at, created_by, updated_at)
- pos_order_lines: created_at, updated_at, created_by, updated_by
- pos_payments: updated_at, created_by, updated_by
- pos_order_payments: updated_at, created_by, updated_by
- pos_returns: updated_at, created_by, updated_by (has user_id but not created_by)
- pos_return_items: updated_at, created_by, updated_by
- pos_promotions: updated_by (already has created_at, created_by, updated_at)
- pos_loyalty_programs: updated_at, created_by, updated_by
- pos_loyalty_points: updated_at, created_by, updated_by
- pos_loyalty_transactions: updated_at, created_by, updated_by
- pos_tables: updated_at, created_by, updated_by
- pos_table_orders: created_at, updated_at, created_by, updated_by
- pos_kitchen_orders: created_at, updated_at, created_by, updated_by

## R-009: CostingService.consume_layers() Parameter

**Decision**: Verify whether `CostingService.consume_layers()` accepts `Decimal` for quantity. If yes, remove `float()` wrapper at line 543. If no, keep as-is and document.

**Rationale**: Line 543 passes `quantity=float(item.quantity)` to the costing service. If the service internally converts to Decimal anyway, the float wrapper is harmful. If it requires float, we must keep it.

**Resolution**: From prior audit work (009-inventory), `CostingService` was already audited and works with Decimal values. The `float()` wrapper should be removed.

## R-010: Commission Verification

**Decision**: Verify no commission logic exists in `pos.py` — grep confirms 0 matches.

**Rationale**: POS orders bypass the sales commission flow. A simple grep verification is sufficient.

**Result**: `grep -rn "commission" backend/routers/pos.py` → 0 matches. No action needed.
