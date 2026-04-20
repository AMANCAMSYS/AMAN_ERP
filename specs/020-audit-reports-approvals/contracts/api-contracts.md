# API Contracts: Reports & Analytics, Approvals & Workflow — Audit & Bug Fixes

**Feature**: 020-audit-reports-approvals  
**Date**: 2026-04-20

> This document records only the endpoints whose **request or response shape changes**.  
> URL paths and HTTP methods are unchanged (per spec assumption).

---

## 1. Approval Request Creation — Pydantic Schema (FR-024)

### `POST /api/approvals/requests` — Request body

**Before (broken — raw dict, no validation)**
```json
{
  "document_type": "purchase_order",
  "document_id": 42,
  "amount": 25000.0,
  "description": "PO for office supplies"
}
```

**After (Pydantic-validated, Decimal amount)**
```json
{
  "document_type": "purchase_order",
  "document_id": 42,
  "amount": "25000.0000",
  "description": "PO for office supplies"
}
```

**Backend**: New `ApprovalRequestCreate` schema with validated fields: `document_type` (str, required), `document_id` (int, required), `amount` (Decimal, required), `description` (Optional[str]). Missing/invalid fields return 422 (not 500).  
**Frontend**: `ApprovalsPage.jsx` — verify form submission sends correct field names. No shape change expected since the fields are the same; only validation is added server-side.

---

## 2. Approval Workflow Creation — Conditions Mapping (FR-025, FR-038)

### `POST /api/approvals/workflows` — Request body

**Before (misaligned — min/max at root, not in conditions)**
```json
{
  "name": "Purchase Approval",
  "document_type": "purchase_order",
  "steps": [{"approver_id": 5, "order": 1}],
  "min_amount": 1000.0,
  "max_amount": 50000.0
}
```

**After (conditions wrapped in JSONB structure, Decimal)**
```json
{
  "name": "Purchase Approval",
  "document_type": "purchase_order",
  "steps": [{"approver_id": 5, "order": 1}],
  "conditions": {
    "min_amount": "1000.0000",
    "max_amount": "50000.0000"
  }
}
```

**Backend**: `WorkflowCreateSchema` accepts `conditions` as a structured object. `min_amount`/`max_amount` are `Decimal`. The backend maps these into the `conditions` JSONB column. Alternatively, if `min_amount`/`max_amount` are sent at root level for backwards compatibility, the backend wraps them into `conditions` on save.  
**Frontend**: `WorkflowEditor.jsx` must send `min_amount`/`max_amount` inside `conditions` object (not at root). On load, extract from `conditions` for editing.

---

## 3. Approval Action — Concurrency Error (FR-026b)

### `POST /api/approvals/{id}/action` — New error response

**Before (race condition — both actions succeed)**
```json
// Second concurrent action succeeds — data corruption
HTTP 200 OK
```

**After (first-write-wins)**
```json
// Second concurrent action rejected
HTTP 409 Conflict
{
  "detail": "already_actioned"
}
```

**Backend**: `SELECT ... FOR UPDATE` locks the approval request row. After locking, checks if an action already exists for the current step. If yes, returns 409.  
**Frontend**: `ApprovalsPage.jsx` should handle 409 responses with a user-friendly message (e.g., "This step has already been actioned by another user. Please refresh.").

---

## 4. Approval Request Submission — Empty Steps Guard (FR-026a)

### `POST /api/approvals/requests` — New error response

**Before (workflow with empty steps silently accepted)**
```json
HTTP 200 OK  // Document bypasses approval entirely
```

**After (misconfigured workflow rejected)**
```json
HTTP 400 Bad Request
{
  "detail": "workflow_misconfigured_no_steps"
}
```

**Backend**: After matching a workflow, checks `steps` JSONB. If empty array or null, returns 400.  
**Frontend**: No change needed — standard error handling displays the message.

---

## 5. Report Endpoints — Decimal for Money (FR-008..FR-010)

### All financial report responses — Type change

Affects: `GET /api/reports/trial-balance`, `GET /api/reports/profit-loss`, `GET /api/reports/balance-sheet`, `GET /api/reports/cashflow`, `GET /api/reports/general-ledger`

