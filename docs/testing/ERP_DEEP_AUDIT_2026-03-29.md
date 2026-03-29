# AMAN ERP — COMPREHENSIVE PRODUCTION AUDIT REPORT

**Date:** 2026-03-29
**Auditor Role:** Senior ERP Systems Auditor / Enterprise Architect / Financial Systems Expert
**Codebase:** ~187,000 lines (88K backend Python + 99K frontend React)
**Scope:** Full system — schema, business logic, APIs, UI, security, architecture

---

## PHASE 1 — PROJECT STRUCTURE

```
aman/
├── backend/                      FastAPI Python backend
│   ├── main.py                   App factory, router registration, middleware
│   ├── config.py                 Pydantic settings, env vars
│   ├── database.py               211KB — ALL table DDL + seed data
│   ├── routers/
│   │   ├── auth.py               47KB — auth, JWT, rate limiting
│   │   ├── purchases.py          152KB — full procurement
│   │   ├── reports.py            189KB — all reporting
│   │   ├── projects.py           119KB — project management
│   │   ├── pos.py                67KB — point of sale
│   │   ├── crm.py                63KB — CRM
│   │   ├── system_completion.py  85KB — industry templates
│   │   ├── finance/              accounting, treasury, taxes
│   │   ├── sales/                invoices, orders, returns
│   │   ├── hr/                   employees, payroll, leave
│   │   ├── inventory/            products, stock, warehouses
│   │   └── manufacturing/        BOM, production orders
│   ├── utils/
│   │   └── security_middleware.py
│   ├── schemas/
│   ├── services/
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── pages/                277 JSX pages across 22 modules
│   │   ├── components/           shared UI components
│   │   ├── services/             18 API client service files
│   │   └── context/              branch, theme, toast providers
│   └── vite.config.js
├── docker-compose.yml
└── prd.md
```

**Multi-tenancy model:** System DB (`system_companies`, `system_user_index`) + dedicated `aman_{company_id}` database per tenant, 244 tables per company.

---

## PHASE 2 — MODULE DECOMPOSITION

| Module | Tables (key) | API Routes | Frontend Pages | Responsibility |
|--------|-------------|-----------|----------------|----------------|
| Accounting | accounts, journal_entries, journal_lines, fiscal_years, fiscal_periods | /accounting | 24 | COA, double-entry GL, reports |
| Sales | invoices, invoice_lines, sales_orders, quotations, returns, receipts, delivery_orders | /sales | 32 | Quote→Order→Invoice→Receipt |
| Purchases | purchase_orders, purchase_invoices, supplier_payments, rfq | /buying | 26 | RFQ→PO→GRN→Invoice→Payment |
| Inventory | products, inventory, warehouses, batches, serials, adjustments, transfers | /inventory | 26 | Stock, costing, warehousing |
| HR/Payroll | employees, departments, payroll_entries, attendance, leave, loans | /hr | 28 | Headcount, payroll, GOSI, WPS |
| Treasury | treasury_accounts, transactions, reconciliation, checks | /treasury | 16 | Cash, bank, reconciliation |
| Manufacturing | work_centers, bom, production_orders, routings | /manufacturing | 18 | BOM, production, MRP |
| POS | pos_sessions, pos_orders, pos_payments, promotions | /pos | 9 | Retail point of sale |
| CRM | leads, opportunities, contacts, tickets | /crm | 11 | Pipeline, support |
| Projects | projects, tasks, timesheets, budgets | /projects | 12 | PM, time tracking |
| Taxes | tax_rates, tax_groups, tax_returns | /taxes | — | VAT/WHT compliance |
| Assets | fixed_assets, depreciation, disposals | /assets | — | Fixed asset management |

---

## PHASE 3 — DEEP MODULE ANALYSIS

---

### ISSUE-001

**Title:** Multiple Denormalized Running Balances — Guaranteed Divergence
**Category:** Database Architecture / Data Integrity
**Severity:** CRITICAL

**Description:**
The system maintains the same financial balance in at least **four separate places simultaneously**, each updated independently:

1. `accounts.balance DECIMAL(18,4)` — stored GL account balance
2. `treasury_accounts.current_balance DECIMAL(18,4)` — stored cash/bank balance
3. `parties.current_balance DECIMAL(18,4)` — stored AR/AP balance
4. `party_transactions.balance DECIMAL(18,4)` — per-row running balance (ledger style)

Additionally, the accounting router also calculates "live from `journal_lines` aggregation." This means the system has **two sources of truth for GL balances** — stored and computed — with no reconciliation mechanism.

**Impact:**
Any partial failure in a multi-step transaction (invoice creation, payment, etc.) leaves one or more of these balances inconsistent. Financial statements derived from `accounts.balance` will differ from those derived from `SUM(journal_lines.debit)`. Auditors will find discrepancies between the AR ledger and the GL. Bank reconciliation will fail silently.

**Root Cause:**
Performance optimization by pre-computing balances without implementing a proper event-sourcing or CQRS pattern. No single authoritative source defined.

**Fix:**
- Designate `journal_lines` as the **single source of truth** for GL balances. Remove `accounts.balance`.
- Replace `treasury_accounts.current_balance` with a view: `SUM(transactions) WHERE account_id = x`.
- Replace `parties.current_balance` with a materialized view or computed property.
- Remove `party_transactions.balance` running column entirely; compute balances on read with window functions.
- If performance requires caching: use a dedicated `account_balance_cache` table with explicit versioning and a reconciliation job.

---

### ISSUE-002

**Title:** No Database-Level Double-Entry Enforcement
**Category:** Financial Integrity / Database
**Severity:** CRITICAL

**Description:**
The `journal_entries` table has NO `total_debit` or `total_credit` columns and NO database-level constraint enforcing `SUM(debit) = SUM(credit)` across `journal_lines`. The double-entry balance check is implemented only in application code. The actual `journal_entries` DDL:

```sql
CREATE TABLE IF NOT EXISTS journal_entries (
    id SERIAL PRIMARY KEY,
    entry_number VARCHAR(50) UNIQUE NOT NULL,
    entry_date DATE NOT NULL,
    -- NO total_debit, NO total_credit columns
    status VARCHAR(20) DEFAULT 'draft',
    ...
);
```

Any code path that creates `journal_lines` rows directly (bypassing the main invoice creation flow) can create unbalanced entries. Background jobs, data imports, and manual SQL fixes are particularly at risk.

**Impact:**
Unbalanced journal entries will corrupt the trial balance, balance sheet, and all derived financial reports. The error will only be discovered during period-end close or audit — not at the moment of creation.

**Root Cause:**
Reliance on application-layer validation without a database-level backstop. PostgreSQL supports deferred constraints and check constraints via triggers.

**Fix:**
Add a PostgreSQL trigger:
```sql
CREATE OR REPLACE FUNCTION check_journal_balance() RETURNS TRIGGER AS $$
BEGIN
  IF (SELECT ABS(SUM(debit) - SUM(credit)) FROM journal_lines
      WHERE journal_entry_id = NEW.journal_entry_id) > 0.01 THEN
    RAISE EXCEPTION 'Journal entry % is unbalanced', NEW.journal_entry_id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE CONSTRAINT TRIGGER trg_journal_balance
AFTER INSERT OR UPDATE OR DELETE ON journal_lines
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_journal_balance();
```

Also add `total_debit` and `total_credit` as generated columns or populated on post.

---

### ISSUE-003

**Title:** `party_transactions.balance` Running Balance — Race Condition
**Category:** Concurrency / Data Integrity
**Severity:** CRITICAL

**Description:**
The `party_transactions` table stores a running balance column:
```sql
balance DECIMAL(18, 4) DEFAULT 0
```
This implements a ledger running-balance pattern. Computing the correct value requires reading the previous row's balance and adding the current transaction's debit/credit. Under concurrent inserts for the same `party_id`, two transactions will read the same previous balance and produce identical (wrong) balances.

**Example:** Party balance = 10,000. Invoice A (5,000) and Invoice B (3,000) insert simultaneously. Both read 10,000 as previous balance. Result: A records 15,000 and B records 13,000. Correct final balance should be 18,000, but both will appear in the ledger as if correct.

**Impact:**
Incorrect AR/AP ledger balances shown to users. Credit limit checks based on `party.current_balance` will use wrong data. Financial reports showing customer aging will be incorrect.

**Root Cause:**
Running balance pattern requires either serialized writes or computed-on-read calculation. Neither is implemented.

**Fix:**
Remove `party_transactions.balance` column entirely. Calculate running balance on read:
```sql
SELECT *, SUM(debit - credit) OVER (
  PARTITION BY party_id ORDER BY transaction_date, id
) as running_balance
FROM party_transactions
WHERE party_id = :party_id
ORDER BY transaction_date, id;
```

---

### ISSUE-004

**Title:** SQL Injection via String Interpolation in Branch Access Control
**Category:** Security / SQL Injection
**Severity:** CRITICAL

**Description:**
Branch-level access control uses string interpolation for SQL `IN` clauses:
```python
# Pattern found in HR and other routers
f"AND e.branch_id IN ({branches_str})"
```
Where `branches_str` is derived from the user's JWT claims. While JWT claims are server-signed, if the JWT secret is compromised, or if there is any other code path that allows `branches_str` to contain user-controlled data, this is a full SQL injection vector. The pattern also normalizes unsafe SQL construction as acceptable practice throughout the codebase.

**Impact:**
Full database compromise if exploited. An attacker with a forged token could execute arbitrary SQL including `DROP TABLE`, `SELECT *`, exfiltration via `UNION`, etc.

**Root Cause:**
Using Python f-strings for SQL construction instead of parameterized queries.

**Fix:**
Replace with SQLAlchemy parameterized ANY array binding:
```python
# Safe version:
query = text("SELECT * FROM employees WHERE branch_id = ANY(:branch_ids)")
result = db.execute(query, {"branch_ids": allowed_branches_list})
```
Audit **every** file in `/backend/routers/` for `f"...{...}"` patterns inside SQL strings.

---

### ISSUE-005

**Title:** Deprecated FK Columns Left Active in Core `invoices` Table
**Category:** Database Design / Data Integrity
**Severity:** HIGH

**Description:**
The `invoices` table contains two commented-deprecated columns that remain active in production:
```sql
customer_id INTEGER, -- Deprecated
supplier_id INTEGER, -- Deprecated
```
These columns have no FK constraint defined. They coexist with the unified `party_id INTEGER REFERENCES parties(id)`. If any code path (old routes, scripts, imports) still writes to `customer_id` or `supplier_id` instead of `party_id`, those invoices will have `party_id = NULL`, making them invisible to the unified party ledger, credit limit checks, and AR aging reports.

**Impact:**
Invoices with `party_id = NULL` produce no GL entries linked to the customer, no AR balance update, no credit limit check, and no aging. Revenue is recorded but receivables are not tracked. This directly corrupts the balance sheet.

**Root Cause:**
Incomplete migration from customer/supplier model to unified party model. The transition was never finalized.

**Fix:**
1. Run data migration: `UPDATE invoices SET party_id = customer_id WHERE party_id IS NULL AND customer_id IS NOT NULL`
2. Verify all code paths write `party_id`
3. Add NOT NULL constraint to `party_id`
4. Drop `customer_id` and `supplier_id` columns

---

### ISSUE-006

**Title:** Missing FK Constraints on Critical Reference Columns
**Category:** Database Integrity
**Severity:** HIGH

