# Quickstart: Audit HR Module — تدقيق وحدة الموارد البشرية

**Feature**: 015-audit-hr  
**Date**: 2026-04-15

---

## What This Audit Does

Fixes financial precision, error handling, formatting consistency, branch security, PII protection, and audit trail completeness across the entire HR module (backend + frontend).

## Key Changes at a Glance

| Area | Change | Files |
|------|--------|-------|
| **Backend schemas** | `float` → `Decimal` for 31 monetary fields | `schemas/hr.py` |
| **Backend routers** | `float()` → `str()` serialization for 18+ calls | `routers/hr/core.py` |
| **EOS utility** | `float` → `Decimal` inputs/outputs | `utils/hr_helpers.py` |
| **PII masking** | New `mask_pii()` utility + `hr.pii` permission | `utils/masking.py` (new), `utils/permissions.py` |
| **Branch validation** | Add `validate_branch_access()` to 14 endpoints | `routers/hr/performance.py`, `routers/hr_wps_compliance.py`, `routers/hr/advanced.py` |
| **Frontend formatting** | `.toLocaleString()` → `formatNumber()` for 28 calls | 12 frontend files |
| **Frontend errors** | `console.error` → `toastEmitter.emit()` for 37 calls | 25 frontend files |
| **Audit trails** | Verify `AuditMixin` + complete `log_activity()` coverage | Models + all routers |

## How to Verify

```bash
# Backend: No float in HR schemas
grep -rn ": float" backend/schemas/hr.py | wc -l
# Expected: 0

# Backend: No float() in HR core router (monetary)
grep -n "float(" backend/routers/hr/core.py | grep -v "#\|import\|isinstance" | wc -l
# Expected: 0

# Backend: No float in EOS helper signature
grep -n "float" backend/utils/hr_helpers.py | wc -l
# Expected: 0

# Frontend: No console.error in HR pages
grep -rn "console\.error\|console\.log" frontend/src/pages/HR/ frontend/src/pages/SelfService/ frontend/src/pages/Performance/ frontend/src/pages/TimeTracking/ | wc -l
# Expected: 0

# Frontend: No toLocaleString for monetary values in HR pages
grep -rn "toLocaleString\|\.toFixed" frontend/src/pages/HR/ frontend/src/pages/SelfService/ frontend/src/pages/TimeTracking/ | grep -v "date\|Date\|time\|Time" | wc -l
# Expected: 0
```

## Patterns to Follow

### Backend: Decimal in Pydantic Schema
```python
from decimal import Decimal
class EmployeeCreate(BaseModel):
    salary: Decimal = Decimal("0")          # NOT float = 0
    housing_allowance: Decimal = Decimal("0")
```

### Backend: String Serialization in Router
```python
# BEFORE
"net_salary": float(row.net_salary or 0)
# AFTER  
"net_salary": str(row.net_salary or 0)
```

### Backend: PII Masking
```python
from utils.masking import mask_pii
# In employee response construction:
"iban": mask_pii(row.iban) if not has_pii_access else row.iban
```

### Frontend: formatNumber
```jsx
import { formatNumber } from '../../utils/format';
// BEFORE
<td>{v.deduction_amount?.toLocaleString()}</td>
// AFTER
<td>{formatNumber(v.deduction_amount)}</td>
```

### Frontend: Toast Error Handling
```jsx
import { toastEmitter } from '../../utils/toastEmitter';
// BEFORE
} catch (err) { console.error(err); }
// AFTER
} catch (err) { toastEmitter.emit(t('hr.xxx.error_loading'), 'error'); }
```

## Dependencies Between Changes

```
schemas/hr.py (Decimal types)
    ↓
routers/hr/core.py (str() serialization) ← depends on schemas
    ↓
Frontend pages (formatNumber display) ← backward compatible with string values
    
utils/hr_helpers.py (Decimal EOS) ← independent
utils/masking.py (PII) ← independent  
validate_branch_access() additions ← independent
console.error → toastEmitter ← independent
```

Backend schema + router changes should be done first (they're the foundation). Frontend and other backend changes are independent of each other.
