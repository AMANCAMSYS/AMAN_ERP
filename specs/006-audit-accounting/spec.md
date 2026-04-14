# Feature Specification: Audit Accounting Module

**Feature Branch**: `006-audit-accounting`  
**Created**: 2026-04-14  
**Status**: Draft  
**Input**: User description: "فحص شامل لوحدة المحاسبة والقيود — دليل الحسابات، القيود اليومية، التقارير المالية، الموازنات، العملات، القفل المالي، القيود المتكررة، مراكز التكلفة، المعاملات بين الشركات"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Double-Entry Journal Entry Lifecycle (Priority: P1)

An accountant creates, reviews, and posts a journal entry. The system enforces the double-entry principle: total debits must equal total credits. All amounts are processed with decimal precision (never floating-point arithmetic). Posted entries update account balances atomically. Draft entries can be edited; posted entries are immutable (corrections require reversing entries). Every journal entry receives a unique sequential number that never duplicates, even under concurrent posting.

**Why this priority**: Journal entries are the foundational transaction of the entire accounting system. Every other module (sales, purchases, treasury, payroll, inventory) ultimately produces journal entries. Any defect here corrupts all financial data.

**Independent Test**: Can be tested by creating journal entries with various line combinations, posting them, and verifying account balances match the expected debit/credit sums calculated independently.

**Acceptance Scenarios**:

1. **Given** an accountant with `accounting.edit` permission, **When** they create a journal entry with 2+ lines where total debits equal total credits, **Then** the entry is saved with a unique sequential number and status "draft".
2. **Given** a draft journal entry, **When** the accountant posts it, **Then** all referenced account balances are updated atomically using decimal arithmetic with `ROUND_HALF_UP` to 2 decimal places.
3. **Given** a journal entry where debits ≠ credits, **When** submitted, **Then** the system rejects it with a clear Arabic error message specifying the imbalance amount.
4. **Given** a journal entry with a negative debit or credit amount, **When** submitted, **Then** the system rejects it — negative amounts are never permitted.
5. **Given** a journal entry with fewer than 2 lines, **When** submitted, **Then** the system rejects it — every entry requires at least one debit and one credit line.
6. **Given** a posted journal entry, **When** the accountant attempts to edit it, **Then** the system prevents modification and guides the user to create a reversing entry instead.
7. **Given** 50 concurrent users posting journal entries simultaneously, **When** all posts complete, **Then** every entry has a unique sequential number with no duplicates (gaps from rollbacks are acceptable per Constitution XXIII; duplicates are not).
8. **Given** any journal entry operation, **When** successful, **Then** an audit log entry is written with the user, action, entry number, and affected accounts.

---

### User Story 2 - Fiscal Period Locking Enforcement (Priority: P1)

A financial controller locks a fiscal period (month/quarter/year) to prevent any further postings. Once locked, no journal entry — manual or auto-generated from any module — can be posted to that period. The lock can be undone only by an authorized user, and both lock and unlock actions produce audit trail entries.

**Why this priority**: Fiscal period locking is a compliance and audit requirement. Retroactive changes to closed periods corrupt financial statements and violate accounting standards (SOCPA/IFRS).

**Independent Test**: Can be tested by locking a period, attempting to post an entry dated within that period from multiple modules, and verifying all attempts are rejected.

**Acceptance Scenarios**:

1. **Given** a financial controller with appropriate permission, **When** they lock a fiscal period, **Then** the period status changes to "locked", the action is recorded with timestamp, user, and reason.
2. **Given** a locked fiscal period, **When** any user attempts to post a journal entry dated within that period, **Then** the system rejects the posting with a clear Arabic error identifying the locked period.
3. **Given** a locked period, **When** an auto-generated journal entry from sales/purchases/payroll/treasury/inventory targets that period, **Then** the posting is rejected — fiscal lock applies uniformly to all sources.
4. **Given** a locked period, **When** an authorized user unlocks it, **Then** the unlock action is recorded with reason, and postings to that period are again permitted.
5. **Given** a fiscal lock check, **When** the `fiscal_period_locks` table does not yet exist, **Then** the system degrades gracefully (allows posting) rather than crashing.

