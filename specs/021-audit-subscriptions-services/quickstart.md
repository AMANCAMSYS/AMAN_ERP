# Quickstart: 021 Audit — Subscriptions, Services & Expenses

**Branch**: `021-audit-subscriptions-services`
**Prerequisite**: Branch `020-audit-reports-approvals` changes should be committed (schema changes in database.py may overlap).

## Development Setup

```bash
# Switch to the feature branch
git checkout 021-audit-subscriptions-services

# Backend — no new dependencies needed
cd backend
# Verify existing setup works
python -c "from services.gl_service import create_journal_entry; print('GL service OK')"
python -c "from utils.fiscal_lock import check_fiscal_period_open; print('Fiscal check OK')"
python -c "from utils.approval_utils import try_submit_for_approval; print('Approval utils OK')"

# Frontend — no new dependencies needed
cd ../frontend
npm install  # Only if node_modules is stale
```

## Key Files to Edit

### Backend (4 files + database.py + 1 new migration)

| File | Lines | Primary Changes |
|------|-------|-----------------|
| `backend/services/subscription_service.py` | ~500 | GL integration, Decimal, fiscal check, idempotency, billing fixes |
| `backend/routers/finance/subscriptions.py` | ~372 | Decimal, Pydantic schemas, approval, branch access, audit logging |
| `backend/routers/finance/expenses.py` | ~948 | Decimal (15+), soft-delete, Pydantic schemas, fiscal check, FOR UPDATE, policy enforcement |
| `backend/routers/services.py` | ~635 | Pydantic schemas, soft-delete, branch access, audit logging, status machine, pagination, download endpoint |
| `backend/database.py` | — | Schema DDL updates (see data-model.md) |
| `backend/migrations/versions/fix_sub_svc_exp_schema.py` | NEW | Alembic migration for all schema changes |

### Frontend (11 files + locale files)

| File | Primary Changes |
|------|-----------------|
| `frontend/src/pages/Services/ServiceRequests.jsx` | Fix showToast (7+ calls) |
| `frontend/src/pages/Services/DocumentManagement.jsx` | Fix showToast (2), add key prop |
| `frontend/src/pages/Subscription/PlanForm.jsx` | Replace hardcoded 'SAR' with getCurrency() |
| `frontend/src/pages/Subscription/SubscriptionHome.jsx` | Replace hardcoded Arabic with i18n |
| `frontend/src/pages/Subscription/EnrollmentForm.jsx` | Replace hardcoded Arabic with i18n |
| `frontend/src/pages/Subscription/EnrollmentDetail.jsx` | Fix useEffect dependency |
| `frontend/src/pages/Subscription/PlanList.jsx` | Format monetary values |
| `frontend/src/pages/Expenses/ExpenseForm.jsx` | Remove parseFloat, unify expense types |
| `frontend/src/pages/Expenses/ExpenseDetails.jsx` | formatDate, Link instead of <a> |
| `frontend/src/pages/Expenses/ExpensePolicies.jsx` | i18n errors, unify expense types |
| `frontend/src/locales/en.json` | New i18n keys |
| `frontend/src/locales/ar.json` | New i18n keys |

## Verification

```bash
# After all changes, verify Python syntax
cd backend
python -m py_compile services/subscription_service.py
python -m py_compile routers/finance/subscriptions.py
python -m py_compile routers/finance/expenses.py
python -m py_compile routers/services.py

# Verify no remaining float() casts on monetary values
grep -n "float(" services/subscription_service.py routers/finance/subscriptions.py routers/finance/expenses.py
# Should return 0 results (or only non-monetary float usage)

# Verify no remaining DELETE FROM
grep -n "DELETE FROM" routers/finance/expenses.py routers/services.py
# Should return 0 results

# Verify schema parity (Constitution XXVIII)
# Compare database.py CREATE TABLE with migration ALTER TABLE for each affected table
```

## Implementation Order

The recommended implementation order is:

1. **Database schema** (database.py + migration) — foundation for all other changes
2. **Subscription service GL integration** — highest-severity fix
3. **Float→Decimal conversions** — mechanical, high-impact
4. **Soft-delete conversions** — mechanical, critical for audit trail
5. **Pydantic schemas** — improves validation for subsequent changes
6. **Expense router fixes** — fiscal check, FOR UPDATE, policy enforcement
7. **Services router fixes** — branch access, audit logging, status machine, pagination
8. **Subscription billing fixes** — date calculation, resume, JSON, idempotency
9. **Frontend fixes** — showToast, currency, i18n, formatting
10. **Locale file updates** — new i18n keys for frontend fixes

## Notes

- No new Python dependencies needed — all utilities already exist in the codebase
- No new npm packages needed — all frontend utilities already exist
- The GL service's `exchange_rate` parameter uses `float` (pre-existing) — this is out of scope for this audit
- The `company_id=expense_data.get("company_id", 1)` fallback in expenses is a separate fix (FR-057) — use `current_user.company_id` from the auth context
