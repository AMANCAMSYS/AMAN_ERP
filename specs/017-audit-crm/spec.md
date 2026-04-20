# Feature Specification: CRM Module Audit & Bug Fixes

**Feature Branch**: `017-audit-crm`  
**Created**: 2026-04-20  
**Status**: Draft  
**Input**: User description: "Speckit 12: audit-crm — إدارة علاقات العملاء"

## Clarifications

### Session 2026-04-20

- Q: When an opportunity already has a linked quotation and the user clicks "Convert to Quotation" again, should the system block the action or allow creating an additional quotation? → A: Block — show an error message with a link to the existing quotation.
- Q: When a ticket's `sla_hours` is null or zero, how should SLA tracking behave — skip the check, apply a system default, or raise an error? → A: Skip — return `"sla_not_configured"` status; no breach logic applied.
- Q: When an opportunity has no assigned user (`assigned_to` is null) and its stage changes to "won" or "lost," should the system skip the notification or send it to a fallback recipient? → A: Skip silently — no notification sent when `assigned_to` is null.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Sales Rep Converts Opportunity to Quotation (Priority: P1)

A sales representative views a qualified opportunity in the pipeline and clicks "Convert to Quotation." The system creates a corresponding sales quotation linked to that opportunity, and the rep is redirected to the new quotation for review.

**Why this priority**: This is the core revenue-generating flow in the CRM. A broken conversion means no opportunity can produce a quotation, blocking the entire sales pipeline. Currently fails due to wrong column names in the insert query.

**Independent Test**: Can be fully tested by creating an opportunity then clicking "Convert to Quotation" — success means a quotation record appears in the Sales module with the correct customer and value.

**Acceptance Scenarios**:

1. **Given** a sales opportunity in any stage, **When** the sales rep clicks "Convert to Quotation," **Then** a new quotation is created in the Sales module with the opportunity's customer, expected value, and a reference back to the opportunity, and the user sees a success confirmation.
2. **Given** the opportunity has no linked customer, **When** the rep attempts conversion, **Then** the system shows a clear validation error explaining that a customer must be assigned before conversion.
3. **Given** a network or server error during conversion, **When** the rep clicks "Convert to Quotation," **Then** the partial quotation is rolled back and the user sees a meaningful error message; the opportunity remains unchanged.
4. **Given** an opportunity that is already linked to an existing quotation, **When** the rep clicks "Convert to Quotation," **Then** the system blocks the action, shows an error message stating a quotation already exists, and provides a direct link to the existing quotation.

---

### User Story 2 — Support Agent Adds Comment to a Ticket (Priority: P1)

A support agent opens a ticket, types a comment in the reply field, and clicks "Send." The comment appears immediately in the ticket thread, showing the agent's name and timestamp. Currently fails because the frontend sends the wrong field name.

**Why this priority**: Without working comments, support agents cannot communicate on tickets at all, making the entire support module non-functional for team use.

**Independent Test**: Can be fully tested by opening any ticket, submitting a comment, and verifying it appears in the thread with the correct author name.

**Acceptance Scenarios**:

1. **Given** an open support ticket, **When** an agent types a comment and submits, **Then** the comment is saved and immediately visible in the ticket thread with the agent's name displayed correctly.
2. **Given** a ticket with multiple comments, **When** any user views the ticket, **Then** all comments show the correct author name (the name of the user who wrote it, not empty or undefined).
3. **Given** an empty comment field, **When** the agent tries to submit, **Then** submission is blocked and a validation message appears.

---

### User Story 3 — Marketing Manager Views Campaign Engagement Metrics (Priority: P1)

A marketing manager opens the Marketing Campaigns list and sees columns for Sent, Opened, Clicked, and Responded counts populated with actual data. After executing a campaign, updated numbers appear in the list and in the campaign detail report.

**Why this priority**: All engagement metrics in `MarketingCampaigns.jsx` display as zero due to mismatched field names, making the entire campaigns analytics view meaningless.

**Independent Test**: Can be fully tested by executing a campaign against a segment, then viewing the campaigns list — metrics must reflect non-zero values.

**Acceptance Scenarios**:

1. **Given** a campaign that has been executed, **When** the manager views the Campaigns list, **Then** Sent, Opened, Clicked, and Responded columns all show the correct numeric values from the last execution.
2. **Given** the Campaign ROI analytics page, **When** the manager loads it, **Then** open rate, click rate, and conversion metrics are computed from live data rather than returning zeros.
3. **Given** the CRM Dashboard, **When** the manager views the campaign summary widget, **Then** campaign engagement counts match the values shown in the Campaign detail page.

---

### User Story 4 — Support Agent Tracks SLA Deadline on a Ticket (Priority: P2)

A support agent opens a high-priority ticket and can see whether it is within or has breached its SLA time. The SLA check computes elapsed time correctly regardless of the server timezone configuration.

**Why this priority**: SLA tracking is critical for service quality management. An uncaught timezone mismatch causes a server crash (`TypeError`) on every SLA check, making the endpoint completely unusable.

**Independent Test**: Can be tested by checking SLA status on any ticket created more than one hour ago — system must return a valid "within SLA" or "breached" status without throwing an error.

