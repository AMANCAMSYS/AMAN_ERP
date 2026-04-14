# Research: Audit Core Admin Module

**Date**: 2026-04-14 | **Branch**: `005-audit-core-admin`

---

## R1: Audit Log Retention & Archival Strategy

**Question**: How should 7-year retention with 1-year archival be implemented?

**Current State**:
- `audit_logs` table exists in per-tenant DBs (`aman_{company_id}`)
- `system_activity_log` table exists in `aman_system`
- No archival mechanism exists — zero references to "archive", "cold_storage", or "partition" in codebase
- No retention policy enforcement — logs accumulate indefinitely
- `utils/audit.py` `log_activity()` inserts with parameterized SQL (safe)

**Decision**: Add an `is_archived` boolean column + `archived_at` timestamp to `audit_logs`. A scheduled job (APScheduler) runs daily, marking entries older than 1 year as archived. The `/audit/logs` endpoint filters out archived entries by default; an `include_archived=true` query param exposes them. No physical data movement — just a logical partition. Deletion occurs at 7 years via the same scheduled job.

**Rationale**: Logical archival is simplest; physical table partitioning adds DDL complexity with no benefit at current scale. The `is_archived` column + partial index on `created_at WHERE NOT is_archived` keeps live queries fast.

**Alternatives Considered**:
1. PostgreSQL table partitioning (range on `created_at`) — rejected: requires DDL migration per tenant, complicates backup/restore
2. Separate `audit_logs_archive` table with `INSERT ... SELECT` + `DELETE` — rejected: data movement is risky, adds complexity
3. External cold storage (S3 + Parquet) — rejected: over-engineered for current scale

---

## R2: Notification Retry with Exponential Backoff

**Question**: How should notification retry work?

**Current State**:
- `notification_service.py`: Zero retry logic. On failure, exception is logged and silently skipped
- WebSocket failures suppressed at DEBUG level — invisible in production
- `email_service.py`: Single attempt, no retry, no timeout on SMTP connection
- Synchronous email call in async context (not awaited) — potential event loop blocking

**Decision**: Add retry logic to `notification_service.py` with 3 attempts and exponential backoff (1min → 5min → 30min). Track delivery status per notification with `delivery_status` and `retry_count` columns on the `notifications` table. Failed deliveries are marked `permanently_failed` after 3 attempts. Retry execution via APScheduler job (every 1 minute, checks for pending retries).

**Rationale**: APScheduler-driven retry avoids blocking the request handler. Status tracking enables visibility. Exponential backoff prevents thundering herd on SMTP outages.

**Alternatives Considered**:
1. In-process asyncio.create_task retry loop — rejected: lost on process restart
2. Celery/RQ background queue — rejected: adds infrastructure dependency not in current stack
3. Redis-backed retry queue — rejected: Redis is optional (fallback mode exists)

---

## R3: Dashboard Cache Invalidation

**Question**: How should 60s TTL with event-driven invalidation work?

**Current State**:
- `cache.py`: Hybrid Redis/in-memory cache with TTL support. `invalidate_company_cache(company_id, module)` exists but is never called from financial write endpoints
- `dashboard.py`: Uses `@cached()` decorator with 120s and 180s TTL (spec requires 60s)
- No event-driven invalidation wired — cache expires only via TTL
- `invalidate_cache(pattern)` uses Redis `KEYS` command (O(N) — acceptable at current scale)

**Decision**: 
1. Reduce dashboard cache TTL from 120s/180s → 60s
2. Add `invalidate_company_cache(company_id, "dashboard")` calls to financial write endpoints (invoice create/update, journal entry post, payment record) — these are in other routers (sales, finance) but the invalidation call is a one-liner
3. Keep the existing `@cached` decorator pattern

**Rationale**: Minimal change — just wire existing invalidation API to write paths and adjust TTL. No new infrastructure needed.

**Alternatives Considered**:
1. PostgreSQL LISTEN/NOTIFY for real-time invalidation — rejected: adds complexity, requires persistent connection
2. Redis pub/sub for cache invalidation — rejected: over-engineered for single-process deployment
3. Write-through cache — rejected: changes read path unnecessarily

---

## R4: Scheduler Overlap Prevention

**Question**: How to prevent job overlap?

**Current State**:
- `scheduler.py`: Three jobs registered with APScheduler (`interval` trigger)
- Zero concurrency control: no `coalesce`, no `max_instances`, no locking
- If `check_scheduled_reports()` takes >5min, APScheduler stacks instances
- Creates new DB engines per call — connection pool leak
- MV refresh uses `CONCURRENTLY` (good) but no timeout/heartbeat

**Decision**: Add `max_instances=1` and `coalesce=True` to all APScheduler job configs. Add `misfire_grace_time` to skip missed triggers rather than stacking. Log warning when a job is skipped due to overlap.

