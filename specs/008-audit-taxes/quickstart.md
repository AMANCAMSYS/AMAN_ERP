# Quickstart: audit-taxes — الضرائب والزكاة

**Branch**: `008-audit-taxes` | **Date**: 2026-04-15

---

## Prerequisites

- Docker + Docker Compose running with `aman_system` and at least one tenant DB (`aman_1`)
- Backend running: `cd backend && uvicorn main:app --reload --port 8000`
- Frontend running: `cd frontend && npm run dev`
- Redis running (for rate limiting)
- A company with `country_code = 'SA'` configured in `company_tax_settings`

---

## Key Files to Audit

| File | What to Check |
|------|--------------|
| `backend/routers/finance/taxes.py` | 40+ endpoints — permission decorators, Decimal usage, GL posting |
| `backend/routers/finance/tax_compliance.py` | ZATCA settings, branch regex, private key never in response |
| `backend/routers/external.py` | WHT certificate GL entry creation, ZATCA QR attachment |
| `backend/routers/system_completion.py` | Zakat calculate uses posted GL; post creates balanced JE |
| `frontend/src/services/taxes.js` | Add 5 missing service functions (see Gap R-05) |
| `frontend/src/pages/Taxes/TaxHome.jsx` | Loading/error state coverage |
| `frontend/src/pages/Taxes/TaxCompliance.jsx` | ZATCA private key NOT in response; settings load/save |
| `frontend/src/pages/Taxes/TaxReturnDetails.jsx` | No undefined/null field display |
| `frontend/src/pages/Taxes/WithholdingTax.jsx` | Certificate creation + calc preview |
| `frontend/src/pages/Accounting/ZakatCalculator.jsx` | SA-only gate + post-to-GL success handling |

---

## Running the Tax Module Locally

### 1. Start the stack
```bash
cd /home/omar/Desktop/aman
bash safe-start.sh
```

### 2. Verify tax routes are registered
```bash
curl http://localhost:8000/openapi.json | python3 -m json.tool | grep '"/taxes'
# Should show all /taxes/* routes
curl http://localhost:8000/openapi.json | python3 -m json.tool | grep '"/tax-compliance'
curl http://localhost:8000/openapi.json | python3 -m json.tool | grep '"/external/wht'
```

### 3. Get a test JWT token
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin@test.com", "password": "test123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

---

## Key Test Scenarios

### Scenario 1: VAT Rate Creation & Verification
```bash
# Create 15% VAT rate
curl -X POST http://localhost:8000/taxes/rates \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tax_type":"VAT","name":"Saudi VAT 15%","rate":"15.0000","country_code":"SA","effective_date":"2020-07-01","gl_account_id":42}'

# Verify: rate field is string, not float
# PASS: "rate": "15.0000"
# FAIL: "rate": 15.0
```

### Scenario 2: Tax Return Pre-Population
```bash
# Create VAT return for Q1 2026 — should pre-fill from posted invoices
curl -X POST http://localhost:8000/taxes/returns \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tax_type":"VAT","tax_period":"2026-Q1","branch_id":null}'

# Expected: taxable_amount and output_vat pre-populated (may be 0 in empty DB)
# Verify: status = "draft"
```

### Scenario 3: File Return & Duplicate Prevention
```bash
# File the return
RETURN_ID=1
curl -X PUT http://localhost:8000/taxes/returns/$RETURN_ID/file \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'

# Attempt duplicate — must fail with 400
curl -X POST http://localhost:8000/taxes/returns \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tax_type":"VAT","tax_period":"2026-Q1","branch_id":null}'
# Expected: 400 or 409 with "already exists" message
```

### Scenario 4: WHT Certificate Creation
```bash
# Create WHT certificate
curl -X POST http://localhost:8000/external/wht/transactions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"supplier_id":1,"wht_rate_id":1,"gross_amount":"20000.0000","transaction_date":"2026-04-15","expense_account_id":612,"bank_account_id":101}'

# Verify: wht_amount = "1000.0000", net_amount = "19000.0000"
# Verify: gl_reference is populated (JE was created)
```

