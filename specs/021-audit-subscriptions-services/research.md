# Research: Subscriptions, Services & Expenses Audit

**Date**: 2026-04-20
**Feature**: 021-audit-subscriptions-services

## R1: GL Journal Entry Integration for Subscriptions

**Decision**: Use the existing `create_journal_entry` from `services/gl_service.py` with `source="subscription"` and `source_id=enrollment_id`. Use the built-in idempotency key support (`idempotency_key` parameter) to prevent duplicate entries.

**Rationale**: The GL service already has all needed functionality — balance validation, fiscal period check, idempotency, and source-level duplicate guard. The expenses module uses this exact pattern successfully. No new GL infrastructure is needed.

**Alternatives considered**:
- Creating a dedicated `subscription_gl_service.py` — rejected, would violate Constitution XIX (duplicate calculation logic). The existing GL service is the single source of truth.
- Posting GL entries asynchronously via a queue — rejected, the current synchronous pattern (used by expenses) is sufficient and ensures transactional consistency.

**Key details**:
- Idempotency key format: `sub-{enrollment_id}-{billing_period_start}`
- Source duplicate guard: `source="subscription" + source_id=enrollment_id + date`
- GL accounts needed: Accounts Receivable (debit), Subscription Revenue or Deferred Revenue (credit), VAT Payable (credit)
- GL accounts will be resolved from company settings or chart of accounts by account type

---

## R2: Deferred Revenue Implementation

**Decision**: Implement straight-line amortization for prepaid subscriptions (annual/multi-month). When an upfront invoice is created, credit Deferred Revenue. Create a `deferred_revenue_schedules` table to track monthly amortization entries.

**Rationale**: Constitution I requires deferred revenue support. Straight-line is the standard method for subscription services (IFRS 15 / ASC 606). The amortization schedule can be processed by the existing scheduled jobs infrastructure.

**Alternatives considered**:
- Point-in-time recognition (recognize all revenue at billing) — rejected, violates IFRS 15 for services delivered over time.
- Usage-based recognition — rejected, overly complex for fixed-price subscriptions; can be added as future enhancement.

**Key details**:
- Monthly amortization amount: `total_amount / months_in_subscription_period`
- Each amortization entry: DR Deferred Revenue, CR Subscription Revenue
- Schedule generated at invoice creation time
- Amortization entries posted by a recurring job or triggered at month-end

---

## R3: VAT on Subscription Invoices

**Decision**: Apply Saudi 15% VAT to subscription billing amounts using the existing tax rate from company settings. Store tax breakdown per Constitution XXVI.

**Rationale**: Constitution V requires ZATCA compliance. All commercial invoices in Saudi Arabia must include 15% VAT. The subscription module is the only billing module that omits VAT entirely.

**Alternatives considered**:
- Making VAT optional per plan — rejected, Saudi VAT is mandatory for all commercial transactions. If a plan is VAT-exempt, it should be explicitly configured, not silently omitted.

**Key details**:
- Tax rate: from company tax settings (currently 15% for Saudi standard rate)
- Invoice amount structure: `base_amount + (base_amount * tax_rate) = total_amount`
- Store: `tax_rate`, `taxable_base`, `tax_amount` on subscription invoice or linked invoice record

---

## R4: Expense Treasury Balance Race Condition

**Decision**: Add `FOR UPDATE` to the treasury balance SELECT query in expense approval. This locks the row for the duration of the transaction, preventing concurrent approvals from both passing the balance check.

**Rationale**: Constitution VI requires `SELECT ... FOR UPDATE` for treasury movements. The current pattern uses a plain SELECT which allows a TOCTOU race condition.

**Alternatives considered**:
- Optimistic locking with version column — rejected, treasury balance is a high-contention resource where pessimistic locking is more appropriate (per Constitution VI).
- Application-level mutex — rejected, doesn't work in multi-process deployments.

---

## R5: Subscription Enrollment Duplicate Prevention

**Decision**: Add a unique constraint on `(customer_id, plan_id)` WHERE `status IN ('active', 'paused')` (partial unique index). Additionally, use `SELECT ... FOR UPDATE` on the customer row before enrollment to serialize concurrent requests.

**Rationale**: Constitution XXIII requires duplicate prevention. A partial unique index is the strongest guarantee — it works even if the application crashes between check and insert. The FOR UPDATE provides additional serialization for the enrollment flow.

**Alternatives considered**:
- Application-level check only — rejected, race window between SELECT and INSERT.
- Full unique constraint on `(customer_id, plan_id)` — rejected, would prevent re-enrollment after cancellation.

---

## R6: Billing Period Date Calculation

**Decision**: Replace `min(start.day, 28)` with proper calendar-aware date calculation using Python's `calendar.monthrange()` to get the correct last day of each month.

