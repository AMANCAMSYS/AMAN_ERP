# Data Model: Reports & Analytics, Approvals & Workflow — Audit & Bug Fixes

**Feature**: 020-audit-reports-approvals  
**Date**: 2026-04-20

---

## Overview

This audit requires schema changes in **three categories**:

1. **DDL fixes in `database.py`** — missing columns, wrong types, missing FKs, missing indexes, default conflicts
2. **Alembic migrations** — to apply the same fixes to existing tenant DBs
3. **One new table** — `scheduled_report_results` for storing generated report output

No tables are dropped. All changes are additive (new columns, new FKs, new indexes, new table) or corrective (type changes, default fixes).

---

## Change 1: Add Missing Audit Columns (Constitution XVII)

### Root Cause

Constitution XVII (`AuditMixin`) requires `created_at`, `updated_at`, `created_by`, `updated_by` on all domain models. Three tables in the Reports & Approvals modules are missing `updated_at`, and `report_templates` also lacks `created_by`.

### Tables Affected

| Table | Missing Columns |
|-------|----------------|
| `shared_reports` | `updated_at` |
| `report_templates` | `updated_at`, `created_by` |

### Current DDL (abbreviated)

```sql
CREATE TABLE IF NOT EXISTS shared_reports (
    id SERIAL PRIMARY KEY,
    ...
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    -- updated_at MISSING
    UNIQUE(report_type, report_id, shared_with)
);

CREATE TABLE IF NOT EXISTS report_templates (
    id SERIAL PRIMARY KEY,
    ...
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    -- updated_at MISSING
    -- created_by MISSING
);
```

### Target Columns

```sql
-- shared_reports
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

-- report_templates
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES company_users(id),
```

### Dual-Update Checklist (Constitution XXVIII)

| Location | Action |
|----------|--------|
| `backend/database.py` — `shared_reports` CREATE TABLE | Add `updated_at` column |
| `backend/database.py` — `report_templates` CREATE TABLE | Add `updated_at` and `created_by` columns |
| `backend/migrations/versions/<ts>_fix_approval_reports_schema.py` | `ALTER TABLE ... ADD COLUMN ...` × 3 |

### Migration Template

```python
"""add missing audit columns to shared_reports and report_templates

Revision ID: <auto>
Revises: <previous>
Create Date: 2026-04-20
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('shared_reports',
        sa.Column('updated_at', sa.DateTime(timezone=True),
                   server_default=sa.func.current_timestamp(), nullable=True))
    op.add_column('report_templates',
        sa.Column('updated_at', sa.DateTime(timezone=True),
                   server_default=sa.func.current_timestamp(), nullable=True))
    op.add_column('report_templates',
        sa.Column('created_by', sa.Integer(),
                   sa.ForeignKey('company_users.id'), nullable=True))

def downgrade():
    op.drop_column('shared_reports', 'updated_at')
    op.drop_column('report_templates', 'updated_at')
    op.drop_column('report_templates', 'created_by')
```

---

## Change 2: Add Missing FK Constraints to Approval Tables

### Root Cause

Several user-reference columns in the approval tables were added via ALTER TABLE without FK constraints, allowing orphaned references and breaking referential integrity.

### Columns Affected

| Table | Column | Current | Target |
|-------|--------|---------|--------|
| `approval_requests` | `current_approver_id` | `INTEGER` (no FK) | `INTEGER REFERENCES company_users(id)` |
| `approval_requests` | `escalated_to` | `INTEGER` (no FK) | `INTEGER REFERENCES company_users(id)` |
| `approval_actions` | `actioned_by` | `INTEGER` (no FK) | `INTEGER REFERENCES company_users(id)` |

### Current DDL (from ALTER TABLE blocks)

```sql
-- approval_requests (line 4524)
ALTER TABLE approval_requests ADD COLUMN IF NOT EXISTS current_approver_id INTEGER;
ALTER TABLE approval_requests ADD COLUMN IF NOT EXISTS escalated_to INTEGER;

-- approval_actions (line 4509)
CREATE TABLE IF NOT EXISTS approval_actions (
    ...
    actioned_by INTEGER,   -- no FK constraint
    ...
);
```

### Target DDL

```sql
-- approval_requests
ALTER TABLE approval_requests ADD COLUMN IF NOT EXISTS current_approver_id INTEGER REFERENCES company_users(id);
ALTER TABLE approval_requests ADD COLUMN IF NOT EXISTS escalated_to INTEGER REFERENCES company_users(id);

-- approval_actions
    actioned_by INTEGER REFERENCES company_users(id),
```

### Dual-Update Checklist (Constitution XXVIII)

