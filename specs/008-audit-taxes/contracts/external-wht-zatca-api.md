# API Contract: /external/wht/* & /external/zatca/* — WHT Certificates & ZATCA E-Invoicing

**Router**: `backend/routers/external.py`  
**Prefix**: `/external`  
**Auth**: Bearer JWT required

---

## Withholding Tax (WHT)

### GET /external/wht/rates
List active WHT rates by category.

**Permissions**: `accounting.view` OR `taxes.view`

**Query Params**: `category`, `is_active`

**Response 200**:
```json
[
  {
    "id": 1,
    "category": "professional_services",
    "category_ar": "الخدمات المهنية",
    "rate": "5.0000",
    "effective_date": "2020-01-01",
    "expiry_date": null,
    "is_active": true
  },
  {
    "id": 2,
    "category": "rent",
    "category_ar": "الإيجار",
    "rate": "5.0000",
    "effective_date": "2020-01-01",
    "expiry_date": null,
    "is_active": true
  }
]
```

---

### POST /external/wht/rates
Create a new WHT rate.

**Permissions**: `accounting.edit` AND `taxes.manage`

**Request Body**:
```json
{
  "category": "technical_services",
  "category_ar": "الخدمات التقنية",
  "rate": "15.0000",
  "effective_date": "2026-01-01",
  "notes": "GAZT circular 2025"
}
```

**Response 201**: Created WhtRate

---

### POST /external/wht/calculate
Calculate WHT amount without creating a transaction (preview only).

**Permissions**: `accounting.view` OR `taxes.view`

**Request Body**:
```json
{
  "wht_rate_id": 1,
  "gross_amount": "20000.0000"
}
```

**Response 200**:
```json
{
  "gross_amount": "20000.0000",
  "wht_rate": "5.0000",
  "wht_amount": "1000.0000",
  "net_amount": "19000.0000"
}
```

> All amounts as strings (Constitution §I)

---

### POST /external/wht/transactions
Create a WHT certificate and post GL entries.

**Permissions**: `accounting.edit` AND `taxes.manage`

**Request Body**:
```json
{
  "supplier_id": 45,
  "wht_rate_id": 1,
  "gross_amount": "20000.0000",
  "transaction_date": "2026-04-15",
  "invoice_reference": "SUP-INV-2026-001",
  "expense_account_id": 612,
  "bank_account_id": 101,
  "notes": "Professional consulting fee"
}
```

**Response 201**:
```json
{
  "id": 23,
  "certificate_number": "WHT-2026-0023",
  "supplier_id": 45,
  "supplier_name": "Acme Consulting",
  "category": "professional_services",
  "rate": "5.0000",
  "gross_amount": "20000.0000",
  "wht_amount": "1000.0000",
  "net_amount": "19000.0000",
  "transaction_date": "2026-04-15",
  "invoice_reference": "SUP-INV-2026-001",
  "gl_reference": "JE-2026-0891",
  "created_at": "2026-04-15T12:00:00Z"
}
```

**GL Entry created** (Constitution §III — via gl_service):
```
Dr. Expense Account (expense_account_id)    20000.0000  gross_amount
    Cr. WHT Payable (220xxx)                  1000.0000  wht_amount
    Cr. Bank / AP (bank_account_id)          19000.0000  net_amount
```

**Response 400**: `{"detail": "Fiscal period is locked for date 2026-04-15"}`  
**Response 404**: Supplier or WHT rate not found

---

### GET /external/wht/transactions
List WHT certificates with filters.

**Permissions**: `accounting.view` OR `taxes.view`

**Query Params**:
| Param | Type | Description |
|-------|------|-------------|
| `supplier_id` | int | Filter by supplier |
| `from_date` | date | `transaction_date >= from_date` |
| `to_date` | date | `transaction_date <= to_date` |
| `category` | string | Filter by WHT category |
| `page` | int | Default 1 |
| `page_size` | int | Default 25, max 100 |

**Response 200**:
```json
{
  "total": 47,
  "page": 1,
  "page_size": 25,
  "items": [
    {
      "id": 23,
      "certificate_number": "WHT-2026-0023",
      "supplier_name": "Acme Consulting",
      "category": "professional_services",
      "rate": "5.0000",
      "gross_amount": "20000.0000",
      "wht_amount": "1000.0000",
      "net_amount": "19000.0000",
      "transaction_date": "2026-04-15",
      "gl_reference": "JE-2026-0891"
    }
  ]
}
```

---

## ZATCA E-Invoicing

### POST /external/zatca/generate-qr
Generate a ZATCA-compliant QR code for an invoice.

**Permissions**: `accounting.edit` OR `invoices.create`

**Request Body**:
```json
{
  "invoice_id": 1234
}
```

**Response 200**:
```json
{
  "invoice_id": 1234,
  "qr_base64": "AQlBY21lIENvcnAAA...",
  "zatca_phase": 1
}
```

**QR Code TLV Encoding** (ZATCA standard):
| Tag | Field |
|-----|-------|
| 1 | Seller name |
| 2 | VAT registration number |
| 3 | Invoice timestamp (ISO 8601) |
| 4 | Invoice total (with VAT) |
| 5 | VAT amount |

---

### POST /external/zatca/generate-keypair
Generate RSA key pair for ZATCA Phase 2 signing.

**Permissions**: `taxes.manage` (admin only)

**Response 200**: `{"message": "ZATCA keypair generated and stored securely"}` 

> ⛔ Private key NEVER returned in response. Stored encrypted in `company_tax_settings.zatca_private_key`.

---

### GET /external/zatca/verify/{invoice_id}
Verify ZATCA hash and signature for an existing invoice.

**Permissions**: `accounting.view` OR `taxes.view`

**Response 200**:
```json
{
  "invoice_id": 1234,
  "qr_valid": true,
  "signature_valid": true,
  "zatca_phase": 2,
  "verified_at": "2026-04-15T12:00:00Z"
}
```

**Response 404**: Invoice not found  
**Response 422**: Invoice has no ZATCA QR code (was not Saudi/Phase 1+)

---

## Auto-ZATCA on Invoice Creation

> This is not a direct call — it is automatically triggered by `POST /invoices` (sales):

```
POST /invoices (sales invoice creation)
  └── After GL posting succeeds:
      └── process_invoice_for_zatca(db, invoice_id, company_id)
          ├── Phase 1: generate TLV QR → store qr_base64 on invoice
          └── Phase 2: sign XML → attach signature + QR → store on invoice
          └── On exception: log warning, invoice creation still succeeds (graceful)
```

**Returned** in invoice response:
```json
{
  "id": 1234,
  "invoice_number": "INV-2026-001",
  "zatca_qr": "AQlBY21lIENvcnAAA..."
}
```
