# AMAN ERP Constitution

## Core Principles

### I. Financial Precision (NON-NEGOTIABLE)

All monetary values MUST use `Decimal` types with deterministic
rounding. Floating-point arithmetic (`float`, `double`, JavaScript
`Number`) is forbidden for any amount, rate, or balance calculation.

- SQL columns storing money MUST be `NUMERIC(18,4)` or narrower.
- Python code MUST use `decimal.Decimal` with `ROUND_HALF_UP`.
  JavaScript code MUST use string-based amounts or a fixed-point
  library.
- Tolerance for assertion comparisons: `Decimal("0.01")`.
- Multi-currency transactions MUST lock the exchange rate at the
  transaction date. Subsequent revaluation MUST NOT alter the
  original locked rate.
- Cost center budgets MUST be enforced at journal entry posting time;
  budget overruns MUST block or require explicit approval.
- Payment allocation MUST support multi-step distribution: a single
  payment allocated across multiple invoices with remainder tracking.
- Revenue recognition schedules (deferred revenue) MUST follow the
  configured recognition method (over-time or at-point-in-time).

### II. Multi-Tenant Isolation (NON-NEGOTIABLE)

Each company operates in a dedicated PostgreSQL database
(`aman_{company_id}`). Cross-tenant data leakage is a critical defect.

- Every database operation MUST route through
  `get_db_connection(company_id)`.
- DDL operations MUST call `validate_aman_identifier()` before
  executing to prevent SQL injection in schema names.
- DDL operations MUST use a dedicated engine with `AUTOCOMMIT`
  isolation level (separate from transactional engines).
- Shared/system-level data (user accounts, company registry, audit
  logs) lives in the central `aman_system` database only.
- The engine cache MUST be bounded (LRU) to prevent connection
  exhaustion under high tenant load.
- Alembic migrations MUST target individual company databases via
  `alembic -x company=<id> upgrade head`.
- New company creation MUST auto-apply all migrations to HEAD.
- Migrations MUST be idempotent (`CREATE TABLE IF NOT EXISTS`,
  conditional column adds) to safely re-run.

### III. Double-Entry Integrity (NON-NEGOTIABLE)

Every financial transaction MUST produce balanced journal entries
(total debits = total credits). Unbalanced entries are never
permitted, even temporarily.

- All journal entry creation MUST go through the centralized GL
  service (`services/gl_service.py`). Direct INSERT into
  `journal_entries` or `journal_lines` outside this service is
  forbidden.
- The database MUST enforce balance via a PostgreSQL CONSTRAINT
  TRIGGER (`trg_journal_balance`) on `journal_lines` that is
  `DEFERRABLE INITIALLY DEFERRED` — allowing bulk inserts within a
  transaction but validating balance at commit.
- `validate_je_lines()` MUST be called at every transaction point
  before persistence as an application-layer safety net.
- Fiscal period checks (`check_fiscal_period_open()`) MUST gate all
  transaction creation. Posting to a locked or closed fiscal period
  is forbidden.
- Recurring journal templates MUST auto-post only into open fiscal
  periods; skipped periods MUST be flagged for manual review.

### IV. Security & Access Control (NON-NEGOTIABLE)

Authentication and authorization MUST be enforced on every endpoint.

- JWT access and refresh tokens are returned in the login response
  body and stored client-side in `localStorage`. The shared Axios
  interceptor (`utils/api`) attaches `Authorization: Bearer <token>`
  to every request. Migrating to HttpOnly cookies would require
  a full migration plan and is NOT required by this constitution.
- New secrets, credentials, or sensitive data MUST NOT be added
  to `localStorage` without documented architectural justification.
- Tokens carry `user_id`, `company_id`, `role`, `permissions`,
  `enabled_modules`, `allowed_branches`, and `type`.
- Two-factor authentication (TOTP via pyotp) MUST be supported.
- Every router endpoint MUST use `require_permission("module.action")`
  decorator.
- Permissions operate at three granularity levels: role-level,
  field-level, and cost-center/warehouse-level.
- Rate limiting MUST be active (Redis-backed in production,
  in-memory fallback in dev):
  - Login: 5 attempts/minute per IP
  - Forgot-password: 3 attempts/minute per email
  - General API: 100 requests/minute per user
  - API keys: configurable `rate_limit_per_minute` per key
- Token refresh on 401; logout blacklists tokens in DB and cache.
- Concurrent session validation MUST prevent stale session reuse.
- Secrets, tokens, and credentials MUST never appear in logs or API
  responses.
- All SQL MUST use parameterized queries (`:param` syntax). No string
  interpolation in SQL.
- Nginx MUST set CSP headers to mitigate XSS.
- **Error Sanitization**: `raise HTTPException(detail=str(e))` or any
  variant that exposes raw Python exceptions to the client is
  forbidden. Internal errors MUST return a generic message and log
  the full traceback via `logger.exception()`.
