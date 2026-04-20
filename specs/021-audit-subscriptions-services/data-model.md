# Data Model: Subscriptions, Services & Expenses Audit

**Date**: 2026-04-20
**Feature**: 021-audit-subscriptions-services

This document describes schema changes and entity modifications required by this audit. Only **changes** are listed — unchanged columns are omitted.

---

## Modified Entities

### 1. subscription_plans

**Current issues**: `created_by`/`updated_by` are `VARCHAR(100)` instead of INTEGER FK.

| Change | Column | Old | New |
|--------|--------|-----|-----|
| ALTER TYPE | `created_by` | `VARCHAR(100)` | `INTEGER REFERENCES company_users(id)` |
| ALTER TYPE | `updated_by` | `VARCHAR(100)` | `INTEGER REFERENCES company_users(id)` |

**Migration note**: Existing VARCHAR values must be resolved to user IDs. Unresolvable values set to NULL.

---

### 2. subscription_enrollments

**Current issues**: VARCHAR audit columns, missing columns referenced by service code.

| Change | Column | Old | New |
|--------|--------|-----|-----|
| ALTER TYPE | `created_by` | `VARCHAR(100)` | `INTEGER REFERENCES company_users(id)` |
| ALTER TYPE | `updated_by` | `VARCHAR(100)` | `INTEGER REFERENCES company_users(id)` |
| ADD | `trial_end_date` | — | `DATE` |
| ADD | `cancelled_at` | — | `TIMESTAMPTZ` |
| ADD | `cancellation_reason` | — | `TEXT` |
| ADD INDEX | `(customer_id, plan_id)` | — | Partial unique index WHERE `status IN ('active', 'paused')` |

**Service code alignment**: All references to `enrollment_date` in `subscription_service.py` must change to `start_date`.

---

### 3. subscription_invoices

**Current issues**: VARCHAR audit columns, no journal entry reference.

| Change | Column | Old | New |
|--------|--------|-----|-----|
| ALTER TYPE | `created_by` | `VARCHAR(100)` | `INTEGER REFERENCES company_users(id)` |
| ALTER TYPE | `updated_by` | `VARCHAR(100)` | `INTEGER REFERENCES company_users(id)` |
| ADD | `journal_entry_id` | — | `INTEGER REFERENCES journal_entries(id)` |
| ADD | `tax_rate` | — | `NUMERIC(5,2)` |
| ADD | `tax_amount` | — | `NUMERIC(18,4) DEFAULT 0` |
| ADD | `currency` | — | `VARCHAR(3)` |

---

### 4. expense_policies

**Current issues**: Missing `updated_at`, `updated_by`, `is_deleted`.

| Change | Column | Old | New |
|--------|--------|-----|-----|
| ADD | `updated_at` | — | `TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP` |
| ADD | `updated_by` | — | `INTEGER REFERENCES company_users(id)` |
| ADD | `is_deleted` | — | `BOOLEAN DEFAULT false` |

---

### 5. expenses

**Current issues**: Missing `currency`, `exchange_rate`, `policy_id`, missing indexes.

| Change | Column | Old | New |
|--------|--------|-----|-----|
| ADD | `currency` | — | `VARCHAR(3)` |
| ADD | `exchange_rate` | — | `NUMERIC(18,6) DEFAULT 1` |
| ADD | `policy_id` | — | `INTEGER REFERENCES expense_policies(id)` |
| ADD | `updated_by` | — | `INTEGER REFERENCES company_users(id)` |
| ADD | `is_deleted` | — | `BOOLEAN DEFAULT false` |
| ADD INDEX | `expense_date` | — | `idx_expenses_expense_date` |
| ADD INDEX | `approval_status` | — | `idx_expenses_approval_status` |
| ADD INDEX | `branch_id` | — | `idx_expenses_branch_id` |
| ADD INDEX | `created_by` | — | `idx_expenses_created_by` |

---

### 6. documents

**Current issues**: No `is_deleted`, tags as TEXT, missing `updated_by`, no indexes.

| Change | Column | Old | New |
|--------|--------|-----|-----|
| ADD | `is_deleted` | — | `BOOLEAN DEFAULT false` |
| ADD | `updated_by` | — | `INTEGER REFERENCES company_users(id)` |
| ALTER TYPE | `tags` | `TEXT` | `JSONB DEFAULT '[]'` |
| ADD INDEX | `(related_module, related_id)` | — | `idx_documents_related` |
| ADD INDEX | `created_by` | — | `idx_documents_created_by` |