**Rationale**: APScheduler has built-in `max_instances` and `coalesce` — no custom locking needed. This is the idiomatic solution.

**Alternatives Considered**:
1. PostgreSQL advisory locks — rejected: APScheduler handles this natively
2. Redis-based distributed lock — rejected: single-process deployment, not needed
3. Custom file-based lock — rejected: fragile, unnecessary

---

## R5: Data Import Partial-Commit Strategy

**Question**: How should partial-commit work for imports?

**Current State**:
- `data_import.py`: Has `skip_errors` parameter. When `True`, skips invalid rows and collects errors. When `False`, aborts on first error
- Single `db.commit()` at end — all valid rows committed together
- Row-level error reporting exists: `"سطر {i + 2}: {str(e)}"` — but leaks exception details
- File validation exists: size limits, extension whitelist, column validation
- SQL identifiers validated via `validate_sql_identifier()`

**Decision**: The partial-commit strategy already exists via `skip_errors=True`. Fixes needed:
1. Sanitize row-level error messages (remove `str(e)`, use typed validation errors)
2. Ensure `skip_errors=True` is the default for bulk imports per spec
3. Add `log_activity()` call on import completion (currently only called for successful imports)

**Rationale**: Existing implementation matches spec intent. Only error sanitization and audit logging gaps need fixing.

**Alternatives Considered**: None — existing implementation is sufficient with minor fixes.

---

## R6: Error Sanitization Across Core Admin Routers

**Question**: How many `detail=str(e)` / `detail=f"...{e}"` leaks remain?

**Current State** (10 routers in scope):

| Router | Error Leaks Found | Details |
|--------|-------------------|---------|
| dashboard.py | 2 | L233 `f"Dashboard calculation error: {str(e)}"`, L699 `f"فشل في حفظ التخطيط: {str(e)}"` |
| data_import.py | 3 | L137, L205 file read errors, L277 row-level `str(e)` |
| companies.py | 1 | L216 `f"Failed to upload: {str(e)}"` |
| external.py | TBD | Webhook/API key endpoints — need verification |
| notifications.py | 1 | L293 or similar `str(e)` in error response |
| system_completion.py | 0 | Already uses generic `"حدث خطأ داخلي"` consistently |
| audit.py | 0 | No error detail leaks |
| branches.py | TBD | Need full verification |
| settings.py | TBD | Need full verification |
| parties.py | 0 | Uses generic error messages |

**Decision**: Replace all `detail=str(e)` and `detail=f"...{e}"` with generic Arabic messages + `logger.exception()`. Each instance is a one-line fix. Total estimate: ~10 instances across the 10 routers.

---

## R7: SSRF Protection for Webhook URLs

**Question**: How to block SSRF in webhook URL registration?

**Current State**:
- `external.py`: Accepts any URL for webhook registration without validation
- `webhooks.py`: Calls `requests.post(url, ...)` without SSRF checks
- HMAC signing exists and works correctly
- Delivery timeout is 10s (acceptable)

**Decision**: Add `validate_webhook_url()` function to `utils/webhooks.py` that:
1. Parses URL with `urllib.parse.urlparse()`
2. Resolves hostname to IP via `socket.getaddrinfo()`
3. Blocks private/reserved ranges: `127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`, `::1`, `fc00::/7`
4. Blocks non-HTTP(S) schemes
5. Called in `external.py` webhook create/update endpoints AND in `webhooks.py` before dispatch

**Rationale**: Defense-in-depth — validate at registration AND dispatch time. DNS rebinding is mitigated by resolving at dispatch time.

**Alternatives Considered**:
1. DNS pinning (resolve once, cache IP) — rejected: doesn't handle DNS rebinding
2. Allowlist-only URLs — rejected: too restrictive for legitimate use
3. Egress proxy — rejected: infrastructure change outside scope

---

## R8: Missing Audit Logging in CRUD Routers

**Question**: Which CRUD routers lack `log_activity()` calls?

**Current State**:

| Router | Has log_activity? | State-Changing Operations |
|--------|-------------------|--------------------------|
| companies.py | ❌ NO | Create, update, upload logo, enable/disable modules |
| branches.py | ❌ NO | Create, update, delete |
| settings.py | ❌ NO | Update settings, bulk update |
| notifications.py | ❌ NO | Mark read, update preferences, send test email |
| data_import.py | ✅ YES (partial) | Import execution logged, but not preview/template |
| external.py | TBD | Webhook/API key CRUD |
| dashboard.py | ❌ NO | Widget layout save (state change) |
| system_completion.py | ✅ YES | Fiscal lock, backup, zakat calc |
| parties.py | ❌ N/A | Read-only (GET only) |
| audit.py | ❌ N/A | Read-only (GET only) |

