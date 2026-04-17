# Data Model: audit-taxes — الضرائب والزكاة

**Branch**: `008-audit-taxes` | **Date**: 2026-04-15  
**Tenant Scope**: Per-company DB `aman_{company_id}` (all tables below, unless noted)

---

## Entity Relationship Overview

```
CompanyTaxSetting (1) ──── (N) BranchTaxSetting
CompanyTaxSetting (1) ──── (N) TaxReturn
CompanyTaxSetting (1) ──── (N) ZakatCalculation

TaxRate  (N) ──── (N) TaxGroup  [via tax_group_rates junction]
TaxGroup (1) ──── (N) InvoiceLine   [tax_group_id FK]

TaxReturn (1) ──── (N) TaxPayment

TaxRegime (1) ──── (N) BranchTaxSetting
TaxRegime (N) ──── (1) country_code  [string, not FK]

TaxCalendar  (1) ──── (0..1) TaxCalendar  [self-ref: parent_id for recurrence chain]

WhtRate      (1) ──── (N) WhtTransaction
WhtTransaction (1) ──── (1) JournalEntry  [via gl_reference]

ZakatCalculation (1) ──── (0..1) JournalEntry [via gl_reference when posted]

FiscalYear  (1) ──── (N) FiscalPeriodLock
FiscalPeriodLock  [gates all transaction creation via check_fiscal_period_open()]
```

---

## 1. TaxRate

**Table**: `tax_rates`  
**Purpose**: Master list of tax rates used as the source of truth for all automatic VAT/WHT calculations.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | SERIAL | PK | |
| `tax_type` | VARCHAR(50) | NOT NULL | `'VAT'`, `'WHT'`, `'INCOME'`, `'CUSTOMS'`, `'GOSI'`, `'OTHER'` |
| `name` | VARCHAR(200) | NOT NULL | e.g., "Saudi VAT 15%" |
| `name_ar` | VARCHAR(200) | | Arabic label |
| `rate` | NUMERIC(8,4) | NOT NULL | e.g., `15.0000` — no float |
| `country_code` | VARCHAR(5) | NOT NULL | ISO 3166-1 alpha-2, e.g., `'SA'` |
| `effective_date` | DATE | NOT NULL | Rate applies from this date forward |
| `expiry_date` | DATE | | NULL = still active |
| `gl_account_id` | INTEGER | FK → `accounts.id` | Posting account for this tax |
| `is_active` | BOOLEAN | DEFAULT TRUE | Deactivation-only lifecycle |
| `created_by` | INTEGER | FK → `aman_system.users.id` | |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | | |

**Audit Annotations**:
- `rate` stored as `NUMERIC(8,4)` — never float (Constitution §I)
- Deletion forbidden — use `is_active = FALSE` to preserve historical reference
- Rate changes for a new period: insert new row with new `effective_date`; old row kept for audit

**Indexes**: `(country_code, is_active)`, `(effective_date, expiry_date)`

---

## 2. TaxGroup

**Table**: `tax_groups`  
**Purpose**: Named collection of tax rates applied together to an invoice line item.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | SERIAL | PK | |
| `name` | VARCHAR(200) | NOT NULL UNIQUE | e.g., "GCC Standard VAT" |
| `name_ar` | VARCHAR(200) | | |
| `description` | TEXT | | |
| `is_active` | BOOLEAN | DEFAULT TRUE | |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |

**Junction Table**: `tax_group_rates`

| Column | Type | Constraints |
|--------|------|-------------|
| `group_id` | INTEGER | FK → `tax_groups.id`, CASCADE DELETE |
| `rate_id` | INTEGER | FK → `tax_rates.id` |
| PRIMARY KEY | `(group_id, rate_id)` | |

---

## 3. TaxReturn

