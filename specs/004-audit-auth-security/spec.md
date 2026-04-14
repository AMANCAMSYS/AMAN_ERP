# Feature Specification: Authentication & Security Audit

**Feature Branch**: `004-audit-auth-security`  
**Created**: 2026-04-14  
**Status**: Draft  
**Input**: Comprehensive audit of Authentication and Security module — JWT lifecycle, RBAC enforcement, tenant isolation, rate limiting, SSO integration, password security, session management, CORS, and input sanitization across all backend routers, frontend pages, middleware, and cross-module dependencies.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Secure Login and Token Lifecycle (Priority: P1)

A user opens the AMAN ERP login page, enters valid credentials, and receives a secure JWT access token and refresh token. The system enforces rate limiting to prevent brute-force attacks. When the access token expires, the system transparently refreshes it. On logout, both tokens are fully invalidated and cannot be reused.

**Why this priority**: Authentication is the gateway to the entire system. If login, token creation, refresh, or revocation has any vulnerability, every module in the system is compromised.

**Independent Test**: Can be tested by attempting login with valid/invalid credentials, verifying token contents, testing refresh flow, and confirming logout invalidation.

**Acceptance Scenarios**:

1. **Given** a registered user with valid credentials, **When** they submit login, **Then** the system returns an access token (30-min expiry) and refresh token (7-day expiry) containing user_id, company_id, role, permissions, enabled_modules, allowed_branches, and type.
2. **Given** a user submitting 6 failed login attempts within one minute from the same IP, **When** the 6th attempt is made, **Then** the system blocks further attempts for 15 minutes and returns an appropriate error.
3. **Given** a valid refresh token, **When** the access token expires and the client requests a refresh, **Then** a new access token is issued without requiring re-login.
4. **Given** a logged-in user, **When** they logout, **Then** the access and refresh tokens are blacklisted in the database and cache, and any subsequent request using those tokens is rejected with 401.
5. **Given** a user with 2FA enabled, **When** they submit valid credentials, **Then** the system requires a valid TOTP code before issuing tokens.

---

### User Story 2 - Role-Based Access Control Enforcement (Priority: P1)

Every API endpoint in the system enforces permission checks based on the user's role. A user can only access modules and perform actions explicitly granted by their role's permission set. No endpoint is accessible without authentication and proper authorization.

**Why this priority**: RBAC is the foundational security layer that prevents unauthorized access to sensitive financial, HR, and operational data across all 16 modules.

**Independent Test**: Can be tested by making API requests with different role tokens to every endpoint and verifying 403 responses for unauthorized access.

**Acceptance Scenarios**:

1. **Given** a user with the "cashier" role, **When** they attempt to access an accounting endpoint, **Then** the system returns 403 Forbidden.
2. **Given** a user with the "accountant" role, **When** they attempt to create a journal entry, **Then** the system allows the request.
3. **Given** any API endpoint in the system, **When** a request is made without a valid Authorization header, **Then** the system returns 401 Unauthorized.
4. **Given** a user with branch-restricted access, **When** they request data from a branch not in their allowed_branches list, **Then** the system filters or denies the data.
5. **Given** a superuser, **When** they access any endpoint, **Then** the system grants full access without restriction.

---

### User Story 3 - Tenant Data Isolation (Priority: P1)

Each company's data is completely isolated in its own database (`aman_{company_id}`). No user, regardless of role, can access or modify data belonging to another company. All database operations route through tenant-aware connection management.

**Why this priority**: Multi-tenant isolation is a non-negotiable security boundary. Cross-tenant data leakage is a critical defect with legal and financial consequences.

**Independent Test**: Can be tested by verifying database routing, attempting cross-tenant access, and checking that every query uses the correct tenant connection.

**Acceptance Scenarios**:

1. **Given** a user authenticated for company A, **When** they make any API request, **Then** all database queries execute against `aman_{company_a_id}` and no other database.
2. **Given** a user authenticated for company A, **When** they attempt to manipulate the request to reference company B's data, **Then** the system rejects the request or routes only to the user's own tenant database.
3. **Given** any DDL operation (migrations, table creation), **When** it executes, **Then** `validate_aman_identifier()` is called to prevent SQL injection in schema/database names.
4. **Given** system-level data (user accounts, company registry), **When** it is stored or queried, **Then** it resides only in the `aman_system` database, not in tenant databases.

