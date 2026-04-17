# Research: Audit Sales Module

**Feature**: 012-audit-sales | **Date**: 2026-04-15

## 1. AuditMixin & SoftDeleteMixin Availability

**Decision**: Use existing `AuditMixin` from `backend/models/base.py`
**Rationale**: Already defined with all four columns (`created_at`, `updated_at`, `created_by`, `updated_by`). Same class used in prior audits (009-inventory, 011-purchases).
**Alternatives considered**: None — the existing mixin is the canonical pattern.

**Exact definition** (base.py lines 8-18):
```python
class AuditMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
```

## 2. Sales Domain Model Structure

**Decision**: Add AuditMixin only to sales-exclusive models in `domain_models/sales_rfq.py` and `domain_models/sales_customers_delivery.py`; skip POS-exclusive models (deferred to POS audit).
**Rationale**: Per clarification — shared/POS models get their own audit. Avoids merge conflicts.

### Model Ownership Map

| Model | Source File | AuditMixin Status | Scope |
|-------|-----------|-------------------|-------|
| SalesCommission | sales_rfq.py | has `created_at` only → **NEEDS FULL MIXIN** | Sales exclusive |
| SalesOpportunity | sales_rfq.py | has created_at → **NEEDS FULL MIXIN** | Sales exclusive |
| SalesOrder | sales_rfq.py | has created_at → **NEEDS FULL MIXIN** | Sales exclusive |
| SalesOrderLine | sales_rfq.py | **NONE** → **NEEDS FULL MIXIN** | Sales exclusive |
| SalesQuotation | sales_rfq.py | has created_at → **NEEDS FULL MIXIN** | Sales exclusive |
| SalesQuotationLine | sales_rfq.py | **NONE** → **NEEDS FULL MIXIN** | Sales exclusive |
| SalesReturn | sales_rfq.py | has created_at → **NEEDS FULL MIXIN** | Sales exclusive |
| SalesReturnLine | sales_rfq.py | **NONE** → **NEEDS FULL MIXIN** | Sales exclusive |
| SalesTarget | sales_rfq.py | has created_at → **NEEDS FULL MIXIN** | Sales exclusive |
| RequestForQuotation | sales_rfq.py | has created_at/updated_at/created_by → **NEEDS updated_by** | Sales/CPQ |
| RfqLine | sales_rfq.py | **NONE** → **NEEDS FULL MIXIN** | Sales/CPQ |
| RfqResponse | sales_rfq.py | has submitted_at → **NEEDS FULL MIXIN** | Sales/CPQ |
| Customer+ | sales_customers_delivery.py | has created_at/updated_at → **VERIFY** | Shared |
| DeliveryOrder+ | sales_customers_delivery.py | has created_at → **VERIFY** | Shared |
| POS models | sales_pos.py | **SKIP** — POS audit | POS exclusive |
| RevenueRecognitionSchedule | finance_recognition_tax.py | **SKIP** — finance audit | Shared |

## 3. Database Audit Column Gaps

**Decision**: Add missing audit columns to all sales-exclusive tables in database.py
**Rationale**: Constitution XVII requires `AuditMixin` on ALL domain models. Many sales tables have partial audit columns.

### Column Gap Analysis

| Table | created_at | updated_at | created_by | updated_by | Action |
|-------|-----------|-----------|-----------|-----------|--------|
| invoices | ✓ | ✓ | ✓ | ✗ | Add updated_by |
| invoice_lines | ✓ | ✗ | ✗ | ✗ | Add updated_at, created_by, updated_by |
| sales_quotations | ✓ | ✗ | ✓ | ✗ | Add updated_at, updated_by |
| sales_quotation_lines | ✗ | ✗ | ✗ | ✗ | Add ALL four |
| sales_orders | ✓ | ✗ | ✓ | ✗ | Add updated_at, updated_by |
| sales_order_lines | ✗ | ✗ | ✗ | ✗ | Add ALL four |
| sales_returns | ✓ | ✗ | ✓ | ✗ | Add updated_at, updated_by |
| sales_return_lines | ✗ | ✗ | ✗ | ✗ | Add ALL four |
| payment_vouchers | ✓ | ✗ | ✗ | ✗ | Add updated_at, created_by, updated_by |
| sales_commissions | ✓ | ✗ | ✗ | ✗ | Add updated_at, created_by, updated_by |

**POS tables skipped**: pos_sessions, pos_orders, pos_order_lines, pos_payments, pos_order_payments, pos_returns → deferred to POS audit.

## 4. Fiscal Period Check Status

**Decision**: Verify existing checks are correct; no new checks needed for currently-covered endpoints.
**Rationale**: All GL-posting sales endpoints already have fiscal checks:

