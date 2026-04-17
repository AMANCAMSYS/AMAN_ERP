# API Contracts: audit-treasury — الخزينة والبنوك

**Date**: 2026-04-14  
**Phase**: 1 — Design & Contracts

> These contracts document the existing API surface with audit-driven changes marked as **[AUDIT FIX]** or **[AUDIT NEW]**.

## Base Path

All endpoints under `/api/treasury/` and `/api/finance/`.

## Authentication & Authorization

All endpoints require:
- `Authorization: Bearer <JWT>` header
- Module guard: `require_module("treasury")`
- Permission: `require_permission("treasury.<action>")` where action ∈ {view, create, manage, delete}

---

## 1. Treasury Accounts

### GET `/treasury/accounts`
List all treasury accounts for the current company.

**Query Parameters**:
| Param | Type | Required | Default |
|-------|------|----------|---------|
| branch_id | int | no | all branches |
| limit | int | no | 25 |
| offset | int | no | 0 |

**Response 200**:
```json
{
  "accounts": [
    {
      "id": 1,
      "name": "الصندوق الرئيسي",
      "name_en": "Main Cash",
      "account_type": "cash",
      "currency": "SAR",
      "current_balance": "50000.0000",
      "gl_account_id": 42,
      "gl_account_code": "1101001",
      "branch_id": 1,
      "bank_name": null,
      "account_number": null,
      "iban": null,
      "is_active": true,
      "allow_overdraft": null
    }
  ],
  "total": 5
}
```

### POST `/treasury/accounts`
Create a new treasury account with auto-linked GL account.

**[AUDIT FIX]**: Add `check_fiscal_period_open()` before opening balance GL posting (R-008). Add `allow_overdraft` field (R-004).

**Request Body**:
```json
{
  "name": "بنك الراجحي",
  "name_en": "Al Rajhi Bank",
  "account_type": "bank",
  "currency": "SAR",
  "bank_name": "بنك الراجحي",
  "account_number": "1234567890",
  "iban": "SA0380000000608010167519",
  "opening_balance": 100000,
  "exchange_rate": 1.0,
  "branch_id": 1,
  "allow_overdraft": null
}
```

**Response 201**: Created account object.

### PUT `/treasury/accounts/{id}`
Update treasury account details.

**[AUDIT FIX]**: Log GL account linkage changes in audit trail (before/after `gl_account_id`).

### DELETE `/treasury/accounts/{id}`
Soft-delete (deactivate) a treasury account.

**Validation**: Rejects if `current_balance != 0` or any non-cancelled transactions exist.

---

## 2. Treasury Transactions

### POST `/treasury/transactions/expense`
Record an expense paid from a treasury account.

**[AUDIT FIX]**: 
1. Reorder to GL-first, balance-second (R-001)
2. Add `SELECT FOR UPDATE` on treasury account (R-002)
3. Add fiscal period check (already in code, verify)
4. Add overdraft validation (R-004)
5. Persist `exchange_rate` in transaction record (R-009)

**Request Body**:
```json
{
  "treasury_id": 1,
  "target_account_id": 55,
  "amount": 3000,
  "description": "مصروفات إيجار",
  "transaction_date": "2026-04-14",
  "exchange_rate": 1.0,
  "branch_id": 1
}
```

**Response 201**: Transaction object with `transaction_number` and `journal_entry_id`.

**Error 400**: Fiscal period locked, insufficient balance (cash accounts), inactive account.

### POST `/treasury/transactions/transfer`
Transfer between treasury accounts.

**[AUDIT FIX]**: Same fixes as expense (R-001, R-002, R-004, R-009).

**Request Body**:
```json
{
  "treasury_id": 1,
  "target_treasury_id": 2,
  "amount": 8000,
  "description": "تحويل بين حسابات",
  "transaction_date": "2026-04-14",
  "exchange_rate": 1.0
}
```

---

## 3. Checks Receivable

### GET `/checks/receivable`
List checks receivable with filtering.

**Query Parameters**: `status`, `branch_id`, `search`, `limit`, `offset`

### GET `/checks/receivable/summary/stats`
Summary statistics by status.

### POST `/checks/receivable`
Create a check receivable.

**[AUDIT FIX]**: 
1. Add duplicate check number warning (R-007)
2. Persist `exchange_rate` (R-009)
3. Call `ensure_treasury_gl_accounts()` for 1205 auto-creation (R-005)