---

### User Story 4 - SSO Integration Security (Priority: P2)

An organization configures Single Sign-On (SSO) for their AMAN ERP instance. Users can authenticate through their organization's identity provider. The SSO configuration and token exchange are secure and follow industry standards.

**Why this priority**: SSO is an enterprise requirement for larger organizations; however, it is used by fewer tenants than direct login, making it secondary to core auth.

**Independent Test**: Can be tested by configuring SSO, performing the login flow, and verifying token exchange and user provisioning.

**Acceptance Scenarios**:

1. **Given** an admin configuring SSO, **When** they save the SSO provider settings, **Then** the system validates the configuration (metadata URL, client ID/secret) before saving.
2. **Given** a user initiating SSO login, **When** the identity provider returns a valid assertion, **Then** the system creates or maps the user account and issues AMAN JWT tokens.
3. **Given** a user initiating SSO login, **When** the identity provider returns an invalid or expired assertion, **Then** the system rejects the login and logs the security event.

---

### User Story 5 - Security Event Monitoring (Priority: P2)

System administrators can view and monitor security events including failed login attempts, permission violations, token anomalies, and suspicious activity. Events are logged with sufficient detail for forensic analysis without exposing sensitive data.

**Why this priority**: Visibility into security events is essential for threat detection and compliance, but it depends on the core auth and RBAC systems being functional first.

**Independent Test**: Can be tested by triggering various security events (failed logins, unauthorized access) and verifying they appear in the security events log.

**Acceptance Scenarios**:

1. **Given** a failed login attempt, **When** the event occurs, **Then** the system logs the IP address, username attempted, timestamp, and failure reason without logging the password.
2. **Given** a user accessing the Security Events page, **When** they have admin permissions, **Then** they see a filterable, paginated list of all security events.
3. **Given** any security-relevant action (role change, permission modification, 2FA toggle), **When** the action completes, **Then** an audit trail entry is recorded with the acting user, timestamp, and change details.

---

### User Story 6 - Password Security and Session Management (Priority: P2)

Users' passwords are securely hashed and validated. The system enforces password policies, tracks password history, and manages active sessions. Users can view and revoke their active sessions.

**Why this priority**: Password security and session management are critical but rely on the core login flow (P1) being solid first.

**Independent Test**: Can be tested by creating/changing passwords, verifying hash storage, testing password history enforcement, and managing sessions.

**Acceptance Scenarios**:

1. **Given** a user creating or updating a password, **When** the password is saved, **Then** it is stored using a strong cryptographic hash and never in plaintext.
2. **Given** password history tracking is enabled, **When** a user attempts to reuse a recent password, **Then** the system rejects the change.
3. **Given** a user viewing their profile, **When** they check active sessions, **Then** they see a list of active sessions with device/IP information and can revoke any session.
4. **Given** a forgot-password request, **When** the user submits a valid email, **Then** a single-use reset token is generated and rate limited to 3 requests per minute per email.

---

### Edge Cases

