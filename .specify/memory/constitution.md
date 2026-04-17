# AMAN ERP — System Constitution

**v1.1.0 | Last Amended: 2026-04-14**
Non-negotiable principles marked ⛔ — violation = critical defect

---

## I. Financial Precision ⛔

⛔ `float` / `double` / JS `Number` forbidden for any monetary value.

| Rule | Requirement |
|------|-------------|
| SQL type | `NUMERIC(18,4)` or narrower for all money columns |
| Python | `decimal.Decimal` + `ROUND_HALF_UP` |
| JavaScript | String-based amounts or fixed-point library |
| Comparison tolerance | `Decimal("0.01")` |
| Exchange rate | Locked at transaction date; revaluation MUST NOT alter original rate |
| Budget | Enforced at journal-entry posting; overrun blocks or requires approval |
| Payment allocation | Multi-step: one payment → multiple invoices + remainder tracking |
| Deferred revenue | Follows configured method: over-time or at-point-in-time |

---

## II. Multi-Tenant Isolation ⛔

One PostgreSQL DB per company: `aman_{company_id}`. Cross-tenant leakage = critical defect.

| Rule | Requirement |
|------|-------------|
| DB routing | All ops via `get_db_connection(company_id)` |
| DDL safety | `validate_aman_identifier()` before DDL; `AUTOCOMMIT` engine only |
| System data | `aman_system` DB only (users, company registry, audit logs) |
| Engine cache | LRU-bounded to prevent connection exhaustion |
| Migrations | `alembic -x company=<id> upgrade head` per tenant; idempotent (`IF NOT EXISTS`) |
| New company | Auto-apply all migrations to HEAD on creation |

---

## III. Double-Entry Integrity ⛔

Every transaction → balanced journal entries. Debit total = Credit total. No exceptions, even temporarily.

| Rule | Requirement |
|------|-------------|
| Entry creation | All via `services/gl_service.py`. Direct INSERT forbidden. |
| DB constraint | `trg_journal_balance` trigger — `DEFERRABLE INITIALLY DEFERRED` on `journal_lines` |
| App validation | `validate_je_lines()` called at every transaction point before persist |
| Fiscal period | `check_fiscal_period_open()` gates all transaction creation |
| Recurring JEs | Auto-post to open periods only; skipped periods → flagged for review |

---

## IV. Security & Access Control ⛔

| Area | Rule |
|------|------|
| Tokens | JWT access + refresh in login body → `localStorage`. Axios interceptor adds Bearer header. |
| New secrets | MUST NOT be added to `localStorage` without architectural justification |
| Token payload | `user_id`, `company_id`, `role`, `permissions`, `enabled_modules`, `allowed_branches`, `type` |
| 2FA | TOTP via `pyotp` required |
| Endpoints | `require_permission('module.action')` on every router endpoint |
| Permission levels | Role-level, field-level, cost-center/warehouse-level |
| Rate limits | Login 5/min·IP · Forgot-pw 3/min·email · API 100/min·user · API keys configurable |
| Sessions | 401 → refresh; logout blacklists token in DB+cache; concurrent session validation |
| Logs | Secrets, tokens, credentials NEVER in logs or API responses |
| SQL | Parameterized `:param` always. String interpolation forbidden. |
| XSS | Nginx CSP headers required |
| Error sanitization | `raise HTTPException(detail=str(e))` forbidden. Generic message + `logger.exception()` |
| Branch filtering | `validate_branch_access(current_user, branch_id)` on every branch-scoped endpoint |
| Bypass rules | Superusers/admins bypass; empty `allowed_branches` = unrestricted |
| New routers | Auto-extract + validate `branch_id` via dep/decorator. Warehouse → `resolve_warehouse_branch()` |

---

## V. Regulatory Compliance — Saudi Arabia ⛔