| Location | Action |
|----------|--------|
| `backend/database.py` — `approval_requests` ALTER TABLE block | Add `REFERENCES company_users(id)` to both columns |
| `backend/database.py` — `approval_actions` CREATE TABLE | Add `REFERENCES company_users(id)` to `actioned_by` |
| `backend/migrations/versions/<ts>_fix_approval_reports_schema.py` | Add FK constraints to 3 columns |

### Migration Template

```python
# Part of the same migration as Change 1

def upgrade():
    # ... (Change 1 columns above)

    # Add FK constraints to approval_requests
    op.create_foreign_key(
        'fk_approval_requests_current_approver',
        'approval_requests', 'company_users',
        ['current_approver_id'], ['id'])
    op.create_foreign_key(
        'fk_approval_requests_escalated_to',
        'approval_requests', 'company_users',
        ['escalated_to'], ['id'])

    # Add FK constraint to approval_actions
    op.create_foreign_key(
        'fk_approval_actions_actioned_by',
        'approval_actions', 'company_users',
        ['actioned_by'], ['id'])

def downgrade():
    op.drop_constraint('fk_approval_actions_actioned_by', 'approval_actions', type_='foreignkey')
    op.drop_constraint('fk_approval_requests_escalated_to', 'approval_requests', type_='foreignkey')
    op.drop_constraint('fk_approval_requests_current_approver', 'approval_requests', type_='foreignkey')
```

---

## Change 3: Fix `analytics_dashboards` User Reference Types

### Root Cause

`analytics_dashboards.created_by` and `updated_by` are `VARCHAR(100)` — storing usernames as strings instead of integer FK references to `company_users`. This prevents JOINs, breaks referential integrity, and is inconsistent with every other table in the system.

### Current DDL

```sql
CREATE TABLE IF NOT EXISTS analytics_dashboards (
    id SERIAL PRIMARY KEY,
    ...
    created_by VARCHAR(100),   -- should be INTEGER FK
    updated_by VARCHAR(100),   -- should be INTEGER FK
    ...
);
```

### Target DDL

```sql
    created_by INTEGER REFERENCES company_users(id),
    updated_by INTEGER REFERENCES company_users(id),
```

### Dual-Update Checklist (Constitution XXVIII)

| Location | Action |
|----------|--------|
| `backend/database.py` — `analytics_dashboards` CREATE TABLE | Change both columns from `VARCHAR(100)` to `INTEGER REFERENCES company_users(id)` |
| `backend/migrations/versions/<ts>_fix_approval_reports_schema.py` | Type change with data conversion |

### Migration Template

```python
# Part of the same migration

def upgrade():
    # ... (Changes 1-2 above)

    # Convert VARCHAR(100) username → INTEGER user ID
    # Step 1: Add temporary INT columns
    op.add_column('analytics_dashboards',
        sa.Column('created_by_new', sa.Integer(), nullable=True))
    op.add_column('analytics_dashboards',
        sa.Column('updated_by_new', sa.Integer(), nullable=True))

    # Step 2: Populate from company_users lookup
    op.execute("""
        UPDATE analytics_dashboards ad
        SET created_by_new = cu.id
        FROM company_users cu
        WHERE cu.username = ad.created_by
    """)
    op.execute("""
        UPDATE analytics_dashboards ad
        SET updated_by_new = cu.id
        FROM company_users cu
        WHERE cu.username = ad.updated_by
    """)

    # Step 3: Drop old, rename new, add FK
    op.drop_column('analytics_dashboards', 'created_by')
    op.drop_column('analytics_dashboards', 'updated_by')
    op.alter_column('analytics_dashboards', 'created_by_new', new_column_name='created_by')
    op.alter_column('analytics_dashboards', 'updated_by_new', new_column_name='updated_by')
    op.create_foreign_key(
        'fk_analytics_dashboards_created_by',
        'analytics_dashboards', 'company_users',
        ['created_by'], ['id'])
    op.create_foreign_key(
        'fk_analytics_dashboards_updated_by',
        'analytics_dashboards', 'company_users',
        ['updated_by'], ['id'])

def downgrade():
    op.drop_constraint('fk_analytics_dashboards_updated_by', 'analytics_dashboards', type_='foreignkey')
    op.drop_constraint('fk_analytics_dashboards_created_by', 'analytics_dashboards', type_='foreignkey')
    op.alter_column('analytics_dashboards', 'created_by',
        type_=sa.String(100), existing_type=sa.Integer())
    op.alter_column('analytics_dashboards', 'updated_by',
        type_=sa.String(100), existing_type=sa.Integer())
```

