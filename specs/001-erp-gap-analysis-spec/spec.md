# Feature Specification: AMAN ERP Gap Closure — Missing & Partial Features

**Feature Branch**: `001-erp-gap-analysis-spec`  
**Created**: 2026-04-02  
**Status**: Draft  
**Input**: User description: "Identify all missing or partial features from the Feature Comparison Matrix and Gap Analysis in ERP_COMPLETE_REPORT.md. For each missing feature: explain the gap, create implementation plan, break into phases, identify dependencies, highlight risks, estimate effort, assign priority."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Architecture Hardening (Priority: P1)

As a system administrator, I need the ERP platform to have safe schema migrations, consistent financial balances, enforced double-entry integrity, centralized journal posting, and secure token storage so that the system is enterprise-ready and audit-proof.

**Why this priority**: Without these foundational fixes, every feature built on top inherits architectural debt — data drift, duplicated GL logic, and security vulnerabilities block enterprise adoption.

**Independent Test**: Deploy a schema change through the migration system, verify balances reconcile across all four sources, confirm journal entries reject unbalanced debits/credits at the database level, and validate that auth tokens are not accessible via client-side scripts.

**Acceptance Scenarios**:

1. **Given** a new table or column change, **When** a migration is run, **Then** the schema updates atomically with rollback capability and zero data loss.
2. **Given** journal entry lines with unequal debits and credits, **When** the entry is saved, **Then** the database rejects it before commit.
3. **Given** 15+ modules that currently post GL entries independently, **When** any module creates a journal entry, **Then** it routes through a single centralized service.
4. **Given** a logged-in user session, **When** inspecting browser storage and scripts, **Then** no auth tokens are accessible to client-side code.
5. **Given** a balance inquiry, **When** comparing calculated vs. stored balances, **Then** they match within a scheduled reconciliation window.

---

### User Story 2 — Enterprise Authentication & Access (Priority: P1)

As an IT administrator at a mid-sized enterprise, I need SSO/LDAP integration so employees can use their corporate credentials to log in, meeting our security policy requirements.

**Why this priority**: SSO/LDAP is a deal-breaker for enterprise sales; without it, organizations with centralized identity management cannot adopt AMAN.

**Independent Test**: Configure an LDAP directory, attempt login with corporate credentials, and verify user provisioning and role mapping.

**Acceptance Scenarios**:

1. **Given** an LDAP directory with employee accounts, **When** a user logs in with their corporate credentials, **Then** they are authenticated and assigned appropriate roles.
2. **Given** SSO is configured, **When** a user accesses AMAN from their corporate portal, **Then** they are seamlessly authenticated without a separate login.
3. **Given** an employee is deactivated in the corporate directory, **When** they attempt to access AMAN, **Then** access is denied.
4. **Given** the identity provider is unreachable, **When** a regular user attempts login, **Then** access is denied with a message indicating IdP unavailability. **When** a designated admin attempts login, **Then** they can authenticate using local credentials.

---

### User Story 3 — Workflow Engine (Priority: P2)

As a department manager, I need configurable multi-step approval workflows so that purchase orders, expense claims, and leave requests follow our company's approval chain without manual coordination.

**Why this priority**: Every major competitor offers configurable workflows. Without this, AMAN cannot automate business processes beyond basic single-step approvals.

**Independent Test**: Create a 3-step approval workflow for purchase orders, submit a PO, verify it routes through each approver in sequence, and confirm it proceeds or rejects correctly.

**Acceptance Scenarios**:

1. **Given** a workflow with 3 approval steps, **When** a purchase order is submitted, **Then** it routes to the first approver and proceeds step-by-step.
2. **Given** a conditional rule (e.g., amount > 50,000 SAR), **When** a PO exceeds that threshold, **Then** an additional approval step is triggered.
3. **Given** an approver rejects a request, **When** the rejection is submitted, **Then** the requester is notified with the reason and can revise and resubmit.

---

### User Story 4 — 3-Way Matching (Priority: P2)

As a procurement officer, I need the system to automatically match purchase orders, goods receipt notes, and supplier invoices so that discrepancies are flagged before payment is authorized.

**Why this priority**: 3-way matching is a standard procurement compliance control present in all major ERPs. Its absence creates financial risk and audit findings.

**Independent Test**: Create a PO, receive goods partially, submit a supplier invoice, and verify the system flags quantity and price discrepancies.

**Acceptance Scenarios**:

1. **Given** a PO for 100 units, a GRN for 80 units, and an invoice for 100 units, **When** matching is performed, **Then** a quantity discrepancy of 20 units is flagged.
2. **Given** all three documents match within tolerance, **When** matching is performed, **Then** the invoice is approved for payment automatically.
3. **Given** a price variance exceeding the configured tolerance, **When** matching is performed, **Then** the invoice is held for review.

---

### User Story 5 — Intercompany Accounting (Priority: P2)

As a group CFO overseeing multiple legal entities, I need intercompany transactions to post reciprocal entries automatically and generate elimination entries for consolidation.

**Why this priority**: Multi-entity enterprises cannot use AMAN without intercompany accounting. This is a core requirement for any organization with subsidiaries.

**Independent Test**: Create an intercompany sale between Entity A and Entity B, verify reciprocal journal entries are created in both, and confirm elimination entries appear in consolidation.

**Acceptance Scenarios**:

1. **Given** Entity A sells goods to Entity B, **When** the transaction is posted, **Then** both entities have matching reciprocal journal entries.
2. **Given** outstanding intercompany balances at period-end, **When** consolidation is run, **Then** intercompany balances are eliminated and the consolidated balance sheet is correct.

---

### User Story 6 — ZATCA Phase 2 E-Invoicing (Priority: P2)

As an accountant in a Saudi business, I need full ZATCA Phase 2 clearance integration so that invoices are submitted to ZATCA in real-time, cryptographically signed, and compliance is maintained.

**Why this priority**: ZATCA Phase 2 is a regulatory mandate in Saudi Arabia. Non-compliance means the business cannot legally issue invoices.

**Independent Test**: Generate an invoice, verify it is submitted to ZATCA's clearance portal, receives a signed response, and the QR code is embedded.

**Acceptance Scenarios**:

1. **Given** a new sales invoice, **When** it is finalized, **Then** it is submitted to ZATCA's clearance API and a signed XML is returned.
2. **Given** ZATCA rejects an invoice, **When** the rejection response is received, **Then** the user sees the specific rejection reason and can correct and resubmit.
3. **Given** a cleared invoice, **When** the PDF is generated, **Then** it includes the ZATCA-compliant QR code with the cryptographic stamp.

---

### User Story 7 — Mobile App (Priority: P2)

As a field sales representative, I need a mobile app to view inventory, create quotations, and submit orders while visiting customer sites, even with intermittent connectivity.

**Why this priority**: Every major competitor offers mobile access. Field teams without mobile cannot use AMAN, limiting its applicability for distributed workforces.

**Independent Test**: Log in on a mobile device, create a quotation, lose connectivity, continue working, and verify data syncs when connectivity returns.

**Acceptance Scenarios**:

1. **Given** a mobile device with network access, **When** the user opens the app, **Then** they can view inventory, customers, pending orders, and pending workflow approvals.
2. **Given** intermittent connectivity, **When** the user creates a quotation offline, **Then** it syncs to the server when connectivity is restored without data loss.
3. **Given** a pending approval notification, **When** a manager opens the mobile app, **Then** they can review the document details and approve or reject with a comment.

---

### User Story 8 — FIFO/LIFO Costing & Demand Forecasting (Priority: P3)

As a warehouse manager, I need FIFO and LIFO costing methods and demand forecasting so I can choose the costing method appropriate for my industry and plan procurement based on predicted demand.

**Why this priority**: WAC-only costing excludes industries requiring FIFO/LIFO (e.g., food, pharma). Demand forecasting is a differentiator for supply chain optimization.

**Independent Test**: Configure FIFO for a product category, perform purchases and sales, verify COGS is calculated using FIFO. Run demand forecast and verify projections are generated.

**Acceptance Scenarios**:

1. **Given** FIFO is selected for a product, **When** units are sold, **Then** COGS is calculated from the earliest purchase cost.
2. **Given** 12 months of sales history, **When** demand forecast is run, **Then** projected quantities for the next 3 months are generated with confidence intervals.

---

### User Story 9 — Employee Self-Service & Performance Reviews (Priority: P3)

As an employee, I need a self-service portal to submit leave requests, view payslips, and update my profile without contacting HR. As a manager, I need to conduct structured performance reviews.

**Why this priority**: Self-service reduces HR administrative burden. Performance reviews are standard in talent management.

**Independent Test**: Log in as employee, submit a leave request, view payslip, update profile. Log in as manager, create a review cycle, complete a review.

**Acceptance Scenarios**:

