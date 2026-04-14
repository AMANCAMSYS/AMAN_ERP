# Tasks: Audit Core Admin Module

**Input**: Design documents from `/specs/005-audit-core-admin/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/api-conformance.md

**Tests**: Not requested — no test tasks included.

**Organization**: Tasks grouped by user story. This is a code-audit module — tasks modify existing files in-place.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Schema additions and shared utility functions needed by all user stories

- [x] T001 Add `is_archived` BOOLEAN DEFAULT FALSE and `archived_at` TIMESTAMPTZ columns to `audit_logs` table via migration in backend/migrations/add_audit_archival_columns.py
- [x] T002 Add partial indexes on `audit_logs`: `idx_audit_logs_live` on `(created_at DESC) WHERE NOT is_archived` and `idx_audit_logs_archival` on `(created_at) WHERE NOT is_archived` via same migration file
- [x] T003 [P] Add `delivery_status` VARCHAR DEFAULT 'pending', `retry_count` INTEGER DEFAULT 0, `last_retry_at` TIMESTAMPTZ, and `delivery_channel` VARCHAR columns to `notifications` table via migration in backend/migrations/add_notification_delivery_columns.py
- [x] T004 [P] Add `validate_webhook_url()` function to backend/utils/webhooks.py — parse URL, resolve hostname via `socket.getaddrinfo()`, block private/reserved IP ranges (127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 169.254.0.0/16, ::1, fc00::/7), block non-HTTP(S) schemes

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Cross-cutting fixes that multiple user stories depend on

**⚠️ CRITICAL**: Error sanitization and log injection fixes MUST be complete before user story work begins — they affect every router

- [x] T005 [P] Add log injection sanitization to backend/utils/logging_config.py — sanitize user-supplied fields in structured JSON log output (strip newlines, null bytes, and control characters from `extra_data` dict values before formatting)
- [x] T006 [P] Add connection limit per user (max 3 concurrent WebSocket connections) to backend/utils/ws_manager.py — track connection count per `company_id:user_id` key, reject with close code 4008 when exceeded

**Checkpoint**: Foundation ready — user story implementation can begin

---

## Phase 3: User Story 1 — Secure Company & Branch Management (Priority: P1) 🎯 MVP

**Goal**: All company and branch CRUD operations enforce tenant isolation, produce audit trails, sanitize errors, and protect branches with dependent transactions from deletion

**Independent Test**: Create two companies, log in as users from each, verify data isolation. CRUD branches and verify audit logs. Attempt to delete a branch with invoices and verify rejection.

### Implementation for User Story 1

- [x] T007 [P] [US1] Sanitize error responses in backend/routers/companies.py — replace `detail=f"Failed to upload: {str(e)}"` (L216) and fix undefined `error_details` variable (L121-122) with generic Arabic message + `logger.exception()`
- [x] T008 [P] [US1] Sanitize error responses in backend/routers/branches.py — scan all `except Exception` blocks and replace any `detail=str(e)` or `detail=f"...{e}"` patterns with `detail="حدث خطأ داخلي"` + `logger.exception()`
- [x] T009 [US1] Add `log_activity()` calls to all state-changing endpoints in backend/routers/companies.py — import `log_activity` from `utils.audit`, call after successful create, update, logo upload, and module enable/disable operations with `resource_type="company"`, include `request` parameter
- [x] T010 [US1] Add `log_activity()` calls to all state-changing endpoints in backend/routers/branches.py — call after successful create, update, and delete operations with `resource_type="branch"`, include `branch_id` and `request` parameters
- [x] T011 [US1] Add transaction existence check before branch deletion in backend/routers/branches.py — before the existing delete logic, query `invoices`, `journal_entries`, and `inventory_movements` for matching `branch_id`; if any count > 0, return HTTP 409 with `detail="لا يمكن حذف الفرع لوجود عمليات مرتبطة به"` (FR-012)

**Checkpoint**: Company and branch CRUD fully hardened with audit trails, error sanitization, and deletion protection

---

## Phase 4: User Story 2 — Settings Persistence & Validation (Priority: P1)

**Goal**: All settings operations validate input types/ranges, reject unknown keys, produce audit trails, and sanitize errors

**Independent Test**: Update each setting category, verify validation catches invalid values, re-read to confirm persistence, check audit log entries.

### Implementation for User Story 2

- [x] T012 [US2] Sanitize error responses in backend/routers/settings.py — scan all `except Exception` blocks and replace any `detail=str(e)` or `detail=f"...{e}"` patterns with generic Arabic message + `logger.exception()`
- [x] T013 [US2] Add `SETTINGS_VALIDATION_MAP` to backend/routers/settings.py — define a dict mapping each known `setting_key` to its expected type (str/int/float/bool/json), allowed range (min/max), and permitted values; reject any key not in the map with HTTP 400 `detail="مفتاح إعدادات غير معروف"` (FR-002)
- [x] T014 [US2] Add value validation logic to the settings update endpoint in backend/routers/settings.py — before persisting, look up the key in `SETTINGS_VALIDATION_MAP`, validate type and range, reject invalid values with HTTP 400 `detail="قيمة غير صالحة للإعداد"`
- [x] T015 [US2] Remove hardcoded SMTP test bypass in backend/routers/settings.py — delete the `if host == "smtp.example.com": return {"success": True}` block that allows fake SMTP configurations to pass validation
- [x] T016 [US2] Add `log_activity()` calls to settings update endpoints in backend/routers/settings.py — import `log_activity` from `utils.audit`, call after successful single and bulk setting updates with `resource_type="settings"`, `action="configure"`, include old→new value in details dict

**Checkpoint**: Settings fully validated, audited, and error-safe

---

## Phase 5: User Story 5 — Audit Trail Completeness (Priority: P1)

**Goal**: Audit log queries support archival filtering, archival job runs on schedule, 7-year retention enforced

**Independent Test**: Insert audit entries with old timestamps, run archival job, verify entries marked archived, query with and without `include_archived` flag.

### Implementation for User Story 5

- [x] T017 [US5] Add `include_archived` query parameter to `/audit/logs` endpoint in backend/routers/audit.py — default `False`; when `False`, add `AND NOT is_archived` to WHERE clause; when `True`, return all entries including archived
- [x] T018 [US5] Add archival scheduler job to backend/services/scheduler.py — new function `archive_old_audit_logs()` that iterates all tenant DBs, marks `audit_logs` entries older than 1 year as `is_archived=TRUE, archived_at=NOW()`, and deletes entries older than 7 years; register with APScheduler as daily interval job with `max_instances=1, coalesce=True`
- [x] T019 [US5] Add notification retry scheduler job to backend/services/scheduler.py — new function `retry_failed_notifications()` that iterates tenant DBs, finds notifications with `delivery_status='failed' AND retry_count < 3` AND `last_retry_at` older than backoff interval (1m/5m/30m based on retry_count), re-attempts delivery, updates status; register with APScheduler as 1-minute interval job with `max_instances=1, coalesce=True`

**Checkpoint**: Audit archival and retention fully operational

---

## Phase 6: User Story 3 — Notification Delivery & Preferences (Priority: P2)

**Goal**: Notifications retry on failure with exponential backoff, delivery status tracked, WebSocket connections validated before accept, errors sanitized

**Independent Test**: Trigger notification with unreachable SMTP, verify 3 retries with correct delays, verify final status is `permanently_failed`. Connect WebSocket with invalid token and verify rejection before accept.

### Implementation for User Story 3

- [x] T020 [US3] Sanitize error responses in backend/routers/notifications.py — replace any `detail=str(e)` patterns with generic Arabic message + `logger.exception()`; fix fire-and-forget `asyncio.ensure_future()` call at L109 to properly await or track the task
- [x] T021 [US3] Add input validation to notification settings update endpoint in backend/routers/notifications.py — validate `smtp_port` is integer, `smtp_host` is non-empty string, etc. before inserting into `company_settings` via raw `text()` query
- [x] T022 [US3] Fix WebSocket authentication order in backend/routers/notifications.py — move `ws.accept()` call AFTER JWT token validation (currently at L252-273, connection is accepted before validation); if token is invalid, close without accepting
- [x] T023 [US3] Add retry logic with exponential backoff to backend/services/notification_service.py — on channel dispatch failure, update notification record with `delivery_status='failed'`, `retry_count+=1`, `last_retry_at=NOW()`; after 3 failures mark `delivery_status='permanently_failed'`; log failures at WARNING level without exposing SMTP credentials
- [x] T024 [US3] Add SMTP connection timeout to backend/services/email_service.py — pass `timeout=30` to `smtplib.SMTP()` and `smtplib.SMTP_SSL()` constructors; classify SMTP errors (timeout/auth/connection) for retry decision

**Checkpoint**: Notification delivery is reliable with retry, tracking, and proper WS auth

---

## Phase 7: User Story 4 — Data Import with Validation (Priority: P2)

**Goal**: Import uses partial-commit by default, error messages sanitized (no `str(e)` leaks), audit trail written for all import operations

**Independent Test**: Import file with mix of valid/invalid rows, verify valid rows committed, invalid rows listed with safe Arabic error descriptions, audit log entry written.

### Implementation for User Story 4

- [x] T025 [P] [US4] Sanitize error responses in backend/routers/data_import.py — replace `detail=f"خطأ في قراءة الملف: {str(e)}"` at L137 and L205, and `detail=f"خطأ في السطر {i + 2}: {str(e)}"` at L277 with generic Arabic messages; log original exceptions via `logger.exception()`
- [x] T026 [US4] Ensure `skip_errors=True` is the default for bulk import execution in backend/routers/data_import.py — verify the import execute endpoint defaults to partial-commit strategy per FR-004; if currently defaulting to `False`, change to `True`

**Checkpoint**: Data import is safe with sanitized errors and partial-commit default

---

## Phase 8: User Story 6 — Dashboard Data Accuracy & Performance (Priority: P2)

**Goal**: Dashboard cache TTL reduced to 60s, event-driven invalidation wired from financial write endpoints, branch filtering maintained, errors sanitized

**Independent Test**: Load dashboard, post a journal entry, reload dashboard within 60s and verify updated figures. Verify branch-scoped user sees only their branches' data.

### Implementation for User Story 6

- [x] T027 [US6] Sanitize error responses in backend/routers/dashboard.py — replace `detail=f"Dashboard calculation error: {str(e)}"` at L233 and `detail=f"فشل في حفظ التخطيط: {str(e)}"` at L699 with generic Arabic `detail="حدث خطأ داخلي"` + `logger.exception()`
- [x] T028 [US6] Reduce dashboard cache TTL in backend/routers/dashboard.py — change `@cached("dashboard_stats", expire=120)` to `expire=60` and `@cached("dashboard_charts_financial", expire=180)` to `expire=60` (FR-019)
- [x] T029 [US6] Wire dashboard cache invalidation from financial write endpoints — add `invalidate_company_cache(company_id, "dashboard")` call (from `utils.cache`) after successful invoice create/update in backend/routers/sales/, journal entry post in backend/routers/finance/, and payment record in relevant payment router

**Checkpoint**: Dashboard shows fresh data within 60s or immediately after financial writes

---

## Phase 9: User Story 7 — Onboarding Wizard & System Completion (Priority: P3)

**Goal**: Verify existing hardening in system_completion.py, ensure no error leaks or missing audit trails

**Independent Test**: Run onboarding wizard for different industry types, verify correct configuration applied, check audit logs for all state changes.

### Implementation for User Story 7

- [x] T030 [US7] Verify and fix error sanitization in backend/routers/system_completion.py — scan all `except Exception` blocks for any `detail=str(e)` or `detail=f"...{e}"` patterns; replace any found with generic Arabic + `logger.exception()`; verify `log_activity()` is called for fiscal lock, backup, and zakat operations (already expected to be in place per research R8)

**Checkpoint**: Onboarding wizard error-safe and fully audited

---

## Phase 10: User Story 8 — Webhook & External Integration Security (Priority: P3)

**Goal**: SSRF protection on webhook URLs, webhook secrets encrypted at rest, API keys verified as hashed, error responses sanitized, audit trails for all CRUD

**Independent Test**: Create webhook with `http://localhost` URL and verify rejection. Create API key and verify hash storage. Trigger webhook and verify HMAC signature.