---

### User Story 3 - Chart of Accounts Management (Priority: P1)

A company admin manages the chart of accounts (COA): creating accounts, organizing them in a hierarchy (parent-child), tagging them by module, and ensuring the COA follows SOCPA/IFRS conventions (1xxxx = Assets, 2xxxx = Liabilities, 3xxxx = Equity, 4xxxx = Revenue, 5xxxx = Expenses). During company onboarding, industry-specific account templates are seeded automatically. Accounts with posted transactions cannot be deleted.

**Why this priority**: The chart of accounts is the structural backbone of every financial report. Incorrect hierarchy or missing accounts render trial balance, balance sheet, and income statement unreliable.

**Independent Test**: Can be tested by creating a company with a specific industry, verifying the seeded accounts match the expected template, then performing CRUD operations and checking hierarchy integrity.

**Acceptance Scenarios**:

1. **Given** a new company with industry type "retail", **When** the COA is seeded, **Then** the system creates all core accounts (SOCPA/IFRS structure) plus retail-specific accounts (POS sales, inventory variance, spoilage).
2. **Given** an admin creating a new account, **When** they assign a parent account, **Then** the new account is positioned correctly in the hierarchy and inherits the parent's account type (asset/liability/equity/revenue/expense).
3. **Given** an account with posted journal lines, **When** an admin attempts to delete it, **Then** the system prevents deletion with a clear message listing the number of dependent transactions.
4. **Given** a chart of accounts query, **When** executed, **Then** each account's live balance is computed by aggregating its journal lines (debits − credits for asset/expense accounts; credits − debits for liability/equity/revenue accounts).
5. **Given** any COA operations, **When** completed, **Then** the system invalidates relevant caches and logs the activity for audit trails.

---

### User Story 4 - Multi-Currency Journal Entries & Currency Management (Priority: P1)

An accountant creates journal entries in foreign currencies. The system maintains exchange rates, converts amounts to the base currency using the rate at the transaction date, and tracks both the original currency amount and the base currency equivalent on each journal line. The system enforces that exactly one currency is designated as the base currency and validates ISO 4217 currency codes.

**Why this priority**: Multi-currency transactions are essential for international trade. Incorrect exchange rate application or base currency confusion produces material financial misstatements.

**Independent Test**: Can be tested by creating journal entries in multiple currencies, verifying the base currency conversion at each entry's exchange rate, and checking that currency balances and base balances reconcile.

**Acceptance Scenarios**:

1. **Given** a journal entry in USD (non-base currency) with exchange rate 3.75, **When** posted, **Then** each line stores both the original USD amount and the SAR equivalent (amount × 3.75), and account balances are updated in both currencies.
2. **Given** a currency creation request with an invalid code (e.g., "ABCD" or "12"), **When** submitted, **Then** the system rejects it — only 3-letter uppercase ISO 4217 codes are accepted.
3. **Given** an attempt to set two currencies as base, **When** submitted, **Then** the system enforces the constraint that exactly one currency can be the base, and the base currency's exchange rate is always 1.0.
4. **Given** a company without a currencies table, **When** the currencies endpoint is accessed, **Then** the system auto-provisions the table and seeds the company's base currency from the system database.
5. **Given** exchange rate updates, **When** a rate is set to zero or negative, **Then** the system rejects it — exchange rates must be positive.

---

### User Story 5 - Budget Management & Over-Budget Controls (Priority: P2)

A financial controller creates budgets tied to accounts and fiscal periods. Budget line items define planned amounts per account. The system tracks actuals against budget and alerts users when spending approaches or exceeds the budgeted amount. Active budgets cannot be deleted.

**Why this priority**: Budget controls prevent overspending and are a management reporting requirement. Per Constitution I, budgets MUST be enforced at journal entry posting time — budget overruns MUST block the transaction or require explicit approval before proceeding.

**Independent Test**: Can be tested by creating a budget, posting transactions to budgeted accounts, and verifying that budget vs. actual comparisons are accurate and over-budget conditions are flagged.

