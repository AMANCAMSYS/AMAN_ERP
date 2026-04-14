# Research: Audit Accounting Module

**Feature**: 006-audit-accounting  
**Date**: 2026-04-14  
**Purpose**: Resolve all NEEDS CLARIFICATION items from Technical Context and investigate constitution compliance concerns.

---

## Research Task 1: Sequential Number Race Condition

**Question**: Does `generate_sequential_number()` use locking to prevent duplicate numbers under concurrent access?

**Decision**: ❌ **CRITICAL DEFECT — No locking mechanism exists**

**Findings**:
- `backend/utils/accounting.py` uses `SELECT MAX(CAST(SUBSTRING(...)))` without `FOR UPDATE`
- Two concurrent requests can read the same MAX value and produce duplicate numbers
- Affects all document types: journal entries, invoices, purchase orders, etc.

**Rationale**: The SQL-based MAX extraction is inherently vulnerable to TOCTOU (time-of-check-time-of-use) races. Under concurrent load, duplicates will occur.

**Alternatives Considered**:
1. PostgreSQL SEQUENCE — cleanest but requires schema change per document type
2. `SELECT ... FOR UPDATE` on a counter table — minimal change, proven pattern
3. Advisory locks (`pg_advisory_xact_lock`) — lightweight but harder to debug

**Recommendation**: Add `SELECT ... FOR UPDATE` on a dedicated counter row, or use PostgreSQL sequences. This is a **must-fix** item.

---

## Research Task 2: GL Service Audit Logging Gap

**Question**: Does `create_journal_entry()` log activity internally, or are there callers that forget to log?

**Decision**: ❌ **HIGH SEVERITY GAP — Logging delegated to callers; some callers omit it**

**Findings**:
- `gl_service.py` → `create_journal_entry()` does NOT call `log_activity()` internally
- **Callers WITH audit logging**: `accounting.py`, `hr/core.py`, `inventory/adjustments.py`
- **Callers WITHOUT audit logging**: `projects.py` (6 GL posting locations), likely some `finance/*` routers

**Rationale**: Delegating audit logging to callers violates the "pit of success" principle — every new caller must remember to log. Missing logs break audit trail completeness (FR-017, SC-015).

**Alternatives Considered**:
1. Move `log_activity()` inside `create_journal_entry()` — ensures 100% coverage but requires passing user/IP context
2. Create a wrapper function that always logs — backward-compatible
3. Add a post-commit hook — complex, fragile

**Recommendation**: Add audit logging inside `create_journal_entry()` accepting user context parameters. All existing callers that already log can be updated to remove their redundant calls, or the internal logging can be made conditional.

---

## Research Task 3: Balance Update Canonicality

**Question**: Is `update_account_balance()` the ONLY place where account balances are modified?

**Decision**: ⚠️ **MEDIUM SEVERITY — Scripts bypass the canonical path**

**Findings**:
- Canonical: `utils/accounting.py` → `update_account_balance()` — uses Decimal arithmetic
- **Bypass 1**: `scripts/populate_company_data.py` — bulk `UPDATE accounts SET balance = COALESCE(sub.bal, 0)` 
- **Bypass 2**: `scripts/reconcile_balances.py` — recalculates and directly sets balances
- **Bypass 3**: `scripts/reconcile_balances.py` — resets balances to 0

**Rationale**: The scripts serve legitimate purposes (data seeding, reconciliation). However, they bypass Decimal precision handling and could introduce rounding errors. The reconciliation script is itself a safety net, so the risk is bounded.

**Alternatives Considered**:
1. Force scripts through `update_account_balance()` — impractical for bulk operations
2. Ensure scripts use `NUMERIC` cast in SQL — simple fix
3. Accept scripts as maintenance tools with documented precision guarantees

**Recommendation**: Ensure reconciliation/seeding scripts use `CAST(... AS NUMERIC(18,4))` in their UPDATE statements. Document these as maintenance-only operations that must not run during active business hours.

---

## Research Task 4: Financial Report Query Sources

**Question**: Do financial reports query `journal_lines` directly or use cached summaries?

**Decision**: ✅ **ACCEPTABLE — All reports query live data**

**Findings**:
- Trial balance, balance sheet, income statement, and cash flow all query `journal_lines` + `journal_entries` via CTEs
- 60-second TTL cache (`@cached(expire=60)`) wraps the results but the underlying query runs live against the database
- Reports use parameterized SQL with proper date/branch/company filters

