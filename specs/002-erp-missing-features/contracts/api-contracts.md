# API Contracts: AMAN ERP — 18 Missing Features

**Branch**: `002-erp-missing-features` | **Date**: 2026-04-02

All endpoints follow the standard AMAN response format:
```json
{ "success": bool, "data": {}, "message": "", "errors": [], "pagination": {} }
```

All endpoints require `require_permission("module.action")` decorator. All request/response bodies validated via Pydantic schemas (422 on failure).

---

## Tier 1 — Enterprise Essentials

### SSO/LDAP (`/api/auth/sso`)

| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| GET | `/api/auth/sso/config` | List SSO configurations | `auth.sso_manage` |
| POST | `/api/auth/sso/config` | Create SSO configuration | `auth.sso_manage` |
| PUT | `/api/auth/sso/config/{id}` | Update SSO configuration | `auth.sso_manage` |
| DELETE | `/api/auth/sso/config/{id}` | Deactivate SSO configuration | `auth.sso_manage` |
| GET | `/api/auth/sso/saml/metadata` | Get SAML SP metadata XML | Public |
| POST | `/api/auth/sso/saml/acs` | SAML Assertion Consumer Service (callback) | Public |
| POST | `/api/auth/sso/ldap/test` | Test LDAP connection | `auth.sso_manage` |
| POST | `/api/auth/sso/login` | Initiate SSO login flow | Public |
| GET | `/api/auth/sso/mappings` | List group-to-role mappings | `auth.sso_manage` |
| POST | `/api/auth/sso/mappings` | Create group-to-role mapping | `auth.sso_manage` |

### 3-Way Matching (`/api/purchases/matching`)

| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| GET | `/api/purchases/matching` | List match records (filterable by status) | `purchases.matching_view` |
| GET | `/api/purchases/matching/{id}` | Get match detail with line variances | `purchases.matching_view` |
| POST | `/api/purchases/matching/{id}/approve` | Approve held match with exception | `purchases.matching_approve` |
| POST | `/api/purchases/matching/{id}/reject` | Reject held match | `purchases.matching_approve` |
| GET | `/api/purchases/matching/tolerances` | List tolerance configurations | `purchases.matching_manage` |
| POST | `/api/purchases/matching/tolerances` | Create/update tolerance | `purchases.matching_manage` |

**Note**: Match records are auto-created on invoice submission — no manual create endpoint.

### Intercompany (`/api/finance/intercompany`)

| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| GET | `/api/finance/intercompany/entities` | List entity group hierarchy | `finance.intercompany_view` |
| POST | `/api/finance/intercompany/entities` | Create/update entity group node | `finance.intercompany_manage` |
| POST | `/api/finance/intercompany/transactions` | Create intercompany transaction | `finance.intercompany_create` |
| GET | `/api/finance/intercompany/transactions` | List intercompany transactions | `finance.intercompany_view` |
| GET | `/api/finance/intercompany/transactions/{id}` | Get transaction with reciprocal entries | `finance.intercompany_view` |
| POST | `/api/finance/intercompany/consolidate` | Run consolidation with eliminations | `finance.intercompany_consolidate` |
| GET | `/api/finance/intercompany/balances` | Get intercompany balance report | `finance.intercompany_view` |
| GET | `/api/finance/intercompany/mappings` | List account mappings | `finance.intercompany_manage` |
| POST | `/api/finance/intercompany/mappings` | Create/update account mapping | `finance.intercompany_manage` |

### FIFO/LIFO Costing (`/api/inventory/costing`)

| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| GET | `/api/inventory/costing/layers` | List cost layers (filter by product/warehouse) | `inventory.costing_view` |
| GET | `/api/inventory/costing/layers/{product_id}` | Get cost layers for product | `inventory.costing_view` |
| PUT | `/api/inventory/costing/method` | Change costing method for product/warehouse | `inventory.costing_manage` |
| GET | `/api/inventory/costing/valuation` | Get inventory valuation report | `inventory.costing_view` |
| GET | `/api/inventory/costing/consumption/{product_id}` | Get consumption history per layer | `inventory.costing_view` |