- **Branch-Level Data Filtering**: Every endpoint that accepts,
  stores, or queries by `branch_id` MUST call
  `validate_branch_access(current_user, branch_id)` from
  `utils/permissions.py` before processing. Superusers and admins
  bypass the check; users with an empty `allowed_branches` list are
  unrestricted; all others MUST be restricted to their assigned
  branches. Warehouse-bound operations MUST resolve
  warehouse → branch and validate. Company-wide configuration
  endpoints and user-scoped endpoints are exempt.
- **Branch Filtering Enforcement**: New routers MUST use a dependency
  or decorator that automatically extracts and validates `branch_id`.
  Warehouse-bound endpoints MUST use `resolve_warehouse_branch()`
  from `utils/permissions.py`.

### V. Regulatory Compliance (NON-NEGOTIABLE)

AMAN MUST comply with Saudi Arabian regulatory requirements across all
applicable modules.

- **ZATCA**: VAT calculations (15% standard rate), tax basis,
  e-invoicing rules, and gross-up logic MUST be correctly implemented
  in all sales, purchase, and return flows.
- **Withholding Tax (WHT)**: WHT deduction at source MUST follow
  `WhtRate` and `WhtTransaction` models. Capital gains MUST be
  excluded from normal VAT.
- **Tax Regimes**: Country-specific tax rules MUST be configured via
  `TaxRegime` with jurisdiction codes. Branch-level and company-level
  tax settings MUST override defaults where applicable.
- **GOSI/WPS**: Payroll processing MUST enforce GOSI contribution
  rules. GOSI rates MUST be read from the `gosi_settings` table at
  runtime; hardcoded rates are permitted only as fallback defaults.
  WPS payment file generation MUST include mandatory fields (labor
  card number, insurance number, visa status).
- **Zakat**: Zakat calculation methodology MUST follow the documented
  algorithm in `docs/ZAKAT_CALCULATION_METHODOLOGY.md`.
- **ZATCA Header Discount**: When a header-level discount percentage
  is applied to a sales invoice, the tax base for each line MUST
  be proportionally reduced before VAT calculation.
- **Configurability Mandate**: All Saudi regulatory rates,
  thresholds, and percentages MUST be stored as configurable
  settings, not hardcoded constants. Hardcoding is permitted only
  as a documented fallback when settings are absent.
- **Test Coverage**: Adding or modifying ZATCA, GOSI, WHT, Zakat, or
  Saudization logic without corresponding test coverage is forbidden.
- Tax return and compliance reports MUST be accurate and auditable.

### VI. Concurrency Safety

Concurrent operations on shared resources MUST be explicitly protected
against race conditions.

- Inventory transfers and treasury inter-account movements MUST use
  row-level `SELECT ... FOR UPDATE` locks.
- Optimistic locking (version columns) MUST be used where row-level
  locks are impractical (e.g., `Party.version`).
- Balance-affecting operations MUST be atomic within a single database
  transaction.
- Credit limit enforcement MUST check
  `customer_balance + order_total <= credit_limit` atomically at
  sales order posting time.
- BOM component reservation MUST atomically decrement available
  inventory when a manufacturing order is released.
- Three-way match (PO quantity = receipt quantity = invoice quantity)
  MUST be validated before payment authorization.

### VII. Simplicity & Maintainability

Prefer the simplest solution that satisfies requirements. Complexity
MUST be justified.

- **SQL-First Implementation**: The established pattern uses
  `db.execute(text(...))` with parameterized queries. SQLAlchemy ORM
  models define schema and relationships. New code MUST follow this
  pattern unless ORM query-building demonstrably reduces complexity.
  Pydantic models MUST be used at API boundaries.
- New abstractions require demonstrated need (three or more use cases).
- Centralize shared logic rather than duplicating across modules.
- Follow existing conventions: `snake_case` in Python, `camelCase`
  in JavaScript/React.
- Use structured logging (`logger.error()`, not `print()`). All
  `print()` statements in production code are forbidden.
- Virtual lists (`VirtualList` component) MUST be used when rendering
  1,000+ rows.
- New high-cardinality filter columns MUST get database indexes.
- Pagination default is 25 rows, configurable up to 100.
- **Frontend standards**: See `docs/FRONTEND_STYLE_GUIDE.md` for
  component mandates, cell rendering standards, and page checklists.

### VIII. Inventory Integrity

All inventory movements MUST maintain accurate stock levels and full
traceability.

- UOM validation MUST be enforced on every inventory movement:
  quantity MUST be divisible by the product's base unit.
- Stock availability formula:
  `qty_available = qty_on_hand - qty_reserved - qty_damaged`.
  All queries MUST use this formula, never `qty_on_hand` alone.
- FIFO costing MUST be enforced via `batch_serial_movements`.
- Costing policies (FIFO, LIFO, Weighted Average) are configured per
  company via `CostingPolicy`; policy changes MUST generate
  `CostingPolicyHistory` records and `InventoryCostSnapshot` entries.
- Stock adjustments MUST automatically generate variance journal
  entries through the GL service.
- Inter-warehouse transfers MUST track transit status and MUST NOT
  reduce source stock until shipment confirmation.
