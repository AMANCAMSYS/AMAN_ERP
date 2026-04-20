# Data Model: Projects, Contracts & Fixed Assets — Audit & Bug Fixes

**Feature**: 019-audit-projects-assets  
**Date**: 2026-04-20

---

## Overview

This audit requires schema changes in **two categories**:

1. **DDL fixes in `database.py`** — missing columns, wrong types, missing `updated_at`, missing indexes
2. **Alembic migrations** — to apply the same fixes to existing tenant DBs

No new tables are created. No tables are dropped. All changes are additive (new columns, type widening, new indexes) or corrective (adding missing audit columns).

---

## Change 1: Add Missing Columns to `projects` Table

### Root Cause

The `projects` table DDL is missing 3 columns used by the retainer billing endpoints (`setup_retainer`, `generate_retainer_invoices`). Fresh tenant DBs crash on these endpoints.

### Current DDL (abbreviated)

```sql
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    ...
    -- retainer_amount, billing_cycle, next_billing_date are MISSING
    ...
);
```

### Target DDL (add to `projects` table)

```sql
    retainer_amount DECIMAL(18,4) DEFAULT 0,
    billing_cycle VARCHAR(20),          -- 'monthly', 'quarterly', 'annual'
    next_billing_date DATE,
```

### Dual-Update Checklist (Constitution XXVIII ⛔)

| Location | Action |
|----------|--------|
| `backend/database.py` — `projects` CREATE TABLE | Add 3 columns |
| `backend/migrations/versions/<ts>_add_project_retainer_columns.py` | `ALTER TABLE projects ADD COLUMN ...` × 3 |

---

## Change 2: Add Missing `updated_at` to 15 Tables (Constitution XVII)

### Root Cause

Constitution XVII (`AuditMixin`) requires `created_at`, `updated_at`, `created_by`, `updated_by` on ALL domain models. 15 tables lack `updated_at` (and in some cases `updated_by`).

### Tables Affected

| Table | Missing Columns |
|-------|----------------|
| `project_tasks` | `updated_at` |
| `project_budgets` | `updated_at` |
| `project_expenses` | `updated_at` |
| `project_revenues` | `updated_at` |
| `project_documents` | `updated_at` |
| `task_dependencies` | `updated_at` |
| `contract_items` | `updated_at` |
| `contract_amendments` | `updated_at` |
| `asset_depreciation_schedule` | `updated_at` |
| `asset_transfers` | `updated_at` |
| `asset_revaluations` | `updated_at` |
| `asset_maintenance` | `updated_at` |
| `asset_insurance` | `updated_at` |
| `lease_contracts` | `updated_at` |
| `asset_impairments` | `updated_at` |

### Target Column Definition

```sql
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
```

### Dual-Update Checklist (Constitution XXVIII ⛔)

| Location | Action |
|----------|--------|
| `backend/database.py` — each of 15 CREATE TABLE blocks | Add `updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP` |
| `backend/migrations/versions/<ts>_add_updated_at_to_project_asset_tables.py` | `ALTER TABLE ... ADD COLUMN updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP` × 15 |

### Migration Template

```python
"""add updated_at to project and asset tables

Revision ID: <auto>
Revises: <previous>
Create Date: 2026-04-20
"""
from alembic import op
import sqlalchemy as sa

TABLES = [
    "project_tasks", "project_budgets", "project_expenses",
    "project_revenues", "project_documents", "task_dependencies",
    "contract_items", "contract_amendments",
    "asset_depreciation_schedule", "asset_transfers",
    "asset_revaluations", "asset_maintenance", "asset_insurance",
    "lease_contracts", "asset_impairments",
]

def upgrade():
    for table in TABLES:
        op.add_column(table,
            sa.Column('updated_at', sa.DateTime(timezone=True),
                       server_default=sa.func.current_timestamp(), nullable=True))

def downgrade():
    for table in TABLES:
        op.drop_column(table, 'updated_at')
```

---

## Change 3: Fix Money Column Types (Constitution I)

### Root Cause

Several asset-related tables use `NUMERIC(15,2)` instead of the constitutionally required `DECIMAL(18,4)`.

### Columns to Widen

| Table | Column | Current | Target |
|-------|--------|---------|--------|
| `asset_transfers` | `book_value_at_transfer` | `NUMERIC(15,2)` | `DECIMAL(18,4)` |
| `asset_revaluations` | `old_value` | `NUMERIC(15,2)` | `DECIMAL(18,4)` |
| `asset_revaluations` | `new_value` | `NUMERIC(15,2)` | `DECIMAL(18,4)` |
| `asset_revaluations` | `difference` | `NUMERIC(15,2)` | `DECIMAL(18,4)` |
| `asset_maintenance` | `cost` | `NUMERIC(15,2)` | `DECIMAL(18,4)` |
| `asset_insurance` | `premium_amount` | `NUMERIC(15,2)` | `DECIMAL(18,4)` |
| `asset_insurance` | `coverage_amount` | `NUMERIC(15,2)` | `DECIMAL(18,4)` |

### Dual-Update Checklist (Constitution XXVIII ⛔)

| Location | Action |
|----------|--------|
| `backend/database.py` — each CREATE TABLE | Change type from `NUMERIC(15,2)` to `DECIMAL(18,4)` |
| `backend/migrations/versions/<ts>_widen_asset_money_columns.py` | `ALTER TABLE ... ALTER COLUMN ... TYPE DECIMAL(18,4)` × 7 |

### Migration Template

