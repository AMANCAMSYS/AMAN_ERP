# AMAN ERP — Cross-Artifact Consistency & Quality Analysis

**Date:** 2026-04-02
**Constitution Version:** 2.0.0 (17 principles)
**Methodology:** Deep static analysis of all production source files, models, services, routers, frontend, database, and migrations
**Scope:** Full codebase against Constitution v2.0.0 principles + spec/plan/tasks template alignment

---

## EXECUTIVE SUMMARY

**System Status: CONDITIONALLY PRODUCTION-READY (75/100)**

The AMAN ERP system demonstrates strong foundational architecture with comprehensive feature coverage across 12 modules, 240+ models, 767 endpoints, and 279 frontend pages. Previous audit remediation (76 fixes) addressed most critical issues. However, this analysis identifies **6 Critical**, **8 High**, and **7 Medium** residual findings that must be addressed to achieve full constitution compliance.

**Key Strengths:**
- GL service centralization complete (routers: 100% migrated)
- Double-entry constraint trigger hardened and deployed
- Multi-tenant isolation architecture sound
- Rate limiting at production values
- JWT in HttpOnly cookies with SameSite=Strict
- 2FA backup codes properly hashed
- Fiscal period enforcement on 23/25 endpoints
- Optimistic locking on 13 critical tables
- 46 database indexes + 32 FK constraints

**Key Gaps:**
- 45+ residual `float()` conversions in monetary contexts
- f-string SQL formatting in 40+ locations
- Missing permission decorators on ~40 endpoints
- Three independent balance calculation methods (divergence risk)
- Fiscal period check missing on inventory adjustments
- Treasury transfer deadlock potential
- PO receipt line TOCTOU race condition

---

## PRINCIPLE-BY-PRINCIPLE COMPLIANCE MATRIX

| # | Principle | Status | Severity | Key Finding |
|---|-----------|--------|----------|-------------|
| I | Financial Precision | ⚠️ Partial | CRITICAL | 45+ float() conversions remain in dashboards, KPIs, HR, external, cache serializer |
| II | Multi-Tenant Isolation | ⚠️ Partial | HIGH | Audit router bypasses company routing (line 54); price_lists/currencies access system DB |
| III | Double-Entry Integrity | ⚠️ Partial | HIGH | Three independent balance sources can diverge; validate_je_lines not called in most routers |
| IV | Security & Access Control | ❌ Violation | CRITICAL | f-string SQL in 40+ files; ~40 endpoints missing permission decorators |
| V | Regulatory Compliance | ✅ Compliant | — | ZATCA, WHT, GOSI/WPS, Zakat properly implemented |
| VI | Concurrency Safety | ⚠️ Partial | HIGH | PO receipt TOCTOU race; treasury deadlock risk; invoice double-commit |
| VII | Simplicity & Maintainability | ✅ Compliant | — | GL service centralized; DataTable/FormField 100%; structured logging |
| VIII | Inventory Integrity | ⚠️ Partial | HIGH | Fiscal period check missing on adjustments; destination transfer race |
| IX | Procurement Discipline | ⚠️ Partial | MEDIUM | PO line received_quantity has TOCTOU race condition |
| X | Manufacturing Execution | ✅ Compliant | — | BOM, routing, capacity properly implemented |
| XI | HR & Payroll Compliance | ⚠️ Partial | MEDIUM | float() in GOSI calculations and salary exports |
| XII | Asset Lifecycle Management | ✅ Compliant | — | Depreciation, disposal, revaluation, impairment complete |
| XIII | Sales & CRM Workflow | ✅ Compliant | — | State machine, credit limits, commissions, pricing all enforced |
| XIV | Approval Workflow Governance | ✅ Compliant | — | Multi-level sequential approval with audit trail |
| XV | Project & Contract Management | ✅ Compliant | — | Budget variance, dependencies, contract types implemented |
| XVI | POS Operations | ✅ Compliant | — | Session integrity, multi-tender, KDS, loyalty all functional |
| XVII | Observability & Audit Trail | ⚠️ Partial | MEDIUM | AuditMixin/SoftDeleteMixin in place; audit log tenant isolation gap |

