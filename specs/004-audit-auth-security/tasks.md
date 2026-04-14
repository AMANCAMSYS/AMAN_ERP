# Tasks: Authentication & Security Audit

**Input**: Design documents from `/specs/004-audit-auth-security/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Not explicitly requested in the feature specification. Test tasks are omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Phase 1: Setup

**Purpose**: Audit preparation — verify scope, establish baseline, confirm tooling

- [x] T001 Verify all audit-scope files exist and record line counts per `backend/routers/auth.py`, `backend/routers/security.py`, `backend/routers/sso.py`, `backend/routers/roles.py`, `backend/routers/mobile.py`, `backend/utils/permissions.py`, `backend/utils/security_middleware.py`, `backend/utils/limiter.py`, `backend/utils/sql_safety.py`, `backend/config.py`, `backend/database.py`, `backend/services/sso_service.py`
- [x] T002 [P] Run baseline grep sweep and record all current violations: `grep -rn "detail=str(e)" backend/routers/ --include="*.py"` and `grep -rn "traceback.print_exc" backend/ --include="*.py"` saving results to `specs/004-audit-auth-security/baseline-violations.txt`
- [x] T003 [P] Run existing auth/security tests to establish baseline pass/fail: `cd backend && pytest tests/ -k "auth or security or login or permission" -v`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Fix critical cross-cutting violations that affect ALL user stories. These MUST complete before story-level work.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Sweep all router files under `backend/routers/` and replace every `raise HTTPException(detail=str(e))` with `logger.exception()` + generic Arabic error message `"حدث خطأ داخلي"` — start with `backend/routers/purchases.py` (20+ instances)
- [x] T005 [P] Replace all `raise HTTPException(detail=str(e))` in `backend/routers/services.py` (10+ instances) with `logger.exception()` + generic Arabic error message
- [x] T006 Sweep remaining router files under `backend/routers/` for any additional `detail=str(e)` or `detail=f"...{e}"` patterns and fix each to use generic messages with structured logging
- [x] T007 [P] Replace all `traceback.print_exc()` calls in `backend/routers/auth.py` and any other backend files with `logger.exception()` calls
- [x] T008 [P] Verify no `print()` statements exist in production code under `backend/routers/`, `backend/utils/`, `backend/services/` — remove or replace with `logger.debug()` if found
- [x] T009 Run full grep verification confirming zero `detail=str(e)`, zero `traceback.print_exc()`, zero `print()` in production code

**Checkpoint**: All error sanitization violations (Constitution §IV) resolved. All stories can now proceed.

---

## Phase 3: User Story 1 — Secure Login and Token Lifecycle (Priority: P1) 🎯 MVP

**Goal**: Verify and harden JWT login, refresh, logout, 2FA challenge, rate limiting, and token blacklisting in `backend/routers/auth.py`

**Independent Test**: Attempt login with valid/invalid credentials, verify token contents match contract (user_id, company_id, role, permissions, enabled_modules, allowed_branches, type), test refresh flow, confirm logout invalidation via blacklist check

### Implementation for User Story 1

- [x] T010 [US1] Audit `backend/routers/auth.py` login endpoint: verify JWT payload contains all required claims (user_id, company_id, role, permissions, enabled_modules, allowed_branches, type), access token 30-min expiry, refresh token 7-day expiry per contract
- [x] T011 [US1] Audit `backend/routers/auth.py` rate limiting: verify `check_rate_limit()` enforces 5 attempts/min per IP with 15-minute lockout; verify `record_failed_attempt()` and `clear_failed_attempts()` work correctly with Redis + in-memory fallback
- [x] T012 [US1] Audit `backend/routers/auth.py` token refresh: verify refresh endpoint checks blacklist, validates `token_use == "refresh"`, re-verifies user is active in DB, and issues new access token
- [x] T013 [US1] Audit `backend/routers/auth.py` logout: verify both access and refresh tokens are SHA-256 hashed and added to `token_blacklist` in DB AND Redis cache; verify `user_sessions` record is deactivated
- [x] T014 [US1] Audit `backend/routers/auth.py` 2FA challenge flow: verify that when `two_factor_enabled=true`, login returns `requires_2fa: true` with temp token and does NOT issue full JWT until TOTP verified
- [x] T015 [US1] Audit `backend/routers/auth.py` `get_current_user()`: verify it decodes JWT, checks blacklist (Redis first, DB fallback), checks user `is_active` status, and rejects expired/tampered tokens with 401
- [x] T016 [US1] Audit `backend/routers/auth.py` forgot-password and reset-password: verify rate limit (3/min per email), single-use token, response does NOT reveal whether email exists, and reset token is invalidated after use
- [x] T017 [US1] Fix `backend/routers/auth.py` admin login to require TOTP when `ADMIN_TOTP_SECRET` env var is set; add stricter rate limit (3 attempts/5 minutes) for admin account per research RT-003

**Checkpoint**: Login, refresh, logout, 2FA, and rate limiting fully audited and hardened

---

## Phase 4: User Story 2 — Role-Based Access Control Enforcement (Priority: P1)

**Goal**: Verify every API endpoint enforces authentication and permission checks; complete field-level permission matrix

**Independent Test**: Make requests with different role tokens to endpoints across all modules; verify 403 for unauthorized access, 401 for missing auth

### Implementation for User Story 2

- [x] T018 [US2] Audit `backend/utils/permissions.py` `require_permission()`: verify wildcard (`*`), section wildcard (`module.*`), alias expansion, and exact match logic are correct
- [x] T019 [US2] Audit `backend/utils/permissions.py` `require_sensitive_permission()`: verify it re-validates user `is_active` from DB for sensitive operations (accounting.manage, treasury.edit, sales.delete, hr.payroll, admin.*, settings.manage)
- [x] T020 [US2] Audit `backend/utils/permissions.py` `validate_branch_access()`: verify admin/superuser bypass, empty `allowed_branches` handling, and warehouse-to-branch resolution
- [x] T021 [US2] Sweep all router files under `backend/routers/` and verify every `@router.get/post/put/delete` endpoint uses `Depends(get_current_user)` or `Depends(require_permission(...))` — document any unprotected endpoints (excluding intentionally public ones: login, forgot-password, reset-password, SSO callbacks)
- [x] T022 [P] [US2] Audit `backend/routers/roles.py`: verify all CRUD endpoints require `admin.roles` permission, verify `AVAILABLE_PERMISSIONS` registry is complete for all 16 modules, verify default role initialization includes all 12 default roles
- [x] T023 [US2] Expand `DEFAULT_FIELD_RESTRICTIONS` in `backend/utils/permissions.py` to cover additional roles: add `cashier` (hide cost_price, profit_margin, supplier info), `inventory` (hide financial fields), `user` (hide all cost and financial data) per research RT-009
- [x] T024 [US2] Audit `backend/routers/roles.py` for missing audit trail logging on role create/update/delete — add `log_activity()` calls for all privilege-escalating actions if missing

**Checkpoint**: Every endpoint verified as protected; field-level permissions complete for all roles

---

## Phase 5: User Story 3 — Tenant Data Isolation (Priority: P1)

**Goal**: Verify database-per-tenant isolation, engine cache LRU, DDL safety, and no cross-tenant data leakage

**Independent Test**: Verify `get_db_connection()` routes to correct tenant DB; verify `validate_aman_identifier()` blocks injection; verify engine cache bounded at 50

### Implementation for User Story 3

- [x] T025 [US3] Audit `backend/database.py`: verify `_engines` OrderedDict LRU with `_MAX_ENGINES = 50`, verify `pool_pre_ping=True`, `pool_recycle=3600`, `pool_size=5`, `max_overflow=10` per constitution
- [x] T026 [US3] Audit `backend/database.py`: verify DDL engine uses `isolation_level="AUTOCOMMIT"` and is separate from transactional engines per FR-021
- [x] T027 [US3] Audit `backend/database.py` `create_company_database()`: verify `validate_aman_identifier()` is called on db_name and db_user BEFORE any DDL execution
- [x] T028 [P] [US3] Audit `backend/utils/sql_safety.py`: verify `validate_aman_identifier()` pattern `^[a-z0-9_]+$` blocks SQL injection in identifiers and SQL keywords
- [x] T029 [US3] Sweep all router files under `backend/routers/` to verify every database access uses parameterized queries (`:param` syntax) and no string interpolation/f-string in SQL — grep for `f"SELECT|f"INSERT|f"UPDATE|f"DELETE|f"CREATE` patterns
- [x] T030 [US3] Verify `backend/routers/auth.py` login flow routes to correct tenant DB using `system_user_index` lookup and `company_engine = create_engine(conn_url)` with proper pool settings