| File | Lines | Check | Import Source | Status |
|------|-------|-------|---------------|--------|
| invoices.py | 194 | `check_fiscal_period_open(db, invoice.invoice_date)` | utils.accounting | ✓ Correct |
| credit_notes.py | 195-197 | `check_fiscal_period_open(db, inv_date)` | utils.accounting | ✓ Correct |
| credit_notes.py | 538-540 | `check_fiscal_period_open(db, inv_date)` | utils.accounting | ✓ Correct (debit notes) |
| returns.py | 104-105 | `check_fiscal_period_open(db, data.return_date)` | utils.fiscal_lock | ✓ Correct |
| vouchers.py | 34-36 | `check_fiscal_period_open(db, data.voucher_date)` | utils.accounting | ✓ Correct (receipts) |
| vouchers.py | 266-268 | `check_fiscal_period_open(db, data.voucher_date)` | utils.accounting | ✓ Correct (payments) |

**Note**: `delivery_orders.py` and `orders.py` need verification — if they create GL entries, fiscal checks may be needed.

## 5. Frontend Toast Pattern

**Decision**: Use `useToast` from `../../context/ToastContext` with `showToast()` calls.
**Rationale**: Established pattern in other modules. No sales files currently use `useToast`.

**Import pattern**:
```javascript
import { useToast } from '../../context/ToastContext';
```

**Usage pattern**:
```javascript
const { showToast } = useToast();
// In catch blocks:
showToast(t('common.error'), 'error');
// On success:
showToast(t('common.saved'), 'success');
```

**Current patterns to replace**:
- `console.error(err)` → `showToast(t('common.error'), 'error')`
- `toastEmitter.emit('error', msg)` → `showToast(msg, 'error')`
- `toastEmitter.emit('success', msg)` → `showToast(msg, 'success')`

## 6. Backend float() Replacement Pattern

**Decision**: Replace `float(value)` with `str(value)` for all database Decimal result serialization.
**Rationale**: Constitution I forbids float for monetary values. `str()` preserves exact precision.

**Before**:
```python
"total_revenue": float(total_revenue),
"total_receivables": float(total_receivables),
"monthly_sales": float(monthly_sales),
```

**After**:
```python
"total_revenue": str(total_revenue or 0),
"total_receivables": str(total_receivables or 0),
"monthly_sales": str(monthly_sales or 0),
```

## 7. Frontend parseFloat Replacement Pattern

**Decision**: Replace `parseFloat(value)` with `Number(value)` for local calculations and `String(value)` for API payloads.
**Rationale**: `Number()` is safe for UI display; `String()` preserves precision for API boundary.

**Local calculations (before)**:
```javascript
const quantity = parseFloat(item.quantity) || 0
const unitPrice = parseFloat(item.unit_price) || 0
```

**Local calculations (after)**:
```javascript
const quantity = Number(item.quantity) || 0
const unitPrice = Number(item.unit_price) || 0
```

**API payloads (before)**:
```javascript
paid_amount: parseFloat(formData.paid_amount) || 0,
exchange_rate: parseFloat(formData.exchange_rate) || 1.0,
```

**API payloads (after)**:
```javascript
paid_amount: String(formData.paid_amount || 0),
exchange_rate: String(formData.exchange_rate || 1),
```

## 8. Commission Calculation Analysis

**Decision**: Fix `float()` calls in commission logic AND verify functional correctness.
**Rationale**: Per clarification, commission calculation logic must be functionally verified.

**Current code** (sales_improvements.py):
```python
rate = float(rule.rate) if rule else 0.0
total = float(getattr(inv, 'grand_total', getattr(inv, 'total', 0)) or 0)
commission = round(total * rate / 100, 2)
```

**Issues**:
1. `float(rule.rate)` — should use `Decimal(str(rule.rate))`
2. `float(getattr(...))` — should use `Decimal(str(...))`
3. `round(total * rate / 100, 2)` — should use `Decimal.quantize(Decimal("0.01"))`

**Corrected pattern**:
```python
rate = Decimal(str(rule.rate)) if rule else Decimal("0")
total = Decimal(str(getattr(inv, 'grand_total', getattr(inv, 'total', 0)) or 0))
commission = (total * rate / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
```

**Functional verification**: `10000.00 * 7.5 / 100 = 750.00` (exact).

## 9. Pydantic Schema Audit

**Decision**: Change remaining `float` fields to `Decimal` in all sales schemas.
**Rationale**: Constitution I requires Decimal for monetary values at API boundary.

**Files with float fields**:
- `backend/schemas/sales_credit_notes.py`: `quantity: float = 1` → `quantity: Decimal = Decimal("1")`
- `backend/routers/sales/schemas.py`: Multiple float fields (inline Pydantic models)
- `backend/schemas/sales_improvements.py`: Needs audit for float fields
- `backend/schemas/cpq.py`: Already mostly Decimal — verify completeness

**Note**: `cpq.py` is mostly correct already (uses `Decimal` throughout). Only `sales_credit_notes.py` has a clear `float` field (`quantity`).

## 10. Delivery Orders Fiscal Check

**Decision**: Verify whether `delivery_orders.py` creates GL entries; add fiscal check if so.
**Rationale**: Constitution XXII requires fiscal period check before any GL posting.

To be verified during implementation: if delivery orders trigger stock movements that generate GL entries (inventory valuation JEs), a fiscal check is needed.
