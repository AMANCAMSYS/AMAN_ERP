<!--
  Sync Impact Report
  ==================
  Version change: 2.1.0 → 2.2.0
  Bump rationale: MINOR — materially expanded guidance in
    three existing areas (IV branch filtering, VII-A cell
    design, Model & Schema Integrity FK rules) and added new
    sub-section VII-B (Cell & Column Rendering Standards).
    Motivated by codebase audit finding 335 FKs without
    explicit ondelete, 16 routers missing branch validation,
    and fragmented table cell styling across manual-table
    pages vs DataTable pages.
  Modified principles:
    - IV. Security & Access Control — strengthened: branch
      filtering now MUST be enforced via middleware or
      decorator pattern, not ad-hoc per-endpoint calls;
      warehouse-to-branch resolution MUST use a centralized
      helper; 16 non-compliant routers identified for
      remediation
    - VII-A. Frontend Component Mandates — strengthened:
      all list pages MUST migrate to DataTable (manual
      <table> elements forbidden on list pages)
    - Model & Schema Integrity — strengthened: every
      ForeignKey() declaration MUST include an explicit
      ondelete argument; relationship() back_populates
      MUST be defined on both sides; 335 FK refs identified
      for remediation
  Added sections:
    - VII-B. Cell & Column Rendering Standards (cell render
      functions, status badge mapping, currency cell pattern,
      code/ID cell pattern, date cell pattern, action column
      pattern)
  Modified sections:
    - Development Workflow & Quality Gates — added gates
      #14 (Cell Design Checklist), #15 (FK ondelete Audit)
  Removed sections: None
  Templates requiring updates:
    - .specify/templates/plan-template.md — ✅ reviewed
      (Constitution Check table is dynamic; new sub-rules
      auto-populate under existing principles IV, VII)
    - .specify/templates/spec-template.md — ✅ reviewed
      (no structural changes needed)
    - .specify/templates/tasks-template.md — ✅ reviewed
      (phase structure accommodates new quality-gate tasks)
  Follow-up TODOs:
    - Retroactive remediation of 335 FK ondelete clauses
    - Retroactive remediation of 16 routers missing
      validate_branch_access
    - Migration of manual-table pages to DataTable with
      standardized cell rendering
    - Retroactive remediation of 13 Phase 2–6 pages and
      13 ORM models (carried from v2.1.0)
-->

# AMAN ERP Constitution

## Core Principles

### I. Financial Precision (NON-NEGOTIABLE)

All monetary values MUST use `Decimal` types with deterministic
rounding. Floating-point arithmetic (`float`, `double`) is forbidden
for any amount, rate, or balance calculation.

- Every SQL column storing money MUST be `NUMERIC(18,4)` or narrower.
  Four decimal places are the minimum for SAR sub-unit precision.
- Python code MUST use `decimal.Decimal` with `ROUND_HALF_UP`.
  JavaScript code MUST use string-based amounts or a fixed-point
  library (never native `Number` for currency math).
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

**Rationale**: ERP financial integrity depends on deterministic
arithmetic. A single floating-point drift can cascade through journal
entries, tax returns, and regulatory filings.

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
- The engine cache MUST be bounded (currently max 50 LRU entries) to
  prevent connection exhaustion under high tenant load.
- Alembic migrations MUST target individual company databases via
  `alembic -x company=<id> upgrade head`.
- New company creation MUST auto-apply all migrations to HEAD.
- Migrations MUST be idempotent (`CREATE TABLE IF NOT EXISTS`,
  conditional column adds) to safely re-run.

**Rationale**: Multi-tenant ERP systems handle sensitive financial,
payroll, and tax data. Isolation failures are compliance violations.

### III. Double-Entry Integrity (NON-NEGOTIABLE)

Every financial transaction MUST produce balanced journal entries
(total debits = total credits). Unbalanced entries are never
permitted, even temporarily.

- All journal entry creation MUST go through the centralized GL
  service (`services/gl_service.py`). Direct INSERT into
  `journal_entries` or `journal_lines` outside this service is
  forbidden (75 legacy duplicates have been consolidated).
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

**Rationale**: Double-entry bookkeeping is the foundation of
accounting. Violations produce unauditable books and regulatory risk.

