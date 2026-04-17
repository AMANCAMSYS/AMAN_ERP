# Feature Specification: Audit Purchases Module — تدقيق وحدة المشتريات

**Feature Branch**: `011-audit-purchases`
**Created**: 2026-04-15
**Status**: Draft
**Input**: User description: "audit-purchases — المشتريات — أوامر الشراء، المرتجعات، فواتير الشراء، الموردين، التكاليف المضافة، المطابقة، عروض الأسعار، الاتفاقيات الإطارية"

## User Scenarios & Testing

### User Story 1 — Purchase Order CRUD, Line-Level Pricing & Submission (Priority: P1) 🎯 MVP

As a procurement officer, I create and manage purchase orders — entering line items with quantity, unit price, tax rate, discounts, and markups — so that I can submit accurate orders to suppliers with correct totals and the backend processes all monetary values without floating-point precision loss.

**Why this priority**: Purchase orders are the foundation of the entire procurement cycle — every downstream operation (receiving, invoicing, matching, returns) depends on PO data being correct and precisely represented.

**Independent Test**: Create a PO with 3 line items (unit_price 1,250.7500 SAR, quantity 7, tax_rate 15%, discount 5%) → verify API returns all monetary values as strings (not JSON floats) → verify line totals and grand total are calculated correctly without floating-point artifacts → submit the PO → verify the order list page shows toast on error (not console.error) → verify the order detail page renders all amounts via `formatNumber()`.

**Acceptance Scenarios**:

1. **Given** a user on the PO form page, **When** I enter line items with monetary values, **Then** the frontend sends all amounts as strings (not `parseFloat`) and the backend processes them with `Decimal` arithmetic
2. **Given** a PO with discount and markup lines, **When** I submit, **Then** the backend computes totals using `Decimal` and returns all monetary fields as strings in the response
3. **Given** a PO list page, **When** the API call fails, **Then** a user-facing toast error appears (not just `console.error` or `toastEmitter.emit`)
4. **Given** I view PO details, **When** the page loads, **Then** all monetary values render correctly via `formatNumber()` with no "NaN", "undefined", or floating-point artifacts
5. **Given** the PO form, **When** I change quantity/price/discount, **Then** line subtotals update in the UI using `Number()` for local comparison (not `parseFloat`) and `formatNumber()` for display

---

### User Story 2 — Purchase Invoices with Fiscal Period Enforcement (Priority: P1)

As an accounts payable clerk, I create purchase invoices linked to POs — the system validates fiscal period status before posting, creates GL entries (Dr. Expense/Asset, Cr. Accounts Payable), and tracks payment status — so that all purchase obligations are recorded with double-entry integrity and period controls.

**Why this priority**: Purchase invoices are the financial record of procurement spend — they must enforce fiscal period locks and create balanced GL entries, and they represent the accounts payable obligation.

**Independent Test**: Create a purchase invoice for an existing PO → verify fiscal period is checked before posting → verify a balanced GL journal entry is created → verify all monetary values in the response are strings → verify the invoice list and detail pages show toast errors on failure → verify duplicate invoice detection works.

**Acceptance Scenarios**:

1. **Given** a purchase invoice form, **When** I submit, **Then** the API payload sends all monetary values as strings and the backend uses `Decimal` arithmetic for totals and GL posting
2. **Given** a purchase invoice, **When** it posts, **Then** the system checks fiscal period is open, creates a balanced GL journal entry, and updates supplier balance
3. **Given** the invoice list/detail pages, **When** an error occurs, **Then** a toast notification appears to the user (not `console.error` only)
4. **Given** an invoice with the same supplier, amount, and date as an existing one, **When** I attempt to create it, **Then** the system warns about potential duplicates
5. **Given** all invoice monetary fields (paid_amount, exchange_rate, line amounts), **When** returned from the API, **Then** they arrive as string representations of Decimal values

---

### User Story 3 — PO Receiving (GRN) & Inventory Integration (Priority: P1)

As a warehouse receiver, I receive goods against a purchase order — the system updates inventory quantities, recalculates weighted average cost via CostingService, creates inventory transactions, and posts GL entries — so that received goods are accurately tracked in both inventory and accounting.

