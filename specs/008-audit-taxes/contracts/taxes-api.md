# API Contract: /taxes/* — Tax Rates, Returns, Payments & Calendar

**Router**: `backend/routers/finance/taxes.py`  
**Prefix**: `/taxes`  
**Module Gate**: `require_module("taxes")` on all endpoints  
**Auth**: Bearer JWT required on all endpoints

---

## Tax Rates

### GET /taxes/rates
List all tax rates.

**Permissions**: `accounting.view` OR `taxes.view`

**Query Params**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `country_code` | string | — | Filter by country (e.g., `SA`) |
| `tax_type` | string | — | `VAT`, `WHT`, `INCOME` |
| `is_active` | bool | `true` | Filter active/inactive |

**Response 200**:
```json
[
  {
    "id": 1,
    "tax_type": "VAT",
    "name": "Saudi VAT 15%",
    "name_ar": "ضريبة القيمة المضافة 15%",
    "rate": "15.0000",
    "country_code": "SA",
    "effective_date": "2020-07-01",
    "expiry_date": null,
    "gl_account_id": 42,
    "is_active": true
  }
]
```
> ⚠️ `rate` returned as string (Constitution §I — no float)

---

### GET /taxes/rates/{id}
Get a single tax rate.

**Permissions**: `accounting.view` OR `taxes.view`

**Response 200**: Single TaxRate object (same schema as above)  
**Response 404**: `{"detail": "Tax rate not found"}`

---

### POST /taxes/rates
Create a new tax rate.

**Permissions**: `accounting.edit` OR `taxes.manage`

**Request Body**:
```json
{
  "tax_type": "VAT",
  "name": "Saudi VAT 15%",
  "name_ar": "ضريبة القيمة المضافة 15%",
  "rate": "15.0000",
  "country_code": "SA",
  "effective_date": "2020-07-01",
  "gl_account_id": 42
}
```

**Response 201**: Created TaxRate object  
**Response 400**: `{"detail": "A rate of this type already exists for this country and date range"}`

---

### PUT /taxes/rates/{id}
Update an existing tax rate.

**Permissions**: `accounting.edit` OR `taxes.manage`

**Request Body**: Partial TaxRate fields (all optional)  
**Response 200**: Updated TaxRate  
**Response 404**: Not found

---

### DELETE /taxes/rates/{id}
Deactivate a tax rate (soft delete — sets `is_active = false`).

**Permissions**: `taxes.manage`

**Response 200**: `{"message": "Tax rate deactivated"}`  
**Response 400**: `{"detail": "Cannot deactivate rate used in active tax groups"}`

---

## Tax Groups

### GET /taxes/groups
List all tax groups with their member rates.

**Permissions**: `accounting.view` OR `taxes.view`

**Response 200**:
```json
[
  {
    "id": 1,
    "name": "GCC Standard VAT",
    "name_ar": "ضريبة القيمة المضافة الخليجية",
    "is_active": true,
    "rates": [
      {"id": 1, "name": "Saudi VAT 15%", "rate": "15.0000"}
    ]
  }
]
```

---

### POST /taxes/groups
Create a new tax group.

**Permissions**: `taxes.manage`

**Request Body**:
```json
{
  "name": "GCC Standard VAT",
  "name_ar": "ضريبة القيمة المضافة الخليجية",
  "rate_ids": [1, 2]
}
```

**Response 201**: Created TaxGroup with rates

---

## Tax Returns

### GET /taxes/returns
List tax returns.

**Permissions**: `accounting.view` OR `taxes.view`

**Query Params**:
| Param | Type | Description |
|-------|------|-------------|
| `tax_type` | string | Filter by `VAT`, `INCOME`, etc. |
| `status` | string | `draft`, `filed`, `cancelled` |
| `tax_period` | string | e.g., `2025-Q1` |
| `branch_id` | int | Filter by branch |
| `page` | int | Default 1 |
| `page_size` | int | Default 25, max 100 |