### Scenario 5: Zakat Calculation (SA only)
```bash
# Calculate Zakat for 2025
curl -X POST http://localhost:8000/accounting/zakat/calculate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"fiscal_year":2025,"calculation_method":"net_assets","use_gregorian_rate":false}'

# Verify: zakat_amount = zakat_base × 0.025 (within 0.01 tolerance)
# Post to GL
ZAKAT_ID=7
curl -X POST http://localhost:8000/accounting/zakat/2025/post \
  -H "Authorization: Bearer $TOKEN"
# Verify: gl_reference populated

# Attempt duplicate post — must fail
curl -X POST http://localhost:8000/accounting/zakat/2025/post \
  -H "Authorization: Bearer $TOKEN"
# Expected: 400 "already posted"
```

### Scenario 6: ZATCA QR on Invoice
```bash
# Create a sales invoice (existing sales endpoint)
# Invoice response must include zatca_qr field for SA company
# Verify: "zatca_qr" is a non-empty base64 string

# Verify QR
INVOICE_ID=1
curl http://localhost:8000/external/zatca/verify/$INVOICE_ID \
  -H "Authorization: Bearer $TOKEN"
# Expected: qr_valid = true
```

### Scenario 7: Company Settings — ZATCA Private Key Not Exposed
```bash
curl http://localhost:8000/tax-compliance/company-settings \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# FAIL if response contains: "zatca_private_key" field
# PASS if response contains: "has_zatca_keys": true|false (boolean only)
```

### Scenario 8: Tax Calendar Recurring Completion
```bash
# Create recurring quarterly calendar item
curl -X POST http://localhost:8000/taxes/calendar \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Q1 VAT Filing","tax_type":"VAT","due_date":"2026-04-30","is_recurring":true,"recurrence_months":3,"reminder_days":[7,3,1]}'

ITEM_ID=1
# Complete it
curl -X PUT http://localhost:8000/taxes/calendar/$ITEM_ID/complete \
  -H "Authorization: Bearer $TOKEN"

# Expected: next_recurrence_id is populated (non-null)
# New item due date = 2026-04-30 + 3 months = 2026-07-30
```

---

## Frontend Manual Smoke Test

Open the browser at `http://localhost:5173` and verify:

| Page | URL | Check |
|------|-----|-------|
| Tax Home | `/taxes` | Dashboard cards show data (not empty), no JS errors in console |
| Tax Returns | `/taxes` (Returns tab) | Table populates, filters work |
| New Tax Return | `/taxes/returns/new` | Period dropdown + auto-calculate works |
| Tax Return Details | `/taxes/returns/1` | All fields show values, not "undefined" or blank |
| Withholding Tax | `/taxes/withholding` | Rates list loads, WHT calculator computes correct net |
| Tax Compliance | `/taxes/compliance` | Company settings show VAT# / Zakat# / ZATCA phase, save works |
| Tax Calendar | `/taxes/calendar` | Obligations listed, mark-complete updates status |
| Zakat Calculator | `/accounting/zakat` | Shows SA form; non-SA shows "Coming Soon" |

---

## Audit Checklist (from Research Gaps)

- [ ] **taxes.js**: Add `getSummary()`, `getVATReport()`, `getTaxAudit()`, `getBranchAnalysis()`, `getEmployeeTaxes()`, `getCalendarSummary()` functions
- [ ] **TaxHome.jsx**: Verify `getSummary()` is called on mount; loading spinner shown; error toast on API failure
- [ ] **TaxReturnDetails.jsx**: Verify `payments` array renders even when empty; `amount_remaining` shown correctly
- [ ] **WithholdingTax.jsx**: Verify calculator shows string amounts, not floats; certificate creation shows success toast
- [ ] **TaxCompliance.jsx**: Verify `has_zatca_keys` used (not `zatca_private_key`); save shows success toast
- [ ] **ZakatCalculator.jsx**: Verify `post()` disables button after success to prevent double-post
- [ ] **Branch creation**: Add validation that `country_code` is required; prevents NULL silently skipping taxes
- [ ] **All 6 tax pages**: Verify empty state (no records) shows friendly message, not blank screen

---

## Running Backend Tests
```bash
cd /home/omar/Desktop/aman
source .venv/bin/activate
cd src
pytest tests/ -v -k "tax or zakat or wht or zatca"
# Or from backend directory:
cd /home/omar/Desktop/aman/backend
pytest tests/ -v --tb=short
```

## Linting
```bash
cd /home/omar/Desktop/aman
ruff check .
```
