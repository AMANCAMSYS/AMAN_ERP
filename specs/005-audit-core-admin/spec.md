# Feature Specification: Audit Core Admin Module

**Feature Branch**: `005-audit-core-admin`  
**Created**: 2026-04-14  
**Status**: Draft  
**Input**: User description: "Comprehensive audit of the Core Admin module: company/branch management, settings, notifications, data import, onboarding, audit logs, dashboard, and all cross-module tracing"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Secure Company & Branch Management (Priority: P1)

A system administrator creates, edits, and deletes companies and branches. Every operation enforces tenant isolation — a user from Company A must never access or modify data belonging to Company B. Branch operations correctly scope data to the owning company. All CRUD operations produce accurate audit trails and return user-facing error messages that never leak internal details.

**Why this priority**: Companies and branches are the foundational entities of the multi-tenant system. Any defect here compromises every downstream module.

**Independent Test**: Can be tested by creating two companies, logging in as users from each, and verifying complete data isolation. Branch CRUD can be tested within a single company and verified against audit logs.

**Acceptance Scenarios**:

1. **Given** a system admin is logged in, **When** they create a new company, **Then** a tenant database is provisioned, initial settings are populated, and an audit entry is recorded.
2. **Given** a company admin, **When** they attempt to access another company's branches, **Then** the system returns 403/404 without revealing that the other company exists.
3. **Given** a company admin, **When** they create, update, or delete a branch, **Then** the change is persisted under the correct tenant, associated accounts/settings are updated, and an audit log is written.
4. **Given** any error during company/branch creation, **When** the error is returned, **Then** the response contains a generic user-facing message (Arabic) and no stack traces, SQL fragments, or internal paths.
5. **Given** a branch with active transactions, **When** an admin tries to delete it, **Then** the system prevents deletion with a clear explanation of dependent data.

---

### User Story 2 - Settings Persistence & Validation (Priority: P1)

A company admin configures system settings (general, financial, accounting mappings, sales, purchases, inventory, invoicing, HR, POS, CRM, projects, expenses, reporting, notifications, workflows, branding, integrations, audit, performance, compliance, branches). Each setting is validated before storage, persisted to the correct tenant database, and reflected immediately in subsequent operations. Invalid values are rejected with descriptive Arabic error messages.

**Why this priority**: Settings drive the behaviour of every other module (decimal places, currencies, fiscal year, cost method, tax settings, etc.). Incorrect settings silently corrupt financial data.

**Independent Test**: Can be tested by changing each setting category, verifying the value is persisted, re-reading it, and confirming dependent module behaviour changes accordingly.

**Acceptance Scenarios**:

1. **Given** a company admin, **When** they update a setting, **Then** the new value is validated, persisted, and immediately returned on subsequent reads.
2. **Given** an invalid setting value (e.g., negative decimal places, unsupported currency code), **When** submitted, **Then** the system rejects it with a specific validation error and does not modify the stored value.
3. **Given** a setting that affects other modules (e.g., decimal_places), **When** updated, **Then** all dependent calculations in other modules reflect the new value on the next request.
4. **Given** concurrent setting updates from two admins, **When** both submit, **Then** the system handles the conflict without data corruption (last writer wins or optimistic lock).

---

### User Story 3 - Notification Delivery & Preferences (Priority: P2)

Users receive notifications through multiple channels (in-app, WebSocket, email). Each user can configure their notification preferences per event type. The system delivers notifications reliably, retries on transient failures, and never exposes internal error details in notification content. WebSocket connections are authenticated and tenant-isolated.

**Why this priority**: Notifications are the primary channel for approval workflows, security alerts, and business events. Unreliable notifications block business processes.

**Independent Test**: Can be tested by triggering each notification event type, verifying delivery through each channel, and confirming preference-based suppression works correctly.

**Acceptance Scenarios**:

