# Feature Specification: AMAN ERP — 18 Missing Competitive Features

**Feature Branch**: `002-erp-missing-features`  
**Created**: 2026-04-02  
**Status**: Draft  
**Input**: User description: "Implement 18 missing features from Feature Comparison Matrix (section 2.1) to achieve competitive parity with SAP, NetSuite, Dynamics 365, Odoo, and Sage X3."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — SSO/LDAP Enterprise Login (Priority: P1)

As an IT administrator at a mid-sized Saudi enterprise, I need employees to log in with their existing corporate credentials via SSO or LDAP so I can enforce our security policy and avoid managing separate AMAN passwords.

**Why this priority**: SSO/LDAP is a deal-breaker for enterprise sales. Organizations with centralized identity management cannot adopt AMAN without it. Every major competitor supports it.

**Independent Test**: Connect AMAN to a corporate directory, log in with corporate credentials, verify role mapping, deactivate a user in the directory, and confirm access is revoked.

**Acceptance Scenarios**:

1. **Given** an LDAP directory with employee accounts, **When** a user logs in with corporate credentials, **Then** they are authenticated and assigned the correct AMAN role based on their directory group.
2. **Given** SSO is configured with the company's identity provider, **When** a user clicks "Login with SSO" from the AMAN login page, **Then** they are redirected, authenticated, and returned to AMAN without entering separate credentials.
3. **Given** an employee is deactivated in the corporate directory, **When** they attempt to access AMAN, **Then** access is denied immediately.
4. **Given** the identity provider is unreachable, **When** a regular user attempts login, **Then** they see a message that corporate login is temporarily unavailable. **When** a designated admin attempts login, **Then** they can authenticate using local credentials as a fallback.
5. **Given** a new employee is added to the corporate directory in an "ERP Users" group, **When** they first log in to AMAN, **Then** their account is automatically provisioned with the appropriate role.

---

### User Story 2 — 3-Way Matching for Procurement Compliance (Priority: P1)

As a procurement officer, I need the system to automatically match purchase orders, goods receipt notes, and supplier invoices so that quantity and price discrepancies are flagged before payment is authorized.

**Why this priority**: 3-way matching is a standard procurement compliance control present in SAP, NetSuite, Dynamics 365, and Odoo. Its absence exposes the organization to overpayment, fraud, and audit findings.

**Independent Test**: Create a PO, receive goods (partial and full), submit a supplier invoice, and verify the system correctly flags quantity and price variances against configurable tolerances.

**Acceptance Scenarios**:

1. **Given** a PO for 100 units at 50 SAR each, a GRN for 80 units, and an invoice for 100 units, **When** matching is performed, **Then** a quantity discrepancy of 20 units is flagged and the invoice is held.
2. **Given** all three documents match within configured tolerance, **When** matching is performed, **Then** the invoice is approved for payment automatically.
3. **Given** a price variance of 8% on an invoice where the tolerance is set to 5%, **When** matching is performed, **Then** the invoice is held for review with the variance highlighted.
4. **Given** tolerance is configured as both 5% percentage and 100 SAR absolute, **When** a variance of 4% (but 200 SAR) occurs, **Then** the invoice passes on percentage but is flagged on absolute amount.
5. **Given** a single PO with 3 partial GRNs and 2 invoices, **When** matching is performed, **Then** each invoice is matched against the cumulative received quantity.

---

### User Story 3 — Intercompany Accounting (Priority: P1)

As a group CFO overseeing multiple legal entities, I need intercompany transactions to automatically create reciprocal journal entries in both entities and generate elimination entries during consolidation.

**Why this priority**: Multi-entity enterprises cannot use AMAN without intercompany accounting. SAP, NetSuite, Dynamics 365, and Odoo all support this. It unlocks the corporate/group market segment.

**Independent Test**: Create an intercompany sale from Entity A to Entity B, verify both entities have reciprocal entries, run consolidation, and confirm intercompany balances are eliminated.

**Acceptance Scenarios**:

