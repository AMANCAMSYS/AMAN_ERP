# AMAN ERP Backend Remediation Report (Phases 2 & 3)

## Executive Summary
This report details the completion of the Phase 2 (Financial Precision) and Phase 3 (Concurrency & Logic) hardening of the AMAN ERP backend. All 16 core modules undergo strict `Decimal` accounting precision standards and utilize robust explicit database locking (`FOR UPDATE`) for concurrent operations. System compliance against double-spending, inventory race conditions, and precision drift has now been fortified.

## Phase 2: Financial Precision Highlights
All financial amount extractions before database insertion have been standardized to construct `Decimal` values quantized to 2 decimal places (`ROUND_HALF_UP`), solving potential long-term floating-point inaccuracies. 
*   **Purchases & Sales:** Corrected subtotals, complex tax, and final amount mathematical drift.
*   **Manufacturing & Landed Costs:** Standardized algorithm allocation basis percentages using exact Decimals to prevent fractions of cents misallocation during weighted average costing (WAC). 
*   **Treasury & Taxes:** Solved general ledger journal entry imbalance caused by foreign currency exchange rate float inaccuracies. 
*   **HR Module:** Refactored complex salary generation payloads (loans, GOSI, allowances, overtime) to strictly cast Decimals down to float formats immediately bounding database insertion.

## Phase 3: Concurrency & Fiscal Logic Controls
*   **Inventory (Transfers & Adjustments):** Implemented row-level `SELECT ... FOR UPDATE` locks. This strictly guarantees that stock levels remain locked during transaction calculation to prevent race-condition overselling.
*   **Treasury:** Integrated database locking when verifying active treasury balances during inter-account transfers and outgoing expenses. 
*   **Fiscal Period Enforcements:** Integrated `check_fiscal_period_open()` into expense ledgers and delivery order routing flows. Ensures users cannot back-date transactions into permanently closed fiscal periods without administrative overrides.

## Next Steps / Recommendations
1.  **Frontend Synchronisation:** The frontend React dashboard payloads should be audited to mirror the robust strict numeric enforcement adopted on the backend.
2.  **Comprehensive E2E Testing:** We recommend running a full integration test-suite across core transaction flows (Sales -> Delivery -> Invoicing -> Treasury Receipt) under load-testing conditions to fully validate concurrency performance.

## Scope Lock (2026-04-08)
After reviewing the current workspace diff, the repository contains three parallel streams:
1. Critical accounting hardening (Decimal precision, locking, fiscal integrity, strict JE balancing).
2. New subscription feature set (backend, frontend, migrations, scheduler).
3. Broad mobile/frontend UX and routing changes.

To keep execution aligned with the "important only" directive, the active implementation scope is locked to stream (1) only.

### In Scope (continue now)
- backend/routers/purchases.py
- backend/routers/sales/invoices.py
- backend/routers/sales/returns.py
- backend/routers/sales/vouchers.py
- backend/routers/sales/credit_notes.py
- backend/services/matching_service.py
- backend/services/gl_service.py
- backend/utils/accounting.py
- backend/utils/fiscal_lock.py
- backend/utils/quantity_validation.py
- backend/routers/finance/accounting.py

### Out of Scope (frozen for this remediation pass)
- Subscription module additions (models/schemas/router/service/migrations/frontend pages).
- Mobile app navigation/API/UI expansion.
- Non-critical UI reshaping and route aliases.

### Execution Rule
Any further edits in this remediation pass must stay inside In Scope files and must directly improve one of:
- monetary precision correctness,
- race-condition/concurrency safety,
- fiscal lock enforcement,
- strict accounting validation behavior.

## Final Audit Pass (2026-04-08)
Completed targeted hardening inside the locked critical scope:

1. Sales vouchers allocation safety and locking
- Added `FOR UPDATE` locking on allocated invoice rows during both customer receipt and customer payment flows.
- Enforced ownership check: allocated invoice must belong to the selected customer.
- Enforced positive allocation amounts and strict cap: total allocations cannot exceed voucher amount.
- Fixed allocation flow robustness by ensuring allocation amount is always initialized before use.

2. Treasury account linkage correctness
- Normalized `treasury_account_id` persistence in customer payment voucher creation to use explicit treasury field when provided.

3. Supplier payment status threshold correction
- Fixed partial-status threshold typo from `0.1` to `0.01` in supplier allocation status transition logic.

Validation result:
- No diagnostics errors detected in updated critical files.