**Why this priority**: GRN is the critical bridge between procurement and inventory — it affects stock quantities, costing, and the general ledger simultaneously.

**Independent Test**: Receive 50 units against a PO line of 100 → verify inventory increases by 50 → verify WAC is recalculated → verify an `inventory_transaction` record is created → verify a GL entry is posted (Dr. Inventory Asset, Cr. GRN Accrual) → partially receive remaining 50 → verify PO status updates correctly → verify all quantities in the response are strings not floats.

**Acceptance Scenarios**:

1. **Given** the PO receive form, **When** I enter received quantities, **Then** the frontend sends them as strings (not `parseFloat`) and the backend processes with `Decimal`
2. **Given** a partial receipt, **When** it completes, **Then** the PO line status updates to "partially_received" and remaining quantity is tracked precisely
3. **Given** a receipt operation, **When** it completes, **Then** the system validates fiscal period is open, inventory updates, WAC recalculates via CostingService, and a GL entry posts — all within a single transaction
4. **Given** the receive form, **When** an error occurs (e.g., over-receipt), **Then** a toast notification appears (not just `toastEmitter.emit` or `console.error`)
5. **Given** a receipt that would exceed PO quantity, **When** I submit it, **Then** the backend rejects it with a clear error message

---

### User Story 4 — Purchase Returns with Fiscal Period & Stock Validation (Priority: P1)

As a procurement manager, I process purchase returns for defective or excess goods — the system validates fiscal period status, checks available stock, restores supplier balance, updates inventory, and posts reversal GL entries — so that returns are properly reflected across inventory and accounting with period controls.

**Why this priority**: Purchase returns reverse financial and inventory transactions — they must enforce fiscal period locks (currently missing) and verify stock availability before processing.

**Independent Test**: Create a return for 10 units of a received product → verify fiscal period is checked → verify stock is sufficient → verify inventory decreases → verify a reversal GL entry posts → verify supplier balance updates → verify the return form sends quantities as strings → verify toast errors on failure.

**Acceptance Scenarios**:

1. **Given** a purchase return form, **When** I submit and the fiscal period is closed, **Then** the backend returns HTTP 400 rejecting the operation entirely (hard block, no override) before creating any GL entries
2. **Given** a return that would make available stock negative, **When** I submit it, **Then** the backend rejects it with a clear error about insufficient stock
3. **Given** a purchase return, **When** it completes, **Then** balanced reversal GL entries are posted, inventory is decreased, and supplier balance is adjusted — all atomically
4. **Given** the return form/list pages, **When** the API call fails, **Then** toast errors appear (not `console.error` only)
5. **Given** return monetary values, **When** returned from the API, **Then** they are strings (not `float()` conversions)

---

### User Story 5 — Credit Notes & Debit Notes with Fiscal Period Enforcement (Priority: P1)

As an accounts payable clerk, I issue credit notes (supplier overcharge) and debit notes (additional charges) — each generating balanced GL entries with fiscal period validation — so that post-invoice adjustments are properly recorded and auditable.

**Why this priority**: Credit/debit notes modify the AP balance and GL — they must enforce fiscal period locks (currently missing for both) to maintain accounting integrity.

**Independent Test**: Create a credit note for an existing purchase invoice → verify fiscal period is checked → verify GL entry posts (Dr. AP, Cr. Expense) → create a debit note → verify GL entry posts (Dr. Expense, Cr. AP) → verify all amounts in responses are strings → verify frontend pages show toast on errors.

**Acceptance Scenarios**:

1. **Given** a credit note creation, **When** I submit and the fiscal period is closed, **Then** the backend returns HTTP 400 rejecting the operation entirely (hard block, no override)
2. **Given** a debit note creation, **When** I submit and the fiscal period is closed, **Then** the backend returns HTTP 400 rejecting the operation entirely (hard block, no override)
3. **Given** credit/debit note forms, **When** I enter amounts, **Then** the frontend sends values as strings (not `parseFloat`) and the backend uses `Decimal`
4. **Given** credit/debit note list pages, **When** errors occur during CRUD operations, **Then** toast notifications appear (not `console.error` only)
5. **Given** credit/debit note responses, **When** monetary fields are returned, **Then** they are string representations (not `float()`)

