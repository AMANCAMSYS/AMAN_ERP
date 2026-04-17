# Quickstart: Audit Sales Module

**Feature**: 012-audit-sales | **Date**: 2026-04-15

## What This Audit Does

Fixes numeric precision, error handling, and audit infrastructure across the entire sales module:

1. **Backend**: Replaces `float()` with `str()` in 12 router/service files; changes Pydantic `float` fields to `Decimal` in 4 schema files
2. **Frontend**: Replaces `parseFloat()` with `Number()`/`String()` in 38 JSX files; replaces `console.error`/`toastEmitter` with `useToast`/`showToast`
3. **Models**: Adds `AuditMixin` to sales-exclusive domain models
4. **Database**: Adds missing `updated_at`, `created_by`, `updated_by` columns to sales tables
5. **Verification**: Verifies existing fiscal period checks; verifies commission calculation correctness

## File Scope

- **Backend routers** (11): `sales/customers.py`, `quotations.py`, `orders.py`, `invoices.py`, `returns.py`, `credit_notes.py`, `vouchers.py`, `cpq.py`, `sales_improvements.py`, `schemas.py`, `delivery_orders.py`
- **Backend service** (1): `services/cpq_service.py`
- **Backend schemas** (4): `schemas/sales_credit_notes.py`, `schemas/sales_improvements.py`, `schemas/cpq.py`, `routers/sales/schemas.py`
- **Backend models** (1): `models/domain_models/sales_rfq.py` (+ verify `sales_customers_delivery.py`)
- **Backend database** (1): `database.py`
- **Frontend Sales** (34): All files in `pages/Sales/`
- **Frontend CPQ** (4): All files in `pages/CPQ/`

## Patterns Reference

### Backend: float → str
```python
# Before
"total": float(row.total),
# After
"total": str(row.total or 0),
```

### Backend: Pydantic float → Decimal
```python
# Before
quantity: float = 1
# After
from decimal import Decimal
quantity: Decimal = Decimal("1")
```

### Frontend: parseFloat → Number/String
```javascript
// Local calculation (before → after)
const qty = parseFloat(item.quantity) || 0
const qty = Number(item.quantity) || 0

// API payload (before → after)  
quantity: parseFloat(item.quantity) || 0,
quantity: String(item.quantity || 0),
```

### Frontend: console.error → showToast
```javascript
// Add import
import { useToast } from '../../context/ToastContext';

// Add hook
const { showToast } = useToast();

// Replace
console.error('Error:', err);
showToast(t('common.error'), 'error');
```

### Frontend: toastEmitter → useToast
```javascript
// Remove
import { toastEmitter } from '../../utils/toastEmitter';
toastEmitter.emit('error', 'Something failed');

// Replace with
import { useToast } from '../../context/ToastContext';
const { showToast } = useToast();
showToast(t('common.error'), 'error');
```

## Verification Commands

```bash
# Backend compilation check
cd backend && python -m py_compile routers/sales/customers.py  # repeat for all files

# Frontend build check
cd frontend && npx vite build

# Violation count (should be 0 after audit)
grep -rn "float(" backend/routers/sales/ backend/routers/delivery_orders.py backend/services/cpq_service.py | grep -v "# " | wc -l
grep -rn "parseFloat" frontend/src/pages/Sales/ frontend/src/pages/CPQ/ | wc -l
grep -rn "console\.error" frontend/src/pages/Sales/ frontend/src/pages/CPQ/ | wc -l
grep -rn "toastEmitter" frontend/src/pages/Sales/ frontend/src/pages/CPQ/ | wc -l
```

## Out of Scope

- Cross-module files (inventory, GL, treasury, taxes, approvals, CRM) — boundary verification only
- ZATCA XML/QR logic — only numeric precision at ZATCA function boundary
- POS-shared models — deferred to POS audit
- New features or business logic changes (except commission functional verification)
