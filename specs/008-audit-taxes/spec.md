# Feature Specification: audit-taxes — الضرائب والزكاة

**Feature Branch**: `008-audit-taxes`  
**Created**: 2026-04-15  
**Status**: Draft  
**Input**: User description: "Speckit 5: audit-taxes — الضرائب والزكاة — comprehensive audit of the taxes & zakat module ensuring VAT, WHT, Zakat, ZATCA e-invoicing, tax returns, and tax calendar are all correct and properly connected to the frontend"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - VAT Calculation, Rates & GL Posting (Priority: P1)

A tax accountant creates and manages VAT rates (e.g., Saudi 15%, zero-rated, exempt). Every sales invoice, purchase invoice, and POS transaction that involves a taxable item automatically applies the correct rate. The system posts the corresponding VAT GL entries (Input Tax payable / Output Tax payable) and the VAT summary is visible in both the Tax Home dashboard and the VAT report page.

**Why this priority**: VAT is the most critical and frequently-used tax obligation. Incorrect VAT calculation or broken GL posting cascades into wrong financial statements, regulatory penalties, and failed ZATCA compliance. Every other tax scenario depends on the rates table being correct.

**Independent Test**: Can be fully tested by creating a VAT rate of 15%, applying it to a sales invoice of 1,000 SAR, verifying the system calculates 150 SAR VAT, posts the GL entry (Dr. AR 1,150 / Cr. Revenue 1,000 / Cr. Output VAT 150), and confirming the Tax Home dashboard shows the correct totals.

**Acceptance Scenarios**:

1. **Given** a Saudi company with a 15% VAT rate configured, **When** an accountant creates a sales invoice of 10,000 SAR with a taxable line item, **Then** the system automatically calculates 1,500 SAR VAT, posts the correct GL entry, and the invoice total is 11,500 SAR.
2. **Given** multiple VAT rates exist (standard, zero-rated, exempt), **When** the accountant applies zero-rated to an export sale, **Then** the VAT amount is 0 and the GL entry records zero output tax correctly.
3. **Given** a configured VAT rate, **When** a purchase invoice with input VAT is posted, **Then** the GL entry posts to the Input Tax account (not Output Tax), and the net VAT liability (Output − Input) is correctly reflected in the VAT report.
4. **Given** a POS transaction, **When** a cashier processes a sale with a taxable product, **Then** the receipt shows the VAT amount separately, and the end-of-session POS report includes the total VAT collected.
5. **Given** the Tax Home page (`/taxes`), **When** the accountant opens it, **Then** the VAT summary card shows total output VAT, total input VAT, and net VAT liability for the current period — all reflecting real data from the backend.

---

### User Story 2 - Tax Returns: Filing, Tracking & Status (Priority: P1)

A tax officer creates VAT return filings for each required period (monthly or quarterly based on company settings). The officer reviews the pre-filled amounts from posted transactions, makes any manual adjustments, files the return, and tracks the filing status. The frontend Tax Returns page displays all returns with their statuses and links to individual details.

**Why this priority**: Tax return filing is the primary compliance obligation imposed by ZATCA. Missing, duplicate, or incorrectly filed returns result in regulatory fines. The ability to view, file, and track returns through the frontend is a direct user workflow.

**Independent Test**: Can be tested by creating a VAT return for Q1 2026, verifying the system pre-populates it with the output and input VAT totals from posted transactions for that period, filing it, and confirming the status changes to "filed" with timestamps visible on the Tax Returns page.

**Acceptance Scenarios**:

1. **Given** a company with monthly VAT filing frequency, **When** the tax officer opens the Tax Returns page and clicks "New Return," **Then** the system creates a draft return for the correct period with pre-filled taxable amounts from posted transactions.
2. **Given** a draft tax return, **When** the officer reviews and clicks "File Return," **Then** the status changes to "filed," the filed date is recorded, and the return becomes read-only.
3. **Given** a filed return, **When** the officer views the Tax Return Details page, **Then** all relevant data (period, taxable amount, VAT due, filed date, payment status) are displayed correctly with no broken fields or missing labels.
4. **Given** an attempt to file a return for a period that already has a filed return of the same type, **When** the system processes the request, **Then** it rejects the duplicate filing with a clear error message.
5. **Given** an officer on the Tax Returns list page, **When** they filter by period, status, or return type, **Then** the table updates to show only matching records with correct pagination.

