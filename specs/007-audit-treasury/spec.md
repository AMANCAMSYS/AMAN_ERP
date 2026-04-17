# Feature Specification: audit-treasury — الخزينة والبنوك

**Feature Branch**: `007-audit-treasury`  
**Created**: 2026-04-14  
**Status**: Draft  
**Input**: User description: "Comprehensive audit of treasury and banking module: bank accounts, reconciliation, transfers, checks, promissory notes, and cash flow"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Treasury Account Management & GL Integrity (Priority: P1)

A finance manager creates and manages treasury accounts (cash and bank) for the company. Each treasury account is automatically linked to a corresponding general ledger account. The manager sets opening balances, updates account details, and deactivates accounts that are no longer needed. The system ensures that the treasury account balance always matches the linked GL account balance.

**Why this priority**: Treasury accounts are the foundation of the entire module — every transaction (transfers, checks, notes, reconciliation) depends on correctly configured treasury accounts with reliable GL linkage. Data integrity here prevents cascading errors across the entire financial system.

**Independent Test**: Can be fully tested by creating a treasury account with an opening balance, verifying the GL account is auto-created, confirming the opening balance journal entry posts correctly, and verifying that the balance in the treasury account matches the GL balance.

**Acceptance Scenarios**:

1. **Given** a company with an established chart of accounts, **When** the user creates a new bank treasury account with an opening balance of 50,000, **Then** the system creates a GL account under the Cash & Equivalents parent, posts a balanced opening balance journal entry, and the treasury balance equals 50,000.
2. **Given** a treasury account with a non-zero balance, **When** the user attempts to delete the account, **Then** the system prevents deletion and displays a clear message explaining the account has an existing balance.
3. **Given** a treasury account linked to a GL account, **When** transactions are posted against it, **Then** the treasury `current_balance` and the GL `accounts.balance` remain synchronized at all times.
4. **Given** a company with multiple currencies, **When** the user creates a USD treasury account with an exchange rate, **Then** the GL entry correctly reflects the converted amount in the base currency, and the stored exchange rate is preserved for audit.

---

### User Story 2 - Expense and Transfer Transactions (Priority: P1)

An accountant records expenses paid from a treasury account and transfers funds between treasury accounts. Each transaction generates a proper double-entry journal entry. The system enforces fiscal period locks, validates sufficient balances (when configured), and prevents posting to inactive accounts.

**Why this priority**: Expenses and transfers are the most frequent daily treasury operations. Correct GL posting and balance tracking are essential for financial accuracy and regulatory compliance.

**Independent Test**: Can be tested by recording an expense from a bank account, verifying the GL debit/credit entries, then transferring between two accounts and confirming both treasury balances and both GL balances update correctly.

**Acceptance Scenarios**:

1. **Given** a treasury account with a balance of 10,000, **When** the user records an expense of 3,000 against an expense GL account, **Then** the system creates a journal entry (Dr. Expense / Cr. Treasury GL) and reduces the treasury balance to 7,000.
2. **Given** two treasury accounts (Source: 20,000, Target: 5,000), **When** the user transfers 8,000 from Source to Target, **Then** Source balance becomes 12,000, Target balance becomes 13,000, and a balanced GL entry is posted.
3. **Given** a fiscal period that is locked, **When** the user attempts to record an expense or transfer with a transaction date in the locked period, **Then** the system rejects the transaction with a clear error message.
4. **Given** a multi-currency transfer (SAR to USD account), **When** the user enters the exchange rate, **Then** the GL entry records the correct amounts in both currencies, and the exchange rate is stored in the transaction record for audit.

---

### User Story 3 - Checks Receivable Lifecycle (Priority: P1)

A treasury clerk manages checks received from customers. The clerk records new checks, tracks their due dates, collects checks when they clear, and handles bounced checks. Each state transition generates the correct GL entries to move amounts between Accounts Receivable, Checks Under Collection, and the bank account.

**Why this priority**: Check management is a core banking operation in the Saudi/GCC market. Incorrect GL posting on check state transitions (especially bounces) leads to misstated financial reports and customer balance errors.