**Acceptance Scenarios**:

1. **Given** a ticket created 2 hours ago with a 24-hour SLA, **When** the SLA check is triggered, **Then** the system returns "within SLA" with the correct hours remaining, without any server error.
2. **Given** a ticket created 30 hours ago with a 24-hour SLA, **When** the SLA check is triggered, **Then** the system returns "SLA breached" with the number of hours overdue.
3. **Given** a server configured in a non-UTC timezone, **When** any SLA check runs, **Then** the elapsed time calculation is correct and no `TypeError` is raised.

---

### User Story 5 — Sales Manager Views Campaign ROI Analytics (Priority: P2)

A sales manager navigates to Pipeline Analytics → Campaign ROI and sees a table with campaign names, cost, leads attributed, and ROI percentages populated with real data from executed campaigns.

**Why this priority**: ROI analytics data is all zeros because the backend queries stale column names that are never written. Decision-makers cannot evaluate campaign effectiveness.

**Independent Test**: Can be fully tested by loading the Campaign ROI analytics endpoint after at least one campaign has been executed — all rate fields must be non-zero.

**Acceptance Scenarios**:

1. **Given** at least one completed campaign with attributed leads, **When** the manager loads Campaign ROI analytics, **Then** open rate, click rate, response rate, and cost-per-lead are populated with correct values.
2. **Given** a campaign with zero attributed leads, **When** ROI is computed, **Then** cost-per-lead shows "N/A" or infinity indicator rather than a divide-by-zero error.

---

### User Story 6 — CRM User Links a Contact to a Customer (Priority: P3)

A CRM user creates or edits a contact record and selects the associated customer from a searchable dropdown, rather than having to know and type the internal customer ID number.

**Why this priority**: The current manual numeric ID input is unusable in practice and highly error-prone. A dropdown improves data integrity and usability significantly.

**Independent Test**: Can be tested by opening the Add Contact form — a searchable customer dropdown must appear, and selecting a customer must save the correct association.

**Acceptance Scenarios**:

1. **Given** the Add Contact form, **When** the user types part of a customer name in the customer field, **Then** a dropdown of matching customers appears.
2. **Given** the user selects a customer from the dropdown, **When** the contact is saved, **Then** the contact is correctly linked to that customer in the database.
3. **Given** no customers exist in the system, **When** the user opens the Add Contact form, **Then** the customer field shows an empty state message rather than an empty dropdown with no explanation.

---

### User Story 7 — Sales Manager Receives Notification on Pipeline Events (Priority: P3)

When a support ticket is assigned to an agent, or when an opportunity moves to "Won" or "Lost," the relevant user receives an in-app notification. Currently no CRM events trigger any notifications.

**Why this priority**: Operational gap that reduces team responsiveness. The notification infrastructure already exists and is used by other modules — integration is straightforward.

**Independent Test**: Can be tested by assigning a ticket to a user — that user must receive an in-app notification.

**Acceptance Scenarios**:

1. **Given** a ticket is assigned to an agent, **When** the assignment is saved, **Then** the agent receives an in-app notification with the ticket subject and a link to the ticket.
2. **Given** an opportunity is moved to "Won," **When** the stage is saved and the opportunity has an assigned sales rep, **Then** the assigned rep receives an in-app notification.
3. **Given** an opportunity is moved to "Won" or "Lost" but has no assigned user, **When** the stage is saved, **Then** no notification is sent and the update completes without error.
3. **Given** a campaign finishes execution, **When** all messages are dispatched, **Then** the campaign creator receives an in-app notification with the total recipients count.

---

### Edge Cases

- What happens when `convert_opportunity_to_quotation` is called for an opportunity already linked to a quotation? **Resolved: the system blocks the action and returns an error with a link to the existing quotation.**
- How does SLA tracking behave when `sla_hours` is set to zero or null on a ticket? **Resolved: skip the SLA check and return `"sla_not_configured"` — no breach logic is applied.**
- What happens when a campaign is executed against a segment with no members? The system must return a clear message rather than silently sending to zero recipients.
- What happens when the `marketing_campaigns` table still has the old `sent_count` / `open_count` columns with stale data? Analytics must read only from the correct `total_*` columns.
- How does the `update_opportunity` endpoint behave if an API client sends an unexpected field name in the PATCH body (SQL injection via dynamic SET clause)?

---

## Requirements *(mandatory)*

### Functional Requirements

**Critical Bug Fixes**

- **FR-001**: The system MUST correctly create a quotation from an opportunity using the columns `sq_number`, `expiry_date`, and `sq_id` as defined in the `sales_quotations` and `sales_quotation_lines` tables. If the opportunity already has a linked quotation (`won_quotation_id` is set), the system MUST block conversion and return an error message with a reference to the existing quotation.
- **FR-002**: The add-ticket-comment endpoint MUST accept and store the comment text from a field named `comment`, and the frontend MUST send `{ comment: "<text>" }` in the request body.
- **FR-003**: The ticket comment list response MUST include the author's display name in a field named `author_name`, and the frontend MUST render it from `comment.author_name`.

