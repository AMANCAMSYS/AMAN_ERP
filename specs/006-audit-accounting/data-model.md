# Data Model: Audit Accounting Module

**Feature**: 006-audit-accounting  
**Date**: 2026-04-14  
**Source**: Extracted from ORM models and SQL queries in production code

---

## Entity Relationship Overview

```
accounts (COA)
  ├── 1:N journal_lines (account_id FK)
  ├── 1:N budget_items (account_id FK)
  └── self-ref parent_id (hierarchy)

journal_entries
  ├── 1:N journal_lines (journal_entry_id FK, CASCADE DELETE)
  ├── N:1 branches (branch_id FK)
  └── N:1 company_users (created_by FK)

journal_lines
  ├── N:1 journal_entries
  ├── N:1 accounts
  └── N:1 cost_centers (cost_center_id, optional)

fiscal_period_locks (gates all postings)

budgets
  ├── 1:N budget_items
  └── N:1 cost_centers (optional)

currencies
  └── 1:N exchange_rates

costing_policies
  └── 1:N costing_policy_history

recurring_journal_templates
  └── 1:N recurring_journal_lines

intercompany_transactions_v2
  ├── N:1 entity_groups (source)
  ├── N:1 entity_groups (target)
  ├── N:1 journal_entries (source_je)
  └── N:1 journal_entries (target_je)
```

---

## Core Tables

### accounts

Chart of accounts — hierarchical structure following SOCPA/IFRS numbering.

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | INTEGER | NO | auto | PK |
| account_number | VARCHAR(50) | NO | — | UNIQUE, NOT NULL |
| account_code | VARCHAR(20) | YES | NULL | — |
| name | VARCHAR(255) | NO | — | NOT NULL (Arabic) |
| name_en | VARCHAR(255) | YES | NULL | English name |
| account_type | VARCHAR(50) | NO | — | NOT NULL (asset/liability/equity/revenue/expense) |
| parent_id | INTEGER | YES | NULL | FK → accounts.id (self-referential) |
| is_header | BOOLEAN | YES | FALSE | Header accounts cannot hold balances |
| balance | NUMERIC(18,4) | YES | 0 | Running balance (base currency) |
| balance_currency | NUMERIC(18,4) | YES | 0 | Running balance (foreign currency) |
| currency | VARCHAR(3) | YES | NULL | ISO 4217 |
| is_active | BOOLEAN | YES | TRUE | Soft-disable |
| created_at | TIMESTAMPTZ | YES | now() | — |
| updated_at | TIMESTAMPTZ | YES | now() | — |

**Audit Finding**: `balance` column type in ORM model is `float` but DB column is `NUMERIC(18,4)`. Precision preserved at DB level; ORM mapping should use `Numeric`.

**Balance Formula**:
- Asset/Expense accounts: balance = Σ(debit) − Σ(credit)
- Liability/Equity/Revenue accounts: balance = Σ(credit) − Σ(debit)

---

### journal_entries

Double-entry transaction headers.

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | INTEGER | NO | auto | PK |
| entry_number | VARCHAR(50) | NO | — | UNIQUE, NOT NULL, sequential |
| entry_date | DATE | NO | — | NOT NULL, checked against fiscal locks |
| reference | VARCHAR(100) | YES | NULL | External reference |
| description | TEXT | YES | NULL | — |
| status | VARCHAR(20) | YES | 'draft' | CHECK: draft \| posted |
| currency | VARCHAR(10) | YES | 'SAR' | Transaction currency |
| exchange_rate | NUMERIC(18,6) | YES | 1.0 | Rate to base currency |
| branch_id | INTEGER | YES | NULL | FK → branches.id |
| source | VARCHAR(100) | YES | NULL | Origin module (Manual/sales/purchases/etc.) |
| source_id | INTEGER | YES | NULL | Origin document ID |
| created_by | INTEGER | YES | NULL | FK → company_users.id |
| created_at | TIMESTAMPTZ | YES | now() | — |
| posted_at | TIMESTAMPTZ | YES | NULL | Set when status → posted |
| updated_at | TIMESTAMPTZ | YES | now() | — |

**Validation Rules**:
1. `entry_date` must fall within an open fiscal period
2. Total debits across lines MUST equal total credits
3. Posted entries are immutable — no edits, only reversals
4. Sequential `entry_number` generated atomically (pattern: `JE-YYYY-NNNNN`)

---

### journal_lines

