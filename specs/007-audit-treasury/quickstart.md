# Quickstart: audit-treasury Implementation Guide

**Date**: 2026-04-14  
**Branch**: `007-audit-treasury`

## 1. Database Migration (run first)

Create a new Alembic migration:

```bash
cd backend
alembic revision --autogenerate -m "audit_treasury_fixes"
```

### Schema Changes (copy into migration)

```sql
-- 1. Fix TreasuryAccount balance type: float → Decimal (R-010)
ALTER TABLE treasury_accounts
  ALTER COLUMN current_balance TYPE NUMERIC(20, 4)
    USING current_balance::NUMERIC(20, 4);

-- 2. Add overdraft policy column (R-004)
ALTER TABLE treasury_accounts
  ADD COLUMN allow_overdraft BOOLEAN;
-- NULL = follow account_type default (cash=reject, bank=allow)

-- 3. Add exchange_rate to treasury_transactions (R-009)
ALTER TABLE treasury_transactions
  ADD COLUMN exchange_rate NUMERIC(12, 6) NOT NULL DEFAULT 1.0,
  ADD COLUMN currency VARCHAR(3) NOT NULL DEFAULT 'SAR';

-- 4. Add re-presentation fields to checks_receivable (R-003)
ALTER TABLE checks_receivable
  ADD COLUMN exchange_rate NUMERIC(12, 6) NOT NULL DEFAULT 1.0,
  ADD COLUMN re_presentation_date DATE,
  ADD COLUMN re_presentation_count INT NOT NULL DEFAULT 0,
  ADD COLUMN re_presentation_journal_id INT;

-- 5. Add re-presentation fields to checks_payable
ALTER TABLE checks_payable
  ADD COLUMN exchange_rate NUMERIC(12, 6) NOT NULL DEFAULT 1.0,
  ADD COLUMN re_presentation_date DATE,
  ADD COLUMN re_presentation_count INT NOT NULL DEFAULT 0,
  ADD COLUMN re_presentation_journal_id INT;

-- 6. Add exchange_rate to notes_receivable (R-009)
ALTER TABLE notes_receivable
  ADD COLUMN exchange_rate NUMERIC(12, 6) NOT NULL DEFAULT 1.0;

-- 7. Add exchange_rate to notes_payable
ALTER TABLE notes_payable
  ADD COLUMN exchange_rate NUMERIC(12, 6) NOT NULL DEFAULT 1.0;

-- 8. Add reconciliation tolerance setting (R-006)
-- Insert via application code into company_settings table:
-- key='reconciliation_tolerance', value='1.00'
```

## 2. Files to Modify (in order)

### Step 1: Model Updates

| File | Change |
|------|--------|
| `models/domain_models/core_business.py` | `TreasuryAccount.current_balance`: change `Float` → `Numeric(20, 4)`. Add `allow_overdraft = Column(Boolean, nullable=True)` |
| `models/domain_models/operations_financial_support.py` | Add `exchange_rate`, `re_presentation_date`, `re_presentation_count`, `re_presentation_journal_id` to `CheckReceivable` / `CheckPayable`. Add `exchange_rate` to `NoteReceivable` / `NotePayable` |
| `models/domain_models/finance_treasury_tax.py` | `TreasuryTransaction`: add `exchange_rate = Column(Numeric(12,6), default=1.0)`, `currency = Column(String(3), default='SAR')` |

### Step 2: Utility — ensure_treasury_gl_accounts()

Create `utils/treasury_gl.py`:

```python
"""Auto-create required GL accounts for treasury if missing (R-005)."""
from sqlalchemy import text
from backend.utils.audit import log_activity

REQUIRED_ACCOUNTS = {
    1205: {"name": "شيكات تحت التحصيل", "name_en": "Checks Under Collection", "parent_id": 1200},
    2105: {"name": "شيكات مستحقة الدفع", "name_en": "Checks Payable", "parent_id": 2100},
    1210: {"name": "أوراق قبض", "name_en": "Notes Receivable", "parent_id": 1200},
    2110: {"name": "أوراق دفع", "name_en": "Notes Payable", "parent_id": 2100},
}

async def ensure_treasury_gl_accounts(db, company_id, user_id, username, request=None):
    for code, meta in REQUIRED_ACCOUNTS.items():
        row = await db.execute(text(
            "SELECT id FROM accounts WHERE code = :code"
        ), {"code": str(code)})
        if row.scalar() is None:
            result = await db.execute(text("""
                INSERT INTO accounts (code, name, name_en, parent_id, is_active, account_type)
                VALUES (:code, :name, :name_en, :parent_id, true, 'asset')
                RETURNING id
            """), {"code": str(code), **meta})
            new_id = result.scalar()
            await log_activity(db, user_id, username, "auto_create",
                "gl_account", new_id,
                {"code": code, "reason": "treasury_module_init"},
                request)
```