- Cycle count variances MUST trigger auto-adjustment entries.
- Bin location management MUST track `BinInventory` per
  warehouse-bin-product combination.
- Batch and serial traceability MUST be enforced for products
  flagged as batch-tracked or serial-tracked.
- Quality inspections (`QualityInspection`) MUST gate receipt into
  available stock for configured product categories.

### IX. Procurement Discipline

Procurement processes MUST enforce controls from requisition through
payment.

- Purchase orders MUST support both discounts and markups at line
  and total level (`effect_type`: discount/markup).
- Landed costs MUST be allocated to received line items based on
  quantity or value, via `LandedCostAllocation`.
- Three-way match (PO ↔ GRN ↔ supplier invoice) MUST be validated
  before payment is authorized. Variance tolerance is configurable.
- Blanket purchase agreements (`PurchaseAgreement`) MUST track
  consumed quantities against agreement limits.
- Supplier rating (`SupplierRating`) on quality, delivery, and price
  MUST be maintained and MUST influence future PO approval workflows.
- Payment terms MUST auto-calculate due date from
  `invoice_date + payment_days`.

### X. Manufacturing Execution

Manufacturing processes MUST enforce BOM accuracy, routing sequences,
and capacity constraints.

- BOM consumption MUST automatically reduce component inventory when
  a manufacturing order is completed.
- Scrap allowance MUST be factored into output quantity:
  `output_qty = required_qty / (1 - scrap_rate%)`.
- Work order routing MUST enforce sequence: step N cannot start
  until step N-1 is marked complete.
- Capacity checks (`ResourceCapacity` vs. `ResourceUtilization`)
  MUST be validated before releasing a work order.
- Job cards MUST track per-operation data: quantity produced, scrap,
  and downtime at the shop-floor level.
- Manufacturing order status MUST follow the state machine:
  `draft → planned → released → in_progress → completed`.

### XI. HR & Payroll Compliance

HR and payroll processes MUST enforce legal requirements and maintain
employee data integrity.

- Salary structure: `basic_salary + allowances - deductions =
  net_salary`. Multi-currency payroll MUST lock exchange rates at
  period-end.
- Payroll period status MUST follow: `draft → calculated → locked`.
  No modifications after locking.
- Leave balance MUST decrement on approval and reset on fiscal
  year-end per leave type configuration.
- Employee termination MUST close all pending leaves and generate
  end-of-service benefit calculations.
- WPS compliance fields (labor card number, insurance number, visa
  status) MUST be mandatory for Saudi-based employees.
- GOSI contribution calculations MUST follow the configured rate
  tables.
- Employee documents MUST track expiry dates for compliance alerting.
- Employee custody (company assets) MUST be tracked and reconciled
  at termination.
- Recruitment pipeline (`JobOpening` → `JobApplication`) MUST track
  status through the hiring workflow.

### XII. Asset Lifecycle Management

Fixed assets MUST be tracked from acquisition through disposal with
accurate depreciation and valuation.

- Depreciation calculation:
  `monthly_depreciation = (cost - salvage_value) / (useful_life_years * 12)`.
- Depreciation schedules MUST be pre-generated at asset creation via
  `AssetDepreciationSchedule`.
- Asset disposal MUST trigger derecognition journal entries through
  the GL service.
- Asset revaluation MUST adjust both the asset carrying value and
  equity (revaluation surplus/deficit).
- Impairment write-downs MUST reduce carrying value to fair value
  with corresponding journal entries.
- Asset transfers MUST be logged via `AssetTransfer`.
- Asset insurance policies MUST track policy numbers and expiry dates.
- Maintenance history MUST be recorded with cost tracking per asset.

### XIII. Sales & CRM Workflow

Sales processes MUST follow a controlled workflow from quotation to
collection with CRM pipeline management.

- Sales workflow MUST follow the state machine:
  `Quotation → Sales Order → Delivery Order → Invoice → Receipt`.
  Skipping states is forbidden.
- Customer credit limit MUST be enforced at SO posting:
  `customer_balance + order_total > credit_limit` blocks the order.
- Sales commissions MUST be calculated per invoice and paid only
  after collection.
- Customer-specific pricing (`CustomerPriceList`) MUST override
  standard prices when configured.
- Party groups MUST support discount/markup with configurable scope.
- A `Party` entity can be both customer AND supplier simultaneously.
- CRM opportunity pipeline MUST track stages:
  `lead → proposal → negotiation → won/lost` with probability
  percentages and expected close dates.
- Lead scoring rules MUST auto-calculate lead quality scores.
- Sales targets MUST be trackable per salesperson.
- Customer segmentation MUST support targeted campaigns.

### XIV. Approval Workflow Governance

Business transactions requiring authorization MUST go through
configured approval workflows.

- Multi-level approval MUST be supported: configurable number of
  required approvers per document type.
- Approval MUST be sequential: a level cannot approve if the
  previous level has rejected.
- Every approval action MUST be logged in `ApprovalAction` with
  timestamp, approver, action, and comments.
