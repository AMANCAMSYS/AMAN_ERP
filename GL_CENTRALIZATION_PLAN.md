# P0 FIX: GL Centralization & DB Trigger — Implementation Plan

**Date:** 2026-03-29  
**Status:** Planning Phase  
**Goal:** Replace 75+ repetitive journal entry insertions with centralized `gl_service.py`

---

## CURRENT STATE ASSESSMENT

### ✅ Already Implemented

1. **Database Trigger (check_journal_balance)**
   - Location: `backend/database.py` line 366-382
   - Status: ✓ ACTIVE
   - Functionality: Validates `SUM(debit) = SUM(credit)` within 0.01 on journal_lines INSERT/UPDATE
   - Constraint: DEFERRABLE INITIALLY DEFERRED (allows bulk inserts)

2. **GL Service Interface (gl_service.py)**
   - Location: `backend/services/gl_service.py` line 1-160
   - Function: `create_journal_entry(db, company_id, date, description, lines, user_id, ...)`
   - Status: ✓ COMPLETE & READY TO USE
   - Features:
     - ✓ Validates lines balance
     - ✓ Checks fiscal period not closed
     - ✓ Generates sequential entry number
     - ✓ Inserts header + lines
     - ✓ Updates account balances if posted
     - ✓ Returns (journal_id, entry_number)

### 📊 Duplication Analysis

**Files with Journal Entry Insertions:**

| File | Count | Impact |
|------|-------|--------|
| routers/finance/accounting.py | 12 | Reversal, FY closing, recurring, opening balances, provisions, FX revaluation |
| routers/finance/checks.py | 8 | Check clearance, bounce, issuance |
| routers/sales/vouchers.py | 2 | Receipt, payment |
| routers/sales/returns.py | 1 | Return approval |
| routers/sales/credit_notes.py | 2 | Credit note, debit note |
| routers/inventory/adjustments.py | 1 | Stock adjustment |
| routers/inventory/transfers.py | 2 | Cross-branch transfer, same-branch transfer |
| routers/delivery_orders.py | 1 | Delivery order invoice + COGS |
| routers/landed_costs.py | 1 | Landed cost distribution |
| routers/hr_wps_compliance.py | 1 | End of service settlement |
| routers/manufacturing/core.py | 2 | Production start, completion |
| routers/finance/treasury.py | 3 | Treasury transaction, expense, transfer |
| routers/finance/notes.py | 6 | Receivable/payable notes |
| routers/finance/assets.py | 6 | Asset transactions |
| routers/purchases.py | 7 | Purchase invoice, returns, down payments |
| routers/projects.py | 6 | Project costing |
| routers/hr/core.py | 2 | Payroll posting, loan processing |
| routers/sales/sales_improvements.py | 1 | Commission payout |
| routers/system_completion.py | 1 | Zakat posting |
| routers/finance/intercompany.py | 2 | Intercompany transaction, revenue recognition |
| routers/finance/currencies.py | 1 | Currency revaluation |
| scripts/populate_company_data.py | 13 | Sample data insertion |

**Total: 75+ occurrences across 22 files**

---

## IMPLEMENTATION STRATEGY

### Phase 1: Refactoring (High Priority)

**Priority 1 — Core Financial Workflows**

| Priority | File | Function | Expected Change | Risk | Effort |
|----------|------|----------|-----------------|------|--------|
| 1 | routers/sales/invoices.py | Invoice creation GL posting | Replace 2 INSERT blocks with `create_journal_entry()` | LOW | 1h |
| 2 | routers/finance/accounting.py | Reversals, closing, provisions | Replace 12 INSERT patterns → 4-6 `create_journal_entry()` calls | MEDIUM | 4h |
| 3 | routers/finance/checks.py | Check operations | Replace 8 INSERT patterns → 3 `create_journal_entry()` calls | LOW | 2h |
| 4 | routers/pos.py | POS order GL posting | Replace 2 INSERT patterns | LOW | 1h |
| 5 | routers/finance/treasury.py | Treasury GL posting | Replace 3 INSERT patterns | MEDIUM | 2h |

**Priority 2 — Secondary Workflows**

