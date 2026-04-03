# Implementation Plan: AMAN ERP — 18 Missing Competitive Features

**Branch**: `002-erp-missing-features` | **Date**: 2026-04-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-erp-missing-features/spec.md`

## Summary

Implement 18 missing features identified in the Feature Comparison Matrix to close gaps against SAP, NetSuite, Dynamics 365, Odoo, and Sage X3. Features span SSO/LDAP, 3-way matching, intercompany accounting, FIFO/LIFO costing, cash flow forecasting, employee self-service, mobile app, subscription billing, BI integration, blanket POs, campaign management, performance reviews, CPQ, demand forecasting, shop floor control, routing/operations, time tracking, and resource planning. A cross-cutting unified notification service underpins 6+ features. Delivery is phased across 3 tiers: P1 (enterprise essentials), P2 (competitive parity), P3 (market differentiation).

## Technical Context

**Language/Version**: Python 3.12.3 (backend), React 18 / Vite (frontend), React Native (mobile)  
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0, Pydantic, Redis, i18next, pyotp  
**Storage**: PostgreSQL 15 (multi-tenant: one DB per company + system DB), Redis (cache/sessions)  
**Testing**: pytest (backend), vitest/jest (frontend)  
**Target Platform**: Linux server (backend), Web browsers (frontend), iOS/Android (mobile)  
**Project Type**: Full-stack ERP web application + mobile app  
**Performance Goals**: SSO auth < 3s, dashboard load < 5s, mobile task < 60s, forecast gen < 30s, 3-way match on invoice entry < 2s  
**Constraints**: Multi-tenant isolation, Decimal-only financials, ZATCA/GOSI compliance, Arabic-first RTL, HttpOnly cookie auth  
**Scale/Scope**: 767 endpoints, 240+ models, 279 frontend pages, 73 routers, 12 industry templates, 3-4 developer team

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Financial Precision | PASS | FIFO/LIFO cost layers use Decimal(18,4). Subscription billing proration uses Decimal. Intercompany FX uses locked exchange rates. |
| II. Multi-Tenant Isolation | PASS | All new features route through `get_db_connection(company_id)`. New migrations via Alembic per-tenant. |
| III. Double-Entry Integrity | PASS | Intercompany reciprocal entries and FIFO cost adjustments route through GL service. Elimination entries use GL service. |
| IV. Security & Access Control | PASS | SSO/LDAP extends HttpOnly cookie auth. Admin-only fallback preserves security posture. Mobile uses same JWT-in-cookie flow. Permission decorators on all new endpoints. |
| V. Regulatory Compliance | PASS | FIFO/LIFO costing meets industry requirements. ZATCA compliance maintained. GOSI/WPS unaffected. |
| VI. Concurrency Safety | PASS | 3-way matching uses FOR UPDATE on invoice/PO/GRN. FIFO cost layer consumption uses row-level locks. Subscription billing uses atomic invoice generation. |
| VII. Simplicity & Maintainability | PASS | Unified notification service (1 service, not 6). New features follow existing patterns (DataTable, FormField, GL service). |
| VIII. Inventory Integrity | PASS | FIFO/LIFO enforced via cost layers with negative inventory prevention. UOM validation on all new inventory flows. |
| IX. Procurement Discipline | PASS | 3-way matching auto-triggers on invoice entry. Blanket POs track consumed quantities. Tolerance uses both % and absolute. |
| X. Manufacturing Execution | PASS | Routing/operations enforce sequence. Shop floor tracks per-operation. Capacity checks on work order release. |
| XI. HR & Payroll Compliance | PASS | Employee self-service uses existing leave balance/payroll models. Performance reviews add new models with AuditMixin. |
| XII. Asset Lifecycle Management | N/A | No asset changes in this feature set. |
| XIII. Sales & CRM Workflow | PASS | CPQ integrates with existing quotation workflow. Campaign management links to CRM pipeline. |
| XIV. Approval Workflow Governance | PASS | Mobile app exposes existing approval workflows. No changes to approval logic. |
| XV. Project & Contract Management | PASS | Time tracking and resource planning extend existing project module. |
| XVI. POS Operations | N/A | No POS changes in this feature set. |
| XVII. Observability & Audit Trail | PASS | All new models use AuditMixin. Unified notification service logs all dispatched notifications. New AuditLog entries for all state changes. |

**Gate Result: PASS — No violations. Proceeding to Phase 0.**

## Project Structure

### Documentation (this feature)

```text
specs/002-erp-missing-features/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (API contracts)
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

> **Note on model directories**: The plan originally specified `models/domains/` but the
> codebase uses **two** model directories: `models/domains/` (thin ORM stubs per module) and
> `models/domain_models/` (detailed columns/relationships, used by migrations). New feature
> models were placed in `domain_models/` following the existing pattern (e.g., `sso.py`,
> `matching.py`, `intercompany.py`, `inventory_costing.py`, `finance_forecast.py`).
> Both directories re-export via `models/__init__.py`.

> **Intercompany v1 vs v2**: A legacy intercompany page
> (`pages/Accounting/IntercompanyTransactions.jsx`) uses `accountingAPI.*` endpoints from
> `routers/accounting.py`. The new v2 system (`pages/Intercompany/*`, `routers/finance/intercompany_v2.py`,
> `services/intercompany_service.py`) adds entity-group hierarchy, account mappings, and
> consolidation elimination. Both coexist — v1 is the simple single-company view; v2 is the
> full multi-entity system per FR-003.