---

### User Story 3 - ZATCA E-Invoicing Compliance (Priority: P1)

A finance manager configures the company's ZATCA phase (Phase 1 or Phase 2) and generates compliant e-invoices. For Phase 2, each issued invoice receives a cryptographic QR code and digital signature. The compliance settings page shows the current ZATCA status, VAT registration number, and allows the manager to update the ZATCA configuration.

**Why this priority**: ZATCA Phase 2 is a legal mandate for Saudi businesses. Non-compliant invoices risk rejection by buyers and regulatory penalties. The compliance settings page must correctly read and write the ZATCA configuration, and e-invoice generation must produce valid QR codes.

**Independent Test**: Can be tested by setting ZATCA Phase 2 in the Compliance settings, generating a test invoice, and verifying the invoice response contains a valid QR code string and a signed XML document, then confirming the Tax Compliance page reflects the updated phase.

**Acceptance Scenarios**:

1. **Given** a Saudi company, **When** the finance manager opens the Tax Compliance page, **Then** it displays the current VAT registration number, Zakat number, ZATCA phase, and filing frequency — all loaded correctly from the backend.
2. **Given** a company in ZATCA Phase 1, **When** a sales invoice is issued, **Then** the invoice includes a Base64-encoded QR code with seller name, VAT number, timestamp, total, and VAT amount as required by ZATCA.
3. **Given** a company upgraded to ZATCA Phase 2, **When** the finance manager saves the compliance settings, **Then** subsequent invoices include both the QR code and a cryptographic signature, and the Compliance page confirms the phase change.
4. **Given** a branch with its own tax registration, **When** the manager configures branch tax settings, **Then** the branch settings are saved independently and the branch's invoices use the branch-specific registration number.
5. **Given** the Compliance page displaying supported countries, **When** a company is set to a country that does not support ZATCA, **Then** the ZATCA configuration section is hidden or disabled with an informational message.

---

### User Story 4 - Zakat Calculation & GL Posting (Priority: P2)

A Saudi company's finance manager calculates the annual Zakat obligation (2.5% of net Zakat base) at year-end using the Zakat Calculator interface. The system computes the Zakat base from the GL data (net assets, inventory, receivables, investments). The manager reviews the computed amount, confirms it, and posts the Zakat expense journal entry to the GL. The posted calculation is stored with full details for the GAZT audit trail.

**Why this priority**: Zakat is a mandatory annual religious and legal obligation for Saudi entities. Incorrect computation or failure to post to GL understates the company's obligations. The Zakat Calculator page must reliably drive computation and GL posting.

**Independent Test**: Can be tested by opening the Zakat Calculator for fiscal year 2025, providing a net assets value, verifying the computed Zakat (2.5%), clicking "Post to GL," and confirming the journal entry (Dr. Zakat Expense / Cr. Zakat Payable) appears in the GL with the correct amounts.

**Acceptance Scenarios**:

1. **Given** a Saudi company with a net Zakat base of 400,000 SAR, **When** the manager initiates the Zakat calculation for the current fiscal year, **Then** the Zakat Calculator displays a computed Zakat of 10,000 SAR (2.5%) with a breakdown of components.
2. **Given** a computed Zakat result, **When** the manager clicks "Post to GL," **Then** the system creates a balanced GL journal entry (Dr. Zakat Expense / Cr. Zakat Payable) and marks the calculation as posted in the database.
3. **Given** a Zakat calculation already posted for a fiscal year, **When** the manager attempts to post again for the same year, **Then** the system prevents duplicate posting and shows a clear message.
4. **Given** a non-Saudi company, **When** the manager navigates to the Accounting module, **Then** the Zakat Calculator option is hidden or disabled with a note that it applies only to Saudi entities.
5. **Given** a posted Zakat calculation, **When** the manager views the calculation details, **Then** the full breakdown (net assets, exclusions, rate, due amount, posting date, GL reference) is displayed correctly.

---

### User Story 5 - Withholding Tax (WHT) Rates & Certificate Tracking (Priority: P2)

A payables accountant manages withholding tax deductions from supplier payments. The accountant retrieves the applicable WHT rate by service category (professional services, rent, goods, etc.), creates a WHT certificate when a payment is made, and the system automatically calculates the net payment (gross − WHT). The WHT Transactions page lists all certificates with filter capabilities. The system generates a WHT declaration report summarizing total WHT collected.