### Implementation for User Story 8

- [x] T031 [US8] Sanitize error responses in backend/routers/external.py — scan all `except Exception` blocks and replace any `detail=str(e)` or `detail=f"...{e}"` with generic Arabic + `logger.exception()`
- [x] T032 [US8] Wire SSRF validation in backend/routers/external.py — import `validate_webhook_url` from `utils.webhooks`, call it in webhook create and update endpoints before persisting the URL; reject blocked URLs with HTTP 400 `detail="عنوان URL غير مسموح به"` (FR-018)
- [x] T033 [US8] Add SSRF check before dispatch in backend/utils/webhooks.py — call `validate_webhook_url()` before `requests.post()` in the webhook dispatch function as defense-in-depth against DNS rebinding
- [x] T034 [US8] Encrypt webhook secrets at rest in backend/routers/external.py — use Fernet symmetric encryption (key derived from `SECRET_KEY` via `base64.urlsafe_b64encode(hashlib.sha256(SECRET_KEY).digest())`) to encrypt webhook `secret` before INSERT and decrypt before HMAC signing in backend/utils/webhooks.py (FR-009 analog for webhook secrets)
- [x] T035 [US8] Add `log_activity()` calls to all webhook and API key CRUD endpoints in backend/routers/external.py — call after successful create, update, delete, and revoke operations with `resource_type="webhook"` or `resource_type="api_key"`

