# API Contracts: Audit Core Admin Module

**Date**: 2026-04-14 | **Branch**: `005-audit-core-admin`

---

## Overview

This module does NOT create new endpoints. These contracts define the **post-audit conformance requirements** for existing endpoints — what each MUST do after hardening.

---

## Cross-Cutting Contracts (Apply to ALL endpoints in scope)

### CC-1: Error Response Contract

All error responses MUST conform to:

```json
{
  "detail": "<generic Arabic message>"
}
```

**Forbidden**: `detail=str(e)`, `detail=f"...{e}"`, stack traces, SQL fragments, file paths, class names.

**Required**: `logger.exception()` MUST be called before raising the generic HTTPException.

**Pattern**:
```python
except HTTPException:
    raise
except Exception:
    logger.exception("Internal error in <endpoint_name>")
    raise HTTPException(status_code=500, detail="حدث خطأ داخلي")
```

### CC-2: Tenant Isolation Contract

Every endpoint MUST:
1. Extract `company_id` from `current_user.company_id`
2. Route DB via `get_db_connection(company_id)`
3. Never accept user-supplied `company_id` for data access (except system_admin viewing audit logs)

### CC-3: Audit Trail Contract

Every **state-changing** endpoint MUST call `log_activity()` with:
- `user_id`: from `current_user.id`
- `username`: from `current_user.username`
- `action`: verb string (`"create"`, `"update"`, `"delete"`, `"import"`, `"configure"`)
- `resource_type`: entity name (`"branch"`, `"settings"`, `"webhook"`)
- `resource_id`: affected entity ID
- `details`: dict with changed fields/values (before → after for updates)
- `request`: FastAPI Request object
- `branch_id`: when applicable

### CC-4: Branch Access Contract

Endpoints that filter by `branch_id` MUST:
1. Call `validate_branch_access(current_user, branch_id)` before processing
2. For listing endpoints without explicit `branch_id`: auto-filter by `allowed_branches` when user is not admin

---

## Router-Specific Contracts

### companies.py (8 endpoints)

| Method | Path | Auth | Audit | Error Contract | Notes |
|--------|------|------|-------|----------------|-------|
| POST | `/register` | system_admin | ✅ log_activity | CC-1 | Must validate `db_name` via `validate_aman_identifier()` |
| GET | `/` | authenticated | N/A (read) | CC-1 | Tenant-scoped |
| PUT | `/{id}` | admin | ✅ log_activity | CC-1 | Update company profile |
| POST | `/{id}/logo` | admin | ✅ log_activity | CC-1 | File upload, no path traversal |
| PUT | `/{id}/modules` | admin | ✅ log_activity | CC-1 | Module enable/disable |
| GET | `/{id}/settings` | authenticated | N/A (read) | CC-1 | |
| PUT | `/{id}/settings` | admin | ✅ log_activity | CC-1 | |
| DELETE | `/{id}` | system_admin | ✅ log_activity | CC-1 | Soft-delete only |

### branches.py (4 endpoints)

| Method | Path | Auth | Audit | Error Contract | Special |
|--------|------|------|-------|----------------|---------|
| GET | `/` | authenticated | N/A | CC-1 | Filter by allowed_branches |
| POST | `/` | branches.create | ✅ log_activity | CC-1 | Unique branch_code check |
| PUT | `/{id}` | branches.update | ✅ log_activity | CC-1 | |
| DELETE | `/{id}` | branches.delete | ✅ log_activity | CC-1 | MUST check for dependent transactions before delete |

**Branch Deletion Pre-Check**:
```sql
SELECT COUNT(*) FROM invoices WHERE branch_id = :bid
UNION ALL
SELECT COUNT(*) FROM journal_entries WHERE branch_id = :bid
UNION ALL
SELECT COUNT(*) FROM inventory_movements WHERE branch_id = :bid
```
If any count > 0 → HTTP 409 with `"لا يمكن حذف الفرع لوجود عمليات مرتبطة"`.

### settings.py (4 endpoints)

| Method | Path | Auth | Audit | Error Contract | Special |
|--------|------|------|-------|----------------|---------|
| GET | `/` | authenticated | N/A | CC-1 | Permission-filtered |
| GET | `/{key}` | authenticated | N/A | CC-1 | |
| PUT | `/{key}` | settings.manage | ✅ log_activity | CC-1 | MUST validate value type/range |
| PUT | `/bulk` | settings.manage | ✅ log_activity | CC-1 | MUST reject unknown keys |

**Settings Validation Contract**:
- Every `setting_key` MUST exist in `SETTINGS_VALIDATION_MAP`
- Unknown keys → HTTP 400 `"مفتاح إعدادات غير معروف"`
- Type mismatch → HTTP 400 `"قيمة غير صالحة للإعداد"`

### notifications.py (11 endpoints)

