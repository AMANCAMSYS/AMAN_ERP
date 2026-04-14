# Research: Authentication & Security Audit

**Feature**: `004-audit-auth-security`  
**Date**: 2026-04-14  
**Status**: Complete

## Research Tasks

### RT-001: Exception Detail Leakage Pattern

**Task**: Research all instances of `HTTPException(detail=str(e))` or raw exception exposure across the codebase.

**Decision**: Replace all `raise HTTPException(detail=str(e))` with generic error messages + structured logging.

**Rationale**: Constitution §IV explicitly forbids exposing raw Python exceptions to clients. The pattern `detail=str(e)` can expose SQL errors, file paths, internal identifiers, and stack traces. The correct pattern is:
```python
except Exception as e:
    logger.exception(f"Operation failed: {context}")
    raise HTTPException(status_code=500, detail="حدث خطأ داخلي")
```

**Alternatives Considered**:
- Custom exception classes with error codes → Overkill for audit fix; adds abstraction without need
- Error mapping dictionary → Useful for known errors but doesn't address the catch-all pattern

**Findings**: 30+ instances found primarily in `routers/purchases.py` (20+) and `routers/services.py` (10+). Additional files may have similar patterns. A grep sweep of all routers is required during implementation.

---

### RT-002: SAML RelayState Security

**Task**: Research SAML RelayState validation best practices for multi-tenant SSO.

**Decision**: Replace URI-based RelayState (`company_id:config_id`) with server-side session state + CSRF token.

**Rationale**: The current implementation passes `company_id` and `sso_config_id` in the SAML RelayState parameter, which is user-controllable. An attacker could forge a RelayState to redirect a SAML assertion to a different company, enabling cross-tenant authentication bypass.

**Best Practice**:
1. Generate a random state token before redirecting to IdP
2. Store the mapping `{state_token → company_id, sso_config_id}` in Redis with short TTL (5 min)
3. Use the state token as the RelayState value
4. On ACS callback, look up the server-side state by the received RelayState token
5. Reject if state token not found or expired

**Alternatives Considered**:
- Signed/encrypted RelayState → Acceptable but more complex; server-side state is simpler and prevents replay
- Cookie-based state → Doesn't work for SAML POST binding where browser context differs

---

### RT-003: Admin Account Hardening

**Task**: Research best practices for system admin authentication in multi-tenant ERP.

**Decision**: Require 2FA for system admin account; add admin-specific rate limiting.

**Rationale**: The system admin account (`ADMIN_PASSWORD_HASH` in config) has full system access. If this hash is compromised, the entire multi-tenant system is compromised. Adding mandatory 2FA provides a second layer of defense.

**Implementation Approach**:
- Store admin 2FA secret in environment variable (`ADMIN_TOTP_SECRET`)
- Require TOTP code during admin login flow
- Add stricter rate limiting for admin login (3 attempts/5 minutes)

**Alternatives Considered**:
- Separate admin database user → Good practice but doesn't address auth flow
- LDAP/SSO for admin → Too complex for current scope; can be future enhancement
- Hardware key (WebAuthn) → Out of scope per spec assumptions

---

### RT-004: Token Invalidation Reliability

**Task**: Research strategies for reliable token invalidation when Redis is unavailable.

**Decision**: Make token invalidation mandatory with database fallback; remove silent try-except.

**Rationale**: Current implementation wraps `invalidate_user_tokens()` in try-except with warning-level logging. If Redis is down during password change, the user's old tokens remain valid. This violates Constitution §IV on session management.

**Implementation Approach**:
1. Remove try-except around `invalidate_user_tokens()` in password change flow
2. Add database-only fallback: if Redis write fails, ensure DB `user_token_invalidation` table is updated
3. In `get_current_user()`, always check DB invalidation timestamp when Redis is unavailable
4. Log at ERROR level (not WARNING) when Redis path fails