- Rejection MUST loop the workflow back to the preparer.
- Approval status MUST follow: `pending → approved/rejected`.

### XV. Project & Contract Management

Projects MUST track scope, budget, and execution with full cost
visibility.

- Project budget variance (`planned - actual`) MUST be tracked and
  surfaced in dashboards.
- Task percent complete MUST roll up to project-level progress.
- Task dependencies MUST prevent out-of-order execution.
- Contract types MUST support fixed-price and time-and-materials
  billing models.
- Project expenses MUST be logged with receipt references and
  linked to cost types.
- Project phases/milestones MUST track planned vs. actual dates.

### XVI. POS Operations

Point-of-sale operations MUST maintain session integrity, support
multi-tender payments, and integrate with inventory and accounting.

- POS sessions MUST track opening and closing balances per
  shift/user/warehouse.
- Multi-tender payment MUST be supported (cash, card, credit) via
  `PosOrderPayment`.
- POS returns MUST validate quantity and UOM against the original
  order.
- Loyalty programs MUST track points accumulation and redemption.
- Table management (restaurant/F&B) MUST support pre-ordering with
  KDS workflow: `pending → preparing → ready`.
- POS promotions MUST be applied at order time and reflected in the
  journal entries.
- Session closure MUST reconcile actual cash vs. system balance.

### XVII. Observability & Audit Trail

All state-changing operations MUST be observable and auditable.

- **AuditMixin**: All domain models MUST use `AuditMixin` to
  populate `created_at`, `updated_at`, `created_by`, and
  `updated_by` fields automatically. No exceptions.
- **SoftDeleteMixin**: All domain models that represent business
  entities MUST use `SoftDeleteMixin` in addition to `AuditMixin`.
  Physical DELETE on soft-deletable tables is forbidden. All
  queries on soft-deletable entities MUST filter
  `is_deleted = false` by default. Exceptions: (a) pure
  junction/mapping tables, (b) append-only log/event tables.
- `AuditLog` entries MUST record user, action, resource, and changes
  (JSONB diff) for all state-changing API calls.
- Backup history MUST be tracked via `BackupHistory`.
- Email communications MUST use `EmailTemplate`.
- Custom reports (`CustomReport`) MUST be user-definable without
  code changes.
- Notifications MUST support multiple channels: in-app, WebSocket,
  webhook, and email.

### XVIII. Session Contract & API Consistency

The login and session endpoints define the application's runtime
contract.

- **Login Response** (`POST /api/auth/login`): MUST return a JSON
  body containing at minimum: `access_token`, `refresh_token`,
  `token_type`, `user` object with `{id, username, full_name, email,
  role, company_id, permissions, enabled_modules, allowed_branches,
  industry_type, currency, decimal_places, timezone}`. Removing or
  renaming existing fields is a MAJOR breaking change.
- **Me Endpoint** (`GET /api/auth/me`): MUST return the same `user`
  shape as the login response.
- **Frontend Contract**: `AuthContext` MUST store the full user
  object from login. `BranchContext` MUST derive from
  `user.allowed_branches`. `useIndustryType()` MUST derive from
  `user.industry_type`. New session-dependent contexts MUST source
  from the login/me contract.
- **Module Guard**: Route visibility MUST be gated by
  `user.enabled_modules`, not by hardcoded role or industry checks.
- **Backend Sync**: Both login and `/me` endpoints MUST be updated
  simultaneously when user payload fields change.

### XIX. Calculation Centralization (NON-NEGOTIABLE)

Every business calculation (tax, discount, balance, cost, commission,
depreciation, payroll) MUST have exactly ONE canonical implementation.
Duplicate calculation logic across routers, services, or frontend is
a critical defect.

- Tax computation (VAT, WHT, gross-up) MUST be performed by a single
  shared utility. Routers MUST NOT inline tax math — they MUST call
  the canonical function.
- Discount and markup application (line-level, header-level,
  proportional distribution) MUST be centralized in a shared
  calculator. Reimplementing discount math per-router is forbidden.
- Account balance derivation MUST use a single canonical method.
  Multiple independent balance queries (running column vs. SUM of
  journal lines) MUST NOT be used interchangeably — one MUST be
  designated as the source of truth, and the other MUST be treated
  as a cache that is periodically reconciled.
- Invoice total calculation (subtotal, tax, discount, rounding) MUST
  use a shared `compute_invoice_totals()` function. Sales invoices,
  purchase invoices, POS orders, credit notes, and debit notes MUST
  all derive totals from this single function.
- Frontend MUST NOT perform monetary calculations. All amounts MUST
  arrive pre-calculated from the backend. Frontend MAY perform
  display-only formatting (e.g., `formatNumber()`).
- When a calculation bug is fixed, the fix MUST propagate to all
  consumers automatically because the logic lives in one place. If a
  fix requires touching multiple files, the calculation was
  duplicated and MUST be consolidated first.

### XX. Report Consistency & Reconciliation (NON-NEGOTIABLE)

Every financial report MUST be derivable from and reconcilable with
the general ledger. Reports that disagree with GL or with each other
are a critical defect.