1. **Given** an employee, **When** they access self-service, **Then** they can view payslips, submit leave requests, and update personal details.
2. **Given** a review cycle, **When** a manager initiates a review, **Then** the employee receives a notification and can submit a self-assessment.

---

### User Story 10 — Subscription Billing, Campaign Management & Advanced Features (Priority: P3)

As a business with recurring revenue, I need subscription billing for automated recurring invoicing. As a marketing manager, I need campaign management for customer outreach tracking.

**Why this priority**: These features target specific market segments (SaaS, marketing-heavy businesses) and differentiate AMAN from Sage X3.

**Independent Test**: Create a subscription plan, enroll a customer, verify recurring invoices are generated on schedule. Create a campaign, send it, and track engagement.

**Acceptance Scenarios**:

1. **Given** a customer enrolled in a monthly plan, **When** the billing date arrives, **Then** an invoice is automatically generated and sent.
2. **Given** a campaign is sent to 100 contacts, **When** the campaign completes, **Then** open/click/response metrics are available.

---

### Edge Cases

- What happens when a migration fails mid-execution? System must rollback to the previous schema state automatically.
- What happens when ZATCA's clearance API is unavailable? Invoices must be queued and retried with exponential backoff; users are informed of pending status.
- What happens when an intercompany entity has a different fiscal year? The system must handle cross-period postings with appropriate accruals.
- What happens when a workflow approver is on leave? Delegation rules must route to the designated backup approver.
- What happens when offline mobile data conflicts with server data? Conflict resolution must present both versions to the user for manual resolution.
- What happens when 3-way matching tolerance is zero? All variances, however small, must be flagged for review.

## Requirements *(mandatory)*

### Functional Requirements

**P0 — Critical Architecture (Foundation)**

- **FR-001**: System MUST support versioned, reversible schema migrations with rollback capability.
- **FR-002**: System MUST reconcile all balance sources (GL-calculated, stored columns, subsidiary ledgers, report queries) on an hourly scheduled cycle and flag discrepancies automatically.
- **FR-003**: System MUST enforce debit-credit equality at the database level before any journal entry is committed.
- **FR-004**: System MUST route all journal entry creation through a single centralized service, eliminating duplicated GL posting logic.
- **FR-005**: System MUST store authentication tokens in secure, script-inaccessible storage (httpOnly cookies) rather than client-accessible localStorage.
- **FR-006**: System MUST support SSO (SAML 2.0) and LDAP authentication with automatic user provisioning and role mapping. When the identity provider is unreachable, only designated admin accounts may fall back to local credentials; all other users are blocked until IdP connectivity is restored.
- **FR-007**: System MUST enforce referential integrity via foreign key constraints on all applicable columns (excluding documented polymorphic columns).

**P1 — High Priority (Competitive Parity)**

- **FR-008**: System MUST provide a configurable workflow engine supporting multi-step, conditional approval chains with both sequential and parallel (AND/OR) branch topology for any document type.
- **FR-009**: System MUST provide a mobile application for core operations (inventory view, quotations, orders, and workflow approvals) with offline data sync.
- **FR-010**: System MUST perform automated 3-way matching of purchase orders, goods receipt notes, and supplier invoices with configurable tolerance thresholds supporting both percentage-based and absolute-amount-based tolerances (variance passes if either threshold is satisfied).
- **FR-011**: System MUST support intercompany transactions with automatic reciprocal journal entries and consolidation elimination entries.
- **FR-012**: System MUST comply with ZATCA Phase 2 e-invoicing: real-time clearance, cryptographic signing, and QR code embedding.
- **FR-013**: System MUST support FIFO and LIFO inventory costing methods in addition to existing WAC.
- **FR-014**: System MUST generate cash flow forecasts based on accounts receivable, accounts payable, and recurring entries.
- **FR-015**: System MUST provide an employee self-service portal for leave requests, payslip viewing, and profile management.
- **FR-016**: System MUST support embedded analytics dashboards via integration with BI tools.

**P2 — Medium Priority (Differentiation)**

- **FR-017**: System MUST support subscription billing with automated recurring invoice generation.
- **FR-018**: System MUST support advanced MRP with capacity planning and production scheduling.
- **FR-019**: System MUST generate statistical demand forecasts based on historical sales data.
- **FR-020**: System MUST support structured performance reviews with goal setting and self-assessment.
- **FR-021**: System MUST support marketing campaign management with engagement tracking.
- **FR-022**: System MUST support project time tracking with billable/non-billable classification.
- **FR-023**: System MUST support resource capacity planning across projects and manufacturing.
- **FR-024**: System MUST support blanket purchase orders with scheduled releases.
- **FR-025**: System MUST support advanced document management with version control and digital signatures.
- **FR-026**: System MUST support full offline mode for POS and field operations with reliable sync.

