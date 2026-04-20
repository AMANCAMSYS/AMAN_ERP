# Implementation Plan: Subscriptions, Services & Expenses — Audit & Bug Fixes

**Branch**: `021-audit-subscriptions-services` | **Date**: 2026-04-20 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/021-audit-subscriptions-services/spec.md`

## Summary

Audit and fix critical bugs across the Subscriptions, Services, and Expenses modules. The most severe issue is that subscription billing creates invoices but posts **no GL journal entries**, meaning subscription revenue is completely absent from the books. Other critical fixes include: replacing 19+ `float()` casts with `Decimal` for monetary values, converting 5 hard `DELETE FROM` statements to soft-deletes, adding Pydantic validation to 8 raw-dict endpoints, fixing race conditions in expense approval and subscription enrollment, adding branch access validation and audit logging to the services module, correcting frontend `showToast` signatures (9 calls), replacing hardcoded currencies and Arabic strings, and fixing database schema deficiencies (VARCHAR audit columns, missing indexes, missing columns).

## Technical Context

**Language/Version**: Python 3.12 (backend), React 18 / Vite (frontend)
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0, Pydantic (backend); React, i18next, Bootstrap (frontend)
**Storage**: PostgreSQL 15 — one DB per tenant (`aman_{company_id}`)
**Testing**: No tests requested for this audit
**Target Platform**: Linux server (Docker + Nginx)
**Project Type**: Web application (ERP system)
**Performance Goals**: Standard ERP — pagination default 25, max 100
**Constraints**: Constitution rules are non-negotiable; schema changes require dual-update (database.py + Alembic migration)
**Scale/Scope**: 4 backend files (~2,455 lines), 13 frontend files, database schema changes, 1-2 Alembic migrations

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Relevant? | Status | Notes |
|---|-----------|-----------|--------|-------|
| I | Financial Precision | YES | VIOLATION → FIX | 19+ float casts across 4 backend files + 1 frontend file. GL service itself uses float for exchange_rate param — out of scope (pre-existing). |
| II | Multi-Tenant Isolation | YES | PASS | All DB operations via `get_db_connection(company_id)`. No cross-tenant changes needed. |
| III | Double-Entry Integrity | YES | VIOLATION → FIX | Subscription invoices have NO journal entries. `check_fiscal_period_open()` not called. `validate_je_lines()` not called. |
| IV | Security & Access Control | YES | VIOLATION → FIX | Services router has no `validate_branch_access`. Subscription router has no branch validation. |
| V | Regulatory Compliance — Saudi | YES | VIOLATION → FIX | No VAT applied to subscription invoices. |
| VI | Concurrency Safety | YES | VIOLATION → FIX | Expense treasury balance check lacks FOR UPDATE. Subscription enrollment has no duplicate prevention. |
| VII | Simplicity & Maintainability | YES | PASS | No new abstractions. Following existing patterns. |
| XIV | Approval Workflow | YES | VIOLATION → FIX | Subscriptions have no approval integration. |
| XVII | Observability & Audit Trail | YES | VIOLATION → FIX | Hard deletes (5 locations). Missing audit logging in services router. VARCHAR audit columns in subscription tables. |
| XVIII | Session Contract & API | YES | VIOLATION → FIX | Hardcoded 'SAR' in PlanForm.jsx (2). Hardcoded currency omission in subscription invoices. |
| XXII | Transaction Validation Pipeline | YES | VIOLATION → FIX | 8 endpoints accept raw dict. No Pydantic validation on input. |
| XXIII | Idempotency & Duplicate Prevention | YES | VIOLATION → FIX | `generate_subscription_invoice` can create duplicates. |
| XXV | Performance & Query Discipline | YES | VIOLATION → FIX | Services router has no pagination on any list endpoint. |
| XXVIII | Schema Definition Synchronization | YES | VIOLATION → FIX | Schema changes must update both database.py and migration. DDL/service column mismatch in subscriptions (`start_date` vs `enrollment_date`). |

**Gate evaluation**: Multiple Constitution violations identified. All are being fixed by this spec — no unjustified violations.

## Project Structure

### Documentation (this feature)

```text
specs/021-audit-subscriptions-services/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── routers/
│   ├── finance/
│   │   ├── subscriptions.py      # 372 lines — audit target
│   │   └── expenses.py           # 948 lines — audit target
│   └── services.py               # 635 lines — audit target
├── services/
│   └── subscription_service.py   # 500 lines — audit target (GL, billing fixes)
├── utils/
│   ├── fiscal_lock.py            # check_fiscal_period_open() — referenced
│   ├── approval_utils.py         # try_submit_for_approval() — referenced
│   ├── audit.py                  # log_activity() — referenced
│   ├── permissions.py            # validate_branch_access() — referenced
│   └── i18n.py                   # http_error() — referenced
├── database.py                   # Schema DDL — audit target
└── migrations/versions/
    └── fix_subscriptions_services_expenses_schema.py  # New migration

