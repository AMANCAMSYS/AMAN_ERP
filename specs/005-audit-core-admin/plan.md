# Implementation Plan: Audit Core Admin Module

**Branch**: `005-audit-core-admin` | **Date**: 2026-04-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-audit-core-admin/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Comprehensive security and quality audit of the Core Admin module — 10 backend routers (101 endpoints), 3 services, 9 utils, 2 config files, and ~37 frontend pages. The audit enforces constitution compliance (error sanitization, tenant isolation, parameterized SQL, audit trail completeness, branch filtering, SSRF protection) and implements missing features (notification retry with exponential backoff, dashboard cache invalidation, scheduler overlap guard, audit log archival, import partial-commit strategy). This is a code-review + fix module — no new tables or APIs are created, but existing implementations are hardened to meet spec requirements.

## Technical Context

**Language/Version**: Python 3.12 (backend), React 18 / Vite (frontend)
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 (SQL-first via `text()`), APScheduler, Pydantic, openpyxl, ReportLab, i18next, React Router
**Storage**: PostgreSQL 15 (multi-tenant `aman_{company_id}` + system `aman_system`), Redis (rate limiting, cache — partially adopted)
**Testing**: pytest (backend), vitest (frontend)
**Target Platform**: Linux server (Docker), modern browsers
**Project Type**: Web application (multi-tenant ERP)
**Performance Goals**: Dashboard < 3s for 100K transactions, import 10K rows without timeout, notifications < 5s (in-app/WS) / < 30s (email)
**Constraints**: 7-year audit log retention, Arabic-primary UI, ZATCA/GOSI compliance, database-per-tenant isolation
**Scale/Scope**: 101 backend endpoints across 10 routers, ~37 frontend pages, 3 services, 9 utils, 2 config files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Relevant FRs | Status | Notes |
|---|-----------|-------------|--------|-------|
| II | Multi-Tenant Isolation | FR-001, FR-011 | ✅ PASS | Spec requires tenant isolation on every company/branch op and WebSocket scoping |
| IV | Security & Access Control | FR-009, FR-010, FR-016, FR-017, FR-018 | ✅ PASS | Error sanitization, parameterized SQL, SSRF blocking, API key hashing, log injection prevention |
| VII | Simplicity & Maintainability | FR-016 | ✅ PASS | SQL-first pattern maintained; no new ORM abstractions introduced |
| XVII | Observability & Audit Trail | FR-005, FR-014, FR-021 | ✅ PASS | Immutable audit logs, 7-year retention with 1-year archival, queryable with filters |
| XXIV | Data Lifecycle Governance | FR-021 | ✅ PASS | 7-year retention, archival after 1 year, cold-storage partition |
| XXV | Performance & Query Discipline | FR-019, SC-006 | ✅ PASS | 60s cache TTL with event-driven invalidation, 3s dashboard SLA |
| IV.Branch | Branch-Level Data Filtering | FR-006 | ✅ PASS | Dashboard scoped to allowed branches |
| IV.Error | Error Sanitization | FR-010 | ✅ PASS | Generic Arabic messages, no internal details exposed |
| XXIII | Idempotency & Duplicate Prevention | FR-004, FR-013 | ✅ PASS | Import deduplication via partial-commit strategy |

**Gate Result**: ✅ ALL PASS — no violations. Proceeding to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/005-audit-core-admin/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── config.py                          # App configuration (pydantic_settings)
├── database.py                        # DB engines, sessions, tenant routing
├── models/
│   └── domains/
│       └── core.py                    # Core entity barrel (Company, Branch, etc.)
├── routers/
│   ├── companies.py                   # Company CRUD (8 endpoints)
│   ├── branches.py                    # Branch CRUD (4 endpoints)
│   ├── settings.py                    # Settings key-value store (4 endpoints)
│   ├── notifications.py               # Notifications + WS (11 endpoints)
│   ├── audit.py                       # Audit log query (3 endpoints)
│   ├── data_import.py                 # Bulk data import (6 endpoints)
│   ├── system_completion.py           # Onboarding + mixed admin (23 endpoints)
│   ├── external.py                    # Webhooks, API keys, ZATCA, WHT (17 endpoints)
│   ├── parties.py                     # Customer/supplier listing (2 endpoints)
│   └── dashboard.py                   # Dashboard metrics + widgets (23 endpoints)
├── services/
│   ├── notification_service.py        # Multi-channel dispatch
│   ├── email_service.py               # SMTP email sending
│   └── scheduler.py                   # APScheduler report jobs
├── utils/
│   ├── audit.py                       # log_activity() function
│   ├── cache.py                       # In-memory TTL cache
│   ├── email.py                       # Email helpers
│   ├── exports.py                     # PDF/Excel generation
│   ├── logging_config.py              # Structured logging setup
│   ├── webhooks.py                    # HMAC-signed webhook dispatch
│   ├── ws_manager.py                  # WebSocket connection manager
│   ├── sql_builder.py                 # Safe parameterized query builder
│   └── sql_safety.py                  # SQL identifier validation
└── tests/

