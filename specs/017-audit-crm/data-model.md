# Data Model: CRM Module Audit & Bug Fixes

**Feature**: 017-audit-crm  
**Date**: 2026-04-20

---

## Overview

This feature requires **one schema change**: dropping four legacy columns from `marketing_campaigns`.  
All other fixes are code-only (wrong column names in queries, wrong field names in frontend).  
No new tables, no new columns, no FK changes.

---

## Schema Change: `marketing_campaigns` — Drop Legacy Columns

### Current DDL (`backend/database.py:4719–4750`, abbreviated)

```sql
CREATE TABLE IF NOT EXISTS marketing_campaigns (
    id SERIAL PRIMARY KEY,
    ...
    -- LEGACY (stale — never written, always 0): TO BE REMOVED
    sent_count INT DEFAULT 0,        -- line 4730
    open_count INT DEFAULT 0,        -- line 4731
    click_count INT DEFAULT 0,       -- line 4732
    conversion_count INT DEFAULT 0,  -- line 4733
    ...
    -- CURRENT (written by campaign execute endpoint): KEEP
    total_sent INTEGER DEFAULT 0,      -- line 4740
    total_delivered INTEGER DEFAULT 0, -- line 4741
    total_opened INTEGER DEFAULT 0,    -- line 4742
    total_clicked INTEGER DEFAULT 0,   -- line 4743
    total_responded INTEGER DEFAULT 0  -- line 4744
);
```

### Target DDL (after fix)

```sql
CREATE TABLE IF NOT EXISTS marketing_campaigns (
    id SERIAL PRIMARY KEY,
    ...
    -- Legacy columns removed
    total_sent INTEGER DEFAULT 0,
    total_delivered INTEGER DEFAULT 0,
    total_opened INTEGER DEFAULT 0,
    total_clicked INTEGER DEFAULT 0,
    total_responded INTEGER DEFAULT 0
);
```

### Dual-Update Checklist (Constitution XXVIII ⛔)

| Location | Action |
|----------|--------|
| `backend/database.py` lines 4730–4733 | Delete the four `sent_count`, `open_count`, `click_count`, `conversion_count` lines |
| `backend/migrations/versions/<timestamp>_drop_legacy_campaign_columns.py` | `ALTER TABLE marketing_campaigns DROP COLUMN IF EXISTS sent_count, open_count, click_count, conversion_count` |

### Migration Template

```python
"""drop legacy campaign metric columns

Revision ID: <auto>
Revises: <previous>
Create Date: 2026-04-20
"""
from alembic import op

def upgrade():
    op.drop_column('marketing_campaigns', 'sent_count')
    op.drop_column('marketing_campaigns', 'open_count')
    op.drop_column('marketing_campaigns', 'click_count')
    op.drop_column('marketing_campaigns', 'conversion_count')

def downgrade():
    op.add_column('marketing_campaigns',
        sa.Column('sent_count', sa.Integer(), server_default='0', nullable=True))
    op.add_column('marketing_campaigns',
        sa.Column('open_count', sa.Integer(), server_default='0', nullable=True))
    op.add_column('marketing_campaigns',
        sa.Column('click_count', sa.Integer(), server_default='0', nullable=True))
    op.add_column('marketing_campaigns',
        sa.Column('conversion_count', sa.Integer(), server_default='0', nullable=True))
```

> **Pre-condition**: BUG-05 backend fix must be merged before or together with this migration,  
> so the ROI analytics endpoint no longer references the dropped columns.

---

## No Other Schema Changes

| Entity | Change | Reason |
|--------|--------|--------|
| `sales_quotations` | None | Correct schema already exists (`sq_number`, `expiry_date`). BUG-01 is a code fix only. |
| `sales_quotation_lines` | None | Correct schema already exists (`sq_id`). BUG-01 is a code fix only. |
| `sales_opportunities` | None | `won_quotation_id INT` already exists (`database.py:4653`). |
| `support_tickets` | None | `sla_hours`, `created_at TIMESTAMPTZ` already correct. BUG-07 is a Python fix only. |
| `ticket_comments` | None | `comment` column already correct. BUG-02/03 are frontend fixes only. |
| Notification tables | None | `notification_service.dispatch()` handles its own inserts. |

---

## Existing Column Reference (confirmed from `database.py`)

| Table | Column | Type | Notes |
|-------|--------|------|-------|
| `sales_quotations` | `sq_number` | `VARCHAR(50) UNIQUE NOT NULL` | line 995 |
| `sales_quotations` | `expiry_date` | `DATE` | line 1000 |
| `sales_quotation_lines` | `sq_id` | `INTEGER REFERENCES sales_quotations(id) ON DELETE CASCADE` | line 1018 |
| `sales_opportunities` | `won_quotation_id` | `INT` | line 4653 |
| `ticket_comments` | `comment` | `TEXT` | — |
| `ticket_comments` | `created_by` | `INT` | — |
| `marketing_campaigns` | `total_sent` | `INTEGER DEFAULT 0` | line 4740 |
| `marketing_campaigns` | `total_opened` | `INTEGER DEFAULT 0` | line 4742 |
| `marketing_campaigns` | `total_clicked` | `INTEGER DEFAULT 0` | line 4743 |
| `marketing_campaigns` | `total_responded` | `INTEGER DEFAULT 0` | line 4744 |
