# Research: AMAN ERP — 18 Missing Competitive Features

**Branch**: `002-erp-missing-features` | **Date**: 2026-04-02

## Technical Decisions

### TD-001: SSO/LDAP Implementation Approach

**Decision**: Use `python-saml` (OneLogin) for SAML 2.0 SP and `python-ldap` for LDAP bind authentication. Extend existing `auth.py` router.

**Rationale**: `python-saml` is the most mature SAML SP library for Python with FastAPI compatibility. `python-ldap` is the standard for LDAP operations. Both are well-documented and actively maintained.

**Alternatives considered**:
- `python3-saml` (fork) — less active maintenance
- `authlib` — broader OAuth scope, more complexity than needed for SAML-only
- Custom SAML parsing — high risk, low value

### TD-002: 3-Way Matching Engine

**Decision**: Implement as a service (`matching_service.py`) triggered synchronously on supplier invoice creation. Matching runs at line-item level, comparing PO lines → GRN lines → invoice lines.

**Rationale**: Line-level matching catches partial receipt and partial invoicing scenarios. Synchronous trigger ensures no invoice enters the payment pipeline unmatched. Aligns with constitution VI (Concurrency Safety) — uses `SELECT ... FOR UPDATE` on PO and GRN records during matching.

**Alternatives considered**:
- Header-level matching only — misses partial receipt discrepancies
- Async batch matching — delays detection, invoices could slip to payment
- Probabilistic matching — unnecessary complexity for structured PO/GRN/invoice data

### TD-003: Intercompany Entity Hierarchy

**Decision**: Parent-child entity tree stored in `EntityGroup` model with recursive `parent_id`. Consolidation runs bottom-up, eliminating intercompany balances at each level.

**Rationale**: Supports both flat (single-level) and multi-level corporate structures. Bottom-up consolidation is the standard approach in SAP and NetSuite. Aligns with constitution III — all intercompany entries route through GL service.

**Alternatives considered**:
- Flat group only — insufficient for holding company structures
- Matrix/graph structure — over-engineered for entity consolidation

### TD-004: FIFO/LIFO Cost Layer Engine

**Decision**: Extend `costing_service.py` with a cost layer model (`CostLayer`). Each purchase creates a layer; each sale consumes layers in FIFO or LIFO order. Negative inventory is blocked by default.

**Rationale**: Cost layer approach is the industry standard. Aligns with constitution VIII (Inventory Integrity) — FIFO via `batch_serial_movements` already partially exists. Extends rather than replaces.

**Alternatives considered**:
- Periodic FIFO/LIFO (end-of-period recalculation) — less accurate for real-time costing
- Separate inventory tables per costing method — data duplication

### TD-005: Unified Notification Service

**Decision**: New `notification_service.py` with channel dispatchers (email via existing `email_service.py`, in-app via WebSocket, push via Firebase Cloud Messaging for mobile). User preferences stored in `NotificationPreference` model.

**Rationale**: Constitution XVII already mandates multi-channel notifications. A unified service prevents 6+ features from implementing their own notification logic. Aligns with VII (Simplicity).

**Alternatives considered**:
- Per-feature notifications — duplication across 6+ features
- Third-party notification service (e.g., Novu) — external dependency, cost

### TD-006: Mobile App Architecture

**Decision**: React Native with offline-first architecture. Local SQLite for offline storage, background sync service, conflict detection on sync.

**Rationale**: React Native shares skills with existing React frontend team. Offline-first is required per spec (FR-007). SQLite provides reliable local storage on both iOS and Android.

**Alternatives considered**:
- Flutter — different language (Dart), team ramp-up cost
- PWA — limited push notification and offline capabilities on iOS
- Native iOS/Android — double the development effort

### TD-007: Subscription Billing Engine

**Decision**: New `subscription_service.py` handling plan lifecycle (trial → active → paused → cancelled → at-risk), proration engine, and recurring invoice generation via scheduled job in `scheduler.py`.

**Rationale**: Separating subscription logic from general invoicing keeps the existing sales flow clean. Scheduled job aligns with existing scheduler pattern. Trial support included per clarification.