1. **Given** Entity A sells goods worth 10,000 SAR to Entity B, **When** the sale is posted, **Then** Entity A records revenue and a receivable, Entity B records COGS and a payable, and both entries cross-reference each other.
2. **Given** outstanding intercompany balances at period-end, **When** consolidation is run, **Then** all intercompany receivables/payables and revenue/expenses are eliminated and the consolidated statements are correct.
3. **Given** an intercompany transaction in different currencies, **When** posted, **Then** each entity records in its local currency with the exchange rate applied, and any FX difference is posted to the designated exchange gain/loss account.
4. **Given** Entity A and Entity B have different fiscal year-ends, **When** an intercompany transaction occurs near period-end, **Then** the system handles the cross-period posting with appropriate accruals.

---

### User Story 4 — FIFO/LIFO Inventory Costing (Priority: P1)

As a warehouse manager in the food/pharma industry, I need FIFO and LIFO costing methods so that cost of goods sold reflects the actual flow of goods and meets industry regulatory requirements.

**Why this priority**: AMAN currently only supports WAC. FIFO/LIFO is available in all major competitors and is legally required in certain industries. Without it, AMAN is excluded from food, pharma, and manufacturing sectors.

**Independent Test**: Set a product to FIFO, perform multiple purchases at different prices, sell units, and verify COGS uses the earliest cost layer. Repeat for LIFO.

**Acceptance Scenarios**:

1. **Given** Product X uses FIFO with purchases of 50 units at 10 SAR then 50 units at 15 SAR, **When** 60 units are sold, **Then** COGS = (50 x 10) + (10 x 15) = 650 SAR.
2. **Given** Product Y uses LIFO with the same purchases, **When** 60 units are sold, **Then** COGS = (50 x 15) + (10 x 10) = 850 SAR.
3. **Given** a product switches costing method from WAC to FIFO, **When** the change is applied, **Then** existing inventory is revalued and cost layers are established from the change date forward.
4. **Given** a sales return on a FIFO product, **When** the return is processed, **Then** the returned units are added back at their original cost layer.

---

### User Story 5 — Cash Flow Forecasting (Priority: P2)

As a treasury manager, I need the system to project future cash inflows and outflows based on AR aging, AP aging, and recurring entries so I can plan liquidity and avoid cash shortfalls.

**Why this priority**: Cash flow forecasting is offered by SAP, NetSuite, Dynamics 365, and Sage X3. Without it, treasury teams cannot plan ahead, increasing the risk of cash crunches.

**Independent Test**: With existing AR/AP and recurring entries, generate a 90-day cash flow forecast and verify the projections match expected inflows/outflows.

**Acceptance Scenarios**:

1. **Given** outstanding AR of 500,000 SAR due in 30 days and AP of 300,000 SAR due in 15 days, **When** a cash flow forecast is generated, **Then** it shows the AP outflow before the AR inflow with the resulting cash position.
2. **Given** a recurring monthly expense of 50,000 SAR, **When** the 90-day forecast is generated, **Then** it includes 3 occurrences of that expense.
3. **Given** historical payment patterns show customers pay on average 10 days late, **When** the forecast uses "expected" mode, **Then** AR inflows are shifted by 10 days from due date.
4. **Given** multiple bank accounts, **When** the forecast is generated, **Then** it shows projected balances per account and a consolidated total.

---

### User Story 6 — Employee Self-Service Portal (Priority: P2)

As an employee, I need a self-service portal to submit leave requests, view my payslips, update my personal profile, and check my leave balance without contacting HR.

**Why this priority**: Employee self-service is offered by SAP, NetSuite, Dynamics 365, and Odoo. It reduces HR administrative workload and improves employee satisfaction.

**Independent Test**: Log in as an employee, submit a leave request, view a payslip, update a phone number, and verify the leave balance is correctly reduced after approval.

**Acceptance Scenarios**:

1. **Given** an employee with 15 days annual leave remaining, **When** they submit a 3-day leave request, **Then** the request is sent to their manager for approval and the pending balance shows 12 days.
2. **Given** payroll has been processed for March, **When** the employee opens the payslips section, **Then** they see the March payslip with gross, deductions, and net amounts.
3. **Given** an employee updates their phone number, **When** the update is saved, **Then** the HR record reflects the new number and an audit log entry is created.
4. **Given** a manager receives a leave request, **When** they approve it, **Then** the employee is notified and the leave calendar is updated.