**Note**: Cost layers are auto-created on purchase receipt — no manual create endpoint.

---

## Tier 2 — Competitive Parity

### Cash Flow Forecast (`/api/finance/cashflow`)

| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| POST | `/api/finance/cashflow/generate` | Generate forecast (params: horizon_days, mode) | `finance.cashflow_generate` |
| GET | `/api/finance/cashflow` | List saved forecasts | `finance.cashflow_view` |
| GET | `/api/finance/cashflow/{id}` | Get forecast detail with lines | `finance.cashflow_view` |
| DELETE | `/api/finance/cashflow/{id}` | Delete forecast | `finance.cashflow_manage` |

### Employee Self-Service (`/api/hr/self-service`)

| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| GET | `/api/hr/self-service/profile` | Get own employee profile | `hr.self_service` |
| PUT | `/api/hr/self-service/profile` | Update own profile fields | `hr.self_service` |
| GET | `/api/hr/self-service/payslips` | List own payslips | `hr.self_service` |
| GET | `/api/hr/self-service/payslips/{id}` | Get payslip detail | `hr.self_service` |
| GET | `/api/hr/self-service/leave-balance` | Get own leave balances | `hr.self_service` |
| POST | `/api/hr/self-service/leave-request` | Submit leave request | `hr.self_service` |
| GET | `/api/hr/self-service/leave-requests` | List own leave requests | `hr.self_service` |
| GET | `/api/hr/self-service/team-requests` | List team's pending requests (manager) | `hr.self_service_approve` |
| POST | `/api/hr/self-service/leave-request/{id}/approve` | Approve leave request | `hr.self_service_approve` |
| POST | `/api/hr/self-service/leave-request/{id}/reject` | Reject leave request | `hr.self_service_approve` |

### Mobile API (`/api/mobile`)

| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| POST | `/api/mobile/sync` | Sync offline changes (batch) | `mobile.sync` |
| GET | `/api/mobile/sync/status` | Get sync status for device | `mobile.sync` |
| POST | `/api/mobile/sync/resolve` | Resolve sync conflict | `mobile.sync` |
| GET | `/api/mobile/dashboard` | Get mobile dashboard data | `mobile.view` |
| POST | `/api/mobile/register-device` | Register device for push notifications | `mobile.sync` |

**Note**: Mobile app also uses existing endpoints for inventory, quotations, orders, approvals. These are mobile-specific additions for sync and push.

### Subscription Billing (`/api/finance/subscriptions`)

| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| GET | `/api/finance/subscriptions/plans` | List subscription plans | `finance.subscription_view` |
| POST | `/api/finance/subscriptions/plans` | Create plan | `finance.subscription_manage` |
| PUT | `/api/finance/subscriptions/plans/{id}` | Update plan | `finance.subscription_manage` |
| POST | `/api/finance/subscriptions/enroll` | Enroll customer in plan | `finance.subscription_manage` |
| GET | `/api/finance/subscriptions/enrollments` | List enrollments (filterable) | `finance.subscription_view` |
| GET | `/api/finance/subscriptions/enrollments/{id}` | Get enrollment detail | `finance.subscription_view` |
| POST | `/api/finance/subscriptions/enrollments/{id}/pause` | Pause subscription | `finance.subscription_manage` |
| POST | `/api/finance/subscriptions/enrollments/{id}/resume` | Resume subscription | `finance.subscription_manage` |
| POST | `/api/finance/subscriptions/enrollments/{id}/cancel` | Cancel subscription | `finance.subscription_manage` |
| POST | `/api/finance/subscriptions/enrollments/{id}/change-plan` | Change plan (proration) | `finance.subscription_manage` |

