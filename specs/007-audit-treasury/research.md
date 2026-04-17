# Research: audit-treasury — الخزينة والبنوك

**Date**: 2026-04-14  
**Phase**: 0 — Outline & Research

## R-001: GL Entry Ordering in Treasury Operations

**Context**: Treasury expense/transfer endpoints update `current_balance` BEFORE calling `create_journal_entry()`. If GL creation fails, the balance is already decremented but the GL is not posted.

**Decision**: Reorder to GL-first, balance-second — matching the pattern already used in `checks.py` for collections.

**Rationale**: The GL service performs double-entry validation and fiscal period checks. If it rejects the entry, the balance must not have changed. The safest sequence is: (1) create GL entry, (2) update treasury balance, (3) commit. Both within the same `db` session so rollback reverts both.

**Alternatives considered**:
- Savepoint-based rollback: More complex, same result; rejected for simplicity.
- Post-commit reconciliation: Detects drift but doesn't prevent it; rejected.

## R-002: Concurrency Safety for Treasury Balance Updates

**Context**: Treasury balance operations use `UPDATE ... SET current_balance = current_balance ± :amt` without `SELECT FOR UPDATE`. Check collection does not lock the check row before status transition.

**Decision**: Add `SELECT ... FOR UPDATE` on the treasury account row before any balance-modifying operation. Add `SELECT ... FOR UPDATE` on check/note rows before status transitions.

**Rationale**: Constitution §VI mandates row-level `SELECT ... FOR UPDATE` locks for treasury inter-account movements. The existing pattern is already used in `fiscal_lock.py` (line 29-35). This prevents double-collection of checks and race conditions on concurrent transfers.

**Alternatives considered**:
- Optimistic locking (version column): Would require adding a `version` column to `treasury_accounts`, `checks_receivable`, etc. More invasive schema change for the same result. Rejected.
- Application-level mutex: Not viable in multi-process/multi-server deployment. Rejected.

## R-003: Check Re-Presentation (Bounced → Pending)

**Context**: Current codebase treats `bounced` as terminal. No endpoint exists to transition a bounced check back to pending. Spec clarification mandates re-presentation support for Saudi banking practice.

**Decision**: Add a new `POST /checks/receivable/{id}/represent` endpoint (and equivalent for payable) that:
1. Validates check is in `bounced` status
2. Locks the row with `SELECT FOR UPDATE`
3. Posts a new GL entry (Dr. Checks Under Collection / Cr. AR)
4. Resets status to `pending`
5. Clears `bounce_date`, `bounce_reason`, `bounce_journal_id` but preserves `journal_entry_id` (original) — adds a `re_presentation_count` or uses audit trail to track history

**Rationale**: Matches Saudi banking practice. Keeping the same record avoids duplicate entries and preserves the complete GL audit trail (original entry → bounce reversal → re-presentation entry).

**Alternatives considered**:
- Create a new check record referencing the original: Loses the continuous audit trail and clutters the check list. Rejected per clarification.

## R-004: Overdraft Policy Implementation

**Context**: No balance validation exists today. Spec clarification mandates: reject on cash accounts (default), allow on bank accounts (default), configurable per account.

**Decision**: Add an `allow_overdraft` boolean column to `treasury_accounts` (default: `NULL` = use type-based default). In expense/transfer endpoints, check before posting:
```
if account_type == 'cash' and allow_overdraft is not True:
    if current_balance - amount < 0: reject
elif account_type == 'bank' and allow_overdraft is False:
    if current_balance - amount < 0: reject
```

**Rationale**: Column-level configuration per account is simpler than a company_settings lookup. NULL means "use the default for account type", explicit True/False overrides.

**Alternatives considered**:
- Company-level setting only: Too coarse; some bank accounts (payroll) should block overdraft while others allow it. Rejected.
- Separate `overdraft_limit` field: Adds complexity beyond the spec requirement. Can be added later if needed.

## R-005: Auto-Creation of Missing GL Accounts

**Context**: Checks/notes routers hard-code account codes (1205, 2105, 1210, 2110) and fail with HTTP 500 if they don't exist. The `_ensure_checks_accounts(db)` helper in `checks.py` already has partial auto-creation logic.