**Checkpoint**: Tenant isolation verified — zero cross-tenant data leakage risk

---

## Phase 6: User Story 4 — SSO Integration Security (Priority: P2)

**Goal**: Fix SAML RelayState cross-tenant vulnerability; verify SSO config validation and SAML signature checking

**Independent Test**: Configure SSO, perform SAML login, verify server-side state prevents RelayState forgery

### Implementation for User Story 4

- [x] T031 [US4] Fix `backend/routers/sso.py` SAML RelayState: replace URI-based `company_id:config_id` with server-side Redis state token (random UUID → {company_id, sso_config_id} mapping with 5-min TTL) per research RT-002
- [x] T032 [US4] Fix `backend/routers/sso.py` `saml_acs()` callback: look up server-side state by received RelayState token, reject if not found or expired, then extract company_id and config_id from server state
- [x] T033 [US4] Audit `backend/services/sso_service.py` `saml_process_acs()`: verify SAML response signature is validated against IdP X.509 certificate and response timestamp is checked for freshness (prevent replay)
- [x] T034 [US4] Audit `backend/routers/sso.py` SSO config CRUD: verify all config endpoints require `auth.sso_manage` permission, verify config validation (metadata URL, entity ID, certificate) runs before save
- [x] T035 [US4] Audit `backend/routers/sso.py` auto-provisioning in `provision_or_update_user()`: verify group-to-role mapping is applied, verify user creation uses parameterized queries, verify security event is logged for new SSO user creation
- [x] T036 [US4] Audit `backend/routers/sso.py` LDAP test endpoint: verify LDAP bind password is not logged and not returned in response; verify connection uses TLS where configured