---

### User Story 7 — Mobile App for Field Operations (Priority: P2)

As a field sales representative, I need a mobile app to view real-time inventory, create quotations, submit orders, and approve workflows while visiting customer sites, even with intermittent connectivity.

**Why this priority**: SAP, NetSuite, Dynamics 365, and Odoo all offer mobile apps. Field teams cannot use AMAN without mobile access, limiting its applicability for distributed workforces.

**Independent Test**: Log in on a mobile device, browse inventory, create a quotation, lose connectivity, continue working, reconnect, and verify all data syncs correctly.

**Acceptance Scenarios**:

1. **Given** a mobile device with network access, **When** the user opens the app, **Then** they see a dashboard with inventory levels, pending orders, and pending approvals.
2. **Given** a customer meeting, **When** the user creates a quotation on mobile, **Then** it syncs to the server and appears in the web interface.
3. **Given** intermittent connectivity, **When** the user creates a quotation offline, **Then** it is saved locally and syncs automatically when connectivity returns with no data loss.
4. **Given** a pending purchase order approval, **When** a manager opens the mobile app, **Then** they can review the PO details and approve or reject with a comment.
5. **Given** two users edit the same record (one mobile, one web) while offline, **When** both sync, **Then** the system flags the conflict and presents both versions for manual resolution.

---

### User Story 8 — Subscription Billing (Priority: P2)

As a finance manager at a company with recurring revenue (SaaS, maintenance contracts), I need subscription billing to automatically generate invoices on a recurring schedule based on customer plans.

**Why this priority**: Subscription billing is offered by SAP, NetSuite, Dynamics 365, and Odoo. Without it, businesses with recurring revenue must manually create invoices each period.

**Independent Test**: Create a subscription plan, enroll a customer, advance the billing date, and verify invoices are generated automatically.

**Acceptance Scenarios**:

1. **Given** a customer enrolled in a monthly 5,000 SAR plan starting Jan 1, **When** the billing cycle runs on Feb 1, **Then** an invoice for 5,000 SAR is automatically generated and linked to the subscription.
2. **Given** a customer upgrades mid-cycle from a 5,000 SAR plan to an 8,000 SAR plan on the 15th, **When** the next invoice is generated, **Then** it includes a prorated credit for the unused portion and a prorated charge for the new plan.
3. **Given** a subscription is cancelled, **When** the cancellation is processed, **Then** a final prorated invoice is generated (if applicable) and no further invoices are created.
4. **Given** a payment fails for a subscription invoice, **When** the system retries, **Then** the customer is notified and the subscription is flagged after 3 consecutive failures.

---

### User Story 9 — BI Dashboard Integration (Priority: P2)

As a business owner, I need embedded analytics dashboards showing key financial, sales, and operational KPIs so I can make data-driven decisions without exporting data to external tools.

**Why this priority**: BI integration is offered by all major competitors. Without it, decision-makers lack real-time visibility and must manually analyze exported data.

**Independent Test**: Open the dashboard page, verify KPIs update in real-time, filter by date range and branch, and confirm data matches the underlying reports.

**Acceptance Scenarios**:

1. **Given** the user has dashboard access, **When** they open the analytics page, **Then** they see pre-built dashboards for revenue, expenses, cash position, top customers, and inventory turnover.
2. **Given** a date range filter, **When** the user selects "Last Quarter," **Then** all dashboard widgets update to reflect that period's data.
3. **Given** a multi-branch company, **When** a branch manager views dashboards, **Then** they only see data for their authorized branches.
4. **Given** new transactions are posted, **When** the dashboard is refreshed, **Then** KPIs reflect the latest data within 15 minutes.

---

### User Story 10 — Blanket Purchase Orders (Priority: P3)

As a procurement manager, I need blanket purchase orders for long-term supplier agreements so I can negotiate better prices and release orders against the agreement as needed.

**Why this priority**: Blanket POs are offered by SAP, NetSuite, Dynamics 365, and Odoo. They enable strategic procurement for organizations with recurring purchasing needs.