1. **Given** a triggering event (e.g., approval request), **When** the notification is generated, **Then** it is delivered through all enabled channels for the target user.
2. **Given** a user who disabled email notifications, **When** an event triggers, **Then** only in-app and WebSocket notifications are sent.
3. **Given** an email delivery failure, **When** the send fails, **Then** the system retries up to 3 times with exponential backoff (delays of 1 minute, 5 minutes, then 30 minutes); after the third failure the notification is marked as permanently failed and the failure event is logged without leaking SMTP credentials or configuration.
4. **Given** a WebSocket connection, **When** a user connects, **Then** the connection is authenticated via token and scoped to the user's company only.

---

### User Story 4 - Data Import with Validation (Priority: P2)

Users import data (products, parties, employees, accounts, opening balances) from Excel/CSV files. The system validates every row, reports detailed per-row errors in Arabic, and uses a partial-commit (best-effort) strategy — valid rows are committed and invalid rows are listed with per-row error details. The entire batch is rolled back only on a critical system failure (database unreachable, file corruption, or out-of-memory). Large files are processed without timeouts.

**Why this priority**: Data import is used during onboarding and ongoing data entry. Faulty imports silently corrupt master data.

**Independent Test**: Can be tested by importing files with valid rows, invalid rows, duplicate keys, and oversized files — verifying correct handling of each case.

**Acceptance Scenarios**:

1. **Given** a valid Excel file with products, **When** imported, **Then** all rows are persisted to the correct tenant database with an audit trail.
2. **Given** a file with some invalid rows (missing required fields, invalid references), **When** imported, **Then** valid rows are committed to the database and each invalid row is listed with its row number and error description; the import job summary reports both success and failure counts.
3. **Given** a critical system failure mid-import (e.g., database connection lost), **When** the failure occurs, **Then** the entire in-progress batch is rolled back and the import job is marked as failed.
4. **Given** a file containing duplicate unique keys (e.g., product codes), **When** imported, **Then** duplicate rows are reported as errors without corrupting existing data; non-duplicate rows are committed normally.
5. **Given** a file larger than expected (10,000+ rows), **When** imported, **Then** the system processes it without HTTP timeout or memory exhaustion.
5. **Given** any import operation, **When** an internal error occurs, **Then** the error response contains a generic Arabic message and the full trace is logged server-side only.

---

### User Story 5 - Audit Trail Completeness (Priority: P1)

Every state-changing operation across the system writes an audit log entry containing who (user_id, username), what (action, resource_type, resource_id), when (timestamp), where (IP, branch), and details (changed fields/values). Audit logs are queryable by admin users with filters for date range, user, action type, and resource. Logs are immutable — no update or delete operations are exposed.

**Why this priority**: Audit trails are a compliance requirement and the foundation for security forensics. Gaps make the entire audit framework unreliable.

**Independent Test**: Can be tested by performing CRUD operations across multiple modules and querying audit logs to verify completeness, accuracy, and immutability.

**Acceptance Scenarios**:

1. **Given** any create/update/delete operation in any module, **When** the operation completes, **Then** an audit log entry exists with correct user, action, resource, and detail information.
2. **Given** an admin user, **When** they query audit logs with filters, **Then** results are correctly filtered and paginated, scoped to their company only.
3. **Given** the audit logs API, **When** a user attempts to modify or delete log entries, **Then** the system rejects the request (no PUT/DELETE endpoints exist for audit logs).
4. **Given** a `log_activity()` call that fails (e.g., database error), **When** the main operation has already committed, **Then** the audit failure is logged to the application log but does not roll back the user's operation.

---

### User Story 6 - Dashboard Data Accuracy & Performance (Priority: P2)

The main dashboard displays aggregated financial and operational metrics (revenue, expenses, receivables, payables, open orders, inventory value). All figures are computed from live data, scoped to the user's company and allowed branches. The dashboard loads within acceptable time limits even with large datasets.

**Why this priority**: The dashboard is the first screen users see. Inaccurate figures erode trust; slow loads waste time.