**Checkpoint**: SAML RelayState vulnerability fixed; SSO integration fully audited

---

## Phase 7: User Story 5 — Security Event Monitoring (Priority: P2)

**Goal**: Make audit logging reliable; verify security events page correctness

**Independent Test**: Trigger failed login, permission violation, 2FA change — verify all appear in security events log

### Implementation for User Story 5

- [x] T037 [US5] Fix `backend/routers/security.py` audit logging: remove `try: log_activity(...) except: pass` pattern around 2FA setup/verify/disable — replace with mandatory logging that raises or retries on failure per research RT-005
- [x] T038 [US5] Audit `backend/routers/auth.py` security event logging: verify failed login attempts log IP, username, timestamp, failure reason WITHOUT logging password or token values
- [x] T039 [US5] Audit `backend/routers/security.py` `/events` endpoint: verify it requires `security.view` permission, supports pagination (default 25, max 100), filtering by event_type/user_id/date_range, and returns proper response per contracts
- [x] T040 [US5] Audit `backend/utils/audit.py`: verify `log_activity()` function uses parameterized queries, does not expose sensitive data in event details, and handles DB connection errors gracefully with logging (not silent pass)
- [x] T041 [P] [US5] Audit `backend/routers/roles.py` for audit trail: verify role create/update/delete operations generate security events via `log_activity()` — add calls if missing

**Checkpoint**: All security events reliably logged and queryable by administrators

---

## Phase 8: User Story 6 — Password Security and Session Management (Priority: P2)

**Goal**: Harden password change flows, fix token invalidation reliability, verify session management

**Independent Test**: Change password, verify old tokens invalidated; view/revoke sessions; test password history enforcement

### Implementation for User Story 6

- [x] T042 [US6] Fix `backend/routers/security.py` token invalidation after password change: remove `try-except` wrapper around `invalidate_user_tokens()` — make it mandatory with DB fallback if Redis fails per research RT-004
- [x] T043 [US6] Audit `backend/routers/security.py` `/change-password`: verify it validates current password, checks new password against company policy (min length, complexity), checks password history (`password_history` table with `LIMIT :limit`), and stores bcrypt hash
- [x] T044 [US6] Verify password history is also checked during admin-initiated password reset (if such endpoint exists in `backend/routers/auth.py` or `backend/routers/security.py`) per research RT-007
- [x] T045 [US6] Audit `backend/routers/security.py` session endpoints: verify `/sessions` GET returns only current user's sessions with IP/user_agent/timestamps, verify `/sessions/{id}` DELETE only allows revoking own sessions (unless admin), verify `/sessions` DELETE (all) invalidates all tokens
- [x] T046 [US6] Audit `backend/routers/security.py` password policy validation: verify policy settings have Pydantic validation preventing invalid values (e.g., `min_length < 1`, `max_age_days < 0`) before persisting to `company_settings`
- [x] T047 [US6] Audit `backend/routers/security.py` password expiry: verify `check_password_expiry()` returns correct `days_remaining`, `warning` flag (7-day threshold), and `is_expired` status

**Checkpoint**: Password security and session management fully audited and hardened

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final verification, frontend audit, mobile rate limiting, and cross-module sweep