**Independent Test**: Create a blanket PO for 1,000 units over 12 months, release 3 partial orders against it, and verify the remaining quantity and budget are tracked correctly.

**Acceptance Scenarios**:

1. **Given** a blanket PO for 1,000 units at 20 SAR each (total 20,000 SAR) valid for 12 months, **When** a release order for 200 units is created, **Then** the blanket PO shows 800 units / 16,000 SAR remaining.
2. **Given** the blanket PO has 100 units remaining, **When** a release order for 150 units is attempted, **Then** the system warns that it exceeds the agreement and requires approval to proceed.
3. **Given** the blanket PO expires, **When** a user tries to create a release order, **Then** the system blocks it and prompts for agreement renewal.

---

### User Story 11 — Campaign Management for CRM (Priority: P3)

As a marketing manager, I need to create and track marketing campaigns (email/SMS) targeted at customer segments so I can measure engagement and attribute leads to campaigns.

**Why this priority**: Campaign management is offered by SAP, NetSuite, Dynamics 365, and Odoo. Without it, marketing teams cannot track ROI on outreach efforts.

**Independent Test**: Create a campaign targeted at a customer segment, execute it, and verify engagement metrics (opens, clicks, responses) are recorded.

**Acceptance Scenarios**:

1. **Given** a customer segment of 500 contacts, **When** an email campaign is sent, **Then** delivery, open, and click-through rates are tracked per contact.
2. **Given** a completed campaign, **When** the marketing manager views the campaign report, **Then** they see total sends, opens, clicks, responses, and cost per lead.
3. **Given** a lead is generated from a campaign, **When** the lead is converted to an opportunity, **Then** the CRM attributes it to the originating campaign.

---

### User Story 12 — Performance Reviews for HR (Priority: P3)

As an HR manager, I need structured performance review cycles with goal setting, self-assessments, and manager evaluations so the company can track employee development and make informed promotion decisions.

**Why this priority**: Performance reviews are offered by SAP, Dynamics 365, and Odoo. Without them, talent management relies on ad-hoc processes.

**Independent Test**: Create a review cycle, assign reviewees, complete self-assessments and manager evaluations, and verify final scores are calculated.

**Acceptance Scenarios**:

1. **Given** a quarterly review cycle is created, **When** it is launched, **Then** all eligible employees are notified to complete self-assessments by the deadline.
2. **Given** an employee submits their self-assessment, **When** the manager opens the review, **Then** they see the self-assessment alongside their own evaluation form.
3. **Given** both self-assessment and manager evaluation are complete, **When** the review is finalized, **Then** a composite score is calculated and the employee can view their results.
4. **Given** a review deadline passes with incomplete assessments, **When** the system checks, **Then** reminders are sent to the employee and their manager.

---

### User Story 13 — CPQ (Configure Price Quote) (Priority: P3)

As a sales representative selling configurable products, I need a guided configuration tool that validates combinations, calculates pricing with rules/discounts, and generates professional quotes.

**Why this priority**: CPQ is offered by SAP, NetSuite, and Dynamics 365. It targets complex B2B sales where products have options, bundles, and tiered pricing.

**Independent Test**: Configure a product with options, verify invalid combinations are blocked, confirm pricing rules apply correctly, and generate a quote document.

**Acceptance Scenarios**:

1. **Given** a product with 3 configuration options (size, color, material), **When** the user selects incompatible options (e.g., "Large" + "Glass"), **Then** the system prevents the invalid combination with an explanation.
2. **Given** a configured product with volume discount tiers, **When** the quantity exceeds a tier threshold, **Then** the unit price automatically adjusts to the discounted rate.
3. **Given** a completed configuration, **When** the user clicks "Generate Quote," **Then** a professional PDF quote is created with line items, options, pricing, and terms.

---

### User Story 14 — Demand Forecasting (Priority: P3)

As a supply chain planner, I need the system to forecast future demand based on historical sales data so I can optimize purchasing and avoid stockouts or overstock.

**Why this priority**: Demand forecasting is offered by SAP, NetSuite, and Dynamics 365. Without it, procurement decisions are reactive rather than proactive.

**Independent Test**: With 12+ months of sales history, generate a 3-month demand forecast and verify projections are reasonable with confidence intervals.