### Key Entities

- **Migration**: Schema version identifier, up/down scripts, execution timestamp, status (applied/rolled back).
- **Workflow Definition**: Name, document type, steps (sequence, approver rules, conditions, branch topology: sequential or parallel AND/OR), escalation rules, delegation rules.
- **Workflow Instance**: Definition reference, document reference, current step, status, approval history.
- **Intercompany Transaction**: Source entity, target entity, transaction type, amount, reciprocal entry references, elimination status.
- **3-Way Match**: PO reference, GRN reference, invoice reference, quantity/price variances, match status, tolerance applied (percentage and/or absolute amount).
- **ZATCA Submission**: Invoice reference, submission timestamp, clearance status, signed XML, rejection reason (if any), QR code data.
- **Subscription Plan**: Name, billing frequency, amount, start/end dates, auto-renewal flag.
- **Subscription Enrollment**: Customer, plan, enrollment date, next billing date, status.
- **Demand Forecast**: Product, period, forecasted quantity, confidence interval, model used.
- **Performance Review**: Employee, reviewer, cycle, goals, self-assessment, manager assessment, rating, status.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Schema migrations execute with zero data loss and rollback completes in under 5 minutes for any single migration.
- **SC-002**: Balance reconciliation detects 100% of discrepancies between GL-calculated and stored balances within one hourly reconciliation cycle.
- **SC-003**: Zero unbalanced journal entries exist in the database after double-entry trigger deployment.
- **SC-004**: 100% of GL postings route through the centralized service (zero direct GL insert points remain in module code).
- **SC-005**: Security audit confirms no auth tokens are accessible via client-side scripts.
- **SC-006**: Users authenticate via SSO/LDAP within 3 seconds, with automatic role assignment matching corporate directory groups.
- **SC-007**: Workflow-driven documents (POs, expenses, leave) complete the full approval cycle without manual routing intervention.
- **SC-008**: 3-way matching processes 95% of invoices automatically, flagging only genuine discrepancies.
- **SC-009**: Intercompany elimination entries balance to zero in consolidated reports.
- **SC-010**: ZATCA Phase 2 clearance succeeds on first submission for 98%+ of invoices.
- **SC-011**: Mobile app users can complete core tasks (view inventory, create quotation) in under 60 seconds.
- **SC-012**: FIFO/LIFO costing calculations match manual verification for 100% of test transactions.
- **SC-013**: Cash flow forecast accuracy is within 15% of actuals over a 30-day horizon.
- **SC-014**: Employee self-service reduces HR-handled leave/payslip requests by 70%.
- **SC-015**: Overall system completion rises from 72% to 90%+ after P0 and P1 implementation.

## Clarifications

### Session 2026-04-02

- Q: Should the workflow engine support parallel approval branches (AND/OR) or sequential-only? → A: Sequential + parallel (AND/OR branches)
- Q: When SSO/LDAP identity provider is unreachable, should local auth be available? → A: Admin-only fallback — only designated admin accounts can use local credentials
- Q: How frequently should balance reconciliation run? → A: Hourly scheduled refresh
- Q: Should mobile app v1 include workflow approval actions? → A: Yes, include approvals (view + approve/reject) in mobile v1
- Q: What tolerance model for 3-way matching? → A: Both percentage and absolute amount (variance passes if either threshold is met)

## Assumptions

- The existing PostgreSQL database supports triggers, materialized views, and the extensions needed for migration tooling.
- ZATCA's Phase 2 clearance API specifications and sandbox environment are available for integration testing.
- The organization has an existing LDAP/Active Directory or SAML 2.0 identity provider for SSO integration.
- The mobile app will target iOS and Android and will share business logic with the web frontend where feasible.
- Demand forecasting will use statistical methods (moving average, exponential smoothing) rather than requiring a dedicated ML infrastructure.
- The current approval system (basic single-step) will be superseded by the new workflow engine, not run in parallel.
- Intercompany accounting assumes all entities share the same chart of accounts structure (with entity-specific segments).
- BI integration will use embedded dashboards (e.g., Metabase, Grafana) rather than building a custom analytics engine.
- Full offline mode (P2) will use a Progressive Web App approach with local storage and sync queue.
- The team size is 3-4 developers, informing the phased delivery timeline.

