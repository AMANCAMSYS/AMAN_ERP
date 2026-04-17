# Feature Specification: Audit Sales Module — تدقيق وحدة المبيعات

**Feature Branch**: `012-audit-sales`  
**Created**: 2026-04-15  
**Status**: Draft  
**Input**: User description: "audit-sales — المبيعات — لاتنسى ان تجعل كل شيء مرتبط بالفرونت اند بالشكل الصحيح"

## User Scenarios & Testing

### User Story 1 — Numeric Precision Across All Sales Endpoints (Priority: P1)

An auditor inspects sales invoices, credit notes, debit notes, returns, and customer receipts and expects all monetary values (unit prices, quantities, taxes, discounts, totals) to arrive as exact string or Decimal representations — never as IEEE-754 floating-point numbers that can silently lose precision.

**Why this priority**: Floating-point rounding errors in financial data are the single highest-severity audit finding; they affect every downstream report, GL posting, and tax return.

**Independent Test**: Send a sales invoice with `unit_price = "10.05"` and `quantity = "3"` via the API; confirm the response returns exact string values and the GL entry posts the correct total of `"30.15"` without rounding drift.

**Acceptance Scenarios**:

1. **Given** a sales invoice payload with line item amounts as strings, **When** the backend processes and stores them, **Then** all returned monetary fields are strings — no `float` serialization anywhere in the response.
2. **Given** a credit or debit note with a tax-rate of `"5.125"`, **When** the note is posted, **Then** the computed tax is exact and the GL entry matches without penny differences.
3. **Given** a customer receipt with `exchange_rate = "3.7505"`, **When** the receipt is saved, **Then** the stored and returned exchange rate preserves all four decimal places.

---

### User Story 2 — Frontend Sends Correct Data Types to Backend (Priority: P1)

A sales clerk fills out an invoice form, and the frontend sends the payload with monetary fields as string values (not `parseFloat` outputs) and performs local calculations using `Number()` to avoid precision loss in the UI.

**Why this priority**: Frontend `parseFloat` in API payloads is the primary source of precision corruption; local display calculations with `Number()` are safe for UI rounding but payloads must be exact strings.

**Independent Test**: Open InvoiceForm, enter a line item with price `10.05` and quantity `3`, submit; inspect the network request and confirm `unit_price: "10.05"` (string), not `unit_price: 10.05` (float).

**Acceptance Scenarios**:

1. **Given** any sales form (invoice, order, quotation, return, receipt), **When** the user submits, **Then** all monetary fields in the HTTP payload are string-typed.
2. **Given** the InvoiceForm `calculateTotals()` function, **When** line items are updated, **Then** intermediate calculations use `Number()` — not `parseFloat()`.
3. **Given** the SalesQuotationForm with a discount percentage, **When** the user changes the discount field, **Then** the UI calculates the new subtotal using `Number()` and displays it via `formatNumber()`.

---

### User Story 3 — User-Visible Error Handling via Toast Notifications (Priority: P1)

When any sales operation fails (fetch, submit, delete), the user sees a toast notification with a meaningful error message instead of the error being silently swallowed by `console.error` or dispatched via the deprecated `toastEmitter`.

**Why this priority**: Silent errors cause users to believe operations succeeded when they failed — a data-integrity risk. Migrating to `useToast` also eliminates a deprecated dependency.

**Independent Test**: Disconnect the network, attempt to load the customer list; confirm a toast "Error" appears and no `console.error` output is written.

**Acceptance Scenarios**:

1. **Given** any sales frontend page, **When** an API call fails, **Then** a toast notification is displayed via `showToast()` from the `useToast` hook.
2. **Given** pages currently using `toastEmitter.emit()`, **When** the audit fixes are applied, **Then** all `toastEmitter` imports are removed and replaced with `useToast`.
3. **Given** pages with `console.error(err)` in catch blocks, **When** the audit fixes are applied, **Then** every `console.error` is replaced with `showToast(t('common.error'), 'error')`.

---

### User Story 4 — Pydantic Schema Decimal Types (Priority: P1)

All Pydantic schemas for sales data (invoices, orders, quotations, credit/debit notes, CPQ, delivery orders) use `Decimal` field types instead of `float` for monetary and quantity fields, ensuring the serialization boundary enforces precision.

**Why this priority**: Pydantic `float` fields silently coerce string inputs to IEEE floats before they even reach business logic; `Decimal` fields preserve exactness from API boundary to database.

**Independent Test**: Submit a sales invoice with `"unit_price": "10.05"` and confirm the Pydantic model stores it as `Decimal("10.05")`.

**Acceptance Scenarios**:

1. **Given** `backend/routers/sales/schemas.py` and `backend/schemas/sales_credit_notes.py`, **When** any field representing money, quantity, rate, or percentage is declared, **Then** it uses `Decimal` type, not `float`.
2. **Given** `backend/schemas/cpq.py`, **When** pricing fields are declared, **Then** they use `Decimal` type.
3. **Given** `backend/schemas/sales_improvements.py`, **When** monetary fields exist, **Then** they use `Decimal` type.

---

### User Story 5 — Audit Trail Columns on All Sales Tables (Priority: P2)

Every sales-related database table has `created_at`, `updated_at`, `created_by`, and `updated_by` columns, ensuring full traceability of who created or modified each record and when.

**Why this priority**: Audit trail is a regulatory requirement for financial records; missing columns prevent accountability tracking.

**Independent Test**: Query any sales table (`sales_invoices`, `sales_orders`, `customer_receipts`) and verify all four audit columns exist and are populated on insert/update.

**Acceptance Scenarios**:

1. **Given** the `database.py` CREATE TABLE definitions for sales tables, **When** inspected, **Then** every table has `created_at`, `updated_at`, `created_by`, `updated_by` columns.
2. **Given** the domain models in `models/domains/sales.py` and related files, **When** inspected, **Then** every sales-exclusive model class includes `AuditMixin`; shared models (e.g., POS entities) are skipped.
3. **Given** a new sales invoice is created via the API, **When** the row is queried, **Then** `created_at` and `created_by` are populated.

---

### User Story 6 — Fiscal Period Validation on All GL-Posting Endpoints (Priority: P2)

Every sales endpoint that creates a General Ledger entry validates that the fiscal period is open before posting. If the period is closed, the system returns HTTP 400 — not a silent failure.

**Why this priority**: Posting to a closed fiscal period corrupts finalized financial statements; hard-blocking with HTTP 400 is the established pattern.

**Independent Test**: Close the current fiscal period, then attempt to create a sales invoice; confirm the API returns HTTP 400 with a clear error message.

**Acceptance Scenarios**:

1. **Given** the sales invoice endpoint already has a fiscal check, **When** verified, **Then** the check is correctly placed before the GL posting block.
2. **Given** the sales return endpoint, **When** a return with GL reversal is submitted for a closed period, **Then** HTTP 400 is returned.
3. **Given** the delivery order endpoint, **When** a delivery that triggers stock and GL entries is submitted for a closed period, **Then** HTTP 400 is returned if a fiscal check is missing.

---

### User Story 7 — Correct Display Formatting in Sales Frontend (Priority: P2)

All monetary values rendered in sales frontend pages use `formatNumber()` instead of raw `.toLocaleString()` or `parseFloat().toLocaleString()`, ensuring consistent formatting aligned with the company's locale and decimal settings.

**Why this priority**: Inconsistent number formatting creates confusion in multi-currency environments and can mask precision issues.

**Independent Test**: Open the InvoiceDetails page for an invoice with amount `1234567.89`; confirm it displays as the company-standard formatted string, not a raw JS locale string.

**Acceptance Scenarios**:

1. **Given** any sales page rendering a monetary value, **When** the value is displayed, **Then** `formatNumber()` from `utils/format` is used.
2. **Given** CustomerStatement or AgingReport pages, **When** balances are shown, **Then** they use `formatNumber()` consistently.

---

### User Story 8 — CPQ Pricing Engine Numeric Correctness (Priority: P2)

The CPQ (Configure-Price-Quote) module uses string/Decimal representations throughout the pricing engine so that complex multi-option configured quotes do not accumulate floating-point drift.

**Why this priority**: CPQ quotes often involve many multiplied options; float drift compounds with each calculation step.

**Independent Test**: Configure a product with 10 options each at `"99.99"`, submit the quote; confirm the total is exactly `"999.90"`, not `999.8999999...`.

**Acceptance Scenarios**:

1. **Given** `backend/services/cpq_service.py`, **When** price calculations use `float()`, **Then** they are replaced with `str()` for serialization and `Decimal` for computation.
2. **Given** `frontend/src/pages/CPQ/Configurator.jsx`, **When** price totals are calculated locally, **Then** `Number()` is used instead of `parseFloat()`.
3. **Given** CPQ quote payloads, **When** submitted to the API, **Then** all price fields are string-typed.

---

### User Story 9 — Delivery Order Audit Completeness (Priority: P3)

Delivery orders created from sales orders have full audit columns, correct numeric serialization, and proper error handling in the frontend.

**Why this priority**: Delivery orders bridge sales and inventory; correctness here prevents stock discrepancies.

**Independent Test**: Create a delivery order from a sales order; inspect the database row for audit columns, the API response for string-typed quantities, and the UI for toast error handling.

**Acceptance Scenarios**:

1. **Given** `backend/routers/delivery_orders.py`, **When** quantities and amounts are serialized in responses, **Then** they use `str()` not `float()`.
2. **Given** `frontend/src/pages/Sales/DeliveryOrderForm.jsx`, **When** quantities are submitted, **Then** they are `String()` in the payload.
3. **Given** `frontend/src/pages/Sales/DeliveryOrders.jsx`, **When** an API error occurs, **Then** a toast notification is shown.

---

### User Story 10 — Contract and Commission Numeric Precision (Priority: P3)

Sales contracts and commission calculations use correct numeric types so that recurring billing amounts and commission percentages do not drift over multiple billing cycles.

**Why this priority**: Commission disputes and billing errors are costly; they stem from float arithmetic on percentages.

**Independent Test**: Create a contract with a monthly amount of `"3333.33"` and a commission rate of `"7.5%"`; verify the commission amount is exactly `"249.9975"` (or its correctly rounded string).

**Acceptance Scenarios**:

1. **Given** contract forms and endpoints, **When** monetary fields are submitted and returned, **Then** they are string/Decimal typed.
2. **Given** commission calculation logic, **When** a percentage is applied, **Then** the result is not subject to float drift.
3. **Given** `SalesCommissions.jsx`, **When** commission data is displayed, **Then** values use `formatNumber()`.
4. **Given** a sales invoice of `"10000.00"` with a commission rate of `"7.5%"`, **When** the commission is calculated, **Then** the result is exactly `"750.00"` and the GL entry matches.
5. **Given** multiple invoices with varying amounts and tiered commission rates, **When** commissions are computed, **Then** the total commission equals the sum of individually computed commissions without rounding drift.

---

### User Story 11 — Customer Groups and Pricing Lists (Priority: P3)

Customer groups with discount percentages and price list entries use Decimal/string types so that group-level discounts are applied exactly.

**Why this priority**: Group discounts affect every invoice in the group; a float error here multiplies across all customers.

**Independent Test**: Set a customer group discount to `"12.5%"`, create an invoice for a grouped customer; confirm the discount amount is exact.

**Acceptance Scenarios**:

1. **Given** `CustomerGroups.jsx`, **When** a discount percentage is submitted, **Then** it is sent as `String()`.
2. **Given** the backend customer group endpoint, **When** the discount percentage is stored and returned, **Then** it uses `str()` / `Decimal`.

---

### User Story 12 — Sales Quotation-to-Order-to-Invoice Flow Integrity (Priority: P3)

The full quote → order → invoice → delivery pipeline preserves numeric precision at each stage, with no data loss when values propagate from one entity to the next.

**Why this priority**: The sales cycle is multi-step; precision must be consistent from the first quote to the final delivery.

**Independent Test**: Create a quotation, convert to order, convert to invoice, create delivery; compare the total at each stage and confirm they are identical strings.

**Acceptance Scenarios**:

1. **Given** a quotation with line totals, **When** converted to a sales order, **Then** all numeric values carry over as exact strings.
2. **Given** a sales order converted to an invoice, **When** the invoice is posted, **Then** the GL entry total matches the order total exactly.

---

### Edge Cases

- What happens when a sales return is created for a quantity larger than the original invoice line? System should reject with HTTP 400.
- How does the system handle a credit note for an invoice in a different currency? Exchange rates must be preserved as strings.
- What happens when a delivery order's shipped quantity exceeds the ordered quantity? Validation must block it.
- How does the system handle a receipt allocated across invoices in multiple currencies? Each allocation must respect its own exchange rate.
- What happens when a CPQ configuration has zero-price optional items? The total should remain correct and not produce `-0` or `NaN`.

## Requirements

### Functional Requirements

- **FR-001**: System MUST serialize all monetary, quantity, rate, discount, and tax fields as strings in API responses across all sales endpoints (invoices, orders, quotations, returns, credit/debit notes, receipts, delivery orders, CPQ).
- **FR-002**: System MUST use `Decimal` field types (not `float`) in all Pydantic schemas for sales data (`schemas.py`, `sales_credit_notes.py`, `sales_improvements.py`, `cpq.py`).
- **FR-003**: All sales frontend forms MUST send monetary fields as `String()` values in API payloads, not `parseFloat()` outputs.
- **FR-004**: All sales frontend local calculations MUST use `Number()` instead of `parseFloat()` for intermediate values.
- **FR-005**: All sales frontend pages MUST replace `console.error` with `showToast()` from the `useToast` hook for user-visible error reporting.
- **FR-006**: All sales frontend pages MUST replace `toastEmitter.emit()` with `showToast()` and remove `toastEmitter` imports.
- **FR-007**: All sales frontend pages displaying monetary values MUST use `formatNumber()` from `utils/format` instead of `.toLocaleString()` or `parseFloat().toLocaleString()`.
- **FR-008**: All sales database tables MUST have `created_at`, `updated_at`, `created_by`, `updated_by` audit columns.
- **FR-009**: All sales-exclusive domain models MUST include `AuditMixin`; shared models used by POS or other modules are deferred to their respective audits.
- **FR-010**: All sales endpoints that create GL entries MUST validate the fiscal period is open before posting, returning HTTP 400 if closed.
- **FR-011**: The CPQ pricing engine MUST use `str()` for serialization and avoid `float()` for computation.
- **FR-012**: Delivery order endpoints MUST use `str()` serialization for quantities and amounts.
- **FR-013**: Commission calculation logic MUST produce functionally correct results; the audit MUST include test scenarios verifying commission amounts against known inputs.

