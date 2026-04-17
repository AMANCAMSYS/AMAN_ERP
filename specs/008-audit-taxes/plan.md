# Implementation Plan: audit-taxes — الضرائب والزكاة

**Branch**: `008-audit-taxes` | **Date**: 2026-04-15 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/008-audit-taxes/spec.md`

---

## Summary

Comprehensive audit and repair of the taxes & zakat module — covering VAT rates, tax returns, ZATCA e-invoicing, Zakat calculation, WHT certificates, and tax calendar. The existing module has 40+ backend endpoints and 6 frontend pages already built; the audit identifies and fixes broken frontend-backend wiring, missing GL postings, incorrect calculations, and UX gaps (loading/error states, missing filters). Every fix must satisfy the constitution's financial precision, double-entry integrity, security, and Saudi regulatory compliance requirements.

---

## Technical Context

**Language/Version**: Python 3.12 (backend) · React 18 / Vite (frontend)  
**Primary Dependencies**: FastAPI · SQLAlchemy 2.0 (SQL-first via `text()`) · Pydantic · i18next · React Router · openpyxl · python-jose  
**Storage**: PostgreSQL 15 — per-tenant `aman_{company_id}` + system `aman_system`; Redis (rate limiting/cache)  
**Testing**: pytest (backend) · vitest (frontend)  
**Target Platform**: Linux server (backend API) · Browser SPA (frontend)  
**Project Type**: Web service (REST API) + SPA frontend — audit/repair of existing module  
**Performance Goals**: ≤ 500ms p95 for all tax report endpoints; Tax Home dashboard loads within 2s  
**Constraints**: All monetary values `NUMERIC(18,4)` / `Decimal` — no float; fiscal period lock enforced; per-tenant DB isolation; ZATCA legal mandate  
**Scale/Scope**: 12 supported countries · 6 tax pages · 40+ endpoints · 12+ domain models

---

## Constitution Check

*GATE: Must pass before Phase 0. Re-checked after Phase 1 design.*

| # | Gate | Status | Evidence |
|---|------|--------|----------|
| I | Financial precision — `NUMERIC(18,4)` / `Decimal` for all money | ✅ PASS | `TaxRate.rate`, `TaxReturn.taxable_amount`, `ZakatCalculation.amount` use NUMERIC; backend service uses Decimal |
| II | Multi-tenant isolation — `get_db_connection(company_id)` on all endpoints | ✅ PASS | All tax routers extract `company_id` from JWT via `get_current_user` |
| III | Double-entry integrity — all postings via `gl_service.py` | ⚠️ VERIFY | Tax payments create GL entries; Zakat posting must also use GL service — needs verification in Phase 0 |
| IV | Security — `require_permission()` on every endpoint | ⚠️ VERIFY | `taxes.py` and `tax_compliance.py` routes need permission decorator audit |
| V | Saudi regulatory — ZATCA, WHT, Zakat rules implemented | ✅ PASS | ZATCA QR/signing logic exists; WHT rate table + certificate tracker present; Zakat 2.5% implemented |
| VII | SQL-first — `db.execute(text(...))` with parameterized queries | ✅ PASS | Confirmed in existing finance routers pattern |

**Pre-Phase 0 Gate**: PASS with 2 items to verify during research phase.

---

## Project Structure

### Documentation (this feature)

```text
specs/008-audit-taxes/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── taxes-api.md
│   ├── tax-compliance-api.md
│   └── external-wht-zatca-api.md
└── tasks.md             # Phase 2 output (speckit.tasks)
```

### Source Code (to be audited/modified)

```text
backend/
├── routers/finance/
│   ├── taxes.py                    # 40+ tax endpoints — audit/fix
│   └── tax_compliance.py           # Compliance & ZATCA settings — audit/fix
├── routers/
│   ├── external.py                 # ZATCA + WHT endpoints — audit QR logic
│   └── system_completion.py        # Zakat calculate/post — audit GL posting
├── models/domain_models/
│   ├── finance_treasury_tax.py     # TaxRate, TaxGroup, TaxReturn, TaxPayment, TaxRegime, CompanyTaxSetting, BranchTaxSetting
│   ├── finance_fiscal_zakat.py     # FiscalYear, FiscalPeriodLock, ZakatCalculation
│   └── finance_recognition_tax.py  # TaxCalendar, WhtRate, WhtTransaction, RevenueRecognitionSchedule
└── services/
    └── gl_service.py               # Must be used for all tax GL postings