**Acceptance Scenarios**:

1. **Given** a financial controller with `accounting.budgets.manage` permission, **When** they create a budget with line items, **Then** each item is linked to an account and records the planned amount.
2. **Given** an existing budget item for an account, **When** a new budget item is submitted for the same account, **Then** the system upserts (updates the existing item rather than creating a duplicate).
3. **Given** an active budget, **When** an admin attempts to delete it, **Then** the system prevents deletion with an explanation that the budget is active.
4. **Given** budget line items and posted journal entries, **When** a budget report is requested, **Then** the actual amounts are computed from journal lines and compared against budgeted amounts with variance calculations.
5. **Given** a module gating requirement, **When** the "budgets" module is not enabled for the company, **Then** all budget endpoints return a module-not-enabled error.
6. **Given** a journal entry posting that would cause any budgeted account to exceed its planned amount, **When** the entry is submitted, **Then** the system blocks the posting with an over-budget error — unless the user has `accounting.budgets.override` permission and explicitly confirms the override, which is logged in the audit trail.

---

### User Story 6 - Cost Center Tracking (Priority: P2)

An accountant assigns cost centers to journal entry lines for departmental expense tracking. Cost centers are managed with unique codes, and the system prevents deletion of cost centers in use. Reports can be filtered or grouped by cost center for management accounting.

**Why this priority**: Cost center tracking is essential for management accounting and profitability analysis by department/project, but it is supplementary to core GL operations.

**Independent Test**: Can be tested by creating cost centers, assigning them to journal lines, and verifying that cost center reports aggregate correctly and deletion protection works.

**Acceptance Scenarios**:

1. **Given** an admin creating a cost center, **When** they submit a code that already exists, **Then** the system rejects it with a duplicate code error.
2. **Given** a cost center assigned to journal lines, **When** an admin attempts to delete it, **Then** the system prevents deletion indicating the number of journal lines using it.
3. **Given** a cost center update with a code that conflicts with another center, **When** submitted, **Then** the system rejects the change without modifying the record.
4. **Given** journal entries with cost center assignments, **When** a cost center report is requested, **Then** amounts are correctly aggregated per cost center.

---

### User Story 7 - Intercompany Transactions & Consolidation (Priority: P2)

A group accountant creates intercompany transactions between related entities. The system automatically creates reciprocal journal entries in both the source and target entities: the source records an intercompany receivable, and the target records an intercompany payable. During consolidation, elimination entries net out intercompany balances. Account mappings define which GL accounts to use for each entity pair.

**Why this priority**: Intercompany transactions are critical for corporate groups. Incorrect reciprocal entries or failed eliminations produce materially misstated consolidated financials.

**Independent Test**: Can be tested by creating an intercompany transaction, verifying both reciprocal journal entries exist with correct amounts, and running consolidation to verify elimination entries balance to zero.

**Acceptance Scenarios**:

1. **Given** a group accountant creating an intercompany transaction between Entity A and Entity B, **When** submitted, **Then** the system creates a source JE (Dr IC Receivable, Cr Revenue) in Entity A and a target JE (Dr Expense, Cr IC Payable) in Entity B — both atomically committed.
2. **Given** entities with different base currencies, **When** an intercompany transaction is created, **Then** the target JE is posted at the exchange rate specified, with currency amounts tracked correctly.
3. **Given** intercompany account mappings for an entity pair, **When** a transaction is processed, **Then** the mapped accounts are used; if no mapping exists, the system defaults to account ranges (13xx for receivables, 21xx for payables).
4. **Given** outstanding intercompany balances, **When** consolidation is run, **Then** elimination entries are generated that net intercompany receivables and payables to zero.
5. **Given** an entity group hierarchy, **When** entities are queried, **Then** the system returns the correct parent-child tree with consolidation levels.
6. **Given** intercompany v1 and v2 both exist, **When** auditing, **Then** verify that v2 (with reciprocal posting) is the recommended path and v1 (single-sided) is deprecated.

---

### User Story 8 - Financial Report Accuracy (Priority: P1)