### IV. Security & Access Control (NON-NEGOTIABLE)

Authentication and authorization MUST be enforced on every endpoint.

- JWT tokens are stored in HttpOnly cookies with `SameSite=Strict`
  and `Secure` flags. Bearer token headers are NOT used.
- Tokens carry `user_id`, `company_id`, `role`, `permissions`,
  `enabled_modules`, and `allowed_branches`.
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
- Nginx MUST set CSP headers to mitigate XSS. React's auto-escaping
  is necessary but not sufficient alone.
- **Branch-Level Data Filtering**: Every endpoint that accepts,
  stores, or queries by `branch_id` MUST call
  `validate_branch_access(current_user, branch_id)` from
  `utils/permissions.py` before processing the request.
  Superusers and admins bypass the check; users with an empty
  `allowed_branches` list are unrestricted; all others MUST be
  restricted to their assigned branches. Warehouse-bound
  operations MUST resolve warehouse → branch and validate.
  Company-wide configuration endpoints (e.g., SSO config) and
  user-scoped endpoints (e.g., own notifications) are exempt.
- **Branch Filtering Enforcement Pattern**: Branch validation
  MUST NOT be left to ad-hoc per-endpoint implementation.
  New routers MUST use a dependency or decorator that
  automatically extracts and validates `branch_id` from query
  parameters, path parameters, or request body. Warehouse-bound
  endpoints MUST use a centralized `resolve_warehouse_branch()`
  helper (in `utils/permissions.py`) that queries the warehouse's
  `branch_id` and passes it to `validate_branch_access()`.
  Existing routers that accept `branch_id` without calling
  `validate_branch_access()` are non-compliant and MUST be
  remediated. Known non-compliant routers (16 identified):
  `inventory/{shipments, suppliers, reports, warehouses,
  categories, adjustments}`, `sales/{customers, orders,
  quotations, returns, vouchers}`, `finance/reconciliation`,
  `audit`, `hr_wps_compliance`.

**Rationale**: ERP systems are high-value targets containing financial,
payroll, and personal data. Defense-in-depth is mandatory.

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
  tax settings (`BranchTaxSetting`, `CompanyTaxSetting`) MUST
  override defaults where applicable.
- **GOSI/WPS**: Payroll processing MUST enforce GOSI contribution
  rules. WPS payment file generation MUST include mandatory fields
  (labor card number, insurance number, visa status).
- **Zakat**: Zakat calculation methodology MUST follow the documented
  algorithm in `docs/ZAKAT_CALCULATION_METHODOLOGY.md`, including
  deductibility rules and capital gains treatment.
- Tax return and compliance reports MUST be accurate and auditable.

**Rationale**: Non-compliance with Saudi tax and labor regulations
exposes clients to fines, penalties, and operational risk.

### VI. Concurrency Safety

Concurrent operations on shared resources MUST be explicitly protected
against race conditions.

- Inventory transfers and treasury inter-account movements MUST use
  row-level `SELECT ... FOR UPDATE` locks.
- Optimistic locking (version columns) MUST be used where row-level
  locks are impractical (e.g., `Party.version` for customer/supplier
  updates).
- Balance-affecting operations MUST be atomic within a single database
  transaction.
- Credit limit enforcement MUST check
  `customer_balance + order_total <= credit_limit` atomically at
  sales order posting time.
- BOM component reservation MUST atomically decrement available
  inventory when a manufacturing order is released.
- Three-way match (PO quantity = receipt quantity = invoice quantity)
  MUST be validated before payment authorization.

**Rationale**: ERP systems process concurrent transactions across
inventory, treasury, and accounting. Unprotected concurrency produces
phantom balances and data corruption.

### VII. Simplicity & Maintainability

Prefer the simplest solution that satisfies requirements. Complexity
MUST be justified.

- New abstractions require demonstrated need (three or more concrete
  use cases).
- Centralize shared logic (e.g., GL service, DataTable wrapper)
  rather than duplicating across modules. The GL service
  consolidation (75 duplicates → 1 service) is the reference pattern.
- Follow existing conventions: `snake_case` in Python, `camelCase`
  in JavaScript/React.