frontend/src/
├── pages/
│   ├── Subscription/
│   │   ├── SubscriptionHome.jsx    # i18n fixes
│   │   ├── PlanList.jsx            # formatting fixes
│   │   ├── PlanForm.jsx            # hardcoded SAR fix
│   │   ├── EnrollmentList.jsx      # (clean)
│   │   ├── EnrollmentForm.jsx      # i18n + UX fixes
│   │   └── EnrollmentDetail.jsx    # useEffect dep fix
│   ├── Services/
│   │   ├── ServiceRequests.jsx     # showToast signature fix (7+)
│   │   └── DocumentManagement.jsx  # showToast + key fix
│   └── Expenses/
│       ├── ExpenseForm.jsx         # parseFloat fix
│       ├── ExpenseDetails.jsx      # date + Link fix
│       └── ExpensePolicies.jsx     # hardcoded error + type mismatch
├── utils/
│   ├── auth.js                     # getCurrency() — referenced
│   ├── format.js                   # formatNumber(), formatCurrency() — referenced
│   └── dateUtils.js                # formatDate() — referenced
└── locales/
    ├── en.json                     # New i18n keys
    └── ar.json                     # New i18n keys
```

**Structure Decision**: Existing web application structure. No new directories needed. All changes are edits to existing files plus 1 new Alembic migration.

## Key Integration Patterns (from research)

### GL Journal Entry Creation
```python
from services.gl_service import create_journal_entry

je_id, entry_number = create_journal_entry(
    db=db, company_id=company_id, date=billing_date,
    description=f"اشتراك: {plan_name}",
    lines=[
        {"account_id": ar_account_id, "debit": amount, "credit": Decimal("0")},
        {"account_id": revenue_account_id, "debit": Decimal("0"), "credit": net_amount},
        {"account_id": vat_account_id, "debit": Decimal("0"), "credit": vat_amount},
    ],
    user_id=user_id, branch_id=branch_id,
    source="subscription", source_id=enrollment_id,
    idempotency_key=f"sub-{enrollment_id}-{billing_period_start}"
)
```

### Fiscal Period Check
```python
from utils.fiscal_lock import check_fiscal_period_open
check_fiscal_period_open(db, invoice_date)
```

### Approval Submission
```python
from utils.approval_utils import try_submit_for_approval
result = try_submit_for_approval(
    db, document_type="subscription", document_id=enrollment_id,
    document_number=enrollment_number, amount=plan_amount,
    submitted_by=user_id, description="Subscription enrollment"
)
```

### Branch Access Validation
```python
from utils.permissions import validate_branch_access
branch_id = validate_branch_access(current_user, branch_id)
```

### Audit Logging
```python
from utils.audit import log_activity
log_activity(db, user_id=current_user.id, username=current_user.username,
    action="service_request.create", resource_type="service_request",
    resource_id=str(request_id), details={...}, request=request)
```

### showToast Correct Signature
```javascript
// CORRECT:
showToast(err.response?.data?.detail || t('common.error'), 'error')
// WRONG (current):
showToast(err.response?.data?.detail || t('common.error', 'error'))
```

### Frontend Currency/Formatting
```javascript
import { getCurrency } from '../../utils/auth'
import { formatNumber, formatCurrency } from '../../utils/format'
import { formatDate } from '../../utils/dateUtils'
```

## DDL/Service Column Mismatches (Subscriptions)

The subscription service references columns that do not exist in the DDL:
- Service uses `enrollment_date` → DDL has `start_date`
- Service references `trial_end_date` → NOT in DDL
- Service references `cancelled_at` → NOT in DDL
- Service references `cancellation_reason` → NOT in DDL

**Decision**: Add missing columns to DDL (`trial_end_date DATE`, `cancelled_at TIMESTAMPTZ`, `cancellation_reason TEXT`) and keep `start_date` as the DDL column name. Align service code to use `start_date` instead of `enrollment_date`.

## Complexity Tracking

No unjustified violations. All Constitution violations are being fixed, not introduced.