- **Trial Balance = GL**: The trial balance report MUST equal
  `SUM(debit) - SUM(credit)` from `journal_lines` grouped by
  account, filtered by the same fiscal period. Any discrepancy
  indicates a data integrity failure.
- **Subledger Reconciliation**: AR aging totals MUST equal the
  GL receivables account balance. AP aging totals MUST equal the
  GL payables account balance. Inventory valuation report totals
  MUST equal the GL inventory account balance. These reconciliations
  MUST be verifiable on demand.
- **Report Query Source**: Reports MUST query `journal_lines` and
  source tables directly — never from cached or denormalized
  summaries unless the cache is proven current. If a report uses
  a materialized view or cached aggregate, the report MUST display
  the cache timestamp and offer a "recalculate" option.
- **Same Parameters = Same Results**: A report executed with
  identical parameters (date range, filters, company) MUST return
  identical results regardless of which endpoint, page, or export
  format triggers it. Dashboard widgets, report pages, and Excel
  exports for the same data MUST share the same query function.
- **Period Boundaries**: Reports MUST respect fiscal period
  boundaries. A report for "Q1 2026" MUST include only transactions
  posted within Q1's open dates, regardless of `created_at`
  timestamps.
- **Multi-Currency Reports**: Reports displaying multi-currency data
  MUST clearly separate functional currency totals from foreign
  currency amounts. Mixing currencies in a single total column is
  forbidden.

### XXI. Cross-Module Data Consistency

Shared entities used across modules MUST have a single canonical
source. Conflicting representations of the same entity across
modules are a defect.

- **Party as Single Source**: `Party` (customer/supplier) data MUST
  be read from the `parties` table everywhere. Modules MUST NOT
  maintain shadow copies of party name, tax ID, or address. If a
  party's name changes, all modules MUST reflect the change
  immediately via FK joins — not via denormalized columns that
  require sync jobs.
- **Product Catalog**: Product name, UOM, tax category, and costing
  policy MUST be read from the `products` table. Modules (POS,
  inventory, sales, purchases) MUST NOT store local copies of
  product attributes that can drift.
- **Account References**: When a module references a GL account
  (e.g., revenue account on an invoice, COGS account on inventory),
  it MUST store only the `account_id` FK. The account code, name,
  and type MUST be resolved at query time via join.
- **Exchange Rates**: All modules requiring currency conversion MUST
  read rates from the same `exchange_rates` table using the same
  date-lookup logic. Per-module exchange rate lookups with different
  date semantics are forbidden.
- **Configuration Cascade**: Company-level settings MUST be the
  default. Branch-level overrides MUST take precedence when present.
  Modules MUST NOT query settings from different tables or with
  different fallback logic.

### XXII. Transaction Validation Pipeline

Every financial mutation (invoice, payment, journal entry, stock
movement, payroll run) MUST pass through a standardized validation
sequence before persistence. Ad-hoc validation scattered across
routers is insufficient.

- **Validation Order**: All financial transactions MUST validate in
  this sequence: (1) schema validation (Pydantic), (2) permission
  check, (3) fiscal period open, (4) business rules (credit limit,
  stock availability, budget, approval status), (5) calculation
  correctness (totals balance, tax correct), (6) persist, (7)
  post-persist side effects (GL entry, notifications).
- **Fail-Fast**: Validation MUST fail at the earliest possible stage.
  A transaction blocked by fiscal period MUST NOT proceed to credit
  limit checking. Errors MUST accumulate within a stage (report all
  failing business rules at once, not one at a time).
- **Validation Reuse**: The same validation logic MUST apply
  regardless of entry point. A sales invoice created via API, POS,
  or bulk import MUST pass the same validation pipeline. Per-entry-
  point validation shortcuts are forbidden.
- **Draft Bypass**: Draft-status documents MAY skip business rule
  validation (stages 4-5) but MUST still pass schema and permission
  validation. Transitioning from draft to posted MUST trigger the
  full pipeline.
- **Amount Reconciliation**: Before persisting any document with
  lines, the sum of line amounts MUST be validated against the
  document header total. Line-header discrepancies MUST block
  persistence.

### XXIII. Idempotency & Duplicate Prevention

Mutation endpoints MUST be safe to retry. Duplicate business
documents (payments, invoices, orders) caused by double-submission
are a critical defect.

- **Idempotency Keys**: All payment, invoice creation, and order
  creation endpoints MUST accept an optional `idempotency_key`
  header. If a request with the same key has already been processed,
  the endpoint MUST return the original response without creating a
  duplicate. Keys MUST be stored with a TTL (minimum 24 hours).
- **Duplicate Detection**: Before creating an invoice or payment,
  the system MUST check for an existing document with the same
  `(party_id, amount, date, reference)` tuple within a configurable
  window (default: 5 minutes). Matches MUST trigger a confirmation
  prompt, not silent creation.
- **Sequence Number Gaps**: Document sequence numbers (invoice_number,
  po_number, so_number) MUST be generated atomically via
  `SELECT ... FOR UPDATE` on the sequence counter. Gaps caused by
  rollbacks are acceptable; duplicates are not.