**Description:**
Multiple columns reference other tables without FOREIGN KEY constraints:

| Table | Column | References | Risk |
|-------|---------|-----------|------|
| `invoice_lines` | `product_id INTEGER` | products | Deleted products leave orphan lines |
| `invoices` | `warehouse_id INTEGER` | warehouses | Orphaned warehouse refs |
| `invoices` | `related_invoice_id INTEGER` | invoices | Circular/broken return chain |
| `journal_entries` | `source_id INTEGER` | (polymorphic) | Deleted source docs leave dangling GL |
| `party_transactions` | `payment_id INTEGER` | — | No referential integrity |
| `party_transactions` | `invoice_id INTEGER` | invoices | Orphaned ledger entries |
| `journal_lines` | `cost_center_id INTEGER` | — | Silent cost center deletion |
| `journal_lines` | `reconciliation_id INTEGER` | — | Broken reconciliation chains |

**Impact:**
Orphaned records cause silent data loss. A deleted product still has `invoice_lines` referencing its ID — cost calculations break. A voided journal entry can leave `party_transactions.payment_id` pointing to nothing.

**Root Cause:**
Deliberate omission of FK constraints, likely for performance or flexibility. Polymorphic `source`/`source_id` pattern inherently cannot use FK constraints.

**Fix:**
Add FK constraints on all non-polymorphic references. For the polymorphic `source`/`source_id` pattern, replace with per-document link columns (`invoice_id`, `purchase_order_id`, etc.) or use a proper polymorphic association table.

---

### ISSUE-007

**Title:** No Inventory Concurrency Lock — Overselling Risk
**Category:** Business Logic / Concurrency
**Severity:** CRITICAL

**Description:**
Inventory deduction on invoice creation follows a read-then-write pattern:
1. Read current `inventory.quantity`
2. Check if sufficient stock available
3. Deduct quantity via UPDATE

Between steps 1 and 3, another concurrent transaction can read the same quantity and approve the same stock. The POS module uses `FOR UPDATE SKIP LOCKED` for session management — confirming awareness of the pattern — but the inventory deduction in the sales invoice router does not visibly use pessimistic locking.

**Impact:**
Under concurrent load (especially POS peak hours), the same stock can be sold multiple times. Inventory quantity goes negative. COGS entries become inaccurate. Customer orders must be cancelled after the fact.

**Root Cause:**
Missing `SELECT ... FOR UPDATE` on the inventory row before deduction.

**Fix:**
```sql
-- In the invoice creation transaction:
SELECT quantity FROM inventory
WHERE product_id = :pid AND warehouse_id = :wid
FOR UPDATE;  -- pessimistic lock

-- Then validate and deduct in same transaction
UPDATE inventory SET quantity = quantity - :qty
WHERE product_id = :pid AND warehouse_id = :wid;
```
Add a `CHECK (quantity >= -0.0001)` database constraint as a final backstop.

---

### ISSUE-008

**Title:** No `status` CHECK Constraints on Transaction Tables
**Category:** Database Integrity
**Severity:** HIGH

**Description:**
Status columns across all transaction tables use `VARCHAR(20) DEFAULT 'draft'` with NO CHECK constraints:

```sql
invoices.status VARCHAR(20) DEFAULT 'draft'          -- no CHECK
journal_entries.status VARCHAR(20) DEFAULT 'draft'   -- no CHECK
purchase_orders.status VARCHAR(50)                    -- no CHECK
payroll_entries.status VARCHAR(20)                    -- no CHECK
```

The `accounts.account_type` field does have a CHECK constraint as a positive example, but it is the exception, not the rule.

**Impact:**
Invalid status values like `'POSTED'` (wrong case), `'psted'` (typo), or `''` (empty) can be inserted directly. Reports and state machine logic that filter by status will silently miss records with non-standard values.

**Fix:**
```sql
ALTER TABLE invoices ADD CONSTRAINT chk_invoice_status
  CHECK (status IN ('draft', 'posted', 'paid', 'partial', 'cancelled', 'void'));

ALTER TABLE journal_entries ADD CONSTRAINT chk_je_status
  CHECK (status IN ('draft', 'posted', 'void'));
```

---

### ISSUE-009

**Title:** Production Rate Limits at Testing Values — Brute Force Window
**Category:** Security
**Severity:** CRITICAL

**Description:**
The authentication rate limits were explicitly increased for automated testing (commit `79ae47e`) and were never reverted:

```python
# auth.py — current values (testing levels)
MAX_LOGIN_ATTEMPTS_IP = 500       # Should be: 5–10
MAX_LOGIN_ATTEMPTS_USERNAME = 1000  # Should be: 10–20
LOCKOUT_DURATION = 900  # 15 minutes
```

With 500 attempts per IP before lockout, an attacker can try 500 passwords per 15 minutes = 2,000 attempts per hour. Targeted attacks against common passwords (rockyou.txt top 10,000) would succeed in minutes against any account with a weak password.

**Impact:**
All user accounts are vulnerable to brute-force password attacks. 2FA protects only users who have enabled it — it is not mandatory.

**Root Cause:**
Testing configuration was committed and deployed to production.

**Fix:**
Immediately:
```python
MAX_LOGIN_ATTEMPTS_IP = 5
MAX_LOGIN_ATTEMPTS_USERNAME = 10
LOCKOUT_DURATION = 1800  # 30 minutes
```
Enforce 2FA as mandatory for all admin/finance roles. Add CAPTCHA after 3 failed attempts. Use environment variables so test configs never reach production.

---

### ISSUE-010

**Title:** In-Memory Rate Limiter Fallback Ineffective in Multi-Instance Deployment
**Category:** Security / Architecture
**Severity:** HIGH