**Rationale**: The current implementation clips all billing dates to the 28th, which loses 1-3 days for months with 29/30/31 days. For a plan starting on the 31st, billing should advance to Jan 31 → Feb 28 → Mar 31 → Apr 30 (last day of month, not permanently clipped to 28).

**Key details**:
```python
import calendar
def next_billing_date(current_date, original_day):
    month = current_date.month % 12 + 1
    year = current_date.year + (1 if month == 1 else 0)
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(original_day, last_day))
```

---

## R7: Expense Type Unification

**Decision**: Create a unified expense type list that merges both sets. The canonical types will be: `travel`, `meals`, `supplies`, `transportation`, `entertainment`, `materials`, `labor`, `services`, `rent`, `utilities`, `salaries`, `other`. Both the expense form and policy form will use this same list.

**Rationale**: The current mismatch means policies can never match most expenses (only `travel` and `other` overlap). Merging both sets preserves backward compatibility — no existing data breaks, and new types become available.

**Alternatives considered**:
- Using only policy types and mapping form types — rejected, would break existing expense records with types like `materials`, `labor`.
- Database-driven expense types — rejected, overkill for this audit; can be a future enhancement.

---

## R8: Subscription DDL/Service Column Alignment

**Decision**: Add missing columns to DDL (`trial_end_date DATE`, `cancelled_at TIMESTAMPTZ`, `cancellation_reason TEXT`) and align service code to use `start_date` (the DDL column name) instead of `enrollment_date`.

**Rationale**: The DDL is the source of truth for table structure. The service code references columns that don't exist in the DDL, meaning either: (a) they were added via ad-hoc SQL and never synced to database.py, or (b) the service code is buggy. Either way, the DDL must include all columns the service uses, and column names must match.

**Key details**:
- `enrollment_date` references in service → change to `start_date`
- Add to `subscription_enrollments` DDL: `trial_end_date DATE`, `cancelled_at TIMESTAMPTZ`, `cancellation_reason TEXT`
- Include in Alembic migration with `IF NOT EXISTS` pattern for idempotency

---

## R9: Service Request Status State Machine

**Decision**: Enforce the following state transitions:
- `pending` → `assigned`, `cancelled`
- `assigned` → `in_progress`, `cancelled`
- `in_progress` → `on_hold`, `completed`, `cancelled`
- `on_hold` → `in_progress`, `cancelled`
- `completed` → (terminal, no transitions)
- `cancelled` → (terminal, no transitions)

**Rationale**: The DDL already defines a CHECK constraint with these status values. The state machine prevents illogical transitions (e.g., `completed` → `pending`) which are currently possible because the router accepts any status string.

**Alternatives considered**:
- Allowing all transitions — rejected, undermines the purpose of status tracking.
- Adding a `reopened` status — rejected, out of scope for audit; can be added later if needed.

---

## R10: Document Download Endpoint

**Decision**: Add a `GET /services/documents/{document_id}/download` endpoint that serves the file via `FileResponse`, with access level validation. Remove `file_path` from list/detail API responses and replace with a `download_url` field.

**Rationale**: Currently files can be uploaded but never downloaded — a completely broken feature. The `file_path` field exposes server internals. The download endpoint provides controlled access with proper authorization.

**Key details**:
- Validate `access_level` against requesting user's role
- Use `FileResponse` from FastAPI for streaming
- Set `Content-Disposition` header for proper filename
- Return 404 if file not found on disk (handle orphaned DB records gracefully)

---

## R11: showToast Signature Fix Pattern

**Decision**: In all 9 affected calls, move the closing parenthesis of `t()` before the comma, so the toast type becomes the second argument to `showToast` instead of the fallback argument to `t()`.

**Rationale**: The bug is a simple parenthesis placement error. The fix is mechanical — no logic changes needed.

**Current (wrong)**:
```javascript
showToast(err.response?.data?.detail || t('common.error', 'error'))
```

**Fixed**:
```javascript
showToast(err.response?.data?.detail || t('common.error'), 'error')
```

---

## R12: Soft-Delete Migration for Tables Without is_deleted

**Decision**: Add `is_deleted BOOLEAN DEFAULT false` to `documents` table via migration. The `expenses` and `service_requests` tables already have adequate structure (expenses has no is_deleted but uses approval_status; service_requests DDL has status with CHECK constraint). For `expense_policies`, add `is_deleted BOOLEAN DEFAULT false`, `updated_at`, and `updated_by`.

**Rationale**: Soft-delete requires an `is_deleted` column. Tables that currently lack it cannot be soft-deleted. The migration adds the column with a default of `false` so existing records are unaffected.