**Independent Test**: Can be tested by comparing dashboard figures against direct SQL queries on the same data, and measuring load time with representative data volumes.

**Acceptance Scenarios**:

1. **Given** a logged-in user, **When** they open the dashboard, **Then** all displayed metrics match the underlying data for their company and branches.
2. **Given** a user with branch restrictions, **When** they view the dashboard, **Then** metrics reflect only their allowed branches.
3. **Given** a company with 100,000+ transactions, **When** the dashboard loads, **Then** the response completes within 3 seconds.
4. **Given** stale cached dashboard data, **When** a new financial transaction is posted (invoice, journal entry, or payment), **Then** the dashboard cache for that company is immediately invalidated so the next load reflects the updated figures; in the absence of writes, cached data expires after 60 seconds.

---

### User Story 7 - Onboarding Wizard & System Completion (Priority: P3)

New companies go through an onboarding wizard that sets up the industry type, chart of accounts, default settings, initial branches, and module configuration. The system tracks completion percentage and guides users through remaining setup steps. The process is idempotent — re-running a step does not corrupt previously configured data.

**Why this priority**: Onboarding quality determines first impressions and data correctness. However, it runs only once per company, so defects affect fewer operations than ongoing features.

**Independent Test**: Can be tested by running the wizard for different industry types and verifying the resulting configuration matches expectations.

**Acceptance Scenarios**:

1. **Given** a newly created company, **When** the admin starts onboarding, **Then** the wizard presents industry-specific setup steps in logical order.
2. **Given** an industry selection (e.g., retail), **When** the admin confirms, **Then** the correct chart of accounts template, default settings, and module configuration are applied.
3. **Given** a partially completed wizard, **When** the admin returns later, **Then** the wizard resumes from the last incomplete step without losing prior progress.
4. **Given** a completed step, **When** re-executed, **Then** the system applies changes idempotently without creating duplicate records.

---

### User Story 8 - Webhook & External Integration Security (Priority: P3)

Admins configure webhooks and external integrations (API keys). Webhook payloads are signed with HMAC for authenticity verification. API keys are hashed before storage and never returned in plaintext after creation. External endpoint calls enforce timeouts and do not leak internal data in request headers or error responses.

**Why this priority**: Webhooks and API keys are attack surfaces. Misconfigured webhooks can leak sensitive business data to arbitrary external URLs.

**Independent Test**: Can be tested by configuring a webhook, triggering an event, and verifying the payload is signed, the receiving endpoint can validate the signature, and API keys are irretrievable after creation.

**Acceptance Scenarios**:

1. **Given** a configured webhook, **When** a matching event fires, **Then** the payload is delivered to the external URL with an HMAC signature header.
2. **Given** a webhook delivery failure, **When** the external endpoint is unreachable, **Then** the system retries with exponential backoff and logs failures without leaking the endpoint URL or payload content.
3. **Given** an API key creation request, **When** the key is generated, **Then** the plaintext key is returned only once and stored as a hash.
4. **Given** an API key listing request, **When** keys are retrieved, **Then** only masked/truncated key identifiers are shown — never the full key.

---

### Edge Cases

