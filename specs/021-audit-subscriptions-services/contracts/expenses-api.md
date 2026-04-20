# API Contract Changes: Expenses

**Module**: Expenses (`/api/expenses/*`)
**Date**: 2026-04-20

## Changed Endpoints

### POST /api/expenses/policies
**Change**: Now accepts Pydantic schema instead of raw dict
- Request body validated: `name` (required), `expense_type` (required, from unified enum), `department_id` (optional int), limits as Decimal
- Returns `422` on validation failure (was `500`)
- Expense types unified: `travel`, `meals`, `supplies`, `transportation`, `entertainment`, `materials`, `labor`, `services`, `rent`, `utilities`, `salaries`, `other`

### PUT /api/expenses/policies/{id}
**Change**: Now accepts Pydantic schema instead of raw dict
- Same validation as POST
- Returns `422` on validation failure (was `500`)
- Soft-delete: DELETE endpoint now sets `is_deleted = true` (was hard delete)

### DELETE /api/expenses/policies/{id}
**Change**: Soft-delete instead of hard delete
- Record marked `is_deleted = true`, `updated_at = NOW()`
- Returns `200` (unchanged)
- Record excluded from list queries but retained in database

### POST /api/expenses/validate-policy
**Change**: Now accepts Pydantic schema instead of raw dict
- Request body validated: `expense_type` (required), `amount` (required Decimal), `department_id` (optional int)

### POST /api/expenses/
**Change**: 
- `amount` processed as Decimal (was float-cast)
- `check_fiscal_period_open()` now enforced — returns `400` if period closed
- Policy validation enforced during creation (was separate endpoint only)
- `currency` and `exchange_rate` accepted in request body
- `policy_id` can be specified to link expense to policy

### POST /api/expenses/{id}/approve
**Change**: Treasury balance check now uses `FOR UPDATE` lock
- Concurrent approval requests properly serialized
- Second concurrent approval may fail with `409 Conflict` if balance insufficient after first approval

### DELETE /api/expenses/{id}
**Change**: Soft-delete instead of hard delete
- Record marked `is_deleted = true`

## Response Shape Changes

### Expense Record
```json
{
  "id": 1,
  "expense_number": "EXP-2026-001",
  "amount": "1500.00",
  "currency": "SAR",
  "exchange_rate": "1.000000",
  "policy_id": 5,
  "approval_status": "pending"
}
```
New fields: `currency`, `exchange_rate`, `policy_id`
