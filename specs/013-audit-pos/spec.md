# Feature Specification: Audit POS Module — تدقيق وحدة نقاط البيع

**Feature Branch**: `013-audit-pos`  
**Created**: 2026-04-15  
**Status**: Draft  
**Input**: User description: "audit-pos — نقاط البيع. لاتنسى ان تجعل كل شيء مرتبط بالفرونت اند بالشكل الصحيح"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Numeric Precision Across All POS Endpoints (Priority: P1) 🎯 MVP

An auditor reviewing POS transaction data must see exact monetary values (e.g., "1234.56") rather than floating-point approximations (e.g., "1234.5600000001"). All backend POS endpoints must serialize monetary fields as strings using `str()` instead of `float()`, and all Pydantic schemas must use `Decimal` instead of `float` for monetary/quantity/rate fields.

**Why this priority**: Floating-point serialization is the most fundamental audit deficiency — it affects every POS transaction, session report, and financial reconciliation. Without exact values, no downstream audit finding is reliable.

**Independent Test**: `grep -rn "float(" backend/routers/pos.py | grep -v "#" | wc -l` → 0; `grep -rn ": float" backend/schemas/pos.py | wc -l` → 0

**Acceptance Scenarios**:

1. **Given** a POS order with subtotal 99.95 and tax 14.99, **When** the order details endpoint returns the order, **Then** `total_amount` is the string `"114.94"`, not the float `114.94000000000001`
2. **Given** a POS session closed with opening 5000 and closing 5347.50, **When** the session report is retrieved, **Then** `difference` is `"347.50"`, not `347.5`
3. **Given** a Pydantic schema `OrderLineCreate`, **When** it receives `quantity: "2.5"`, **Then** it is parsed as `Decimal("2.5")`, not `float(2.5)`

---

### User Story 2 — Frontend Sends Correct Data Types to Backend (Priority: P1)

A cashier using the POS interface enters prices, quantities, and payment amounts. The frontend must send numeric values as `String()` in API payloads (not `parseFloat()`) and use `Number()` only for local display calculations. This ensures the backend receives exact values that can be parsed into `Decimal` without floating-point intermediate conversion.

**Why this priority**: If the frontend sends `parseFloat("99.95")` = `99.94999999999999`, the backend stores an incorrect amount. This directly affects financial integrity.

**Independent Test**: `grep -rn "parseFloat" frontend/src/pages/POS/ | wc -l` → 0

**Acceptance Scenarios**:

1. **Given** a cashier enters quantity 2.5 in POSInterface, **When** the order is submitted, **Then** the API payload contains `quantity: "2.5"` (string), not `quantity: 2.5` (float)
2. **Given** a cashier closes a POS session with cash register balance 5347.50, **When** the close-session API is called, **Then** `closing_balance` is sent as `"5347.50"` (string)
3. **Given** loyalty points are being redeemed, **When** the redeem API is called, **Then** the points value is sent as `String()`

---

### User Story 3 — User-Visible Error Handling via Toast Notifications (Priority: P1)

When a POS operation fails (order creation, session close, return processing, network error), the user sees a clear toast notification instead of the error being silently logged to `console.error`. All `console.error` calls in POS frontend files must be replaced with `showToast` from the `useToast` hook. Additionally, leftover `console.log` debug statements must be removed from production code.

**Why this priority**: In a retail POS environment, silent failures can result in lost sales, incorrect cash counts, or unprocessed returns. Cashiers need immediate visual feedback.

**Independent Test**: `grep -rn "console\.error\|console\.log" frontend/src/pages/POS/ | wc -l` → 0

**Acceptance Scenarios**:

1. **Given** a network error occurs during order creation in POSInterface, **When** the API call fails, **Then** the cashier sees a toast notification "حدث خطأ" (error occurred)
2. **Given** the POS session close fails, **When** the error is caught, **Then** a toast is shown (not a silent `console.error`)
3. **Given** HeldOrders.jsx is loaded, **When** the component renders, **Then** no `console.log` debug output appears in the browser console

---

### User Story 4 — Correct Display Formatting with formatNumber (Priority: P1)

All monetary values displayed in POS pages (order totals, item prices, session balances, refund amounts) must use the `formatNumber()` utility instead of raw `.toLocaleString()`. This ensures consistent formatting that respects the company's configured decimal precision.

**Why this priority**: Inconsistent number formatting across the POS interface creates confusion for cashiers and makes printed receipts look unprofessional. The `formatNumber()` utility already handles company-specific decimal places — using raw `.toLocaleString()` bypasses this.

**Independent Test**: `grep -rn "toLocaleString\|\.toFixed" frontend/src/pages/POS/ | wc -l` → 0 for monetary values (date `.toLocaleString()` is acceptable)