```text
backend/
├── models/
│   ├── domain_models/           # Detailed ORM models (actual location)
│   │   ├── sso.py               # SSO config models (US1)
│   │   ├── matching.py          # 3-way match models (US2)
│   │   ├── intercompany.py      # Intercompany entity/txn models (US3)
│   │   ├── inventory_costing.py # Cost layer FIFO/LIFO models (US4)
│   │   ├── finance_forecast.py  # Cash flow forecast models (US5)
│   │   └── ...                  # Other domain models
│   └── domains/                 # Thin stubs / re-exports
│       ├── core.py
│       ├── finance.py
│       ├── procurement.py
│       ├── inventory.py
│       ├── manufacturing.py
│       ├── hr.py
│       ├── projects_crm.py
│       ├── sales.py
│       └── operations.py
├── routers/
│   ├── auth.py                  # SSO/LDAP endpoints (extend existing)
│   ├── finance/
│   │   ├── intercompany.py      # NEW: intercompany transactions
│   │   ├── cashflow.py          # NEW: cash flow forecasting
│   │   └── subscriptions.py     # NEW: subscription billing
│   ├── inventory/
│   │   └── costing.py           # NEW: FIFO/LIFO costing management
│   ├── purchases.py             # Extend: 3-way matching, blanket POs
│   ├── hr/
│   │   ├── self_service.py      # NEW: employee self-service
│   │   └── performance.py       # NEW: performance reviews
│   ├── manufacturing/
│   │   ├── routing.py           # NEW: routing/operations
│   │   └── shopfloor.py         # NEW: shop floor control
│   ├── projects.py              # Extend: time tracking, resource planning
│   ├── crm.py                   # Extend: campaign management
│   ├── sales/
│   │   └── cpq.py               # NEW: configure price quote
│   ├── notifications.py         # Extend: unified notification service
│   └── dashboard.py             # Extend: BI dashboard integration
├── services/
│   ├── gl_service.py            # Extend: intercompany entries, FIFO cost adjustments
│   ├── costing_service.py       # Extend: FIFO/LIFO cost layer engine
│   ├── matching_service.py      # NEW: 3-way matching engine
│   ├── notification_service.py  # NEW: unified notification dispatcher
│   ├── forecast_service.py      # NEW: cash flow + demand forecasting
│   ├── subscription_service.py  # NEW: subscription lifecycle + billing
│   ├── sso_service.py           # NEW: SAML/LDAP authentication
│   └── cpq_service.py           # NEW: configuration + pricing engine
├── schemas/
│   ├── intercompany.py          # NEW
│   ├── matching.py              # NEW
│   ├── subscription.py          # NEW
│   ├── self_service.py          # NEW
│   ├── performance.py           # NEW
│   ├── cpq.py                   # NEW
│   ├── routing.py               # NEW
│   ├── shopfloor.py             # NEW
│   ├── cashflow.py              # NEW
│   ├── timetracking.py          # NEW
│   ├── resource.py              # NEW
│   ├── campaign.py              # NEW
│   └── notification.py          # NEW
└── tests/
    ├── test_sso.py
    ├── test_matching.py
    ├── test_intercompany.py
    ├── test_costing_fifo_lifo.py
    ├── test_cashflow.py
    ├── test_self_service.py
    ├── test_subscription.py
    ├── test_cpq.py
    ├── test_routing.py
    ├── test_shopfloor.py
    ├── test_notifications.py
    ├── test_performance.py
    ├── test_timetracking.py
    ├── test_resource.py
    └── test_campaign.py

frontend/
├── src/
│   ├── pages/
│   │   ├── SSO/                 # NEW: SSO configuration pages
│   │   ├── Matching/            # NEW: 3-way matching views
│   │   ├── Intercompany/        # NEW: intercompany transaction pages
│   │   ├── Costing/             # NEW: FIFO/LIFO costing setup
│   │   ├── CashFlow/            # NEW: cash flow forecast views
│   │   ├── SelfService/         # NEW: employee portal pages
│   │   ├── Subscription/        # NEW: subscription management
│   │   ├── Analytics/           # NEW: BI dashboard pages
│   │   ├── BlanketPO/           # NEW: blanket PO management
│   │   ├── Campaign/            # NEW: campaign management
│   │   ├── Performance/         # NEW: performance review pages
│   │   ├── CPQ/                 # NEW: product configurator
│   │   ├── Forecast/            # NEW: demand forecast views
│   │   ├── ShopFloor/           # NEW: shop floor dashboard
│   │   ├── Routing/             # NEW: routing definition pages
│   │   ├── TimeTracking/        # NEW: timesheet pages
│   │   └── ResourcePlanning/    # NEW: resource allocation views
│   ├── components/
│   │   └── Notifications/       # NEW: notification center component
│   └── services/
│       └── notificationService.js  # NEW: push notification client
└── tests/

mobile/                          # NEW: React Native app
├── src/
│   ├── screens/
│   │   ├── Dashboard/
│   │   ├── Inventory/
│   │   ├── Quotations/
│   │   ├── Orders/
│   │   └── Approvals/
│   ├── services/
│   │   ├── syncService.js       # Offline sync engine
│   │   ├── conflictResolver.js  # Conflict detection + resolution
│   │   └── pushService.js       # Push notification handler
│   └── store/                   # Local storage for offline
└── tests/
```

**Structure Decision**: Extends the existing `backend/` + `frontend/` web application structure. New `mobile/` directory for the React Native app. Backend follows existing patterns: models in `models/domains/`, routers in `routers/`, services in `services/`, schemas in `schemas/`. All new models use AuditMixin and follow multi-tenant isolation.

## Complexity Tracking

No constitution violations to justify — all gates pass.
