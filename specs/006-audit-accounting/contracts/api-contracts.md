# API Contracts: Audit Accounting Module

**Feature**: 006-audit-accounting  
**Date**: 2026-04-14  
**Source**: Extracted from existing backend routers

---

## Base URL

All endpoints are prefixed with `/api` and require JWT authentication via `Authorization: Bearer <token>`.

---

## 1. Chart of Accounts

### GET /api/accounting/accounts

List all accounts with live balances computed from journal lines.

**Permission**: `accounting.view`  
**Query Parameters**:
- `branch_id` (optional): Filter by branch

**Response** `200`:
```json
{
  "accounts": [
    {
      "id": 1,
      "account_number": "11001",
      "account_code": "11001",
      "name": "الصندوق",
      "name_en": "Cash",
      "account_type": "asset",
      "parent_id": null,
      "is_header": false,
      "balance": 50000.00,
      "is_active": true
    }
  ]
}
```

**Audit Points**:
- ✅ Tenant isolation via `get_db_connection(current_user.company_id)`
- ✅ Branch access validated via `validate_branch_access()`
- ⚠️ Balance returned as `float()` — acceptable for display only

### POST /api/accounting/accounts

Create a new GL account.

**Permission**: `accounting.edit`  
**Request Body**:
```json
{
  "account_number": "11005",
  "name": "حساب جديد",
  "name_en": "New Account",
  "account_type": "asset",
  "parent_id": 1
}
```

**Response** `201`: Created account object  
**Error** `400`: Duplicate account number, invalid type  
**Audit**: `log_activity()` called on success

### DELETE /api/accounting/accounts/{account_id}

Delete an unused account.

**Permission**: `accounting.edit`  
**Response** `200`: Success  
**Error** `400`: Account has journal lines (deletion blocked)

---

## 2. Journal Entries

### POST /api/accounting/journal-entries

Create a new journal entry (via `gl_service.create_journal_entry()`).

**Permission**: `accounting.edit`  
**Request Body**:
```json
{
  "entry_date": "2026-04-14",
  "description": "قيد يومية",
  "reference": "REF-001",
  "status": "posted",
  "currency": "SAR",
  "exchange_rate": 1.0,
  "branch_id": 1,
  "lines": [
    {"account_id": 1, "debit": 1000.00, "credit": 0, "cost_center_id": null, "description": "مدين"},
    {"account_id": 2, "debit": 0, "credit": 1000.00, "cost_center_id": null, "description": "دائن"}
  ]
}
```

**Validation Pipeline** (Constitution XXII order):
1. Permission check (`require_permission`)
2. Branch access validation
3. Fiscal period open check (`check_fiscal_period_open`)
4. Line validation (`validate_je_lines`): debit=credit, no negatives, min 2 lines
5. Sequential number generation
6. Persist JE header + lines
7. If status=posted: `update_account_balance()` for each line
8. Audit log

**Response** `201`:
```json
{
  "id": 42,
  "entry_number": "JE-2026-00042",
  "status": "posted"
}
```

**Errors**:
- `400`: Unbalanced entry, negative amounts, locked fiscal period, < 2 lines
- `403`: Insufficient permissions
- `404`: Referenced account not found

**Audit Points**:
- ✅ Double-entry enforced
- ✅ Decimal precision with `ROUND_HALF_UP`
- ✅ Fiscal period checked
- ❌ DEFECT: Sequential numbering lacks `FOR UPDATE` lock — race condition
- ⚠️ Audit logging is caller's responsibility, not internal to GL service

---

## 3. Fiscal Period Locks

### POST /api/accounting/fiscal-periods/lock

Lock a fiscal period to prevent postings.

**Permission**: `accounting.edit` (fiscal period management)  
**Request Body**:
```json
{
  "period_name": "يناير 2026",
  "period_start": "2026-01-01",
  "period_end": "2026-01-31",
  "reason": "إقفال شهري"
}
```

**Response** `200`: Period locked  
**Audit**: Lock action recorded with user, timestamp, reason

### POST /api/accounting/fiscal-periods/unlock

Unlock a previously locked period.

**Permission**: `accounting.edit`  
**Response** `200`: Period unlocked  
**Audit**: Unlock action recorded

---

## 4. Currencies

### GET /api/accounting/currencies

List all currencies with auto-provisioning on first access.

**Permission**: `accounting.view`  
**Response** `200`:
```json
{
  "currencies": [
    {"id": 1, "code": "SAR", "name": "ريال سعودي", "is_base": true, "current_rate": 1.0},
    {"id": 2, "code": "USD", "name": "دولار أمريكي", "is_base": false, "current_rate": 3.75}
  ]
}
```

**Audit Points**:
- ✅ Auto-creates table and seeds base currency if missing
- ✅ ISO 4217 validation (`^[A-Z]{3}$`)

### POST /api/accounting/currencies

Create a new currency.