### Key Entities

- **Sales Invoice**: Central financial document; links to customer, line items, GL entries, tax records. Key fields: total, tax, discount, exchange_rate, paid_amount.
- **Sales Order**: Pre-invoice commitment; may convert to invoice and delivery order.
- **Sales Quotation**: Non-binding price offer; may convert to sales order.
- **Sales Return**: Reversal of an invoice; triggers stock restoration and GL reversal.
- **Credit Note / Debit Note**: Post-invoice adjustments affecting customer balance and GL.
- **Customer Receipt (Voucher)**: Payment received from customer; allocated against outstanding invoices.
- **Delivery Order**: Physical goods shipment; decrements inventory stock.
- **CPQ Quote**: Configured product quote with dynamic pricing from multiple options.
- **Sales Contract**: Recurring billing agreement with commission linkage.
- **Customer Group**: Grouping with shared discount percentage and payment terms.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Zero `float()` calls remain in all sales backend router and service files after audit.
- **SC-002**: Zero `parseFloat()` calls remain in all sales and CPQ frontend files after audit.
- **SC-003**: Zero `console.error` calls remain in all sales and CPQ frontend files after audit.
- **SC-004**: Zero `toastEmitter` imports remain in all sales and CPQ frontend files after audit.
- **SC-005**: All Pydantic schemas for sales data use `Decimal` types for monetary/quantity fields.
- **SC-006**: All sales database tables have complete audit columns (`created_at`, `updated_at`, `created_by`, `updated_by`).
- **SC-007**: All sales GL-posting endpoints include fiscal period validation.
- **SC-008**: `py_compile` passes for all modified backend files.
- **SC-009**: `vite build` succeeds with zero errors for the frontend.
- **SC-010**: The full quotation → order → invoice → delivery pipeline preserves exact numeric values end-to-end.

## Clarifications

### Session 2026-04-15

- Q: Should the sales audit fix `float()` calls in cross-module files (inventory, GL, treasury, taxes, approvals, CRM) that sales endpoints call? → A: Fix only the listed sales module files; verify (don't fix) cross-module connections.
- Q: Should this audit include full ZATCA XML/QR compliance validation or only ensure numeric precision at the ZATCA boundary? → A: Only ensure numeric values passed to ZATCA functions are string/Decimal; defer ZATCA logic validation to the taxes audit.
- Q: Should AuditMixin be added to all models re-exported through sales.py or only sales-exclusive models? → A: Add AuditMixin only to sales-exclusive model classes (e.g., Customer, SalesInvoice, SalesOrder); skip shared models used by POS or other modules.
- Q: Should the audit verify commission calculation logic correctness or only fix numeric types? → A: Verify commission calculation logic produces correct results (add functional test scenarios).

## Assumptions

- Cross-module files (`stock_movements.py`, `shipments.py`, `gl_service.py`, `accounting.py`, `treasury.py`, `checks.py`, `taxes.py`, `zatca.py`, `approvals.py`, `crm.py`) are out of scope for code changes; only boundary data-flow verification is in scope.
- ZATCA e-invoicing logic validation (XML generation, QR codes, Phase 2 compliance) is deferred to the taxes audit; this audit only ensures numeric fields passed to ZATCA functions use string/Decimal types.
- The `useToast` hook and `ToastContext` are available and working across the application (verified in prior audits).
- The `formatNumber()` utility in `utils/format` is already implemented and handles locale-aware formatting.
- The `check_fiscal_period_open()` function is available and raises HTTP 400 on closed periods.
- The `AuditMixin` base class is defined in `models/base.py` and provides all four audit columns.
- The `Decimal` type from Python's `decimal` module is used for backend precision; JavaScript `Number` is acceptable for UI display since final payload values are converted to `String()`.
- Existing fiscal checks in `invoices.py`, `returns.py`, `credit_notes.py`, and `vouchers.py` will be verified but likely already correct from prior work.
- The `database.py` file contains CREATE TABLE definitions that may need audit column additions for sales tables.
- The sales module scope covers 38 frontend files (34 Sales + 4 CPQ) and 12 backend files (11 routers + 1 service).
