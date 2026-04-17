# Quickstart: Audit Purchases Module

**Feature**: 011-audit-purchases | **Date**: 2026-04-15

## Overview

This audit fixes the purchases module for constitution compliance. No new features — only precision, error handling, fiscal period validation, and audit trail fixes.

## Prerequisites

- Branch `011-audit-purchases` checked out
- Python 3.12 with venv activated: `source .venv/bin/activate`
- Node.js installed for frontend build: `cd frontend && npm install`
- PostgreSQL running with at least one tenant DB

## Implementation Order

### Phase 1: Backend Schema Layer (Foundation)
1. Change Pydantic `float` → `Decimal` in `schemas/purchases.py` and `schemas/matching.py`
2. Change inline `float` → `Decimal` in `routers/matching.py` (ToleranceSave class)

### Phase 2: Backend Router float→str
3. Replace all `float()` → `str()` in `routers/purchases.py` (55 calls)
4. Replace all `float()` → `str()` in `routers/landed_costs.py` (6 calls)
5. Replace all `float()` → `str()` in `routers/matching.py` (13 calls)
6. Replace all `float()` → `str()` in `services/matching_service.py` (2 calls)

### Phase 3: Backend Fiscal Period Checks
7. Add `check_fiscal_period_open()` to `receive_purchase_order`
8. Add `check_fiscal_period_open()` to `create_purchase_return`
9. Add `check_fiscal_period_open()` to `create_purchase_credit_note`
10. Add `check_fiscal_period_open()` to `create_purchase_debit_note`

### Phase 4: Database Audit Columns (Triple-Update)
11. Create Alembic migration for all 11 tables
12. Update `database.py` CREATE TABLE definitions
13. Add `AuditMixin` to domain models

### Phase 5: Frontend parseFloat→String/Number/formatNumber
14. Fix top-5 files: BuyingOrderForm, PurchaseInvoiceForm, BuyingReturnForm, PaymentForm, BlanketPOForm
15. Fix remaining files with parseFloat

### Phase 6: Frontend toastEmitter→useToast Migration
16. Migrate 7 files from toastEmitter to useToast

### Phase 7: Frontend console.error→useToast
17. Add useToast to 16 files that have neither pattern
18. Replace console.error with showToast in all 36 files

### Phase 8: Verification
19. `python3 -m py_compile` on all modified backend files
20. `cd frontend && npx vite build` — zero errors

## Verification Commands

```bash
# Backend compile check
python3 -m py_compile backend/routers/purchases.py
python3 -m py_compile backend/routers/landed_costs.py
python3 -m py_compile backend/routers/matching.py
python3 -m py_compile backend/services/matching_service.py
python3 -m py_compile backend/schemas/purchases.py
python3 -m py_compile backend/schemas/matching.py

# Frontend build check
cd frontend && npx vite build

# Grep verification — should return zero results
grep -rn "float(" backend/routers/purchases.py backend/routers/landed_costs.py backend/routers/matching.py backend/services/matching_service.py | grep -v "# " | grep -v "def "
grep -rn "parseFloat" frontend/src/pages/Buying/ frontend/src/pages/Purchases/ frontend/src/pages/Matching/ frontend/src/pages/BlanketPO/
grep -rn "toastEmitter" frontend/src/pages/Buying/ frontend/src/pages/Purchases/ frontend/src/pages/Matching/ frontend/src/pages/BlanketPO/
```

## Key Patterns

### Backend float→str pattern
```python
# Before
"total": float(_dec(r.total))
# After  
"total": str(_dec(r.total))
```

### Frontend parseFloat→String (payload)
```js
// Before
quantity: parseFloat(item.quantity) || 0,
// After
quantity: String(item.quantity || 0),
```

### Frontend parseFloat→Number (local calc)
```js
// Before
const qty = parseFloat(item.quantity) || 0
// After
const qty = Number(item.quantity) || 0
```

### useToast addition
```js
import { useToast } from '../../context/ToastContext'
// Inside component function:
const { showToast } = useToast()
// In catch blocks:
showToast(err.response?.data?.detail || t('common.error'), 'error')
```

### Fiscal period check
```python
# Add before GL posting call:
check_fiscal_period_open(db, transaction_date)
```