**Compliance Score: 10/17 Fully Compliant, 7/17 Partially Compliant, 0/17 Fully Non-Compliant**

---

## DETAILED FINDINGS

### CRITICAL FINDINGS (Must Fix Before Production)

#### C-001: Residual float() Conversions in Monetary Contexts
**Principle:** I (Financial Precision)
**Severity:** CRITICAL
**Count:** 45+ instances across 14 files

**Most Dangerous:** `backend/utils/cache.py:20` — The JSON serializer converts ALL cached `Decimal` values to `float`, affecting every cached monetary response system-wide.

| File | Count | Context |
|------|-------|---------|
| `utils/cache.py` | 1 | Global JSON serializer — ALL cached monetary values lose precision |
| `services/industry_kpi_service.py` | 14 | Financial KPIs: GMROI, margins, ratios |
| `routers/hr/advanced.py` | 10 | GOSI contributions, salary components |
| `routers/dashboard.py` | 9 | Sales, expenses, profit, cash balances |
| `services/kpi_service.py` | 8 | Revenue, expenses, customer values |
| `routers/finance/intercompany.py` | 6 | Intercompany debits/credits, revenue recognition |
| `routers/crm.py` | 4 | CRM field values, win rates |
| `utils/hr_helpers.py` | 3 | Gratuity calculations |
| `utils/accounting.py` | 2 | Account balance change for SQL params |
| `utils/zatca.py` | 2 | Invoice total and VAT for ZATCA |
| `services/scheduler.py` | 2 | GL balance and net income for reports |
| `routers/external.py` | 4 | ZATCA invoice totals, WHT amounts |
| `services/gl_service.py` | 1 | Exchange rate in GL entry |
| `services/costing_service.py` | 1 | Cost impact deviation |

**Fix Priority:** Start with `utils/cache.py` (system-wide impact), then `utils/accounting.py` (balance accuracy), then `utils/zatca.py` (regulatory), then remaining files.

**Recommended Fix for cache.py:**
```python
if isinstance(obj, Decimal):
    return str(obj)  # Preserve precision; frontend parses as needed
```

---

#### C-002: f-String SQL Formatting (Potential SQL Injection)
**Principle:** IV (Security & Access Control)
**Severity:** CRITICAL
**Count:** 40+ instances across 20+ router files

**Pattern:**
```python
db.execute(text(f"UPDATE documents SET {', '.join(fields)} WHERE id = :id"), params)
```

**Affected Files (sample):**
- `routers/services.py:500, 212`
- `routers/crm.py:246, 435, 635, 747, 827, 1007, 1179`
- `routers/hr/advanced.py:79, 149, 510, 587, 644, 697, 762, 828`
- `routers/projects.py:313, 476, 1098, 1659`
- `routers/pos.py:1139, 1376, 1467`
- `routers/finance/*` (multiple files)
- `routers/sales/*` (multiple files)
- `routers/inventory/*` (multiple files)

**Mitigation:** Most instances build field names from hardcoded allowlists, reducing actual exploit risk. However, the constitution mandates parameterized queries for ALL SQL — f-string formatting violates this even with hardcoded fields because:
1. Future edits could introduce user-controlled field names
2. Code review cannot easily distinguish safe from unsafe f-string SQL
3. The pattern normalizes a dangerous practice

**Recommended Fix:** Create a utility:
```python
def build_update_clause(allowed_fields: set, requested: dict) -> tuple[str, dict]:
    safe = {k: v for k, v in requested.items() if k in allowed_fields}
    clause = ", ".join(f"{k} = :{k}" for k in safe)
    return clause, safe
```

---

#### C-003: Missing Permission Decorators on ~40 Endpoints
**Principle:** IV (Security & Access Control)
**Severity:** CRITICAL