Individual debit/credit lines within a journal entry.

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | INTEGER | NO | auto | PK |
| journal_entry_id | INTEGER | NO | — | FK → journal_entries.id (CASCADE DELETE) |
| account_id | INTEGER | NO | — | FK → accounts.id |
| debit | NUMERIC(18,4) | YES | 0 | ≥ 0 |
| credit | NUMERIC(18,4) | YES | 0 | ≥ 0 |
| cost_center_id | INTEGER | YES | NULL | FK → cost_centers.id |
| amount_currency | NUMERIC(18,4) | YES | 0 | Original currency amount |
| currency | VARCHAR(3) | YES | NULL | Line-level currency |
| description | TEXT | YES | NULL | — |
| is_reconciled | BOOLEAN | YES | FALSE | Bank reconciliation flag |
| reconciliation_id | INTEGER | YES | NULL | FK → bank_reconciliation |
| created_at | TIMESTAMPTZ | YES | now() | — |

**Validation Rules**:
1. Cannot have both debit > 0 AND credit > 0 on same line
2. Neither debit nor credit can be negative
3. Minimum 2 lines per journal entry
4. Account must exist and be active

---

### fiscal_period_locks

Period-level posting controls.

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | SERIAL | NO | auto | PK |
| period_name | VARCHAR(100) | NO | — | NOT NULL |
| period_start | DATE | NO | — | NOT NULL |
| period_end | DATE | NO | — | NOT NULL |
| is_locked | BOOLEAN | YES | FALSE | — |
| locked_at | TIMESTAMPTZ | YES | NULL | — |
| locked_by | INTEGER | YES | NULL | FK → company_users.id |
| unlocked_at | TIMESTAMPTZ | YES | NULL | — |
| unlocked_by | INTEGER | YES | NULL | FK → company_users.id |
| reason | TEXT | YES | NULL | Audit trail |
| created_at | TIMESTAMPTZ | YES | now() | — |

**Behavior**: `check_fiscal_period_open(db, entry_date)` queries this table with `SELECT ... FOR UPDATE` and raises HTTP 400 if the date falls in a locked period. Gracefully degrades if table does not exist.

---

### currencies

Tenant-scoped currency definitions.

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | INTEGER | NO | auto | PK |
| code | VARCHAR(3) | NO | — | UNIQUE, ISO 4217 (regex: `^[A-Z]{3}$`) |
| name | VARCHAR(255) | YES | NULL | Arabic name |
| name_en | VARCHAR(255) | YES | NULL | English name |
| symbol | VARCHAR(10) | YES | NULL | — |
| is_base | BOOLEAN | YES | FALSE | Exactly one per tenant |
| current_rate | NUMERIC(18,6) | YES | 1.0 | 1.0 for base currency |
| is_active | BOOLEAN | YES | TRUE | — |
| updated_at | TIMESTAMPTZ | YES | now() | — |

**Constraint**: Base currency rate is always forced to 1.0. Exchange rates must be > 0.

---

### exchange_rates

Historical exchange rate records.

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | INTEGER | NO | auto | PK |
| currency_id | INTEGER | NO | — | FK → currencies.id |
| rate_date | DATE | NO | — | NOT NULL |
| rate | NUMERIC(18,6) | NO | — | CHECK: > 0 |
| source | VARCHAR(100) | YES | NULL | Manual or system |
| created_by | INTEGER | YES | NULL | FK → company_users.id |
| created_at | TIMESTAMPTZ | YES | now() | — |

**Unique**: (currency_id, rate_date)

---

### cost_centers

Departmental expense allocation targets.

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | INTEGER | NO | auto | PK |
| center_code | VARCHAR(50) | YES | NULL | UNIQUE |
| center_name | VARCHAR(255) | NO | — | NOT NULL |
| center_name_en | VARCHAR(255) | YES | NULL | — |
| department_id | INTEGER | YES | NULL | — |
| manager_id | INTEGER | YES | NULL | FK → company_users.id |
| is_active | BOOLEAN | YES | TRUE | — |

**Deletion Protection**: Cannot delete if referenced by any `journal_lines.cost_center_id`.

---

### budgets

Financial planning records.

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | INTEGER | NO | auto | PK |
| name | VARCHAR(255) | NO | — | UNIQUE, NOT NULL |
| budget_name | VARCHAR(255) | YES | NULL | Display name |
| start_date | DATE | NO | — | NOT NULL |
| end_date | DATE | NO | — | NOT NULL |
| description | TEXT | YES | NULL | — |
| status | VARCHAR(20) | YES | 'draft' | draft → active → closed |
| cost_center_id | INTEGER | YES | NULL | FK → cost_centers.id |
| budget_type | VARCHAR(50) | YES | 'annual' | annual / quarterly / multi_year |
| fiscal_year | INTEGER | YES | NULL | — |
| created_by | INTEGER | YES | NULL | FK → company_users.id |
| created_at | TIMESTAMPTZ | YES | now() | — |
| updated_at | TIMESTAMPTZ | YES | now() | — |