**Before (float values)**
```json
{
  "accounts": [
    {
      "account_name": "Cash",
      "debit": 150000.0,
      "credit": 0.0,
      "balance": 150000.0
    }
  ],
  "total_debit": 500000.0,
  "total_credit": 500000.0
}
```

**After (Decimal values)**
```json
{
  "accounts": [
    {
      "account_name": "Cash",
      "debit": "150000.0000",
      "credit": "0.0000",
      "balance": "150000.0000"
    }
  ],
  "total_debit": "500000.0000",
  "total_credit": "500000.0000"
}
```

**Backend**: All monetary fields in report schema models changed from `float` to `Decimal`. Pydantic v2 serializes Decimal as string by default. `_compute_net_income_from_gl()` returns `Decimal`. `exchange_rate` defaults to `Decimal("1")`.  
**Frontend**: Minimal impact — React renders both string and number values. Verify `formatNumber()` utility handles string inputs (it likely already does, as other modules use Decimal).

---

## 6. Scheduled Reports — Recipients JSONB (FR-040)

### `POST /api/scheduled-reports` — Request body

**Before (comma-separated text)**
```json
{
  "report_name": "Weekly P&L",
  "report_type": "profit_loss",
  "frequency": "weekly",
  "recipients": "user1@company.com,user2@company.com",
  "format": "pdf",
  "report_config": {"branch_id": 1}
}
```

**After (JSONB array)**
```json
{
  "report_name": "Weekly P&L",
  "report_type": "profit_loss",
  "frequency": "weekly",
  "recipients": ["user1@company.com", "user2@company.com"],
  "format": "pdf",
  "report_config": {"branch_id": 1}
}
```

**Backend**: `recipients` stored as JSONB array. All reads/writes updated to use array operations instead of comma-separated parsing.  
**Frontend**: Forms that submit recipients must send a JSON array. Any comma-separated input field should split into array before sending.

### `GET /api/scheduled-reports/{id}` — Response

**Before**
```json
{ "recipients": "user1@company.com,user2@company.com" }
```

**After**
```json
{ "recipients": ["user1@company.com", "user2@company.com"] }
```

---

## 7. Scheduled Report Execution — New Stored Results (FR-039)

### No new API endpoint

Report execution happens in the background scheduler (`_execute_scheduled_report`). Results are stored in the new `scheduled_report_results` table. The existing `GET /api/scheduled-reports/{id}` response may be extended to include latest result status, but the URL and core shape are unchanged.

**Backend**: `_execute_scheduled_report` calls internal helpers (`_get_profit_loss_data`, `_get_balance_sheet_data`, etc.), stores result in `scheduled_report_results`, updates `last_run_at` and `last_status` on the `scheduled_reports` row.

---

## 8. Monetary Fields — Decimal Throughout

All monetary fields across Approvals responses will return `Decimal` string representations (e.g., `"25000.0000"`) instead of float (e.g., `25000.0`).

**Affected response fields** (non-exhaustive):
- Approval Request: `amount`
- Approval Workflow: `conditions.min_amount`, `conditions.max_amount`, `auto_approve_below`
- KPI Dashboard: All monetary KPI values
- Report data: All debit, credit, balance, total fields

**Frontend impact**: Minimal — `formatNumber()` utility handles both string and number inputs.

---

## No-Change Endpoints

| Endpoint | Reason |
|----------|--------|
| `GET /api/reports/trial-balance` | URL unchanged; only response value types change (float→Decimal) — covered in section 5 |
| `GET /api/reports/profit-loss` | Same as above |
| `GET /api/reports/balance-sheet` | Same as above |
| `GET /api/reports/cashflow` | Same as above |
| `GET /api/reports/general-ledger` | Same as above |
| `GET /api/approvals/requests` | Response shape unchanged; concurrency fix is internal |
| `GET /api/approvals/workflows` | Response shape unchanged; conditions default fix is internal |
| `GET /api/scheduled-reports` | List endpoint unchanged; individual recipient format change only affects detail/create |
| `GET /api/analytics/dashboards` | Response shape unchanged; `created_by` type change (VARCHAR→INT) is an internal DB fix |
| `GET /api/kpi/*` | URL unchanged; KPI values may change to Decimal but the response structure is the same |
| `POST /api/reports/export/*` | Export endpoints unchanged; Decimal conversion is internal |