| Regulation | Requirements |
|------------|-------------|
| ZATCA / VAT | 15% standard rate; e-invoicing; gross-up logic; header discount → proportional tax base reduction per line |
| WHT | Deduction at source via `WhtRate` + `WhtTransaction`. Capital gains excluded from VAT. |
| Tax Regimes | `TaxRegime` with jurisdiction codes. Branch- and company-level overrides apply. |
| GOSI / WPS | Rates from `gosi_settings` at runtime (hardcode as fallback only). WPS: labor card, insurance no., visa status mandatory. |
| Zakat | Follow `docs/ZAKAT_CALCULATION_METHODOLOGY.md` |
| Configurability | All SA rates/thresholds stored as settings. Hardcoding = fallback only, must be documented. |
| Test coverage | ZATCA, GOSI, WHT, Zakat, Saudization changes require tests — no exceptions |

---

## VI. Concurrency Safety

| Scenario | Protection |
|----------|------------|
| Inventory transfers, treasury movements | `SELECT … FOR UPDATE` row-level lock |
| Low-lock entities (e.g., `Party`) | Optimistic locking via version columns |
| Balance-affecting ops | Atomic within single DB transaction |
| Credit limit check | `customer_balance + order_total ≤ credit_limit` — atomic at SO posting |
| BOM component reservation | Atomic inventory decrement on MO release |
| Three-way match | PO qty = GRN qty = invoice qty — validated before payment |

---

## VII. Simplicity & Maintainability

| Rule | Detail |
|------|--------|
| SQL-first | `db.execute(text(…))` + parameterized queries. ORM for schema/relationships. Pydantic at API boundary. |
| Abstractions | New abstraction requires 3+ proven use cases |
| Naming | Python `snake_case` · JS/React `camelCase` |
| Logging | `logger.error()` / structured logging. `print()` in production code forbidden. |
| Large lists | `VirtualList` for 1000+ rows |
| Indexes | Required for new high-cardinality filter columns |
| Pagination | Default 25 rows, max 100 |
| Frontend | See `docs/FRONTEND_STYLE_GUIDE.md` |

---

## VIII. Inventory Integrity

| Rule | Detail |
|------|--------|
| UOM | Every movement: qty divisible by product base unit |
| Available qty | `qty_on_hand − qty_reserved − qty_damaged` (never use `qty_on_hand` alone) |
| Costing | FIFO via `batch_serial_movements`; policy per company (FIFO/LIFO/WA); changes → `CostingPolicyHistory` + `InventoryCostSnapshot` |
| Adjustments | Auto-generate variance JEs via GL service |
| Transfers | Transit status tracked; source stock unchanged until shipment confirm |
| Cycle count | Variances → auto-adjustment entries |
| Bin mgmt | `BinInventory` per warehouse-bin-product |
| Traceability | Batch/serial enforced for flagged products |
| Quality | `QualityInspection` gates receipt for configured categories |

---

## IX. Procurement Discipline

| Rule | Detail |
|------|--------|
| PO lines | Discounts + markups at line and total (`effect_type`: discount/markup) |
| Landed costs | Allocated by qty or value via `LandedCostAllocation` |
| Three-way match | PO ↔ GRN ↔ supplier invoice before payment; variance tolerance configurable |
| Blanket PO | `PurchaseAgreement` tracks consumed qty vs. limits |
| Supplier rating | Quality, delivery, price → `SupplierRating` → influences PO approval |
| Payment terms | Due date = `invoice_date + payment_days` (auto) |

---

## X. Manufacturing Execution

| Rule | Detail |
|------|--------|
| BOM consumption | Auto-reduces components on MO completion |
| Scrap | `output_qty = required_qty / (1 − scrap_rate%)` |
| Routing | Step N blocked until step N-1 = complete |
| Capacity | `ResourceCapacity` vs `ResourceUtilization` validated before MO release |
| Job cards | Per-operation: qty produced, scrap, downtime |
| MO state machine | `draft → planned → released → in_progress → completed` |

---

## XI. HR & Payroll Compliance