**Checkpoint**: External integrations secured with SSRF protection, encrypted secrets, and audit trails

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Scheduler hardening, final verification, cross-router wiring

- [x] T036 Harden scheduler job configuration in backend/services/scheduler.py — add `max_instances=1`, `coalesce=True`, and `misfire_grace_time=60` to all existing `scheduler.add_job()` calls (`check_scheduled_reports`, `check_subscription_billing`, `refresh_analytics_materialized_views`) per FR-020
- [x] T037 Fix scheduler connection pool leak in backend/services/scheduler.py — replace `get_system_engine()` and `get_company_engine()` functions that create new engines per call with imports from `database.py` (`engine` for system, `get_db_connection()` for per-tenant); ensure connections are properly closed after use
- [x] T038 [P] Verify error sanitization in backend/routers/parties.py — scan for any `detail=str(e)` or `detail=f"...{e}"` patterns; replace any found with generic Arabic + `logger.exception()`
- [x] T039 Run full error leak scan across all 10 in-scope routers — execute `grep -rn 'detail=str(e)\|detail=f"' backend/routers/{companies,branches,settings,notifications,audit,data_import,dashboard,external,system_completion,parties}.py` and verify zero matches remain
- [x] T040 Run `python -m py_compile` syntax check on all modified files to verify no syntax errors introduced

