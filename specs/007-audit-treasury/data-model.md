# Data Model: audit-treasury — الخزينة والبنوك

**Date**: 2026-04-14  
**Phase**: 1 — Design & Contracts

## Entity Overview

```
┌─────────────────────┐     1:1      ┌──────────────┐
│  TreasuryAccount    │─────────────→│  GL Account   │
│  (treasury_accounts)│              │  (accounts)   │
└────────┬────────────┘              └──────────────┘
         │ 1:N
         ▼
┌─────────────────────┐
│ TreasuryTransaction │
│(treasury_transactions)│
└─────────────────────┘

┌─────────────────────┐     N:1      ┌──────────────┐
│  CheckReceivable    │─────────────→│  Party       │
│(checks_receivable)  │              │  (parties)   │
└────────┬────────────┘              └──────────────┘
         │ 1:N (journal_entries FK)
         ▼
┌─────────────────────┐
│  JournalEntry       │
│(journal_entries)    │
└─────────────────────┘

┌─────────────────────┐     1:N      ┌───────────────────┐
│  BankReconciliation │─────────────→│ BankStatementLine │
│(bank_reconciliations)│             │(bank_statement_   │
└─────────────────────┘              │ lines)            │
                                     └───────────────────┘
```

## Entities (Current State + Audit Changes)

### 1. TreasuryAccount (`treasury_accounts`)

| Column | Type | Nullable | Default | Change |
|--------|------|----------|---------|--------|
| id | SERIAL PK | NO | auto | — |
| name | VARCHAR(255) | NO | — | — |
| name_en | VARCHAR(255) | YES | NULL | — |
| account_type | VARCHAR(50) | NO | — | — (values: 'cash', 'bank') |
| currency | VARCHAR(3) | YES | NULL | — |
| current_balance | NUMERIC(18,4) | YES | 0 | **FIX**: Python model → `Decimal` (R-010) |
| gl_account_id | INT FK→accounts | YES | NULL | — |
| branch_id | INT FK→branches | YES | NULL | — |
| bank_name | VARCHAR(255) | YES | NULL | — |
| account_number | VARCHAR(100) | YES | NULL | — |
| iban | VARCHAR(100) | YES | NULL | — |
| is_active | BOOLEAN | YES | TRUE | — |
| **allow_overdraft** | **BOOLEAN** | **YES** | **NULL** | **NEW** (R-004): NULL=type default |
| created_at | TIMESTAMP | YES | NOW() | — |
| updated_at | TIMESTAMP | YES | NOW() | — |

**State rules**:
- `allow_overdraft = NULL` → cash rejects overdraft, bank allows
- `allow_overdraft = TRUE` → always allows overdraft
- `allow_overdraft = FALSE` → always rejects overdraft

### 2. TreasuryTransaction (`treasury_transactions`)

| Column | Type | Nullable | Default | Change |
|--------|------|----------|---------|--------|
| id | SERIAL PK | NO | auto | — |
| transaction_number | VARCHAR(50) UNIQUE | NO | — | — |
| transaction_date | DATE | NO | — | — |
| transaction_type | VARCHAR(50) | NO | — | — (expense, transfer, receipt, check_collection, etc.) |
| amount | NUMERIC(18,4) | NO | — | — |
| treasury_id | INT FK | YES | NULL | — |
| target_account_id | INT FK→accounts | YES | NULL | — |
| target_treasury_id | INT FK | YES | NULL | — |
| reference_number | VARCHAR(100) | YES | NULL | — |
| description | TEXT | YES | NULL | — |
| status | VARCHAR(30) | YES | 'posted' | — |
| **exchange_rate** | **NUMERIC(18,6)** | **YES** | **1.0** | **NEW** (R-009) |
| **currency** | **VARCHAR(3)** | **YES** | **NULL** | **NEW**: store transaction currency |
| created_by | INT FK | YES | NULL | — |
| branch_id | INT FK | YES | NULL | — |
| created_at | TIMESTAMP | YES | NOW() | — |

### 3. CheckReceivable (`checks_receivable`)