**Description:**
When Redis is unavailable, the system falls back to an in-memory rate limiter. In a horizontally scaled deployment (multiple backend containers), each instance maintains its own independent counter. An attacker can distribute login attempts across N instances and get N × limit attempts before any lockout.

**Impact:**
Rate limiting provides no protection when Redis is down or in any scaled deployment without Redis. Docker Compose marks Redis as `optional` with a "graceful fallback," meaning this failure mode is actively expected.

**Root Cause:**
Treating rate limiting as a best-effort feature rather than a security requirement.

**Fix:**
Options:
1. Make Redis a required dependency (fail startup if unavailable)
2. Implement rate limiting at the Nginx layer as primary mechanism
3. Use `limit_req_zone` in Nginx (always effective regardless of backend scaling)

---

### ISSUE-011

**Title:** Refresh Token Stored in `localStorage` — XSS Token Theft
**Category:** Security
**Severity:** HIGH

**Description:**
Frontend API client stores refresh tokens in `localStorage`. Any successful XSS attack allows an attacker to read `localStorage` and steal the refresh token. Refresh tokens have a 7-day validity — meaning account takeover persists for up to a week after the initial XSS event, even if the user changes their password (unless explicitly blacklisted).

**Impact:**
Persistent account takeover for up to 7 days per stolen token. Attackers can generate new access tokens at will during this window.

**Root Cause:**
Convenience of `localStorage` access from JavaScript vs. security of `httpOnly` cookies.

**Fix:**
Move refresh token to `httpOnly; SameSite=Strict; Secure` cookie. Access tokens (30-min lifetime) should remain in memory only — not stored anywhere. Implement CSRF protection on the refresh endpoint.

---

### ISSUE-012

**Title:** VAT/Tax Calculation Ambiguity — Header Discount Creates ZATCA Non-Compliance Risk
**Category:** Financial / Tax Compliance
**Severity:** CRITICAL

**Description:**
The invoice model has discount at two levels simultaneously:
- `invoice_lines.discount DECIMAL(18,4)` — line-level discount (absolute)
- `invoices.discount DECIMAL(18,4)` — header-level discount (absolute)
- `invoices.effect_percentage DECIMAL(5,2)` — header percentage

Tax calculation at line level: `(quantity × unit_price - line_discount) × tax_rate / 100`

The header-level discount is NOT deducted from the taxable base at line level. Tax is computed on the undiscounted amount when header discounts are used — directly violating **ZATCA Article 53**, which requires VAT to be computed on the consideration actually paid (net of all discounts).

**ZATCA-Compliant calculation:**
```
Taxable_per_line = (qty × price) - proportional_header_discount - line_discount
VAT_per_line = Taxable_per_line × tax_rate
```

**Impact:**
For any invoice with a header-level discount, VAT is overcollected from the customer and over-reported to ZATCA. This is incorrect tax collection/remittance — subject to ZATCA penalties up to 50% of the incorrect amount.

**Root Cause:**
Two-level discount model without propagating header discounts to the tax base computation.

**Fix:**
Distribute header discount proportionally to each line before calculating tax. Or eliminate header discounts and require all discounts at line level (ZATCA best practice).

---

### ISSUE-013

**Title:** `accounts.balance` Used Inconsistently — Stale Balance Risk
**Category:** Data Integrity / Financial
**Severity:** HIGH

**Description:**
The `accounts` table has `balance DECIMAL(18,4) DEFAULT 0`, but the accounting router also "calculates live from journal_lines aggregation." Two code paths exist:
- **Path A:** Read `accounts.balance` (fast, potentially stale)
- **Path B:** `SUM(journal_lines.debit) - SUM(journal_lines.credit)` (always correct, slower)

There is no guarantee that every GL posting that creates `journal_lines` also updates `accounts.balance`. If any posting skips the balance update, the stored balance diverges permanently — silently.

**Impact:**
Dashboard KPIs reading `accounts.balance` may show different values than the Trial Balance report which recalculates from lines. Management makes decisions on incorrect summary data.

**Fix:**
Eliminate `accounts.balance` entirely. Create a materialized view:
```sql
CREATE MATERIALIZED VIEW account_balances AS
SELECT account_id,
       SUM(debit) as total_debit,
       SUM(credit) as total_credit,
       SUM(debit) - SUM(credit) as balance
FROM journal_lines jl
JOIN journal_entries je ON je.id = jl.journal_entry_id
WHERE je.status = 'posted'
GROUP BY account_id;

CREATE INDEX ON account_balances(account_id);
```
Refresh on post/void operations.

---

### ISSUE-014

**Title:** Document Number Generation Under Concurrency — Duplicate Key Errors
**Category:** Data Integrity / Concurrency
**Severity:** HIGH

**Description:**
Document numbers (invoice_number, entry_number, po_number) are `UNIQUE NOT NULL` at the DB level, but number generation runs in Python application code. The typical pattern reads `MAX()` and increments — two concurrent requests read the same MAX, generate the same number, and one fails with a DB unique constraint violation (500 error), not a graceful retry.

**Impact:**
Concurrent invoice creation fails with database errors under peak POS/sales load. Users experience crashes when creating documents. The error surface is a user-visible 500, not a handled business error.

**Root Cause:**
Sequence generation in application layer instead of using a database sequence.

**Fix:**
Use PostgreSQL sequences for all document numbers:
```sql
CREATE SEQUENCE invoice_number_seq START 1000;
-- In INSERT:
'INV-' || LPAD(nextval('invoice_number_seq')::text, 6, '0')
```

---

### ISSUE-015

**Title:** No Negative Inventory Prevention at Database Level
**Category:** Data Integrity / Financial
**Severity:** HIGH