**Independent Test**: Can be tested by creating a check receivable, verifying the AR-to-Checks-Under-Collection GL entry, then collecting it and verifying the Checks-Under-Collection-to-Bank GL entry, the treasury balance increase, and that the check status is correctly updated.

**Acceptance Scenarios**:

1. **Given** a customer with an outstanding receivable, **When** the clerk creates a check receivable for 15,000, **Then** the system posts a journal entry (Dr. Checks Under Collection / Cr. AR) and the check status is "pending."
2. **Given** a pending check, **When** the clerk marks it as collected with a collection date and destination bank account, **Then** the system posts (Dr. Bank / Cr. Checks Under Collection), increases the treasury balance, and the check status changes to "collected."
3. **Given** a pending check, **When** the clerk marks it as bounced with a reason, **Then** the system reverses the original entry (Dr. AR / Cr. Checks Under Collection) and the check status changes to "bounced."
4. **Given** a check that was already collected and later bounces, **When** the clerk marks it as bounced, **Then** the system reverses both the collection and original entries (Dr. AR / Cr. Bank) and reduces the treasury balance.
5. **Given** a bounced check receivable, **When** the clerk re-presents it, **Then** the system transitions the check from "bounced" back to "pending," posts a new GL entry (Dr. Checks Under Collection / Cr. AR), and preserves the complete audit trail of all prior state transitions.
6. **Given** a check with a duplicate check number, **When** the clerk attempts to create it, **Then** the system either warns about the duplicate or prevents creation.

---

### User Story 4 - Checks Payable Lifecycle (Priority: P2)

A treasury clerk manages checks issued to suppliers. The clerk records issued checks, tracks clearing, and handles returned (bounced) checks. Each transition generates proper GL entries between Accounts Payable, Checks Payable, and the bank account.

**Why this priority**: Supplier check management is the mirror of receivable checks and is critical for accurate AP reporting and supplier statement reconciliation.

**Independent Test**: Can be tested by creating a check payable, verifying the AP-to-Checks-Payable GL entry, clearing it, and verifying the bank balance reduction.

**Acceptance Scenarios**:

1. **Given** a supplier with an outstanding payable, **When** the clerk creates a check payable for 25,000, **Then** the system posts (Dr. AP / Cr. Checks Payable) and the check status is "issued."
2. **Given** an issued check, **When** the clerk marks it as cleared with a clearance date and bank account, **Then** the system posts (Dr. Checks Payable / Cr. Bank), deducts the treasury balance, and the status becomes "cleared."
3. **Given** an issued check, **When** the clerk marks it as bounced, **Then** the system reverses the original entry and the check status becomes "bounced."
4. **Given** a bounced check payable, **When** the clerk re-presents it, **Then** the system transitions it from "bounced" back to "issued," posts a new GL entry (Dr. AP / Cr. Checks Payable), and preserves the full audit trail.

---

### User Story 5 - Notes Receivable & Payable Lifecycle (Priority: P2)

A treasury clerk manages promissory notes (bills of exchange) received from customers and issued to suppliers. Notes follow a similar lifecycle to checks but include maturity dates and protest (legal rejection) workflows.

**Why this priority**: Notes are commonly used in large commercial transactions and have distinct accounting treatment. Their lifecycle includes protest actions that require accurate GL reversal.

**Independent Test**: Can be tested by creating a note receivable, collecting it at maturity, and verifying the GL entries. Separately, testing the protest flow to confirm the reversal entries.

**Acceptance Scenarios**:

1. **Given** a customer, **When** a note receivable is created, **Then** the system posts (Dr. Notes Receivable / Cr. AR) and the status is "pending."
2. **Given** a pending note receivable at maturity, **When** it is collected, **Then** (Dr. Bank / Cr. Notes Receivable) is posted and the treasury balance increases.
3. **Given** a pending note receivable, **When** it is protested, **Then** (Dr. AR / Cr. Notes Receivable) is posted to reverse the original entry.
4. **Given** a note payable, **When** it is paid at maturity, **Then** (Dr. Notes Payable / Cr. Bank) is posted and the treasury balance decreases.
5. **Given** a note payable, **When** it is protested, **Then** (Dr. Notes Payable / Cr. AP) is posted to reverse the original entry.

