# API Contract Changes: Subscriptions

**Module**: Subscriptions (`/api/subscriptions/*`)
**Date**: 2026-04-20

## Changed Endpoints

### POST /api/subscriptions/plans
**Change**: `base_amount` field now validated as Decimal (was float-cast internally)
- Request body unchanged (string/number accepted, converted to Decimal server-side)
- No breaking change for API consumers

### POST /api/subscriptions/enroll
**Change**: Adds approval workflow integration and fiscal period check
- May return `400` if fiscal period is closed (new error)
- May return `200` with `approval_request_id` if amount exceeds approval threshold (new field in response)
- May return `409` if customer already has active enrollment in same plan (new error)
- Response adds: `journal_entry_id`, `tax_amount`, `currency` on generated invoice

### POST /api/subscriptions/change-plan
**Change**: Fiscal period check added
- May return `400` if fiscal period is closed (new error)

### Invoice Generation (internal service)
**Change**: `generate_subscription_invoice` now:
- Posts GL journal entry (DR Receivable, CR Revenue/Deferred Revenue, CR VAT Payable)
- Checks fiscal period before creation
- Includes VAT in invoice amount
- Returns idempotently if invoice already exists for billing period

## Response Shape Changes

### Subscription Invoice (in enrollment detail)
```json
{
  "id": 1,
  "enrollment_id": 1,
  "invoice_id": 100,
  "billing_period_start": "2026-01-01",
  "billing_period_end": "2026-01-31",
  "amount": "115.00",
  "tax_rate": "15.00",
  "tax_amount": "15.00",
  "currency": "SAR",
  "journal_entry_id": 500,
  "is_prorated": false,
  "proration_details": null
}
```
New fields: `tax_rate`, `tax_amount`, `currency`, `journal_entry_id`