- What happens when a JWT token is tampered with or has an invalid signature?
- How does the system behave when Redis (rate limiter backend) is unavailable?
- What happens when a user's role is changed while they have an active session?
- How does the system handle concurrent login from multiple devices?
- What happens when the token refresh endpoint receives an expired refresh token?
- How does the system behave when the tenant database connection pool is exhausted?
- What happens when a user is deleted or deactivated while holding valid tokens?
- How does the system handle time-based attacks on TOTP (clock skew)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST authenticate users via username/password and issue JWT access tokens (30-min expiry) and refresh tokens (7-day expiry).
- **FR-002**: System MUST enforce rate limiting on login endpoint — 5 attempts per minute per IP with 15-minute lockout after threshold.
- **FR-003**: System MUST enforce rate limiting on forgot-password endpoint — 3 attempts per minute per email.
- **FR-004**: System MUST enforce general API rate limiting — 100 requests per minute per user.
- **FR-005**: System MUST support Two-Factor Authentication (TOTP) as an optional security layer.
- **FR-006**: System MUST enforce `require_permission("module.action")` on every router endpoint.
- **FR-007**: System MUST support three permission granularity levels: role-level, field-level, and cost-center/warehouse-level.
- **FR-008**: System MUST enforce branch-level data filtering via `validate_branch_access()` on every endpoint that accepts, stores, or queries by `branch_id`.
- **FR-009**: System MUST route all tenant database operations through `get_db_connection(company_id)` with no cross-tenant data access.
- **FR-010**: System MUST call `validate_aman_identifier()` before any DDL operation to prevent SQL injection in database/schema names.
- **FR-011**: System MUST use parameterized SQL queries exclusively — no string interpolation in SQL is permitted.
- **FR-012**: System MUST store all passwords using strong cryptographic hashing.
- **FR-013**: System MUST track password history and prevent reuse of recent passwords.
- **FR-014**: System MUST support active session listing and revocation.
- **FR-015**: System MUST blacklist tokens on logout in both the database and cache layer.
- **FR-016**: System MUST log all security events (failed logins, permission violations, role changes) with IP, user, and timestamp — without exposing sensitive data (passwords, tokens).
- **FR-017**: System MUST sanitize all error responses — raw exceptions, stack traces, and internal details MUST NOT be exposed to clients.
- **FR-018**: System MUST support SSO integration with secure token exchange and configuration validation.
- **FR-019**: System MUST enforce CORS policies to restrict cross-origin requests to authorized domains.
- **FR-020**: System MUST validate and sanitize all user inputs to prevent injection attacks (SQL injection, XSS).
- **FR-021**: System MUST use AUTOCOMMIT isolation level with a dedicated engine for DDL operations, separate from transactional engines.
- **FR-022**: System MUST enforce a bounded (LRU) engine cache to prevent connection exhaustion under high tenant load.
- **FR-023**: System MUST support API key authentication with configurable rate limits per key.
- **FR-024**: System MUST prevent stale session reuse through concurrent session validation.

### Key Entities

- **User**: Represents a person who can authenticate with the system. Carries identity, credentials, role assignment, branch assignments, and 2FA configuration.
- **Role**: A named set of permissions (e.g., superuser, admin, accountant, cashier). Defines what actions a user can perform and which modules they can access.
- **Permission**: A module.action string (e.g., `sales.create`, `accounting.manage`) that gates access to specific functionality.
- **JWT Token**: A signed credential containing user_id, company_id, role, permissions, enabled_modules, allowed_branches, and type. Has access (30-min) and refresh (7-day) variants.
- **Security Event**: An auditable record of a security-relevant action (login attempt, permission change, token anomaly) with actor, timestamp, IP, and outcome.
- **SSO Configuration**: Provider settings (metadata URL, client ID, secret) enabling federated authentication for a tenant.
- **Session**: An active user connection tracked by device/IP, enabling session listing and revocation.
- **API Key**: A long-lived credential for programmatic access with its own rate limit configuration.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of API endpoints require valid authentication — no unauthenticated access to any protected resource.
- **SC-002**: 100% of API endpoints enforce role-based permission checks — unauthorized access is blocked.
- **SC-003**: Zero cross-tenant data leakage — every database query executes against the authenticated user's tenant database only.
- **SC-004**: Brute-force login attempts are blocked within 5 failed attempts per minute, with a 15-minute lockout period.
- **SC-005**: Users can complete the login flow (including 2FA when enabled) in under 5 seconds under normal conditions.
- **SC-006**: Token refresh occurs transparently without requiring the user to re-enter credentials during an active session.
- **SC-007**: All security events are recorded and viewable by administrators within 1 minute of occurrence.
- **SC-008**: No raw system errors, stack traces, or internal details are exposed in any API error response.
- **SC-009**: All passwords are stored using one-way cryptographic hashing — plaintext passwords are never persisted.
- **SC-010**: Logged-out tokens are fully invalidated within 1 second across all system layers (database and cache).

## Assumptions

- The system uses database-per-tenant isolation (`aman_{company_id}`) and a central `aman_system` database for shared data.
- Redis is available in production for rate limiting and token blacklist caching; in-memory fallback is acceptable for development.
- JWT tokens are stored client-side in localStorage (per constitution — migration to HttpOnly cookies is not in scope).
- The existing 8 default roles cover all necessary permission levels; custom role creation is supported.
- TOTP-based 2FA is the only supported second factor (no SMS, no hardware keys).
- SSO configuration is per-tenant, managed by tenant administrators.
- CSP headers are configured at the reverse proxy level for XSS mitigation.
- The audit covers both backend and frontend code across all files listed in the audit plan scope.