**Acceptance Scenarios**:

1. **Given** 12 months of sales history for Product X, **When** a demand forecast is generated, **Then** it produces projected quantities for the next 3 months with confidence intervals.
2. **Given** seasonal products with peak/trough patterns, **When** the forecast runs, **Then** it detects and accounts for seasonality.
3. **Given** a forecast is generated, **When** the planner reviews it, **Then** they can manually adjust projected quantities and save the adjusted forecast as the working plan.

---

### User Story 15 — Shop Floor Control (Priority: P3)

As a production supervisor, I need real-time visibility into work order progress on the shop floor, including station-by-station tracking, so I can identify bottlenecks and manage production schedules.

**Why this priority**: Shop floor control is offered by SAP and Dynamics 365. Without it, manufacturing visibility is limited to work order start/complete with no in-process tracking.

**Independent Test**: Start a work order, report progress at each routing operation/station, and verify the dashboard shows real-time status.

**Acceptance Scenarios**:

1. **Given** a work order with 4 operations, **When** an operator completes operation 2, **Then** the shop floor dashboard shows the order at 50% progress with time spent per operation.
2. **Given** an operation takes longer than the estimated time, **When** the threshold is exceeded, **Then** the supervisor receives an alert about the delayed operation.
3. **Given** multiple work orders in progress, **When** the supervisor views the shop floor dashboard, **Then** they see all active orders with their current operation, status, and estimated completion.

---

### User Story 16 — Routing/Operations for Manufacturing (Priority: P3)

As a manufacturing engineer, I need to define production routings (sequences of operations with work centers, setup times, and run times) so that work orders follow the correct production steps and costing is accurate.

**Why this priority**: Routing is offered by SAP, NetSuite, Dynamics 365, and Odoo. Without it, BOMs have no production process definition and manufacturing costing is inaccurate.

**Independent Test**: Define a routing with 3 operations, create a work order using that routing, and verify each operation appears in sequence with correct time estimates.

**Acceptance Scenarios**:

1. **Given** a routing with operations: Cutting (10 min setup, 2 min/unit run), Assembly (15 min setup, 5 min/unit run), QC (5 min setup, 1 min/unit run), **When** a work order for 100 units is created, **Then** total estimated time = (10+200) + (15+500) + (5+100) = 830 minutes.
2. **Given** a BOM linked to a routing, **When** the work order is costed, **Then** labor cost is calculated from operation times x work center hourly rates.
3. **Given** an alternative routing exists, **When** the primary work center is at capacity, **Then** the planner can select the alternative routing for the work order.

---

### User Story 17 — Time Tracking for Projects (Priority: P3)

As a project team member at a service company, I need to log time against project tasks with billable/non-billable classification so the company can accurately bill clients and track project profitability.

**Why this priority**: Time tracking is offered by SAP, NetSuite, Dynamics 365, and Odoo. Service companies cannot bill accurately without it.

**Independent Test**: Log time entries against a project task, mark them billable, and verify the project profitability report reflects the logged hours and costs.

**Acceptance Scenarios**:

1. **Given** a project with tasks, **When** an employee logs 8 hours against "Design Phase" as billable, **Then** the timesheet shows the entry and the project accumulates 8 billable hours.
2. **Given** a weekly timesheet, **When** the employee submits it, **Then** the manager can approve or reject individual entries with comments.
3. **Given** approved billable hours at 200 SAR/hour, **When** the project profitability report is viewed, **Then** it shows 1,600 SAR in billable revenue against the project.

---

### User Story 18 — Resource Planning (Priority: P3)

As a project manager, I need to view team member availability and allocate resources across projects so I can avoid over-booking and balance workloads.

**Why this priority**: Resource planning is offered by SAP, NetSuite, Dynamics 365, and Odoo. Without it, resource allocation is done manually with spreadsheets.

**Independent Test**: View the resource calendar, allocate team members to projects, and verify conflicts are flagged when over-allocation occurs.

**Acceptance Scenarios**:

1. **Given** 3 active projects requiring developers, **When** the resource planner opens the allocation view, **Then** they see each team member's current allocation percentage across projects.
2. **Given** a developer allocated at 80% to Project A, **When** the planner tries to allocate them at 40% to Project B, **Then** the system warns of 120% over-allocation.
3. **Given** the resource calendar, **When** filtered by "available next week," **Then** it shows team members with capacity below 100%.

---

### Edge Cases

- What happens when an SSO identity provider is intermittently failing? System must cache the last successful auth for a configurable grace period for designated admins only; all other users are blocked.
- What happens when a 3-way match involves partial GRNs across multiple warehouses? Each GRN is matched independently and the cumulative received quantity is compared against the PO line.
- What happens when intercompany entities use different charts of accounts? The system must maintain a mapping table between entity-specific accounts and the consolidated chart.
- What happens when FIFO cost layers are exhausted (negative inventory)? The system must prevent negative inventory by default — sales that would cause negative stock are blocked with a clear error message.
- What happens when a subscription customer's payment method expires? The system must notify the customer 7 days before the next billing cycle and flag the subscription as at-risk.
- What happens when a mobile user and web user edit the same quotation simultaneously? The system must detect the conflict at sync time and present both versions for manual resolution.
- What happens when a CPQ configuration has circular dependency rules? The configuration engine must detect and prevent circular dependencies during rule definition.
- What happens when demand forecast has insufficient history (< 3 months)? The system must warn the user and offer a simple moving average with wider confidence intervals.
- What happens when a blanket PO's negotiated price changes mid-agreement? The system must support price amendments with an effective date, and new releases use the amended price.
- What happens when a shop floor operation is skipped? The system must enforce operation sequence unless an authorized supervisor overrides it.
- What happens when a user receives too many notifications? The system must allow users to configure notification preferences per channel (email, in-app, push) and per event type, with sensible defaults.

## Requirements *(mandatory)*

### Functional Requirements

**Tier 1 — Enterprise Essentials (P1)**

- **FR-001**: System MUST support SSO authentication (SAML 2.0) and LDAP directory integration with automatic user provisioning, role mapping from directory groups, and admin-only local auth fallback when the identity provider is unreachable.
- **FR-002**: System MUST perform automated 3-way matching of purchase orders, goods receipt notes, and supplier invoices immediately upon invoice entry, with configurable tolerance thresholds supporting both percentage-based and absolute-amount-based tolerances (variance passes if either threshold is satisfied).
- **FR-003**: System MUST support intercompany transactions between legal entities organized in a parent-child hierarchy (supporting multi-level consolidation) with automatic reciprocal journal entries in both entities, multi-currency handling, and elimination entries at each consolidation level.
- **FR-004**: System MUST support FIFO and LIFO inventory costing methods per product/warehouse in addition to existing WAC, including cost layer tracking, sales return handling, costing method change revaluation, and prevention of negative inventory by default (sales are blocked when available stock is insufficient).

**Tier 2 — Competitive Parity (P2)**

- **FR-005**: System MUST generate cash flow forecasts based on AR aging, AP aging, recurring entries, and historical payment patterns, with projections per bank account and consolidated totals.
- **FR-006**: System MUST provide an employee self-service portal for leave requests (with balance tracking), payslip viewing, personal profile updates, and manager approval workflows.
- **FR-007**: System MUST provide a mobile application for core operations (inventory view, quotations, order entry, and workflow approvals) with offline capability and automatic sync with conflict detection.
- **FR-008**: System MUST support subscription billing with plan management, configurable trial periods with auto-conversion to paid, automated recurring invoice generation, mid-cycle proration for plan changes, cancellation handling, and failed payment retry logic.
- **FR-009**: System MUST support embedded analytics dashboards with pre-built KPIs for finance, sales, inventory, and operations, including date range filtering, branch-level access control, and near-real-time data refresh.

**Cross-Cutting**

- **FR-019**: System MUST provide a unified notification service supporting email, in-app, and mobile push channels, with user-configurable preferences per channel and event type. All features requiring notifications (self-service, subscriptions, performance reviews, workflow approvals, campaigns, shop floor alerts) MUST route through this service.

**Tier 3 — Market Differentiation (P3)**