**Acceptance Scenarios**:

1. **Given** a company configured with 3 decimal places, **When** a POS order total of 114.940 is displayed in POSInterface, **Then** it shows "114.940" (3 decimals), not "114.94" (browser default)
2. **Given** POSReturns shows a refund amount, **When** the refund total is rendered, **Then** it uses `formatNumber(refundAmount)` instead of `refundAmount.toLocaleString()`
3. **Given** HeldOrders shows order totals, **When** the list renders, **Then** each total uses `formatNumber()` for consistent display

---

### User Story 5 — Pydantic Schema Decimal Types (Priority: P1)

All Pydantic schemas for POS (`backend/schemas/pos.py`) must use `Decimal` instead of `float` for monetary, quantity, and rate fields. This matches the database column types (`DECIMAL(18,4)`) and prevents precision loss at the API boundary.

**Why this priority**: The schema layer is the entry point for all POS data. If schemas accept `float`, precision is already lost before reaching the database. This is a foundational fix that all other precision work depends on.

**Independent Test**: `grep -rn ": float" backend/schemas/pos.py | wc -l` → 0

**Acceptance Scenarios**:

1. **Given** `SessionCreate` schema, **When** `opening_balance: "5000.00"` is submitted, **Then** Pydantic parses it as `Decimal("5000.00")`
2. **Given** `OrderLineCreate` schema, **When** `unit_price: "99.95"` and `quantity: "2"` are submitted, **Then** both are `Decimal` types
3. **Given** `OrderResponse` schema, **When** serialized to JSON, **Then** `total_amount` is rendered as a string (not a floating-point number)

---

### User Story 6 — Audit Trail Columns on All POS Tables (Priority: P2)

All POS domain models must inherit `AuditMixin` to gain consistent `created_at`, `updated_at`, `created_by`, and `updated_by` columns. The corresponding database tables must have these columns added through `sync_essential_columns()`. This enables auditors to track who created or modified every POS record.

**Why this priority**: Without audit columns, there is no way to trace who opened a session, who modified a promotion, or who processed a return. This is a compliance requirement for financial systems.

**Independent Test**: All 13 POS models in `sales_pos.py` inherit `AuditMixin`; `sync_essential_columns()` includes all POS tables.

**Acceptance Scenarios**:

1. **Given** a POS session is opened by user "cashier1", **When** the session record is created, **Then** `created_by` = "cashier1" and `created_at` is set automatically
2. **Given** a promotion is updated, **When** the update is saved, **Then** `updated_by` reflects the user who made the change and `updated_at` is refreshed
3. **Given** an auditor queries `pos_orders`, **When** they filter by `created_by`, **Then** all orders have a non-null `created_by` value

---

### User Story 7 — Fiscal Period Validation on GL-Posting Endpoints (Priority: P2)

Every POS endpoint that creates general ledger (GL) entries must validate that the fiscal period is open before posting. Currently, only `create_order` has this check. The `close_session` (cash over/short GL entry) and `create_return` (reversal GL entry) endpoints are missing this critical validation.

**Why this priority**: Posting to a closed fiscal period corrupts the accounting records. If a cashier processes a return or closes a session after the period is locked, the GL entries bypass the fiscal lock — a direct audit violation.

**Independent Test**: `grep -n "check_fiscal_period_open" backend/routers/pos.py` → returns 3 matches (create_order, close_session, create_return)

**Acceptance Scenarios**:

1. **Given** the current fiscal period is closed, **When** a cashier attempts to close a POS session with a cash difference, **Then** the system rejects with "الفترة المالية مقفلة" before creating any GL entry
2. **Given** the current fiscal period is closed, **When** a cashier attempts to process a POS return, **Then** the system rejects with an appropriate error before creating the reversal GL entry
3. **Given** the fiscal period is open, **When** a POS return is processed, **Then** the GL reversal entry is created successfully

---

### User Story 8 — Commission-Free POS Order Verification (Priority: P3)

POS orders do not generate sales commissions (commissions are handled through the sales module for non-POS invoices). Verify that no commission calculation logic exists in the POS flow that could produce incorrect financial entries.

**Why this priority**: Lower priority because POS orders typically don't involve commissions, but a verification pass is needed to confirm no accidental commission triggers exist.

**Independent Test**: `grep -rn "commission" backend/routers/pos.py` → 0 matches

**Acceptance Scenarios**:

1. **Given** a POS order is completed, **When** the GL entry is posted, **Then** no commission-related journal lines are created
2. **Given** the POS order flow, **When** reviewed end-to-end, **Then** there are no references to commission calculation functions

---

### Edge Cases

