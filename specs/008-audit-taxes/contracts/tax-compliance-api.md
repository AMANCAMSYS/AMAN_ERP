# API Contract: /tax-compliance/* & Zakat — Compliance, Regimes & ZATCA Settings

**Routers**: `backend/routers/finance/tax_compliance.py` + `backend/routers/system_completion.py`  
**Prefixes**: `/tax-compliance`, `/accounting/zakat`, `/accounting/fiscal-periods`  
**Auth**: Bearer JWT required on all endpoints

---

## Tax Regimes & Countries

### GET /tax-compliance/regimes
List all tax regimes (optionally filtered by country).

**Permissions**: `accounting.view` OR `taxes.view`

**Query Params**: `country_code`, `tax_type`, `is_active`

**Response 200**:
```json
[
  {
    "id": 1,
    "country_code": "SA",
    "tax_type": "VAT",
    "name": "Saudi Arabia VAT",
    "name_ar": "ضريبة القيمة المضافة السعودية",
    "default_rate": "15.0000",
    "is_required": true,
    "jurisdiction_code": "ZATCA"
  }
]
```

---

### GET /tax-compliance/countries
List all supported countries with their metadata and supported tax types.

**Permissions**: `accounting.view` OR `taxes.view`

**Response 200**:
```json
[
  {
    "country_code": "SA",
    "country_name": "Saudi Arabia",
    "currency": "SAR",
    "supports_vat": true,
    "supports_zakat": true,
    "supports_zatca": true,
    "vat_rate": "15.0000",
    "regimes": ["VAT", "ZAKAT", "WHT"]
  },
  {
    "country_code": "AE",
    "country_name": "United Arab Emirates",
    "currency": "AED",
    "supports_vat": true,
    "supports_zakat": false,
    "supports_zatca": false,
    "vat_rate": "5.0000",
    "regimes": ["VAT"]
  }
]
```

---

## Company Tax Settings

### GET /tax-compliance/company-settings
Get company-level tax configuration.

**Permissions**: `taxes.view` OR `accounting.view`

**Response 200**:
```json
{
  "id": 1,
  "country_code": "SA",
  "vat_number": "310123456789012",
  "zakat_number": "ZK-123456",
  "tax_id": "TID-789",
  "fiscal_year_start_month": 1,
  "filing_frequency": "quarterly",
  "zatca_phase": 2,
  "is_vat_registered": true,
  "is_zakat_registered": true,
  "has_zatca_keys": true
}
```
> ⛔ `zatca_private_key` NEVER included in response (Constitution §IV)

---

### PUT /tax-compliance/company-settings
Update company tax configuration.

**Permissions**: `taxes.manage`

**Request Body**:
```json
{
  "vat_number": "310123456789012",
  "zakat_number": "ZK-123456",
  "filing_frequency": "quarterly",
  "zatca_phase": 2,
  "is_vat_registered": true,
  "is_zakat_registered": true
}
```

**Response 200**: Updated company settings (same schema as GET, without private key)  
**Response 400**: Validation errors (e.g., invalid VAT number format)

---

## Branch Tax Settings

### GET /tax-compliance/branch-settings/{branch_id}
Get tax settings for a specific branch including applicable regime overrides.

**Permissions**: `taxes.view` OR `branches.view`

**Response 200**:
```json
{
  "branch_id": 3,
  "branch_name": "Riyadh Branch",
  "country_code": "SA",
  "settings": [
    {
      "tax_regime_id": 1,
      "tax_type": "VAT",
      "default_rate": "15.0000",
      "custom_rate": null,
      "effective_rate": "15.0000",
      "is_exempt": false,
      "is_registered": true,
      "registration_number": "SAU-BR-001"
    }
  ]
}
```

---

### PUT /tax-compliance/branch-settings
Update branch tax override settings.

**Permissions**: `taxes.manage` AND `branches.manage`

**Request Body**:
```json
{
  "branch_id": 3,
  "tax_regime_id": 1,
  "custom_rate": null,
  "is_exempt": false,
  "is_registered": true,
  "registration_number": "SAU-BR-001"
}
```

**Response 200**: Updated branch settings

---

### GET /tax-compliance/applicable-taxes/{branch_id}
Get taxes applicable to a branch — used by invoice creation to determine which taxes to apply.