---

### User Story 6 - Bank Reconciliation (Priority: P2)

An accountant reconciles the company's bank statement with the GL entries for a specific treasury account. The accountant enters or imports bank statement lines, matches them against GL journal entries (manually or via auto-matching), reviews unmatched items, and finalizes the reconciliation when the difference is zero (within tolerance).

**Why this priority**: Reconciliation is a critical internal control that detects errors, fraud, and timing differences. Unreconciled accounts are a major audit finding.

**Independent Test**: Can be tested by creating a reconciliation, importing a sample bank statement CSV, running auto-match against existing GL entries, verifying the match results, and finalizing the reconciliation.

**Acceptance Scenarios**:

1. **Given** a treasury bank account, **When** the user creates a new reconciliation with start/end balances from the bank statement, **Then** a draft reconciliation is created and no duplicate drafts are allowed for the same account.
2. **Given** a draft reconciliation, **When** the user imports a CSV bank statement file, **Then** the system auto-detects columns (date, description, reference, debit, credit), parses amounts correctly (including Arabic numerals and negative amounts), and displays a preview before confirming import.
3. **Given** imported statement lines and existing GL entries, **When** the user clicks auto-match, **Then** the system matches lines by amount and reference/description, reporting the number of successful matches and leaving unmatched items highlighted.
4. **Given** all items matched and the calculated difference is within tolerance, **When** the user finalizes the reconciliation, **Then** the status changes to "approved" and the reconciliation is locked for editing.
5. **Given** a reconciliation with a non-zero difference exceeding tolerance, **When** the user attempts to finalize, **Then** the system prevents finalization and displays the remaining difference.

---

### User Story 7 - Cash Flow Forecasting (Priority: P3)

A finance manager generates cash flow forecasts based on open receivables (AR), open payables (AP), and recurring journal templates. The forecast shows projected inflows and outflows over a configurable horizon, with a running balance to help anticipate liquidity needs.

**Why this priority**: Forecasting is a planning/decision-support feature that builds on the transactional foundation established by the higher-priority stories.

**Independent Test**: Can be tested by creating open invoices (sales and purchase), running the forecast generator, and verifying the projected flows match the invoice amounts and dates.

**Acceptance Scenarios**:

1. **Given** open sales invoices totaling 100,000 due within 30 days and purchase invoices totaling 60,000, **When** the manager generates a 30-day forecast in "actual" mode, **Then** the forecast shows inflows of 100,000 and outflows of 60,000, with a net positive projection.
2. **Given** the same invoices, **When** the manager generates a forecast in "expected" mode, **Then** AR inflows are shifted by the expected collection lag and AP outflows by the expected payment lag.
3. **Given** recurring journal templates, **When** the forecast is generated, **Then** recurring entries are included in the projected flows based on their recurrence schedule.

---

### User Story 8 - Treasury Reporting & Dashboards (Priority: P3)

Management views treasury dashboards and reports: treasury balances across all accounts, checks aging report (overdue receivable/payable checks), cash flow reports, and bank import summaries. Reports support branch filtering and multi-currency display.

**Why this priority**: Reporting is a read-only aggregation layer that depends on correctness of all underlying transactional data.

**Independent Test**: Can be tested by populating treasury data (accounts, checks, transactions) and verifying the dashboard metrics, aging buckets, and balance totals are accurate.

**Acceptance Scenarios**:

1. **Given** multiple treasury accounts across branches, **When** the manager views the treasury home dashboard, **Then** total balance, cash account count, and bank account count are displayed correctly with branch filtering.
2. **Given** issued checks with various due dates, **When** the manager views the checks aging report, **Then** checks are grouped into aging buckets (current, 30 days, 60 days, 90+ days) with correct totals.
3. **Given** completed reconciliations and treasury transactions, **When** the manager views the balances report, **Then** each treasury account shows its current balance, GL balance, and any discrepancy.