| Column | Type | Nullable | Default | Change |
|--------|------|----------|---------|--------|
| id | SERIAL PK | NO | auto | — |
| check_number | VARCHAR(50) | NO | — | — |
| drawer_name | VARCHAR(255) | YES | NULL | — |
| bank_name | VARCHAR(255) | YES | NULL | — |
| branch_name | VARCHAR(255) | YES | NULL | — |
| amount | NUMERIC(18,4) | NO | — | — |
| currency | VARCHAR(3) | YES | 'SAR' | — |
| **exchange_rate** | **NUMERIC(18,6)** | **YES** | **1.0** | **NEW** (R-009) |
| issue_date | DATE | YES | NULL | — |
| due_date | DATE | YES | NULL | — |
| collection_date | DATE | YES | NULL | — |
| bounce_date | DATE | YES | NULL | — |
| **re_presentation_date** | **DATE** | **YES** | **NULL** | **NEW** (R-003) |
| **re_presentation_count** | **INT** | **YES** | **0** | **NEW** (R-003) |
| party_id | INT FK→parties | YES | NULL | — |
| treasury_account_id | INT FK | YES | NULL | — |
| receipt_id | INT | YES | NULL | — |
| journal_entry_id | INT FK | YES | NULL | — |
| collection_journal_id | INT FK | YES | NULL | — |
| bounce_journal_id | INT FK | YES | NULL | — |
| **re_presentation_journal_id** | **INT FK** | **YES** | **NULL** | **NEW** (R-003) |
| status | VARCHAR(30) | NO | 'pending' | — (pending, collected, bounced) |
| bounce_reason | TEXT | YES | NULL | — |
| notes | TEXT | YES | NULL | — |
| branch_id | INT FK | YES | NULL | — |
| created_by | INT FK | YES | NULL | — |
| created_at | TIMESTAMP | YES | NOW() | — |
| updated_at | TIMESTAMP | YES | NOW() | — |

**State machine (updated)**:
```
CREATE (pending)
  ├─→ [collect] → collected (TERMINAL)
  └─→ [bounce] → bounced
        └─→ [represent] → pending (re-presentation; increments re_presentation_count)
              ├─→ [collect] → collected (TERMINAL)
              └─→ [bounce] → bounced (cycle continues)
```

### 4. CheckPayable (`checks_payable`)

Same structure as CheckReceivable with these name differences:
- `beneficiary_name` instead of `drawer_name`
- `clearance_date` instead of `collection_date`
- `clearance_journal_id` instead of `collection_journal_id`
- `payment_voucher_id` (INT, nullable)
- Status values: `issued`, `cleared`, `bounced`

**New columns** (same as receivable): `exchange_rate`, `re_presentation_date`, `re_presentation_count`, `re_presentation_journal_id`

**State machine (updated)**:
```
CREATE (issued)
  ├─→ [clear] → cleared (TERMINAL)
  └─→ [bounce] → bounced
        └─→ [represent] → issued (re-presentation)
              ├─→ [clear] → cleared (TERMINAL)
              └─→ [bounce] → bounced (cycle continues)
```

### 5. NoteReceivable (`notes_receivable`)

| Column | Type | Nullable | Default | Change |
|--------|------|----------|---------|--------|
| id | SERIAL PK | NO | auto | — |
| note_number | VARCHAR(50) | NO | — | — |
| drawer_name | VARCHAR(255) | YES | NULL | — |
| amount | NUMERIC(18,4) | NO | — | — |
| currency | VARCHAR(3) | YES | 'SAR' | — |
| **exchange_rate** | **NUMERIC(18,6)** | **YES** | **1.0** | **NEW** |
| issue_date | DATE | YES | NULL | — |
| due_date | DATE | YES | NULL | — |
| maturity_date | DATE | YES | NULL | — |
| collection_date | DATE | YES | NULL | — |
| protest_date | DATE | YES | NULL | — |
| party_id | INT FK | YES | NULL | — |
| treasury_account_id | INT FK | YES | NULL | — |
| journal_entry_id | INT FK | YES | NULL | — |
| collection_journal_id | INT FK | YES | NULL | — |
| protest_journal_id | INT FK | YES | NULL | — |
| status | VARCHAR(30) | NO | 'pending' | — (pending, collected, protested) |
| protest_reason | TEXT | YES | NULL | — |
| notes | TEXT | YES | NULL | — |
| branch_id | INT FK | YES | NULL | — |
| created_by | INT FK | YES | NULL | — |
| created_at | TIMESTAMP | YES | NOW() | — |
| updated_at | TIMESTAMP | YES | NOW() | — |

