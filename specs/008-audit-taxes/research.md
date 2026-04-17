# Research: audit-taxes — الضرائب والزكاة

**Branch**: `008-audit-taxes` | **Date**: 2026-04-15  
**Status**: Complete — all NEEDS CLARIFICATION resolved

---

## R-01: WHT Transactions Endpoint Existence

**Decision**: Both WHT endpoint directions are fully implemented.

**Findings**:
- `POST /external/wht/transactions` → exists at `external.py` line ~461; creates certificate + optional GL entry; guarded by `require_permission(["accounting.edit", "taxes.manage"])`
- `GET /external/wht/transactions` → exists at `external.py` line ~519; supports `supplier_id`, `from_date`, `to_date` filters

**Rationale**: No missing endpoints for WHT certificate lifecycle. Frontend `WithholdingTax.jsx` correctly maps to `externalAPI.listWhtTransactions()` and `externalAPI.createWhtTransaction()`.

**Alternatives considered**: N/A — endpoints exist.

---

## R-02: Permission Decorators Coverage

**Decision**: Both tax routers use `require_permission()` with appropriate permission lists; pattern is consistent.

**Findings**:
- `taxes.py`: Router-level `dependencies=[Depends(require_module("taxes"))]` + per-endpoint `require_permission(["accounting.view", "taxes.view"])` or `["accounting.edit", "taxes.manage"]`
- `tax_compliance.py`: Same router-level pattern; branch-settings PUT uses `["taxes.manage", "branches.manage"]`
- No unguarded endpoints found in either file

**Rationale**: Constitution §IV compliance confirmed — every tax endpoint has at least module-level gate plus action-level permission.

**Alternatives considered**: N/A — guards are correctly applied.

---

## R-03: Zakat GL Posting Mechanism

**Decision**: Zakat calculation reads from posted GL journal entries via `journal_lines`; the separate "post Zakat" action is handled as a journal entry via the accounts balance system.

**Findings**:
- `calculate_zakat` in `system_completion.py` aggregates from `journal_lines` (posted entries only) using account code patterns for cash (1101xx), trade goods (1103xx, 13001xx), receivables, investments
- `_zakat_balance_query()` helper fetches from both `journal_lines` and `accounts.balance`
- Constitution §III compliance: calculation relies on existing posted GL data; the separate GL post for "Zakat Expense" uses `update_account_balance()` patterns consistent with other financial postings
- The Zakat posting creates a balanced JE (Dr. Zakat Expense / Cr. Zakat Payable)

**Rationale**: GL integrity maintained — Zakat calculation is read-only from posted data; Zakat GL entry creation follows constitution pattern that all postings go through account balance update with journal line insertion.

**Alternatives considered**: Using ORM models directly — rejected per Constitution §VII SQL-first mandate.

---

## R-04: ZATCA QR Code on Invoice Creation

**Decision**: ZATCA QR code is automatically generated at invoice creation time; not optional; fails gracefully.

**Findings**:
- `backend/routers/sales/invoices.py` line ~661: `process_invoice_for_zatca(db, invoice_id, company_id)` is called immediately after invoice is posted
- QR code result stored and returned in invoice response as `zatca_qr` field
- If ZATCA generation fails (network, keys not set up), exception is caught and logged with `logger.warning()`; invoice creation still succeeds (graceful degradation)
- ZATCA QR encodes: `seller_name`, `vat_number`, `invoice_timestamp`, `total_amount`, `vat_amount` per ZATCA TLV standard

**Rationale**: Phase 1 ZATCA compliance is automatic. Phase 2 (cryptographic signature) is triggered by `zatca_phase` setting in `CompanyTaxSetting`.

**Alternatives considered**: Manual QR generation only — rejected because Phase 1 is a legal mandate and must be automatic.

---

## R-05: Frontend taxes.js API Endpoint Map

**Decision**: All frontend tax service functions use correct paths that match backend routes; no mismatches found.

**Findings**:

| Frontend function | Mapped endpoint | Exists in backend |
|------------------|----------------|-------------------|
| `taxesAPI.listRates()` | `GET /taxes/rates` | ✅ taxes.py |
| `taxesAPI.createRate()` | `POST /taxes/rates` | ✅ taxes.py |
| `taxesAPI.updateRate(id)` | `PUT /taxes/rates/{id}` | ✅ taxes.py |
| `taxesAPI.deleteRate(id)` | `DELETE /taxes/rates/{id}` | ✅ taxes.py |
| `taxesAPI.listReturns()` | `GET /taxes/returns` | ✅ taxes.py |
| `taxesAPI.createReturn()` | `POST /taxes/returns` | ✅ taxes.py |
| `taxesAPI.fileReturn(id)` | `PUT /taxes/returns/{id}/file` | ✅ taxes.py |
| `taxesAPI.cancelReturn(id)` | `PUT /taxes/returns/{id}/cancel` | ✅ taxes.py |
| `taxesAPI.listCalendar()` | `GET /taxes/calendar` | ✅ taxes.py |
| `taxesAPI.completeCalendarItem(id)` | `PUT /taxes/calendar/{id}/complete` | ✅ taxes.py |
| `taxComplianceAPI.getCompanySettings()` | `GET /tax-compliance/company-settings` | ✅ tax_compliance.py |
| `taxComplianceAPI.updateCompanySettings()` | `PUT /tax-compliance/company-settings` | ✅ tax_compliance.py |
| `taxComplianceAPI.getSaudiVATReport()` | `GET /tax-compliance/reports/sa-vat` | ✅ tax_compliance.py |
| `taxComplianceAPI.getOverview()` | `GET /tax-compliance/overview` | ✅ tax_compliance.py |

**Rationale**: No 404-causing endpoint mismatches. API base URL comes from `apiClient` config, not hardcoded.

**Gap identified**: `taxes.js` is missing `getSummary()`, `getVATReport()`, `getTaxAudit()`, `getBranchAnalysis()`, `getEmployeeTaxes()` — these exist as backend endpoints but have no corresponding frontend service function. Frontend pages may be calling them directly with `api.get(...)` inline rather than through the service.

---

## R-06: Hardcoded Mock Data in Frontend Tax Pages

**Decision**: No hardcoded transaction mock data arrays found in tax pages. All data fetched from backend APIs.

**Findings**:
- `TaxHome.jsx`: Uses `taxesAPI.listRates()`, `taxesAPI.listReturns()`, `useState` with empty arrays as initial state
- `WithholdingTax.jsx`: Uses `externalAPI.listWhtRates()` and `externalAPI.listWhtTransactions()`; only static constant is WHT category labels (UI UX text, not data)
- `TaxCompliance.jsx`: Uses `taxComplianceAPI.getOverview()`, `listCountries()`, `listRegimes()`; `COUNTRY_FLAGS` object is purely cosmetic UI mapping

**Gap identified**: Several pages initialize with empty arrays (e.g., `const [rates, setRates] = useState([])`) which is correct, but the audit must verify error handling is present — some pages may show a blank table on API error instead of an error message.

**Rationale**: No mock data contamination. The API wiring pattern exists; the audit focus shifts to loading/error state coverage.

---

## R-07: Tax Calendar Recurring Item Handling

**Decision**: Recurring calendar logic is implemented — marks current item complete and creates next occurrence using `relativedelta(months=recurrence_months)`.

**Findings**:
- `PUT /taxes/calendar/{id}/complete` handler in `taxes.py` line ~1569:
  1. Fetches calendar item
  2. Sets `is_completed = true` on current item
  3. If `is_recurring = true`: calculates `next_due = due_date + relativedelta(months=recurrence_months)`
  4. INSERTs new calendar row with same title, tax_type, reminder_days, notes
  5. Returns `{"message": "Completed", "next_recurrence_id": new_id}`
- `recurrence_months` stored as integer (1 = monthly, 3 = quarterly, 12 = annual)

**Rationale**: Correct implementation. No changes needed. Frontend only needs to handle the `next_recurrence_id` in the response to optionally navigate/highlight the new item.

**Alternatives considered**: Cron-based schedule generation — rejected for supporting existing event-driven completion model.

---

## R-08: ZakatCalculator — Saudi Arabia Gating Mechanism

**Decision**: Frontend gate uses `getCountry()` utility to extract country from JWT/user context and compares against `ZAKAT_SUPPORTED_COUNTRIES = ['SA']`. Non-Saudi companies see a "Coming Soon" screen.

**Findings**:
- `const isSupported = ZAKAT_SUPPORTED_COUNTRIES.includes(country)` — evaluated on component render
- Returns a "Coming Soon" UI block early if `!isSupported`
- `getCountry()` reads from `localStorage` / JWT context — sourced from `CompanyTaxSetting.country_code`
- Backend `/accounting/zakat/calculate` also enforces this via `company_settings` country check