---

### Edge Cases

- What happens when the required GL accounts (1205, 2105, 1210, 2110) do not exist in a newly created company database? The system auto-creates them on first use under the correct parent accounts, logging the creation in the audit trail.
- What happens when a treasury transaction is posted and the GL journal entry creation fails midway? The system must roll back the treasury balance update atomically.
- How does the system handle a bank statement CSV with unexpected column layouts, mixed languages (Arabic/English), or non-standard date formats?
- What happens when two users simultaneously collect the same check? The system must prevent double-collection via state validation.
- What happens when a check is collected into a treasury account in a different currency than the check? The system should require an exchange rate or prevent the mismatch.
- How does the system handle bank reconciliation for an account with thousands of unmatched lines? Performance and pagination must be maintained.
- What happens when a treasury account is deactivated while it still has pending checks or notes linked to it?
- What happens when an expense or transfer amount exceeds the treasury account balance? Cash accounts reject the transaction by default (no physical overdraft); bank accounts allow overdraft by default (overdraft facilities). Both policies are configurable per account.

## Requirements *(mandatory)*

### Functional Requirements

**Treasury Account Management**

- **FR-001**: System MUST allow creating treasury accounts of type "cash" or "bank" with name (Arabic/English), currency, bank details (name, account number, IBAN), and an optional opening balance.
- **FR-002**: System MUST auto-create a linked GL account under the Cash & Equivalents parent when a treasury account is created, with auto-generated sequential account codes.
- **FR-003**: System MUST post a balanced opening balance journal entry when a treasury account is created with a non-zero opening balance.
- **FR-004**: System MUST prevent deletion of a treasury account that has a non-zero balance or prior transactions, allowing only soft-deactivation.
- **FR-005**: System MUST support multi-currency treasury accounts and store the applicable exchange rate at the time of account creation and each transaction.

**Expense & Transfer Transactions**

- **FR-006**: System MUST create a balanced double-entry journal (Dr. Expense / Cr. Treasury GL) for every expense transaction.
- **FR-007**: System MUST create a balanced double-entry journal (Dr. Target GL / Cr. Source GL) for every inter-account transfer and update both treasury balances atomically.
- **FR-008**: System MUST enforce fiscal period locks on all treasury transactions — rejecting expense and transfer postings dated within a locked period.
- **FR-009**: System MUST update the treasury `current_balance` only after the GL journal entry is successfully created, within the same database transaction, to prevent balance-GL drift.
- **FR-009a**: System MUST enforce a positive balance constraint on cash-type treasury accounts by default, rejecting expense/transfer transactions that would result in a negative balance. Bank-type treasury accounts MUST allow overdraft by default. This policy MUST be configurable per individual treasury account.

**Checks Management**

- **FR-010**: System MUST support the full check receivable lifecycle: create (pending) → collect OR bounce, with correct GL entries at each transition.
- **FR-011**: System MUST support the full check payable lifecycle: create (issued) → clear OR bounce, with correct GL entries at each transition.
- **FR-012**: System MUST post a reversal GL entry when a check bounces — reversing the original creation entry (and the collection entry if the check was already collected).
- **FR-013**: System MUST prevent state transitions on checks in terminal states (collected/cleared), EXCEPT that bounced checks MAY be re-presented (bounced → pending) to support the common Saudi banking practice of re-depositing returned checks. Re-presentation MUST generate a new GL entry (Dr. Checks Under Collection / Cr. AR) and preserve the full audit trail of all prior transitions.
- **FR-014**: System MUST detect and warn about duplicate check numbers within the same branch to prevent double-posting.
- **FR-015**: System MUST track check due dates and identify overdue checks (pending/issued past due date) for aging reports.

**Notes (Bills of Exchange) Management**

