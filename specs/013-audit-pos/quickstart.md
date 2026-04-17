# Quickstart: Audit POS Module — تدقيق وحدة نقاط البيع

**Feature**: 013-audit-pos | **Date**: 2026-04-15

## Pattern Reference

This audit follows the same patterns established in 009-audit-inventory, 011-audit-purchases, and 012-audit-sales.

### Backend: float() → str() in Response Dicts
```python
# BEFORE
"total_amount": float(row.total_amount),

# AFTER
"total_amount": str(row.total_amount),
```

### Backend: Pydantic float → Decimal
```python
# BEFORE
from pydantic import BaseModel
class OrderCreate(BaseModel):
    discount_amount: float = 0

# AFTER
from decimal import Decimal
from pydantic import BaseModel
class OrderCreate(BaseModel):
    discount_amount: Decimal = Decimal("0")
```

### Backend: AuditMixin Addition
```python
# BEFORE
class PosSession(ModelBase):
    __tablename__ = "pos_sessions"

# AFTER
class PosSession(AuditMixin, ModelBase):
    __tablename__ = "pos_sessions"
```

### Backend: Fiscal Period Check
```python
# BEFORE (create_order already has it)
check_fiscal_period_open(db, company_id, date.today())

# ADD to close_session and create_return before GL posting
check_fiscal_period_open(db, company_id, date.today())
```

### Backend: Audit Columns in database.py
```python
# Add to sync_essential_columns() for each POS table:
ensure_column(conn, 'pos_sessions', 'created_by', 'VARCHAR(100)')
ensure_column(conn, 'pos_sessions', 'updated_by', 'VARCHAR(100)')
ensure_column(conn, 'pos_sessions', 'created_at', 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()')
# ... repeat for all 14 POS tables
```

### Frontend: parseFloat → Number for calc
```jsx
// BEFORE
const total = parseFloat(value);

// AFTER
const total = Number(value);
```

### Frontend: toLocaleString → formatNumber
```jsx
// BEFORE
{amount.toLocaleString()}

// AFTER
import { formatNumber } from '../../utils/formatNumber';
{formatNumber(amount)}
```

### Frontend: console.error → useToast
```jsx
// BEFORE
console.error('Failed to load:', error);

// AFTER (most files already have useToast)
showToast(t('pos.loadError'), 'error');
```

## File Checklist

### Backend (4 files)
- [ ] `backend/routers/pos.py` — 31 float() → str(), 2 fiscal checks added
- [ ] `backend/schemas/pos.py` — 23 float → Decimal fields
- [ ] `backend/models/domain_models/sales_pos.py` — AuditMixin on 16 models
- [ ] `backend/database.py` — 14 POS tables in sync_essential_columns

### Frontend (9 files, 2 clean)
- [ ] `POSHome.jsx` — 1 parseFloat, 3 console.error
- [ ] `POSInterface.jsx` — 2 parseFloat, 4 console.error, 14 toLocaleString
- [ ] `POSOfflineManager.jsx` — 2 console.error, add useToast import
- [ ] `TableManagement.jsx` — 1 console.error
- [ ] `KitchenDisplay.jsx` — 1 console.error
- [ ] `LoyaltyPrograms.jsx` — 2 parseFloat, 1 console.error
- [ ] `Promotions.jsx` — 2 parseFloat, 1 console.error
- [ ] `POSReturns.jsx` — 1 toLocaleString
- [ ] `HeldOrders.jsx` — 2 console.error, 5 console.log, 1 toLocaleString
- [x] `CustomerDisplay.jsx` — Clean (already uses formatNumber)
- [x] `ThermalPrintSettings.jsx` — Clean (toLocaleString is for dates only)