- **Frontend Double-Submit Guard**: All mutation buttons MUST be
  disabled after the first click until the server responds. The
  shared API client MUST enforce this — per-page implementation is
  forbidden.
- **Bulk Import Deduplication**: Data import endpoints MUST detect
  and skip rows that match existing records by natural key (e.g.,
  invoice_number, party_code). Import results MUST report created,
  skipped, and failed row counts.

### XXIV. Data Lifecycle Governance

Business data MUST follow defined retention, archival, and purge
rules. Uncontrolled data growth degrades performance and violates
compliance requirements.

- **Retention Periods**: Audit logs MUST be retained for a minimum of
  7 years (Saudi regulatory requirement). Soft-deleted records MUST
  be retained for a minimum of 1 fiscal year before archival
  eligibility.
- **Archival**: Records older than the configurable retention period
  MUST be archivable to a separate archive schema or database.
  Archived records MUST remain queryable for compliance but MUST NOT
  appear in operational queries or reports by default.
- **Restore**: Soft-deleted records MUST be restorable
  (`is_deleted = false`, `deleted_at = null`, `deleted_by = null`)
  within the retention period. Restore MUST be logged in `AuditLog`.
  Restoring a document MUST re-validate it against current business
  rules (fiscal period, stock availability).
- **Transient Data Cleanup**: Expired sessions, used OTP codes,
  consumed idempotency keys, and stale cache entries MUST be purged
  by a scheduled job. Purge frequency MUST be configurable.
- **Attachment Storage**: File uploads (invoice scans, employee
  documents, logo images) MUST track file size and MIME type. Total
  storage per company MUST be monitorable. Orphaned attachments
  (referenced by soft-deleted records only) MUST be flagged for
  review, not auto-deleted.

### XXV. Performance & Query Discipline

Database queries MUST be efficient, reusable, and predictable.
Uncontrolled query patterns degrade system performance under
production load.

- **N+1 Prevention**: Endpoints returning lists with related data
  MUST use JOINs or batch queries. Executing a query per row in a
  loop (N+1 pattern) is forbidden. Code review MUST flag loops
  containing `db.execute()`.
- **Query Reuse**: When multiple endpoints need the same data shape
  (e.g., "invoice with lines and party details"), they MUST share a
  common query function in the service or utils layer. Copy-pasting
  SQL across routers is forbidden.
- **Unbounded Queries**: Every list endpoint MUST enforce pagination.
  Queries without `LIMIT` on tables that can exceed 1,000 rows are
  forbidden. Export endpoints MAY bypass pagination but MUST use
  streaming (chunked response or cursor-based iteration).
- **Heavy Aggregations**: Dashboard and report queries that perform
  full-table scans with GROUP BY MUST be profiled. Queries exceeding
  2 seconds on representative data MUST be optimized (index,
  materialized view, or pre-aggregation via scheduler).
- **Connection Discipline**: Every database session MUST be closed
  after request completion. Long-held connections (e.g., forgetting
  to yield from a generator) are forbidden. The `get_db` dependency
  MUST handle session lifecycle.

### XXVI. Calculation Traceability

Financial calculations MUST be traceable — not just the result, but
the inputs, method, and intermediate values that produced it.

- **Tax Breakdown**: Every tax amount on an invoice line MUST be
  stored with: tax_rate applied, taxable_base, tax_amount, tax
  regime reference, and whether the rate was overridden. Storing
  only the final tax amount without the computation trail is
  forbidden.
- **Discount Trace**: Every discount applied MUST record: source
  (header %, line %, customer price list, promotion), original
  amount, discount amount, and net amount. Post-hoc reconstruction
  of how a discount was derived MUST be possible from stored data
  alone.
- **Exchange Rate Audit**: Every multi-currency transaction MUST
  store: source_currency, target_currency, rate_used, rate_date,
  and rate_source (manual entry vs. system table). Relying on
  re-fetching the rate at query time to reconstruct the original
  transaction is forbidden.
- **Payroll Calculation Log**: Each payroll run MUST store per-
  employee: basic_salary, each allowance (name + amount), each
  deduction (name + amount + rule reference), GOSI employee share,
  GOSI employer share, and net_salary. Summary-only payroll records
  (just net_salary) are insufficient for audit.
- **Costing Trace**: Inventory costing events (FIFO layer
  consumption, weighted average recalculation) MUST log: previous
  cost, new cost, quantity affected, and trigger event (receipt,
  return, adjustment). Cost changes without trace records are
  forbidden.

### XXVII. UI/UX Behavioral Consistency (NON-NEGOTIABLE)

All pages MUST exhibit identical behavioral patterns for the same
interaction type. Users MUST NOT experience different behaviors
for the same action across different modules.

- **Table Behavior**: Every `DataTable` instance MUST support:
  server-side pagination (default 25 rows), column sorting (at
  least on date and amount columns), and a search input that
  filters on the primary text column. Tables that omit any of
  these are non-compliant. Pagination controls, sort indicators,
  and empty-state messages MUST look and behave identically
  everywhere.