**Decision**: Add `log_activity()` calls to all state-changing operations in companies.py, branches.py, settings.py, and external.py. Notifications mark-read and dashboard widget saves are low-severity — log at a lower priority.

---

## R9: Scheduler Connection Pool Leak

**Question**: `scheduler.py` creates new engines per call. Is this a leak?

**Current State**:
- `get_system_engine()` and `get_company_engine()` both call `create_engine()` every time
- APScheduler calls these every 5/15/1440 minutes
- Each `create_engine()` creates a new connection pool
- Old engines not disposed — pool_size connections accumulate

**Decision**: Reuse the application's existing `engine` (system) and `get_db_connection()` (per-tenant) from `database.py` instead of creating new engines. The `database.py` module already has LRU-cached engine management.

**Rationale**: Eliminates resource leak entirely by using existing infrastructure.

---

## R10: SQL Injection Patterns (text(f"..."))

**Question**: How many `text(f"...")` patterns exist in scope?

**Current State**:
- `audit.py` router: 5 instances — `where_clause` built safely via parameterized placeholder concatenation (no user input in SQL text, only `:param` placeholders)
- `dashboard.py`: Uses `text(f"...")` but with parameterized values — safe pattern
- `data_import.py`: `text(f"INSERT INTO {config['table']}...")` — `config['table']` comes from hardcoded `IMPORT_CONFIGS` dict, not user input — safe
- `companies.py`: `text(f'DROP DATABASE IF EXISTS "{db_name}"')` — `db_name` validated via `validate_aman_identifier()` — safe but anti-pattern
- `sql_builder.py`: All parameterized with `validate_sql_identifier()` — safe
- `sql_safety.py`: Regex validation + keyword blocking — sufficient

**Decision**: The `text(f"...")` pattern is used throughout the codebase for dynamic WHERE clause construction. These are NOT SQL injection vulnerabilities because:
1. Column/table names come from code constants or validated identifiers
2. User values are always bound via `:param` placeholders
3. `validate_sql_identifier()` blocks SQL keywords in identifiers

No changes needed for SQL injection. The pattern is the project's established SQL-first convention (Constitution VII).

---

## R11: API Key & Webhook Secret Storage

**Question**: Are API keys hashed? Are webhook secrets encrypted?

**Current State**:
- API keys: Hashed with SHA256 before storage (FR-009 ✅). Raw key shown only once on creation
- Webhook secrets: Stored plaintext in DB
- ZATCA private keys: Stored plaintext in `company_settings`

**Decision**: 
1. API key hashing: Already implemented — no change needed
2. Webhook secrets: Encrypt at rest using Fernet (symmetric encryption) with key derived from `SECRET_KEY`. Decrypt only at dispatch time
3. ZATCA private keys: Out of scope for this audit (compliance module, not core admin)

**Rationale**: Fernet is available via `cryptography` package (already in requirements for JWT). Simple encrypt/decrypt with no key management overhead.

---

## R12: WebSocket Security

**Question**: Are WebSocket connections authenticated and tenant-scoped?

**Current State**:
- `notifications.py` WS endpoint: JWT validated from query param or cookie
- Connection accepted BEFORE validation — then closed with custom code if invalid
- `ws_manager.py`: Tenant-scoped via `company_id:user_id` key structure
- No rate limiting on WS connections
- No message size validation
- No token expiry re-check mid-session

**Decision**:
1. Move `ws.accept()` AFTER JWT validation (reject before accept)
2. Add connection limit per user (max 3 concurrent WS connections)
3. Token expiry check is out of scope (would require periodic ping/re-auth — complex)

---

## R13: Branch Deletion Protection

**Question**: Is branch deletion blocked when transactions exist?

**Current State**:
- `branches.py`: Default branch protected (`is_default = TRUE` → blocked)
- No explicit transaction check before delete
- FK constraints may catch it at DB level, but error message is generic
- No audit logging on branch operations

**Decision**: Add explicit check before deletion — query `invoices`, `journal_entries`, `inventory_movements` for `branch_id` reference. Return specific Arabic error message listing what's linked. Add `log_activity()` for all branch CRUD.

---

## R14: Settings Validation

**Question**: Are settings values validated before persistence?

**Current State**:
- `settings.py`: Updates settings without type/range validation
- Permission mapping exists (good) but unclassified settings fall through
- Cache invalidated on update (good)
- SMTP test has hardcoded bypass (`smtp.example.com` returns success)

**Decision**:
1. Add validation map: `{setting_key: {type, min, max, allowed_values}}` for each setting
2. Reject any setting key not in the validation map (block unknown keys)
3. Remove SMTP test hardcoded bypass
4. Add `log_activity()` for settings changes