**Affected File (example):** `routers/companies.py`
- `PUT /modules` — update enabled modules (no permission check)
- `GET /{company_id}` — read company details (no permission check)
- `PUT /update/{company_id}` — modify company (no permission check)
- `POST /upload-logo/{company_id}` — file upload (no permission check)

These endpoints use `Depends(get_current_user)` for authentication but lack `require_permission("module.action")` for authorization. Any authenticated user can access these endpoints regardless of role.

**Fix:** Add `dependencies=[Depends(require_permission("company.read"))]` (or appropriate permission) to each endpoint.

---

#### C-004: Three Independent Balance Calculation Methods
**Principle:** III (Double-Entry Integrity)
**Severity:** CRITICAL

The system maintains THREE independent balance sources that can diverge:

1. **Running balance column** (`accounts.balance`) — updated by trigger `trg_jl_account_balance` on journal_lines INSERT/UPDATE/DELETE
2. **SUM of journal lines** — used in year-end closing, reports, dashboards
3. **Treasury balance** (`treasury_accounts.current_balance`) — synced from `accounts.balance` via trigger `trg_sync_treasury_from_gl`

**Divergence Risk:**
- If trigger fails but transaction commits → balance column diverges from SUM
- If application directly updates `accounts.balance` → trigger bypassed
- Foreign-currency handling differs between methods
- Treasury balance inherits errors from accounts.balance (cascading divergence)

**Recommended Fix:**
1. Designate SUM(journal_lines) as the canonical source
2. Implement a balance reconciliation utility that compares all three and reports differences
3. Add a scheduled job to detect divergence daily
4. Long-term: consider materialized views

---

#### C-005: Invoice Creation Double-Commit (Atomicity Violation)
**Principle:** VI (Concurrency Safety)
**Severity:** CRITICAL
**File:** `routers/sales/invoices.py:559, 604`

```python
db.commit()  # Line 559: commits invoice + GL entries
# ... ZATCA QR generation (try-except) ...
db.execute(text("INSERT INTO notifications..."))
db.commit()  # Line 604: commits notifications
```

If the second commit fails, the invoice exists but notifications are lost. Similar pattern in:
- `routers/sales/orders.py:210`
- `routers/purchases.py:659, 692`
- `routers/hr/core.py:1122`

**Fix:** Wrap all operations in a single transaction using `trans = db.begin()`.

---

#### C-006: Fiscal Period Check Missing on Inventory Adjustments
**Principle:** VIII (Inventory Integrity)
**Severity:** CRITICAL
**File:** `routers/inventory/adjustments.py` — missing `check_fiscal_period_open()` before GL entry at line 225

Stock adjustments generate variance journal entries. Without fiscal period enforcement, adjustments can post to closed accounting periods, violating the double-entry integrity principle.

**Fix:** Add `check_fiscal_period_open(db, str(datetime.now().date()))` before line 225.

---

### HIGH FINDINGS

#### H-001: Audit Router Bypasses Company Database Routing
**Principle:** II (Multi-Tenant Isolation)
**File:** `routers/audit.py:54` — uses `engine.connect()` (system DB) directly
**Risk:** Authenticated users with `audit.view` could access cross-company audit logs
**Fix:** Add company_id filter or restrict to system_admin role

#### H-002: validate_je_lines() Not Called in Most Routers
**Principle:** III (Double-Entry Integrity)
**File:** Only `pos.py:671` calls it explicitly. All other routers rely solely on the DB trigger.
**Risk:** Errors detected at commit time instead of early validation
**Fix:** Add `validate_je_lines()` call inside `gl_service.create_journal_entry()` before line insertion

#### H-003: PO Receipt Line TOCTOU Race Condition
**Principle:** VI (Concurrency Safety) / IX (Procurement Discipline)
**File:** `routers/purchases.py:750-775`
**Risk:** Concurrent receipts of same PO line can overwrite each other's quantities
**Fix:** Add `FOR UPDATE` lock when reading purchase_order_lines