**Why this priority**: WHT is a legal requirement in Saudi Arabia for certain vendor payments. The WHT module must accurately calculate deductions and track certificates with audit-quality records for GAZT submission.

**Independent Test**: Can be tested by selecting "Professional Services" category (5% WHT rate), entering a gross amount of 20,000 SAR, creating a WHT certificate, verifying the system computes 1,000 SAR WHT and 19,000 SAR net, and confirming the certificate appears in the WHT Transactions list.

**Acceptance Scenarios**:

1. **Given** a WHT rate of 5% for "Professional Services," **When** the accountant creates a WHT certificate for a 20,000 SAR invoice, **Then** the system calculates 1,000 SAR WHT, 19,000 SAR net, and stores the certificate with a unique reference number.
2. **Given** the WHT Transactions page, **When** the accountant filters by supplier or date range, **Then** the list updates to show only matching certificates with all relevant columns (gross, rate, WHT amount, net, supplier, date).
3. **Given** multiple WHT rates for different categories, **When** the accountant selects a rate in the certificate form, **Then** the WHT Rates section on the page loads correctly with all active rates and their effective dates.
4. **Given** a WHT certificate is created, **When** the accountant views the WHT details, **Then** all fields (supplier, gross amount, category, rate %, WHT amount, net payment, reference) are populated and displayed correctly with no empty or undefined values.
5. **Given** the WHT Dashboard section in the Tax Home, **When** the accountant views it, **Then** it shows total WHT collected for the current period with a breakdown by category.

---

### User Story 6 - Tax Calendar: Deadlines & Reminders (Priority: P3)

A tax officer views all upcoming tax obligations in the Tax Calendar — including VAT filing deadlines, Zakat payment dates, and WHT submission dates. The calendar shows recurring obligations, days remaining until each deadline, and allows the officer to mark an obligation as completed. Reminder notifications are sent a configurable number of days before each deadline.

**Why this priority**: Missed tax deadlines result in automatic fines. A reliable calendar prevents filing gaps and gives tax officers visibility across all obligations. It is lower priority because it does not affect calculation accuracy, but it is critical for operational compliance management.

**Independent Test**: Can be tested by opening the Tax Calendar page, verifying that it loads upcoming deadlines (VAT monthly filing, quarterly Zakat) with correct due dates, clicking "Mark Complete" on an obligation, and confirming the status updates and the completed item is visually marked.

**Acceptance Scenarios**:

1. **Given** a company with monthly VAT filing, **When** the tax officer opens the Tax Calendar, **Then** the page displays recurring VAT deadlines for the next 12 months with correct due dates based on the filing frequency setting.
2. **Given** an upcoming VAT deadline in 7 days, **When** the system sends reminders, **Then** the responsible officers receive notification at 7, 3, and 1 days before the deadline.
3. **Given** a past-due obligation that has not been marked complete, **When** the officer views the calendar, **Then** the overdue item is visually highlighted and shows the number of days overdue.
4. **Given** the officer marks a tax obligation as "Completed," **When** the calendar refreshes, **Then** the item shows a "Completed" status with the date of completion and moves out of the "Pending" list.
5. **Given** both VAT, Zakat, and WHT obligations on the calendar, **When** the officer filters by obligation type, **Then** only the selected type's deadlines are shown.

---

### Edge Cases

- What happens when a tax return period overlaps with a locked fiscal period — can the return still be filed?
- How does the system handle a VAT rate change mid-period (e.g., rate changes from 5% to 15%) — does it apply the new rate only to invoices created after the effective date?
- What if a Zakat calculation is initiated but the GL does not have sufficient data — does the system warn the user or compute with zero values?
- How are WHT certificates handled when a supplier payment is reversed or voided — is the certificate automatically cancelled?
- What happens when ZATCA key generation fails (network or certificate error) — does the invoice fallback to Phase 1 formatting or fail hard?
- How does the system handle a company that transitions from VAT-exempt to VAT-registered mid-year — are old invoices retroactively affected?

## Requirements *(mandatory)*

### Functional Requirements

#### VAT & Tax Rates