### BI Dashboards (`/api/dashboard/analytics`)

| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| GET | `/api/dashboard/analytics` | List available dashboards | `dashboard.analytics_view` |
| GET | `/api/dashboard/analytics/{id}` | Get dashboard with widget data | `dashboard.analytics_view` |
| POST | `/api/dashboard/analytics` | Create custom dashboard | `dashboard.analytics_manage` |
| PUT | `/api/dashboard/analytics/{id}` | Update dashboard layout/widgets | `dashboard.analytics_manage` |
| GET | `/api/dashboard/analytics/widget-data/{widget_id}` | Get single widget data (refresh) | `dashboard.analytics_view` |

---

## Tier 3 — Market Differentiation

### Blanket PO (`/api/purchases/blanket`)

| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| POST | `/api/purchases/blanket` | Create blanket PO | `purchases.blanket_manage` |
| GET | `/api/purchases/blanket` | List blanket POs | `purchases.blanket_view` |
| GET | `/api/purchases/blanket/{id}` | Get blanket PO with releases | `purchases.blanket_view` |
| POST | `/api/purchases/blanket/{id}/release` | Create release order | `purchases.blanket_release` |
| PUT | `/api/purchases/blanket/{id}/amend-price` | Amend price with effective date | `purchases.blanket_manage` |

### Campaign Management (`/api/crm/campaigns`)

| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| POST | `/api/crm/campaigns` | Create campaign | `crm.campaign_manage` |
| GET | `/api/crm/campaigns` | List campaigns | `crm.campaign_view` |
| GET | `/api/crm/campaigns/{id}` | Get campaign with metrics | `crm.campaign_view` |
| POST | `/api/crm/campaigns/{id}/execute` | Execute campaign | `crm.campaign_execute` |
| GET | `/api/crm/campaigns/{id}/recipients` | List recipients with status | `crm.campaign_view` |
| POST | `/api/crm/campaigns/webhook/track` | Tracking webhook (opens/clicks) | Public (signed) |

### Performance Reviews (`/api/hr/performance`)

| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| POST | `/api/hr/performance/cycles` | Create review cycle | `hr.performance_manage` |
| GET | `/api/hr/performance/cycles` | List review cycles | `hr.performance_view` |
| POST | `/api/hr/performance/cycles/{id}/launch` | Launch cycle (notify employees) | `hr.performance_manage` |
| GET | `/api/hr/performance/reviews` | List my reviews (employee) | `hr.performance_self` |
| PUT | `/api/hr/performance/reviews/{id}/self-assessment` | Submit self-assessment | `hr.performance_self` |
| GET | `/api/hr/performance/team-reviews` | List team reviews (manager) | `hr.performance_review` |
| PUT | `/api/hr/performance/reviews/{id}/manager-assessment` | Submit manager assessment | `hr.performance_review` |
| POST | `/api/hr/performance/reviews/{id}/finalize` | Finalize review (compute score) | `hr.performance_manage` |

### CPQ (`/api/sales/cpq`)

| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| GET | `/api/sales/cpq/products` | List configurable products | `sales.cpq_view` |
| GET | `/api/sales/cpq/products/{id}/configure` | Get configuration options + rules | `sales.cpq_view` |
| POST | `/api/sales/cpq/validate` | Validate configuration combination | `sales.cpq_create` |
| POST | `/api/sales/cpq/price` | Calculate price for configuration | `sales.cpq_create` |
| POST | `/api/sales/cpq/quotes` | Create CPQ quote | `sales.cpq_create` |
| GET | `/api/sales/cpq/quotes/{id}` | Get quote detail | `sales.cpq_view` |
| POST | `/api/sales/cpq/quotes/{id}/generate-pdf` | Generate quote PDF | `sales.cpq_create` |
| POST | `/api/sales/cpq/quotes/{id}/convert` | Convert to standard quotation | `sales.cpq_create` |