| Rule | Detail |
|------|--------|
| Salary formula | `basic_salary + allowances − deductions = net_salary`; multi-currency locks rate at period-end |
| Payroll status | `draft → calculated → locked` (no edits after lock) |
| Leave | Decrement on approval; reset on fiscal year-end per leave type |
| Termination | Close pending leaves + generate end-of-service benefit calc |
| WPS (Saudi) | Labor card no., insurance no., visa status mandatory |
| GOSI | Rates from configured tables |
| Documents | Expiry dates tracked for compliance alerts |
| Custody | Company assets tracked; reconciled at termination |
| Recruitment | `JobOpening → JobApplication` status through hiring workflow |

---

## XII. Asset Lifecycle Management

| Rule | Detail |
|------|--------|
| Depreciation | `monthly = (cost − salvage_value) / (useful_life_years × 12)`; schedules pre-generated at creation |
| Disposal | Derecognition JE via GL service |
| Revaluation | Adjusts carrying value + equity (surplus/deficit) |
| Impairment | Write-down to fair value + JE |
| Transfers | Logged via `AssetTransfer` |
| Insurance | Policy numbers + expiry dates tracked |
| Maintenance | Cost per asset recorded |

---

## XIII. Sales & CRM Workflow

| Rule | Detail |
|------|--------|
| State machine | `Quotation → SO → Delivery → Invoice → Receipt` (no skipping) |
| Credit limit | `customer_balance + order_total > credit_limit` blocks SO posting |
| Commissions | Per invoice; paid after collection only |
| Pricing | `CustomerPriceList` overrides standard when configured |
| Party | Can be customer AND supplier simultaneously |
| CRM pipeline | `lead → proposal → negotiation → won/lost` + probability + expected close |
| Lead scoring | Auto-calculated by rule |
| Targets | Trackable per salesperson |

---

## XIV. Approval Workflow Governance

| Rule | Detail |
|------|--------|
| Levels | Configurable number of required approvers per doc type |
| Sequence | Level N cannot approve if level N-1 rejected |
| Logging | `ApprovalAction`: timestamp, approver, action, comments |
| Rejection | Loops back to preparer |
| Status | `pending → approved / rejected` |

---

## XV. Project & Contract Management

| Rule | Detail |
|------|--------|
| Budget | Variance (`planned − actual`) tracked and surfaced in dashboards |
| Progress | Task % complete rolls up to project level |
| Dependencies | Task deps prevent out-of-order execution |
| Contract types | Fixed-price and time-and-materials billing |
| Expenses | Receipt references + cost type links |
| Milestones | Planned vs. actual dates tracked |

---

## XVI. POS Operations

| Rule | Detail |
|------|--------|
| Sessions | Opening and closing balances per shift/user/warehouse |
| Payments | Multi-tender: cash, card, credit via `PosOrderPayment` |
| Returns | Validate qty + UOM against original order |
| Loyalty | Points accumulation and redemption tracked |
| F&B / Tables | Pre-order with KDS: `pending → preparing → ready` |
| Promotions | Applied at order time; reflected in JEs |
| Closure | Reconcile actual cash vs. system balance |

---

## XVII. Observability & Audit Trail

| Rule | Detail |
|------|--------|
| `AuditMixin` | ALL domain models: `created_at`, `updated_at`, `created_by`, `updated_by` — no exceptions |
| `SoftDeleteMixin` | All business-entity models; physical DELETE forbidden; queries filter `is_deleted=false` |
| Soft-delete exceptions | Pure junction/mapping tables; append-only log/event tables |
| `AuditLog` | user, action, resource, JSONB diff for all state-changing API calls |
| Notifications | In-app, WebSocket, webhook, email channels |
| Reports | `CustomReport` user-definable without code changes |

---

## XVIII. Session Contract & API Consistency

**Login response** (`POST /api/auth/login`) required fields:

| Token fields | User object fields |
|---|---|
| `access_token`, `refresh_token`, `token_type` | `id`, `username`, `full_name`, `email`, `role`, `company_id`, `permissions`, `enabled_modules`, `allowed_branches`, `industry_type`, `currency`, `decimal_places`, `timezone` |