- **FR-001**: The system MUST allow authorised users to create, update, and deactivate tax rates specifying type (VAT, WHT, etc.), percentage, effective date, country, and applicable account.
- **FR-002**: The system MUST automatically apply the correct tax rate to sales invoices, purchase invoices, and POS transactions based on the line item's tax group assignment.
- **FR-003**: Every taxable transaction MUST post a GL journal entry that separates the net amount, input/output VAT, and any WHT, with a traceable reference to the originating document.
- **FR-004**: The Tax Home dashboard (`/taxes`) MUST load real-time summary data: total output VAT, total input VAT, net VAT liability, pending returns, and upcoming deadlines — all sourced from the backend without hardcoded values.

#### Tax Returns

- **FR-005**: The system MUST allow authorised users to create draft tax returns per period and type (VAT, income tax), pre-populated with transaction totals from posted GL entries.
- **FR-006**: Users MUST be able to file a tax return, which transitions its status to "filed," records the filed date, and locks the return from further edits.
- **FR-007**: The system MUST prevent filing a return for a period that already has a filed return of the same type.
- **FR-008**: The Tax Returns list page MUST support filtering by period, status (draft/filed/cancelled), and return type, and display all relevant columns with correct data.
- **FR-009**: The Tax Return Details page MUST display all return fields (period, taxable base, VAT due, adjustments, filed date, payment status) in a readable format with no undefined or empty label placeholders.

#### ZATCA E-Invoicing

- **FR-010**: The system MUST generate a Base64-encoded QR code on every issued sales invoice for Phase 1 compliance, encoding seller name, VAT number, invoice timestamp, total amount, and VAT amount.
- **FR-011**: For Phase 2 ZATCA, the system MUST generate an RSA key pair, attach a cryptographic signature to each invoice XML, and include the QR code alongside the signature.
- **FR-012**: The Tax Compliance page MUST correctly load and display the company's ZATCA configuration (phase, VAT registration number, Zakat number, filing frequency) and allow authorised users to update these settings.
- **FR-013**: Branch-level tax settings MUST be independently configurable per branch and applied when generating invoices from that branch.

#### Zakat

- **FR-014**: The Zakat Calculator MUST be visible and accessible ONLY for companies with Saudi Arabia as their country setting.
- **FR-015**: The system MUST calculate Zakat as 2.5% of the entered/computed net Zakat base, displaying the full breakdown (gross assets, liabilities, exclusions, net base, amount due).
- **FR-016**: Users MUST be able to post the Zakat result to the GL exactly once per fiscal year; subsequent attempts MUST be rejected with an informative message.
- **FR-017**: Posted Zakat calculations MUST be stored with the fiscal year, net base, amount, method, posting user, and timestamp for audit purposes.

#### Withholding Tax (WHT)

- **FR-018**: The system MUST maintain a list of active WHT rates by category (professional services, rent, goods, etc.) with effective dates and rates.
- **FR-019**: Authorised users MUST be able to create WHT certificates specifying supplier, gross amount, category, and date; the system MUST auto-calculate WHT amount and net payment.
- **FR-020**: The WHT Transactions page MUST list all certificates with filters for supplier, date range, and category, and display correct amounts (gross, rate, WHT, net) with no broken data.
- **FR-021**: WHT amounts MUST be posted as GL entries (Dr. Expense / Cr. WHT Payable / Cr. Bank) at the time the certificate is created.

#### Tax Calendar

- **FR-022**: The Tax Calendar MUST display upcoming and past-due tax obligations for VAT, Zakat, and WHT organised by due date with the number of days remaining or overdue.
- **FR-023**: Users MUST be able to mark an obligation as "Completed" with a timestamp, which visually distinguishes it from pending items.
- **FR-024**: The system MUST send reminder notifications at 7, 3, and 1 day(s) before each deadline based on the configured reminder schedule in the TaxCalendar entity.

#### Frontend Connectivity

- **FR-025**: All frontend pages within the Taxes module (`TaxHome`, `TaxCompliance`, `TaxCalendar`, `TaxReturnForm`, `TaxReturnDetails`, `WithholdingTax`) MUST call their corresponding backend API endpoints through the `taxes.js` service file, with no hardcoded mock data in production views.
- **FR-026**: All API calls MUST handle loading states (spinner/skeleton), success states (populated data), and error states (user-friendly error messages) — no silent failures or blank pages.
- **FR-027**: The Taxes module sidebar link MUST be correctly wired in the navigation configuration and accessible from the main sidebar for all industry types.
- **FR-028**: The Zakat Calculator (`/accounting/zakat`) MUST be accessible from the Accounting module navigation and conditionally rendered based on the company's country setting.