- What happens when a company's tenant database is unreachable during settings read/write?
- How does the system handle concurrent onboarding wizard submissions from two admin sessions?
- What happens when a webhook target URL redirects to an internal/private IP address (SSRF)?
- How does data import handle files with mixed encodings (UTF-8, Windows-1256)?
- What happens when notification delivery is attempted for a deactivated user?
- How does the dashboard handle a company with zero transactions (empty state)?
- What happens when the scheduler triggers a job while the previous run is still executing? The new run is skipped and a warning is logged; running late is safer than double-posting.
- How does the audit log handle extremely large detail payloads (> 64KB)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST enforce tenant isolation on every company and branch operation — no cross-tenant data access.
- **FR-002**: System MUST validate all settings values against their expected types, ranges, and permitted values before persisting.
- **FR-003**: System MUST deliver notifications through in-app, WebSocket, and email channels based on per-user preferences. On transient delivery failure, the system MUST retry up to 3 times with exponential backoff (1 min → 5 min → 30 min) before marking the delivery as permanently failed.
- **FR-004**: System MUST use a partial-commit (best-effort) strategy for data import — valid rows are committed and invalid rows are reported with per-row error details; the entire batch is rolled back only on a critical system failure (database unreachable, file corruption, out-of-memory).
- **FR-005**: System MUST write an immutable audit log entry for every state-changing operation, including user identity, action, resource, timestamp, IP address, and branch.
- **FR-006**: System MUST display dashboard metrics scoped to the user's company and allowed branches, computed from current data.
- **FR-007**: System MUST track onboarding completion percentage and allow resumption from the last incomplete step.
- **FR-008**: System MUST sign webhook payloads with HMAC and enforce delivery timeouts.
- **FR-009**: System MUST hash API keys before storage and never return plaintext keys after initial creation.
- **FR-010**: System MUST return generic Arabic error messages in all error responses — no internal details, stack traces, SQL fragments, or file paths.
- **FR-011**: System MUST authenticate WebSocket connections and scope them to the authenticated user's company.
- **FR-012**: System MUST prevent deletion of branches that have dependent transactions (invoices, journal entries, inventory movements).
- **FR-013**: System MUST validate data import files for size limits, format correctness, and encoding before processing rows.
- **FR-014**: System MUST provide audit log querying with filters (date range, user, action, resource type) and pagination, scoped to the tenant. Live query results cover the most recent 1 year; entries older than 1 year are in cold-archive status and returned only when explicitly requested with an archive flag.
- **FR-021**: System MUST retain audit log entries for a minimum of 7 years. Entries older than 1 year MUST be marked as archived and may be stored in a separate cold-storage partition.
- **FR-015**: System MUST apply industry-specific templates (chart of accounts, default settings, module configuration) during onboarding.
- **FR-016**: System MUST use parameterized queries for all SQL operations — no string concatenation with user input.
- **FR-017**: System MUST sanitize all log output to prevent log injection attacks.
- **FR-018**: System MUST validate webhook target URLs against SSRF (block private/internal IP ranges).
- **FR-019**: System MUST cache dashboard metrics with a 60-second TTL and MUST invalidate the cache immediately on any write to financial data (invoices, journal entries, payments) for the affected company — stale data MUST NOT be served after a write event.
- **FR-020**: System MUST prevent overlapping executions of the same scheduled job — if a job is still running when the next trigger fires, the new run MUST be skipped and a warning logged. Double-execution of financial jobs (reports, notification batches) is never acceptable.

### Key Entities