### Step 3: Router Fixes

**`routers/finance/treasury.py`**:

1. **Expense endpoint**: Reorder to GL-first → balance-update-second (R-001)
2. **Both expense/transfer**: Add `SELECT FOR UPDATE` on treasury row (R-002):
   ```python
   row = await db.execute(text(
       "SELECT current_balance, allow_overdraft, account_type "
       "FROM treasury_accounts WHERE id = :id FOR UPDATE"
   ), {"id": treasury_id})
   ```
3. **Both endpoints**: Add overdraft check (R-004):
   ```python
   if account_type == 'cash' and allow_overdraft is not True:
       if current_balance - amount < 0:
           raise HTTPException(400, "رصيد غير كافٍ")
   ```
4. **Opening balance**: Add fiscal period check (R-008)
5. **All mutations**: Persist `exchange_rate` in transaction record (R-009)

**`routers/finance/checks.py`**:

1. **Create**: Add duplicate check number warning (R-007) — return 409 with existing check info
2. **Create**: Call `ensure_treasury_gl_accounts()` (R-005)
3. **Collect/bounce/cancel**: Add `SELECT FOR UPDATE` (R-002)
4. **New endpoint**: Add `POST /{id}/represent` (R-003)
5. **All**: Persist `exchange_rate` (R-009)

**`routers/finance/notes.py`**:

1. **Collect**: Add `SELECT FOR UPDATE` (R-002)
2. **Create**: Persist `exchange_rate` (R-009)

**`routers/finance/reconciliation.py`**:

1. **Auto-match**: Add `branch_id` filter
2. **Finalize**: Read `reconciliation_tolerance` from company_settings (R-006)

### Step 4: Test Updates

Create/update test files:

| File | Coverage |
|------|----------|
| `tests/test_treasury_gl_first.py` | Verify GL entry exists when balance update fails |
| `tests/test_treasury_concurrency.py` | Concurrent expense requests → one succeeds, one blocked |
| `tests/test_check_represent.py` | Bounced → represent → pending flow |
| `tests/test_overdraft_policy.py` | Cash reject / bank allow / explicit override |
| `tests/test_duplicate_check.py` | Same check_number + bank_name → 409 warning |
| `tests/test_recon_tolerance.py` | Finalize within/outside tolerance |

## 3. Key Patterns to Follow

### GL-First Pattern
```python
# CORRECT: GL entry first, then balance
journal_id, _ = await create_journal_entry(db, company_id, ...)
await db.execute(text(
    "UPDATE treasury_accounts SET current_balance = current_balance - :amt WHERE id = :id"
), {"amt": amount, "id": treasury_id})
```

### SELECT FOR UPDATE Pattern
```python
# Lock the row before reading balance
row = await db.execute(text(
    "SELECT current_balance FROM treasury_accounts WHERE id = :id FOR UPDATE"
), {"id": treasury_id})
balance = row.scalar()
```

### Fiscal Lock Pattern
```python
from backend.utils.fiscal_lock import check_fiscal_period_open
await check_fiscal_period_open(db, entry_date, raise_error=True)
```

### Audit Trail Pattern
```python
from backend.utils.audit import log_activity
await log_activity(db, user_id, username, "create", "check_receivable",
    check_id, {"amount": amount, "check_number": number}, request)
```

## 4. Verification Checklist

After implementation, verify:

- [ ] `current_balance` stored as Numeric, not float
- [ ] All treasury mutations: GL before balance
- [ ] All treasury mutations: SELECT FOR UPDATE on balance row
- [ ] Cash accounts: overdraft rejected by default
- [ ] Bounced checks: re-presentation endpoint works
- [ ] Duplicate check numbers: returns 409 warning
- [ ] Bank reconciliation: respects tolerance setting
- [ ] Opening balance: fiscal lock enforced
- [ ] GL accounts 1205/2105/1210/2110: auto-created if missing
- [ ] exchange_rate persisted on all foreign-currency transactions