- Use structured logging (`logger.error()`, not `print()`). All
  `print()` statements in production code are forbidden.
- Virtual lists (`VirtualList` component) MUST be used when rendering
  1,000+ rows.
- Performance: 46 database indexes exist for common query patterns;
  new high-cardinality filter columns MUST get indexes.
- Pagination default is 25 rows, configurable up to 100.

#### VII-A. Frontend Component Mandates

All new frontend pages MUST follow the established design system.
Non-compliance is a blocking defect.

- **Page Layout**: Root element MUST be
  `<div className="workspace fade-in">`. Header MUST use
  `<div className="workspace-header">` containing title in
  `<h1 className="workspace-title">` and optional subtitle in
  `<p className="workspace-subtitle">`. Using `module-container`,
  `page-container`, or bare `<h2>` headers is forbidden.
- **List Pages**: MUST use `DataTable` from
  `../../components/common/DataTable`. Raw `<table>` elements
  are forbidden on pages that display tabular data. DataTable
  provides built-in pagination, loading state, empty state,
  and consistent styling.
- **Search & Filter**: List pages MUST use `SearchFilter` from
  `../../components/common/SearchFilter`. Custom bare `<select>`
  or `<input>` filter elements outside SearchFilter are forbidden.
- **Form Pages**: All form inputs MUST use `FormField` from
  `../../components/common/FormField`. Raw `<label>/<input>`
  pairs without FormField are forbidden. All `<input>` and
  `<select>` elements MUST have `className="form-input"`.
- **Navigation**: Every page (except top-level dashboards) MUST
  include `BackButton` from `../../components/common/BackButton`
  inside the `workspace-header` div.
