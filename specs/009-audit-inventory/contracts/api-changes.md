# API Contracts: Audit Inventory Module

**Feature**: 009-audit-inventory
**Date**: 2026-04-15

## Overview

This audit does not create new endpoints. It fixes the **response format** of existing endpoints to comply with Constitution §I (monetary values as strings, not floats).

## Contract Changes

### 1. Product Endpoints — Response Format Fix

**Endpoints affected**:
- `GET /inventory/products` (list)
- `GET /inventory/products/{id}` (detail)
- `GET /inventory/products/{id}/cost-breakdown` (cost view)

**Before (violation)**:
```json
{
  "id": 1,
  "product_name": "Widget A",
  "selling_price": 1250.75,
  "cost_price": 500.5,
  "buying_price": 480.0,
  "last_buying_price": 475.25,
  "tax_rate": 15.0,
  "current_stock": 100.0,
  "reserved_quantity": 10.0
}
```

**After (compliant)**:
```json
{
  "id": 1,
  "product_name": "Widget A",
  "selling_price": "1250.7500",
  "cost_price": "500.5000",
  "buying_price": "480.0000",
  "last_buying_price": "475.2500",
  "tax_rate": "15.00",
  "current_stock": "100.0000",
  "reserved_quantity": "10.0000"
}
```

**Rule**: All `NUMERIC(18,4)` and `NUMERIC(5,2)` fields return as string representations of their Decimal value. Integer fields (id, count) remain as integers.

---

### 2. Warehouse Endpoints — Response Format Fix

**Endpoints affected**:
- `GET /inventory/warehouses/{id}/current-stock`
- `GET /inventory/warehouses` (list with stock summary)

**Change**: `stock` and `quantity` fields: `float()` → `str()`

---

### 3. Stock Movements — Response Format Fix

**Endpoints affected**:
- `POST /inventory/receipt`
- `POST /inventory/delivery`
- `GET /inventory/movements` (list)

**Change**: `unit_cost` and `quantity` fields: `float()` → `str()`

---

### 4. Reports — Response Format Fix

**Endpoints affected**:
- `GET /inventory/reports/valuation-report`

**Change**: `total_quantity`, `moving_avg_cost`, `total_valuation`: `float()` → `str()`

---

### 5. Batches/Cycle Counts — Response Format Fix

**Endpoints affected**:
- `GET /inventory/cycle-counts/{id}` (items detail)
- `GET /inventory/batches` (list)

**Change**: `quantity`, `cost`, `system_quantity`, `unit_cost`: `float()` → `str()`

---

### 6. Cycle Count Completion — New GL Side Effect

**Endpoint**: `PUT /inventory/cycle-counts/{id}/complete`

**Before**: Creates `inventory_transactions` for variances when `auto_adjust=true`. No GL entry.

**After**: Same behavior + posts a balanced GL journal entry for each variance:
- Surplus (counted > system): Dr. Inventory Asset / Cr. Inventory Variance
- Shortage (counted < system): Dr. Inventory Variance / Cr. Inventory Asset
- Amount = `abs(variance) × unit_cost`
- Requires fiscal period to be open

---

### 7. Frontend Payload Contracts

**Forms affected** (API request body changes):

| Form | Field | Before | After |
|------|-------|--------|-------|
| StockTransferForm | `items[].quantity` | `parseFloat(item.quantity)` (number) | `String(item.quantity)` (string) |
| StockShipmentForm | `items[].quantity` | `parseFloat(currentItem.quantity)` (number) | `String(currentItem.quantity)` (string) |
| StockAdjustmentForm | `new_quantity` | `parseFloat(formData.new_quantity)` (number) | `String(formData.new_quantity)` (string) |
| BatchList (create) | `quantity`, `unit_cost` | `parseFloat(form.quantity)` (number) | `String(form.quantity)` (string) |
| CycleCounts | `counted_quantity` | `parseFloat(item.counted_quantity)` (number) | `String(item.counted_quantity)` (string) |
| QualityInspections | `min_value`, `max_value` | `parseFloat(c.min_value)` (number) | `String(c.min_value)` (string) |
| PriceListItems | `price` | `parseFloat(newPrice)` (number) | `String(newPrice)` (string) |

**Backend compatibility**: All inventory endpoints already use `Decimal(str(value))` parsing or SQLAlchemy's Numeric type coercion, which handles both string and number inputs. Sending strings is safe and preferred.

## Notification Endpoint Removal

**Endpoints removed from frontend service** (already unmounted on backend):
- `GET /inventory/notifications` → REMOVED (use `/notifications` instead)
- `GET /inventory/notifications/unread-count` → REMOVED (use `/notifications/unread-count`)
- `POST /inventory/notifications/{id}/read` → REMOVED (use `/notifications/{id}/read`)
- `POST /inventory/notifications/read-all` → REMOVED (use `/notifications/read-all`)

No frontend code calls these functions — removal is safe with zero caller impact.