- `GET /api/auth/me` MUST return same user shape.
- Removing/renaming existing fields = MAJOR breaking change.
- `AuthContext` stores full user object. `BranchContext` derives from `user.allowed_branches`. `useIndustryType()` derives from `user.industry_type`.
- Route visibility gated by `user.enabled_modules` — NOT hardcoded role/industry checks.
- Login and `/me` MUST be updated simultaneously when payload changes.

---

## XIX. Calculation Centralization ⛔

⛔ Duplicate calculation logic across routers, services, or frontend = critical defect.

| Calculation | Rule |
|-------------|------|
| Tax (VAT, WHT, gross-up) | Single shared utility; routers MUST NOT inline tax math |
| Discounts / markups | Centralized calculator; re-implementation per-router forbidden |
| Account balance | One canonical method; one designated source of truth; other = reconciled cache |
| Invoice totals | `compute_invoice_totals()` for: sales, purchase, POS, credit/debit notes |
| Frontend | NO monetary calculations; all amounts pre-calculated by backend; `formatNumber()` for display only |
| Bug fixes | Fix propagates automatically because logic is in one place; if touching multiple files → consolidate first |

---

## XX. Report Consistency & Reconciliation ⛔

| Rule | Detail |
|------|--------|
| Trial Balance | Must equal `SUM(debit)−SUM(credit)` from `journal_lines` per fiscal period; any discrepancy = integrity failure |
| Subledger reconciliation | AR aging = GL receivables; AP aging = GL payables; Inventory valuation = GL inventory — verifiable on demand |
| Query source | Reports query `journal_lines` directly; cached views must show cache timestamp + recalculate button |
| Same params = same results | API, page, and Excel export for identical filters must use same query function |
| Period boundaries | Fiscal period open dates — not `created_at` timestamps |
| Multi-currency | Functional vs. foreign amounts separated; mixing in one total column forbidden |

---

## XXI. Cross-Module Data Consistency

| Entity | Rule |
|--------|------|
| Party (customer/supplier) | Read from `parties` table everywhere; no shadow copies; name change reflects via FK join immediately |
| Product catalog | Name, UOM, tax category, costing from `products` table; no local module copies |
| GL account refs | Store `account_id` FK only; resolve code/name/type at query time via join |
| Exchange rates | All modules read from same `exchange_rates` table with same date-lookup logic |
| Config cascade | Company default → branch override; consistent across all modules |

---

## XXII. Transaction Validation Pipeline

Required sequence — every financial mutation:

| Step | Stage | Detail |
|------|-------|--------|
| 1 | Schema | Pydantic validation |
| 2 | Permission | `require_permission` check |
| 3 | Fiscal period | `check_fiscal_period_open()` |
| 4 | Business rules | Credit limit, stock, budget, approval status |
| 5 | Calculation | Totals balance, tax correct, line-header match |
| 6 | Persist | DB write |
| 7 | Post-persist | GL entry, notifications, side effects |

- Fail-fast: block at earliest stage; accumulate all errors within a stage.
- Same pipeline regardless of entry point (API, POS, bulk import).
- Draft: skips stages 4–5 but still requires 1–2. Draft → posted triggers full pipeline.

---

## XXIII. Idempotency & Duplicate Prevention

⛔ Duplicate payments, invoices, or orders caused by double-submit = critical defect.

| Rule | Detail |
|------|--------|
| Idempotency keys | Payment, invoice, order endpoints accept optional `Idempotency-Key` header; same key → return original; TTL ≥ 24h |
| Duplicate detection | Check `(party_id, amount, date, reference)` within configurable window (default 5 min); prompt, don't silently create |
| Sequence numbers | `invoice_no`, `po_no`, `so_no` generated atomically via `SELECT … FOR UPDATE`; gaps ok, duplicates never |
| Frontend guard | Mutation buttons disabled after first click until server responds; enforced in shared API client |
| Bulk import | Detect + skip rows matching existing natural key; report created / skipped / failed counts |

---

## XXIV. Data Lifecycle Governance