- **Loading State**: MUST use the shared `PageLoading` component
  (or DataTable's built-in loading). Plain `<p>Loading...</p>`
  or Bootstrap spinners are forbidden.
- **API Client**: All API calls MUST use the shared instance
  from `../../utils/api`. Importing from `../../services/apiClient`
  or creating custom axios instances is forbidden.
- **Number Formatting**: Monetary and numeric display MUST use
  `formatNumber()` from utils. Raw `parseFloat().toLocaleString()`
  is forbidden.
- **Status Badges**: MUST use `badge badge-success`,
  `badge badge-warning`, `badge badge-danger`, `badge badge-info`
  CSS classes. Hardcoded hex color values in badge styles are
  forbidden.
- **RTL Support**: Spacing MUST use CSS logical properties
  (`marginInlineStart`, `marginInlineEnd`, `paddingInlineStart`,
  `insetInlineStart`) instead of physical `marginLeft`,
  `marginRight`, `paddingLeft`, `left`, `right`.
- **i18n Discipline**: All user-facing strings MUST use `t()` from
  `useTranslation()` with keys defined in both `en.json` and
  `ar.json`. Hardcoded English fallback arguments in `t()` calls
  (e.g., `t('key', 'Fallback')`) are forbidden.
- **User Feedback**: MUST use `useToast()` for success/error
  messages. `window.alert()` and `window.confirm()` are forbidden.

#### VII-B. Cell & Column Rendering Standards

All DataTable column `render` functions MUST follow these
standardized patterns. Inline styles for cell content are
forbidden; use CSS utility classes.

- **Status/Badge Cells**: MUST use a centralized status-color
  mapping object (e.g., `STATUS_BADGE_MAP` in `utils/constants`)
  that returns the appropriate `badge badge-{variant}` class.
  Hardcoded `backgroundColor`/`color` inline styles in badge
  rendering are forbidden. Every status value displayed in the
  UI MUST have a corresponding badge class entry.
- **Currency/Monetary Cells**: MUST use `formatNumber(value)` for
  the amount and display currency code in a `<small>` tag after
  the formatted number. Cell text MUST be right-aligned
  (`textAlign: 'end'` logical property). Raw
  `parseFloat().toLocaleString()` is forbidden.
- **Code/ID Cells**: Reference codes (invoice numbers, PO
  numbers, account codes) MUST render with
  `className="code-cell"` which applies monospace font and
  subtle background. Manual `fontFamily: 'monospace'` inline
  styles are forbidden.
- **Date Cells**: MUST use `formatShortDate()` or
  `formatDate()` from utils. Raw `new Date().toLocaleDateString()`
  is forbidden.
- **Action Columns**: MUST be the last column. Action buttons
  MUST use icon buttons with `title` attributes for
  accessibility. Actions MUST use `className="btn-icon"` and
  MUST NOT use inline `onClick` handlers with `window.confirm()`.
- **Boolean/Toggle Cells**: MUST render as status badges
  (`badge badge-success` for true, `badge badge-secondary` for
  false) with translated labels, not raw "true"/"false" strings.
- **Empty/Null Cells**: MUST render `—` (em-dash) for null or
  undefined values, not blank cells or "N/A" strings.
- **Column Widths**: MUST be defined in the column configuration
  object as percentages. Columns MUST NOT rely on auto-sizing
  for tables with 5+ columns.
- **Manual Tables Forbidden**: All pages displaying tabular data
  MUST use `DataTable`. Existing pages with raw `<table>`
  elements MUST be migrated. No new pages may use `<table>`
  directly.

**Rationale**: A 767-endpoint, 240-model system becomes unmaintainable
without strict discipline around simplicity and consistency. The
Phase 1–6 audit found 13 of 14 new pages violating frontend
patterns, causing visual inconsistency and broken RTL layout.
The cell design audit found fragmented badge styling (inline hex
colors vs CSS classes), inconsistent number formatting, and
missing column width definitions across manual-table pages.

### VIII. Inventory Integrity

All inventory movements MUST maintain accurate stock levels and full
traceability.

- UOM validation MUST be enforced on every inventory movement:
  quantity MUST be divisible by the product's base unit.
- Stock availability formula:
  `qty_available = qty_on_hand - qty_reserved - qty_damaged`.
  All queries MUST use this formula, never `qty_on_hand` alone.
- FIFO costing MUST be enforced via `batch_serial_movements` — the
  oldest batch is consumed first.
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
- Quality inspections (`QualityInspection` with criteria) MUST gate
  receipt into available stock for configured product categories.

**Rationale**: Inventory is the physical backbone of operations.
Inaccurate stock levels cascade into failed deliveries, production
stoppages, and financial misstatement.

### IX. Procurement Discipline

Procurement processes MUST enforce controls from requisition through
payment.

- Purchase orders MUST support both discounts and markups at line
  and total level (`effect_type`: discount/markup).
- Landed costs (freight, duty, insurance) MUST be allocated to
  received line items based on quantity or value, via
  `LandedCostAllocation`.
- Three-way match (PO ↔ GRN ↔ supplier invoice) MUST be validated
  before payment is authorized. Variance tolerance is configurable.
- Blanket purchase agreements (`PurchaseAgreement`) MUST track
  consumed quantities against agreement limits.
- Supplier rating (`SupplierRating`) on quality, delivery, and price
  MUST be maintained and MUST influence future PO approval workflows.
- Payment terms MUST auto-calculate due date from
  `invoice_date + payment_days`.

**Rationale**: Uncontrolled procurement leads to cost overruns,
duplicate payments, and supplier disputes.

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

**Rationale**: Manufacturing without BOM and routing discipline
produces waste, inventory discrepancies, and missed delivery dates.

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
- Employee documents (visa, ID, certifications) MUST track expiry
  dates for compliance alerting.
- Employee custody (company assets) MUST be tracked and reconciled
  at termination.
- Recruitment pipeline (`JobOpening` → `JobApplication`) MUST track
  status through the hiring workflow.

**Rationale**: Payroll errors and labor law violations expose the
organization to fines, employee disputes, and regulatory action.

### XII. Asset Lifecycle Management

Fixed assets MUST be tracked from acquisition through disposal with
accurate depreciation and valuation.

- Depreciation calculation:
  `monthly_depreciation = (cost - salvage_value) / (useful_life_years * 12)`.
- Depreciation schedules MUST be pre-generated at asset creation via
  `AssetDepreciationSchedule`.
- Asset disposal MUST trigger derecognition journal entries
  (gain/loss on disposal) through the GL service.
- Asset revaluation MUST adjust both the asset carrying value and
  equity (revaluation surplus/deficit).
- Impairment write-downs MUST reduce carrying value to fair value
  with corresponding journal entries.
- Asset transfers (inter-location, inter-department) MUST be logged
  via `AssetTransfer`.
- Asset insurance policies MUST track policy numbers and expiry dates
  for coverage gap alerting.
- Maintenance history MUST be recorded with cost tracking per asset.

**Rationale**: Misstated asset values distort financial statements and
lead to incorrect depreciation charges and tax filings.

### XIII. Sales & CRM Workflow

Sales processes MUST follow a controlled workflow from quotation to
collection with CRM pipeline management.

- Sales workflow MUST follow the state machine:
  `Quotation → Sales Order → Delivery Order → Invoice → Receipt`.
  Skipping states is forbidden.
- Customer credit limit MUST be enforced at SO posting:
  `customer_balance + order_total > credit_limit` blocks the order.
- Sales commissions MUST be calculated per invoice
  (`invoice_total × commission_rate`) and paid only after collection.
- Customer-specific pricing (`CustomerPriceList`) MUST override
  standard prices when configured.
- Party groups MUST support discount/markup with configurable scope
  (applies to total or per line).
- A `Party` entity can be both customer AND supplier simultaneously
  (`is_customer`, `is_supplier` flags).
- CRM opportunity pipeline MUST track stages:
  `lead → proposal → negotiation → won/lost` with probability
  percentages and expected close dates.
- Lead scoring rules (`CrmLeadScoringRule`) MUST auto-calculate
  lead quality scores.
- Sales targets MUST be trackable per salesperson
  (quarterly/annual).
- Customer segmentation MUST support targeted campaigns via
  `CrmCustomerSegment`.

**Rationale**: Uncontrolled sales processes lead to revenue leakage,
credit losses, and inaccurate forecasting.

### XIV. Approval Workflow Governance

Business transactions requiring authorization MUST go through
configured approval workflows.

- Multi-level approval MUST be supported: configurable number of
  required approvers per document type (`required_approvers_count`).
- Approval MUST be sequential: a level cannot approve if the
  previous level has rejected.
- Every approval action (approve, reject) MUST be logged in
  `ApprovalAction` with timestamp, approver, action, and comments.
- Rejection MUST loop the workflow back to the preparer for
  revision.
- Approval status MUST follow: `pending → approved/rejected`.

**Rationale**: Uncontrolled authorization exposes the organization
to fraud, unauthorized commitments, and compliance violations.

### XV. Project & Contract Management

Projects MUST track scope, budget, and execution with full cost
visibility.

- Project budget variance (`planned - actual`) MUST be tracked and
  surfaced in dashboards.
- Task percent complete MUST roll up to project-level progress.
- Task dependencies (predecessor/successor via `ProjectDependency`)
  MUST prevent out-of-order execution.
- Contract types MUST support fixed-price and time-and-materials
  billing models.
- Project expenses MUST be logged with receipt references and
  linked to cost types for budget tracking.
- Project phases/milestones MUST track planned vs. actual dates.

**Rationale**: Projects without budget and schedule discipline
consistently overrun, eroding margins and client trust.

### XVI. POS Operations

Point-of-sale operations MUST maintain session integrity, support
multi-tender payments, and integrate with inventory and accounting.

- POS sessions MUST track opening and closing balances per
  shift/user/warehouse.
- Multi-tender payment MUST be supported (cash, card, credit) via
  `PosOrderPayment`.
- POS returns MUST validate quantity and UOM against the original
  order.
- Loyalty programs MUST track points accumulation and redemption
  via `PosLoyaltyProgram`, `PosLoyaltyPoint`, `PosLoyaltyTransaction`.
- Table management (restaurant/F&B) MUST support pre-ordering with
  kitchen display system (KDS) workflow:
  `pending → preparing → ready`.
- POS promotions (discounts, bundles) MUST be applied at order time
  and reflected in the journal entries.
- Session closure MUST reconcile actual cash vs. system balance.

**Rationale**: POS is the highest-volume transaction source. Session
and inventory integrity at this point prevents downstream accounting
and stock discrepancies.

### XVII. Observability & Audit Trail

All state-changing operations MUST be observable and auditable.

- **AuditMixin**: All domain models MUST use `AuditMixin` to
  populate `created_at`, `updated_at`, `created_by`, and
  `updated_by` fields automatically. No exceptions.
- **SoftDeleteMixin**: All domain models that represent business
  entities MUST use `SoftDeleteMixin` in addition to `AuditMixin`.
  SoftDeleteMixin adds `is_deleted` (Boolean, default false),
  `deleted_at` (DateTime), and `deleted_by` (Integer FK) columns.
  Physical DELETE on soft-deletable tables is forbidden. All
  queries on soft-deletable entities MUST filter
  `is_deleted = false` by default. The only exceptions are:
  (a) pure junction/mapping tables with no business identity,
  (b) log/event tables that are append-only.
- `AuditLog` entries MUST record user, action, resource, and changes
  (JSONB diff) for all state-changing API calls.
- Backup history MUST be tracked via `BackupHistory` for disaster
  recovery compliance.
- Email communications MUST use `EmailTemplate` for consistency and
  auditability.
- Custom reports (`CustomReport`) MUST be user-definable without
  code changes.
- Notifications MUST support multiple channels: in-app, WebSocket,
  webhook, and email.

**Rationale**: An ERP system without comprehensive audit trails
cannot pass financial audits or demonstrate regulatory compliance.
The Phase 1–6 audit found all 13 new models lacking SoftDeleteMixin,
meaning physical DELETEs would bypass the audit trail.

## Technology Stack & Constraints

| Layer | Technology | Constraint |
|-------|-----------|-----------|
| Backend | Python 3.11 / FastAPI | All endpoints via FastAPI routers |
| Frontend | React 18 / Vite | JSX, i18next for AR/EN, RTL support |
| Database | PostgreSQL 15 | One DB per company tenant + system DB |
| ORM | SQLAlchemy 2.0 | 240+ domain models, Alembic migrations |
| Cache | Redis | Rate limiting, session management, token blacklist |
| Auth | JWT (HttpOnly cookies) + TOTP | SameSite=Strict, pyotp for 2FA |
| Container | Docker + Nginx | Docker Compose orchestration, SSL/TLS |
| Validation | Pydantic | All request/response bodies schema-validated |

- Backend and frontend MUST remain deployable independently.
- New Python dependencies MUST be added to `backend/requirements.txt`.
- Database schema changes MUST go through Alembic migrations; manual
  DDL against production is forbidden.
- The system MUST support 12 industry templates and 8 default roles.
- All Pydantic schemas MUST return 422 on validation failure with
  structured error details.
- API response format: `{ success: bool, data?, message?, errors?,
  pagination? }`.

## Industry Templates & Module Flags

AMAN supports 12 industry types. Each industry activates a specific
set of modules via `INDUSTRY_FEATURES[industry_type]`.

| Code | Industry | Special Capabilities |
|------|----------|---------------------|
| RT | Retail | POS, loyalty, UOM variants, bin management |
| WS | Wholesale | Volume discounts, bulk orders |
| FB | Food & Beverage | Table management, KDS, meal combos |
| MF | Manufacturing | BOM, routings, MRP, capacity planning |
| CN | Construction | Job costing, progress billing, equipment |
| SV | Services | Time tracking, expense claims, retainers |
| PH | Pharmacy | Batch/serial tracking, expiry dates |
| WK | Wholesale Dealer | Net terms, volume tiers, distributor pricing |
| EC | E-Commerce | Multi-channel, dropshipping, fulfillment |
| LG | Logistics | Fleet management, shipment tracking |
| AG | Agriculture | Seasonal cycles, crop management, yield |
| GN | Generic | All modules enabled, no restrictions |

- Industry selection at company creation MUST configure the correct
  module flags. Changing industry type after initial setup MUST be
  treated as a major configuration change requiring data review.
- Industry-specific GL account mappings MUST follow rules in
  `services/industry_gl_rules.py`.
- Industry-specific KPI calculations MUST use
  `services/industry_kpi_service.py`.
- Chart of accounts templates MUST be scaffolded per industry via
  `services/industry_coa_templates.py`.

## Data Integrity Constraints

### Database-Level Enforcement

- **46 indexes** on high-cardinality, frequently-filtered columns
  (accounts, journal lines, inventory, invoices, etc.).
- **32 foreign key constraints** with `CASCADE` or `SET NULL` delete
  rules as appropriate.
- **Check constraints**: debit >= 0 and credit >= 0 on journal lines;
  start_date <= end_date on projects/phases; quantity >= 0 on
  inventory and orders.
- **Unique constraints**: account_number, party_code, invoice_number,
  rfq_number, po_number, so_number, entry_number — all unique per
  company database.
- **Constraint trigger** (`trg_journal_balance`): DEFERRABLE
  INITIALLY DEFERRED — validates debit = credit per entry at
  transaction commit.

### Application-Level Enforcement

- All endpoints MUST validate input via Pydantic schemas (422 on
  failure).
- Business rule validators (credit limit, fiscal period, UOM
  consistency, balance check) MUST run before database writes.
- Optimistic locking via version columns MUST be used on
  high-contention entities.

### Model & Schema Integrity

ORM models, DDL functions, and Alembic migrations MUST remain
synchronized at all times.

- **Model Registration**: Every new SQLAlchemy model MUST be
  imported in `backend/models/__init__.py` AND listed in the
  `__all__` tuple. Alembic autogenerate relies on this import
  path; unregistered models will be silently skipped.
- **DDL-ORM Parity**: The DDL functions in `database.py`
  (`get_*_tables_sql()`) create tables for fresh company databases.
  Every column, type, length, default, and constraint in the ORM
  model MUST have a matching definition in the corresponding DDL
  function. Column-type drift (e.g., `VARCHAR(50)` in DDL vs.
  `String(100)` in ORM) is a defect — fresh databases will
  diverge from migrated databases.
- **FK `ondelete` Parity**: Every `ForeignKey()` declaration
  in ORM models MUST include an explicit `ondelete` argument
  (`"CASCADE"`, `"SET NULL"`, or `"RESTRICT"`). Omitting
  `ondelete` is forbidden — it silently defaults to database
  engine behavior which varies across environments.
  The DDL function MUST specify the matching
  `ON DELETE CASCADE`, `ON DELETE SET NULL`, or
  `ON DELETE RESTRICT` clause. Mismatches between ORM and DDL
  produce different FK behaviors on fresh vs. migrated databases.
  **Remediation**: 335 existing FK references lack explicit
  `ondelete` and MUST be audited and corrected.
- **Relationship Completeness**: Every `ForeignKey` column
  MUST have a corresponding `relationship()` on the parent
  model with `back_populates` pointing to a matching
  `relationship()` on the child model. One-sided relationships
  (only parent or only child defines it) are forbidden — they
  cause stale identity-map references and make eager-loading
  unreliable. Lazy-load strategy MUST be explicit
  (`lazy="select"`, `lazy="joined"`, or `lazy="noload"`) —
  relying on SQLAlchemy's implicit default is forbidden for
  models with 5+ relationships.
- **Migration Coverage**: Every DDL table addition MUST have
  a corresponding Alembic migration that applies the same
  schema to existing company databases. The DDL is the safety
  net for fresh creates; the migration is the upgrade path.
- **Audit Columns in DDL**: Tables for models using `AuditMixin`
  MUST include `created_at`, `updated_at`, `created_by`,
  `updated_by` columns in DDL. Tables for models using
  `SoftDeleteMixin` MUST additionally include `is_deleted`,
  `deleted_at`, `deleted_by` columns in DDL.

## Deployment & Infrastructure

- **Docker Compose** orchestrates: postgres, backend (uvicorn:8000),
  frontend (vite:5173), redis, nginx (80/443).
- **Nginx** handles SSL/TLS termination, gzip compression, API
  reverse proxy, static asset caching, and per-IP rate limiting.
- Backend and frontend containers MUST be independently rebuildable
  and deployable.
- Database backups MUST be tracked via `BackupHistory` model.
- Background tasks (recurring journals, payroll reminders, backup
  alerts) run via `services/scheduler.py`.

## Development Workflow & Quality Gates

1. **Testing**: pytest is the test framework. Tests MUST cover
   authentication, permission boundaries, fiscal enforcement, journal
   balance validation, and UOM consistency for any new transactional
   endpoint.
2. **Migrations**: Every schema change MUST have a corresponding
   Alembic migration that works across all active company databases.
   Migrations MUST be idempotent.
3. **Code Review**: Changes to GL service, permission decorators,
   multi-tenant routing, or approval workflows MUST receive explicit
   review attention due to blast radius.
4. **Decimal Audit**: Any PR touching monetary calculations MUST
   verify no `float` usage crept in.
5. **Internationalization**: New user-facing strings MUST have entries
   in both `frontend/src/locales/en.json` and
   `frontend/src/locales/ar.json`. Default language is Arabic.
6. **UOM Validation**: Invoice, return, POS, delivery order, and
   inventory movement endpoints MUST validate unit-of-measure
   consistency.
7. **GL Service Usage**: All journal entry creation MUST go through
   `services/gl_service.py`. Direct SQL inserts into journal tables
   are forbidden.
8. **Soft Delete**: Entities using `SoftDeleteMixin` MUST NOT be
   physically deleted. All queries on soft-deletable entities MUST
   filter `is_deleted = false` by default.
9. **Audit Fields**: All new models MUST use `AuditMixin` unless
   there is an explicit documented reason not to.
10. **Frontend Patterns**: List pages MUST use `DataTable`, forms
    MUST use `FormField`, large lists MUST use `VirtualList`,
    all pages MUST support RTL layout.
11. **Frontend Checklist** (for every new page): Verify
    `workspace fade-in` root, `DataTable` on lists,
    `FormField` on forms, `SearchFilter` on list pages,
    `BackButton` in header, `PageLoading` for loading state,
    API from `../../utils/api`, `formatNumber()` for numbers,
    `badge-*` classes for status, logical CSS properties for
    spacing, no `t()` fallback strings, no `alert()`/`confirm()`.
12. **Model Registration**: Every new ORM model MUST be imported
    in `backend/models/__init__.py` and added to `__all__`.
    DDL function MUST match ORM columns and FK `ondelete` args.
    SoftDeleteMixin MUST be applied to all business entity models.
13. **Branch Filtering**: Every endpoint accepting `branch_id`
    MUST call `validate_branch_access()`. Warehouse-bound
    endpoints MUST resolve warehouse → branch before validating.
    New routers MUST use dependency/decorator pattern, not
    ad-hoc calls. 16 existing non-compliant routers MUST be
    remediated.
14. **Cell Design Checklist** (for every DataTable): Verify
    status badges use `STATUS_BADGE_MAP` (no inline colors),
    currency cells use `formatNumber()` + right-aligned,
    code cells use `code-cell` class, dates use `formatShortDate()`,
    actions column is last with `btn-icon` buttons, null values
    show em-dash, column widths defined as percentages.
    No raw `<table>` elements on list pages.
15. **FK `ondelete` Audit**: Every new or modified model MUST
    have explicit `ondelete` on all `ForeignKey()` declarations.
    Every FK MUST have bidirectional `relationship()` with
    `back_populates`. PR reviewers MUST reject FKs without
    `ondelete` arguments.

## Governance

This constitution is the authoritative reference for architectural and
quality decisions in AMAN ERP. When a conflict arises between this
document and ad-hoc practices, this document prevails.

- **Amendments**: Any change to this constitution MUST be documented
  with a version bump, rationale, and updated Sync Impact Report.
- **Versioning**: Follows semantic versioning — MAJOR for principle
  removal/redefinition or material expansion, MINOR for new
  principles or new sections, PATCH for clarifications and wording.
- **Compliance Review**: Each feature spec and implementation plan
  MUST include a Constitution Check verifying alignment with all
  active principles before work begins.
- **Guidance**: For runtime development guidance, refer to
  `docs/SYSTEM_KNOWLEDGE_BASE.md` and `docs/MODULE_AUDIT_REPORT.md`.
- **System Metrics**: 767 endpoints, 240 models, 279 frontend pages,
  73 routers, 9,335+ i18n keys, 12 industry templates. These
  numbers MUST be updated when major feature batches land.

**Version**: 2.2.0 | **Ratified**: 2026-04-02 | **Last Amended**: 2026-04-03