---

### User Story 6 — Suppliers: CRUD, Statements, Payments & Ratings (Priority: P2)

As a procurement manager, I manage supplier records, view supplier statements (transaction history with running balance), process supplier payments, and review supplier ratings — so that supplier relationships are tracked with accurate financial data and performance metrics.

**Why this priority**: Suppliers underpin the procurement cycle — their data feeds into POs, invoices, payments, and matching. Accurate supplier statements and ratings drive informed purchasing decisions.

**Independent Test**: Create a supplier → view supplier statement → verify running balance is computed with string amounts → process a supplier payment → verify GL entry posts → view supplier rating → verify score renders correctly → verify all pages show toast on errors.

**Acceptance Scenarios**:

1. **Given** the supplier form, **When** I submit, **Then** the frontend sends data correctly and errors display as toast notifications
2. **Given** a supplier statement page, **When** loaded, **Then** all transaction amounts and running balances are rendered via `formatNumber()` without loss of precision
3. **Given** a supplier payment form, **When** I submit payment details, **Then** amounts are sent as strings (not `parseFloat`), the backend posts a GL entry, and toast confirms success/failure
4. **Given** the supplier list/details/groups pages, **When** API calls fail, **Then** toast errors appear (not `console.error` or `toastEmitter.emit`)
5. **Given** supplier payment pages (both `Buying/SupplierPayments` and `Purchases/SupplierPayments`), **When** loaded, **Then** both consistently use `useToast` (not mixed `toastEmitter`)

---

### User Story 7 — Three-Way Matching & Tolerance Configuration (Priority: P2)

As an AP supervisor, I run three-way matching (PO ↔ GRN ↔ Invoice) with configurable tolerance thresholds to validate that quantities received and invoiced amounts align with what was ordered — so that payment is only authorized for verified receipts within acceptable variances.

**Why this priority**: Three-way matching is the control gate before payment — it prevents overpayment and fraud, and it enforces procurement discipline.

**Independent Test**: Configure tolerance thresholds (5% quantity, 2% price) → create a match for a PO-GRN-Invoice set → verify the match correctly identifies within-tolerance and out-of-tolerance variances → verify all match line values are strings → verify tolerance config sends values as strings → verify toast errors on match failures.

**Acceptance Scenarios**:

1. **Given** the tolerance configuration page, **When** I save thresholds, **Then** the frontend sends values as strings (not `parseFloat`) and the backend stores them with Decimal precision
2. **Given** a three-way match, **When** computed, **Then** the matching service uses `Decimal` for variance percentage calculations (not `float()` as currently implemented)
3. **Given** match detail responses, **When** line values are returned, **Then** all monetary fields per line are strings (not `float()` conversions)
4. **Given** the match list page, **When** the API call fails, **Then** a toast error appears (not `console.error`)
5. **Given** a match that exceeds tolerance, **When** reviewed, **Then** the system clearly flags which lines are out-of-tolerance with the exact variance amount

---

### User Story 8 — Landed Costs: Allocation & Inventory Cost Adjustment (Priority: P2)

As a cost accountant, I record landed costs (freight, customs, insurance) and allocate them to purchase invoice lines by quantity or value — the system recalculates product costs and posts GL entries — so that the true cost of goods is accurately reflected in inventory valuation.

**Why this priority**: Landed costs affect inventory valuation and COGS — incorrect allocation cascades into financial misstatements across inventory and accounting modules.

**Independent Test**: Create a landed cost with 3 cost items → allocate to a purchase invoice with multiple lines → verify allocation computes correctly with `Decimal` → verify inventory cost is updated → verify GL entries post (Dr. Inventory, Cr. Landed Cost Clearing) → verify all responses use strings for amounts → verify the landed cost pages show toast on errors.

**Acceptance Scenarios**:

1. **Given** the landed cost create form, **When** I enter cost amounts, **Then** the frontend sends them as strings (not `parseFloat` on a `float` field)
2. **Given** a landed cost allocation, **When** it computes shares, **Then** the backend uses `Decimal` (not `float(share.quantize(...))` as currently implemented) and assigns any rounding remainder to the largest line item so that allocations sum exactly to the total
3. **Given** a landed cost posting, **When** it completes, **Then** the system validates fiscal period is open via `check_fiscal_period_open()`, inventory costs are updated, and balanced GL entries are created
4. **Given** landed cost responses, **When** amounts are returned, **Then** they are strings (not `float()` conversions)
5. **Given** the landed cost pages (already have `useToast`), **When** errors occur, **Then** toast notifications display correctly

---

### User Story 9 — RFQ, Purchase Agreements & Blanket POs (Priority: P3)

As a procurement planner, I create RFQs to solicit supplier quotes, convert winning quotes to POs, manage purchase agreements with quantity/value limits, and track blanket PO releases — so that strategic sourcing decisions are data-driven and contract compliance is enforced.

**Why this priority**: These are advanced procurement workflows that build on the core PO cycle — they need correct pricing data but are less frequently used than daily PO/invoice operations.

**Independent Test**: Create an RFQ → receive responses → convert to PO → verify conversion preserves amounts as strings → create a purchase agreement → release orders against it → verify consumed quantities and remaining limits use string amounts → verify blanket PO detail shows amounts via `formatNumber()`.

**Acceptance Scenarios**:

1. **Given** an RFQ conversion to PO, **When** the conversion runs, **Then** all amounts (total_price) are passed as strings (not `float()`)
2. **Given** a purchase agreement, **When** I view remaining amounts, **Then** they are displayed as strings from backend and rendered via `formatNumber()` (not `float()` conversions)
3. **Given** a blanket PO form, **When** I enter quantities and prices, **Then** the frontend sends values as strings (not `parseFloat`) and the backend processes with `Decimal`
4. **Given** blanket PO release operations, **When** releases track consumed vs remaining, **Then** all computations use `Decimal` (not `float()`) and responses are strings
5. **Given** RFQ/agreement pages, **When** errors occur, **Then** toast notifications appear (not `console.error` only)

---

### User Story 10 — Pydantic Schema Decimal Enforcement (Priority: P1)

As a system architect, all purchase-related Pydantic schemas must use `Decimal` types for monetary and quantity fields instead of `float` — so that the validation pipeline enforces precision from the API boundary through to the database.

**Why this priority**: The Pydantic schemas are the API boundary — if they accept `float`, precision is lost before business logic even runs. This is a foundational fix that affects all endpoints.

**Independent Test**: Change all `float` fields in `backend/schemas/purchases.py` to `Decimal` → verify the API still accepts both string and numeric input → verify validation errors trigger correctly → verify downstream routers receive `Decimal` values from Pydantic models.

**Acceptance Scenarios**:

1. **Given** `PurchaseLineItem` schema, **When** defining fields, **Then** `quantity`, `unit_price`, `tax_rate`, `discount`, `markup` use `Decimal` type (not `float`)
2. **Given** `PurchaseCreate` schema, **When** defining fields, **Then** `paid_amount`, `exchange_rate` use `Decimal` type
3. **Given** all other purchase schemas (`POCreate`, `ReceiveItem`, `SupplierPaymentCreate`, etc.), **When** defining monetary fields, **Then** all use `Decimal` type
4. **Given** a matching tolerance schema (`ToleranceSave`), **When** defining fields, **Then** percentage and absolute tolerance values use `Decimal`
5. **Given** the landed cost schema (`LandedCostItemCreate`), **When** defining the amount field, **Then** it uses `Decimal` (not `float = 0`)

---

### User Story 11 — Audit Column Completeness (Priority: P1)

As a system auditor, all procurement database tables must have complete audit columns (`created_at`, `updated_at`, `created_by`, `updated_by`) — so that every record's creation and modification history is fully traceable.

**Why this priority**: Missing audit columns mean untraceable changes — this is a compliance requirement for Saudi regulatory standards and the system constitution.