**Checkpoint**: All user stories hardened, scheduler safe, zero error leaks confirmed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — schema migrations, utility functions
- **Phase 2 (Foundational)**: No dependencies on Phase 1 — independent cross-cutting fixes
- **Phase 3 (US1)**: Depends on Phase 1 (T001-T002 for archival columns used by audit logging)
- **Phase 4 (US2)**: Independent of Phase 3 — can run in parallel
- **Phase 5 (US5)**: Depends on Phase 1 (T001-T003 for schema columns) and Phase 2 (T005 for log sanitization)
- **Phase 6 (US3)**: Depends on Phase 1 (T003 for notification delivery columns)
- **Phase 7 (US4)**: Independent — can run in parallel with other user stories
- **Phase 8 (US6)**: Independent — can run in parallel
- **Phase 9 (US7)**: Independent — can run in parallel
- **Phase 10 (US8)**: Depends on Phase 1 (T004 for `validate_webhook_url()`)
- **Phase 11 (Polish)**: Depends on all user story phases being complete

### User Story Independence

- **US1 (Company/Branch)**: Fully independent
- **US2 (Settings)**: Fully independent
- **US5 (Audit Trail)**: Depends on T001-T003 (schema) but independent of other stories
- **US3 (Notifications)**: Depends on T003 (schema) and T019 (retry job) but independently testable
- **US4 (Data Import)**: Fully independent
- **US6 (Dashboard)**: Fully independent
- **US7 (Onboarding)**: Fully independent
- **US8 (Webhooks/External)**: Depends on T004 (SSRF util) but independently testable

### Parallel Opportunities

Within Phase 1: T001-T002 (sequential — same file), T003 and T004 (parallel — different files)
Within Phase 2: T005 and T006 (parallel — different files)
Within Phase 3: T007 and T008 (parallel — different files); T009-T011 sequential within branches.py
Phase 3, 4, 7, 8 can all run in parallel (independent routers)
Phase 6 (US3) and Phase 7 (US4) can run in parallel

---

## Implementation Strategy

### MVP Scope (Phase 1 + 2 + 3)

Complete Setup → Foundational → User Story 1 (Company/Branch hardening). This delivers:
- Schema ready for archival + notification tracking
- SSRF validation utility available
- Log injection protection in place
- Full company/branch hardening (error sanitization, audit logging, deletion protection)

### Incremental Delivery

1. **Batch 1** (MVP): Phases 1-3 → P1 company/branch hardening
2. **Batch 2**: Phase 4 → P1 settings validation
3. **Batch 3**: Phase 5 → P1 audit trail archival
4. **Batch 4**: Phases 6-8 → P2 notifications, import, dashboard
5. **Batch 5**: Phases 9-10 → P3 onboarding, webhooks
6. **Batch 6**: Phase 11 → Final verification pass

---

## Summary

| Metric | Value |
|--------|-------|
| **Total Tasks** | 40 |
| **User Story 1 (Company/Branch)** | 5 tasks |
| **User Story 2 (Settings)** | 5 tasks |
| **User Story 3 (Notifications)** | 5 tasks |
| **User Story 4 (Data Import)** | 2 tasks |
| **User Story 5 (Audit Trail)** | 3 tasks |
| **User Story 6 (Dashboard)** | 3 tasks |
| **User Story 7 (Onboarding)** | 1 task |
| **User Story 8 (Webhooks/External)** | 5 tasks |
| **Setup** | 4 tasks |
| **Foundational** | 2 tasks |
| **Polish** | 5 tasks |
| **Parallel Opportunities** | 12 tasks marked [P] |
| **Suggested MVP** | Phases 1-3 (T001-T011, 11 tasks) |