**Table**: `tax_returns`  
**Purpose**: Period-based tax filing record. Pre-populated from posted invoices; lifecycle draft → filed → cancelled.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | SERIAL | PK | |
| `tax_type` | VARCHAR(50) | NOT NULL | `'VAT'`, `'INCOME'`, `'WHT'`, `'GENERIC'` |
| `tax_period` | VARCHAR(20) | NOT NULL | `'2024-01'` (monthly) or `'2024-Q1'` (quarterly) |
| `start_date` | DATE | NOT NULL | Period start |
| `end_date` | DATE | NOT NULL | Period end |
| `taxable_amount` | NUMERIC(18,4) | NOT NULL DEFAULT 0 | Net taxable sales |
| `output_vat` | NUMERIC(18,4) | NOT NULL DEFAULT 0 | VAT collected on sales |
| `input_vat` | NUMERIC(18,4) | NOT NULL DEFAULT 0 | VAT paid on purchases |
| `tax_amount` | NUMERIC(18,4) | NOT NULL DEFAULT 0 | `output_vat - input_vat` |
| `adjustments` | NUMERIC(18,4) | DEFAULT 0 | Manual adjustments |
| `status` | VARCHAR(20) | NOT NULL DEFAULT `'draft'` | `draft`, `filed`, `cancelled` |
| `filed_date` | TIMESTAMPTZ | | Set when status → filed |
| `branch_id` | INTEGER | FK → `branches.id` NULLABLE | NULL = all branches |
| `notes` | TEXT | | |
| `created_by` | INTEGER | FK → `aman_system.users.id` | |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | | |

**Constraints**:
- UNIQUE `(tax_type, tax_period, branch_id)` — prevents double-filing (NULL branch treated as company-wide)
- Once `status = 'filed'`, only `status = 'cancelled'` transition is allowed
- `tax_amount` = `output_vat - input_vat + adjustments`

**State Machine**:
```
draft ──▶ filed
draft ──▶ cancelled
filed ──▶ cancelled  (rare; requires admin permission)
```

---

## 4. TaxPayment

**Table**: `tax_payments`  
**Purpose**: Payment record against a tax return; creates a GL journal entry at creation.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | SERIAL | PK | |
| `return_id` | INTEGER | FK → `tax_returns.id` | |
| `amount` | NUMERIC(18,4) | NOT NULL | Amount paid |
| `payment_date` | DATE | NOT NULL | |
| `payment_method` | VARCHAR(50) | | `'bank_transfer'`, `'check'`, `'cash'` |
| `reference` | VARCHAR(200) | | Bank reference or check number |
| `gl_reference` | VARCHAR(100) | | Journal entry reference created by GL service |
| `notes` | TEXT | | |
| `created_by` | INTEGER | FK → `aman_system.users.id` | |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |

**GL Entry created at payment**:
```
Dr. Tax Payable Account       amount
    Cr. Bank / Cash Account   amount
```

---

## 5. TaxRegime

**Table**: `tax_regimes`  
**Purpose**: Country-specific tax system definition; master data for all supported jurisdictions.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | SERIAL | PK | |
| `country_code` | VARCHAR(5) | NOT NULL | ISO country code |
| `tax_type` | VARCHAR(50) | NOT NULL | `'VAT'`, `'INCOME'`, `'ZAKAT'`, `'WHT'` |
| `name` | VARCHAR(200) | NOT NULL | e.g., "Saudi Arabia VAT" |
| `name_ar` | VARCHAR(200) | | |
| `default_rate` | NUMERIC(8,4) | NOT NULL | Standard rate for this regime |
| `is_required` | BOOLEAN | DEFAULT FALSE | Mandatory for all entities in this country |
| `is_active` | BOOLEAN | DEFAULT TRUE | |
| `jurisdiction_code` | VARCHAR(20) | | e.g., "ZATCA", "FTA", "ETA" |
| `notes` | TEXT | | |

**Country Support Matrix** (from research R-02):

| Country | VAT | Zakat | ZATCA | Default VAT Rate |
|---------|-----|-------|-------|-----------------|
| SA | ✅ | ✅ | ✅ | 15% |
| AE | ✅ | ❌ | ❌ | 5% |
| EG | ✅ | ❌ | ❌ | 14% |
| BH | ✅ | ❌ | ❌ | 10% |
| OM | ✅ | ❌ | ❌ | 5% |
| KW | ❌ | ✅ | ❌ | 0% |
| SY | ❌ | ❌ | ❌ | 0% |
| QA | ❌ | ❌ | ❌ | 0% |
| JO | ❌ | ❌ | ❌ | 0% |