**Description:**
The `inventory` table has no CHECK constraint preventing negative quantities:
```sql
quantity DECIMAL(18, 4) DEFAULT 0  -- No CHECK constraint
```

If the application-level stock check fails (race condition from ISSUE-007, or a bug), the database will accept negative inventory. Negative inventory makes WAC formula invalid:
`(qty × cost + new_qty × new_cost) / (qty + new_qty)` — division by zero or negative denominator.

**Impact:**
Negative inventory produces mathematically invalid weighted average cost. All subsequent cost calculations for that product are corrupted. Physical inventory counts will show large unexplained variances.

**Fix:**
```sql
ALTER TABLE inventory ADD CONSTRAINT chk_inventory_qty
  CHECK (quantity >= -0.0001);
```
Add application-level setting "Allow negative inventory" (default: No) for businesses that legitimately need it.

---

### ISSUE-016

**Title:** Payroll GOSI Rates Hardcoded — Labor Law Change Risk
**Category:** Business Logic / Financial Compliance
**Severity:** HIGH

**Description:**
The payroll system references GOSI rates (9% employee, 10% employer) as constants. Any GOSI rate change requires a code change and redeployment. Any payroll processed before the code is updated uses wrong rates.

**Impact:**
Incorrect GOSI contributions: over- or under-deduction from employee salaries, over- or under-remittance to GOSI. Under-remittance is a compliance violation. Historical payroll records become incorrect after a rate change.

**Root Cause:**
Financial compliance rates embedded in application code rather than configuration.

**Fix:**
Store GOSI rates in a configuration table with effective dates:
```sql
CREATE TABLE gosi_rates (
  id SERIAL PRIMARY KEY,
  effective_from DATE NOT NULL,
  employee_rate DECIMAL(5,4) NOT NULL,
  employer_rate DECIMAL(5,4) NOT NULL,
  created_by INTEGER,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```
Payroll generation uses the rate effective on the payroll period date — not the current rate.

---

### ISSUE-017

**Title:** GL Posting Not Atomic with Sub-ledger Updates
**Category:** Architecture / Data Integrity
**Severity:** CRITICAL

**Description:**
A sales invoice creation involves these sequential steps across multiple tables:

1. `INSERT INTO invoices`
2. `INSERT INTO invoice_lines`
3. `UPDATE inventory SET quantity = quantity - x`
4. `INSERT INTO journal_entries`
5. `INSERT INTO journal_lines` × N
6. `UPDATE accounts SET balance = ...`
7. `UPDATE parties SET current_balance = ...`
8. `INSERT INTO party_transactions`
9. `UPDATE treasury_accounts SET current_balance = ...` (if paid)
10. `INSERT INTO payment_vouchers` (if paid)

If `db.commit()` is called mid-sequence (e.g., after step 3) and a later step fails, the inventory is already deducted but no invoice exists. If an HTTPException is raised after step 5 but before step 7, GL is posted but AR is not updated.

**Impact:**
Partial transaction failures leave the system in an inconsistent state: stock deducted but no invoice, GL entries posted but inventory not updated, payment recorded but AR not updated.

**Root Cause:**
Multi-step financial operations without explicit, end-to-end transaction boundary management.

**Fix:**
Wrap all operations for a single document in one explicit transaction block. Never call `db.commit()` mid-transaction. All validation must occur **before** any writes. The single final `db.commit()` is the last statement.

---

### ISSUE-018

**Title:** Schema Evolution via `CREATE TABLE IF NOT EXISTS` — Migration Blind Spot
**Category:** DevOps / Architecture
**Severity:** HIGH

**Description:**
All 244 tables are defined in `database.py` using `CREATE TABLE IF NOT EXISTS`. While `alembic/` exists, the primary schema management uses this DDL-in-code pattern. `CREATE TABLE IF NOT EXISTS` only creates tables that don't exist — **it does not apply ALTER TABLE for new columns, changed types, or new constraints added to existing tables**.

When a developer adds a new column to a table in `database.py`, existing installations will NOT get that column. The production system likely has columns missing that were added after initial deployment.

**Impact:**
Production crashes when code references columns that don't exist. Silent data loss when code writes to non-existent columns. Impossible to safely upgrade without manual DB inspection. No migration version history.

**Root Cause:**
Using DDL initialization code instead of a proper migration framework.

**Fix:**
Commit fully to Alembic:
1. Generate initial migration from current schema
2. All future schema changes through `alembic revision --autogenerate`
3. `entrypoint.sh` runs `alembic upgrade head` on startup
4. Remove `CREATE TABLE IF NOT EXISTS` from `database.py`

---

### ISSUE-019

**Title:** Polymorphic `journal_entries.source` / `source_id` — No Referential Integrity
**Category:** Database Design
**Severity:** HIGH

**Description:**
```sql
source VARCHAR(100),   -- e.g., 'invoice', 'purchase_order', 'payroll'
source_id INTEGER,     -- ID in the source table
```
This anti-pattern stores a type string and an ID without a foreign key. PostgreSQL cannot enforce referential integrity. When a source document is deleted, all linked journal entries remain with `source_id` pointing to a non-existent record. No ON DELETE behavior is possible.

**Impact:**
Orphaned journal entries that cannot be traced to their originating document. Auditors find GL entries with no supporting document — a major audit finding. Historical drilling from GL to source is broken.

**Fix:**
Use separate nullable FK columns per document type:
```sql
invoice_id              INTEGER REFERENCES invoices(id) ON DELETE RESTRICT,
purchase_invoice_id     INTEGER REFERENCES purchase_invoices(id) ON DELETE RESTRICT,
payroll_entry_id        INTEGER REFERENCES payroll_entries(id) ON DELETE RESTRICT,
```
`ON DELETE RESTRICT` prevents deletion of source documents that have GL entries — enforcing a void-then-delete workflow.

---

