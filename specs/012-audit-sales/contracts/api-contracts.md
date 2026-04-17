# API Contracts: Audit Sales Module

**Feature**: 012-audit-sales | **Date**: 2026-04-15

> This audit modifies the **type** of existing API response fields from `float` to `string`. No new endpoints are created. No fields are added or removed.

## Contract Changes

### Response Field Type Changes

All monetary, quantity, rate, discount, and tax fields in API responses change from `float` to `string`:

**Before** (current):
```json
{
  "total_revenue": 15432.50,
  "total_receivables": 8721.33,
  "exchange_rate": 3.7505
}
```

**After** (audit-fixed):
```json
{
  "total_revenue": "15432.50",
  "total_receivables": "8721.33",
  "exchange_rate": "3.7505"
}
```

### Affected Endpoints

| Router File | Endpoints Affected | Field Type Change |
|-------------|-------------------|-------------------|
| sales/customers.py | GET /stats, GET /list, GET /{id} | float → str for revenue, receivables, balances |
| sales/quotations.py | POST, GET, PUT | float → str for amounts, totals, discounts |
| sales/orders.py | POST, GET, PUT | float → str for amounts, totals, tax |
| sales/invoices.py | POST, GET, PUT | float → str for amounts, tax, discount, exchange_rate |
| sales/returns.py | POST, GET | float → str for quantities, amounts |
| sales/credit_notes.py | POST credit/debit notes | float → str for amounts, tax (already uses Decimal in schema) |
| sales/vouchers.py | POST receipts/payments | float → str for amounts, exchange_rate |
| sales/cpq.py | POST /price, GET quotes | float → str for prices, adjustments |
| sales/sales_improvements.py | POST /commissions/calculate, GET aging | float → str for commission amounts, aging balances |
| delivery_orders.py | POST, GET, PUT | float → str for quantities, amounts |

### Request Payload Changes

Pydantic schemas change from `float` to `Decimal`, which accepts both `"10.05"` (string) and `10.05` (number) inputs. **This is backward compatible** — existing clients sending numeric values will still work; Pydantic coerces both to `Decimal`.

### New Response Fields (Audit Columns)

All sales entity responses will now include (where previously absent):

```json
{
  "created_at": "2026-04-15T10:30:00+03:00",
  "updated_at": "2026-04-15T10:30:00+03:00",
  "created_by": "admin",
  "updated_by": "admin"
}
```

These are **additive** — new fields in responses; no existing fields removed.

### Breaking Change Assessment

| Change | Breaking? | Mitigation |
|--------|-----------|------------|
| Response float → string | **Semi-breaking** | Frontend already handles both; backend consumers must use `Decimal(value)` or `float(value)` on receipt |
| Request float → Decimal schema | **Non-breaking** | Pydantic accepts both types |
| New audit columns in response | **Non-breaking** | Additive fields |

**Note**: The frontend is being updated simultaneously in this audit to consume string values, so the change is coordinated.