- **FR-010**: System MUST support blanket purchase orders with agreement terms (quantity, price, validity period), release order creation against the agreement, and remaining quantity/budget tracking.
- **FR-011**: System MUST support marketing campaign management with customer segmentation, campaign execution (email/SMS), engagement tracking (delivery, open, click, response), and lead-to-campaign attribution.
- **FR-012**: System MUST support structured performance reviews with configurable review cycles, goal setting, employee self-assessment, manager evaluation, composite scoring, and deadline reminders.
- **FR-013**: System MUST support CPQ (Configure Price Quote) with guided product configuration, combination validation rules, tiered/rule-based pricing, discount application, and professional quote document generation.
- **FR-014**: System MUST generate statistical demand forecasts based on historical sales data with seasonality detection, confidence intervals, and manual adjustment capability.
- **FR-015**: System MUST support shop floor control with real-time work order progress tracking by operation/station, time-per-operation reporting, delay alerts, and a supervisor dashboard.
- **FR-016**: System MUST support production routings with operation sequences, work centers, setup/run times, labor cost calculation, and alternative routing selection.
- **FR-017**: System MUST support project time tracking with timesheet entry, billable/non-billable classification, manager approval, and project profitability reporting.
- **FR-018**: System MUST support resource capacity planning with team member allocation across projects, availability calendar, over-allocation warnings, and capacity filtering.

### Key Entities

- **SSO Configuration**: Identity provider type (SAML/LDAP), connection details, group-to-role mappings, fallback admin accounts.
- **3-Way Match Record**: PO reference, GRN reference(s), invoice reference, line-level quantity/price variances, tolerance applied (% and absolute), match status (matched/held/approved with exception).
- **Entity Group**: Parent entity, child entities (recursive parent-child tree), consolidation level, group currency.
- **Intercompany Transaction**: Source entity, target entity, transaction type, amounts per entity (with currency), reciprocal journal entry references, elimination status, consolidation level.
- **Cost Layer** (FIFO/LIFO): Product, warehouse, purchase date, quantity remaining, unit cost, source document reference.
- **Cash Flow Forecast**: Forecast date, horizon period, projected inflows (by source), projected outflows (by source), bank account, projected balance.
- **Self-Service Request**: Employee, request type (leave/profile update), details, status, approver, timestamps.
- **Subscription Plan**: Name, billing frequency (monthly/quarterly/annual), base amount, currency, start/end dates, auto-renewal flag, trial period duration (days, 0 = no trial).
- **Subscription Enrollment**: Customer, plan, enrollment date, trial end date (if applicable), next billing date, status (trial/active/paused/cancelled/at-risk), payment history.
- **BI Dashboard**: Name, widget definitions (KPI type, data source, filters), access roles, refresh interval.
- **Blanket Purchase Order**: Supplier, total quantity, unit price, validity period, released quantity/amount, remaining balance, status.
- **Campaign**: Name, type (email/SMS), target segment, execution date, content, engagement metrics, attributed leads, cost.
- **Review Cycle**: Name, period, eligible employees, deadline, status (draft/active/completed).
- **Performance Review**: Employee, reviewer, cycle, goals, self-assessment scores, manager scores, composite rating, status.
- **Product Configuration**: Product, available options (grouped), validation rules (allowed/blocked combinations), pricing rules.
- **Quote (CPQ)**: Customer, configured line items, applied pricing rules, discounts, total, PDF document reference.
- **Demand Forecast**: Product, forecast period, method used, projected quantity, confidence interval, manual adjustments.
- **Shop Floor Log**: Work order, operation sequence, station/work center, operator, start/end time, status, output quantity.
- **Routing**: Name, product/BOM reference, operation list (sequence, work center, setup time, run time per unit, labor rate).
- **Timesheet Entry**: Employee, project, task, date, hours, billable flag, rate, status (draft/submitted/approved/rejected).
- **Resource Allocation**: Employee, project, allocation percentage, start/end date, role.
- **Notification**: Recipient, channel (email/in-app/push), event type, feature source, content, status (pending/sent/read), timestamp.
- **Notification Preference**: User, event type, channel toggles (email on/off, in-app on/off, push on/off).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users authenticate via SSO/LDAP within 3 seconds, with automatic role assignment. New user provisioning requires zero manual steps.
- **SC-002**: 3-way matching processes 95% of standard invoices automatically, reducing manual matching effort by 80%.
- **SC-003**: Intercompany elimination entries balance to zero in 100% of consolidation runs.
- **SC-004**: FIFO/LIFO costing calculations match manual verification for 100% of test transactions across purchases, sales, and returns.
- **SC-005**: Cash flow forecast accuracy is within 15% of actuals over a 30-day horizon.
- **SC-006**: Employee self-service reduces HR-handled leave and payslip requests by 70%.
- **SC-007**: Mobile app users complete core tasks (view inventory, create quotation, approve workflow) in under 60 seconds.
- **SC-008**: Subscription billing generates 100% of recurring invoices on schedule with correct proration.
- **SC-009**: BI dashboards load within 5 seconds and reflect data no older than 15 minutes.
- **SC-010**: Blanket PO releases are tracked with 100% accuracy against agreement terms.
- **SC-011**: Campaign engagement metrics (opens, clicks) are tracked for 95%+ of delivered messages.
- **SC-012**: 90% of performance reviews are completed within the configured deadline when reminders are active.
- **SC-013**: CPQ blocks 100% of invalid product configurations and applies correct pricing rules.
- **SC-014**: Demand forecast is generated in under 30 seconds for any product with 12+ months of history.
- **SC-015**: Shop floor dashboard updates within 30 seconds of an operator reporting progress.
- **SC-016**: Routing-based labor cost calculations match manual verification for 100% of test work orders.
- **SC-017**: 95% of timesheet entries are submitted and approved within the same week.
- **SC-018**: Resource over-allocation warnings fire for 100% of assignments exceeding 100% capacity.