- **FR-016**: System MUST support the full note receivable lifecycle: create (pending) → collect OR protest, with correct GL entries. Protest is a terminal state — a protested note cannot be re-presented; a new note record must be created if parties renegotiate.
- **FR-017**: System MUST support the full note payable lifecycle: create (issued) → pay OR protest, with correct GL entries. Protest is a terminal state — a protested note cannot be re-presented.
- **FR-018**: System MUST track note maturity dates and settlement deadlines.

**Bank Reconciliation**

- **FR-019**: System MUST allow creating a reconciliation session for a treasury account with start balance, end balance, and statement date, preventing duplicate draft reconciliations per account.
- **FR-020**: System MUST support manual entry and CSV/Excel import of bank statement lines, with auto-detection of columns, date formats, and amount formats (including Arabic numerals and parenthesized negatives).
- **FR-021**: System MUST support manual one-to-one matching of bank statement lines to GL journal entries.
- **FR-022**: System MUST provide an auto-match feature that matches lines by amount, reference, and/or description similarity.
- **FR-023**: System MUST calculate the reconciliation difference (statement end balance vs. GL-derived end balance) and allow finalization only when the absolute difference is within a configurable tolerance that defaults to ±1.00 in the base currency (e.g., 1.00 SAR). The tolerance MUST be configurable per company in company settings.
- **FR-024**: System MUST lock a finalized reconciliation from further editing.

**Cash Flow Forecasting**

- **FR-025**: System MUST generate cash flow forecasts from open AR invoices, open AP invoices, and recurring journal templates over a configurable horizon (30–365 days).
- **FR-026**: System MUST support two forecast modes: "actual" (exact due dates) and "expected" (with configurable collection/payment lag adjustments).
- **FR-027**: System MUST calculate a running projected balance per forecast date line.

**Reporting**

- **FR-028**: System MUST provide a treasury balances report showing each account's current balance and linked GL balance, with branch filtering.
- **FR-029**: System MUST provide a checks aging report showing overdue checks grouped by aging bucket.
- **FR-030**: System MUST provide a cash flow report summarizing inflows and outflows over a selected period.

**Cross-Module Integration**

- **FR-031**: System MUST auto-create required intermediate GL accounts (Checks Under Collection 1205, Checks Payable 2105, Notes Receivable 1210, Notes Payable 2110) on first use if they do not exist, following the same auto-creation pattern used for treasury GL accounts under the Cash & Equivalents parent (1101). Auto-creation MUST place each account under its correct parent in the chart of accounts hierarchy and log the creation in the audit trail.
- **FR-032**: System MUST record all treasury operations in the audit trail with user, timestamp, action, and before/after values.
- **FR-033**: System MUST enforce tenant isolation — all treasury queries MUST be scoped to the current company's database.
- **FR-034**: System MUST enforce role-based permissions (`treasury.view`, `treasury.create`, `treasury.edit`, `treasury.delete`) on all treasury operations.

### Key Entities

