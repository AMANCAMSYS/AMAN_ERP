# Tasks: AMAN ERP — 18 Missing Competitive Features

**Input**: Design documents from `/specs/002-erp-missing-features/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api-contracts.md, quickstart.md

**Tests**: Not explicitly requested — test tasks are omitted. Add test phases per story if TDD is desired.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: New directory scaffolding and shared dependency installation for all 18 features.

- [x] T001 Create new router directories: `backend/routers/finance/`, `backend/routers/manufacturing/`, `backend/routers/sales/` per plan.md structure
- [x] T002 [P] Create new schema files directory structure: `backend/schemas/` for intercompany.py, matching.py, subscription.py, self_service.py, performance.py, cpq.py, routing.py, shopfloor.py, cashflow.py, timetracking.py, resource.py, campaign.py, notification.py
- [x] T003 [P] Add new Python dependencies to `backend/requirements.txt`: python-saml, python-ldap, firebase-admin (push notifications), statistics (stdlib — demand forecasting)
- [x] T004 [P] Create mobile app scaffold: `mobile/` directory with React Native project structure per plan.md (src/screens/, src/services/, src/store/)
- [x] T004a [P] Add charting library (recharts) to `frontend/package.json` and verify import works — required for BI dashboard widgets (US9)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Unified notification service — 6+ user stories depend on this. MUST complete before any user story work.

**CRITICAL**: No user story work can begin until this phase is complete.

- [x] T005 Create Notification and NotificationPreference models in `backend/models/domain_models/operations.py` per data-model.md (Notification: recipient_id, channel enum, event_type, feature_source, title, body, reference_type, reference_id, status enum, sent_at, read_at + AuditMixin; NotificationPreference: user_id, event_type, email_enabled, in_app_enabled, push_enabled + AuditMixin with unique constraint on user_id+event_type)
- [x] T006 Create Alembic migration for Notification and NotificationPreference tables: `backend/alembic/versions/a1b2c3d4e5f6_add_notification_unified_fields.py`
- [x] T007 Create Pydantic schemas for notifications in `backend/schemas/notification.py` (NotificationCreate, NotificationRead, NotificationPreferenceUpdate, UnreadCountResponse)
- [x] T008 Implement unified notification_service.py in `backend/services/notification_service.py` — dispatch method accepting (recipient_id, event_type, title, body, reference_type, reference_id) that checks NotificationPreference and dispatches to enabled channels (email via existing email_service.py, in_app via DB insert, push via Firebase). All monetary fields Decimal.
- [x] T009 Extend notifications router in `backend/routers/notifications.py` with endpoints: GET /api/notifications (paginated, own only), GET /api/notifications/unread-count, PUT /api/notifications/{id}/read, PUT /api/notifications/read-all, GET /api/notifications/preferences, PUT /api/notifications/preferences — all with `@require_permission` per contracts
- [x] T010 [P] Create NotificationCenter frontend component in `frontend/src/components/Notifications/NotificationCenter.jsx` (bell icon with unread badge, dropdown with notification list, mark-as-read on click) using DataTable pattern, with AR+EN i18n keys in `frontend/src/locales/en.json` and `frontend/src/locales/ar.json`
- [x] T011 [P] Create notification preferences page in `frontend/src/pages/Settings/NotificationPreferences.jsx` (toggle grid: event types × channels) using FormField pattern, with AR+EN i18n keys
- [x] T011a Implement WebSocket endpoint for real-time in-app notifications in `backend/routers/notifications.py` — FastAPI WebSocket route at `/ws/notifications` authenticated via cookie token, pushes new notifications to connected clients immediately on dispatch (per constitution XVII WebSocket mandate)
- [x] T011b [P] Connect NotificationCenter component in `frontend/src/components/Notifications/NotificationCenter.jsx` to WebSocket — live badge update and toast on new notification without polling

**Checkpoint**: Unified notification service ready with real-time WebSocket delivery — all user stories can now dispatch notifications through a single service.

---

## Phase 3: User Story 1 — SSO/LDAP Enterprise Login (Priority: P1)

**Goal**: Employees log in with corporate LDAP/SAML credentials, auto-provisioned with role mapping. Admin-only local fallback when IdP is down.

**Independent Test**: Configure an LDAP directory, log in with corporate credentials, verify role mapping, deactivate a user, confirm access denied.

### Implementation for User Story 1

- [x] T012 [P] [US1] Create SsoConfiguration, SsoGroupRoleMapping, and SsoFallbackAdmin models in `backend/models/domain_models/core.py` per data-model.md (SsoConfiguration: provider_type enum saml/ldap, display_name, metadata_url, ldap_host/port/base_dn/bind_dn, ldap_use_tls, is_active + AuditMixin; SsoGroupRoleMapping: sso_configuration_id FK, external_group_name, aman_role_id FK + unique constraint; SsoFallbackAdmin: sso_configuration_id FK, user_id FK)
- [x] T013 [P] [US1] Create Alembic migration for SSO tables: `backend/alembic/versions/xxx_add_sso_tables.py`
- [x] T014 [P] [US1] Create Pydantic schemas in `backend/schemas/sso.py` (SsoConfigCreate, SsoConfigUpdate, SsoConfigRead, GroupRoleMappingCreate, LdapTestRequest, SamlMetadataResponse)
- [x] T015 [US1] Implement sso_service.py in `backend/services/sso_service.py` — SAML SP init (python-saml), SAML ACS callback (parse assertion, extract groups, map to roles, provision user if new), LDAP bind auth (python-ldap with TLS on port 636), LDAP group lookup, test connection method, admin fallback check (query SsoFallbackAdmin when IdP unreachable)
- [x] T016 [US1] Extend auth router in `backend/routers/auth.py` — add SSO endpoints per contracts: GET /api/auth/sso/config, POST /api/auth/sso/config, PUT /api/auth/sso/config/{id}, DELETE /api/auth/sso/config/{id}, GET /api/auth/sso/saml/metadata, POST /api/auth/sso/saml/acs (public), POST /api/auth/sso/ldap/test, POST /api/auth/sso/login, GET+POST /api/auth/sso/mappings — all with appropriate permissions
- [x] T017 [US1] Add SSO login button and redirect flow to `frontend/src/pages/Login.jsx` — detect if SSO is configured for tenant, show "Login with SSO" button, redirect to IdP, handle return. Show fallback local login for designated admins when IdP unreachable.
- [x] T018 [P] [US1] Create SSO configuration admin pages in `frontend/src/pages/SSO/SsoConfigList.jsx` and `frontend/src/pages/SSO/SsoConfigForm.jsx` — CRUD for SSO configs, group-to-role mapping management, LDAP test connection button. Use DataTable and FormField patterns.
- [x] T019 [US1] Add AR+EN i18n keys for all SSO pages and login flow in `frontend/src/locales/en.json` and `frontend/src/locales/ar.json`
- [x] T020 [US1] Add SSO routes to `frontend/src/App.jsx` and navigation sidebar

**Checkpoint**: SSO/LDAP login functional — users can authenticate via corporate directory with auto-provisioning and admin fallback.

---

## Phase 4: User Story 2 — 3-Way Matching (Priority: P1)

**Goal**: Auto-match PO↔GRN↔Invoice on invoice entry with configurable % and absolute tolerances. Flag discrepancies before payment.

**Independent Test**: Create PO, receive goods partially, submit invoice, verify quantity/price variances flagged correctly.

### Implementation for User Story 2

- [x] T021 [P] [US2] Create MatchTolerance, ThreeWayMatch, and ThreeWayMatchLine models in `backend/models/domain_models/procurement.py` per data-model.md (MatchTolerance: quantity_percent, quantity_absolute, price_percent, price_absolute, optional supplier_id FK, product_category_id FK; ThreeWayMatch: po_id FK, invoice_id FK, match_status enum, exception_approved_by FK; ThreeWayMatchLine: match_id FK, po_line_id FK, grn_ids JSONB, invoice_line_id FK, all variance fields Numeric(18,4), tolerance_id FK, line_status enum)
- [x] T022 [P] [US2] Create Alembic migration for matching tables: `backend/alembic/versions/xxx_add_matching_tables.py`
- [x] T023 [P] [US2] Create Pydantic schemas in `backend/schemas/matching.py` (MatchToleranceCreate, MatchToleranceRead, ThreeWayMatchRead, ThreeWayMatchLineRead, MatchApproveRequest)
- [x] T024 [US2] Implement matching_service.py in `backend/services/matching_service.py` — auto-match triggered on PurchaseInvoice creation: for each invoice line, find PO line, sum all GRN quantities for that PO line, compute quantity and price variances (Decimal), compare against tolerance (pass if either % or absolute threshold met), set line_status and overall match_status, use SELECT FOR UPDATE on PO and GRN records per constitution VI
- [x] T025 [US2] Hook matching_service into purchase invoice creation flow in `backend/routers/purchases.py` — call matching_service.perform_match() after invoice is saved, set invoice status based on match result (auto-approved vs held), dispatch notification via notification_service for held invoices
- [x] T026 [US2] Add matching management endpoints to `backend/routers/purchases.py` per contracts: GET /api/purchases/matching (list, filter by status), GET /api/purchases/matching/{id} (detail with lines), POST /api/purchases/matching/{id}/approve, POST /api/purchases/matching/{id}/reject, GET+POST /api/purchases/matching/tolerances
- [x] T027 [P] [US2] Create matching frontend pages in `frontend/src/pages/Matching/MatchList.jsx` (DataTable with status filter, color-coded rows), `frontend/src/pages/Matching/MatchDetail.jsx` (line-level variance display with PO/GRN/Invoice side-by-side, approve/reject buttons), `frontend/src/pages/Matching/ToleranceConfig.jsx` (FormField for tolerance CRUD)
- [x] T028 [US2] Add AR+EN i18n keys for matching pages in `frontend/src/locales/en.json` and `frontend/src/locales/ar.json`
- [x] T029 [US2] Add matching routes to `frontend/src/App.jsx` and procurement navigation

**Checkpoint**: 3-way matching auto-triggers on invoice entry — discrepancies flagged, approvals tracked, tolerances configurable.

---

## Phase 5: User Story 3 — Intercompany Accounting (Priority: P1)

**Goal**: Intercompany transactions auto-create reciprocal entries in both entities. Consolidation eliminates intercompany balances at each hierarchy level.

**Independent Test**: Create intercompany sale A→B, verify reciprocal entries, run consolidation, confirm eliminations net to zero.

### Implementation for User Story 3

- [X] T030 [P] [US3] Create EntityGroup, IntercompanyTransaction, and IntercompanyAccountMapping models in `backend/models/domain_models/finance.py` per data-model.md (EntityGroup: parent_id self-referential FK, company_id FK, group_currency, consolidation_level; IntercompanyTransaction: source/target entity FKs, amounts per entity Numeric(18,4), exchange_rate Numeric(18,8), source/target journal_entry_id FKs, elimination_status enum, elimination_journal_entry_id FK; IntercompanyAccountMapping: source/target entity and account FKs)
- [X] T031 [P] [US3] Create Alembic migration for intercompany tables: `backend/alembic/versions/xxx_add_intercompany_tables.py`
- [X] T032 [P] [US3] Create Pydantic schemas in `backend/schemas/intercompany.py` (EntityGroupCreate, EntityGroupTree, IntercompanyTransactionCreate, IntercompanyTransactionRead, ConsolidationRequest, ConsolidationResult, AccountMappingCreate)
- [X] T033 [US3] Implement intercompany service in `backend/services/intercompany_service.py` — create_transaction (post reciprocal JEs via gl_service in both entity DBs using get_db_connection for each, lock exchange rate, handle multi-currency), run_consolidation (traverse entity tree bottom-up, generate elimination JEs at each level via gl_service, verify eliminations net to zero), get_intercompany_balances (report outstanding IC balances)
- [X] T034 [US3] Create intercompany router in `backend/routers/finance/intercompany.py` per contracts: GET /entities (tree), POST /entities, POST /transactions, GET /transactions, GET /transactions/{id}, POST /consolidate, GET /balances, GET+POST /mappings — all with permissions
- [X] T035 [US3] Register intercompany router in module `__init__.py`
- [X] T036 [P] [US3] Create intercompany frontend pages in `frontend/src/pages/Intercompany/EntityGroupTree.jsx` (visual hierarchy), `frontend/src/pages/Intercompany/TransactionList.jsx` (DataTable), `frontend/src/pages/Intercompany/TransactionForm.jsx` (FormField with entity selectors and currency), `frontend/src/pages/Intercompany/ConsolidationView.jsx` (run consolidation, view elimination report), `frontend/src/pages/Intercompany/AccountMappings.jsx` (mapping CRUD)
- [X] T037 [US3] Add AR+EN i18n keys for intercompany pages in `frontend/src/locales/en.json` and `frontend/src/locales/ar.json`
- [X] T038 [US3] Add intercompany routes to `frontend/src/App.jsx` and finance navigation

**Checkpoint**: Intercompany transactions create reciprocal entries across entities. Consolidation eliminates IC balances at each hierarchy level.

---

## Phase 6: User Story 4 — FIFO/LIFO Costing (Priority: P1)

**Goal**: FIFO and LIFO costing methods per product/warehouse alongside existing WAC. Cost layers consumed in order, negative inventory blocked.

**Independent Test**: Set product to FIFO, purchase at different prices, sell units, verify COGS uses earliest cost layer.

### Implementation for User Story 4

- [X] T039 [P] [US4] Create CostLayer and CostLayerConsumption models in `backend/models/domain_models/inventory.py` per data-model.md (CostLayer: product_id FK, warehouse_id FK, costing_method enum, purchase_date, original_quantity, remaining_quantity Numeric(18,4), unit_cost Numeric(18,4), source_document_type enum, source_document_id, is_exhausted Boolean, CHECK remaining_quantity >= 0; CostLayerConsumption: cost_layer_id FK, quantity_consumed, sale_document_type enum, sale_document_id, consumed_at)
- [X] T040 [P] [US4] Create Alembic migration for cost layer tables with CHECK constraint and composite index: `backend/alembic/versions/xxx_add_cost_layer_tables.py`
- [X] T041 [P] [US4] Create Pydantic schemas in `backend/schemas/costing.py` (CostLayerRead, CostingMethodChange, InventoryValuationReport, ConsumptionHistoryRead)
- [X] T042 [US4] Extend costing_service.py in `backend/services/costing_service.py` — add create_cost_layer() on purchase receipt, consume_layers() on sale (FIFO: ASC purchase_date, LIFO: DESC purchase_date, use SELECT FOR UPDATE per constitution VI, block if insufficient remaining_quantity), handle_return() (add back at original cost layer), change_costing_method() (revalue existing inventory, create opening layer), calculate_inventory_valuation()
- [X] T043 [US4] Hook cost layer creation into purchase invoice/receipt flow in `backend/routers/purchases.py` and sale consumption into invoice/POS flow in `backend/routers/sales/` and `backend/routers/pos.py` — call costing_service methods when product uses FIFO/LIFO
- [X] T044 [US4] Create costing router in `backend/routers/inventory/costing.py` per contracts: GET /layers (filter by product/warehouse), GET /layers/{product_id}, PUT /method (change costing method), GET /valuation (report), GET /consumption/{product_id}
- [X] T045 [US4] Register costing router in module `__init__.py`
- [X] T046 [P] [US4] Create costing frontend pages in `frontend/src/pages/Costing/CostLayerList.jsx` (DataTable showing layers per product), `frontend/src/pages/Costing/CostingMethodForm.jsx` (FormField to change method per product/warehouse), `frontend/src/pages/Costing/ValuationReport.jsx` (inventory valuation by costing method)
- [X] T047 [US4] Add AR+EN i18n keys for costing pages in `frontend/src/locales/en.json` and `frontend/src/locales/ar.json`
- [X] T048 [US4] Add costing routes to `frontend/src/App.jsx` and inventory navigation

**Checkpoint**: FIFO/LIFO costing functional — cost layers created on purchase, consumed on sale in correct order, negative inventory blocked.

---

## Phase 7: User Story 5 — Cash Flow Forecasting (Priority: P2)

**Goal**: Project future cash inflows/outflows from AR aging, AP aging, recurring entries, and historical payment patterns.

**Independent Test**: With existing AR/AP, generate 90-day forecast, verify projections match expected timing.

### Implementation for User Story 5

- [x] T049 [P] [US5] Create CashFlowForecast and CashFlowForecastLine models in `backend/models/domain_models/finance.py` per data-model.md
- [x] T050 [P] [US5] Create Alembic migration for cash flow tables: `backend/alembic/versions/xxx_add_cashflow_tables.py`
- [x] T051 [P] [US5] Create Pydantic schemas in `backend/schemas/cashflow.py` (ForecastGenerateRequest with horizon_days and mode enum, ForecastRead, ForecastLineRead)
- [x] T052 [US5] Implement forecast logic in `backend/services/forecast_service.py` — generate_cashflow_forecast() with "contractual" mode (AR/AP due dates as-is) and "expected" mode (adjust by average days late per customer/supplier), include recurring entries, compute running balance per bank account and consolidated, all amounts Decimal
- [x] T053 [US5] Create cashflow router in `backend/routers/finance/cashflow.py` per contracts: POST /generate, GET / (list), GET /{id} (detail), DELETE /{id}
- [x] T054 [US5] Register cashflow router in module `__init__.py`
- [x] T055 [P] [US5] Create cash flow frontend pages in `frontend/src/pages/CashFlow/ForecastList.jsx` (DataTable), `frontend/src/pages/CashFlow/ForecastGenerate.jsx` (FormField with horizon/mode selection), `frontend/src/pages/CashFlow/ForecastDetail.jsx` (line chart of projected balance over time + table of inflows/outflows)
- [x] T056 [US5] Add AR+EN i18n keys for cash flow pages in `frontend/src/locales/en.json` and `frontend/src/locales/ar.json`
- [x] T057 [US5] Add cash flow routes to `frontend/src/App.jsx` and treasury navigation

**Checkpoint**: Cash flow forecasting generates projections per bank account with contractual and expected modes.

---

## Phase 8: User Story 6 — Employee Self-Service (Priority: P2)

**Goal**: Employees submit leave requests, view payslips, update profiles. Managers approve leave requests. Reduces HR workload by 70%.

**Independent Test**: Log in as employee, submit leave, view payslip, update phone number, verify leave balance.

### Implementation for User Story 6

- [x] T058 [P] [US6] Create SelfServiceRequest model in `backend/models/domain_models/hr.py` per data-model.md
- [x] T059 [P] [US6] Create Alembic migration for self-service table: `backend/alembic/versions/xxx_add_self_service_tables.py`
- [x] T060 [P] [US6] Create Pydantic schemas in `backend/schemas/self_service.py` (LeaveRequestCreate, ProfileUpdateRequest, SelfServiceRequestRead, PayslipRead, LeaveBalanceRead)
- [x] T061 [US6] Create self-service router in `backend/routers/hr/self_service.py` per contracts: GET /profile, PUT /profile, GET /payslips, GET /payslips/{id}, GET /leave-balance, POST /leave-request, GET /leave-requests, GET /team-requests, POST /leave-request/{id}/approve, POST /leave-request/{id}/reject — dispatch notifications on submit/approve/reject via notification_service
- [x] T062 [US6] Register self-service router in module `__init__.py`
- [x] T063 [P] [US6] Create self-service frontend pages in `frontend/src/pages/SelfService/EmployeeDashboard.jsx` (leave balance, recent payslips, pending requests), `frontend/src/pages/SelfService/LeaveRequestForm.jsx` (FormField), `frontend/src/pages/SelfService/PayslipList.jsx` (DataTable), `frontend/src/pages/SelfService/PayslipDetail.jsx`, `frontend/src/pages/SelfService/ProfileEdit.jsx` (FormField), `frontend/src/pages/SelfService/TeamRequests.jsx` (manager view, DataTable with approve/reject)
- [x] T064 [US6] Add AR+EN i18n keys for self-service pages in `frontend/src/locales/en.json` and `frontend/src/locales/ar.json`
- [x] T065 [US6] Add self-service routes to `frontend/src/App.jsx` and HR navigation

**Checkpoint**: Employee self-service portal functional — leave, payslips, profile, manager approval all working.

---

## Phase 9: User Story 7 — Mobile App (Priority: P2)

**Goal**: React Native app for inventory view, quotations, orders, workflow approvals with offline sync.

**Independent Test**: Log in on mobile, create quotation, lose connectivity, continue offline, reconnect, verify sync.

### Implementation for User Story 7

- [X] T066 [P] [US7] Create SyncQueue model in `backend/models/domain_models/operations.py` per data-model.md
- [X] T067 [P] [US7] Create Alembic migration for sync_queue table: `backend/alembic/versions/xxx_add_sync_queue_table.py`
- [X] T068 [P] [US7] Create mobile-specific API endpoints in `backend/routers/mobile.py` per contracts: POST /sync (batch), GET /sync/status, POST /sync/resolve (conflict), GET /dashboard, POST /register-device — register in module `__init__.py`
- [X] T069 [US7] Implement mobile sync logic in backend: batch sync endpoint receives array of offline changes, detect conflicts (same entity modified by both mobile and web), store conflicts in SyncQueue, return sync results
- [X] T070 [P] [US7] Initialize React Native project in `mobile/` with navigation (React Navigation), state management, and authentication (reuse JWT cookie flow)
- [X] T071 [US7] Implement offline sync service in `mobile/src/services/syncService.js` — queue offline operations in SQLite, background sync on connectivity, idempotent retry, timestamp reconciliation
- [X] T072 [US7] Implement conflict resolver in `mobile/src/services/conflictResolver.js` — detect conflicts, present both versions, manual resolution UI
- [X] T073 [US7] Implement push notification handler in `mobile/src/services/pushService.js` — register device with FCM, receive and display push notifications
- [X] T074 [P] [US7] Create mobile screens: `mobile/src/screens/Dashboard/DashboardScreen.jsx` (inventory levels, pending orders, pending approvals), `mobile/src/screens/Inventory/InventoryScreen.jsx` (browse products, stock levels), `mobile/src/screens/Quotations/QuotationForm.jsx` (create quotation), `mobile/src/screens/Orders/OrderList.jsx` (pending orders), `mobile/src/screens/Approvals/ApprovalList.jsx` (pending approvals with approve/reject)
- [X] T075 [US7] Create mobile offline storage layer in `mobile/src/store/offlineStore.js` — SQLite schema for cached inventory, quotations, orders, approvals; CRUD operations for offline access

**Checkpoint**: Mobile app functional — inventory, quotations, orders, approvals with offline sync and push notifications.

---

## Phase 10: User Story 8 — Subscription Billing (Priority: P2)

**Goal**: Subscription plans with trial periods, automated recurring invoices, proration on plan changes, cancellation, and failed payment handling.

**Independent Test**: Create plan, enroll customer, advance billing date, verify invoice generated. Test mid-cycle upgrade proration.

### Implementation for User Story 8

- [x] T076 [P] [US8] Create SubscriptionPlan, SubscriptionEnrollment, and SubscriptionInvoice models in `backend/models/domain_models/finance.py` per data-model.md (include trial_period_days on plan, trial_end_date and failed_payment_count on enrollment, status enum with "trial" state)
- [x] T077 [P] [US8] Create Alembic migration for subscription tables: `backend/alembic/versions/xxx_add_subscription_tables.py`
- [x] T078 [P] [US8] Create Pydantic schemas in `backend/schemas/subscription.py` (PlanCreate, PlanRead, EnrollmentCreate, EnrollmentRead, PlanChangeRequest, SubscriptionInvoiceRead)
- [x] T079 [US8] Implement subscription_service.py in `backend/services/subscription_service.py` — enroll_customer (set trial_end_date if trial_period_days > 0, status = "trial"), generate_invoice (create invoice via existing invoicing, link via SubscriptionInvoice, all amounts Decimal with ROUND_HALF_UP), prorate_plan_change (credit unused + charge new prorated), cancel (generate final prorated invoice if applicable), handle_failed_payment (increment counter, flag at_risk after 3), check_trial_expirations (auto-convert trial → active)
- [x] T080 [US8] Add scheduled jobs to `backend/services/scheduler.py` — daily: check_billing_due (generate invoices for enrollments where next_billing_date <= today), check_trial_expirations, retry_failed_payments — dispatch notifications via notification_service for each event
- [x] T081 [US8] Create subscription router in `backend/routers/finance/subscriptions.py` per contracts: GET+POST /plans, PUT /plans/{id}, POST /enroll, GET /enrollments, GET /enrollments/{id}, POST /enrollments/{id}/pause|resume|cancel|change-plan
- [x] T082 [US8] Register subscription router in module `__init__.py`
- [x] T083 [P] [US8] Create subscription frontend pages in `frontend/src/pages/Subscription/PlanList.jsx` (DataTable), `frontend/src/pages/Subscription/PlanForm.jsx` (FormField with trial_period_days), `frontend/src/pages/Subscription/EnrollmentList.jsx` (DataTable with status badges), `frontend/src/pages/Subscription/EnrollmentDetail.jsx` (billing history, plan change, pause/resume/cancel actions)
- [x] T084 [US8] Add AR+EN i18n keys for subscription pages in `frontend/src/locales/en.json` and `frontend/src/locales/ar.json`
- [x] T085 [US8] Add subscription routes to `frontend/src/App.jsx` and finance navigation

**Checkpoint**: Subscription billing functional — plans, trials, enrollment, recurring invoices, proration, cancellation.

---

## Phase 11: User Story 9 — BI Dashboard Integration (Priority: P2)

**Goal**: Embedded analytics dashboards with pre-built KPIs, date filters, branch-level access, 15-minute data refresh.

**Independent Test**: Open analytics page, verify KPIs load in <5s, filter by date range, confirm branch access control.

### Implementation for User Story 9

- [ ] T086 [P] [US9] Create Dashboard and DashboardWidget models in `backend/models/domain_models/operations.py` per data-model.md
- [ ] T087 [P] [US9] Create Alembic migration for dashboard tables: `backend/alembic/versions/xxx_add_dashboard_tables.py`
- [ ] T088 [P] [US9] Create materialized views for KPI data sources in a new Alembic migration: revenue_summary, expense_summary, cash_position, top_customers, inventory_turnover, ar_aging, ap_aging, sales_pipeline — refreshed by scheduler
- [ ] T089 [US9] Add scheduled job to `backend/services/scheduler.py` — refresh all materialized views every 15 minutes
- [ ] T090 [US9] Extend dashboard router in `backend/routers/dashboard.py` per contracts: GET /analytics (list dashboards filtered by user role + branch), GET /analytics/{id} (dashboard with widget data queried from materialized views), POST /analytics (create custom), PUT /analytics/{id}, GET /analytics/widget-data/{widget_id} (single widget refresh)
- [ ] T091 [P] [US9] Create analytics frontend pages in `frontend/src/pages/Analytics/DashboardList.jsx` (available dashboards), `frontend/src/pages/Analytics/DashboardView.jsx` (widget grid with chart components — bar, line, pie, gauge, table, KPI cards — date range filter, branch filter), `frontend/src/pages/Analytics/DashboardEditor.jsx` (drag-and-drop widget layout for custom dashboards)
- [ ] T092 [US9] Add AR+EN i18n keys for analytics pages in `frontend/src/locales/en.json` and `frontend/src/locales/ar.json`
- [ ] T093 [US9] Add analytics routes to `frontend/src/App.jsx` and main navigation

**Checkpoint**: BI dashboards load in <5s with pre-built KPIs, date/branch filtering, and 15-minute refresh.

---

## Phase 12: User Story 10 — Blanket Purchase Orders (Priority: P3)

**Goal**: Long-term supplier agreements with quantity/price terms, release orders against agreement, remaining balance tracking.

**Independent Test**: Create blanket PO, release 3 partial orders, verify remaining quantity/budget tracked correctly.

### Implementation for User Story 10

- [ ] T094 [P] [US10] Create BlanketPurchaseOrder and BlanketPOReleaseOrder models in `backend/models/domain_models/procurement.py` per data-model.md
- [ ] T095 [P] [US10] Create Alembic migration for blanket PO tables: `backend/alembic/versions/xxx_add_blanket_po_tables.py`
- [ ] T096 [P] [US10] Create Pydantic schemas in `backend/schemas/blanket_po.py` (BlanketPOCreate, BlanketPORead, ReleaseOrderCreate, PriceAmendRequest)
- [ ] T097 [US10] Add blanket PO endpoints to `backend/routers/purchases.py` per contracts: POST /blanket, GET /blanket, GET /blanket/{id}, POST /blanket/{id}/release (validate remaining quantity, warn if exceeds agreement), PUT /blanket/{id}/amend-price (effective date-based)
- [ ] T098 [P] [US10] Create blanket PO frontend pages in `frontend/src/pages/BlanketPO/BlanketPOList.jsx` (DataTable with status/remaining), `frontend/src/pages/BlanketPO/BlanketPOForm.jsx` (FormField), `frontend/src/pages/BlanketPO/BlanketPODetail.jsx` (releases list, remaining balance, price amendment history, release button)
- [ ] T099 [US10] Add AR+EN i18n keys and routes for blanket PO pages

**Checkpoint**: Blanket POs track agreements with releases, remaining balance, and price amendments.

---

## Phase 13: User Story 11 — Campaign Management (Priority: P3)

**Goal**: Create marketing campaigns targeted at customer segments, send via email/SMS, track engagement metrics, attribute leads.

**Independent Test**: Create campaign for segment, execute, verify delivery/open/click metrics recorded.

### Implementation for User Story 11

- [ ] T100 [P] [US11] Create Campaign, CampaignRecipient, and CampaignLeadAttribution models in `backend/models/domain_models/projects_crm.py` per data-model.md
- [ ] T101 [P] [US11] Create Alembic migration for campaign tables: `backend/alembic/versions/xxx_add_campaign_tables.py`
- [ ] T102 [P] [US11] Create Pydantic schemas in `backend/schemas/campaign.py` (CampaignCreate, CampaignRead, CampaignMetrics, RecipientStatusRead)
- [ ] T103 [US11] Implement campaign execution logic: extend `backend/routers/crm.py` — campaign CRUD, execute endpoint (iterate segment contacts, dispatch via notification_service email/SMS channels to external provider), tracking webhook (POST /webhook/track — signed, public — update recipient open/click/response timestamps), lead attribution. Per contracts.
- [ ] T104 [P] [US11] Create campaign frontend pages in `frontend/src/pages/Campaign/CampaignList.jsx` (DataTable with metrics summary), `frontend/src/pages/Campaign/CampaignForm.jsx` (FormField with segment selector, template editor, schedule), `frontend/src/pages/Campaign/CampaignReport.jsx` (metrics: sends, opens, clicks, responses, cost per lead)
- [ ] T105 [US11] Add AR+EN i18n keys and routes for campaign pages

**Checkpoint**: Campaign management sends to segments, tracks engagement, attributes leads.

---

## Phase 14: User Story 12 — Performance Reviews (Priority: P3)

**Goal**: Structured review cycles with goals, self-assessment, manager evaluation, composite scoring, deadline reminders.

**Independent Test**: Create cycle, launch, complete self-assessment and manager eval, verify composite score.

### Implementation for User Story 12

- [ ] T106 [P] [US12] Create ReviewCycle, PerformanceReview, and PerformanceGoal models in `backend/models/domain_models/hr.py` per data-model.md
- [ ] T107 [P] [US12] Create Alembic migration for performance review tables: `backend/alembic/versions/xxx_add_performance_tables.py`
- [ ] T108 [P] [US12] Create Pydantic schemas in `backend/schemas/performance.py` (ReviewCycleCreate, ReviewCycleRead, ReviewRead, SelfAssessmentSubmit, ManagerAssessmentSubmit, GoalCreate)
- [ ] T109 [US12] Create performance router in `backend/routers/hr/performance.py` per contracts: POST /cycles, GET /cycles, POST /cycles/{id}/launch (notify employees via notification_service), GET /reviews (own), PUT /reviews/{id}/self-assessment, GET /team-reviews (manager), PUT /reviews/{id}/manager-assessment, POST /reviews/{id}/finalize (compute composite score: weighted avg of manager scores) — add deadline reminder to scheduler
- [ ] T110 [US12] Register performance router in module `__init__.py`
- [ ] T111 [P] [US12] Create performance frontend pages in `frontend/src/pages/Performance/CycleList.jsx`, `frontend/src/pages/Performance/CycleForm.jsx`, `frontend/src/pages/Performance/SelfAssessment.jsx` (goal scores + comments), `frontend/src/pages/Performance/ManagerReview.jsx` (side-by-side self/manager), `frontend/src/pages/Performance/ReviewResult.jsx`
- [ ] T112 [US12] Add AR+EN i18n keys and routes for performance pages

**Checkpoint**: Performance reviews functional — cycles, goals, assessments, scoring, reminders.

---

## Phase 15: User Story 13 — CPQ (Priority: P3)

**Goal**: Guided product configuration with validation rules, tiered pricing, discount application, professional PDF quote generation.

**Independent Test**: Configure product with options, verify invalid combo blocked, pricing applied, PDF generated.

### Implementation for User Story 13

- [ ] T113 [P] [US13] Create ProductConfiguration, ConfigOptionGroup, ConfigOption, ConfigValidationRule, CpqPricingRule, CpqQuote, and CpqQuoteLine models in `backend/models/domain_models/sales.py` per data-model.md
- [ ] T114 [P] [US13] Create Alembic migration for CPQ tables: `backend/alembic/versions/xxx_add_cpq_tables.py`
- [ ] T115 [P] [US13] Create Pydantic schemas in `backend/schemas/cpq.py` (ConfigurationRead, OptionGroupRead, ValidateConfigRequest, PriceCalculationRequest, PriceCalculationResponse, QuoteCreate, QuoteRead, QuoteLineRead)
- [ ] T116 [US13] Implement cpq_service.py in `backend/services/cpq_service.py` — validate_configuration (check requires/excludes rules, detect circular dependencies), calculate_price (base + option adjustments, apply pricing rules in priority order: volume → customer → bundle, all Decimal), generate_pdf (use reportlab or similar to create professional quote document)
- [ ] T117 [US13] Create CPQ router in `backend/routers/sales/cpq.py` per contracts: GET /products (configurable), GET /products/{id}/configure, POST /validate, POST /price, POST /quotes, GET /quotes/{id}, POST /quotes/{id}/generate-pdf, POST /quotes/{id}/convert (to standard quotation)
- [ ] T118 [US13] Register CPQ router in module `__init__.py`
- [ ] T119 [P] [US13] Create CPQ frontend pages in `frontend/src/pages/CPQ/ConfigurableProducts.jsx` (DataTable), `frontend/src/pages/CPQ/Configurator.jsx` (guided step-by-step option selection with real-time validation and price preview), `frontend/src/pages/CPQ/QuoteList.jsx`, `frontend/src/pages/CPQ/QuoteDetail.jsx` (line items, PDF download, convert button)
- [ ] T120 [US13] Add AR+EN i18n keys and routes for CPQ pages

**Checkpoint**: CPQ functional — product configuration, validation, pricing, PDF quote, conversion to quotation.

---

## Phase 16: User Story 14 — Demand Forecasting (Priority: P3)

**Goal**: Statistical demand forecast from sales history with seasonality detection, confidence intervals, manual adjustment.

**Independent Test**: With 12+ months of history, generate 3-month forecast, verify projections with confidence intervals.

### Implementation for User Story 14

- [ ] T121 [P] [US14] Create DemandForecast and DemandForecastPeriod models in `backend/models/domain_models/inventory.py` per data-model.md
- [ ] T122 [P] [US14] Create Alembic migration for demand forecast tables: `backend/alembic/versions/xxx_add_demand_forecast_tables.py`
- [ ] T123 [P] [US14] Create Pydantic schemas in `backend/schemas/forecast.py` (ForecastGenerateRequest, ForecastRead, ForecastPeriodRead, ForecastAdjustRequest)
- [ ] T124 [US14] Implement demand forecasting in `backend/services/forecast_service.py` — generate_demand_forecast(): auto-select method based on history (>=12mo: seasonal_decomposition, >=3mo: exponential_smoothing, >=1mo: moving_average), compute confidence intervals, store forecast periods. Use Python statistics stdlib. manual_adjust(): update adjusted_quantity.
- [ ] T125 [US14] Create forecast router in `backend/routers/inventory/forecast.py` per contracts: POST /generate, GET / (list), GET /{id}, PUT /{id}/adjust — register in module `__init__.py`
- [ ] T126 [P] [US14] Create forecast frontend pages in `frontend/src/pages/Forecast/ForecastList.jsx` (DataTable), `frontend/src/pages/Forecast/ForecastGenerate.jsx` (product selector, horizon), `frontend/src/pages/Forecast/ForecastDetail.jsx` (chart with projected qty, confidence bands, editable adjustments)
- [ ] T127 [US14] Add AR+EN i18n keys and routes for forecast pages

**Checkpoint**: Demand forecasting generates projections with auto-selected method, confidence intervals, and manual adjustments.

---

## Phase 17: User Story 15 — Shop Floor Control (Priority: P3)

**Goal**: Real-time work order progress tracking by operation, delay alerts, supervisor dashboard.

**Independent Test**: Start work order, report progress at each operation, verify dashboard shows real-time status.

**Dependency**: Requires User Story 16 (Routing) to be completed first — shop floor operations reference routing operations.

### Implementation for User Story 15

- [ ] T128 [P] [US15] Create ShopFloorLog model in `backend/models/domain_models/manufacturing.py` per data-model.md
- [ ] T129 [P] [US15] Create Alembic migration for shop floor log table: `backend/alembic/versions/xxx_add_shopfloor_tables.py`
- [ ] T130 [P] [US15] Create Pydantic schemas in `backend/schemas/shopfloor.py` (StartOperationRequest, CompleteOperationRequest, ShopFloorDashboardResponse, WorkOrderProgressRead)
- [ ] T131 [US15] Create shopfloor router in `backend/routers/manufacturing/shopfloor.py` per contracts: GET /dashboard (all active work orders with current operation, status, ETA), POST /start (validate operation sequence — must complete N-1 first unless supervisor override), POST /complete (record output/scrap, check delay threshold, dispatch notification_service alert if delayed), POST /pause, GET /work-order/{id} (progress by operation)
- [ ] T132 [US15] Register shopfloor router in module `__init__.py`
- [ ] T133 [P] [US15] Create shop floor frontend pages in `frontend/src/pages/ShopFloor/ShopFloorDashboard.jsx` (real-time grid of active work orders with operation progress bars, color-coded delays), `frontend/src/pages/ShopFloor/OperationEntry.jsx` (operator screen: start/complete/pause with output qty and scrap)
- [ ] T134 [US15] Add AR+EN i18n keys and routes for shop floor pages
- [ ] T134a [US15] Implement WebSocket endpoint for live shop floor updates in `backend/routers/manufacturing/shopfloor.py` — broadcast operation status changes to connected supervisor dashboards within 30 seconds of operator reporting (per SC-015)
- [ ] T134b [US15] Connect ShopFloorDashboard component in `frontend/src/pages/ShopFloor/ShopFloorDashboard.jsx` to WebSocket — live progress bar updates and delay alert toasts without page refresh

**Checkpoint**: Shop floor dashboard shows real-time work order progress with WebSocket live updates and delay alerts.

---

## Phase 18: User Story 16 — Routing/Operations (Priority: P3)

**Goal**: Define production routings with operation sequences, work centers, time estimates, labor costing, alternative routings.

**Independent Test**: Define routing with 3 operations, create work order, verify operations appear in sequence with correct time/cost estimates.

### Implementation for User Story 16

- [ ] T135 [P] [US16] Create Routing and RoutingOperation models in `backend/models/domain_models/manufacturing.py` per data-model.md
- [ ] T136 [P] [US16] Create Alembic migration for routing tables: `backend/alembic/versions/xxx_add_routing_tables.py`
- [ ] T137 [P] [US16] Create Pydantic schemas in `backend/schemas/routing.py` (RoutingCreate, RoutingRead, OperationCreate, OperationRead)
- [ ] T138 [US16] Create routing router in `backend/routers/manufacturing/routing.py` per contracts: POST / (create routing with operations), GET / (list), GET /{id} (with operations), PUT /{id} (update), GET /product/{product_id} (routings for product)
- [ ] T139 [US16] Register routing router in module `__init__.py`
- [ ] T140 [US16] Integrate routing with work order creation in existing manufacturing flow — when creating a manufacturing order, auto-load default routing operations, calculate total estimated time = sum(setup_time + run_time_per_unit * qty), calculate labor cost = sum(operation_time * labor_rate_per_hour / 60)
- [ ] T141 [P] [US16] Create routing frontend pages in `frontend/src/pages/Routing/RoutingList.jsx` (DataTable), `frontend/src/pages/Routing/RoutingForm.jsx` (FormField with dynamic operation rows: sequence, name, work center, setup/run times, labor rate)
- [ ] T142 [US16] Add AR+EN i18n keys and routes for routing pages

**Checkpoint**: Routings define production steps with time/cost. Work orders use routings for scheduling and costing.

---

## Phase 19: User Story 17 — Time Tracking (Priority: P3)

**Goal**: Log time against project tasks with billable/non-billable classification, manager approval, project profitability reporting.

**Independent Test**: Log 8 billable hours, submit timesheet, manager approves, verify project profitability report.

### Implementation for User Story 17

- [ ] T143 [P] [US17] Create TimesheetEntry model in `backend/models/domain_models/projects_crm.py` per data-model.md
- [ ] T144 [P] [US17] Create Alembic migration for timesheet table: `backend/alembic/versions/xxx_add_timesheet_tables.py`
- [ ] T145 [P] [US17] Create Pydantic schemas in `backend/schemas/timetracking.py` (TimesheetEntryCreate, TimesheetEntryRead, WeeklySubmitRequest, ProfitabilityReport)
- [ ] T146 [US17] Extend projects router in `backend/routers/projects.py` per contracts: POST /timetracking (log entry), GET /timetracking (own, filterable), PUT /timetracking/{id}, POST /timetracking/submit-week, GET /timetracking/team (manager), POST /timetracking/{id}/approve|reject, GET /timetracking/profitability/{project_id} (sum billable hours * rate vs project budget)
- [ ] T147 [P] [US17] Create time tracking frontend pages in `frontend/src/pages/TimeTracking/TimesheetWeek.jsx` (weekly grid with project/task per row, days as columns, hours per cell, submit button), `frontend/src/pages/TimeTracking/TeamTimesheets.jsx` (manager view, DataTable with approve/reject), `frontend/src/pages/TimeTracking/ProjectProfitability.jsx` (billable revenue vs budget chart)
- [ ] T148 [US17] Add AR+EN i18n keys and routes for time tracking pages

**Checkpoint**: Time tracking with weekly timesheets, approval workflow, and project profitability reporting.

---

## Phase 20: User Story 18 — Resource Planning (Priority: P3)

**Goal**: View team availability, allocate resources across projects, warn on over-allocation (>100%).

**Independent Test**: Allocate developer at 80% to Project A, try 40% to Project B, verify 120% over-allocation warning.

### Implementation for User Story 18

- [ ] T149 [P] [US18] Create ResourceAllocation model in `backend/models/domain_models/projects_crm.py` per data-model.md
- [ ] T150 [P] [US18] Create Alembic migration for resource allocation table: `backend/alembic/versions/xxx_add_resource_tables.py`
- [ ] T151 [P] [US18] Create Pydantic schemas in `backend/schemas/resource.py` (AllocationCreate, AllocationRead, AvailabilityCalendarResponse)
- [ ] T152 [US18] Extend projects router in `backend/routers/projects.py` per contracts: GET /resources/availability (compute sum of allocation_percent per employee for overlapping date ranges, flag >100%), POST /resources/allocate (validate, warn if over-allocation), PUT /resources/allocate/{id}, DELETE /resources/allocate/{id}, GET /resources/project/{project_id}
- [ ] T153 [P] [US18] Create resource planning frontend pages in `frontend/src/pages/ResourcePlanning/AvailabilityCalendar.jsx` (heatmap grid: employees as rows, weeks as columns, color by allocation %), `frontend/src/pages/ResourcePlanning/AllocationForm.jsx` (FormField with employee/project/percentage/dates), `frontend/src/pages/ResourcePlanning/ProjectResources.jsx` (DataTable of allocations per project)
- [ ] T154 [US18] Add AR+EN i18n keys and routes for resource planning pages

**Checkpoint**: Resource planning shows availability, allocations, and over-allocation warnings.

---

## Phase 21: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories.

- [ ] T155 [P] Add all new router registrations to module `__init__.py` files — verify all 18 features' routers are included with correct prefixes and tags
- [ ] T156 [P] Add all new frontend routes to `frontend/src/App.jsx` — verify all 18 features' pages are routable
- [ ] T157 [P] Update navigation sidebar in `frontend/src/components/Sidebar.jsx` — add menu items for all new modules grouped by category (Finance, HR, Procurement, Manufacturing, Projects, Sales, Analytics)
- [ ] T158 [P] Verify all new models use AuditMixin and SoftDeleteMixin per constitution XVII in all domain files
- [ ] T159 [P] Verify all monetary fields are Numeric(18,4) in all new models per constitution I
- [ ] T160 [P] Verify all new endpoints have `@require_permission()` decorators per constitution IV
- [ ] T161 Run full Alembic migration across test company databases to verify all migrations apply cleanly
- [ ] T162 Verify industry module flags in `backend/services/industry_gl_rules.py` — ensure new features respect industry-specific module activation
- [ ] T163 [P] Run quickstart.md verification checklist for all 18 features
- [ ] T164 Security review: verify SSO uses TLS, no secrets in logs, parameterized SQL, CORS for mobile
- [ ] T165 [P] Performance verification: benchmark SSO/LDAP auth latency against SC-001 target (<3 seconds) — test with SAML redirect + assertion parsing and LDAP bind under simulated load
- [ ] T166 [P] Performance verification: benchmark BI dashboard page load against SC-009 target (<5 seconds) — test with pre-built dashboard containing 6+ widgets, materialized views populated with realistic data volume
- [ ] T167 [P] Performance verification: benchmark demand forecast generation against SC-014 target (<30 seconds) — test with 12+ months of sales history across 100+ products

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories (unified notification service)
- **User Stories (Phases 3-20)**: All depend on Foundational phase completion
- **Polish (Phase 21)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (SSO/LDAP)**: Independent — can start after Phase 2
- **US2 (3-Way Matching)**: Independent — can start after Phase 2
- **US3 (Intercompany)**: Independent — can start after Phase 2
- **US4 (FIFO/LIFO)**: Independent — can start after Phase 2
- **US5 (Cash Flow)**: Independent — can start after Phase 2
- **US6 (Self-Service)**: Independent — can start after Phase 2
- **US7 (Mobile App)**: Best after US1 (SSO) for auth flow, but can start independently
- **US8 (Subscriptions)**: Independent — can start after Phase 2
- **US9 (BI Dashboards)**: Independent — can start after Phase 2
- **US10 (Blanket POs)**: Independent — can start after Phase 2
- **US11 (Campaigns)**: Independent — can start after Phase 2
- **US12 (Performance Reviews)**: Independent — can start after Phase 2; enhanced if US6 (Self-Service) is done
- **US13 (CPQ)**: Independent — can start after Phase 2
- **US14 (Demand Forecasting)**: Independent — can start after Phase 2
- **US15 (Shop Floor)**: **Depends on US16 (Routing)** — operations reference routing operations
- **US16 (Routing)**: Independent — can start after Phase 2; **must complete before US15**
- **US17 (Time Tracking)**: Independent — can start after Phase 2
- **US18 (Resource Planning)**: Independent — can start after Phase 2; enhanced if US17 (Time Tracking) is done

### Within Each User Story

- Models before services
- Services before endpoints/routers
- Routers before frontend pages
- Register routers in module __init__.py after creation
- i18n keys with frontend pages

### Parallel Opportunities

- All [P] tasks within a phase can run in parallel
- After Phase 2, up to 16 independent stories can run in parallel (US15 must wait for US16)
- With 3-4 developers: assign 1 story per developer, work through tiers in priority order

---

## Parallel Examples

### Phase 2 (Foundational): Notification models + schemas in parallel

```
Task T005: Create Notification models in backend/models/domain_models/operations.py
Task T007: Create Pydantic schemas in backend/schemas/notification.py
```

### Phase 3 (US1 — SSO): Models + migration + schemas in parallel

```
Task T012: Create SSO models in backend/models/domain_models/core.py
Task T013: Create Alembic migration for SSO tables
Task T014: Create Pydantic schemas in backend/schemas/sso.py
```

### Cross-Story Parallelism: 4 developers after Phase 2

```
Developer A: US1 (SSO) → US5 (Cash Flow) → US10 (Blanket POs) → US14 (Forecast)
Developer B: US2 (3-Way Match) → US6 (Self-Service) → US11 (Campaigns) → US16 (Routing) → US15 (Shop Floor)
Developer C: US3 (Intercompany) → US7 (Mobile) → US12 (Performance) → US17 (Time Tracking)
Developer D: US4 (FIFO/LIFO) → US8 (Subscriptions) → US9 (BI) → US13 (CPQ) → US18 (Resource Planning)
```

---

## Implementation Strategy

### MVP First (Tier 1 Only — US1-US4)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (notification service)
3. Complete Phases 3-6: US1 (SSO) + US2 (3-Way Match) + US3 (Intercompany) + US4 (FIFO/LIFO)
4. **STOP and VALIDATE**: Test all 4 P1 stories independently
5. Deploy — enterprise essentials are live

### Incremental Delivery

1. Setup + Foundational → Notification service ready
2. Tier 1 (US1-US4) → Enterprise essentials live (MVP!)
3. Tier 2 (US5-US9) → Competitive parity achieved
4. Tier 3 (US10-US18) → Market differentiation complete
5. Polish → Cross-cutting cleanup

### Parallel Team Strategy (3-4 Developers)

1. All developers complete Setup + Foundational together (1 week)
2. Tier 1 (4 stories, 4 developers): 1 story each → all P1 done in ~3 weeks
3. Tier 2 (5 stories, 4 developers): distribute → done in ~5 weeks
4. Tier 3 (9 stories, 4 developers): distribute → done in ~8 weeks
5. Polish: 1 week together

**Estimated total with 4 developers: ~18 weeks for all 18 features**

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- US16 (Routing) MUST complete before US15 (Shop Floor)
- All notifications route through the unified notification_service (Phase 2)
- All monetary calculations use Decimal with ROUND_HALF_UP per constitution I
- All journal entries route through gl_service.py per constitution III
- All new models use AuditMixin per constitution XVII