| Rule | Detail |
|------|--------|
| Retention | Audit logs ≥ 7 years (Saudi req); soft-deleted records ≥ 1 fiscal year before archival |
| Archival | Configurable period → archive schema; queryable for compliance; excluded from operational queries by default |
| Restore | Soft-delete restorable within retention period; logged in `AuditLog`; re-validates against current business rules |
| Transient cleanup | Sessions, OTPs, idempotency keys, stale cache — purged by scheduler; frequency configurable |
| Attachments | Track size + MIME type; monitor total per company; orphaned attachments flagged, never auto-deleted |

---

## XXV. Performance & Query Discipline

| Rule | Detail |
|------|--------|
| N+1 prevention | Lists with related data → JOINs or batch queries. Loop + `db.execute()` = forbidden. |
| Query reuse | Same data shape → shared query function; copy-paste SQL across routers forbidden |
| Pagination | Every list endpoint enforces `LIMIT`; unbounded queries on 1000+ row tables forbidden |
| Exports | May bypass pagination but MUST stream (chunked/cursor) |
| Heavy aggregations | >2s on representative data → optimize with index, materialized view, or pre-aggregation |
| Connections | Session closed after request; `get_db` dependency manages lifecycle |

---

## XXVI. Calculation Traceability

| Domain | Must Store |
|--------|-----------|
| Tax per line | `tax_rate`, `taxable_base`, `tax_amount`, tax regime ref, rate-override flag |
| Discounts | Source (header%/line%/price list/promo), original amount, discount amount, net amount |
| Exchange rates | `source_currency`, `target_currency`, `rate_used`, `rate_date`, `rate_source` (manual vs system) |
| Payroll run | Per employee: `basic_salary`, each allowance (name+amt), each deduction (name+amt+rule), GOSI employee share, GOSI employer share, `net_salary` |
| Inventory costing | Previous cost, new cost, qty affected, trigger event (receipt/return/adjustment) |

---

## XXVII. UI/UX Behavioral Consistency ⛔

| Component | Required Behavior |
|-----------|-------------------|
| `DataTable` | Server-side pagination (default 25), column sort (date + amount), search on primary text column — identical everywhere |
| Table export | Excel/CSV of full filtered dataset (not current page); same query fn as list endpoint |
| Form validation | Inline errors under field; on submit only; real-time clear on change after fail. No `alert()`/toast-only/top-banner errors. |
| Error messages | Translated i18n keys (`en.json`/`ar.json`); same key for same failure across modules; raw backend strings forbidden |
| Loading states | `PageLoading` or `DataTable` skeleton on initial load; action-button spinner on in-page actions; no empty content without indicator |
| Confirmation dialogs | Shared `ConfirmDialog` for destructive actions; explicit confirmation text for high-impact; no custom per-module modals |
| Filter persistence | Filters, sort, page restored on back-navigation |
| Layout rhythm | workspace header → filters/actions → content → pagination; no custom margins between zones |

---

## XXVIII. Schema Definition Synchronization ⛔

⛔ Schema change in only one location = critical defect (schema drift).

Every schema change MUST apply to **BOTH**:
1. `backend/migrations/` — for existing companies
2. `backend/database.py` CREATE TABLE definitions — for new companies

| Change type | Dual-update requirement |
|-------------|------------------------|
| Column add | Same type, default, nullability in both migration `ALTER TABLE` and `database.py` `CREATE TABLE` |
| Column remove | Removed from `database.py` `CREATE TABLE` + `DROP` via migration |
| Index changes | New indexes in migration AND index section of `database.py` (WHERE clauses identical) |
| Table add/remove | Add to `database.py` init; drop via migration + remove from `database.py` |
| Verification | Freshly created company DB must be schema-identical to existing company after all migrations |

---

## Technology Stack