An accountant generates financial reports: trial balance, balance sheet, income statement, and cash flow report. Every report draws from posted journal entries and must mathematically reconcile. The trial balance total debits must equal total credits. The balance sheet must balance (Assets = Liabilities + Equity). Reports are scoped to the user's company and optionally filtered by branch and date range.

**Why this priority**: Financial reports are the primary output of the accounting system. If they do not balance or contain incorrect figures, the system is fundamentally broken.

**Independent Test**: Can be tested by posting a known set of journal entries, generating each report, and verifying the figures match hand-calculated expected values.

**Acceptance Scenarios**:

1. **Given** posted journal entries, **When** a trial balance is generated, **Then** total debits equal total credits across all accounts.
2. **Given** posted journal entries, **When** a balance sheet is generated, **Then** total Assets = total Liabilities + total Equity.
3. **Given** a branch filter, **When** a report is generated, **Then** only journal lines from the specified branch are included.
4. **Given** a date range filter, **When** a report is generated, **Then** only entries within the specified date range are included, and opening balances reflect all prior periods.
5. **Given** a company with zero transactions, **When** a report is generated, **Then** the system returns a valid empty-state report without errors.

---

### User Story 9 - Costing Policy Management (Priority: P2)

A financial controller selects and switches the inventory costing method (global weighted average, per-warehouse weighted average, hybrid, or smart). Switching policies triggers an impact analysis showing affected products and total cost variance. A complete history of policy changes is maintained with before/after metrics.

**Why this priority**: Costing policy determines how inventory is valued and how COGS is calculated. Mid-period switches require careful recalculation.

**Independent Test**: Can be tested by switching between costing policies, verifying the impact analysis output, checking that the history log is accurate, and confirming inventory valuations adjust to the new method.

**Acceptance Scenarios**:

1. **Given** a company using "global_wac" policy, **When** the controller queries the current policy, **Then** the active policy details are returned.
2. **Given** a request to switch from "global_wac" to "per_warehouse_wac", **When** submitted, **Then** the system performs an impact analysis (affected products count, total cost impact) before applying the change.
3. **Given** a successful policy switch, **When** completed, **Then** the old policy is deactivated, the new policy is activated, a snapshot is created, and the change is logged in history.
4. **Given** the costing policy history endpoint, **When** queried, **Then** all past policy changes are returned with timestamps, old/new policy, affected product count, and total cost impact.

---

### User Story 10 - Balance Reconciliation & Integrity Verification (Priority: P2)

A financial controller runs balance reconciliation to verify that account balances stored in the `accounts` table match the actual sum of posted journal lines. The system also reconciles treasury account balances against their linked GL accounts. Discrepancies beyond a 0.01 tolerance threshold are flagged for investigation.

**Why this priority**: Balance drift (stored balance diverging from actual journal totals) indicates a system defect — possibly a failed update, race condition, or data corruption. Early detection prevents cascading errors.

**Independent Test**: Can be tested by intentionally introducing a 0.02 discrepancy between an account's stored balance and its journal line totals, then running reconciliation and verifying the discrepancy is flagged.

**Acceptance Scenarios**:

1. **Given** account balances and posted journal lines, **When** reconciliation is run, **Then** for each account, the stored balance is compared against SUM(debits) − SUM(credits) (or vice versa by account type) from journal lines.
2. **Given** a discrepancy greater than 0.01, **When** detected, **Then** the account is flagged with the expected balance, stored balance, and delta.
3. **Given** treasury accounts linked to GL accounts, **When** treasury reconciliation is run, **Then** each treasury balance is compared against its linked GL account balance.
4. **Given** all accounts are in balance, **When** reconciliation completes, **Then** the report confirms zero discrepancies.

---

### User Story 11 - Approval Workflow for Journal Entries (Priority: P3)

High-value or sensitive journal entries follow an approval workflow with configurable SLA, escalation rules, and auto-approve thresholds. Overdue approvals trigger escalation to designated users. Approval analytics track average processing time and bottlenecks.

**Why this priority**: Approval workflows add a control layer but are supplementary to core posting mechanics. They matter most for compliance and internal controls.