---

## 6. CompanyTaxSetting

**Table**: `company_tax_settings` (one row per company)  
**Purpose**: Company-level tax configuration — VAT registration, Zakat number, ZATCA phase, filing frequency.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | SERIAL | PK | |
| `company_id` | INTEGER | UNIQUE NOT NULL FK→`aman_system.companies.id` | |
| `country_code` | VARCHAR(5) | NOT NULL | Gates Zakat and ZATCA features |
| `vat_number` | VARCHAR(50) | | VAT registration number |
| `zakat_number` | VARCHAR(50) | | GAZT Zakat registration number |
| `tax_id` | VARCHAR(50) | | General tax identification number |
| `fiscal_year_start_month` | SMALLINT | DEFAULT 1 | 1=January, 7=July, etc. |
| `filing_frequency` | VARCHAR(20) | `'monthly'`, `'quarterly'`, `'annual'` | |
| `zatca_phase` | SMALLINT | DEFAULT 1 | 1 = Phase 1 (QR only), 2 = Phase 2 (signed) |
| `zatca_private_key` | TEXT | ENCRYPTED | RSA private key (never logged, never returned in API) |
| `zatca_certificate` | TEXT | | ZATCA-issued X.509 certificate |
| `is_vat_registered` | BOOLEAN | DEFAULT FALSE | |
| `is_zakat_registered` | BOOLEAN | DEFAULT FALSE | |
| `updated_at` | TIMESTAMPTZ | | |
| `updated_by` | INTEGER | FK → `aman_system.users.id` | |

**Security**: `zatca_private_key` MUST NEVER appear in API responses or logs (Constitution §IV).

---

## 7. BranchTaxSetting

**Table**: `branch_tax_settings`  
**Purpose**: Per-branch overrides of tax regime defaults; enables multi-jurisdiction, multi-branch companies.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | SERIAL | PK | |
| `branch_id` | INTEGER | NOT NULL FK → `branches.id` | |
| `tax_regime_id` | INTEGER | NOT NULL FK → `tax_regimes.id` | |
| `custom_rate` | NUMERIC(8,4) | | Overrides `tax_regimes.default_rate` |
| `is_exempt` | BOOLEAN | DEFAULT FALSE | Branch exempt from this regime |
| `is_registered` | BOOLEAN | DEFAULT FALSE | Branch registered for this optional regime |
| `registration_number` | VARCHAR(50) | | Branch-specific registration number |
| UNIQUE | `(branch_id, tax_regime_id)` | | One override per branch-regime pair |

**Risk**: If `branches.country_code` is NULL, `get_applicable_taxes` returns no taxes → invoices issued with 0 tax. Branch creation MUST validate country_code is set.

---

## 8. ZakatCalculation

**Table**: `zakat_calculations`  
**Purpose**: Stores each Zakat computation result for a fiscal year; audit trail for GAZT.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | SERIAL | PK | |
| `fiscal_year` | SMALLINT | NOT NULL | e.g., `2025` |
| `calculation_method` | VARCHAR(50) | DEFAULT `'net_assets'` | `'net_assets'`, `'current_assets'` |
| `zakat_rate` | NUMERIC(6,5) | NOT NULL | `0.02500` (Hijri) or `0.02578` (Gregorian) |
| `cash_balance` | NUMERIC(18,4) | NOT NULL DEFAULT 0 | |
| `trade_goods` | NUMERIC(18,4) | NOT NULL DEFAULT 0 | Inventory + WIP eligible |
| `receivables` | NUMERIC(18,4) | NOT NULL DEFAULT 0 | Trade receivables |
| `trading_investments` | NUMERIC(18,4) | NOT NULL DEFAULT 0 | Short-term investments |
| `current_liabilities` | NUMERIC(18,4) | NOT NULL DEFAULT 0 | Offset against gross |
| `zakat_base` | NUMERIC(18,4) | NOT NULL | `max(0, gross_zakatable - current_liabilities)` |
| `zakat_amount` | NUMERIC(18,4) | NOT NULL | `zakat_base × zakat_rate` — ROUND_HALF_UP |
| `details` | JSONB | | Full breakdown: account codes queried, amounts |
| `is_posted` | BOOLEAN | DEFAULT FALSE | True after GL entry created |
| `gl_reference` | VARCHAR(100) | | Journal entry reference when posted |
| `branch_id` | INTEGER | FK → `branches.id` NULLABLE | NULL = company-wide |
| `calculated_by` | INTEGER | FK → `aman_system.users.id` | |
| `calculated_at` | TIMESTAMPTZ | DEFAULT NOW() | |
| `posted_by` | INTEGER | FK → `aman_system.users.id` NULLABLE | |
| `posted_at` | TIMESTAMPTZ | NULLABLE | |