**State machine (unchanged — protest is TERMINAL)**:
```
CREATE (pending)
  ├─→ [collect] → collected (TERMINAL)
  └─→ [protest] → protested (TERMINAL — new note required for renegotiation)
```

### 6. NotePayable (`notes_payable`)

Same structure as NoteReceivable with:
- `beneficiary_name` instead of `drawer_name`
- `payment_date` instead of `collection_date`
- `payment_journal_id` instead of `collection_journal_id`
- Status values: `issued`, `paid`, `protested`

**State machine**: `created (issued) → paid (TERMINAL) OR protested (TERMINAL)`

### 7. BankReconciliation (`bank_reconciliations`)

No schema changes needed. Existing columns are sufficient.

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | — |
| treasury_account_id | INT FK | — |
| statement_date | DATE | — |
| start_balance | NUMERIC(18,4) | — |
| end_balance | NUMERIC(18,4) | — |
| status | VARCHAR(20) | draft, approved |
| notes | TEXT | — |
| created_by | INT FK | — |
| branch_id | INT FK | — |

### 8. BankStatementLine (`bank_statement_lines`)

No schema changes needed.

### 9. Company Settings (key-value)

| Key | Value Type | Default | Change |
|-----|------------|---------|--------|
| **reconciliation_tolerance** | **NUMERIC** | **1.00** | **NEW** (R-006) |

## Schema Migration Summary

New columns to add via migration:

```sql
-- treasury_accounts
ALTER TABLE treasury_accounts ADD COLUMN IF NOT EXISTS allow_overdraft BOOLEAN DEFAULT NULL;

-- treasury_transactions
ALTER TABLE treasury_transactions ADD COLUMN IF NOT EXISTS exchange_rate NUMERIC(18,6) DEFAULT 1.0;
ALTER TABLE treasury_transactions ADD COLUMN IF NOT EXISTS currency VARCHAR(3) DEFAULT NULL;

-- checks_receivable
ALTER TABLE checks_receivable ADD COLUMN IF NOT EXISTS exchange_rate NUMERIC(18,6) DEFAULT 1.0;
ALTER TABLE checks_receivable ADD COLUMN IF NOT EXISTS re_presentation_date DATE DEFAULT NULL;
ALTER TABLE checks_receivable ADD COLUMN IF NOT EXISTS re_presentation_count INT DEFAULT 0;
ALTER TABLE checks_receivable ADD COLUMN IF NOT EXISTS re_presentation_journal_id INT DEFAULT NULL;

-- checks_payable
ALTER TABLE checks_payable ADD COLUMN IF NOT EXISTS exchange_rate NUMERIC(18,6) DEFAULT 1.0;
ALTER TABLE checks_payable ADD COLUMN IF NOT EXISTS re_presentation_date DATE DEFAULT NULL;
ALTER TABLE checks_payable ADD COLUMN IF NOT EXISTS re_presentation_count INT DEFAULT 0;
ALTER TABLE checks_payable ADD COLUMN IF NOT EXISTS re_presentation_journal_id INT DEFAULT NULL;

-- notes_receivable
ALTER TABLE notes_receivable ADD COLUMN IF NOT EXISTS exchange_rate NUMERIC(18,6) DEFAULT 1.0;

-- notes_payable
ALTER TABLE notes_payable ADD COLUMN IF NOT EXISTS exchange_rate NUMERIC(18,6) DEFAULT 1.0;
```

## Validation Rules

| Entity | Field | Rule |
|--------|-------|------|
| TreasuryAccount | name | Required, non-empty |
| TreasuryAccount | account_type | Must be 'cash' or 'bank' |
| TreasuryAccount | currency | Must be valid ISO 4217 code |
| TreasuryAccount | iban | If provided, basic length check (≤34 chars) |
| CheckReceivable | check_number | Required; duplicate warning per branch |
| CheckReceivable | amount | > 0, NUMERIC(18,4) |
| CheckReceivable | status transitions | pending→collected, pending→bounced, bounced→pending |
| NoteReceivable | status transitions | pending→collected, pending→protested (TERMINAL) |
| BankReconciliation | finalize | abs(difference) ≤ reconciliation_tolerance |
| TreasuryTransaction | amount | > 0, NUMERIC(18,4) |
| TreasuryTransaction | overdraft | Cash: reject if balance < amount (unless allow_overdraft=True); Bank: allow (unless allow_overdraft=False) |