- [x] T048 [P] Add rate limiting to `backend/routers/mobile.py` sync endpoint: `@limiter.limit("30/minute")` on `/sync` POST per research RT-008
- [x] T049 [P] Audit `backend/utils/security_middleware.py`: verify HTTPS redirect works (not localhost), verify security headers (X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, CSP) are complete; document `unsafe-inline` as known limitation per research RT-006
- [x] T050 [P] Audit `backend/config.py`: verify `SECRET_KEY` validation (min 32 chars, min 8 unique chars), verify CORS origins configuration, verify `TRUSTED_PROXIES` CIDR validation
- [x] T051 [P] Audit frontend token handling in `frontend/src/utils/api.js`: verify Axios interceptor attaches `Authorization: Bearer <token>` to every request, verify 401 response triggers transparent token refresh, verify logout clears localStorage
- [x] T052 [P] Audit frontend login page `frontend/src/pages/Login.jsx`: verify credential submission uses HTTPS, verify no sensitive data stored beyond localStorage token, verify rate limit error messages displayed correctly
- [x] T053 [P] Audit frontend SSO pages `frontend/src/pages/SSO/SsoConfigList.jsx` and `frontend/src/pages/SSO/SsoConfigForm.jsx`: verify SSO config forms validate inputs client-side, verify sensitive fields (client_secret, bind_password) use password input type
- [x] T054 [P] Audit frontend security pages `frontend/src/pages/Admin/SecurityEvents.jsx` and `frontend/src/pages/Settings/tabs/SecuritySettings.jsx`: verify pagination, filtering, and data display match API contracts
- [x] T055 [P] Audit frontend session management in `frontend/src/pages/UserProfile.jsx`: verify active session list displays correctly, verify session revocation calls correct API endpoint
- [x] T056 Run full quickstart.md validation: execute all grep checks from quickstart.md, verify zero violations remain, re-run existing auth/security tests and confirm all pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — Login/token lifecycle
- **US2 (Phase 4)**: Depends on Phase 2 — Can run in PARALLEL with US1
- **US3 (Phase 5)**: Depends on Phase 2 — Can run in PARALLEL with US1, US2
- **US4 (Phase 6)**: Depends on Phase 2 — Can run in PARALLEL with US1, US2, US3
- **US5 (Phase 7)**: Depends on Phase 2 — Can run in PARALLEL with other stories
- **US6 (Phase 8)**: Depends on Phase 2 — Can run in PARALLEL with other stories
- **Polish (Phase 9)**: Depends on ALL user story phases being complete

### User Story Dependencies

- **US1 (P1)**: Independent after Phase 2 — no cross-story dependencies
- **US2 (P1)**: Independent after Phase 2 — may validate findings from US1 but no code dependency
- **US3 (P1)**: Independent after Phase 2 — no cross-story dependencies
- **US4 (P2)**: Independent after Phase 2 — no cross-story dependencies
- **US5 (P2)**: Independent after Phase 2 — may reference audit logging patterns from US1/US6
- **US6 (P2)**: Independent after Phase 2 — no cross-story dependencies

### Within Each User Story

- Audit existing code before making fixes
- Fix critical vulnerabilities before minor improvements
- Verify fix with grep/test after each change

### Parallel Opportunities

- T002, T003 can run in parallel (baseline sweep)
- T004 + T005 can run in parallel (different router files)
- T007, T008 can run in parallel (different file searches)
- US1, US2, US3, US4, US5, US6 all can run in parallel after Phase 2
- T022, T028, T029 involve sweeps of all routers (do T028 and T029 first, then T022 can verify)
- All Phase 9 tasks marked [P] can run in parallel

---

## Parallel Example: After Phase 2

```text
# All P1 stories can launch in parallel:
US1: T010-T017 (auth.py audit + admin MFA fix)
US2: T018-T024 (permissions audit + field restrictions)
US3: T025-T030 (tenant isolation audit)

# All P2 stories can also launch in parallel with P1:
US4: T031-T036 (SSO/SAML fix)
US5: T037-T041 (audit logging fix)
US6: T042-T047 (password/session fix)
```

---

## Implementation Strategy

### MVP First (Phase 2 + User Story 1 Only)

1. Complete Phase 1: Setup (baseline)
2. Complete Phase 2: Error sanitization (CRITICAL — blocks everything)
3. Complete Phase 3: US1 — Login/token lifecycle audit
4. **STOP and VALIDATE**: Verify login flow is fully hardened
5. All other stories add incremental security improvements

### Incremental Delivery

1. Setup + Foundational → 30+ error leaks fixed (immediate security win)
2. Add US1 → Login, token, 2FA, rate limiting hardened
3. Add US2 → RBAC fully verified across all 767 endpoints
4. Add US3 → Tenant isolation confirmed
5. Add US4 → SAML RelayState vulnerability fixed
6. Add US5 → Audit logging made reliable
7. Add US6 → Password and session management hardened
8. Polish → Frontend verified, mobile rate-limited, final sweep

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (Phase 1-2)
2. Once Phase 2 is done:
   - Developer A: US1 + US6 (auth.py + security.py — related files)
   - Developer B: US2 + US3 (permissions + database — infrastructure)
   - Developer C: US4 + US5 (SSO + audit logging — related concerns)
3. All reconvene for Phase 9 (Polish)
