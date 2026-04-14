# Implementation Plan: Authentication & Security Audit

**Branch**: `004-audit-auth-security` | **Date**: 2026-04-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-audit-auth-security/spec.md`

## Summary

Comprehensive audit of the Authentication & Security module covering JWT lifecycle, RBAC enforcement, tenant isolation, rate limiting, SSO integration, password security, session management, CORS, and input sanitization. The audit spans backend routers (auth, security, sso, roles, mobile), middleware, utilities, database connection management, and all associated frontend pages. Existing implementation is architecturally sound (7.5/10) but requires tactical fixes in error sanitization (30+ `detail=str(e)` leaks), SAML RelayState validation, admin MFA enforcement, audit logging reliability, and token invalidation error handling.

## Technical Context

**Language/Version**: Python 3.12 (backend), React 18 / Vite (frontend)
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0, python-jose (JWT), passlib (bcrypt), pyotp (TOTP), slowapi (rate limiting), Redis, Starlette middleware
**Storage**: PostgreSQL 15 (multi-tenant `aman_{company_id}` + `aman_system`), Redis (rate limiting, token blacklist cache)
**Testing**: pytest
**Target Platform**: Linux server (Docker)
**Project Type**: web-service (multi-tenant ERP)
**Performance Goals**: 100 req/min per user, login < 5 seconds, token invalidation < 1 second
**Constraints**: Zero cross-tenant data leakage, ZATCA/GOSI compliance, 50 max engine cache (LRU)
**Scale/Scope**: 767 API endpoints, 277 frontend pages, 244 tables per tenant, 150+ permissions

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Financial Precision | ✅ PASS | Not directly affected — audit scope is auth/security |
| II. Multi-Tenant Isolation | ✅ PASS | Engine cache LRU (50), `validate_aman_identifier()` on DDL, `get_db_connection()` routing verified |
| III. Double-Entry Integrity | ✅ PASS | Not directly affected |
| IV. Security & Access Control | ⚠️ VIOLATIONS | 30+ `HTTPException(detail=str(e))` patterns; admin no MFA; SAML RelayState; audit logging silent failures; token invalidation try/except |
| V. Regulatory Compliance | ✅ PASS | Not directly affected |
| VI. Concurrency Safety | ✅ PASS | Not directly affected |
| VII. Simplicity & Maintainability | ✅ PASS | SQL-first pattern followed; no `print()` in production routers |

**Gate Result**: Principle IV has violations requiring fixes. Audit proceeds to remediate.

## Project Structure

### Documentation (this feature)

```text
specs/004-audit-auth-security/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (audit scope)

```text
backend/
├── config.py                        # JWT settings, CORS, SECRET_KEY validation
├── database.py                      # Tenant engine cache (LRU), DDL engine, connection pooling
├── routers/
│   ├── auth.py                      # Login, logout, refresh, 2FA login, password reset
│   ├── security.py                  # 2FA setup/disable, password change, sessions, events
│   ├── sso.py                       # SSO/SAML/LDAP config and login
│   ├── roles.py                     # Role CRUD, permission registry (150+ perms)
│   └── mobile.py                    # Mobile sync endpoints
├── services/
│   ├── sso_service.py               # SAML processing, LDAP auth, user provisioning
│   └── notification_service.py      # Security event notifications
├── utils/
│   ├── permissions.py               # require_permission(), validate_branch_access()
│   ├── security_middleware.py        # HTTPS redirect, security headers, XSS/SQLi detection
│   ├── limiter.py                   # slowapi rate limiter (Redis + in-memory fallback)
│   ├── sql_safety.py                # validate_aman_identifier()
│   └── audit.py                     # Audit trail logging
├── models/
│   └── domains/security_reporting.py # Security models
└── middleware/                       # Empty (middleware in utils/)

frontend/src/
├── pages/
│   ├── Login.jsx
│   ├── Register.jsx
│   ├── ForgotPassword.jsx
│   ├── ResetPassword.jsx
│   ├── UserProfile.jsx
│   ├── SSO/SsoConfigList.jsx
│   ├── SSO/SsoConfigForm.jsx
│   ├── Admin/RoleManagement.jsx
│   ├── Admin/SecurityEvents.jsx
│   └── Settings/tabs/SecuritySettings.jsx
└── utils/
    └── api.js                        # Axios interceptor, token refresh
```

**Structure Decision**: Existing web application structure (backend + frontend). No new directories needed — this is an audit with in-place fixes.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | No new abstractions introduced — audit fixes existing code in-place |

## Constitution Re-Check (Post-Design)

| Principle | Pre-Design | Post-Design | Resolution |
|-----------|-----------|-------------|------------|
| IV. Security & Access Control | ⚠️ VIOLATIONS | ✅ ADDRESSED | Research RT-001 through RT-010 define fixes for all violations: error sanitization, SAML state, admin MFA, audit logging, token invalidation |
| II. Multi-Tenant Isolation | ✅ PASS | ✅ PASS | Engine cache LRU verified; DDL validation verified; no design changes affect isolation |
| VII. Simplicity & Maintainability | ✅ PASS | ✅ PASS | No new abstractions; all fixes are in-place modifications to existing patterns |

**Post-Design Gate**: ✅ PASS — All violations have defined remediation paths in research.md. No new violations introduced by the design.