- **Company**: Represents a tenant. Key attributes: company code, name, industry type, database name, subscription status.
- **Branch**: Organizational unit within a company. Key attributes: branch code, name, type, address, default currency, is_default flag.
- **Setting**: Key-value configuration pair scoped to a company. Key attributes: setting key, setting value, category.
- **Notification**: Message delivered to a user. Key attributes: recipient, channel, event type, content, delivery status, timestamps.
- **Notification Preference**: Per-user, per-event-type channel enablement. Key attributes: user, event type, email enabled, in-app enabled, push enabled.
- **Audit Log**: Immutable record of a state-changing operation. Key attributes: user_id, username, action, resource_type, resource_id, details (JSON), IP address, branch_id, timestamp, is_archived (bool). Entries transition to archived status after 1 year and are retained for a minimum of 7 years.
- **Data Import Job**: Record of a bulk import operation. Key attributes: file name, entity type, total rows, success count, error count, status, error details.
- **Webhook**: External endpoint subscription. Key attributes: target URL, event types, HMAC secret, is_active, retry policy.
- **API Key**: External access credential. Key attributes: key hash, label, permissions, created_at, last_used_at, is_active.
- **Dashboard Metric**: Aggregated figure computed from transactional data. Key attributes: metric name, value, period, branch scope.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All company and branch CRUD operations enforce tenant isolation — zero cross-tenant data leaks detected during testing.
- **SC-002**: 100% of settings categories validate input before persisting — no invalid values can be stored.
- **SC-003**: Notifications are delivered to the correct channels within 5 seconds of the triggering event for in-app/WebSocket and within 30 seconds for email.
- **SC-004**: Data import processes 10,000 rows without timeout and reports per-row errors accurately with row-level success and failure counts.
- **SC-005**: Every state-changing endpoint writes a complete, accurate audit log entry — zero gaps across all tested operations. Audit logs are retained for a minimum of 7 years; entries older than 1 year are archived and queryable via the archive flag.
- **SC-006**: Dashboard loads within 3 seconds for companies with up to 100,000 transactions.
- **SC-007**: Onboarding wizard correctly configures all industry-specific settings and chart of accounts for all supported industry types.
- **SC-008**: Zero internal error details (stack traces, SQL, file paths) are exposed in any API error response.
- **SC-009**: Webhook payloads are correctly HMAC-signed and signature verification succeeds at the receiving end.
- **SC-010**: API keys are never retrievable in plaintext after creation — only hashed values exist in storage.
- **SC-011**: All SQL queries use parameterized statements — zero string-concatenation SQL injection vectors detected.
- **SC-012**: Webhook target URLs are validated against SSRF — private IP ranges are blocked.
- **SC-013**: Dashboard cache expires within 60 seconds; any financial write (invoice, journal entry, payment) triggers immediate cache invalidation — no stale figures are served after a write event.

## Clarifications

### Session 2026-04-14

- Q: How long should audit logs be retained, and is there an archival policy? → A: 7-year retention; entries older than 1 year are archived to cold storage and excluded from live query results by default.
- Q: When importing a file with mixed valid and invalid rows, are valid rows committed or is the entire batch rejected? → A: Partial commit (best-effort) — valid rows are committed immediately; invalid rows are reported with per-row error details. The entire batch is rolled back only on a critical system failure (database unreachable, file corruption, out-of-memory).
- Q: What is the notification retry policy on transient failures? → A: 3 attempts with exponential backoff (1-minute delay, then 5-minute, then 30-minute); after the third failure the delivery is marked as permanently failed and the failure is logged.
- Q: What is the dashboard cache TTL, and does a write to financial data trigger early invalidation? → A: 60-second TTL; any write to financial data (invoices, journal entries, payments) triggers immediate cache invalidation for the affected company so the next dashboard load reflects current figures.
- Q: When a scheduled job is still running and the scheduler triggers the same job again, what happens? → A: The new run is skipped and a warning is logged ("Skipping job X: previous run still active"). Running late is preferable to double-posting, especially for financial jobs.

## Assumptions

- The existing `audit-auth-security` module (Speckit 1) has been completed and its fixes are in place (error sanitization, JWT lifecycle, tenant isolation in auth, rate limiting).
- Arabic is the primary language for all user-facing messages; English is used only in internal logs and developer-facing documentation.
- The system uses PostgreSQL with database-per-tenant isolation (`aman_{company_id}` pattern) and a shared `aman_system` database.
- Redis is available for caching, WebSocket pub/sub, and rate limiting, with graceful fallback to in-memory alternatives when Redis is unavailable.
- Email delivery uses SMTP; the SMTP server is configured externally and not audited as part of this module.
- The scheduler uses APScheduler and is expected to run as a singleton within the FastAPI process (not distributed across multiple workers).
- Audit log retention is 7 years minimum, with archival to cold storage after 1 year; archived entries are excluded from default query results but remain queryable.
- File uploads for data import are limited to Excel (.xlsx) and CSV formats, with a maximum file size governed by server configuration.
- The frontend uses React 18 with Vite and i18next for internationalization; component-level audit focuses on state management, API integration, and error handling rather than visual design.