**Request Body**:
```json
{
  "check_number": "CHK-001",
  "drawer_name": "شركة الأمان",
  "bank_name": "بنك الراجحي",
  "branch_name": "فرع الرياض",
  "amount": 15000,
  "currency": "SAR",
  "exchange_rate": 1.0,
  "issue_date": "2026-04-01",
  "due_date": "2026-05-01",
  "party_id": 10,
  "treasury_account_id": 1,
  "notes": ""
}
```

**Response 201**: Check object with `journal_entry_id`.
**Response 409** (warning): Duplicate check number found — includes existing check details.

### POST `/checks/receivable/{id}/collect`
Collect a pending check.

**[AUDIT FIX]**: Add `SELECT FOR UPDATE` on check row (R-002).

**Request Body**: `{ "collection_date": "2026-05-01", "treasury_account_id": 1 }`

**Validation**: Status must be `pending`. Row locked via `FOR UPDATE`.

### POST `/checks/receivable/{id}/bounce`
Mark a check as bounced.

**Request Body**: `{ "bounce_date": "2026-05-02", "bounce_reason": "رصيد غير كافي" }`

**Validation**: Status must be `pending` or `collected`. Row locked via `FOR UPDATE`.

### POST `/checks/receivable/{id}/represent` **[AUDIT NEW]**
Re-present a bounced check (R-003).

**Request Body**: `{ "re_presentation_date": "2026-05-10" }`

**Validation**: Status must be `bounced`. Row locked via `FOR UPDATE`.

**Behavior**:
1. Posts new GL entry (Dr. 1205 Checks Under Collection / Cr. AR)
2. Status → `pending`
3. Clears `bounce_date`, `bounce_reason`
4. Sets `re_presentation_date`, increments `re_presentation_count`
5. Stores `re_presentation_journal_id`

**Response 200**: Updated check object.

---

## 4. Checks Payable

Mirror of Checks Receivable with adjusted field names:

| Receivable Endpoint | Payable Equivalent |
|--------------------|--------------------|
| POST `/checks/receivable` | POST `/checks/payable` |
| POST `/{id}/collect` | POST `/{id}/clear` |
| POST `/{id}/bounce` | POST `/{id}/bounce` |
| POST `/{id}/represent` **[NEW]** | POST `/{id}/represent` **[NEW]** |

---

## 5. Notes Receivable

### POST `/notes/receivable`
Create a note receivable.

**[AUDIT FIX]**: Persist `exchange_rate`, call `ensure_treasury_gl_accounts()` for 1210.

### POST `/notes/receivable/{id}/collect`
Collect at maturity.

**[AUDIT FIX]**: Add `SELECT FOR UPDATE`.

### POST `/notes/receivable/{id}/protest`
Protest (legal rejection). **TERMINAL state** — no re-presentation.

---

## 6. Notes Payable

Mirror of Notes Receivable:
- POST `/notes/payable` → create
- POST `/{id}/pay` → pay at maturity
- POST `/{id}/protest` → protest (TERMINAL)

---

## 7. Bank Reconciliation

### POST `/reconciliation`
Create draft reconciliation.

### POST `/reconciliation/{id}/import-preview`
Preview CSV import with auto-detected columns.

### POST `/reconciliation/{id}/import-confirm`
Confirm and persist imported lines.

### POST `/reconciliation/{id}/auto-match`
Auto-match statement lines to GL entries.

**[AUDIT FIX]**: Add branch_id filter to matching query to prevent cross-branch matches (R-002 related).

### POST `/reconciliation/{id}/finalize`
Finalize reconciliation.

**[AUDIT FIX]**: Read `reconciliation_tolerance` from company_settings (R-006). Compare `abs(difference) <= tolerance`.

---

## 8. Cash Flow Forecasting

### POST `/finance/cashflow/generate`
Generate forecast from open AR/AP + recurring templates.

### GET `/finance/cashflow`
List forecasts.

### GET `/finance/cashflow/{id}`
Forecast detail with lines.

---

## Error Response Format

All error responses follow:
```json
{
  "detail": "User-facing message in Arabic/English"
}
```

**[AUDIT FIX]**: Per constitution §IV, no raw Python exceptions in responses. All internal errors return generic message and log full traceback via `logger.exception()`.
