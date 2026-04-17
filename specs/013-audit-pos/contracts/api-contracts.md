# API Contracts: Audit POS Module — تدقيق وحدة نقاط البيع

**Feature**: 013-audit-pos | **Date**: 2026-04-15

## Overview

This document describes **type changes** to existing POS API responses. No new endpoints are added. All numeric monetary/quantity values change from `float` → `string` (JSON) / `Decimal` (Pydantic) for precision.

---

## 1. Session Endpoints

### POST /api/pos/sessions — Create Session
**Request body changes:**
| Field | Before | After |
|-------|--------|-------|
| opening_balance | `number` (float) | `string` (Decimal) |

### PUT /api/pos/sessions/{id}/close — Close Session
**Request body changes:**
| Field | Before | After |
|-------|--------|-------|
| closing_balance | `number` (float) | `string` (Decimal) |
| cash_register_balance | `number` (float) | `string` (Decimal) |

**Response changes:** All numeric monetary fields serialized as `string`:
- `opening_balance`, `closing_balance`, `total_sales`, `total_cash`, `total_bank`, `total_returns`, `total_returns_cash`, `difference`

**New behavior:** `check_fiscal_period_open()` called before GL posting.

### GET /api/pos/sessions — List Sessions
**Response changes:** All `SessionResponse` monetary fields → `string`.

---

## 2. Order Endpoints

### POST /api/pos/orders — Create Order
**Request body changes:**
| Field | Before | After |
|-------|--------|-------|
| discount_amount | `number` (float) | `string` (Decimal) |
| paid_amount | `number` (float) | `string` (Decimal) |
| lines[].quantity | `number` (float) | `string` (Decimal) |
| lines[].unit_price | `number` (float) | `string` (Decimal) |
| lines[].discount_amount | `number` (float) | `string` (Decimal) |
| lines[].tax_rate | `number` (float) | `string` (Decimal) |
| payments[].amount | `number` (float) | `string` (Decimal) |

**Response changes:** `total_amount` → `string`

### GET /api/pos/orders/{id} — Get Order
**Response changes:** Same as OrderResponse — `total_amount` → `string`

---

## 3. Return Endpoints

### POST /api/pos/returns — Create Return
**Request body changes:**
| Field | Before | After |
|-------|--------|-------|
| items[].quantity | `number` (float) | `string` (Decimal) |

**New behavior:** `check_fiscal_period_open()` called before GL posting.

---

## 4. Product Endpoints

### GET /api/pos/products — List POS Products
**Response changes:**
| Field | Before | After |
|-------|--------|-------|
| price | `number` (float) | `string` (Decimal) |
| stock_quantity | `number` (float) | `string` (Decimal) |
| tax_rate | `number` (float) | `string` (Decimal) |

---

## 5. Backend Serialization Changes

All `float()` calls in `pos.py` response dictionaries change to `str()`:

| Location | Context | Before | After |
|----------|---------|--------|-------|
| Response dicts (Cat A, 11 calls) | Monetary values in responses | `float(row.amount)` | `str(row.amount)` |
| SQL parameters (Cat B, 5 calls) | Values sent to SQL queries | `float(value)` | Keep as-is (DB handles Decimal) |
| Error messages (Cat C, 13 calls) | Logging/error strings | `float(value)` | `str(value)` |
| CostingService (Cat D, 1 call) | Service parameter | `float(item.quantity)` | Remove float() wrapper |

---

## 6. Frontend Contract Changes

All frontend components must send numeric strings instead of parsed floats:

| Component | Pattern | Before | After |
|-----------|---------|--------|-------|
| POSInterface.jsx | parseFloat (2 calls) | `parseFloat(value)` | `Number(value)` for calc, `String(value)` for API |
| POSHome.jsx | parseFloat (1 call) | `parseFloat(value)` | `Number(value)` for local calc |
| LoyaltyPrograms.jsx | parseFloat (2 calls) | `parseFloat(value)` | `Number(value)` for calc |
| Promotions.jsx | parseFloat (2 calls) | `parseFloat(value)` | `Number(value)` for calc |

All monetary `.toLocaleString()` calls (16 occurrences across 3 files) → `formatNumber()` from shared utility.

**Exception**: Date `.toLocaleString('ar-SA')` calls in POSOfflineManager.jsx and ThermalPrintSettings.jsx are **kept unchanged**.