```python
"""widen asset money columns to DECIMAL(18,4)

Revision ID: <auto>
Revises: <previous>
Create Date: 2026-04-20
"""
from alembic import op
import sqlalchemy as sa

COLUMNS = [
    ("asset_transfers", "book_value_at_transfer"),
    ("asset_revaluations", "old_value"),
    ("asset_revaluations", "new_value"),
    ("asset_revaluations", "difference"),
    ("asset_maintenance", "cost"),
    ("asset_insurance", "premium_amount"),
    ("asset_insurance", "coverage_amount"),
]

def upgrade():
    for table, column in COLUMNS:
        op.alter_column(table, column,
            type_=sa.Numeric(18, 4),
            existing_type=sa.Numeric(15, 2))

def downgrade():
    for table, column in COLUMNS:
        op.alter_column(table, column,
            type_=sa.Numeric(15, 2),
            existing_type=sa.Numeric(18, 4))
```

---

## Change 4: Add Asset Revaluation/Lifecycle Columns

### Root Cause

The `assets` table lacks columns needed for proper IAS 16 revaluation tracking and IFRS compliance. Revaluation currently overwrites `cost`, destroying historical data.

### New Columns on `assets` Table

```sql
    current_value DECIMAL(18,4),           -- updated on revaluation; cost stays as purchase cost
    revaluation_surplus DECIMAL(18,4) DEFAULT 0,  -- IAS 16.40 tracking
```

### Dual-Update Checklist (Constitution XXVIII ⛔)

| Location | Action |
|----------|--------|
| `backend/database.py` — `assets` CREATE TABLE | Add 2 columns |
| `backend/migrations/versions/<ts>_add_asset_revaluation_columns.py` | `ALTER TABLE assets ADD COLUMN ...` × 2 |

### Migration Template

```python
"""add revaluation tracking columns to assets

Revision ID: <auto>
Revises: <previous>
Create Date: 2026-04-20
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('assets',
        sa.Column('current_value', sa.Numeric(18, 4), nullable=True))
    op.add_column('assets',
        sa.Column('revaluation_surplus', sa.Numeric(18, 4),
                   server_default='0', nullable=True))
    # Backfill current_value = cost for existing assets
    op.execute("UPDATE assets SET current_value = cost WHERE current_value IS NULL")

def downgrade():
    op.drop_column('assets', 'current_value')
    op.drop_column('assets', 'revaluation_surplus')
```

---

## Change 5: Add Missing Indexes

### Root Cause

FK and frequently-filtered columns across project/asset tables lack indexes, degrading query performance at scale.

### Indexes to Add

| Table | Column(s) | Index Name |
|-------|-----------|-----------|
| `project_tasks` | `project_id` | `ix_project_tasks_project_id` |
| `project_expenses` | `project_id` | `ix_project_expenses_project_id` |
| `project_revenues` | `project_id` | `ix_project_revenues_project_id` |
| `project_timesheets` | `project_id` | `ix_project_timesheets_project_id` |
| `project_timesheets` | `employee_id` | `ix_project_timesheets_employee_id` |
| `project_documents` | `project_id` | `ix_project_documents_project_id` |
| `task_dependencies` | `task_id` | `ix_task_dependencies_task_id` |
| `contract_items` | `contract_id` | `ix_contract_items_contract_id` |
| `asset_depreciation_schedule` | `asset_id` | `ix_asset_depr_schedule_asset_id` |
| `asset_transfers` | `asset_id` | `ix_asset_transfers_asset_id` |
| `asset_revaluations` | `asset_id` | `ix_asset_revaluations_asset_id` |
| `asset_maintenance` | `asset_id` | `ix_asset_maintenance_asset_id` |

### Dual-Update Checklist (Constitution XXVIII ⛔)

| Location | Action |
|----------|--------|
| `backend/database.py` — index section per table | Add `CREATE INDEX IF NOT EXISTS ...` statements |
| `backend/migrations/versions/<ts>_add_project_asset_indexes.py` | `op.create_index(...)` × 12 |

---

## Change 6: Pydantic Schema Updates (Code-Only — No DDL)

These changes affect Python schema files only, no database changes.

### `schemas/projects.py` — Float → Decimal

| Field | Current | Target |
|-------|---------|--------|
| `budget` | `float` | `Decimal` |
| `amount` | `float` | `Decimal` |
| `hours` | `float` | `Decimal` |
| `unit_price` | `float` | `Decimal` |
| `tax_rate` | `float` | `Decimal` |
| `discount` | `float` | `Decimal` |
| `exchange_rate` | `float` | `Decimal` |
| `cost_impact` | `float` | `Decimal` |
| `retainer_amount` | `float` | `Decimal` |

### `schemas/contracts.py` — Float → Decimal

| Field | Current | Target |
|-------|---------|--------|
| `quantity` | `float` | `Decimal` |
| `unit_price` | `float` | `Decimal` |
| `tax_rate` | `float` | `Decimal` |
| `total` | `float` | `Decimal` |
| `total_amount` | `float` | `Decimal` |

### `schemas/assets.py` — Float → Decimal + Expand

| Field | Current | Target |
|-------|---------|--------|
| `cost` | `float` | `Decimal` |
| `residual_value` | `float` | `Decimal` |
| `disposal_price` | `float` | `Decimal` |
| `new_value` | `float` | `Decimal` |

`AssetUpdate` schema must be expanded beyond `name`/`status` to include all mutable fields.

---

## No-Change Tables (confirmed correct)

| Table | Notes |
|-------|-------|
| `customers` | EXISTS (`database.py:603-632`); `projects.customer_id REFERENCES customers(id)` is valid |
| `projects` (core columns) | Existing columns correct; only retainer columns missing |
| `contracts` | Column names correct in DDL; bugs are in query code, not schema |
| `assets` (core columns) | `cost`, `residual_value`, `useful_life_years` all present and correct |
| `asset_categories` | Table exists; FK link from `assets` is a nice-to-have, not blocking |