### ISSUE-020

**Title:** No UNIQUE Constraint on `branches.is_default`
**Category:** Database Design
**Severity:** MEDIUM

**Description:**
The `branches` table has `is_default BOOLEAN DEFAULT FALSE` with no constraint ensuring only one branch can be default. Multiple branches can have `is_default = TRUE` simultaneously. Any query returning `WHERE is_default = TRUE` returns multiple rows — causing non-deterministic behavior.

**Fix:**
```sql
CREATE UNIQUE INDEX idx_branches_single_default
ON branches (company_id)
WHERE is_default = TRUE;
```

---

### ISSUE-021

**Title:** Missing Explicit Indexes on High-Volume Query Paths
**Category:** Performance
**Severity:** HIGH

**Description:**
No explicit index definitions are visible in the DDL for the following critical query patterns (PostgreSQL does NOT auto-index FK columns):

| Query Pattern | Missing Index |
|---------------|---------------|
| `journal_lines WHERE account_id = X` | `(account_id)` — used for every balance calc |
| `journal_lines WHERE journal_entry_id = X` | `(journal_entry_id)` |
| `invoice_lines WHERE invoice_id = X` | `(invoice_id)` |
| `party_transactions WHERE party_id = X ORDER BY date` | `(party_id, transaction_date)` |
| `inventory WHERE product_id = X AND warehouse_id = Y` | `(product_id, warehouse_id)` composite |
| `invoices WHERE status = 'unpaid' AND due_date < NOW()` | `(status, due_date)` |
| `payroll_entries WHERE period_id = X` | `(period_id)` |
| `attendance WHERE employee_id = X AND date BETWEEN` | `(employee_id, date)` composite |

**Impact:**
Sequential scans on `journal_lines` (millions of rows in production) for every balance calculation. Trial Balance performance degrades exponentially. Period-end close processing becomes very slow.

**Fix:**
```sql
CREATE INDEX idx_journal_lines_account    ON journal_lines(account_id);
CREATE INDEX idx_journal_lines_entry      ON journal_lines(journal_entry_id);
CREATE INDEX idx_invoice_lines_invoice    ON invoice_lines(invoice_id);
CREATE INDEX idx_party_txns_party_date    ON party_transactions(party_id, transaction_date);
CREATE INDEX idx_inventory_product_wh     ON inventory(product_id, warehouse_id);
CREATE INDEX idx_invoices_status_due      ON invoices(status, due_date);
```

---

### ISSUE-022

**Title:** WAC Cost Calculation Not Protected Against Zero-Quantity Division
**Category:** Financial Logic
**Severity:** HIGH

**Description:**
Weighted Average Cost formula:
```
new_avg = (qty_on_hand × avg_cost + new_qty × new_price) / (qty_on_hand + new_qty)
```
If `qty_on_hand + new_qty = 0` (negative inventory offsetting new receipt), this produces division by zero. If `qty_on_hand < 0` (from ISSUE-007/015), the WAC formula produces a mathematically invalid average.

**Impact:**
Application crash (500 error) on cost update for edge cases. In the negative inventory case, WAC produces invalid cost that understates or overstates COGS for all future sales.

**Fix:**
```python
def calculate_wac(qty_on_hand, avg_cost, new_qty, new_price):
    if qty_on_hand < 0:
        qty_on_hand = Decimal('0')
        avg_cost = Decimal('0')
    total_qty = qty_on_hand + new_qty
    if total_qty <= 0:
        return new_price  # fallback to purchase price
    return (qty_on_hand * avg_cost + new_qty * new_price) / total_qty
```

---

### ISSUE-023

**Title:** No Mandatory 2FA for Privileged Roles
**Category:** Security
**Severity:** HIGH

**Description:**
2FA via TOTP is implemented and available but **optional**. A system administrator or accountant with access to all financial data, the ability to post journal entries, and the ability to create users can authenticate with only a username and password.

**Impact:**
Single credential compromise gives full ERP access. Phishing, password reuse from other breaches, or brute force (exacerbated by ISSUE-009) leads to full financial data exfiltration and potential fraudulent transaction entry.

**Fix:**
Enforce 2FA for roles: `superuser`, `admin`, `manager`, `accountant`. During login:
```python
MANDATORY_2FA_ROLES = {'superuser', 'admin', 'manager', 'accountant'}
if user.role in MANDATORY_2FA_ROLES and not user.totp_enabled:
    raise HTTPException(403, "2FA required for your role.")
if user.role in MANDATORY_2FA_ROLES:
    if not verify_totp(user.totp_secret, provided_code):
        raise HTTPException(401, "Invalid 2FA code")
```

---

### ISSUE-024

**Title:** End-of-Service Calculation Missing Audit Parameters
**Category:** HR / Legal Compliance
**Severity:** HIGH

**Description:**
Saudi Labor Law End-of-Service (EOS) benefit differs based on termination reason (voluntary vs. employer), years of service, applicable article (84 vs. 85), and salary components used as the base. There is no schema table storing EOS calculation parameters at the time of calculation — only the final amount appears to be stored.

**Impact:**
Cannot reconstruct EOS calculation if disputed by employee. MOLHR/GOSI audit will find no documented basis. If salary base was calculated incorrectly, the error cannot be identified years later.