- **Treasury Account**: Represents a cash box or bank account, linked 1:1 to a GL account. Key attributes: name, type (cash/bank), currency, current balance, bank details (name, account number, IBAN), branch, active status.
- **Treasury Transaction**: An audit record of every operation (expense, transfer, receipt, check collection). Key attributes: transaction number, type, amount, source/target accounts, date, reference, status.
- **Check Receivable**: A check received from a customer/party. Key attributes: check number, drawer, bank, amount, currency, issue/due/collection/bounce dates, status (pending/collected/bounced), linked journal entries.
- **Check Payable**: A check issued to a supplier/party. Key attributes: check number, beneficiary, bank, amount, currency, issue/due/clearance/bounce dates, status (issued/cleared/bounced), linked journal entries.
- **Note Receivable**: A promissory note or bill of exchange received. Key attributes: note number, drawer, amount, issue/due/maturity dates, status (pending/collected/protested).
- **Note Payable**: A promissory note or bill of exchange issued. Key attributes: note number, beneficiary, amount, issue/due/maturity dates, status (issued/paid/protested).
- **Bank Reconciliation**: A reconciliation session for a specific treasury account and statement period. Key attributes: treasury account, statement date, start/end balance, status (draft/approved).
- **Bank Statement Line**: An individual line from an imported bank statement. Key attributes: date, description, reference, debit, credit, running balance, reconciled flag, matched GL entry reference.
- **Cash Flow Forecast**: A generated projection of future cash positions. Key attributes: name, horizon days, mode (actual/expected), forecast lines with projected inflows/outflows and running balance.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every treasury transaction (expense, transfer, check, note) produces a balanced double-entry journal where total debits equal total credits — verified for 100% of operations.
- **SC-002**: Treasury account `current_balance` matches the linked GL account balance at any point in time, with zero unexplained discrepancy across all active accounts.
- **SC-003**: Check and note lifecycle transitions enforce valid state machines — no check/note can reach an invalid state (e.g., collected twice, bounced after cleared). Bounced checks support re-presentation (bounced → pending/issued) with full audit trail. Protested notes are terminal — no re-presentation allowed; a new note record is required for renegotiated terms.
- **SC-004**: Bank reconciliation auto-match correctly matches at least 70% of statement lines to GL entries in typical scenarios (exact amount and reference match).
- **SC-005**: Bank statement CSV import correctly parses 95%+ of common Saudi bank export formats (Arabic and English headers, multiple date formats, Arabic numeral amounts).
- **SC-006**: Fiscal period lock enforcement prevents 100% of attempts to post treasury transactions in a locked period.
- **SC-007**: All treasury operations complete within 2 seconds for individual transactions and within 10 seconds for batch operations (reconciliation import, forecast generation) under normal load.
- **SC-008**: Cash flow forecasts project balances within 10% accuracy of actual outcomes over a 30-day horizon (when using "expected" mode with historical lag adjustments).
- **SC-009**: Checks aging report accurately identifies 100% of overdue checks (due date ≤ today, status still pending/issued).
- **SC-010**: No treasury operation bypasses tenant isolation — verified by confirming every query includes company-scoped database routing.

## Clarifications

### Session 2026-04-14

- Q: Should a bounced check be re-presentable (bounced → pending again), or must the user create a new check record? → A: Bounced checks can be re-presented (bounced → pending), keeping the same record and full audit trail.
- Q: When required intermediate GL accounts (1205, 2105, 1210, 2110) are missing, should the system fail fast or auto-create them? → A: Auto-create missing intermediate GL accounts on first use, following the same pattern as treasury GL account auto-creation under 1101.
- Q: What should the default overdraft policy be for treasury accounts? → A: Allow overdraft on bank accounts by default (banks offer overdraft facilities); reject on cash accounts (cash can’t go negative physically). Configurable per account.
- Q: What should the default bank reconciliation tolerance be? → A: ±1.00 SAR default, configurable per company. Accommodates typical bank rounding, micro-fees, and currency conversion remainders.
- Q: Should a protested note be re-presentable (protested → pending), or is protest a terminal state? → A: Protest is terminal. Unlike bounced checks (banking operational event), protest is a formal legal action. A new note must be created if parties renegotiate, preserving the legal audit trail.

## Assumptions

- The chart of accounts for each company includes or can auto-create the required intermediate accounts (1101 parent, 1205, 2105, 1210, 2110, AR accounts, AP accounts).
- The fiscal period lock mechanism is already implemented and available for treasury operations to consume.
- The GL service (`gl_service.py`) correctly handles journal entry creation with double-entry validation and is the single point of GL posting.
- Multi-currency support follows the existing pattern: amounts stored in transaction currency with exchange rate to base currency.
- The existing authentication and RBAC system enforces `treasury.*` permissions on all endpoints.
- Bank reconciliation tolerance defaults to ±1.00 in the base currency (e.g., 1.00 SAR) and is configurable per company in company settings.
- Treasury operations are branch-scoped where applicable, using the existing branch isolation pattern.
- Bank import supports CSV format as the primary import format; Excel (XLSX) support is a secondary consideration.
- The audit trail utility (`utils/audit.py`) is available and records changes from all treasury operations.
- Opening balance journal entries offset against a capital/equity account, following the existing pattern.