**Independent Test**: Run migration to add missing columns → verify all procurement tables have the 4 audit columns → verify `database.py` CREATE TABLE definitions match → verify domain models reflect the columns → create and update records → verify audit columns are populated.

**Acceptance Scenarios**:

1. **Given** tables `purchase_orders`, `request_for_quotations`, `supplier_ratings`, `purchase_agreements`, `landed_costs`, **When** checked, **Then** all have `updated_by` column (currently missing)
2. **Given** tables `purchase_order_lines`, `rfq_lines`, `rfq_responses`, `purchase_agreement_lines`, `landed_cost_items`, `landed_cost_allocations`, **When** checked, **Then** all have full audit columns (multiple missing)
3. **Given** a migration is created, **When** applied, **Then** it adds all missing audit columns with appropriate types and foreign key references
4. **Given** `database.py` CREATE TABLE definitions, **When** updated, **Then** they match the migration changes exactly (triple-update)
5. **Given** domain models in `backend/models/domains/procurement.py` and `backend/models/domain_models/`, **When** updated, **Then** they reflect all audit columns (triple-update)

---

### User Story 12 — Purchases Reports & Aging (Priority: P2)

As a financial controller, I view purchasing reports and the purchases aging report — so that I can monitor spending patterns, overdue payables, and supplier performance with accurate monetary data.

**Why this priority**: Reports consolidate data from across the module — they must reflect the precision fixes applied to underlying data and show toast errors for failed loads.

**Independent Test**: Open the purchases aging report → verify amounts render via `formatNumber()` → trigger an API error → verify toast appears → verify report data matches GL balances.

**Acceptance Scenarios**:

1. **Given** the buying reports page, **When** loaded, **Then** all monetary values render via `formatNumber()` and errors show as toast
2. **Given** the purchases aging report, **When** loaded, **Then** aging buckets and balances are computed with Decimal precision and rendered as formatted strings
3. **Given** any report page error, **When** the API call fails, **Then** a toast notification appears (not `console.error`)

---

### Edge Cases

- What happens when a PO line has a discount AND a markup applied simultaneously? The backend must calculate them in the correct order with Decimal precision.
- What happens when landed cost allocation divides unevenly (e.g., 100 SAR across 3 items)? The system must assign the rounding remainder to the largest line item ("largest remainder" method) and ensure the allocation splits sum exactly to the total.
- What happens when a blanket PO release would exceed the agreement limit? The backend must reject with a clear error.
- What happens when a purchase return references a product that has already been fully consumed in manufacturing? The system must check available stock against reserved quantities.
- What happens when a supplier payment is in a foreign currency? The exchange rate must be locked at transaction date.

## Requirements

### Functional Requirements

- **FR-001**: System MUST convert all 76 backend `float()` conversions in `purchases.py`, `landed_costs.py`, and `matching.py` to `str()` for response serialization, preserving `Decimal` precision
- **FR-002**: System MUST convert all 18 Pydantic schema `float` fields in `schemas/purchases.py`, `matching.py`, and `landed_costs.py` to `Decimal` type
- **FR-003**: System MUST convert all 2 `float()` usages in `matching_service.py` to `Decimal` for variance calculations
- **FR-004**: System MUST replace all 81 `parseFloat()` calls across 12 frontend files with `String()` (payloads), `Number()` (local comparisons), or `formatNumber()` (display rendering)
- **FR-005**: System MUST replace all 48 `console.error` patterns across 31 frontend pages with `showToast(translatedMessage, 'error')` via the `useToast` hook
- **FR-006**: System MUST replace all 17 `toastEmitter.emit()` calls across 7 frontend files with `showToast()` via the `useToast` hook, and remove the `toastEmitter` import
- **FR-007**: System MUST add `check_fiscal_period_open()` validation to ALL GL-posting endpoints — `create_purchase_return`, `create_purchase_credit_note`, `create_purchase_debit_note`, `receive_purchase_order`, and `post_landed_cost` — before GL entry creation (invoice already has it). A closed period MUST result in a hard block (HTTP 400) with no role-based override
- **FR-008**: System MUST add missing audit columns to 8+ procurement tables via Alembic migration, with matching updates to `database.py` CREATE TABLE definitions and domain models (triple-update)
- **FR-009**: Existing GL posting for all 6 financial endpoints (invoice, return, credit note, debit note, PO receive, landed cost post) MUST continue to function correctly after precision fixes
- **FR-010**: Three-way matching validation MUST remain functional and use Decimal throughout after precision fixes to the matching service