**Response 200**:
```json
{
  "total": 12,
  "page": 1,
  "page_size": 25,
  "items": [
    {
      "id": 5,
      "tax_type": "VAT",
      "tax_period": "2025-Q1",
      "start_date": "2025-01-01",
      "end_date": "2025-03-31",
      "taxable_amount": "1200000.0000",
      "output_vat": "180000.0000",
      "input_vat": "45000.0000",
      "tax_amount": "135000.0000",
      "adjustments": "0.0000",
      "status": "filed",
      "filed_date": "2025-04-25T10:30:00Z",
      "branch_id": null,
      "created_at": "2025-04-20T09:00:00Z"
    }
  ]
}
```

---

### GET /taxes/returns/{id}
Get a single tax return with associated payments.

**Permissions**: `accounting.view` OR `taxes.view`

**Response 200**:
```json
{
  "id": 5,
  "tax_type": "VAT",
  "tax_period": "2025-Q1",
  "taxable_amount": "1200000.0000",
  "output_vat": "180000.0000",
  "input_vat": "45000.0000",
  "tax_amount": "135000.0000",
  "adjustments": "0.0000",
  "status": "filed",
  "filed_date": "2025-04-25T10:30:00Z",
  "payments": [
    {
      "id": 3,
      "amount": "135000.0000",
      "payment_date": "2025-04-28",
      "payment_method": "bank_transfer",
      "reference": "TRF-2025-001",
      "gl_reference": "JE-2025-0458"
    }
  ],
  "amount_paid": "135000.0000",
  "amount_remaining": "0.0000"
}
```

---

### POST /taxes/returns
Create a new tax return (pre-populates from posted invoices).

**Permissions**: `accounting.edit` OR `taxes.manage`

**Request Body**:
```json
{
  "tax_type": "VAT",
  "tax_period": "2025-Q1",
  "branch_id": null
}
```

**Response 201**: Full TaxReturn object with pre-calculated amounts  
**Response 400**: `{"detail": "A filed return already exists for this period and type"}`  
**Response 409**: Duplicate period + type + branch

---

### PUT /taxes/returns/{id}/file
File a tax return — transitions status draft → filed.

**Permissions**: `taxes.manage`

**Request Body**: `{}` (empty; optionally `{"notes": "Filed on time"}`)  
**Response 200**: `{"message": "Return filed successfully", "filed_date": "2025-04-25T10:30:00Z"}`  
**Response 400**: `{"detail": "Return is already filed"}` | `{"detail": "Cannot file cancelled return"}`

---

### PUT /taxes/returns/{id}/cancel
Cancel a tax return.

**Permissions**: `taxes.manage`

**Request Body**: `{"reason": "Duplicate entry"}` (reason required)  
**Response 200**: `{"message": "Return cancelled"}`  
**Response 400**: Cannot cancel an already-cancelled return

---

## Tax Payments

### GET /taxes/payments
List tax payments.

**Permissions**: `accounting.view` OR `taxes.view`

**Query Params**: `return_id`, `from_date`, `to_date`, `page`, `page_size`

**Response 200**: Paginated list of TaxPayment objects

---

### POST /taxes/payments
Record a tax payment and create corresponding GL journal entry.

**Permissions**: `accounting.edit` OR `taxes.manage`

**Request Body**:
```json
{
  "return_id": 5,
  "amount": "135000.0000",
  "payment_date": "2025-04-28",
  "payment_method": "bank_transfer",
  "reference": "TRF-2025-001"
}
```

**Response 201**: Created TaxPayment with `gl_reference`  
**Response 400**: `{"detail": "Payment exceeds remaining tax due"}`

**GL Entry**: Dr. Tax Payable / Cr. Bank Account

---

## Tax Reports & Dashboard

### GET /taxes/summary
Dashboard summary for Tax Home.

**Permissions**: `accounting.view` OR `taxes.view`

**Response 200**:
```json
{
  "total_returns": 12,
  "pending_returns": 3,
  "overdue_calendar_items": 1,
  "current_vat_liability": "135000.0000",
  "ytd_output_vat": "540000.0000",
  "ytd_input_vat": "180000.0000",
  "net_vat_ytd": "360000.0000"
}
```

---