frontend/
├── src/
│   ├── pages/
│   │   ├── Dashboard.jsx
│   │   ├── NotFound.jsx
│   │   ├── Admin/
│   │   │   ├── CompanyList.jsx
│   │   │   ├── AuditLogs.jsx
│   │   │   └── BackupManagement.jsx
│   │   ├── DataImport/
│   │   │   └── DataImportPage.jsx
│   │   ├── Setup/
│   │   │   ├── OnboardingWizard.jsx
│   │   │   ├── IndustrySetup.jsx
│   │   │   └── ModuleCustomization.jsx
│   │   └── Settings/
│   │       ├── CompanySettings.jsx
│   │       ├── CompanyProfile.jsx
│   │       ├── Branches.jsx
│   │       ├── CostingPolicy.jsx
│   │       ├── PrintTemplates.jsx
│   │       ├── Webhooks.jsx
│   │       ├── ApiKeys.jsx
│   │       ├── NotificationPreferences.jsx
│   │       └── tabs/                  # 23 settings tab components
│   ├── services/                      # API client modules
│   ├── hooks/
│   └── context/
└── tests/
```

**Structure Decision**: Existing web application layout (backend + frontend). This audit modifies files in-place — no structural changes. All work is hardening and fixing existing code.

## Complexity Tracking

> No constitution violations — table not applicable.

## Constitution Check (Post-Design)

*Re-evaluation after Phase 0 research and Phase 1 design decisions.*

| # | Principle | Status | Post-Design Notes |
|---|-----------|--------|-------------------|
| II | Multi-Tenant Isolation | ✅ PASS | All design decisions maintain `get_db_connection(company_id)` routing. Scheduler reuses `database.py` engines (R9) |
| IV | Security & Access Control | ✅ PASS | SSRF protection added (R7), webhook secrets encrypted (R11), error sanitization enforced (R6), WS auth fixed (R12) |
| IV.Branch | Branch-Level Filtering | ✅ PASS | Dashboard branch filtering maintained, audit logs branch-scoped via `validate_branch_access()` |
| IV.Error | Error Sanitization | ✅ PASS | All `detail=str(e)` / `detail=f"...{e}"` replaced with generic Arabic messages across 10 routers |
| VII | Simplicity & Maintainability | ✅ PASS | SQL-first pattern maintained. Reuse existing `cache.py` invalidation API. APScheduler native `max_instances=1` — no custom locking |
| XVII | Observability & Audit Trail | ✅ PASS | `log_activity()` added to companies.py, branches.py, settings.py, external.py. Archival via `is_archived` column |
| XXIV | Data Lifecycle Governance | ✅ PASS | 7-year retention + 1-year archival via scheduler job. `is_archived` logical partition with partial indexes |
| XXV | Performance & Query Discipline | ✅ PASS | Dashboard cache 60s TTL + event-driven invalidation. Partial indexes for live audit queries |

**Post-Design Gate Result**: ✅ ALL PASS — no violations.

---

## Phase 0 Output

**Generated**: [research.md](research.md) — 14 research decisions covering:
- R1: Audit log archival (logical partition via `is_archived` column)
- R2: Notification retry (APScheduler-driven, 3 attempts, exponential backoff)
- R3: Dashboard cache (60s TTL, event-driven invalidation via existing `invalidate_company_cache()`)
- R4: Scheduler overlap (APScheduler `max_instances=1` + `coalesce=True`)
- R5: Import partial-commit (existing `skip_errors` flag — minor fixes only)
- R6: Error sanitization (~10 instances across 10 routers)
- R7: SSRF protection (`validate_webhook_url()` with IP range blocking)
- R8: Missing audit logging (companies, branches, settings, external)
- R9: Scheduler connection pool leak (reuse `database.py` engines)
- R10: SQL injection analysis (safe — parameterized throughout)
- R11: API key/webhook secret storage (keys hashed ✅, secrets need Fernet encryption)
- R12: WebSocket security (accept-after-validate, connection limit)
- R13: Branch deletion protection (explicit transaction check)
- R14: Settings validation (type/range validation map, reject unknown keys)

## Phase 1 Output

**Generated artifacts**:
- [data-model.md](data-model.md) — 9 existing entities documented, 2 schema additions (audit_logs archival columns, notifications delivery tracking columns)
- [contracts/api-conformance.md](contracts/api-conformance.md) — 4 cross-cutting contracts (CC-1 error, CC-2 tenant, CC-3 audit trail, CC-4 branch access) + per-router conformance tables for all 10 routers + service/utility contracts
- [quickstart.md](quickstart.md) — Setup, run, test, and verify instructions

---

## Implementation Scope Summary

### By Category

| Category | Files | Key Changes |
|----------|-------|-------------|
| Error Sanitization | 6 routers | Replace ~10 `detail=str(e)` / `detail=f"...{e}"` with generic Arabic + `logger.exception()` |
| Audit Logging | 4 routers | Add `log_activity()` to companies, branches, settings, external CRUD |
| SSRF Protection | 2 files | Add `validate_webhook_url()` to webhooks.py, wire in external.py |
| Notification Retry | 2 files | Add retry logic + delivery tracking to notification_service.py, schema columns to notifications table |
| Dashboard Cache | 1 file + wiring | Reduce TTL to 60s, wire `invalidate_company_cache()` in financial write endpoints |
| Scheduler Hardening | 1 file | Add `max_instances=1`, `coalesce=True`, reuse DB engines |
| Audit Archival | 2 files | Add `is_archived` columns + scheduler archival job + query filter |
| Branch Delete Guard | 1 file | Add transaction existence check before branch deletion |
| Settings Validation | 1 file | Add validation map, reject unknown keys, remove SMTP fake bypass |
| WebSocket Auth | 1 file | Move accept after validate, add connection limit |
| Webhook Secret Encryption | 2 files | Fernet encrypt/decrypt webhook secrets |
| Log Injection Prevention | 1 file | Sanitize user input in structured log output |

### File Impact (24 backend files)

| File | Changes |
|------|---------|
| `routers/companies.py` | Error sanitization, add `log_activity()`, fix undefined `error_details` |
| `routers/branches.py` | Error sanitization, add `log_activity()`, transaction check on delete |
| `routers/settings.py` | Error sanitization, add `log_activity()`, validation map, reject unknown keys, remove SMTP fake |
| `routers/notifications.py` | Error sanitization, validate settings input, fix fire-and-forget |
| `routers/audit.py` | Add `include_archived` filter, archival-aware queries |
| `routers/data_import.py` | Error sanitization (3 instances), default `skip_errors=True` |
| `routers/dashboard.py` | Error sanitization (2 instances), cache TTL 120→60, 180→60 |
| `routers/external.py` | Error sanitization, SSRF validation on webhook URLs, webhook secret encryption, add `log_activity()` |
| `routers/system_completion.py` | Verify existing hardening (minimal changes expected) |
| `routers/parties.py` | Verify existing hardening (minimal changes expected) |
| `services/notification_service.py` | Add retry logic with exponential backoff, delivery status tracking |
| `services/email_service.py` | Add SMTP timeout, improve error classification |
| `services/scheduler.py` | Add `max_instances=1`, `coalesce=True`, reuse DB engines, add archival + retry jobs |
| `utils/audit.py` | No changes (already correct) |
| `utils/cache.py` | No changes (already has invalidation API) |
| `utils/webhooks.py` | Add `validate_webhook_url()` SSRF check, call before dispatch |
| `utils/ws_manager.py` | Add connection limit per user |
| `utils/logging_config.py` | Add log injection sanitization |
| `utils/sql_builder.py` | No changes (already safe) |
| `utils/sql_safety.py` | No changes (already sufficient) |
| `utils/email.py` | No changes |
| `utils/exports.py` | No changes (already safe) |
| `config.py` | No changes |
| `database.py` | No changes |
