# Data Model: Audit Core Admin Module

**Date**: 2026-04-14 | **Branch**: `005-audit-core-admin`

---

## Overview

This is a code-audit module — no new tables are created. The data model documents:
1. **Existing entities** being audited/hardened (unchanged schema)
2. **Schema additions** to existing tables (new columns)
3. **Relationships** relevant to the audit scope

---

## Existing Entities (Audit Targets)

### audit_logs (per-tenant DB)

Stores all user activity within a company.

| Column | Type | Constraint | Notes |
|--------|------|------------|-------|
| id | SERIAL | PK | |
| user_id | INTEGER | NOT NULL | FK to users |
| username | VARCHAR | NOT NULL | Denormalized for query speed |
| action | VARCHAR | NOT NULL | e.g., "create", "update", "delete" |
| resource_type | VARCHAR | | e.g., "invoice", "branch", "settings" |
| resource_id | VARCHAR | | ID of affected resource |
| details | JSONB | DEFAULT '{}' | Structured change details |
| ip_address | VARCHAR | | Client IP |
| branch_id | INTEGER | | FK to branches |
| created_at | TIMESTAMPTZ | NOT NULL | UTC timestamp |

**Gaps identified**:
- No `is_archived` column for retention management
- No index on `created_at` for archival queries
- No index on `(created_at) WHERE NOT is_archived` for live query performance

### system_activity_log (aman_system DB)

Stores system-level events (company creation, system admin actions).

| Column | Type | Constraint | Notes |
|--------|------|------------|-------|
| id | SERIAL | PK | |
| company_id | VARCHAR | | Affected company |
| action_type | VARCHAR | NOT NULL | Event type |
| action_description | TEXT | | Free-text description |
| performed_by | VARCHAR | | Username or system |
| ip_address | VARCHAR | | Client IP |
| user_agent | TEXT | | Browser/client UA |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | |

### companies (aman_system DB)

| Column | Type | Notes |
|--------|------|-------|
| id | VARCHAR | PK, company identifier |
| name | VARCHAR | Company name (Arabic) |
| email | VARCHAR | Admin email |
| db_name | VARCHAR | `aman_{company_id}` |
| db_user | VARCHAR | DB user for this tenant |
| is_active | BOOLEAN | |
| created_at | TIMESTAMPTZ | |

### branches (per-tenant DB)

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL | PK |
| branch_code | VARCHAR | Unique within company |
| branch_name | VARCHAR | Arabic name |
| is_default | BOOLEAN | One per company |
| is_active | BOOLEAN | Soft delete |
| created_at | TIMESTAMPTZ | |

### company_settings (per-tenant DB)

Key-value store for all company configuration.

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL | PK |
| setting_key | VARCHAR | Unique key |
| setting_value | TEXT | JSON or plain text value |
| updated_at | TIMESTAMPTZ | |

### notifications (per-tenant DB)

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL | PK |
| user_id | INTEGER | Recipient |
| title | VARCHAR | Notification title |
| message | TEXT | Body |
| type | VARCHAR | Category |
| is_read | BOOLEAN | |
| created_at | TIMESTAMPTZ | |

**Gaps identified**:
- No `delivery_status` column for retry tracking
- No `retry_count` column
- No `delivery_channel` column
- No `last_retry_at` timestamp

### webhooks (per-tenant DB)

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL | PK |
| url | VARCHAR | Target URL |
| secret | VARCHAR | **Plaintext** — needs encryption |
| events | JSONB | Subscribed event types |
| is_active | BOOLEAN | |
| created_at | TIMESTAMPTZ | |

### api_keys (per-tenant DB)

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL | PK |
| key_hash | VARCHAR | SHA256 hash (never plaintext) |
| name | VARCHAR | Human label |
| permissions | JSONB | Allowed operations |
| is_active | BOOLEAN | |
| created_at | TIMESTAMPTZ | |

### scheduled_reports (per-tenant DB)

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL | PK |
| report_type | VARCHAR | Report identifier |
| schedule | VARCHAR | Cron/interval spec |
| is_active | BOOLEAN | |
| last_run_at | TIMESTAMPTZ | |
| recipients | JSONB | Email addresses |

---

## Schema Additions (New Columns)

### audit_logs — Archival Support

```sql
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS is_archived BOOLEAN DEFAULT FALSE;
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ;

-- Partial index for live queries (non-archived entries)
CREATE INDEX IF NOT EXISTS idx_audit_logs_live 
  ON audit_logs (created_at DESC) 
  WHERE NOT is_archived;

-- Index for archival job (find entries to archive)
CREATE INDEX IF NOT EXISTS idx_audit_logs_archival 
  ON audit_logs (created_at) 
  WHERE NOT is_archived;
```

### notifications — Delivery Tracking

```sql
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS delivery_status VARCHAR DEFAULT 'pending';
-- Values: 'pending', 'delivered', 'failed', 'permanently_failed'

ALTER TABLE notifications ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0;
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS last_retry_at TIMESTAMPTZ;
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS delivery_channel VARCHAR;
-- Values: 'in_app', 'email', 'websocket', 'push'

-- Index for retry job (find pending retries)
CREATE INDEX IF NOT EXISTS idx_notifications_retry 
  ON notifications (last_retry_at) 
  WHERE delivery_status = 'failed' AND retry_count < 3;
```

---

## Relationships

```
aman_system DB:
  system_activity_log ──── references companies (by company_id)

Per-tenant DB (aman_{company_id}):
  audit_logs ─────── references branches (branch_id → branches.id)
  audit_logs ─────── references users (user_id → users.id)
  notifications ──── references users (user_id → users.id)
  webhooks ────────  standalone (no FK)
  api_keys ────────  standalone (no FK)
  company_settings ─ standalone (key-value)
  scheduled_reports ─ standalone
  branches ────────  referenced by invoices, journal_entries, inventory_movements
```

---

## State Transitions

### Notification Delivery Status
```
pending → delivered       (successful channel dispatch)
pending → failed          (transient failure, retry scheduled)
failed  → delivered       (retry succeeded)
failed  → permanently_failed  (3rd retry failed)
```

### Audit Log Archival Status
```
is_archived=false → is_archived=true  (entry older than 1 year, archived by scheduler)
is_archived=true  → DELETED           (entry older than 7 years, purged by scheduler)
```

---

## Validation Rules

| Entity | Field | Rule |
|--------|-------|------|
| branches | branch_code | Unique within company, alphanumeric + hyphen |
| branches | DELETE | Blocked if referenced by invoices, journal_entries, or inventory_movements |
| company_settings | setting_key | Must exist in validation map; value validated by type/range |
| webhooks | url | Must be HTTPS or HTTP, must not resolve to private/reserved IP |
| webhooks | secret | Encrypted at rest (Fernet), decrypted only for HMAC signing |
| api_keys | key_hash | SHA256, never stored plaintext |
| notifications | retry_count | Max 3 (after 3 → permanently_failed) |
| audit_logs | * | Immutable after creation (no UPDATE/DELETE by application) |