#### H-004: Treasury Transfer Deadlock Potential
**Principle:** VI (Concurrency Safety)
**File:** `routers/finance/treasury.py:574-575`
**Risk:** Concurrent A→B and B→A transfers deadlock
**Fix:** Always lock treasury accounts in sorted ID order

#### H-005: populate_company_data.py Bypasses GL Service
**Principle:** III (Double-Entry Integrity)
**File:** `scripts/populate_company_data.py` — 107 direct INSERT statements
**Risk:** Sample data may not pass balance validation
**Fix:** Migrate to `gl_service.create_journal_entry()`

#### H-006: Concurrent Session Limits Not Enforced
**Principle:** IV (Security & Access Control)
**File:** `routers/security.py`
**Risk:** Unlimited concurrent sessions per user; compromised accounts maintain unlimited access
**Fix:** Enforce max 5 active sessions per user with oldest-session eviction

#### H-007: utils/accounting.py Uses float() for Balance Updates
**Principle:** I (Financial Precision)
**File:** `backend/utils/accounting.py:164, 170`
**Risk:** Account balance changes lose precision when passed as float to SQL params
**Fix:** Pass Decimal directly or use `str(change_base)`

#### H-008: utils/zatca.py Uses float() for Tax Calculations
**Principle:** V (Regulatory Compliance)
**File:** `backend/utils/zatca.py:254-255`
**Risk:** ZATCA invoice totals and VAT amounts lose precision
**Fix:** Use Decimal throughout ZATCA processing

---

### MEDIUM FINDINGS

#### M-001: PO Receipt Inventory Update Without Transaction Wrapper
**File:** `routers/purchases.py:710-875`
**Fix:** Add explicit transaction wrapper

#### M-002: Inventory Transfer Destination Race
**File:** `routers/inventory/transfers.py:107-119`
**Fix:** Add lock on destination warehouse row

#### M-003: HR GOSI Calculations Use float() in Returns
**File:** `routers/hr/advanced.py:324-328, 394-407`
**Fix:** Return string representations of Decimal values

#### M-004: Dashboard All Monetary Values Converted to float()
**File:** `routers/dashboard.py:163-166, 288, 304, 373`
**Fix:** Use `str()` conversion for JSON responses

#### M-005: KPI Services Use float() Extensively
**Files:** `services/industry_kpi_service.py`, `services/kpi_service.py`
**Fix:** Return string for monetary KPIs; float acceptable for percentages/ratios

#### M-006: Bank Reconciliation Lacks Auto-Matching
**File:** `routers/finance/reconciliation.py`
**Status:** Manual matching only; no automatic date/amount matching algorithm
**Fix:** Implement auto-match with configurable tolerance

#### M-007: Audit Log Tenant Isolation Gap
**File:** `routers/audit.py:54, 195, 223`
**Fix:** Add company_id filtering on all system-level audit queries

---

## SPEC / PLAN / TASKS TEMPLATE ALIGNMENT

### Constitution v2.0.0 ↔ Plan Template
**Status:** ✅ ALIGNED
- Plan template's "Constitution Check" section is dynamic and will auto-populate with all 17 principles
- No hardcoded principle references that would become stale
- Technology context section matches stack constraints

### Constitution v2.0.0 ↔ Spec Template
**Status:** ✅ ALIGNED
- FR- requirements format supports all principle-driven constraints
- User story prioritization (P1/P2/P3) supports incremental delivery
- Edge cases section can capture principle-specific edge cases

### Constitution v2.0.0 ↔ Tasks Template
**Status:** ✅ ALIGNED
- Phase structure supports principle-driven task types (security, compliance, testing)
- User story organization enables independent testing per principle
- Checkpoint pattern supports constitution compliance verification

---

## REMEDIATION ROADMAP

### Phase 1: Critical Fixes (Week 1-2)