### Demand Forecasting (`/api/inventory/forecast`)

| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| POST | `/api/inventory/forecast/generate` | Generate forecast for product(s) | `inventory.forecast_generate` |
| GET | `/api/inventory/forecast` | List saved forecasts | `inventory.forecast_view` |
| GET | `/api/inventory/forecast/{id}` | Get forecast with periods | `inventory.forecast_view` |
| PUT | `/api/inventory/forecast/{id}/adjust` | Manual adjustment to periods | `inventory.forecast_manage` |

### Shop Floor (`/api/manufacturing/shopfloor`)

| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| GET | `/api/manufacturing/shopfloor/dashboard` | Get real-time shop floor status | `manufacturing.shopfloor_view` |
| POST | `/api/manufacturing/shopfloor/start` | Start operation for work order | `manufacturing.shopfloor_operate` |
| POST | `/api/manufacturing/shopfloor/complete` | Complete operation | `manufacturing.shopfloor_operate` |
| POST | `/api/manufacturing/shopfloor/pause` | Pause operation | `manufacturing.shopfloor_operate` |
| GET | `/api/manufacturing/shopfloor/work-order/{id}` | Get work order progress by operation | `manufacturing.shopfloor_view` |

### Routing (`/api/manufacturing/routing`)

| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| POST | `/api/manufacturing/routing` | Create routing | `manufacturing.routing_manage` |
| GET | `/api/manufacturing/routing` | List routings | `manufacturing.routing_view` |
| GET | `/api/manufacturing/routing/{id}` | Get routing with operations | `manufacturing.routing_view` |
| PUT | `/api/manufacturing/routing/{id}` | Update routing/operations | `manufacturing.routing_manage` |
| GET | `/api/manufacturing/routing/product/{product_id}` | Get routings for product | `manufacturing.routing_view` |

### Time Tracking (`/api/projects/timetracking`)

| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| POST | `/api/projects/timetracking` | Log time entry | `projects.time_log` |
| GET | `/api/projects/timetracking` | List own time entries (filterable) | `projects.time_view` |
| PUT | `/api/projects/timetracking/{id}` | Update time entry | `projects.time_log` |
| POST | `/api/projects/timetracking/submit-week` | Submit weekly timesheet | `projects.time_log` |
| GET | `/api/projects/timetracking/team` | List team entries (manager) | `projects.time_approve` |
| POST | `/api/projects/timetracking/{id}/approve` | Approve entry | `projects.time_approve` |
| POST | `/api/projects/timetracking/{id}/reject` | Reject entry | `projects.time_approve` |
| GET | `/api/projects/timetracking/profitability/{project_id}` | Project profitability report | `projects.time_view` |

### Resource Planning (`/api/projects/resources`)

| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| GET | `/api/projects/resources/availability` | Get team availability calendar | `projects.resource_view` |
| POST | `/api/projects/resources/allocate` | Allocate resource to project | `projects.resource_manage` |
| PUT | `/api/projects/resources/allocate/{id}` | Update allocation | `projects.resource_manage` |
| DELETE | `/api/projects/resources/allocate/{id}` | Remove allocation | `projects.resource_manage` |
| GET | `/api/projects/resources/project/{project_id}` | Get project resource allocation | `projects.resource_view` |

---

## Cross-Cutting: Unified Notifications (`/api/notifications`)

| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| GET | `/api/notifications` | List own notifications (paginated) | Authenticated |
| GET | `/api/notifications/unread-count` | Get unread count | Authenticated |
| PUT | `/api/notifications/{id}/read` | Mark as read | Authenticated |
| PUT | `/api/notifications/read-all` | Mark all as read | Authenticated |
| GET | `/api/notifications/preferences` | Get own notification preferences | Authenticated |
| PUT | `/api/notifications/preferences` | Update notification preferences | Authenticated |

**Total new endpoints: ~120**