**High-Severity Bug Fixes**

- **FR-004**: The Campaigns list page MUST read engagement metrics from `total_sent`, `total_opened`, `total_clicked`, and `total_responded` fields returned by the API.
- **FR-005**: The Campaign ROI analytics endpoint MUST compute open rate, click rate, and response rate from `total_sent`, `total_opened`, `total_clicked`, and `total_responded` columns.
- **FR-006**: The CRM Dashboard campaign summary widget MUST use `total_responded` (not `conversion_count`) for the responded count.
- **FR-007**: The SLA elapsed-time calculation MUST use a timezone-aware current time that is compatible with the timezone-aware `created_at` timestamp stored in the database, preventing any `TypeError` at runtime. If a ticket's `sla_hours` is null or zero, the SLA check MUST be skipped and the response MUST return a status of `"sla_not_configured"` with no breach evaluation.

**Medium-Severity Fixes**

- **FR-008**: The `update_opportunity` endpoint MUST validate incoming field names against an explicit whitelist of allowed columns before building the SQL SET clause, rejecting any unrecognised field names with a 422 error.
- **FR-009**: The Add/Edit Contact form MUST provide a searchable dropdown to select the associated customer, populated from the existing customers list endpoint, instead of a raw numeric text input.
- **FR-010**: The Attribute Lead modal in the Campaign Report page MUST provide a searchable dropdown of existing opportunities instead of a raw numeric text input.
- **FR-011**: The system MUST dispatch an in-app notification when a support ticket is assigned, when an opportunity stage changes to "won" or "lost," and when a campaign execution completes. If an opportunity has no assigned user (`assigned_to` is null), the stage-change notification MUST be skipped silently.

**Schema Hygiene**

- **FR-012**: The `marketing_campaigns` database table MUST have the obsolete columns `sent_count`, `open_count`, `click_count`, and `conversion_count` removed via a migration, retaining only the `total_*` family of columns.

### Key Entities

- **Opportunity**: A tracked sales lead with stage, probability, expected value, assigned user, and optional customer link. Central entity for the pipeline.
- **Quotation**: A formal price offer generated from an opportunity. Lives in the Sales module; linked to an opportunity via `won_quotation_id`.
- **Support Ticket**: A customer issue record with SLA deadline, priority, status, assignment, and a thread of comments.
- **Ticket Comment**: A message in a ticket thread. Has author, timestamp, content text, and an internal/external flag.
- **Marketing Campaign**: A targeted message campaign (email/SMS) aimed at a customer segment, tracking delivery and engagement per recipient.
- **Campaign Recipient**: Per-contact delivery record tracking sent, delivered, opened, clicked, and responded timestamps.
- **CRM Contact**: A person at a customer company, linked to the customer party record.
- **Notification**: An in-app alert dispatched to a user referencing a CRM event (ticket assigned, opportunity won/lost, campaign completed).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Converting an opportunity to a quotation succeeds 100% of the time when a customer is linked, and the resulting quotation appears in the Sales module with matching customer and value.
- **SC-002**: Submitting a ticket comment always saves and displays the correct author name — zero instances of blank or undefined author names in the ticket thread.
- **SC-003**: All engagement metric columns in the Campaigns list (Sent, Opened, Clicked, Responded) show values consistent with what the Campaign Report page shows for the same campaign.
- **SC-004**: Campaign ROI analytics and the CRM Dashboard campaign widget return non-zero engagement rates for any campaign that has been executed with at least one delivery.
- **SC-005**: SLA check requests succeed without errors across all server timezone configurations — zero `TypeError` exceptions in the SLA module. Tickets with null or zero `sla_hours` return `"sla_not_configured"` rather than triggering breach logic.
- **SC-006**: The opportunity update endpoint rejects any request containing an unrecognised field name with a validation error, without silently including it in the SQL query.
- **SC-007**: Users creating a contact can find and select the correct customer using a name-based search without needing to know any internal numeric ID.
- **SC-008**: In-app notifications are delivered within 5 seconds of the triggering event (ticket assigned, opportunity stage changed to won/lost, campaign executed).
- **SC-009**: After applying the schema migration, no query in the CRM module references the removed legacy columns (`sent_count`, `open_count`, `click_count`, `conversion_count`).

---

## Assumptions

- The `sales_quotations` table schema (using `sq_number`, `expiry_date`, `sq_id`) is the authoritative definition and the CRM router must conform to it — not the other way around.
- The existing `notification_service.dispatch()` interface is used as-is; no new notification channels need to be introduced for CRM events.
- The old columns (`sent_count`, `open_count`, `click_count`, `conversion_count`) in `marketing_campaigns` contain only zeros or stale data, and dropping them will not cause data loss.
- The customers searchable dropdown for the Contact form uses the same `/sales/customers` list endpoint already available in the system.
- SLA notifications (breach alerts) are out of scope for this audit cycle; only the TypeError crash fix is required.
- The `CampaignForm.jsx` `branch_id` dead field is removed as a cleanup item with no functional change.
- Mobile / offline support is out of scope.
- No changes to existing API contract signatures (URL paths or HTTP methods) are required; only field names and query internals change.