### GET /taxes/vat-report
VAT summary report for a period.

**Permissions**: `accounting.view` OR `taxes.view`

**Query Params**: `from_date`, `to_date`, `branch_id`

**Response 200**:
```json
{
  "period": {"from": "2025-01-01", "to": "2025-03-31"},
  "output_vat": "180000.0000",
  "input_vat": "45000.0000",
  "net_vat": "135000.0000",
  "taxable_sales": "1200000.0000",
  "taxable_purchases": "300000.0000"
}
```

---

### GET /taxes/audit-report
Tax audit trail per transaction.

**Permissions**: `accounting.view` OR `taxes.view`

**Query Params**: `from_date`, `to_date`, `tax_type`, `branch_id`

**Response 200**: List of transactions with applied tax rates

---

### GET /taxes/branch-analysis
VAT breakdown by branch.

**Permissions**: `accounting.view` OR `taxes.view`

**Response 200**: Array of branch totals with output_vat, input_vat, net_vat per branch

---

### GET /taxes/employee-taxes
Payroll tax/GOSI summary.

**Permissions**: `accounting.view` OR `taxes.view` OR `hr.view`

**Response 200**: Total WHT deductions and GOSI contributions for current period

---

## Tax Settlement

### POST /taxes/settle
Settle VAT liability — creates a GL reversal entry to clear the VAT Payable account.

**Permissions**: `taxes.manage` AND `accounting.edit`

**Request Body**:
```json
{
  "period_from": "2025-01-01",
  "period_to": "2025-03-31",
  "bank_account_id": 15,
  "reference": "VAT-SET-001"
}
```

**Response 200**: `{"message": "VAT settled", "gl_reference": "JE-2025-0459", "amount": "135000.0000"}`

---

## Tax Calendar

### GET /taxes/calendar
List tax calendar obligations.

**Permissions**: `accounting.view` OR `taxes.view`

**Query Params**:
| Param | Type | Description |
|-------|------|-------------|
| `status` | string | `overdue`, `upcoming`, `pending`, `completed` |
| `tax_type` | string | Filter by `VAT`, `ZAKAT`, `WHT`, etc. |
| `from_date` | date | |
| `to_date` | date | |

**Response 200**: List of TaxCalendar items with `days_remaining` (negative = overdue)

---

### GET /taxes/calendar/summary
Calendar summary counts.

**Response 200**: `{"overdue": 1, "upcoming_7_days": 2, "upcoming_30_days": 5, "completed_this_month": 3}`

---

### POST /taxes/calendar
Create a new calendar obligation.

**Permissions**: `taxes.manage`

**Request Body**:
```json
{
  "title": "VAT Filing - Q1 2026",
  "tax_type": "VAT",
  "due_date": "2026-04-30",
  "reminder_days": [7, 3, 1],
  "is_recurring": true,
  "recurrence_months": 3,
  "notes": "Quarterly ZATCA filing"
}
```

**Response 201**: Created TaxCalendar item

---

### PUT /taxes/calendar/{id}
Update a calendar obligation.

**Permissions**: `taxes.manage`

**Response 200**: Updated TaxCalendar item

---

### DELETE /taxes/calendar/{id}
Delete a calendar obligation.

**Permissions**: `taxes.manage`

**Response 200**: `{"message": "Calendar item deleted"}`

---

### PUT /taxes/calendar/{id}/complete
Mark obligation as complete; creates next recurrence if recurring.

**Permissions**: `taxes.manage`

**Response 200**:
```json
{
  "message": "Completed",
  "completed_at": "2026-04-15T14:30:00Z",
  "next_recurrence_id": 42
}
```
> `next_recurrence_id` is null for non-recurring items

---

## Error Responses

All endpoints return structured errors:

```json
{"detail": "Human-readable message"}
```

Common codes:
| HTTP | Meaning |
|------|---------|
| 400 | Business rule violation (duplicate, invalid state) |
| 401 | Not authenticated |
| 403 | Permission denied |
| 404 | Record not found |
| 422 | Validation error (missing required fields) |
| 500 | Internal error (generic message only — no stack trace) |