## Clarifications

### Session 2026-04-02

- Q: Should intercompany entities be structured as a flat group or parent-child hierarchy? → A: Parent-child tree for multi-level consolidation
- Q: Should notifications be unified or per-feature? → A: Unified notification service with email, in-app, and mobile push channels across all features
- Q: Should FIFO/LIFO allow or prevent negative inventory by default? → A: Prevent by default — block sales that would cause negative inventory
- Q: When should 3-way matching be triggered? → A: Automatically upon supplier invoice entry
- Q: Should subscription billing support free trial periods? → A: Yes, configurable trial period per plan with auto-conversion to paid

## Assumptions

- AMAN's existing authentication system will remain available as a fallback for admin accounts; SSO/LDAP extends rather than replaces it.
- The organization has an existing LDAP/Active Directory or SAML 2.0 identity provider; AMAN does not provide the identity provider itself.
- 3-way matching tolerances are configured at the organization level with optional overrides per supplier or product category.
- Intercompany accounting uses a parent-child entity hierarchy supporting multi-level consolidation (e.g., Holding > Region > Subsidiary). All entities within a group share the same base chart of accounts structure (with entity-specific segments allowed).
- FIFO/LIFO cost layers are tracked from the date the new costing method is applied; historical purchases before the change date are consolidated into an opening layer.
- Cash flow forecasting uses statistical methods (moving average, exponential smoothing) based on historical payment patterns; no ML infrastructure is required.
- The mobile app targets iOS and Android and shares business logic with the web frontend where feasible.
- Subscription billing handles invoicing only; payment collection/gateway integration is out of scope for v1 (invoices are created; payment is recorded manually or via existing payment flows).
- BI dashboards use an embedded analytics approach rather than building a custom analytics engine from scratch.
- Campaign email/SMS delivery requires integration with an external messaging provider; AMAN manages campaign logic, segmentation, and tracking but does not operate its own mail/SMS servers.
- CPQ targets configurable products with option-based configuration (not engineer-to-order custom manufacturing).
- Demand forecasting uses statistical methods; integration with external ML platforms is out of scope for v1.
- Shop floor control assumes each work center has access to a device (tablet, terminal) for operators to report progress.
- Time tracking assumes projects and tasks already exist in the AMAN project module.
- Resource planning covers project-level allocation; individual task-level scheduling is out of scope for v1.
- The team size is 3-4 developers, informing the phased delivery plan across tiers.