| Priority | File | Expected Effort |
|----------|------|-----------------|
| 6 | routers/purchases.py | 2h (7 patterns) |
| 7 | routers/hr/core.py | 1h (2 patterns) |
| 8 | routers/sales/returns.py | 1h (1 pattern) |
| 9 | routers/inventory/* | 2h (3 patterns) |
| 10 | routers/finance/notes.py | 1.5h (6 patterns) |
| 11 | routers/finance/assets.py | 1.5h (6 patterns) |

**Priority 3 — Tertiary/Specialized**

| File | Patterns | Effort |
|------|----------|--------|
| routers/sales/credit_notes.py | 2 | 1h |
| routers/delivery_orders.py | 1 | 0.5h |
| routers/landed_costs.py | 1 | 0.5h |
| routers/hr_wps_compliance.py | 1 | 0.5h |
| routers/manufacturing/core.py | 2 | 1h |
| routers/sales/vouchers.py | 2 | 1h |
| routers/sales/sales_improvements.py | 1 | 0.5h |
| routers/system_completion.py | 1 | 0.5h |
| routers/finance/intercompany.py | 2 | 1h |
| routers/finance/currencies.py | 1 | 0.5h |
| routers/projects.py | 6 | 2h |
| scripts/populate_company_data.py | 13 | 1h (bulk/data) |

---

## REFACTORING PATTERN

### Current Pattern (Duplicate)
```python
# Before: Scattered across 75+ locations
je_number = _generate_sequential_number(db, "JE", "journal_entries", "entry_number")
je_id = db.execute(text("""
    INSERT INTO journal_entries (entry_number, entry_date, ...) 
    VALUES (:num, :date, ...)
    RETURNING id
"""), {...}).scalar()

for line in lines:
    db.execute(text("""
        INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, ...)
        VALUES (:jid, :aid, :debit, :credit, ...)
    """), {...})
    update_account_balance(db, account_id, debit, credit)
```

### New Pattern (Centralized)
```python
# After: Single call, all locations
from services.gl_service import create_journal_entry

je_id, je_number = create_journal_entry(
    db=db,
    company_id=current_user.company_id,
    date=transaction_date,
    description="Transaction description",
    lines=[
        {"account_id": 101, "debit": 1000, "credit": 0, "description": "Line 1"},
        {"account_id": 102, "debit": 0, "credit": 1000, "description": "Line 2"},
    ],
    user_id=current_user.id,
    branch_id=current_user.branch_id,
    reference="INV-001",
    currency="SAR",
    exchange_rate=1.0,
    source="invoice",
    source_id=invoice_id
)
```

---

## REFACTORING SEQUENCE

### Week 1

**Day 1-2: Core Setup & Testing**
- ✓ Verify gl_service.py works with diverse scenarios
- ✓ Write test cases for all branch scenarios
- Create test fixtures

**Day 3: Sales Invoice GL**
- Refactor `routers/sales/invoices.py`
  - Lines: ~350-380 (AR/Revenue/VAT/COGS posting)
  - Lines: ~950-1050 (Payment posting)
- Test: Create invoice → verify GL entries are balanced

**Day 4-5: Accounting Module**
- Refactor `routers/finance/accounting.py`
  - Lines ~888-950: Reversal posting
  - Lines ~1281-1350: FY closing
  - Lines ~1428-1500: Reopening/reversal
  - Lines ~1906-1970: Recurring entry posting
  - Lines ~2086-2150: Opening balances
  - Lines ~2300-2370: Period closing (revenue/expense)
  - Lines ~2454-2520: Bad debt provision
  - Lines ~2501-2570: Leave provision
  - Lines ~2578-2643: FX revaluation
- Test: Each scenario independently

### Week 2

**Day 1-2: Checks & Treasury**
- Refactor `routers/finance/checks.py` (lines ~756-920)
- Refactor `routers/finance/treasury.py` 

**Day 3: Purchases & Collections**
- Refactor `routers/purchases.py`
- Refactor `routers/sales/vouchers.py`

**Day 4-5: HR, Inventory, Manufacturing**
- Refactor `routers/hr/core.py`
- Refactor `routers/inventory/*` (adjustments, transfers)
- Refactor `routers/manufacturing/core.py`

### Week 3

**Day 1-2: Finance Support Modules**
- Refactor `routers/finance/notes.py`
- Refactor `routers/finance/assets.py`
- Refactor `routers/finance/currencies.py`

**Day 3-4: Sales, Projects, Misc**
- Refactor remaining sales modules
- Refactor `routers/projects.py`
- Refactor specialized modules (landed costs, delivery orders, etc.)

**Day 5: Data Scripts**
- Refactor `scripts/populate_company_data.py`
- Update sample data generation

---

## VERIFICATION STRATEGY

### For Each Refactored Router

1. **Syntax Check**: Run Python AST check
   ```bash
   python -m py_compile routers/finance/accounting.py
   ```

2. **Database Integrity**: 
   - All journal entries must be balanced (trigger validates)
   - No new errors in `get_errors()`

3. **Functional Tests**: (Manual for now)
   - Create transaction → verify GL entry is created
   - Verify balance sheet remains balanced
   - Verify VAT calculations correct
   - Verify AR/AP updates

4. **Account Balance Verification**:
   ```sql
   SELECT je.id, je.entry_number, 
          ROUND(SUM(jl.debit)::numeric, 2) as total_debit,
          ROUND(SUM(jl.credit)::numeric, 2) as total_credit,
          CASE WHEN ABS(SUM(jl.debit) - SUM(jl.credit)) < 0.01 THEN 'OK' ELSE 'UNBALANCED' END as status
   FROM journal_entries je
   LEFT JOIN journal_lines jl ON je.id = jl.journal_entry_id
   WHERE je.status = 'posted'
   GROUP BY je.id, je.entry_number
   HAVING ABS(SUM(jl.debit) - SUM(jl.credit)) > 0.01
   ORDER BY je.entry_date DESC;
   ```

### Global Verification (After All Refactoring)

```sql
-- 1. All entries balanced
SELECT COUNT(*) as unbalanced_count
FROM (
    SELECT je.id,
           ABS(SUM(COALESCE(jl.debit, 0)) - SUM(COALESCE(jl.credit, 0))) as diff
    FROM journal_entries je
    LEFT JOIN journal_lines jl ON je.id = jl.journal_entry_id
    WHERE je.status = 'posted'
    GROUP BY je.id
    HAVING ABS(SUM(COALESCE(jl.debit, 0)) - SUM(COALESCE(jl.credit, 0))) > 0.01
) t;

-- 2. Trial balance still matches
SELECT 'Trial Balance Check: ' ||
       CASE WHEN ABS(total_debit - total_credit) < 0.01 THEN '✓ PASS' 
            ELSE '✗ FAIL' END as status,
       total_debit, total_credit
FROM (
    SELECT SUM(debit) as total_debit, SUM(credit) as total_credit
    FROM journal_lines
    WHERE journal_entry_id IN (
        SELECT id FROM journal_entries WHERE status = 'posted'
    )
) t;
```

---

## RISKS & MITIGATIONS

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Account balance diverges from JE total | MEDIUM | HIGH | Verify with SQL post-refactor |
| Forgot to refactor one file → inconsistency | MEDIUM | MEDIUM | Grep search for all `INSERT INTO journal_entries` |
| New developer adds manual journal entry outside service | HIGH | HIGH | Code review, add linter rule, documentation |
| Performance regression (many balance updates) | LOW | MEDIUM | Profile before/after, batch updates if needed |
| Existing posted entries become inconsistent | LOW | HIGH | Don't touch posted entries, only new ones |

---

## SUCCESS CRITERIA

| Criterion | Metric | Pass |
|-----------|--------|------|
| **All journal entries balanced** | 100% balanced entries | `unbalanced_count = 0` |
| **Trial balance matches** | GL debit = GL credit | `diff < 0.01` |
| **No syntax errors** | Python AST check | All files pass |
| **No regressions** | Existing workflows work | Manual test success |
| **Centralization complete** | Duplicate reduction | <5 manual INSERT blocks remaining |
| **Test coverage** | Sample data still loads | populate_company_data runs clean |

---

## APPROVAL CHECKLIST

### Please review and confirm:

- [ ] **GL Service Interface** — Is the `create_journal_entry()` signature acceptable?
- [ ] **DB Trigger** — Is this validation approach (DEFERRABLE DEFERRED) appropriate?
- [ ] **Refactoring Sequence** — Should we follow the priority list (Sales → Accounting → Checks → ...)?
- [ ] **Testing Strategy** — Is manual testing + SQL verification sufficient, or need automated tests?
- [ ] **Rollout** — Should we do all 75 at once or in phases?

### Questions

1. Should we add a `source` and `source_id` parameter to track the originating transaction (invoice, PO, etc.)?
   - Current: YES, already in gl_service
   - Benefit: Better audit trail, easier to reverse transactions

2. Should GL service handle currency-specific calculations (FX, multi-currency)?
   - Current: Basic support (exchange_rate parameter)
   - Need: More sophisticated multi-currency validation?

3. Should we add a dry-run/validate mode before posting?
   - Current: No
   - Need: For complex entries (closing, FX revaluation)?

---

## NEXT STEPS (After Approval)

1. Get sign-off on this plan
2. Refactor in priority order
3. Test after each major module
4. Run global verification queries
5. Update developer documentation
6. Add linter rule: "no manual INSERT INTO journal_entries"

---

*Last Updated: 2026-03-29*