**Migration note**: Existing TEXT tags parsed as comma-separated → JSON array. NULL → `'[]'`.

---

### 7. service_requests

**Current issues**: No `is_deleted`, no `branch_id`.

| Change | Column | Old | New |
|--------|--------|-----|-----|
| ADD | `is_deleted` | — | `BOOLEAN DEFAULT false` |
| ADD | `branch_id` | — | `INTEGER REFERENCES branches(id)` |
| ADD | `updated_by` | — | `INTEGER REFERENCES company_users(id)` |

---

## New Entities

### 8. deferred_revenue_schedules

Tracks monthly amortization of prepaid subscription revenue.

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `SERIAL` | `PRIMARY KEY` |
| `subscription_invoice_id` | `INTEGER` | `REFERENCES subscription_invoices(id) NOT NULL` |
| `enrollment_id` | `INTEGER` | `REFERENCES subscription_enrollments(id) NOT NULL` |
| `recognition_date` | `DATE` | `NOT NULL` |
| `amount` | `NUMERIC(18,4)` | `NOT NULL` |
| `journal_entry_id` | `INTEGER` | `REFERENCES journal_entries(id)` |
| `status` | `VARCHAR(20)` | `DEFAULT 'pending' CHECK (status IN ('pending', 'posted', 'skipped'))` |
| `created_by` | `INTEGER` | `REFERENCES company_users(id)` |
| `created_at` | `TIMESTAMPTZ` | `DEFAULT CURRENT_TIMESTAMP` |
| `updated_at` | `TIMESTAMPTZ` | `DEFAULT CURRENT_TIMESTAMP` |
| `updated_by` | `INTEGER` | `REFERENCES company_users(id)` |

**Indexes**: `(enrollment_id)`, `(recognition_date, status)`, `(subscription_invoice_id)`

---

### 9. service_request_costs (verify/fix existing)

Already exists in DB but needs:

| Change | Column | Old | New |
|--------|--------|-----|-----|
| ADD | `is_deleted` | — | `BOOLEAN DEFAULT false` |
| ADD | `updated_by` | — | `INTEGER REFERENCES company_users(id)` |

---

## New Pydantic Schemas

### Expense Policy Schemas (routers/finance/expenses.py)

```
ExpensePolicyCreateSchema:
  - name: str (required)
  - expense_type: str (required, from unified type enum)
  - department_id: int (optional)
  - daily_limit: Decimal (default 0)
  - monthly_limit: Decimal (default 0)
  - annual_limit: Decimal (default 0)
  - requires_receipt: bool (default True)
  - requires_approval: bool (default True)
  - auto_approve_below: Decimal (default 0)
  - is_active: bool (default True)

ExpensePolicyUpdateSchema:
  - All fields optional (partial update)

ExpenseValidationSchema:
  - expense_type: str (required)
  - amount: Decimal (required)
  - department_id: int (optional)
```

### Service Request Schemas (routers/services.py)

```
ServiceRequestCreateSchema:
  - title: str (required, max 255)
  - description: str (optional)
  - category: str (default 'maintenance')
  - priority: str (enum: low/medium/high/critical)
  - customer_id: int (optional)
  - asset_id: int (optional)
  - branch_id: int (optional)
  - estimated_hours: Decimal (optional)
  - estimated_cost: Decimal (optional)
  - scheduled_date: date (optional)
  - location: str (optional)
  - notes: str (optional)

ServiceRequestUpdateSchema:
  - All fields optional + status: str (validated against state machine)

TechnicianAssignSchema:
  - assigned_to: int (required)

ServiceCostSchema:
  - description: str (required)
  - amount: Decimal (required)
  - cost_type: str (optional)

DocumentMetaUpdateSchema:
  - title: str (optional)
  - description: str (optional)
  - category: str (optional)
  - tags: list[str] (optional)
  - access_level: str (optional, enum: company/department/private)
```

---

## State Machines

### Service Request Status

```
pending ──→ assigned ──→ in_progress ──→ completed (terminal)
   │            │            │    ↑
   │            │            ↓    │
   │            │         on_hold─┘
   │            │
   ↓            ↓            ↓
cancelled   cancelled   cancelled (terminal, reachable from any non-terminal)
```

### Subscription Enrollment Status

```
active ──→ paused ──→ active (resume)
   │          │
   ↓          ↓
cancelled  cancelled (terminal)
```

### Expense Approval Status (existing, enforce enum)

Valid values: `pending`, `approved`, `rejected`, `submitted`