---

## Gap Summary by Priority

### P0 — Critical (7 Features, ~13-15 weeks)

| #  | Gap                           | Current State                              | Plan                                                        | Dependencies      | Risks                                           | Effort     |
|----|-------------------------------|--------------------------------------------|-------------------------------------------------------------|--------------------|--------------------------------------------------|------------|
| 1  | Alembic Migration System      | Schema via CREATE TABLE IF NOT EXISTS      | Adopt Alembic, generate initial migration from current DB   | None               | Data loss during initial migration cutover       | 3-4 weeks  |
| 2  | Balance Reconciliation        | 4 divergent balance sources                | Materialized views + scheduled reconciliation job           | FR-001 (migrations)| Performance impact of materialized view refresh  | 2-3 weeks  |
| 3  | DB Double-Entry Trigger       | No DB-level enforcement                    | PostgreSQL trigger on journal_entry_lines                   | FR-001 (migrations)| Trigger performance on high-volume entry batches | 1 week     |
| 4  | Centralized GL Service        | GL logic duplicated in 25+ files           | Extract single service; refactor all 75 call sites          | None               | Regression in any of 25+ modules during refactor | 2 weeks    |
| 5  | HttpOnly Cookie Auth          | Refresh token in localStorage              | Backend issues httpOnly cookie; frontend removes token mgmt | None               | CORS/cross-domain cookie issues in deployment    | 1 week     |
| 6  | SSO/LDAP Integration          | No SSO or LDAP support                     | SAML 2.0 SP + LDAP bind with user provisioning              | FR-005 (auth fix)  | Varied LDAP schemas across customer environments | 2 weeks    |
| 7  | FK Constraint Enforcement     | 78 missing FKs (18 are polymorphic = N/A)  | Add remaining 60 FKs with data cleanup scripts              | FR-001 (migrations)| Orphaned data blocks constraint creation         | 2 weeks    |

### P1 — High Priority (10 Features, ~31-45 weeks)

| #  | Gap                           | Current State             | Plan                                                         | Dependencies           | Risks                                           | Effort      |
|----|-------------------------------|---------------------------|--------------------------------------------------------------|------------------------|--------------------------------------------------|-------------|
| 8  | Workflow Engine               | Basic single-step only    | Configurable multi-step engine with conditions & escalation  | P0 complete            | Over-engineering; scope creep into BPM           | 4-6 weeks   |
| 9  | Mobile App                    | No mobile app             | Cross-platform app for core ops with offline sync            | P0 complete, API stable| Platform fragmentation; offline sync complexity  | 8-12 weeks  |
| 10 | 3-Way Matching                | No matching               | Automated PO-GRN-Invoice matching with tolerance config      | None                   | Complex partial receipt/multi-invoice scenarios  | 2-3 weeks   |
| 11 | Intercompany Accounting       | Not supported             | Reciprocal entry automation + consolidation elimination      | FR-004 (GL service)    | Multi-currency intercompany adds complexity      | 3-4 weeks   |
| 12 | ZATCA Phase 2 E-Invoicing     | Partial (Phase 1 only)    | Full clearance API integration + crypto signing + QR         | None                   | ZATCA API changes; certification process delays  | 4-6 weeks   |
| 13 | FIFO/LIFO Costing             | WAC only                  | Add costing method selection per product/warehouse           | None                   | FIFO layer tracking adds storage and complexity  | 2-3 weeks   |
| 14 | Cash Flow Forecasting         | Not supported             | Projected cash flows from AR/AP aging + recurring entries    | None                   | Accuracy depends on data quality and entry habits| 2-3 weeks   |
| 15 | Employee Self-Service         | Not supported             | Portal for leave, payslips, profile with manager delegation  | None                   | Security — employees accessing only own data     | 3-4 weeks   |
| 16 | BI Dashboard Integration      | No BI integration         | Embedded analytics via BI tool with pre-built ERP dashboards | None                   | BI tool licensing; dashboard maintenance burden  | 1-2 weeks   |
| 17 | Full IFRS Compliance          | Partial                   | Revenue recognition (ASC 606), lease accounting, impairment  | FR-004 (GL service)    | Requires domain expertise; regulation complexity | 3-4 weeks   |

### P2 — Medium Priority (10 Features, ~33-46 weeks)