**Alternatives Considered**:
- Force logout on Redis failure → Too disruptive; DB fallback is sufficient
- Short token expiry (5 min) → Reduces window but doesn't eliminate it; existing 30-min is standard

---

### RT-005: Audit Logging Reliability

**Task**: Research best practices for mandatory security audit logging.

**Decision**: Remove try-except silencing around security event logging; fail loud for critical security events.

**Rationale**: Current implementation wraps `log_activity()` calls for 2FA changes in try-except with `pass`. This means security-critical events (2FA enable/disable) may go unrecorded without any indication. Constitution §IV requires logging all security events.

**Implementation Approach**:
1. For critical security events (2FA changes, role modifications, permission changes): remove `except: pass` and let audit failures bubble up or retry
2. For non-critical audit events: log at ERROR level instead of silently passing
3. Add a circuit breaker pattern: if audit system is consistently failing, raise an alert but don't block all operations

**Alternatives Considered**:
- Async audit logging queue → Good long-term solution but adds complexity for audit scope
- Separate audit database → Over-engineering; current approach with reliability fixes is sufficient

---

### RT-006: CSP inline-script Hardening

**Task**: Research CSP configuration improvements for the React frontend.

**Decision**: Document the `unsafe-inline` usage as a known limitation; recommend nonce-based CSP as future improvement.

**Rationale**: The current CSP includes `script-src 'self' 'unsafe-inline'` which weakens XSS protection. However, removing `unsafe-inline` requires nonce-based CSP which needs build-time coordination between Vite and the server. This is out of scope for the security audit but should be tracked.

**Alternatives Considered**:
- Hash-based CSP → Requires knowing all inline script hashes at build time; fragile
- Remove all inline scripts → Major React/Vite refactoring; out of scope

---

### RT-007: Password History Validation Gap

**Task**: Research where password history is validated in the change flow.

**Decision**: Ensure password history check runs on both `/change-password` endpoint and admin password reset.

**Rationale**: Current implementation checks password history in `security.py` `/change-password`, but the admin reset flow may bypass this check. Both paths must validate against password history.

**Findings**: Password history with parameterized query (`LIMIT :limit`) is correctly implemented. Needs verification that admin-initiated password resets also check history.

---

### RT-008: Mobile Sync Rate Limiting

**Task**: Research rate limiting requirements for mobile sync endpoints.

**Decision**: Add rate limiting to `/mobile/sync` endpoint (30 requests/minute per user).

**Rationale**: The `/mobile/sync` endpoint accepts large POST payloads for bulk data sync but has no rate limiting. An attacker with valid credentials could perform denial-of-service by flooding sync requests.

**Alternatives Considered**:
- Payload size limiting only → Doesn't prevent rapid small requests
- Queue-based sync → Good architecture but out of audit scope

---

### RT-009: Field-Level Permission Completeness

**Task**: Research gaps in field-level permission restrictions.

**Decision**: Document incomplete field restrictions as a finding; define complete matrix as part of this audit.

**Rationale**: `DEFAULT_FIELD_RESTRICTIONS` in `permissions.py` only defines restrictions for the "salesperson" role. Other roles (cashier, inventory, user) may also need field-level restrictions (e.g., cashier shouldn't see cost prices, HR user shouldn't see salary details of managers).

**Findings**: Current implementation supports the pattern but has incomplete role coverage. The fix is data-driven (adding entries to `DEFAULT_FIELD_RESTRICTIONS`) not code-driven.

---

### RT-010: Cross-Module Permission Audit

**Task**: Research whether all routers enforce `require_permission()`.

**Decision**: Conduct a systematic grep of all router files during implementation to verify every endpoint uses `require_permission()` or `get_current_user` dependency.

**Rationale**: The auth/security module routers are verified. But Constitution §IV requires *every* endpoint to be protected. A full sweep of all 70+ router files is needed to confirm compliance.

**Findings**: Auth-module routers are correctly protected. Public endpoints (login, forgot-password, SSO callbacks) are intentionally unprotected. The cross-module sweep will be a task in implementation.
