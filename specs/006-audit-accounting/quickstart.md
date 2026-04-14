# Quickstart: Audit Accounting Module

**Feature**: 006-audit-accounting  
**Branch**: `006-audit-accounting`

---

## Prerequisites

- Python 3.12+
- PostgreSQL 15 running locally (or via Docker)
- Redis running locally (or via Docker)
- Node.js 18+ (for frontend)

## 1. Start Services

```bash
# From project root
./start-local.sh
# OR manually:
docker-compose up -d postgres redis
cd backend && pip install -r requirements.txt
uvicorn main:app --reload --port 8000
cd ../frontend && npm install && npm run dev
```

## 2. Verify Accounting Module

### Backend endpoints (all require auth token):

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' | jq -r .access_token)

# Chart of Accounts
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/accounting/accounts

# Journal Entries
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/accounting/journal-entries

# Trial Balance
curl -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/reports/trial-balance?start_date=2026-01-01&end_date=2026-12-31"

# Currencies
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/accounting/currencies

# Cost Centers
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/cost-centers

# Budgets
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/accounting/budgets
```

## 3. Run Existing Tests

```bash
cd backend
pytest tests/ -v -k "accounting or journal or fiscal or currency or budget or cost_center"
```

## 4. Key Files for Audit

| Area | File | What to Check |
|------|------|---------------|
| GL Core | `services/gl_service.py` | `create_journal_entry()` — single entry point for all GL postings |
| Validation | `utils/accounting.py` | `validate_je_lines()`, `update_account_balance()`, `generate_sequential_number()` |
| Fiscal Lock | `utils/fiscal_lock.py` | `check_fiscal_period_open()` — must be called by all posting modules |
| Reconciliation | `utils/balance_reconciliation.py` | `reconcile_account_balances()` — drift detection |
| COA Router | `routers/finance/accounting.py` | Account CRUD, JE CRUD, balance queries |
| Intercompany | `routers/finance/intercompany_v2.py` + `services/intercompany_service.py` | Reciprocal postings |
| Models | `models/core_accounting.py` | ORM definitions — check `float` vs `Decimal` mapping |

## 5. Critical Defects to Verify

1. **Sequential number race condition** — `utils/accounting.py` → `generate_sequential_number()`: Check for `FOR UPDATE` lock
2. **Inventory bypass of fiscal lock** — `routers/inventory/adjustments.py`: Verify `check_fiscal_period_open()` is called before GL posting
3. **GL audit logging gap** — `services/gl_service.py`: Verify `log_activity()` is called on journal entry creation

## 6. Cross-Module GL Integration Points

Verify each module calls `gl_service.create_journal_entry()` and `check_fiscal_period_open()`:

| Module | Router | Expected GL Call |
|--------|--------|-----------------|
| Sales | `routers/sales/invoices.py` | ✅ Calls `gl_create_journal_entry()` |
| Purchases | `routers/purchases.py` | ✅ Calls `gl_create_journal_entry()` |
| Treasury | `routers/treasury.py` | ✅ Calls `gl_create_journal_entry()` |
| Payroll | `routers/hr_wps_compliance.py` | ✅ Calls `gl_create_journal_entry()` |
| POS | `routers/pos.py` | ✅ Calls `gl_create_journal_entry()` |
| Assets | `routers/assets.py` | ✅ Calls `gl_create_journal_entry()` |
| Inventory | `routers/inventory/adjustments.py` | ❌ Calls GL but SKIPS fiscal lock |
| Projects | `routers/projects.py` | ⚠️ Calls GL but misses `log_activity()` at 6 locations |
