# API Contracts: Projects, Contracts & Fixed Assets — Audit & Bug Fixes

**Feature**: 019-audit-projects-assets  
**Date**: 2026-04-20

> This document records only the endpoints whose **request or response shape changes**.  
> URL paths and HTTP methods are unchanged (per spec assumption).

---

## 1. Project Risk Endpoints — Type Change

### `POST /api/projects/{project_id}/risks` — Request body

**Before (broken — raw dict, wrong types)**
```json
{
  "risk_name": "Supply chain delay",
  "probability": 0.75,
  "impact": 0.9,
  "mitigation_strategy": "..."
}
```

**After (Pydantic-validated, correct types)**
```json
{
  "risk_name": "Supply chain delay",
  "probability": "high",
  "impact": "critical",
  "mitigation_strategy": "...",
  "risk_owner_id": 5
}
```

**Backend**: New `ProjectRiskCreate` schema. `probability`/`impact` become string enums (`"low"`, `"medium"`, `"high"`, `"critical"`) matching `String(20)` column.  
**Frontend**: `ProjectRisks.jsx` form values already use string labels — no frontend change needed.

---

## 2. Task Dependency Endpoints — Pydantic Schema

### `POST /api/projects/{project_id}/tasks/{task_id}/dependencies` — Request body

**Before (raw dict)**
```json
{ "depends_on_task_id": 42, "dependency_type": "finish_to_start" }
```

**After (Pydantic-validated + self-dependency check)**
```json
{ "depends_on_task_id": 42, "dependency_type": "finish_to_start" }
```

Shape unchanged, but now validated via `TaskDependencyCreate` schema. Server rejects `depends_on_task_id == task_id` with 400.

---

## 3. `POST /api/projects` — Missing Fields Now Persisted

### `POST /api/projects` — Request body (unchanged)

```json
{
  "project_name": "...",
  "branch_id": 3,
  "contract_type": "fixed_price",
  "budget": "150000.0000",
  ...
}
```

**Before**: `branch_id` and `contract_type` silently dropped from INSERT.  
**After**: Both fields persisted. Response now includes them.

**Frontend**: No change — `ProjectCreate` schema already includes these fields.

---

## 4. Contract KPI Endpoint — Response Fix

### `GET /api/contracts/kpis` — Response

**Before (broken — SQL error on nonexistent columns)**
```json
HTTP 500 Internal Server Error
```

**After (correct)**
```json
{
  "total_contracts": 15,
  "total_value": "450000.0000",
  "total_paid": "280000.0000",
  "total_balance": "170000.0000",
  "average_completion": 62.5
}
```

**Backend**: Fix column names (`total` not `total_amount`), compute `balance = total - paid_amount`.

---

## 5. Contract Amendment — Pydantic Schema

### `POST /api/contracts/{contract_id}/amendments` — Request body

**Before (raw dict)**
```json
{ "amendment_type": "scope_change", "effective_date": "2026-05-01", "description": "...", "amount_change": 5000 }
```

**After (Pydantic-validated)**
```json
{
  "amendment_type": "scope_change",
  "effective_date": "2026-05-01",
  "description": "Extended scope for phase 2",
  "amount_change": "5000.0000"
}
```

**Backend**: New `ContractAmendmentCreate` schema with required fields. `amount_change` is `Decimal`.  
**Frontend**: Contract pages that submit amendments may need minor field name alignment.

---

## 6. Contract Update — Partial Updates + Total Recalculation

### `PUT /api/contracts/{contract_id}` — Request body

**Before (broken — requires ALL fields from ContractCreate)**
```json
{
  "contract_number": "...",
  "party_id": 1,
  "contract_type": "...",
  "start_date": "...",
  "end_date": "...",
  "total_amount": 50000,
  ...all required fields...
}
```

**After (partial update via ContractUpdate)**
```json
{
  "end_date": "2027-01-01",
  "notes": "Extended by 6 months"
}
```

**Backend**: New `ContractUpdate` schema (all fields Optional). Server recalculates `total_amount` from line items after update — client-provided `total_amount` is ignored.

---

## 7. Asset Impairment Test — Response Fix

### `POST /api/assets/{asset_id}/impairment-test` — Response