**Constraints**:
- UNIQUE `(fiscal_year, branch_id)` — one Zakat calculation per year per branch
- `is_posted` is immutable once TRUE — duplicate posting prevented at application level and by unique constraint

**GL Entry created at posting**:
```
Dr. Zakat Expense  (account: 710xxx)   zakat_amount
    Cr. Zakat Payable (account: 220xxx)   zakat_amount
```

---

## 9. TaxCalendar

**Table**: `tax_calendar`  
**Purpose**: Tax obligation deadlines; supports recurring events; triggers reminder notifications.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | SERIAL | PK | |
| `title` | VARCHAR(200) | NOT NULL | e.g., "VAT Filing - March 2026" |
| `tax_type` | VARCHAR(50) | NOT NULL | `'VAT'`, `'ZAKAT'`, `'WHT'`, `'INCOME'`, `'GOSI'` |
| `due_date` | DATE | NOT NULL | |
| `reminder_days` | JSONB | DEFAULT `[7, 3, 1]` | Days before due to send reminder |
| `is_recurring` | BOOLEAN | DEFAULT FALSE | |
| `recurrence_months` | SMALLINT | NULLABLE | 1 = monthly, 3 = quarterly, 12 = annual |
| `is_completed` | BOOLEAN | DEFAULT FALSE | |
| `completed_at` | TIMESTAMPTZ | NULLABLE | |
| `parent_id` | INTEGER | FK → `tax_calendar.id` NULLABLE | Previous occurrence in chain |
| `notes` | TEXT | | |
| `created_by` | INTEGER | FK → `aman_system.users.id` | |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |

**Recurrence Logic** (confirmed in research R-07):
- On `PUT /taxes/calendar/{id}/complete`: current item set `is_completed = TRUE`
- If `is_recurring`: new row inserted with `due_date = current.due_date + relativedelta(months=recurrence_months)`, `parent_id = current.id`

**Reminder Integration**: APScheduler job reads `tax_calendar` where `is_completed = FALSE` and `due_date - NOW() IN reminder_days` → sends notification.

---

## 10. WhtRate

**Table**: `wht_rates`  
**Purpose**: Withholding tax rates by service category; effective date range.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | SERIAL | PK | |
| `category` | VARCHAR(100) | NOT NULL | `'professional_services'`, `'rent'`, `'goods'`, `'technical_services'`, `'management_fees'` |
| `category_ar` | VARCHAR(100) | | Arabic label |
| `rate` | NUMERIC(8,4) | NOT NULL | e.g., `5.0000` for 5% |
| `effective_date` | DATE | NOT NULL | |
| `expiry_date` | DATE | NULLABLE | NULL = currently active |
| `is_active` | BOOLEAN | DEFAULT TRUE | |
| `notes` | TEXT | | Regulatory reference |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |

**Indexes**: `(category, is_active, effective_date)`

---

## 11. WhtTransaction

