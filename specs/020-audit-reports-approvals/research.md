# Research: Reports & Analytics, Approvals & Workflow — Audit

**Date**: 2026-04-20  
**Feature**: [spec.md](./spec.md)

---

## R1 — Frontend Currency Access Pattern

**Decision**: Use `getCurrency()` helper from `utils/auth.js`.

**Rationale**: This is the established project pattern, already used by BalanceSheet.jsx, TransactionList.jsx, and others. It reads `user.currency` from localStorage and falls back to `''`. The pattern is:
```js
import { getCurrency } from '../../utils/auth';
const currency = getCurrency() || 'SAR';  // SAR fallback only if no currency configured
```

**Alternatives considered**:
- `getUser()?.currency` — used by RoleDashboard.jsx already but less concise; `getCurrency()` is the canonical shortcut.

**Impact on spec**:
- KPIDashboard.jsx (line 34): Add `getCurrency` import, replace hardcoded `'SAR'`.
- RoleDashboard.jsx (line 56): Already uses `user?.currency || 'SAR'`; optionally standardize to `getCurrency()` for consistency. The fallback `'SAR'` is acceptable since `getCurrency()` itself falls back to `''`.

---

## R2 — Scheduled Report Execution Architecture

**Decision**: Call internal helper functions directly (not HTTP self-calls).

**Rationale**: Two internal helpers already exist — `_get_profit_loss_data(db, start_date, end_date, branch_id)` and `_get_balance_sheet_data(db, as_of_date, branch_id)`. These accept a db connection and parameters directly, no FastAPI dependency injection required. For other report types (trial_balance, cashflow, general_ledger), similar internal helpers need to be extracted from the endpoint functions.

**Alternatives considered**:
- HTTP self-call — adds network overhead, authentication complexity, and circular dependency risk.
- Calling endpoint functions directly with fake user object — works but is fragile and bypasses branch validation.
- Duplicating SQL in `_execute_scheduled_report` — violates Constitution XIX (calculation centralization).

**Implementation approach**:
1. Extract `_get_trial_balance_data(db, start_date, end_date, branch_id)` from `get_trial_balance` endpoint.
2. Extract `_get_cashflow_data(db, start_date, end_date, branch_id)` from `get_cashflow_report` endpoint.
3. Extract `_get_general_ledger_data(db, account_id, start_date, end_date, branch_id)` from `get_general_ledger` endpoint.
4. Create dispatcher in `_execute_scheduled_report` that maps `report_type` → helper function.
5. Store result as JSONB in scheduled_reports or a new `report_results` table.

**The `report_config` JSONB** stores: `{"start_date": "...", "end_date": "...", "branch_id": ..., "account_id": ...}`.

---

## R3 — Database Schema Current State

**Decision**: All 7 tables audited; gaps confirmed and documented in data-model.md.

**Key findings**:
| Table | Has `updated_at` | Has proper FKs | Has indexes |
|-------|-----------------|----------------|-------------|
| `scheduled_reports` | Yes | Yes (branch_id, created_by) | No custom |
| `shared_reports` | **No** | Partial (shared_by, shared_with — yes; report_id — no) | UNIQUE only |
| `report_templates` | **No** | **None** (no created_by) | None |
| `approval_workflows` | Yes | Yes (created_by) | None custom |
| `approval_requests` | Yes | Partial (workflow_id, requested_by — yes; current_approver_id, escalated_to — **no**) | status, doc only |
| `approval_actions` | **No** (has actioned_at) | Partial (request_id — yes; actioned_by — **no**) | request_id only |
| `analytics_dashboards` | Yes | **No** (created_by/updated_by are VARCHAR(100)) | None |

**`approval_workflow_steps` table**: Confirmed DOES NOT EXIST. Steps are JSONB in `approval_workflows.steps`. This is by design per spec assumption — no table creation needed; fix `approval_utils.py` to read JSONB instead.

**`conditions` default conflict**: CREATE TABLE says `DEFAULT '{}'`, ALTER TABLE says `DEFAULT '[]'`. Resolution: standardize to `'{}'` since conditions are key-value (min_amount, max_amount), not an array.

---

## R4 — Concurrency Control for Approval Actions

**Decision**: Use `SELECT ... FOR UPDATE` (pessimistic row locking) with step-action existence check.

**Rationale**: This is the established pattern across the entire codebase. Every router that handles concurrent state mutations (checks, treasury, inventory, notes, assets, vouchers) uses `SELECT ... FOR UPDATE`. 15+ usage sites confirmed across 10 files.

**Current state**: `approvals.py` line 479 uses a plain `SELECT * FROM approval_requests WHERE id = :id` with no locking — a confirmed race condition.

**Implementation**:
1. Change to `SELECT * FROM approval_requests WHERE id = :id FOR UPDATE`
2. After locking, check `approval_actions` for existing action on same `(request_id, step)`
3. If action exists → return 409 Conflict ("already actioned")
4. Otherwise proceed with normal flow

**Alternatives considered**:
- Optimistic locking (version column) — requires schema migration, not used anywhere else in codebase, adds complexity for no benefit.
- Application-level mutex — fragile, doesn't work across multiple workers.
- Just step-status check without FOR UPDATE — classic TOCTOU race; two transactions can both read `status='pending'` before either commits.

---

## R5 — Report Result Storage for Scheduled Reports

**Decision**: Store generated report results in a new `scheduled_report_results` table.

**Rationale**: Scheduled reports need to be retrievable after generation. Storing in the `scheduled_reports` row itself would bloat the scheduling table. A separate results table allows history (multiple runs per schedule) and easy cleanup.

**Schema**:
```
scheduled_report_results (
    id SERIAL PRIMARY KEY,
    scheduled_report_id INT FK → scheduled_reports(id),
    report_data JSONB NOT NULL,
    generated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'completed'
)
```

**Alternatives considered**:
- Store in `scheduled_reports.last_result` JSONB column — simpler but loses history.
- File system storage — adds I/O complexity and cleanup burden.