**Independent Test**: Can be tested by submitting a journal entry requiring approval, letting the SLA expire, and verifying escalation triggers correctly.

**Acceptance Scenarios**:

1. **Given** a workflow with SLA of 24 hours, **When** an approval request has been pending for 25 hours, **Then** the escalation check promotes it to the designated escalation user.
2. **Given** a workflow with auto-approve threshold of 10,000, **When** a journal entry for 5,000 is submitted, **Then** it is automatically approved without human intervention.
3. **Given** approval analytics, **When** queried, **Then** the system returns pending count, approved count, rejected count, and average processing hours.

---

### User Story 12 - Recurring Journal Templates (Priority: P3)

An accountant creates recurring journal entry templates for transactions that repeat at regular intervals (monthly rent, depreciation, amortization). The system generates journal entries from these templates on schedule, respecting fiscal period locks.

**Why this priority**: Recurring entries automate routine accounting tasks. Important for efficiency but can be performed manually if the feature is unavailable.

**Independent Test**: Can be tested by creating a recurring template, triggering the generation cycle, and verifying the produced journal entry has the correct accounts, amounts, and date.

**Acceptance Scenarios**:

1. **Given** a recurring template with monthly frequency, **When** the generation cycle runs, **Then** a journal entry is created with the template's accounts and amounts, dated to the current period.
2. **Given** a recurring template targeting a locked fiscal period, **When** the generation cycle runs, **Then** the entry is not created, and a warning is logged indicating the locked period.
3. **Given** a recurring template, **When** the generation cycle has already run for the current period, **Then** the system does not create a duplicate entry.

---

### Edge Cases

- What happens when an account is referenced in a journal entry line but the account has been deleted between validation and posting?
  > **Triage**: Use `SELECT ... FOR UPDATE` on the account row during posting to prevent concurrent deletion. Reject with "account not found" if missing.
- How does the system handle a journal entry with lines in multiple currencies (mixed-currency entry)?
  > **Triage**: Each line stores its own currency and base-currency equivalent. The JE header currency is informational; the debit=credit balance check uses base-currency amounts.
- What happens when two users post journal entries simultaneously that both update the same account's balance?
  > **Triage**: `update_account_balance()` uses `UPDATE ... SET balance = balance + :delta` (atomic increment) within the posting transaction. No read-modify-write race.
- How does the system recover if a crash occurs mid-posting — after the JE is inserted but before account balances are updated?
  > **Triage**: The entire posting (JE insert + balance updates) is in a single DB transaction. A crash causes a rollback — no partial state.
- What happens when the trial balance does not balance (indicating a system bug)?
  > **Triage**: The `trg_journal_balance` trigger prevents this at the DB level. The balance reconciliation endpoint (FR-019) detects and flags discrepancies beyond 0.01 tolerance.
- How does the system handle extremely large journal entries (1,000+ lines)?
  > **Triage**: No hard limit, but batch insert with `executemany()`. Performance benchmark target: 1,000-line JE posts within 5 seconds.
- What happens when intercompany transactions reference an entity whose database is unreachable?
  > **Triage**: The cross-database posting fails atomically. Neither the source nor target JE is committed. The user receives an error indicating the target entity is unavailable.
- How does the system behave when fiscal years overlap?
  > **Triage**: Fiscal period locks are date-range based, not fiscal-year based. Overlapping ranges are permitted; the lock check tests whether the JE date falls within ANY locked range.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST enforce double-entry accounting: total debits MUST equal total credits on every journal entry. Entries with an imbalance MUST be rejected with the imbalance amount shown in the error.