### Key Entities

- **TaxRate**: A configured tax rate with type (VAT, WHT), percentage, effective date, country, and linked GL account. Used as the source of truth for all automatic tax calculations.
- **TaxGroup**: A named collection of tax rates applied together to a transaction line (e.g., "GCC Standard VAT" = 15% VAT only).
- **TaxReturn**: A period-based filing record grouping all tax liabilities for a period. Has a lifecycle: draft → filed → cancelled. Linked to the company's filing frequency.
- **TaxPayment**: A payment record against a tax return, tracking amount due, amount paid, payment date, and reference.
- **TaxCalendar**: A recurring obligation entry with due date, obligation type, responsible party, and reminder schedule.
- **CompanyTaxSetting**: The company-level tax configuration including VAT registration number, Zakat number, ZATCA phase, and quarterly/monthly filing frequency.
- **BranchTaxSetting**: Per-branch override of tax settings (tax regime, registration number) for multi-branch companies.
- **ZakatCalculation**: The stored result of a Zakat computation for a fiscal year, including net base, rate, amount, method, and posting reference.
- **WhtRate**: A withholding tax rate by service category, active/inactive flag, and effective date range.
- **WhtTransaction**: A WHT certificate record linking a supplier, gross amount, applicable rate, computed WHT, net payment, and GL posting reference.
- **TaxRegime**: A country's tax system definition (name, currency, supported obligations like VAT/Zakat/WHT).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: VAT is correctly calculated on 100% of taxable transactions — zero test cases show incorrect VAT amounts in tax reports.
- **SC-002**: All 6 tax frontend pages (`TaxHome`, `TaxCompliance`, `TaxCalendar`, `TaxReturnForm`, `TaxReturnDetails`, `WithholdingTax`) load real data from the backend with no hardcoded placeholders in production.
- **SC-003**: ZATCA Phase 1 QR code is generated on every issued sales invoice — zero invoices are missing the QR code for Saudi companies.
- **SC-004**: Zakat calculation produces the correct 2.5% result on 100% of net Zakat base computations, with no rounding errors exceeding 0.01 SAR.
- **SC-005**: Tax returns cannot be double-filed — the system rejects 100% of duplicate filing attempts for the same period and type.
- **SC-006**: WHT certificates correctly auto-calculate net payment (gross − WHT) on 100% of certificate creation events.
- **SC-007**: Tax Calendar displays all configured obligations with due dates accurate to the day — no missing or incorrectly dated entries.
- **SC-008**: All tax-related API errors display a human-readable error message in the frontend within 3 seconds — no silent failures or blank pages.
- **SC-009**: The Zakat Calculator is completely hidden for non-Saudi companies — zero non-Saudi companies can access or execute a Zakat calculation.
- **SC-010**: Every tax transaction (VAT posting, WHT deduction, Zakat posting) produces a balanced GL journal entry — zero unbalanced entries in the audit trail.

## Assumptions

- The company's country setting (Saudi Arabia vs. other) is already stored in `CompanyTaxSetting` and is reliably used to gate Zakat and ZATCA features.
- ZATCA Phase 2 key generation is an existing backend capability (`/external/zatca/generate-keys`) and only needs to be correctly called from the frontend compliance page.
- The GL chart of accounts already includes standard tax accounts (Output VAT Payable, Input VAT Receivable, Zakat Payable, WHT Payable) created during company onboarding.
- Tax rates and their effective dates are managed by an administrator before the module is used by accountants — rate creation is not part of the daily workflow.
- Multi-currency VAT (non-SAR invoices) follows the same exchange rate logic used in the accounting and treasury modules.
- The `taxes.js` frontend service file already defines all necessary API call functions; the audit task is to verify they are correctly wired to real API endpoints, not to rewrite the service.
- Fiscal period lock enforcement (preventing posting to locked periods) is shared logic from the accounting module and does not need to be re-implemented for taxes.
- Mobile (React Native) tax views are out of scope for this audit iteration; only the web frontend is in scope.