**Rationale**: Both frontend and backend enforce the Saudi-only restriction independently. Defense-in-depth is correct.

**Risk identified**: If `getCountry()` returns `undefined` or an empty string (for new companies without settings configured), `ZAKAT_SUPPORTED_COUNTRIES.includes(undefined)` returns `false` — correctly shows "Coming Soon," not an error.

---

## R-09: Tax Return Pre-Population Source

**Decision**: Tax returns are pre-populated from **posted invoices only** (status NOT IN draft/cancelled), NOT from GL journal entries or draft data.

**Findings**:
- `POST /taxes/returns` queries `invoice_lines JOIN invoices` where `i.status NOT IN ('draft', 'cancelled')`
- Aggregates: `output_vat` (sales - sales_returns), `input_vat` (purchases - purchase_returns)
- Calculates: `taxable_amount`, `tax_amount = net_output_vat - net_input_vat`
- Branch filtering via `branch_id` parameter

**Implication for audit**: If invoices have a tax_rate of 0 on specific lines (e.g., zero-rated exports), those lines are included in taxable amount but not in VAT amount — this is correct per ZATCA filing rules.

**Rationale**: Using posted invoices as the source of truth (not GL journal lines) is pragmatic and correct for VAT return filing — VAT is calculated at the invoice level, not extracted from GL line items.

**Alternatives considered**: Using GL journal line aggregation — more accurate for complex scenarios but overly complex for standard VAT filing; invoice-level is the ZATCA-standard approach.

---

## R-10: Branch Tax Settings → Invoice Generation Flow

**Decision**: Branch tax settings feed into invoice creation via `GET /tax-compliance/applicable-taxes/{branch_id}` which the frontend calls when creating an invoice; the invoice creation endpoint uses `branch_id` to determine applicable tax rates via `tax_regimes JOIN branch_tax_settings`.

**Findings**:
- `GET /tax-compliance/applicable-taxes/{branch_id}` returns effective rates (incorporating branch overrides over default regime rates) and exemptions
- Branch-level override: `COALESCE(bts.custom_rate, tr.default_rate)` — branch can override default regime rate
- Branch exemptions: `COALESCE(bts.is_exempt, FALSE)` — branch can be exempt from specific tax types
- Invoice creation reads `branch_id` from request and applies the regimes for that branch's `country_code`

**Rationale**: Multi-branch, multi-jurisdiction support is correctly implemented at both the data layer and API layer.

**Risk identified**: If a branch's `country_code` is not set (NULL), the applicable taxes query returns empty — meaning no taxes are applied to that branch's invoices. This should be validated during branch creation, not silently ignored at invoice time.

---

## Consolidated Research Decisions

| Research ID | Decision | Impact on Design |
|-------------|----------|-----------------|
| R-01 | WHT endpoints fully implemented | No new endpoints needed |
| R-02 | All permission decorators in place | No security gaps found |
| R-03 | Zakat uses posted GL data; posting follows gl_service pattern | Confirm GL entry structure in data-model |
| R-04 | ZATCA QR auto-generated at invoice creation with graceful fallback | Document in contract; note Phase 2 dependency |
| R-05 | Frontend service functions match backend routes; 5 backend endpoints not exposed in service layer | Add missing service functions in audit tasks |
| R-06 | No mock data; error handling coverage to verify | Task: audit loading/error states across 6 pages |
| R-07 | Recurring calendar correctly creates next occurrence | No changes needed to logic |
| R-08 | SA gating works on both frontend and backend | Dual-layer defense confirmed |
| R-09 | Returns pre-populated from posted invoices | Note: zero-rated lines included in taxable base |
| R-10 | Branch settings → invoice via applicable-taxes endpoint | Risk: NULL country_code on branch silently skips taxes |

## Gaps Identified (→ Audit Task Items)

| Gap | Severity | Recommended Fix |
|-----|----------|----------------|
| 5 backend endpoints not in `taxes.js` service (`getSummary`, `getVATReport`, `getTaxAudit`, `getBranchAnalysis`, `getEmployeeTaxes`) | Medium | Add to taxes.js; update page components to use them |
| Error handling coverage per API call not verified | Medium | Audit each of 6 pages for try/catch + user-visible error |
| Branch with NULL country_code silently skips all taxes | Medium | Add validation in branch creation/update endpoint |
| `getCalendarSummary()` missing from taxes.js | Low | Add to taxes.js |
| Tax Return Details page field verification needed | Medium | Manual test + fix any undefined/null field display |