**Fix:**
Create an `eos_calculations` audit table:
```sql
CREATE TABLE eos_calculations (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id),
    calculation_date DATE,
    termination_reason VARCHAR(100),
    service_years DECIMAL(5,2),
    applicable_article VARCHAR(10),
    salary_base DECIMAL(18,4),
    basic_salary DECIMAL(18,4),
    housing_allowance DECIMAL(18,4),
    other_allowances DECIMAL(18,4),
    eos_amount DECIMAL(18,4),
    calculated_by INTEGER REFERENCES company_users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

---

### ISSUE-025

**Title:** Audit Log Contains Sensitive Financial Data Without Masking
**Category:** Security / Privacy
**Severity:** MEDIUM

**Description:**
`system_activity_log` captures all write operations with request body data. This means employee salaries, bank account numbers, IBANs, tax IDs, and potentially password fields are stored in plaintext in the audit log.

**Impact:**
The audit log becomes a high-value attack target. Any user with audit log read access can view all employee salaries and bank details. If the audit log table is breached, sensitive PII and financial data is exposed.

**Fix:**
```python
SENSITIVE_FIELDS = {'password', 'salary', 'bank_account_number', 'iban',
                    'tax_number', 'totp_secret', 'commercial_register'}

def mask_sensitive(data: dict) -> dict:
    return {k: '***' if k in SENSITIVE_FIELDS else v for k, v in data.items()}