- **FR-002**: System MUST use decimal arithmetic (never floating-point) for all financial calculations — amounts, balances, exchange rate conversions, and variance computations. All monetary amounts MUST be stored with 4 decimal places (`NUMERIC(18,4)`) and rounded to 2 decimal places (`ROUND_HALF_UP`) for display. Display-layer float serialization is acceptable only for JSON responses, never for intermediate calculations.
- **FR-003**: System MUST prevent posting journal entries to locked fiscal periods — this applies uniformly to manual entries and auto-generated entries from all sub-ledgers (sales, purchases, treasury, payroll, inventory, assets).
- **FR-004**: System MUST assign unique, sequential entry numbers to journal entries even under concurrent posting. Gaps caused by rollbacks are acceptable; duplicates are never acceptable (Constitution XXIII).
- **FR-005**: System MUST enforce tenant isolation on every accounting operation — a user from Company A MUST never read, write, or infer Company B's accounting data.
- **FR-006**: System MUST update account balances atomically when a journal entry is posted, using the correct balance formula per account type (debit − credit for asset/expense; credit − debit for liability/equity/revenue).
- **FR-007**: System MUST validate ISO 4217 currency codes (3 uppercase letters) and enforce exactly one base currency per company with a fixed exchange rate of 1.0.
- **FR-008**: System MUST support multi-currency journal entries, storing both the original currency amount and the base currency equivalent on each line.
- **FR-009**: System MUST seed industry-specific chart of accounts templates during company onboarding, following SOCPA/IFRS account numbering conventions.
- **FR-010**: System MUST prevent deletion of accounts that have posted journal lines.
- **FR-011**: System MUST enforce budget item uniqueness per account via upsert logic — no duplicate budget items for the same account within a budget.
- **FR-012**: System MUST prevent deletion of active budgets and cost centers in use.
- **FR-025**: System MUST enforce budget limits at journal entry posting time — if posting would cause any budgeted account to exceed its planned amount, the system MUST block the transaction unless the user holds `accounting.budgets.override` permission and explicitly confirms the override (Constitution I).
- **FR-013**: System MUST create reciprocal journal entries for intercompany transactions — source entity records receivable, target entity records payable — committed atomically.
- **FR-014**: System MUST generate elimination entries during consolidation that net intercompany balances to zero.
- **FR-015**: System MUST validate all journal entry lines: reject negative amounts, require account IDs, and require a minimum of 2 lines.
- **FR-016**: System MUST compute live account balances by aggregating journal lines rather than relying solely on cached/stored balance fields.
- **FR-017**: System MUST record an audit log entry for every financial state change: journal entry creation/posting, account creation/deletion, budget creation/deletion, cost center changes, fiscal lock/unlock, costing policy switch.
- **FR-018**: System MUST validate exchange rates are positive (> 0) before accepting currency rate updates.
- **FR-019**: System MUST support balance reconciliation that compares stored account balances against computed journal line totals, flagging discrepancies beyond 0.01 tolerance.
- **FR-020**: System MUST use parameterized SQL queries for all database operations — no string concatenation with user input.
- **FR-021**: System MUST return generic Arabic error messages for all financial operations — no internal details, SQL fragments, or stack traces.
- **FR-022**: System MUST enforce permission checks (`accounting.view`, `accounting.edit`, `accounting.budgets.manage`, `accounting.budgets.view`) on all accounting endpoints.
- **FR-023**: System MUST validate branch access on branch-scoped operations — a user assigned to Branch A cannot query or post to Branch B's data.
- **FR-024**: System MUST log fiscal period lock and unlock actions with the user, timestamp, and reason for audit compliance.

### Key Entities