- **Table Export**: Every list page MUST offer an Excel/CSV export
  action that exports the full filtered dataset (not just the
  current page). Export MUST use the same query function as the
  list endpoint (Principle XX — same parameters, same results).
- **Form Validation UX**: All form validation errors MUST appear
  inline under the offending field using the `FormField` error
  slot. Errors MUST appear on submit attempt, not on first
  keystroke. After a failed submit, subsequent changes to the
  failing field MUST clear its error in real-time. Top-of-form
  error banners, `alert()` popups, or toast-only validation
  feedback are forbidden.
- **Error Message Consistency**: User-facing error messages MUST
  use translated keys from `en.json`/`ar.json`. Showing raw
  backend error strings, HTTP status codes, or generic "Something
  went wrong" without a translatable key is forbidden. Error
  messages for the same failure type (e.g., "field required",
  "invalid email", "insufficient stock") MUST use the same i18n
  key across all modules.
- **Loading & Skeleton States**: Every page that fetches data MUST
  show `PageLoading` (or DataTable's built-in skeleton) during
  initial load. Subsequent in-page actions (save, delete) MUST
  show a loading indicator on the action button, not a full-page
  spinner. No page may render empty content without a loading or
  empty-state indicator.
- **Confirmation Dialogs**: Destructive actions (delete, void,
  cancel, reverse) MUST use a shared `ConfirmDialog` component
  with a clear description of the consequences. Per-module custom
  confirmation modals are forbidden. The dialog MUST require
  explicit confirmation text for high-impact actions (e.g.,
  voiding a posted invoice).
- **Filter Persistence**: When a user navigates away from a list
  page and returns (via back button or breadcrumb), applied filters,
  sort order, and current page MUST be restored. Losing filter
  state on navigation is a UX defect.
- **Spacing & Layout Rhythm**: All pages MUST follow the same
  vertical rhythm: workspace header → filters/actions bar →
  content area → pagination. Inserting extra containers, custom
  margins, or ad-hoc spacing between these zones is forbidden.
  See `docs/FRONTEND_STYLE_GUIDE.md` for component-level details.

### XXVIII. Schema Definition Synchronization (NON-NEGOTIABLE)

The multi-tenant architecture creates company databases dynamically
via `database.py` CREATE TABLE definitions. Migrations only apply
to existing company databases. Therefore, schema changes MUST be
synchronized in both locations.

- **Dual Update Rule**: When adding, removing, or modifying any
  table, column, index, or constraint, the change MUST be applied
  in BOTH:
  1. A migration file (`backend/migrations/`) — for existing companies
  2. `backend/database.py` CREATE TABLE definitions — for new companies
  Applying a change in only one location creates schema drift
  between old and new company databases, which is a critical defect.
- **Column Additions**: New columns MUST appear in the base CREATE
  TABLE statement in `database.py` with the same type, default, and
  nullability as the migration's ALTER TABLE ADD COLUMN.
- **Column Removals**: Dropped columns MUST be removed from the
  CREATE TABLE statement in `database.py` and dropped via migration.
- **Index Changes**: New indexes MUST appear in both the migration
  and the index section of `database.py`. Index filters (WHERE
  clauses) MUST be identical in both locations.
- **Table Additions/Removals**: New tables MUST be added to
  `database.py`'s schema initialization. Removed tables MUST be
  dropped via migration and removed from `database.py`.
- **Verification**: Before marking a schema change complete, the
  developer MUST verify that a freshly created company database
  would have an identical schema to an existing database that has
  run all migrations.

## Technology Stack & Constraints

| Layer | Technology | Constraint |
|-------|-----------|------------|
| Backend | Python 3.12 / FastAPI | All endpoints via FastAPI routers |
| Frontend | React 18 / Vite | JSX, i18next for AR/EN, RTL support |
| Mobile | React Native 0.76 | React Navigation, Firebase, AsyncStorage |
| Database | PostgreSQL 15 | One DB per company tenant + system DB |
| ORM | SQLAlchemy 2.0 | Schema definitions; SQL-first query style |
| Cache | Redis | Rate limiting, session management, token blacklist |
| Auth | JWT (Bearer token) + TOTP | localStorage + Axios interceptor, pyotp for 2FA |
| Container | Docker + Nginx | Docker Compose orchestration, SSL/TLS |
| Production | Gunicorn + Uvicorn workers | Behind Nginx reverse proxy |
| Monitoring | Prometheus + Grafana | /metrics endpoint, internal-only access |
| Validation | Pydantic | All request/response bodies schema-validated |

- Backend and frontend MUST remain deployable independently.
- New Python dependencies MUST be added to `backend/requirements.txt`.
- Database schema changes MUST go through Alembic migrations; manual
  DDL against production is forbidden.
- All Pydantic schemas MUST return 422 on validation failure.
- **API Response Shapes**: New endpoints MUST use Pydantic
  `response_model` declarations. Within a module, new endpoints MUST
  NOT introduce a response shape that conflicts with the module's
  established pattern.
- **Industry Templates**: See `docs/INDUSTRY_TEMPLATES.md` for the
  supported industry types and their module configurations.

## Data Integrity Constraints

### Database-Level Enforcement

- Indexes MUST exist on high-cardinality, frequently-filtered columns.
- Foreign key constraints MUST specify `CASCADE`, `SET NULL`, or
  `RESTRICT` delete rules as appropriate.
- Check constraints: debit >= 0 and credit >= 0 on journal lines;
  start_date <= end_date on projects/phases; quantity >= 0 on
  inventory and orders.
- Unique constraints: account_number, party_code, invoice_number,
  rfq_number, po_number, so_number, entry_number — all unique per
  company database.
- Constraint trigger (`trg_journal_balance`): DEFERRABLE INITIALLY
  DEFERRED — validates debit = credit per entry at transaction commit.

### Application-Level Enforcement

- All endpoints MUST validate input via Pydantic schemas.
- Business rule validators (credit limit, fiscal period, UOM
  consistency, balance check) MUST run before database writes.
- Optimistic locking via version columns MUST be used on
  high-contention entities.

### Model & Schema Integrity

ORM models, DDL functions, and Alembic migrations MUST remain
synchronized at all times.

- **Model Registration**: Every new SQLAlchemy model MUST be
  imported in `backend/models/__init__.py` AND listed in the
  `__all__` tuple.
- **DDL-ORM Parity**: Every column, type, length, default, and
  constraint in the ORM model MUST have a matching definition
  in the corresponding DDL function.
- **FK `ondelete` Parity**: Every `ForeignKey()` declaration
  in ORM models MUST include an explicit `ondelete` argument.
  The DDL function MUST specify the matching `ON DELETE` clause.
- **Relationship Completeness**: Every `ForeignKey` column MUST
  have a corresponding bidirectional `relationship()` with
  `back_populates`. Lazy-load strategy MUST be explicit for
  models with 5+ relationships.
- **Migration Coverage**: Every DDL table addition MUST have a
  corresponding Alembic migration.
- **Audit Columns in DDL**: Tables for models using `AuditMixin`
  MUST include audit columns. Tables using `SoftDeleteMixin` MUST
  additionally include soft-delete columns.

## Deployment & Infrastructure

- **Docker Compose** orchestrates all services.
- **Nginx** handles SSL/TLS termination, gzip compression, API
  reverse proxy, static asset caching, and per-IP rate limiting.
- Backend and frontend containers MUST be independently rebuildable.
- Database backups MUST be tracked via `BackupHistory` model.
- Background tasks run via `services/scheduler.py`.

## Quality Gates

1. **Testing**: pytest is the test framework. Tests MUST cover
   authentication, permission boundaries, fiscal enforcement, journal
   balance validation, and UOM consistency for any new transactional
   endpoint.
2. **Migrations**: Every schema change MUST have an idempotent
   Alembic migration that works across all active company databases.
3. **Code Review**: Changes to GL service, permission decorators,
   multi-tenant routing, or approval workflows MUST receive explicit
   review attention.
4. **Internationalization**: New user-facing strings MUST have entries
   in both `en.json` and `ar.json`. Default language is Arabic.
5. **Frontend Testing**: Every new frontend page handling auth,
   permissions, branch state, or i18n switching MUST have at least
   one integration test using Vitest + React Testing Library.
6. **PR Merge Gate Checklist**: Before merging, verify:
   - [ ] No new `float` usage for monetary values
   - [ ] No new `detail=str(e)` error leakage
   - [ ] All new endpoints have `validate_branch_access()` if
         accepting `branch_id`
   - [ ] All new models use `AuditMixin` + `SoftDeleteMixin`
   - [ ] All `ForeignKey()` have explicit `ondelete`
   - [ ] All new user-facing strings in both `en.json` + `ar.json`
   - [ ] All new compliance logic has test coverage
   - [ ] Session contract (login/me) updated if payload changed
   - [ ] Response shape matches module's established pattern
   - [ ] Alembic migration included for schema changes
   - [ ] No duplicated calculation logic (tax, discount, totals)
   - [ ] Idempotency key supported on payment/invoice/order endpoints
   - [ ] Tax/discount/exchange rate breakdown stored, not just totals

## Governance

This constitution is the authoritative reference for architectural and
quality decisions in AMAN ERP.

- **Amendments**: Any change MUST be documented with a version bump
  and rationale.
- **Versioning**: Follows semantic versioning — MAJOR for principle
  removal/redefinition, MINOR for new principles, PATCH for
  clarifications.
- **Compliance Review**: Each feature spec and implementation plan
  MUST include a Constitution Check verifying alignment with all
  active principles.
- **Guidance**: For runtime development guidance, refer to
  `docs/SYSTEM_KNOWLEDGE_BASE.md` and `docs/MODULE_AUDIT_REPORT.md`.

**Version**: 1





.1.0 | **Last Amended**: 2026-04-14