**Table**: `wht_transactions`  
**Purpose**: WHT certificate for each supplier payment with WHT deduction; creates GL entry on creation.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | SERIAL | PK | |
| `certificate_number` | VARCHAR(100) | UNIQUE NOT NULL | Auto-generated reference |
| `supplier_id` | INTEGER | FK → `parties.id` | |
| `wht_rate_id` | INTEGER | FK → `wht_rates.id` | |
| `category` | VARCHAR(100) | NOT NULL | Denormalized from WhtRate for history |
| `rate` | NUMERIC(8,4) | NOT NULL | Rate at time of transaction (locked) |
| `gross_amount` | NUMERIC(18,4) | NOT NULL | Invoice amount before WHT |
| `wht_amount` | NUMERIC(18,4) | NOT NULL | `gross_amount × rate / 100` — ROUND_HALF_UP |
| `net_amount` | NUMERIC(18,4) | NOT NULL | `gross_amount - wht_amount` |
| `transaction_date` | DATE | NOT NULL | |
| `invoice_reference` | VARCHAR(100) | | Supplier invoice number |
| `gl_reference` | VARCHAR(100) | | Journal entry reference |
| `currency_code` | VARCHAR(3) | DEFAULT `'SAR'` | |
| `exchange_rate` | NUMERIC(12,6) | DEFAULT 1 | Locked at transaction date |
| `notes` | TEXT | | |
| `created_by` | INTEGER | FK → `aman_system.users.id` | |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |

**GL Entry created at certificate creation** (Constitution §III):
```
Dr. Expense Account            gross_amount
    Cr. WHT Payable Account       wht_amount
    Cr. Bank / Accounts Payable   net_amount
```

All amounts use `Decimal` with `ROUND_HALF_UP` before DB write.

---

## 12. FiscalYear

**Table**: `fiscal_years`  
**Purpose**: Fiscal year definition; closing status gates all transaction posting.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | SERIAL | PK | |
| `year_name` | VARCHAR(50) | NOT NULL UNIQUE | e.g., `'2025'` or `'FY2025-26'` |
| `start_date` | DATE | NOT NULL | |
| `end_date` | DATE | NOT NULL | |
| `status` | VARCHAR(20) | DEFAULT `'open'` | `'open'`, `'closed'`, `'locked'` |
| `closing_entry_ref` | VARCHAR(100) | | GL reference for year-end closing entry |
| `closed_by` | INTEGER | FK → `aman_system.users.id` NULLABLE | |
| `closed_at` | TIMESTAMPTZ | NULLABLE | |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |

---

## 13. FiscalPeriodLock

**Table**: `fiscal_period_locks`  
**Purpose**: Period-level locking; `check_fiscal_period_open()` checks this before every transaction.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | SERIAL | PK | |
| `fiscal_year_id` | INTEGER | FK → `fiscal_years.id` | |
| `period_start` | DATE | NOT NULL | |
| `period_end` | DATE | NOT NULL | |
| `locked_by` | INTEGER | FK → `aman_system.users.id` | |
| `locked_at` | TIMESTAMPTZ | DEFAULT NOW() | |
| `unlock_reason` | TEXT | NULLABLE | If unlocked, reason required |
| UNIQUE | `(fiscal_year_id, period_start)` | | |

---

## Design Notes

### Financial Precision (Constitution §I)
- ALL monetary columns: `NUMERIC(18,4)` in PostgreSQL
- ALL Python computations: `decimal.Decimal` with `ROUND_HALF_UP`
- ALL API responses: monetary values returned as strings (never float)
- `Decimal("0.01")` as comparison tolerance

### Exchange Rate Locking (Constitution §I)
- `WhtTransaction.exchange_rate` locked at transaction creation date
- Revaluation MUST NOT alter the locked rate
- Multi-currency WHT: `wht_amount` stored in transaction currency; GL entry converts using locked rate

### Security (Constitution §IV)
- `CompanyTaxSetting.zatca_private_key` NEVER returned in GET responses
- All tax endpoints: `require_module("taxes")` + `require_permission([...])`
- Branch tax endpoints: `validate_branch_access(current_user, branch_id)`

### Multi-Tenancy (Constitution §II)
- All tables reside in `aman_{company_id}` DB
- All queries routed via `get_db_connection(company_id)` extracted from JWT