- **Account**: A node in the chart of accounts. Key attributes: account code, name (Arabic/English), account type (asset/liability/equity/revenue/expense), parent account, balance, currency balance, is_active, module tags.
- **Journal Entry**: A double-entry accounting transaction. Key attributes: entry number, entry date, description, status (draft/posted), currency, exchange rate, source (manual/sales/purchases/treasury/payroll), source_id, branch_id, created_by.
- **Journal Line**: A single debit or credit within a journal entry. Key attributes: account_id, debit amount, credit amount, cost_center_id, currency amount, description.
- **Fiscal Period Lock**: A record preventing postings to a date range. Key attributes: period name, start date, end date, is_locked, locked_by, locked_at, unlocked_at, reason.
- **Budget**: A financial plan for a period. Key attributes: name, fiscal year, status (active/closed), created_by.
- **Budget Item**: A planned amount for a specific account within a budget. Key attributes: budget_id, account_id, planned_amount, period.
- **Cost Center**: A department or unit for expense allocation. Key attributes: code, name, description, is_active.
- **Currency**: A monetary unit with exchange rate. Key attributes: code (ISO 4217), name, exchange_rate, is_base, decimal_places.
- **Intercompany Transaction**: A transaction between related entities. Key attributes: source_entity, target_entity, amount, currency, exchange_rate, source_je_id, target_je_id, status, elimination_status.
- **Entity Group**: A node in the corporate group hierarchy. Key attributes: entity code, name, parent_id, consolidation_level, company_id.
- **Costing Policy**: The active inventory valuation method. Key attributes: policy_type (global_wac/per_warehouse_wac/hybrid/smart), is_active, activated_at, deactivated_at, snapshot.
- **Recurring Journal Template**: A repeatable journal entry configuration. Key attributes: template name, frequency, accounts, amounts, last_generated_date, is_active.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of journal entries enforce debit = credit — no unbalanced entries can be posted.
- **SC-002**: All financial calculations use decimal arithmetic — zero instances of float-based math in balance updates, exchange rate conversions, or variance computations.
- **SC-003**: Fiscal period lock is enforced across all posting sources (manual, sales, purchases, treasury, payroll, inventory, assets) — zero entries posted to locked periods.
- **SC-004**: Sequential entry numbering produces zero duplicates under concurrent posting by 50+ users.
- **SC-005**: Tenant isolation verified — zero cross-tenant data access across all accounting endpoints.
- **SC-006**: Trial balance total debits equal total credits for every company at any point in time.
- **SC-007**: Balance sheet equation holds (Assets = Liabilities + Equity) for every company at any point in time.
- **SC-008**: Balance reconciliation detects 100% of discrepancies greater than 0.01 between stored and computed balances.
- **SC-009**: Industry-specific COA templates produce the correct accounts for all supported industries (retail, wholesale, restaurant, manufacturing, construction, services, pharmacy, workshop).
- **SC-010**: Intercompany reciprocal entries balance: source receivable = target payable for every transaction.
- **SC-011**: Consolidation elimination entries net intercompany balances to zero.
- **SC-012**: All accounting endpoints enforce permission checks — unauthorized users receive 403 with no data leakage.
- **SC-013**: All SQL queries use parameterized statements — zero string-concatenation SQL injection vectors detected.
- **SC-014**: All error responses contain generic Arabic messages — zero instances of stack traces, SQL fragments, or internal paths in user-facing errors.
- **SC-015**: Every financial state change produces an audit log entry — zero gaps across all tested operations.

## Assumptions

- The `audit-auth-security` (Speckit 1) and `audit-core-admin` (Speckit 2) modules have been completed and their fixes are in place — authentication, authorization, tenant isolation in auth, error sanitization, and audit logging infrastructure are functional.
- The system uses PostgreSQL with database-per-tenant isolation (`aman_{company_id}` pattern) and a shared `aman_system` database.
- The GL service (`gl_service.py`) is the centralized entry point for creating journal entries from all sub-ledgers — sales, purchases, treasury, payroll, inventory, and assets all call through this service.
- Decimal precision follows `Decimal("0.01")` quantization with `ROUND_HALF_UP` rounding — 2 decimal places for standard currencies unless company settings specify otherwise.
- The chart of accounts follows SOCPA/IFRS numbering conventions: 1xxxx = Assets, 2xxxx = Liabilities, 3xxxx = Equity, 4xxxx = Revenue, 5xxxx = Expenses.
- Float serialization in JSON API responses is acceptable for display purposes — the audit verifies that no float arithmetic is used in balance calculations or financial processing.
- Intercompany v1 (single-sided) is considered deprecated; v2 (reciprocal) is the recommended implementation. The audit examines both but focuses validation on v2.
- Arabic is the primary language for all user-facing messages; English is used in internal logs and developer documentation.
- Redis is available for caching (account balance cache, dashboard metrics) but is not used for transactional financial data.
- The approval workflow for journal entries uses the shared `advanced_workflow.py` router — the audit verifies its integration with accounting but does not re-audit the workflow engine itself.