**Decision**: Consolidate and extend `_ensure_checks_accounts(db)` into a shared utility function `ensure_treasury_gl_accounts(db)` that:
1. Checks for all 4 intermediate accounts (1205, 2105, 1210, 2110)
2. Auto-creates missing ones under the correct parent (12xx for assets, 21xx for liabilities)
3. Logs each creation via `log_activity()`
4. Returns a dict of `{code: account_id}` for caller use

**Rationale**: Follows the existing auto-creation pattern for treasury GL accounts under 1101. Consolidating into one utility eliminates code duplication across checks.py and notes.py.

**Alternatives considered**:
- Migration-only auto-creation: Would require remembering to run migration for every new company. Rejected per clarification (auto-create on first use).
- Onboarding wizard creation: Adds dependency on setup flow completion. Rejected.

## R-006: Reconciliation Tolerance Configuration

**Context**: No tolerance setting exists. Spec clarification mandates ±1.00 SAR default, configurable per company.

**Decision**: Store `reconciliation_tolerance` in the `company_settings` table (key-value pattern already used for `default_currency`, `password_policy`, etc.). Default value: `1.00`. The finalize endpoint reads this setting and compares `abs(difference) <= tolerance`.

**Rationale**: Follows the existing company_settings key-value pattern. No schema change needed beyond inserting the default.

**Alternatives considered**:
- Per-account tolerance: Overly granular for typical use. Rejected.
- Hard-coded tolerance: Violates constitution §V (Configurability Mandate). Rejected.

## R-007: Duplicate Check Number Detection

**Context**: No unique constraint or runtime check on `check_number`. Multiple checks with the same number can be created leading to double GL posting.

**Decision**: Add a runtime duplicate check before creation:
```sql
SELECT id FROM checks_receivable WHERE check_number = :num AND branch_id = :branch AND status != 'bounced'
```
If found, return a warning (not a hard block) since the same check number can appear across different banks/drawers. The warning includes the existing check details for the user to confirm.

**Rationale**: A database UNIQUE constraint on `(check_number, branch_id)` would be too restrictive — the same check number from different banks is legitimate. A soft warning provides protection without false rejections.

**Alternatives considered**:
- Hard UNIQUE constraint: Too restrictive across different banks/drawers. Rejected.
- No check: Current state; allows silent duplicates. Rejected per FR-014.

## R-008: Fiscal Period Lock on Opening Balance

**Context**: Treasury account creation posts opening balance using `date.today()` without checking fiscal period lock.

**Decision**: Add `check_fiscal_period_open(db, date.today())` before posting the opening balance journal entry in the treasury account creation endpoint.

**Rationale**: Constitution §III mandates fiscal period checks gate ALL transaction creation. Opening balance is a GL posting and must respect the same rules.

**Alternatives considered**:
- Allow opening balance in any period: Violates constitution. Rejected.

## R-009: Exchange Rate Persistence in Treasury Transactions

**Context**: TreasuryTransaction model has no `exchange_rate` column. The rate is passed to the GL service but not persisted in the transaction audit trail.

**Decision**: Add `exchange_rate NUMERIC(18,6) DEFAULT 1.0` column to `treasury_transactions` table. Populate on every expense/transfer transaction.

**Rationale**: Constitution §I mandates exchange rates be locked at transaction date. The GL service stores it in journal_lines, but the treasury transaction record should also preserve it for non-GL audit queries and reconciliation.

**Alternatives considered**:
- Derive from GL journal entry: Requires join; doesn't serve treasury-level reports. Rejected.

## R-010: Float vs Decimal in TreasuryAccount Model

**Context**: `TreasuryAccount.current_balance` is typed as `Mapped[float | None]` in the SQLAlchemy model, though the DB column is `NUMERIC(18,4)`.

**Decision**: Change model type annotation to `Mapped[Decimal | None]` with proper `Numeric(18, 4)` column type. Ensure all Python-side balance operations use `Decimal`.

**Rationale**: Constitution §I explicitly forbids floating-point for monetary values. The DB column is correct but the Python type annotation allows float arithmetic which could introduce rounding errors.

**Alternatives considered**:
- Leave as float with DB-level precision: Violates constitution; Python-side calculations would use float arithmetic. Rejected.