**Risk**: Existing rows with usernames that don't match any `company_users.username` will get `NULL` for the new INT column. This is acceptable — the migration preserves data where possible and nullifies orphaned references. A backup before migration is recommended.

---

## Change 4: Fix `approval_workflows.conditions` Default Conflict

### Root Cause

The `conditions` column is defined with `DEFAULT '{}'` in the CREATE TABLE (line 4480) but the ALTER TABLE block (line 4912) re-declares it with `DEFAULT '[]'`. Since ALTER ADD COLUMN is a no-op when the column exists, the CREATE TABLE default wins for fresh DBs. However, the inconsistency is confusing and should be resolved.

The canonical default is `'{}'` (empty JSON object) because conditions contain named fields (`min_amount`, `max_amount`), not an ordered array.

### Current DDL

```sql
-- CREATE TABLE (line 4480)
    conditions JSONB DEFAULT '{}',

-- ALTER TABLE (line 4912) — contradicts CREATE
ALTER TABLE approval_workflows ADD COLUMN IF NOT EXISTS conditions JSONB DEFAULT '[]';
```

### Target DDL

```sql
-- CREATE TABLE (line 4480) — unchanged
    conditions JSONB DEFAULT '{}',

-- ALTER TABLE (line 4912) — fix to match
ALTER TABLE approval_workflows ADD COLUMN IF NOT EXISTS conditions JSONB DEFAULT '{}';
```

### Dual-Update Checklist (Constitution XXVIII)

| Location | Action |
|----------|--------|
| `backend/database.py` — `approval_workflows` ALTER TABLE block | Change `DEFAULT '[]'` to `DEFAULT '{}'` |
| No migration needed | ALTER ADD COLUMN is no-op on existing DBs; default only matters for fresh tenants |

---

## Change 5: Add Missing Indexes

### Root Cause

FK and frequently-filtered columns across approval and report tables lack indexes, degrading query performance as data grows.

### Indexes to Add

| Table | Column(s) | Index Name |
|-------|-----------|-----------|
| `approval_requests` | `workflow_id` | `idx_approval_requests_workflow` |
| `approval_requests` | `requested_by` | `idx_approval_requests_requested_by` |
| `report_templates` | `template_type` | `idx_report_templates_type` |
| `approval_workflows` | `document_type` | `idx_approval_workflows_doc_type` |

### Dual-Update Checklist (Constitution XXVIII)

| Location | Action |
|----------|--------|
| `backend/database.py` — after each relevant CREATE TABLE | Add `CREATE INDEX IF NOT EXISTS ...` statements |
| `backend/migrations/versions/<ts>_fix_approval_reports_schema.py` | `op.create_index(...)` × 4 |

### Migration Template

```python
# Part of the same migration

def upgrade():
    # ... (Changes 1-3 above)

    op.create_index('idx_approval_requests_workflow',
                    'approval_requests', ['workflow_id'])
    op.create_index('idx_approval_requests_requested_by',
                    'approval_requests', ['requested_by'])
    op.create_index('idx_report_templates_type',
                    'report_templates', ['template_type'])
    op.create_index('idx_approval_workflows_doc_type',
                    'approval_workflows', ['document_type'])

def downgrade():
    op.drop_index('idx_approval_workflows_doc_type', 'approval_workflows')
    op.drop_index('idx_report_templates_type', 'report_templates')
    op.drop_index('idx_approval_requests_requested_by', 'approval_requests')
    op.drop_index('idx_approval_requests_workflow', 'approval_requests')
```

---

## Change 6: Create `scheduled_report_results` Table

### Root Cause

The scheduled reports module needs a table to store generated report output. Currently the execution is a TODO stub — when implemented (FR-039), each scheduled run will store its result in this new table. No existing table serves this purpose.

### New Table DDL

```sql
CREATE TABLE IF NOT EXISTS scheduled_report_results (
    id SERIAL PRIMARY KEY,
    scheduled_report_id INTEGER REFERENCES scheduled_reports(id) ON DELETE CASCADE,
    report_data JSONB NOT NULL,
    generated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'completed'
);

CREATE INDEX IF NOT EXISTS idx_report_results_schedule
    ON scheduled_report_results(scheduled_report_id);
```

### Dual-Update Checklist (Constitution XXVIII)

| Location | Action |
|----------|--------|
| `backend/database.py` — after `scheduled_reports` CREATE TABLE | Add full CREATE TABLE + index |
| `backend/migrations/versions/<ts>_add_scheduled_report_results.py` | Create table + index |

### Migration Template