- What happens when a POS return is attempted after the fiscal period is closed? → System rejects with fiscal period error
- What happens when a session is closed with exactly zero cash difference? → No GL entry is created (existing behavior is correct)
- What happens when `.toLocaleString()` is called on a date value (not monetary)? → Date formatting with `.toLocaleString()` is acceptable and should not be replaced with `formatNumber()`
- What happens when a held order has stale prices when resumed? → Out of scope for this audit (functional behavior, not precision issue)
- What happens when offline POS syncs data after the fiscal period closes? → Edge case noted but out of scope for this audit (offline sync is a separate concern)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST serialize all monetary values in POS API responses using `str()` instead of `float()` to preserve exact decimal representation
- **FR-002**: System MUST use `Decimal` type for all monetary, quantity, and rate fields in POS Pydantic schemas (`backend/schemas/pos.py`)
- **FR-003**: All POS frontend files MUST send monetary/quantity values as `String()` in API payloads, not `parseFloat()`
- **FR-004**: All POS frontend files MUST use `Number()` instead of `parseFloat()` for local display calculations
- **FR-005**: All POS frontend error handling MUST use `showToast()` from `useToast` hook instead of `console.error()`
- **FR-006**: All leftover `console.log` debug statements MUST be removed from POS frontend production code
- **FR-007**: All monetary display values in POS frontend MUST use `formatNumber()` from `utils/format` instead of raw `.toLocaleString()` (date formatting excluded)
- **FR-008**: All 13 POS domain models MUST inherit `AuditMixin` for consistent audit trail columns
- **FR-009**: Missing audit columns (`created_at`, `updated_at`, `created_by`, `updated_by`) MUST be added to all POS tables via `sync_essential_columns()`
- **FR-010**: `check_fiscal_period_open()` MUST be called before every GL-posting operation in `pos.py` — including `close_session` and `create_return`, not just `create_order`
- **FR-011**: POS return endpoint MUST validate that the fiscal period is open before creating GL reversal entries
- **FR-012**: POS session close endpoint MUST validate that the fiscal period is open before creating cash over/short GL entries

### Key Entities

- **POS Session**: Represents a cashier's shift at a register — tracks opening/closing balances, total sales, returns, and cash differences
- **POS Order**: A point-of-sale transaction with line items, payments, discounts, and optional loyalty/promotion application
- **POS Order Line**: Individual product within an order — quantity, price, tax, discount
- **POS Payment**: Payment method and amount for an order (cash, card, etc.)
- **POS Return**: Refund against a paid order with item-level detail and GL reversal
- **POS Promotion**: Discount rules (percentage, fixed, buy-X-get-Y, coupon) with date ranges and product scope
- **POS Loyalty Program**: Points earning/redemption rules with tier support
- **POS Table**: Restaurant table management with seating and order linking
- **POS Kitchen Order**: Kitchen display queue for order preparation tracking

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero `float()` calls remain in `backend/routers/pos.py` for monetary serialization — verified by grep
- **SC-002**: Zero `: float` type annotations remain in `backend/schemas/pos.py` — verified by grep
- **SC-003**: Zero `parseFloat` calls remain in `frontend/src/pages/POS/` — verified by grep
- **SC-004**: Zero `console.error` calls remain in `frontend/src/pages/POS/` — verified by grep
- **SC-005**: Zero `console.log` calls remain in `frontend/src/pages/POS/` — verified by grep
- **SC-006**: Zero `.toLocaleString()` calls on monetary values remain in POS frontend — verified by grep (date `.toLocaleString()` excluded)
- **SC-007**: All 13 POS models inherit `AuditMixin` — verified by grep count in `sales_pos.py`
- **SC-008**: `check_fiscal_period_open` appears at least 3 times in `pos.py` — verified by grep
- **SC-009**: All modified backend files pass `py_compile` with zero errors
- **SC-010**: Frontend builds successfully with `npx vite build` — zero errors

## Assumptions

- The existing `AuditMixin` from `backend/models/base.py` provides `created_at`, `updated_at`, `created_by`, and `updated_by` columns — same pattern used in sales audit (012)
- The `formatNumber()` utility in `frontend/src/utils/format.js` handles company-specific decimal precision — no custom POS formatting is needed
- Date-related `.toLocaleString()` calls (e.g., timestamps, date display) are NOT monetary and should be left as-is
- The `useToast` hook and `showToast` function are already available in the project's Toast context
- POS offline synchronization and conflict resolution are out of scope for this audit
- The duplicate payment tables (`pos_payments` and `pos_order_payments`) are a design concern but not addressed in this audit — focus is on data precision and audit trail
- Loyalty point calculations use integer arithmetic (whole points) and do not require Decimal conversion
- The existing `validate_je_lines` function should ideally be added to `close_session` and `create_return` GL entries, but this is a functional improvement beyond the audit scope