### Key Entities

- **Purchase Order**: Core procurement document with line items, discounts, markups, tax, and approval workflow
- **Purchase Invoice**: Financial obligation linked to PO, triggers AP and GL posting
- **Purchase Return**: Reversal of received goods, affects inventory and GL
- **Credit Note / Debit Note**: Post-invoice adjustments to AP balance and GL
- **Supplier**: Party entity with contacts, bank accounts, groups, ratings, statements, and payments
- **Landed Cost**: Additional costs (freight, customs, insurance) allocated to PO lines, affects inventory valuation
- **Three-Way Match**: PO ↔ GRN ↔ Invoice validation with configurable tolerance
- **RFQ**: Request for quotation with supplier responses, convertible to PO
- **Purchase Agreement / Blanket PO**: Framework contracts with quantity/value limits and release tracking

## Success Criteria

### Measurable Outcomes

- **SC-001**: Zero `float()` type usage in all backend purchase router/service/schema files — all monetary and quantity fields use `Decimal` internally and `str()` for API serialization
- **SC-002**: Zero `parseFloat()` usage in all 36 frontend purchase-related pages — replaced with `String()`, `Number()`, or `formatNumber()` as appropriate
- **SC-003**: Zero `console.error` as the sole error feedback in any purchase-related page — all replaced with `useToast` user-facing notifications
- **SC-004**: Zero `toastEmitter` usage in any purchase-related page — all replaced with `useToast` hook
- **SC-005**: All 6 GL-posting endpoints (invoice, return, credit note, debit note, PO receive, landed cost post) validate fiscal period is open before creating GL entries
- **SC-006**: All procurement database tables pass audit column completeness check — full `created_at`, `updated_at`, `created_by`, `updated_by` coverage
- **SC-007**: `python3 -m py_compile` passes on all modified backend files with zero syntax errors
- **SC-008**: `npx vite build` succeeds with zero compilation errors in the frontend
- **SC-009**: Three-way matching and landed cost allocation produce identical results before and after precision fixes
- **SC-010**: All 36 frontend purchase pages render monetary values via `formatNumber()` without "NaN", "undefined", or floating-point artifacts

## Clarifications

### Session 2026-04-15

- Q: Should PO Receive (GRN) and Landed Cost Post also enforce fiscal period validation like the other 4 GL-posting endpoints? → A: Yes — all 6 GL-posting endpoints must validate fiscal period. If it posts to the GL, it must check the period.
- Q: How should landed cost allocation handle rounding remainders when amounts divide unevenly? → A: Assign the remainder to the largest line item ("largest remainder" accounting convention).
- Q: When a fiscal period is closed, should GL-posting endpoints hard block or allow role-based override? → A: Hard block (HTTP 400) with no override. Reopening a period is an explicit admin action through the fiscal period management UI.

## Assumptions

- The existing GL posting logic in all 6 endpoints is correct in terms of account selection and entry structure — only the precision (float→Decimal/str) needs fixing
- The `useToast` hook and `ToastContext` are already established patterns in the codebase and require no infrastructure changes
- The `formatNumber()` utility function from `../../utils/format` is already available and tested
- Pydantic `Decimal` type serialization works correctly with FastAPI's JSON encoder
- The 10 frontend files that already have `useToast` imported do not need useToast addition, but may still need `parseFloat` or `console.error` fixes
- Missing audit columns can be added with `IF NOT EXISTS` to be idempotent across existing tenant databases
- The `matching_service.py` float→Decimal fix will not change matching outcomes for values within the Decimal precision range (18,4)
- Frontend files in `Purchases/` directory (PaymentForm, PaymentDetails, SupplierPayments) are separate from the `Buying/SupplierPayments.jsx` and both need fixes