**Permissions**: `taxes.view` OR `accounting.view`

**Response 200**:
```json
{
  "branch_id": 3,
  "jurisdiction": "SA",
  "taxes": [
    {
      "id": 1,
      "tax_type": "VAT",
      "effective_rate": "15.0000",
      "is_exempt": false
    }
  ]
}
```

---

## Compliance Overview & Reports

### GET /tax-compliance/overview
Compliance dashboard — filing status by jurisdiction.

**Permissions**: `taxes.view`

**Response 200**:
```json
{
  "compliance_status": "compliant",
  "jurisdictions": [
    {
      "country_code": "SA",
      "vat_status": "registered",
      "zakat_status": "registered",
      "zatca_phase": 2,
      "last_vat_return": "2025-Q4",
      "next_filing_due": "2026-04-30",
      "filing_frequency": "quarterly",
      "overdue_obligations": 0
    }
  ]
}
```

---

### GET /tax-compliance/reports/sa-vat
Saudi Arabia VAT return in ZATCA format.

**Permissions**: `taxes.view`

**Query Params**: `period` (e.g., `2025-Q1`), `branch_id`

**Response 200**: ZATCA-formatted VAT return with all box values (Box 1–13 per ZATCA template)

---

### GET /tax-compliance/reports/ae-vat
UAE VAT return in FTA format.

**Query Params**: `period`, `branch_id`

**Response 200**: FTA box format

---

### GET /tax-compliance/reports/eg-vat
Egypt VAT return in ETA format.

**Response 200**: ETA format

---

### GET /tax-compliance/reports/sy-income
Syria income tax return.

**Response 200**: Syria income tax form data

---

### GET /tax-compliance/reports/generic-income
Generic income tax return for any supported country.

**Query Params**: `country_code`, `period`

---

## Zakat

### POST /accounting/zakat/calculate
Calculate Zakat for a fiscal year using net assets method.

**Permissions**: `accounting.manage`

**Constraint**: Company must have `country_code = 'SA'` in `company_tax_settings`

**Request Body**:
```json
{
  "fiscal_year": 2025,
  "calculation_method": "net_assets",
  "use_gregorian_rate": false,
  "branch_id": null
}
```

**Response 200**:
```json
{
  "fiscal_year": 2025,
  "calculation_method": "net_assets",
  "zakat_rate": "0.02500",
  "components": {
    "cash_balance": "500000.0000",
    "trade_goods": "1200000.0000",
    "receivables": "800000.0000",
    "trading_investments": "200000.0000",
    "current_liabilities": "600000.0000"
  },
  "zakat_base": "2100000.0000",
  "zakat_amount": "52500.0000",
  "is_posted": false,
  "id": 7
}
```

**Response 400**: `{"detail": "Zakat calculation not available for country: AE"}`

---

### POST /accounting/zakat/{year}/post
Post Zakat calculation to GL — exactly once per fiscal year.

**Permissions**: `accounting.manage`

**Response 200**:
```json
{
  "message": "Zakat posted to GL",
  "gl_reference": "JE-2025-ZAKAT-001",
  "zakat_amount": "52500.0000"
}
```

**Response 400**: `{"detail": "Zakat already posted for fiscal year 2025"}`

**GL Entry**:
```
Dr. Zakat Expense (710xxx)    52500.0000
    Cr. Zakat Payable (220xxx)   52500.0000
```

---

## Fiscal Periods

### GET /accounting/fiscal-periods
List fiscal years.

**Permissions**: `accounting.view`

**Response 200**: List of FiscalYear objects with status

---

### POST /accounting/fiscal-periods
Create a fiscal year.

**Permissions**: `accounting.manage`

**Request Body**: `{"year_name": "2026", "start_date": "2026-01-01", "end_date": "2026-12-31"}`

---

### POST /accounting/fiscal-periods/{id}/lock
Lock a fiscal period — prevents any new postings to dates within this period.

**Permissions**: `accounting.manage`

**Response 200**: `{"message": "Period locked"}`

---

### POST /accounting/fiscal-periods/{id}/unlock
Unlock a period (requires admin permission and reason).

**Permissions**: `accounting.manage` (admin level)

**Request Body**: `{"reason": "Correction required for supplier invoice"}`