**Permission**: `accounting.edit`  
**Validation**: ISO 4217 code, exchange rate > 0, only one base currency

### PUT /api/accounting/currencies/{currency_id}

Update currency. Enforces single base currency constraint.

### DELETE /api/accounting/currencies/{currency_id}

Delete currency (only if unused in transactions).

---

## 5. Budgets

### POST /api/accounting/budgets

Create a budget.

**Permission**: `accounting.budgets.manage`  
**Module Guard**: `require_module("budgets")`

### GET /api/accounting/budgets

List budgets with status filter.

**Permission**: `accounting.budgets.view`

### DELETE /api/accounting/budgets/{budget_id}

Delete budget (blocked if status=active).

### POST /api/accounting/budgets/{budget_id}/items

Upsert budget line items (per-account uniqueness enforced).

---

## 6. Cost Centers

### GET /api/cost-centers

List all cost centers.

### POST /api/cost-centers

Create cost center (duplicate code check).

### PUT /api/cost-centers/{cc_id}

Update cost center (duplicate code check on rename).

### DELETE /api/cost-centers/{cc_id}

Delete cost center (blocked if used in journal_lines).

---

## 7. Intercompany (v2 — Recommended)

### POST /api/accounting/intercompany/transactions

Create intercompany transaction with reciprocal journal entries.

**Permission**: `accounting.edit`  
**Request Body**:
```json
{
  "source_entity_id": 1,
  "target_entity_id": 2,
  "amount": 50000.00,
  "currency": "SAR",
  "exchange_rate": 1.0,
  "description": "خدمات بين الشركات"
}
```

**Behavior**:
1. Resolves source & target entities
2. Looks up intercompany account mapping (defaults to 13xx/21xx if unmapped)
3. Creates source JE: Dr IC Receivable, Cr Revenue
4. Creates target JE: Dr Expense, Cr IC Payable
5. Inserts transaction record linking both JEs
6. Atomic commit (all-or-nothing)

**Response** `201`:
```json
{
  "transaction_id": 5,
  "source_je_id": 100,
  "target_je_id": 101
}
```

### POST /api/accounting/intercompany/consolidate

Run consolidation elimination — generates entries that net intercompany balances to zero.

### GET /api/accounting/intercompany/balances

Outstanding intercompany balance report.

### GET/POST /api/accounting/intercompany/mappings

Account mapping CRUD for entity pairs.

---

## 8. Costing Policies

### GET /api/costing-policies/current

Get active costing policy.

### POST /api/costing-policies/set

Switch costing policy with impact analysis.

**Request Body**:
```json
{
  "policy_type": "per_warehouse_wac",
  "reason": "تحسين دقة التكلفة"
}
```

**Response** `200`: Impact analysis + policy switch confirmation

### GET /api/costing-policies/history

Policy change history with metrics.

---

## 9. Approval Workflow (Advanced)

### GET /api/workflow/advanced/{workflow_id}

View workflow with conditions and SLA.

### POST /api/workflow/check-escalation

Poll for overdue approval requests and escalate.

### POST /api/workflow/auto-approve

Auto-approve requests below threshold.

### GET /api/workflow/analytics

Approval metrics (pending, approved, rejected, avg hours).

---

## 10. Financial Reports

### GET /api/reports/trial-balance

**Query Params**: `start_date`, `end_date`, `branch_id`  
**Source**: Direct query on `journal_lines` + `journal_entries`  
**Validation**: Total debits MUST equal total credits

### GET /api/reports/balance-sheet

**Query Params**: `as_of_date`, `branch_id`  
**Validation**: Assets = Liabilities + Equity

### GET /api/reports/income-statement

**Query Params**: `start_date`, `end_date`, `branch_id`

### GET /api/reports/cash-flow

**Query Params**: `start_date`, `end_date`  
**Audit Finding**: ⚠️ Uses `float()` before aggregation — precision loss risk

---

## 11. Balance Reconciliation

### POST /api/accounting/reconcile (internal/scheduled)

**Functions**:
- `reconcile_account_balances()`: Compares `accounts.balance` vs SUM(journal_lines)
- `reconcile_treasury_balances()`: Compares treasury vs linked GL accounts
- `run_full_reconciliation()`: Runs both

**Tolerance**: 0.01 — only flags discrepancies above 1 cent

---

## Error Response Contract

All endpoints follow a standardized error format per Constitution IV:

```json
{
  "detail": "حدث خطأ أثناء معالجة الطلب"
}
```

**Rules**:
- NO stack traces, SQL fragments, or file paths in `detail`
- Full error logged server-side via `logger.exception()`
- HTTP status codes: 400 (validation), 403 (permission), 404 (not found), 500 (internal)

---

## Rate Limiting (DEFECT — Currently Missing)

Per Constitution IV, all endpoints should enforce:
- Mutation endpoints: 100 requests/minute per user
- Read endpoints: 200 requests/minute per user

**Current Status**: ❌ No rate limiting on any accounting endpoint — must be added.