**Alternatives considered**:
- Stripe-like external billing — out of scope, adds vendor dependency
- Extending existing invoice module directly — mixes one-time and recurring logic

### TD-008: BI Dashboard Integration

**Decision**: Embedded dashboard approach using pre-computed materialized views refreshed every 15 minutes. Custom dashboard widgets rendered in React using chart components.

**Rationale**: Avoids dependency on external BI tools (Metabase/Grafana licensing). Materialized views provide near-real-time data without impacting transactional performance. Aligns with constitution VII (Simplicity).

**Alternatives considered**:
- Metabase embedded — licensing cost, external dependency
- Grafana — more ops-focused, less suited for business KPIs
- Real-time aggregation queries — too expensive on transactional DB

### TD-009: Cash Flow Forecasting

**Decision**: New `forecast_service.py` with two modes: (1) "contractual" — uses AR/AP due dates as-is; (2) "expected" — adjusts dates based on historical payment patterns (average days late per customer/supplier).

**Rationale**: Dual mode covers both optimistic and realistic planning. Historical pattern adjustment is the key differentiator vs. simple AR/AP aging reports.

**Alternatives considered**:
- ML-based forecasting — requires infrastructure not in scope
- Single mode only — misses the value of historical pattern adjustment

### TD-010: CPQ Configuration Engine

**Decision**: Rule-based configuration engine in `cpq_service.py`. Product options stored as structured data (option groups, allowed/blocked combinations). Pricing rules evaluated in sequence (base price → volume discount → customer discount → final).

**Rationale**: Rule-based approach handles option-based configuration without requiring a full constraint solver. Covers the target use case (configurable products, not engineer-to-order).

**Alternatives considered**:
- Constraint programming (e.g., OR-Tools) — over-engineered for option selection
- Template-based (pre-defined combinations only) — too rigid for configurable products

### TD-011: Demand Forecasting

**Decision**: Statistical methods in `forecast_service.py`: simple moving average, exponential smoothing, and seasonal decomposition. Selection based on data availability (>= 12 months for seasonal, >= 3 months for exponential, >= 1 month for moving average).

**Rationale**: Statistical methods are adequate for ERP demand forecasting and require no ML infrastructure. Auto-selecting the method based on data availability provides the best forecast without user expertise.

**Alternatives considered**:
- ML models (Prophet, ARIMA) — requires ML infrastructure, out of scope
- Manual-only forecasting — no analytical value

### TD-012: Shop Floor Control + Routing

**Decision**: Routing model stores operation sequences with work centers and time estimates. Shop floor log tracks real-time progress per operation. Dashboard uses WebSocket for live updates.

**Rationale**: Aligns with constitution X (Manufacturing Execution) — routing enforces sequence, capacity checks validate before release. WebSocket provides real-time updates without polling.

**Alternatives considered**:
- Polling-based dashboard — higher latency, more server load
- Simple start/complete tracking — misses per-operation visibility

## Dependencies & Best Practices

### SAML 2.0 / LDAP Integration
- SAML SP metadata must be generated and exchangeable with customer IdPs
- LDAP bind requires TLS (LDAPS on port 636) — plaintext LDAP is forbidden
- Group-to-role mapping must be configurable per tenant (different companies may use different LDAP groups)
- Session lifetime should match IdP session to prevent stale access

### Multi-Tenant Considerations
- All 18 features must respect tenant isolation via `get_db_connection(company_id)`
- New Alembic migrations for new models must apply across all company databases
- Industry module flags determine which features are enabled per tenant

### Offline Sync (Mobile)
- Conflict resolution strategy: "last-write-wins" for non-financial data, "manual resolution" for financial data (quotes, orders)
- Sync queue must be idempotent — retries must not create duplicates
- Offline operations must be timestamped with device clock + server clock reconciliation

### Financial Data Patterns
- All monetary calculations in new features (FIFO/LIFO COGS, subscription proration, intercompany FX, cash flow projections) must use `Decimal` with `ROUND_HALF_UP`
- Intercompany elimination entries must net to zero — add assertion in GL service
- Cost layer consumption must be atomic within a transaction to prevent race conditions