| #  | Gap                           | Current State             | Plan                                                         | Dependencies           | Risks                                           | Effort      |
|----|-------------------------------|---------------------------|--------------------------------------------------------------|------------------------|--------------------------------------------------|-------------|
| 18 | Subscription Billing          | Not supported             | Plan management + recurring invoice generation engine        | FR-008 (workflows)     | Proration, upgrades/downgrades, failed payments  | 3-4 weeks   |
| 19 | Advanced MRP                  | Basic MRP only            | Full MRP with capacity planning, scheduling, lead times      | None                   | Manufacturing domain complexity                  | 6-8 weeks   |
| 20 | Demand Forecasting            | Not supported             | Statistical forecasting (moving avg, exp. smoothing)         | None                   | Forecast accuracy with limited historical data   | 4-6 weeks   |
| 21 | Performance Reviews           | Not supported             | Goal setting, 360 feedback, review cycles                    | FR-015 (self-service)  | Adoption resistance; process standardization     | 3-4 weeks   |
| 22 | Campaign Management           | Not supported             | Campaign creation, send, engagement tracking                 | None                   | Email/SMS delivery infrastructure needed         | 3-4 weeks   |
| 23 | Time Tracking                 | Not supported             | Timesheets with project/task allocation, billable flagging   | Project module exists  | Adoption requires discipline; integration points | 2-3 weeks   |
| 24 | Resource Planning             | Not supported             | Capacity view for projects + manufacturing resources         | FR-018 (MRP), Projects | Cross-module data consistency                    | 4-5 weeks   |
| 25 | Blanket Purchase Orders       | Not supported             | Long-term agreements with scheduled release orders           | None                   | Low complexity but needs procurement UI changes  | 1-2 weeks   |
| 26 | Advanced Document Management  | Basic only                | Versioning, digital signatures, OCR for document capture     | None                   | Storage scaling; OCR accuracy for Arabic docs    | 3-4 weeks   |
| 27 | Full Offline Mode             | Partial (POS only)        | PWA with local storage, sync queue, conflict resolution      | FR-009 (mobile)        | Conflict resolution UX; data volume limits       | 4-6 weeks   |

### Partial Features Requiring Enhancement

| #  | Feature              | Current State                  | Gap                                             | Priority | Effort    |
|----|----------------------|--------------------------------|-------------------------------------------------|----------|-----------|
| P1 | Barcode/RFID         | Partial barcode support        | Full barcode scanning + RFID tag read/write      | P2       | 2-3 weeks |
| P2 | POS Offline Mode     | Partial offline                | Full offline with reliable sync and conflict UX  | P2       | 2-3 weeks |
| P3 | Workflow Engine       | Basic approvals only           | Covered by FR-008 above                          | P1       | See #8    |
| P4 | Document Management  | Basic attachments              | Covered by FR-025 above                          | P2       | See #26   |
| P5 | MRP                  | Basic BOM/WO                   | Covered by FR-018 above                          | P2       | See #19   |
| P6 | Quality Management   | Basic inspection               | Full QMS with NCRs, CAPA, audit trails           | P2       | 2-3 weeks |
| P7 | E-Invoicing (ZATCA)  | Phase 1 only                   | Covered by FR-012 above                          | P1       | See #12   |
| P8 | Revenue Recognition  | Basic only                     | Covered by #17 IFRS above                        | P1       | See #17   |
| P9 | Production Planning  | Basic scheduling               | Full production scheduling with optimization     | P2       | 3-4 weeks |
| P10| Offline Capability   | Partial                        | Covered by FR-026 above                          | P2       | See #27   |

---

## Implementation Phases

### Phase A: Foundation (Weeks 1-15) — Target Score: 85/100
P0 features: Alembic migrations, balance reconciliation, DB trigger, centralized GL, httpOnly auth, SSO/LDAP, FK constraints.

### Phase B: Competitive Parity (Weeks 16-60) — Target Score: 92/100
P1 features: Workflow engine, mobile app, 3-way matching, intercompany, ZATCA Phase 2, FIFO/LIFO, cash flow forecasting, self-service, BI, IFRS.

### Phase C: Differentiation (Weeks 61-106) — Target Score: 96/100
P2 features: Subscription billing, advanced MRP, demand forecasting, performance reviews, campaigns, time tracking, resource planning, blanket POs, document management, full offline.

### Phase D: Platform (Weeks 107-153) — Target Score: 98+/100
P3 features (not in scope for this spec): CPQ, shop floor control, AI insights, GCC localization, marketplace.