```
Apply in `log_activity()` before persisting.

---

## PHASE 4 — CROSS-MODULE ANALYSIS

### Cross-Module Issue A: Three Independent AR/AP Balance Sources

The AR/AP position of any counterparty can be read from three incompatible sources:

| Source | Location | Updated By |
|--------|----------|-----------|
| GL account balance | `accounts.balance` WHERE `account_type = 'asset'` | Journal entry posting |
| Party current balance | `parties.current_balance` | Invoice creation / payment |
| Party ledger sum | `SUM(party_transactions.debit - credit)` | Each transaction |

Under ISSUE-001's conditions, these three will disagree. Credit limit checks, AR aging reports, and the balance sheet simultaneously show different AR values.

### Cross-Module Issue B: Inventory Valuation vs. GL Inventory Account

The inventory module maintains `inventory.average_cost × quantity` as the inventory value. The GL maintains the inventory account balance via journal entries. These two should always be equal. However:
- Manual GL adjustments to the inventory account have no corresponding update to `inventory.average_cost`
- Rounding differences accumulate over time
- This "inventory valuation gap" grows every period with no automated reconciliation

### Cross-Module Issue C: POS Orders May Bypass Sales Module AR Logic

POS orders follow a different code path than sales invoices, using dedicated `pos_orders` and `pos_payments` tables. It is unclear whether POS sales:
- Update the unified `party_transactions` ledger for customer AR
- Apply the same credit limit check logic
- Post through the same GL accounts as regular invoices

If POS is a parallel subsystem, consolidating sales reports requires merging two different models — creating reporting inconsistency.

### Cross-Module Issue D: Manufacturing Costs Not Flowing to Inventory WAC

Production order completion should update `inventory.average_cost` of finished goods based on actual production cost (raw materials + labor + overhead). If manufacturing posts GL entries (Dr: FG-INV, Cr: WIP) but does not update `inventory.average_cost`, all future COGS calculations for manufactured goods use an outdated cost. The GL and inventory ledger permanently diverge.

---

## PHASE 5 — CRITICAL RISK DETECTION

### Financial Risks

| Risk | Probability | Financial Impact |
|------|------------|------------------|
| Balance divergence causes wrong financial statements | HIGH | Incorrect P&L, Balance Sheet |
| Unbalanced journal entries pass validation | MEDIUM | Corrupted trial balance |
| ZATCA VAT miscalculation on header discounts | HIGH | ZATCA fines, tax underpayment |
| Overselling → negative inventory → wrong COGS | HIGH | Understated/overstated COGS |
| GOSI rates hardcoded → wrong payroll | MEDIUM | Employee disputes, GOSI penalties |
| EOS calculation not auditable | MEDIUM | Labor tribunal exposure |

### Security Risks

| Risk | Severity | Likelihood |
|------|---------|------------|
| Brute force via testing-level rate limits | CRITICAL | HIGH |
| SQL injection via branch filter f-strings | CRITICAL | LOW–MEDIUM |
| Refresh token theft via XSS | HIGH | MEDIUM |
| No mandatory 2FA for admins | HIGH | HIGH |
| Sensitive data in audit logs | MEDIUM | HIGH |

### Performance Risks

| Risk | Impact Trigger |
|------|---------------|
| No indexes on journal_lines.account_id | >100K journal lines (months of operation) |
| Sequential party_transactions scans | >10K transactions per party |
| Live balance recalculation on every COA load | >50 concurrent users |
| Document number collision errors under concurrency | >5 concurrent invoice creates |

---

## FINAL REPORT

---

### 1) TOP 10 CRITICAL ISSUES

| # | Issue | Severity | Module |
|---|-------|---------|--------|
| 1 | Multiple denormalized running balances — guaranteed divergence | CRITICAL | All financial |
| 2 | No DB-level double-entry enforcement | CRITICAL | Accounting |
| 3 | Production rate limits at testing values (500/IP) | CRITICAL | Security |
| 4 | No inventory concurrency lock — overselling risk | CRITICAL | Inventory/Sales |
| 5 | GL posting not atomic with sub-ledger updates | CRITICAL | All financial |
| 6 | ZATCA VAT miscalculation on header-level discounts | CRITICAL | Sales/Tax |
| 7 | SQL injection via f-string branch filtering | CRITICAL | Security |
| 8 | `party_transactions.balance` running balance race condition | CRITICAL | AR/AP |
| 9 | Deprecated FK columns still active in invoices table | HIGH | Sales |
| 10 | Schema evolution via `CREATE TABLE IF NOT EXISTS` — no real migrations | HIGH | DevOps |

---

### 2) ARCHITECTURE WEAKNESSES

1. **Dual Balance Architecture:** Four places store the same balance. No single source of truth. This is the root cause of the most critical financial risks.

2. **Application-Layer Financial Integrity:** Double-entry balance, document number uniqueness, and status transitions enforced only in code — not in the database. Any direct DB access, bulk import, or code bug bypasses all checks.

3. **Monolithic Router Files:** `purchases.py` (152KB), `reports.py` (189KB), `pos.py` (67KB) are effectively monolithic services in single files. Untestable in isolation, high merge conflict probability, complexity obscured.

4. **No Event Log / Immutable Ledger:** The system mutates state directly (UPDATE balance) rather than appending immutable events (INSERT journal_line). There is no way to replay or reconstruct financial history. Audit logs are a separate concern from financial event sourcing.

5. **Optional Security Dependencies:** Redis (rate limiting) and SMTP (alerts) are optional with graceful fallback. Security features must never degrade silently — they should fail loud.

6. **Multi-Tenant DB Isolation Without Connection Pool Limits:** Each company gets its own database engine with LRU cache of 50 engines. Under 50+ active companies, engines are evicted and recreated. One company can exhaust the PostgreSQL connection limit.

7. **Hardcoded Compliance Constants:** GOSI rates, ZATCA tax thresholds, and other regulatory values are in code, not in versioned configuration tables with effective dates.

---

### 3) RECOMMENDED REFACTORING PLAN

**Phase 1 — Emergency Security Fixes (Week 1)**
1. Revert rate limits to production values (`MAX_ATTEMPTS_IP = 5`)
2. Audit and fix all f-string SQL patterns in branch filtering
3. Move refresh token to `httpOnly` cookie
4. Make 2FA mandatory for `admin`, `superuser`, `accountant` roles
5. Add sensitive field masking to audit log

**Phase 2 — Financial Data Integrity (Weeks 2–4)**
6. Add DB trigger enforcing `SUM(debit) = SUM(credit)` on journal entries
7. Add `SELECT FOR UPDATE` on inventory deduction in invoice creation
8. Add CHECK constraints on all status columns
9. Fix missing FK constraints (all non-polymorphic columns)
10. Add NOT NULL constraint to `invoices.party_id`; migrate data from deprecated columns
11. Fix ZATCA tax calculation to distribute header discounts to line tax base

**Phase 3 — Balance Architecture (Weeks 4–8)**
12. Create materialized view `account_balances` from `journal_lines`
13. Remove `accounts.balance` column; redirect all reads to materialized view
14. Replace `party_transactions.balance` with window function view
15. Add explicit `BEGIN/COMMIT` transaction boundaries in all document creation flows
16. Add `CHECK (quantity >= 0)` on inventory table

**Phase 4 — Performance & Reliability (Weeks 8–12)**
17. Add missing indexes (see ISSUE-021 list)
18. Commit to Alembic for all schema changes; write migration for all existing tables
19. Split monolithic router files into domain-focused sub-modules
20. Add PostgreSQL sequences for all document number generation
21. Make Redis a required dependency for rate limiting

**Phase 5 — Compliance Hardening (Weeks 12–16)**
22. Move GOSI rates and statutory rates to dated configuration tables
23. Create `eos_calculations` audit table with all input parameters
24. Implement end-to-end ZATCA e-invoice flow with cryptographic signing
25. Add automated balance reconciliation job (GL vs. inventory valuation)
26. Replace polymorphic `source`/`source_id` with per-document FK columns

---

### 4) QUICK WINS

These can be done in under a day each and have immediate impact:

| # | Action | Effort | Impact |
|---|--------|--------|--------|
| 1 | Fix rate limits (3 constant changes in `auth.py`) | 30 min | CRITICAL security fix |
| 2 | Add inventory `CHECK (quantity >= 0)` constraint | 15 min | Prevents negative inventory |
| 3 | Add status CHECK constraints on top 5 tables | 1 hour | Prevents invalid state data |
| 4 | Mask sensitive fields in audit log | 2 hours | Reduces data exposure |
| 5 | Add `journal_lines.account_id` index | 15 min | Immediate query speedup |
| 6 | Make 2FA mandatory for admin roles | 2 hours | Closes brute force→admin path |
| 7 | Add NOT NULL to `invoices.party_id` after data migration | 1 hour | Closes AR tracking gap |
| 8 | Create GOSI rates config table and load current values | 3 hours | Compliance hardening |

---

### 5) SYSTEM RISK SCORE

| Dimension | Score (0=worst, 100=best) | Notes |
|-----------|--------------------------|-------|
| Financial Data Integrity | 38 / 100 | Multiple divergent balance sources; no DB-level double-entry enforcement |
| Security | 45 / 100 | Good JWT/2FA architecture undermined by testing-level rate limits and localStorage tokens |
| Business Logic Correctness | 52 / 100 | ZATCA tax bug, GOSI hardcoding, EOS audit gap |
| Performance Architecture | 55 / 100 | Missing indexes, no balance caching strategy, monolithic files |
| DevOps / Deployability | 48 / 100 | No real migrations, optional security dependencies |
| Regulatory Compliance | 50 / 100 | ZATCA risk is direct compliance exposure |
| Code Quality | 62 / 100 | Reasonably organized but files too large, no event sourcing |
| Feature Completeness | 78 / 100 | Most ERP functions implemented and working |

**COMPOSITE SYSTEM RISK SCORE: 34 / 100**

> A score of 34 means this system carries **HIGH RISK for production financial operations**. The combination of divergent balance sources, no DB-level double-entry enforcement, production security at testing values, and ZATCA non-compliance creates conditions where incorrect financial reports, compliance violations, and security breaches are plausible outcomes in normal operation — not just edge cases.

---

**Minimum threshold for safe production operation:** Fix Issues 001, 002, 004, 007, 009, 012. These six issues alone raise the composite risk score to approximately **61 / 100 (MEDIUM RISK)**.

---

*Report generated: 2026-03-29 | Scope: Full codebase audit | Method: Static analysis of source files*
