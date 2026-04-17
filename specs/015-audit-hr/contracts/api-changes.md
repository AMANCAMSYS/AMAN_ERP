# API Contract Changes: HR Module Audit

**Feature**: 015-audit-hr  
**Date**: 2026-04-15  
**Breaking changes**: None — Decimal serialized as string is backward-compatible with frontend `formatNumber()` and `parseFloat()` consumers.

---

## 1. Employee Endpoints

### `GET /hr/employees` — Response Field Type Changes

```json
// BEFORE (float serialization)
{
  "salary": 5000.75,
  "housing_allowance": 1500.0,
  "transport_allowance": 500.0,
  "other_allowances": 0.0,
  "hourly_cost": 28.85
}

// AFTER (Decimal string serialization)
{
  "salary": "5000.75",
  "housing_allowance": "1500.00",
  "transport_allowance": "500.00",
  "other_allowances": "0.00",
  "hourly_cost": "28.85"
}
```

### `GET /hr/employees` — PII Masking (new behavior)

```json
// User WITHOUT hr.pii permission
{
  "iban": "**************3456",
  "social_security": "******7890",
  "gosi_number": "****5678",
  "passport_number": "****4321",
  "iqama_number": "****9876"
}

// User WITH hr.pii permission (unchanged)
{
  "iban": "SA1234567890123456",
  "social_security": "1234567890",
  "gosi_number": "12345678",
  "passport_number": "AB1234321",
  "iqama_number": "2345679876"
}
```

### `POST /hr/employees` — Request Field Type Changes

```json
// BEFORE (float)
{
  "salary": 5000.75,
  "housing_allowance": 1500
}

// AFTER (string accepted, Decimal parsed)
{
  "salary": "5000.75",
  "housing_allowance": "1500.00"
}
```

Note: Pydantic `Decimal` type accepts both `"5000.75"` (string) and `5000.75` (number) — backward compatible.

---

## 2. Payroll Endpoints

### `GET /hr/payroll-periods/{id}/entries` — Response Field Type Changes

```json
// BEFORE
{
  "basic_salary": 8000.0,
  "housing_allowance": 3000.0,
  "deductions": 975.0,
  "net_salary": 10025.0,
  "exchange_rate": 1.0,
  "gosi_employee_share": 780.0,
  "gosi_employer_share": 936.0
}

// AFTER
{
  "basic_salary": "8000.00",
  "housing_allowance": "3000.00",
  "deductions": "975.00",
  "net_salary": "10025.00",
  "exchange_rate": "1.0000",
  "gosi_employee_share": "780.00",
  "gosi_employer_share": "936.00"
}
```

### `GET /hr/payroll-periods` — Response Field Type Changes

```json
// BEFORE
{ "total_net": 125000.0 }

// AFTER  
{ "total_net": "125000.00" }
```

---

## 3. Loan Endpoints

### `POST /hr/loans` — Request/Response Changes

```json
// Request AFTER (string accepted)
{
  "amount": "10000.00",
  "monthly_installment": "833.33"
}

// Response AFTER
{
  "amount": "10000.00",
  "monthly_installment": "833.33",
  "paid_amount": "2499.99"
}
```

---

## 4. EOS Endpoints

### `POST /hr/eos/calculate` — Response Changes

```json
// BEFORE (float)
{
  "gratuity": 190000.0,
  "base_salary": 20000.0,
  "years_of_service": 12.0
}

// AFTER (Decimal string)
{
  "gratuity": "190000.00",
  "base_salary": "20000.00",
  "years_of_service": "12.00"
}
```

---

## 5. WPS Endpoints

### `POST /hr/wps/export` — Permission Change

- **New requirement**: Caller must have `hr.pii` permission (WPS file contains real IBAN)
- Returns 403 if permission not granted

### `GET /hr/wps/preview/{period_id}` — Response Changes

```json
// BEFORE
{ "basic_salary": 8000.0, "allowances": 3500.0, "net_salary": 10525.0 }

// AFTER
{ "basic_salary": "8000.00", "allowances": "3500.00", "net_salary": "10525.00" }
```

---

## 6. Branch Validation — New 403 Responses

The following endpoints gain branch access enforcement (may now return 403 where previously they returned data):

| Endpoint | Router File |
|----------|-------------|
| `POST /hr/performance/cycles` | `performance.py` |
| `GET /hr/performance/cycles` | `performance.py` |
| `POST /hr/performance/cycles/{id}/launch` | `performance.py` |
| `GET /hr/performance/reviews` | `performance.py` |
| `PUT /hr/performance/reviews/{id}/self-assessment` | `performance.py` |
| `PUT /hr/performance/reviews/{id}/manager-assessment` | `performance.py` |
| `GET /hr/saudization/dashboard` | `hr_wps_compliance.py` |
| `GET /hr/saudization/report` | `hr_wps_compliance.py` |
| `POST /hr/wps/export` | `hr_wps_compliance.py` |
| `GET /hr/wps/preview/{period_id}` | `hr_wps_compliance.py` |

---

## Backward Compatibility

| Change | Impact | Mitigation |
|--------|--------|------------|
| float → Decimal string | Frontend `formatNumber()` already calls `parseFloat()` internally | None needed — transparent |
| PII masking | Users without `hr.pii` see masked values where before they saw full values | By design — security improvement |
| Branch 403s | Users accessing cross-branch data now get 403 | By design — security fix |
| New `hr.pii` permission | Must be assigned to HR admin roles | Migration/seed script or manual assignment |