**Rationale**: Live queries ensure report accuracy. The 60s cache is a performance optimization that does not affect correctness for most use cases. Constitution XX requires reports to query source tables directly — this is satisfied.

**Alternatives Considered**: N/A — current pattern is correct.

---

## Research Task 5: Cross-Module Fiscal Lock Enforcement

**Question**: Do all modules calling GL posting check fiscal period locks?

**Decision**: ❌ **CRITICAL DEFECT — Inventory adjustments bypass fiscal lock**

**Findings**:
| Module | Fiscal Lock Check | Status |
|--------|------------------|--------|
| Sales invoices | ✅ `check_fiscal_period_open()` before GL post | Protected |
| Purchases | ✅ `check_fiscal_period_open()` before GL post | Protected |
| Treasury | ✅ `check_fiscal_period_open()` before GL post | Protected |
| Assets | ✅ `check_fiscal_period_open()` at multiple entry points | Protected |
| HR/Payroll | ✅ `check_fiscal_period_open()` before GL post | Protected |
| Projects | ✅ `check_fiscal_period_open()` before GL post | Protected |
| POS | ✅ `check_fiscal_period_open()` before GL post | Protected |
| **Inventory adjustments** | ❌ **NO CHECK** | **UNPROTECTED** |

**Additional finding**: `sales/returns.py` imports `check_fiscal_period_open` from `utils.accounting` instead of `utils.fiscal_lock` — this may work if re-exported, but is a non-standard import path.

**Rationale**: A single unprotected module creates a pathway to post GL entries in locked periods, violating FR-003 and Constitution III.

**Recommendation**: Add `check_fiscal_period_open(db, entry_date)` call in `inventory/adjustments.py` before the `gl_create_journal_entry()` call. Also standardize the import path for `check_fiscal_period_open`.

---

## Research Task 6: Float vs Decimal in Calculations

**Question**: Are there instances where `float()` is used BEFORE financial calculations?

**Decision**: ⚠️ **LOW SEVERITY — One instance found**

**Findings**:
- **Acceptable pattern** (90%+ of cases): `float()` used only after Decimal calculations for JSON serialization
- **Defect**: `reports.py` cash flow calculation uses `sum(float(r.amount) for ...)` — converting to float BEFORE aggregation
- All GL-internal calculations use `Decimal` throughout

**Recommendation**: Fix the single cash flow report instance to aggregate with Decimal first, then convert to float for JSON output.

---

## Research Task 7: Rate Limiting on GL Endpoints

**Question**: Are accounting/finance endpoints protected by rate limiting?

**Decision**: ⚠️ **MEDIUM SEVERITY — No rate limiting on any accounting endpoint**

**Findings**:
- Auth, mobile, and company creation endpoints have rate limiting
- ALL finance/accounting endpoints (journal entries, accounts, fiscal year close, budgets, cost centers, currencies, intercompany) have NO rate limiting
- Constitution IV mandates "General API: 100 requests/minute per user"

**Recommendation**: Add `@limiter.limit("100/minute")` to all accounting mutation endpoints. Read endpoints can have a higher limit (e.g., 200/minute).

---

## Summary of Defects Found

| # | Defect | Severity | Constitution Violation | Fix Complexity |
|---|--------|----------|----------------------|----------------|
| 1 | Sequential number race condition | **CRITICAL** | VI (Concurrency Safety), XXIII (Duplicate Prevention) | Moderate |
| 2 | Inventory adjustments bypass fiscal lock | **CRITICAL** | III (Double-Entry Integrity), XXII (Validation Pipeline) | Simple (1 line) |
| 3 | GL audit logging gaps (projects.py, others) | **HIGH** | XVII (Observability), FR-017 | Simple (add calls) |
| 4 | No rate limiting on accounting endpoints | **MEDIUM** | IV (Security & Access Control) | Simple (add decorators) |
| 5 | Balance update scripts bypass Decimal | **MEDIUM** | I (Financial Precision) | Simple (add CAST) |
| 6 | Float before aggregation in cash flow | **LOW** | I (Financial Precision) | Simple (1 line) |
| 7 | Non-standard import path for fiscal_lock | **LOW** | VII (Simplicity) | Simple (fix import) |