```python
"""add scheduled_report_results table

Revision ID: <auto>
Revises: <previous>
Create Date: 2026-04-20
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table('scheduled_report_results',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('scheduled_report_id', sa.Integer(),
                   sa.ForeignKey('scheduled_reports.id', ondelete='CASCADE'),
                   nullable=True),
        sa.Column('report_data', sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True),
                   server_default=sa.func.current_timestamp()),
        sa.Column('status', sa.String(20), server_default='completed'),
    )
    op.create_index('idx_report_results_schedule',
                    'scheduled_report_results', ['scheduled_report_id'])

def downgrade():
    op.drop_index('idx_report_results_schedule', 'scheduled_report_results')
    op.drop_table('scheduled_report_results')
```

---

## Change 7: Migrate `scheduled_reports.recipients` TEXT → JSONB

### Root Cause

The `recipients` field stores email addresses as comma-separated TEXT (e.g., `"user1@co.com,user2@co.com"`). This makes individual recipient querying/validation impossible and is inconsistent with the JSONB patterns used elsewhere in the system.

### Current DDL

```sql
CREATE TABLE IF NOT EXISTS scheduled_reports (
    ...
    recipients TEXT NOT NULL,
    ...
);
```

### Target DDL

```sql
    recipients JSONB DEFAULT '[]',
```

### Dual-Update Checklist (Constitution XXVIII)

| Location | Action |
|----------|--------|
| `backend/database.py` — `scheduled_reports` CREATE TABLE | Change `recipients TEXT NOT NULL` to `recipients JSONB DEFAULT '[]'` |
| `backend/migrations/versions/<ts>_migrate_recipients_to_jsonb.py` | ALTER TYPE + data conversion |

### Migration Template

```python
"""migrate scheduled_reports recipients from TEXT to JSONB

Revision ID: <auto>
Revises: <previous>
Create Date: 2026-04-20
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Convert existing comma-separated TEXT to JSONB array
    # Handle NULLs and empty strings gracefully
    op.execute("""
        ALTER TABLE scheduled_reports
        ALTER COLUMN recipients TYPE JSONB
        USING CASE
            WHEN recipients IS NULL OR recipients = '' THEN '[]'::jsonb
            ELSE to_jsonb(string_to_array(TRIM(recipients), ','))
        END
    """)
    op.execute("""
        ALTER TABLE scheduled_reports
        ALTER COLUMN recipients SET DEFAULT '[]'::jsonb
    """)

def downgrade():
    op.execute("""
        ALTER TABLE scheduled_reports
        ALTER COLUMN recipients TYPE TEXT
        USING array_to_string(
            ARRAY(SELECT jsonb_array_elements_text(recipients)), ','
        )
    """)
    op.execute("""
        ALTER TABLE scheduled_reports
        ALTER COLUMN recipients SET NOT NULL
    """)
```

---

## Pydantic Schema Updates (Code-Only — No DDL)

These changes affect Python backend code only, no database changes.

### `routers/reports.py` — Float → Decimal

| Schema/Field | Current | Target |
|-------------|---------|--------|
| `TrialBalanceItem` monetary fields | `float` | `Decimal` |
| `FinancialStatementItem` monetary fields | `float` | `Decimal` |
| `_compute_net_income_from_gl()` return | `float` | `Decimal` |
| `exchange_rate` defaults throughout | `1.0` (float) | `Decimal("1")` |

### `routers/approvals.py` — Float → Decimal + New Schema

| Schema/Field | Current | Target |
|-------------|---------|--------|
| `WorkflowCreateSchema.min_amount` | `Optional[float]` | `Optional[Decimal]` |
| `WorkflowCreateSchema.max_amount` | `Optional[float]` | `Optional[Decimal]` |
| `create_approval_request` parameter | raw `dict` | `ApprovalRequestCreate` Pydantic schema |

### `utils/approval_utils.py` — Float → Decimal

| Parameter | Current | Target |
|-----------|---------|--------|
| `amount` | `float` | `Decimal` |

---

## No-Change Tables (confirmed correct)

| Table | Notes |
|-------|-------|
| `approval_workflows` (core columns) | Core CREATE TABLE is correct; only ALTER TABLE default fix needed (Change 4) |
| `approval_requests` (core columns) | Core CREATE TABLE is correct; only FK additions to ALTER columns needed (Change 2) |
| `analytics_dashboard_widgets` | Correctly references `analytics_dashboards(id)` via FK; no changes needed |
| `scheduled_reports` (core columns) | Only `recipients` column type changes (Change 7) |
| `shared_reports.report_id` | Polymorphic reference (no FK) — intentional design decision, documented in spec assumptions |
