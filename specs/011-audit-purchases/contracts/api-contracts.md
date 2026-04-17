# API Contracts: Audit Purchases Module

**Feature**: 011-audit-purchases | **Date**: 2026-04-15

## Contract Changes Summary

This audit does NOT change API routes, request shapes, or add/remove endpoints. It changes the **serialization type** of monetary fields from JSON `number` to JSON `string` in all purchase-related API responses.

## Response Field Type Changes

### Before (current — violates Constitution §I)

```json
{
  "total": 1250.75,
  "paid_amount": 0.0,
  "exchange_rate": 1.0,
  "quantity": 7.0,
  "unit_price": 125.075
}
```

### After (fixed — compliant)

```json
{
  "total": "1250.7500",
  "paid_amount": "0.0000",
  "exchange_rate": "1.0000",
  "quantity": "7.0000",
  "unit_price": "125.0750"
}
```

## Affected Endpoints

All purchase-related endpoints that return monetary/quantity values in their response:

| Router | Endpoints affected | Fields changing from number→string |
|--------|-------------------|-----------------------------------|
| `purchases.py` | GET/POST purchase orders, invoices, returns, credit/debit notes, supplier payments, RFQ, agreements, blanket POs | total, paid_amount, exchange_rate, quantity, unit_price, balance, amount, remaining, etc. |
| `landed_costs.py` | GET/POST landed costs, allocations | allocated, new_cost, total_allocated, total_cost |
| `matching.py` | GET matches, tolerances | po_quantity, received_quantity, invoiced_quantity, variance_pct, variance_abs, tolerance values |

## Request Body Changes

### Pydantic Schema Changes

Request bodies previously accepted `float` — now accept `Decimal`. Pydantic `Decimal` accepts BOTH:
- JSON string: `"quantity": "7.5"` (preferred)
- JSON number: `"quantity": 7.5` (still accepted, converted to Decimal)

**No breaking change for existing API clients.** Clients sending numeric values will continue to work. Clients can optionally start sending string values for full precision.

## Fiscal Period Enforcement — New Error Response

### Endpoints gaining fiscal period validation

4 endpoints will now return HTTP 400 when fiscal period is closed:

1. `POST /api/purchases/returns` (create_purchase_return)
2. `POST /api/purchases/credit-notes` (create_purchase_credit_note)  
3. `POST /api/purchases/debit-notes` (create_purchase_debit_note)
4. `POST /api/purchases/orders/{id}/receive` (receive_purchase_order)

### Error response shape

```json
{
  "detail": "Fiscal period is closed for date 2026-03-15"
}
```

HTTP Status: `400 Bad Request`

This matches the existing pattern from `create_purchase_invoice` and `post_landed_cost`.

## Frontend Contract

### parseFloat → replacement mapping

| Context | Before | After |
|---------|--------|-------|
| API payload construction | `parseFloat(value) \|\| 0` | `String(value \|\| 0)` |
| Local calculation (UI only) | `parseFloat(value) \|\| 0` | `Number(value) \|\| 0` |
| Display rendering | `parseFloat(value).toFixed(2)` | `formatNumber(value)` |

### Error handling contract

| Before | After |
|--------|-------|
| `console.error(err)` | `showToast(t('error.key'), 'error')` |
| `toastEmitter.emit(msg, 'error')` | `showToast(msg, 'error')` |

### Import pattern

```js
// Add to files missing useToast
import { useToast } from '../../context/ToastContext'

// Inside component
const { showToast } = useToast()

// Replace in catch blocks
showToast(err.response?.data?.detail || t('common.error'), 'error')
```