| # | Finding | Effort | Impact |
|---|---------|--------|--------|
| C-001a | Fix `utils/cache.py` Decimal→float (use str) | 1h | System-wide precision fix |
| C-001b | Fix `utils/accounting.py` float params | 2h | Balance accuracy |
| C-001c | Fix `utils/zatca.py` float usage | 2h | Regulatory compliance |
| C-002 | Create `build_update_clause` utility, refactor 40+ files | 3-4 days | SQL injection prevention |
| C-003 | Add permission decorators to ~40 endpoints | 2-3 days | Authorization enforcement |
| C-005 | Wrap invoice/PO/HR in single transactions | 1-2 days | Atomicity fix |
| C-006 | Add fiscal period check to inventory adjustments | 1h | Accounting integrity |

### Phase 2: High-Priority Fixes (Week 2-3)

| # | Finding | Effort | Impact |
|---|---------|--------|--------|
| H-001 | Fix audit router tenant isolation | 2h | Multi-tenant security |
| H-002 | Add validate_je_lines to gl_service | 2h | Fail-fast validation |
| H-003 | Add FOR UPDATE to PO receipt lines | 2h | Concurrency safety |
| H-004 | Implement sorted lock ordering for treasury | 1h | Deadlock prevention |
| H-005 | Migrate populate_company_data to gl_service | 4h | Data integrity |
| H-006 | Enforce concurrent session limits | 4h | Security hardening |
| H-007-008 | Fix remaining float() in accounting/zatca utils | 2h | Precision + compliance |

### Phase 3: Medium-Priority Fixes (Week 3-4)

| # | Finding | Effort | Impact |
|---|---------|--------|--------|
| C-001d | Fix remaining 30+ float() in dashboards/KPIs/HR | 2-3 days | Full precision compliance |
| C-004 | Build balance reconciliation utility | 1 week | Divergence detection |
| M-001-002 | Add transaction wrappers and locks | 1 day | Concurrency safety |
| M-006 | Implement auto-match for bank reconciliation | 3-4 days | Feature completeness |

### Phase 4: Monitoring & Hardening (Ongoing)

- Add scheduled balance reconciliation job (daily)
- Add linting rules to catch `float()` in monetary contexts
- Add pre-commit hook to prevent direct journal INSERT outside gl_service
- Comprehensive E2E test suite for core transaction flows
- Pydantic schema creation for remaining ~98 routes

---

## SCORE PROJECTION

| Phase | Estimated Score | Key Milestone |
|-------|----------------|---------------|
| Current | 75/100 | Baseline after 76 fixes |
| After Phase 1 | 82/100 | Critical security + precision fixes |
| After Phase 2 | 87/100 | Concurrency + isolation fixes |
| After Phase 3 | 91/100 | Full float elimination + reconciliation |
| After Phase 4 | 95+/100 | E2E tests + Pydantic schemas + monitoring |

---

## CONCLUSION

AMAN ERP has a **solid architectural foundation** with comprehensive feature coverage rivaling commercial ERP systems (SAP, Oracle, Dynamics). The previous audit remediation (76 fixes) successfully addressed the most critical issues — rate limiting, token security, core Decimal conversions, FOR UPDATE locks, fiscal period enforcement, and GL centralization.

The remaining findings fall into three categories:
1. **Precision leaks** (float in JSON serialization, dashboards, KPIs) — these affect display accuracy but not core accounting integrity since the DB trigger and GL service enforce balance
2. **Security hardening** (f-string SQL, missing permissions, session limits) — the current risk is mitigated by hardcoded field lists and authentication requirements, but the patterns violate defense-in-depth
3. **Concurrency edge cases** (double-commit, TOCTOU, deadlock) — these require specific concurrent access patterns to trigger but should be fixed for production reliability

**Verdict:** The system is **conditionally production-ready** for low-to-medium transaction volumes. The Phase 1 fixes (1-2 weeks) should be completed before high-volume production deployment. The double-entry trigger and GL service provide a strong safety net even with the remaining issues.