| Layer | Technology & Constraint |
|-------|------------------------|
| Backend | Python 3.12 / FastAPI — all endpoints via FastAPI routers |
| Frontend | React 18 / Vite — JSX, i18next AR/EN, RTL support |
| Mobile | React Native 0.76 — React Navigation, Firebase, AsyncStorage |
| Database | PostgreSQL 15 — one DB per tenant + `aman_system` |
| ORM | SQLAlchemy 2.0 — schema definitions; SQL-first query style |
| Cache | Redis — rate limiting, sessions, token blacklist |
| Auth | JWT Bearer + TOTP (`pyotp`) — `localStorage` + Axios interceptor |
| Container | Docker + Nginx — Compose orchestration, SSL/TLS |
| Production | Gunicorn + Uvicorn workers behind Nginx |
| Monitoring | Prometheus + Grafana — `/metrics` (internal-only) |
| Validation | Pydantic — all request/response bodies; 422 on failure |

- Backend and frontend independently deployable.
- New Python deps → `backend/requirements.txt`.
- Schema changes → Alembic migrations only. Manual DDL on production forbidden.
- New endpoints → Pydantic `response_model`. Shape must match module pattern.

---

## Data Integrity Constraints

### Database-Level

| Constraint | Rule |
|------------|------|
| Indexes | High-cardinality, frequently-filtered columns |
| FK constraints | Explicit `CASCADE` / `SET NULL` / `RESTRICT` |
| Check constraints | `debit/credit ≥ 0`; `start_date ≤ end_date`; `quantity ≥ 0` |
| Unique constraints | `account_number`, `party_code`, `invoice_number`, `rfq/po/so_number`, `entry_number` — per company DB |
| Balance trigger | `trg_journal_balance` `DEFERRABLE INITIALLY DEFERRED` — validates debit=credit at commit |

### Model & Schema Integrity

| Rule | Requirement |
|------|-------------|
| Model registration | Every new SQLAlchemy model → `models/__init__.py` import AND `__all__` tuple |
| DDL-ORM parity | Column, type, length, default, constraint identical in ORM and DDL |
| FK `ondelete` parity | `ForeignKey()` `ondelete=` matches DDL `ON DELETE` clause |
| Relationships | Every FK → bidirectional `relationship()` with `back_populates`; lazy strategy explicit for 5+ rels |
| Migration coverage | Every DDL table addition has Alembic migration |
| Audit columns in DDL | `AuditMixin` → audit columns in DDL; `SoftDeleteMixin` → soft-delete columns in DDL |

---

## Quality Gates

| Gate | Requirement |
|------|-------------|
| Testing | pytest covers: auth, permission boundaries, fiscal enforcement, JE balance, UOM consistency for new transactional endpoints |
| Migrations | Idempotent Alembic migration for every schema change; works across all active company DBs |
| Code review focus | GL service, permission decorators, multi-tenant routing, approval workflows |
| i18n | New user-facing strings → `en.json` + `ar.json`; default language Arabic |
| Frontend tests | New pages handling auth/permissions/branch/i18n → Vitest + React Testing Library integration test |

### PR Merge Gate Checklist

| Item | ☐ |
|------|----|
| No `float` for money | ☐ |
| No `detail=str(e)` error leakage | ☐ |
| `validate_branch_access()` on `branch_id` endpoints | ☐ |
| `AuditMixin` + `SoftDeleteMixin` on new models | ☐ |
| FK `ondelete` explicit | ☐ |
| New strings in `en.json` + `ar.json` | ☐ |
| Compliance logic has test coverage | ☐ |
| Login/me updated if payload changed | ☐ |
| Response shape matches module pattern | ☐ |
| Alembic migration included for schema changes | ☐ |
| No duplicated calculation logic | ☐ |
| Idempotency key on payment/invoice/order | ☐ |
| Tax/discount/FX breakdown stored (not just totals) | ☐ |

---

## Governance

| Area | Rule |
|------|------|
| Amendments | Version bump + rationale required |
| Versioning | MAJOR = principle removal/redefinition · MINOR = new principle · PATCH = clarification |
| Compliance review | Every feature spec must include Constitution Check against all active principles |
| Runtime guidance | `docs/SYSTEM_KNOWLEDGE_BASE.md` and `docs/MODULE_AUDIT_REPORT.md` |
