# Quickstart: Audit Inventory Module

**Feature**: 009-audit-inventory
**Date**: 2026-04-15

## Prerequisites

- Python 3.12 with virtual environment activated
- Node.js 18+ with npm
- PostgreSQL 15 running with tenant databases
- Redis running

## Development Setup

```bash
# 1. Switch to feature branch
cd /home/omar/Desktop/aman
git checkout 009-audit-inventory

# 2. Backend
cd backend
source ../.venv/bin/activate
pip install -r requirements.txt

# 3. Frontend
cd ../frontend
npm install

# 4. Start services
cd ..
./start-local.sh
```

## Verification Commands

### Backend — Python syntax check
```bash
cd backend
python -m py_compile routers/inventory/products.py
python -m py_compile routers/inventory/stock_movements.py
python -m py_compile routers/inventory/warehouses.py
python -m py_compile routers/inventory/reports.py
python -m py_compile routers/inventory/batches.py
python -m py_compile routers/inventory/adjustments.py
python -m py_compile routers/inventory/transfers.py
python -m py_compile routers/inventory/shipments.py
```

### Frontend — Build check
```bash
cd frontend
npx vite build
```

### Lint
```bash
cd backend
ruff check routers/inventory/
```

## What This Audit Changes

| Category | Files | Change Type |
|----------|-------|-------------|
| Backend float→str | 5 router files | `float(x)` → `str(x)` in API responses |
| Frontend parseFloat→String | 7 page files + 1 forecast file | `parseFloat(x)` → `String(x)` in payloads |
| Frontend error handling | 17 page files | Add `useToast` import + `showToast()` calls |
| Dead code removal | 1 service file | Remove 4 unused notification functions |
| Cycle count GL fix | 1 router file (batches.py) | Add `gl_create_journal_entry()` call |
| Missing audit columns | 3 files (migration + database.py + model) | `ALTER TABLE ADD COLUMN` |
| Negative stock check | 1 router file (batches.py) | Add qty check in cycle count auto-adjust |

## Key Patterns

### Backend: Converting float → str
```python
# Before (violation):
"selling_price": float(row.selling_price or 0),

# After (compliant):
"selling_price": str(row.selling_price or 0),
```

### Frontend: Converting parseFloat → String  
```javascript
// Before (violation):
quantity: parseFloat(item.quantity)

// After (compliant):
quantity: String(item.quantity)
```

### Frontend: Adding useToast error handling
```javascript
// Import
import { useToast } from '../../context/ToastContext'

// In component
const { showToast } = useToast()

// In catch block
showToast(err.response?.data?.detail || t('stock.action.error'), 'error')
```

### Backend: GL entry for cycle count variance
```python
# Follow adjustments.py pattern:
# 1. check_fiscal_period_open(db, date)
# 2. Build lines (Dr/Cr based on surplus/shortage)
# 3. gl_create_journal_entry(db, company_id, date, description, lines, user_id, branch_id, reference, currency)
```

## Testing Approach

1. **After each backend change**: `python -m py_compile <file>`
2. **After each frontend change**: `npx vite build`
3. **After all changes**: Full `./start-local.sh` and manual smoke test
4. **Migration**: Apply to dev tenant, verify columns exist