**Deletion Protection**: Active budgets cannot be deleted.

---

### budget_items

Per-account budget line items.

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | INTEGER | NO | auto | PK |
| budget_id | INTEGER | NO | — | FK → budgets.id |
| account_id | INTEGER | NO | — | FK → accounts.id |
| planned_amount | NUMERIC(18,4) | YES | 0 | — |
| actual_amount | NUMERIC(18,4) | YES | 0 | Computed from journal_lines |
| notes | TEXT | YES | NULL | — |

**Unique**: (budget_id, account_id) — upsert logic prevents duplicates.

---

### costing_policies

Active inventory valuation method.

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | INTEGER | NO | auto | PK |
| policy_name | VARCHAR(255) | NO | — | NOT NULL |
| policy_type | VARCHAR(50) | NO | — | CHECK: global_wac / per_warehouse_wac / hybrid / smart |
| description | TEXT | YES | NULL | — |
| is_active | BOOLEAN | YES | FALSE | Exactly one active |
| created_by | INTEGER | YES | NULL | FK → company_users.id |
| created_at | TIMESTAMPTZ | YES | now() | — |

---

### costing_policy_history

Audit trail for costing method changes.

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | INTEGER | NO | auto | PK |
| old_policy_type | VARCHAR(50) | YES | NULL | — |
| new_policy_type | VARCHAR(50) | NO | — | NOT NULL |
| changed_by | INTEGER | YES | NULL | FK → company_users.id |
| reason | TEXT | YES | NULL | — |
| affected_products_count | INTEGER | YES | 0 | — |
| total_cost_impact | NUMERIC(18,4) | YES | 0 | — |
| status | VARCHAR(50) | YES | 'pending' | pending / completed / failed |
| change_date | TIMESTAMPTZ | YES | now() | — |

---

### recurring_journal_templates

Configuration for auto-generated recurring journal entries.

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | INTEGER | NO | auto | PK |
| company_id | INTEGER | NO | — | NOT NULL |
| template_name | VARCHAR(255) | NO | — | NOT NULL |
| description | TEXT | YES | NULL | — |
| frequency | VARCHAR(50) | NO | — | NOT NULL — daily / weekly / monthly / quarterly / yearly |
| next_run_date | DATE | YES | NULL | — |
| last_generated_date | DATE | YES | NULL | — |
| is_active | BOOLEAN | NO | true | NOT NULL |
| created_by | INTEGER | YES | NULL | FK → company_users.id |
| created_at | TIMESTAMPTZ | YES | now() | — |
| updated_at | TIMESTAMPTZ | YES | now() | — |

**Unique**: `(company_id, template_name)`

---

### recurring_journal_lines

Line items for recurring journal templates.

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | INTEGER | NO | auto | PK |
| template_id | INTEGER | NO | — | FK → recurring_journal_templates.id, NOT NULL |
| account_id | INTEGER | NO | — | FK → accounts.id, NOT NULL |
| debit_amount | NUMERIC(18,4) | YES | 0 | >= 0 |
| credit_amount | NUMERIC(18,4) | YES | 0 | >= 0 |
| cost_center_id | INTEGER | YES | NULL | FK → cost_centers.id |
| description | TEXT | YES | NULL | — |

---

## State Transitions

### Journal Entry Lifecycle

```
draft ──[post]──► posted (irreversible)
                    │
                    └──[reverse]──► new posted reversal entry
```

### Budget Lifecycle

```
draft ──[activate]──► active ──[close]──► closed
```

### Fiscal Period Lock

```
unlocked ──[lock]──► locked ──[unlock]──► unlocked
```

### Costing Policy

```
inactive ──[activate]──► active (deactivates previous)
```

---

## Cross-Module Integration Points

| Source Module | GL Posting Path | Fiscal Lock Checked? |
|-------------|----------------|---------------------|
| Sales Invoices | `routers/sales/invoices.py` → `gl_service.create_journal_entry()` | ✅ Yes |
| Purchases | `routers/purchases.py` → `gl_service.create_journal_entry()` | ✅ Yes |
| Treasury | `routers/finance/treasury.py` → `gl_service.create_journal_entry()` | ✅ Yes |
| HR/Payroll | `routers/hr/core.py` → `gl_service.create_journal_entry()` | ✅ Yes |
| POS | `routers/pos.py` → `gl_service.create_journal_entry()` | ✅ Yes |
| Assets | `routers/finance/assets.py` → `gl_service.create_journal_entry()` | ✅ Yes |
| Projects | `routers/projects.py` → `gl_service.create_journal_entry()` | ✅ Yes |
| **Inventory Adjustments** | `routers/inventory/adjustments.py` → `gl_service.create_journal_entry()` | **❌ No — DEFECT** |