**Before (broken — crash on `purchase_cost`, `journal_entry_id` always null)**
```json
HTTP 500 Internal Server Error
```

**After (correct)**
```json
{
  "asset_id": 1,
  "carrying_amount": "95000.0000",
  "recoverable_amount": "80000.0000",
  "impairment_loss": "15000.0000",
  "journal_entry_id": 1234,
  "impaired": true
}
```

**Backend**: Uses `cost` column; captures GL journal entry ID correctly.

---

## 8. Asset Depreciation Post — Parameter Fix

### `POST /api/assets/{asset_id}/depreciation/{schedule_id}/post` — Internal fix

Request/response shape unchanged. Internal fix: `user_id` parameter to GL service receives `current_user.id` (int) instead of `current_user.username` (string).

---

## 9. Asset Revaluation — Preserve Historical Cost

### `POST /api/assets/{asset_id}/revalue` — Request body

**Before (raw dict)**
```json
{ "new_value": 120000, "revaluation_date": "2026-04-01", "reason": "Market appraisal" }
```

**After (Pydantic-validated)**
```json
{
  "new_value": "120000.0000",
  "revaluation_date": "2026-04-01",
  "reason": "Market appraisal"
}
```

**Backend**: New `AssetRevaluationCreate` schema. Revaluation updates `current_value` (not `cost`). Checks `revaluation_surplus` for downward revaluations per IAS 16.40.

---

## 10. Asset Transfer — Pydantic Schema

### `POST /api/assets/{asset_id}/transfer` — Request body

**Before (raw dict)**
```json
{ "to_branch_id": 5, "transfer_date": "2026-04-01", "reason": "Branch consolidation" }
```

**After (Pydantic-validated)**
```json
{
  "to_branch_id": 5,
  "transfer_date": "2026-04-01",
  "reason": "Branch consolidation"
}
```

**Backend**: New `AssetTransferCreate` schema.

---

## 11. Lease Contract — Pydantic Schema + ROU Depreciation

### `POST /api/assets/leases` — Request body

**Before (raw dict)**
```json
{ "asset_id": 1, "lessor": "...", "start_date": "...", "end_date": "...", "monthly_payment": 5000, "discount_rate": 5.0 }
```

**After (Pydantic-validated)**
```json
{
  "asset_id": 1,
  "lessor": "XYZ Leasing",
  "start_date": "2026-01-01",
  "end_date": "2028-12-31",
  "monthly_payment": "5000.0000",
  "discount_rate": "5.0000"
}
```

**Backend**: New `LeaseContractCreate` schema. On creation, ROU depreciation schedule is auto-generated.

### New Endpoint: `POST /api/assets/leases/{lease_id}/post-payment` (FR-031)

```json
// Request
{ "payment_date": "2026-02-01", "amount": "5000.0000" }

// Response
{
  "lease_id": 1,
  "payment_date": "2026-02-01",
  "interest_portion": "208.33",
  "principal_portion": "4791.67",
  "remaining_liability": "145208.33",
  "journal_entry_id": 5678
}
```

---

## 12. Monetary Fields — Decimal Throughout

All monetary fields across Projects, Contracts, and Assets responses will return `Decimal` string representations (e.g., `"150000.0000"`) instead of float (e.g., `150000.0`).

**Affected response fields** (non-exhaustive):
- Project: `budget`, `actual_cost`, `amount`, `retainer_amount`
- Contract: `total`, `paid_amount`, `balance`
- Asset: `cost`, `residual_value`, `current_value`, `book_value`

**Frontend impact**: Minimal — React renders both string and number values. `formatNumber()` utility handles both.

---

## No-Change Endpoints

| Endpoint | Reason |
|----------|--------|
| `GET /api/projects` | Response shape unchanged; route ordering fix is internal |
| `GET /api/projects/{id}/tasks` | Column name fix in SQL is internal; response shape unchanged |
| `GET /api/projects/{id}/timesheets` | `branch_id` added to SELECT is additive |
| `GET /api/contracts` | N+1 fix is a performance optimization; response shape unchanged |
| `POST /api/assets` | Error handling fix is internal; schema unchanged |
| `POST /api/assets/{id}/depreciation/post` | `user_id` fix is internal; response unchanged |
| All `GET` list endpoints | Pagination/filter behavior unchanged |