| Method | Path | Auth | Audit | Error Contract | Special |
|--------|------|------|-------|----------------|---------|
| GET | `/` | authenticated | N/A | CC-1 | Tenant-scoped |
| GET | `/unread-count` | authenticated | N/A | CC-1 | |
| PUT | `/{id}/read` | authenticated | N/A (low-value) | CC-1 | |
| POST | `/mark-all-read` | authenticated | N/A (low-value) | CC-1 | |
| POST | `/send` | notifications.send | ✅ log_activity | CC-1 | Must not fire-and-forget |
| GET | `/settings` | notifications.manage | N/A | CC-1 | Mask SMTP passwords |
| PUT | `/settings` | notifications.manage | ✅ log_activity | CC-1 | Validate input types |
| GET | `/preferences` | authenticated | N/A | CC-1 | |
| PUT | `/preferences` | authenticated | N/A (low-value) | CC-1 | |
| POST | `/test-email` | notifications.manage | N/A | CC-1 | Remove fake SMTP bypass |
| WS | `/ws` | JWT (query/cookie) | N/A | N/A | MUST validate before accept |

### audit.py (3 endpoints)

| Method | Path | Auth | Error Contract | Special |
|--------|------|------|----------------|---------|
| GET | `/logs` | audit.view | CC-1 | Default: `is_archived=false`. Param: `include_archived` |
| GET | `/logs/actions` | audit.view | CC-1 | Distinct action list |
| GET | `/logs/stats` | audit.view | CC-1 | Branch-scoped stats |

### data_import.py (6 endpoints)

| Method | Path | Auth | Audit | Error Contract | Special |
|--------|------|------|-------|----------------|---------|
| GET | `/templates` | data_import.view | N/A | CC-1 | |
| POST | `/preview` | data_import.execute | N/A | CC-1 | File validation |
| POST | `/execute` | data_import.execute | ✅ log_activity | CC-1 | Partial-commit, sanitized errors |
| GET | `/history` | data_import.view | N/A | CC-1 | |
| GET | `/export/{type}` | data_import.export | N/A | CC-1 | |
| GET | `/config` | data_import.view | N/A | CC-1 | |

### external.py (17 endpoints)

| Method | Path | Auth | Audit | Error Contract | Special |
|--------|------|------|-------|----------------|---------|
| POST | `/webhooks` | webhooks.manage | ✅ log_activity | CC-1 | **SSRF validation on URL** |
| GET | `/webhooks` | webhooks.view | N/A | CC-1 | |
| PUT | `/webhooks/{id}` | webhooks.manage | ✅ log_activity | CC-1 | **SSRF validation** |
| DELETE | `/webhooks/{id}` | webhooks.manage | ✅ log_activity | CC-1 | |
| POST | `/api-keys` | api_keys.manage | ✅ log_activity | CC-1 | Key hashed, shown once |
| GET | `/api-keys` | api_keys.view | N/A | CC-1 | Never return hash/key |
| DELETE | `/api-keys/{id}` | api_keys.manage | ✅ log_activity | CC-1 | Soft-delete |
| POST | `/webhooks/{id}/test` | webhooks.manage | N/A | CC-1 | |
| *ZATCA endpoints* | various | zatca.manage | Per-existing | CC-1 | Out of scope (compliance module) |
| *WHT endpoints* | various | wht.manage | Per-existing | CC-1 | Out of scope (compliance module) |

### dashboard.py (23 endpoints)

| Method | Path | Auth | Error Contract | Special |
|--------|------|------|----------------|---------|
| GET | `/stats` | dashboard.view | CC-1 | **Cache: 60s TTL** |
| GET | `/charts/*` | dashboard.view | CC-1 | **Cache: 60s TTL** |
| PUT | `/layout` | dashboard.manage | CC-1 | Widget save |
| GET | `/widgets/*` | dashboard.view | CC-1 | Branch-filtered |

**Cache Contract**: All `@cached` decorators MUST use `expire=60`. Financial writes (invoice/JE/payment) in other routers MUST call `invalidate_company_cache(company_id, "dashboard")`.

### system_completion.py (23 endpoints)

Already well-hardened. Contract: maintain existing pattern (generic errors, log_activity on state changes).

### parties.py (2 endpoints)

Read-only. Contract: CC-1 (error sanitization), CC-2 (tenant isolation).

---

## Service Contracts

### notification_service.py — Retry Contract

```
dispatch(company_id, user_id, event_type, data, channels):
  for channel in channels:
    try:
      deliver(channel, data)
      update notifications SET delivery_status='delivered', delivery_channel=channel
    except TransientError:
      update notifications SET delivery_status='failed', retry_count+=1, last_retry_at=now()
    except PermanentError:
      update notifications SET delivery_status='permanently_failed'

retry_failed_notifications():  # Called by scheduler every 1 minute
  SELECT * FROM notifications WHERE delivery_status='failed' AND retry_count < 3
    AND last_retry_at < now() - backoff_interval(retry_count)
  for each: re-attempt delivery
  if retry_count >= 3: SET delivery_status='permanently_failed'

backoff_interval(retry_count):
  0 → 1 minute
  1 → 5 minutes
  2 → 30 minutes
```

### scheduler.py — Overlap Prevention Contract

All jobs MUST use:
```python
scheduler.add_job(func, 'interval', 
    minutes=N,
    max_instances=1,
    coalesce=True,
    misfire_grace_time=60,
    id='unique_job_id'
)
```

### webhooks.py — SSRF Prevention Contract

```python
def validate_webhook_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https'):
        return False
    ip = socket.getaddrinfo(parsed.hostname, None)[0][4][0]
    addr = ipaddress.ip_address(ip)
    if addr.is_private or addr.is_loopback or addr.is_reserved or addr.is_link_local:
        return False
    return True
```
Called at webhook creation, update, AND before dispatch.