frontend/
└── src/
    ├── pages/Taxes/
    │   ├── TaxHome.jsx             # Dashboard — verify API wiring + loading/error states
    │   ├── TaxCompliance.jsx       # ZATCA settings — verify save/load round-trip
    │   ├── TaxCalendar.jsx         # Calendar — verify mark-complete + filters
    │   ├── TaxReturnForm.jsx       # Return creation — verify pre-fill from GL data
    │   ├── TaxReturnDetails.jsx    # Return details — verify all fields populated
    │   └── WithholdingTax.jsx      # WHT — verify certificate creation + calc
    ├── pages/Accounting/
    │   └── ZakatCalculator.jsx     # Zakat — verify SA-only gate + post-to-GL
    └── services/
        └── taxes.js                # API service — verify all functions point to correct endpoints
```

---

## Complexity Tracking

No constitution violations requiring justification. All changes are within existing architecture.

---

## Phase 0: Research

> Resolve all NEEDS CLARIFICATION items and establish best practices baseline before design.

### Research Tasks

| ID | Research Question | Priority |
|----|-------------------|----------|
| R-01 | Verify WHT transactions endpoint exists in external.py — is `POST /external/wht/transactions` implemented or missing? | HIGH |
| R-02 | Verify all tax/compliance endpoints have `require_permission()` decorator — list any missing | HIGH |
| R-03 | Confirm Zakat GL posting uses `gl_service.py` — or does system_completion.py do raw INSERT? | HIGH |
| R-04 | Verify ZATCA QR code is attached to sales invoices at invoice creation — or only via manual `/external/zatca/generate-qr` call? | HIGH |
| R-05 | Confirm `taxes.js` frontend functions map to correct backend URL paths (no 404s) | HIGH |
| R-06 | Identify any hardcoded mock data in frontend tax pages (static arrays vs real API calls) | HIGH |
| R-07 | Verify Tax Calendar `completeCalendarItem` creates the next recurrence correctly | MEDIUM |
| R-08 | Confirm `ZakatCalculator.jsx` enforces SA-only gate — what is the check mechanism? | MEDIUM |
| R-09 | Verify Tax Return `createReturn` pre-populates from posted GL entries — not from draft/unposted invoices | MEDIUM |
| R-10 | Confirm branch-level ZATCA settings are applied at invoice generation, not overridden by company defaults | MEDIUM |

---

## Phase 1: Design

> Produce data-model.md, contracts/, and quickstart.md after research resolves all unknowns.

### Design Deliverables

1. **data-model.md** — Entity relationship diagram + field-level specification for all 12 domain models with audit annotations
2. **contracts/taxes-api.md** — Full REST contract for `/taxes/*` (40+ endpoints)
3. **contracts/tax-compliance-api.md** — REST contract for `/tax-compliance/*` + Zakat
4. **contracts/external-wht-zatca-api.md** — REST contract for `/external/wht/*` and `/external/zatca/*`
5. **quickstart.md** — Developer guide for running tax module locally + key test scenarios

### Known Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| GL posting for taxes | Via `gl_service.py` only — no direct INSERT | Constitution §III mandate |
| Monetary precision | `Decimal` in Python, `NUMERIC(18,4)` in DB, string in JS | Constitution §I |
| Zakat rate | 2.5% Hijri (configurable to 2.57764% Gregorian) | `docs/ZAKAT_CALCULATION_METHODOLOGY.md` |
| Zakat eligibility | Saudi Arabia only — gated by `country_code == "SA"` in `CompanyTaxSetting` | Regulatory |
| ZATCA Phase gate | Phase stored in `CompanyTaxSetting.zatca_phase`; invoice generation checks phase | ZATCA mandate |
| VAT period overlap | `check_fiscal_period_open()` shared from accounting module | Constitution §III |
| WHT GL entries | Dr. Expense / Cr. WHT Payable / Cr. Bank — atomic at certificate creation | Double-entry mandate |
| Frontend loading states | All API calls wrap in `loading` state + `try/catch` with toast error | FR-026 |
| Pagination | Default 25, max 100 per page on all list endpoints | Constitution §VII |

---

## Post-Phase 1 Constitution Re-Check

*(To be completed after data-model.md and contracts/ are written)*

Key re-check items:
- All new/modified endpoints have `require_permission('taxes.X')` — no missing decorators  
- All monetary response fields returned as strings (not floats) from API  
- No raw SQL using string interpolation — all parameterized  
- ZATCA signing uses RSA keypair from `company_settings` — keys never logged  
- Branch filtering uses `validate_branch_access()` on all branch-scoped tax endpoints  
