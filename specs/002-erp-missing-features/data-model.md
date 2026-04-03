# Data Model: AMAN ERP — 18 Missing Competitive Features

**Branch**: `002-erp-missing-features` | **Date**: 2026-04-02

All models use `AuditMixin` (created_at, updated_at, created_by, updated_by) and `SoftDeleteMixin` where appropriate. All monetary fields use `NUMERIC(18,4)`. All models are tenant-scoped (per-company database).

---

## Tier 1 — Enterprise Essentials

### SSO Configuration

```
SsoConfiguration
├── id: Integer (PK)
├── provider_type: String (enum: "saml", "ldap")
├── display_name: String
├── metadata_url: String (nullable, SAML)
├── metadata_xml: Text (nullable, SAML)
├── ldap_host: String (nullable, LDAP)
├── ldap_port: Integer (nullable, LDAP)
├── ldap_base_dn: String (nullable, LDAP)
├── ldap_bind_dn: String (nullable, LDAP)
├── ldap_use_tls: Boolean (default: true)
├── is_active: Boolean (default: false)
└── AuditMixin

SsoGroupRoleMapping
├── id: Integer (PK)
├── sso_configuration_id: Integer (FK → SsoConfiguration)
├── external_group_name: String
├── aman_role_id: Integer (FK → Role)
└── AuditMixin

SsoFallbackAdmin
├── id: Integer (PK)
├── sso_configuration_id: Integer (FK → SsoConfiguration)
├── user_id: Integer (FK → User)
└── AuditMixin
```

**Relationships**: SsoConfiguration 1→N SsoGroupRoleMapping, SsoConfiguration 1→N SsoFallbackAdmin  
**Uniqueness**: (sso_configuration_id, external_group_name) unique per mapping  
**State**: SsoConfiguration.is_active — only one active per provider_type

---

### 3-Way Match

```
MatchTolerance
├── id: Integer (PK)
├── name: String
├── quantity_percent: Numeric(5,2)
├── quantity_absolute: Numeric(18,4)
├── price_percent: Numeric(5,2)
├── price_absolute: Numeric(18,4)
├── supplier_id: Integer (FK → Party, nullable — override per supplier)
├── product_category_id: Integer (FK → ProductCategory, nullable)
└── AuditMixin

ThreeWayMatch
├── id: Integer (PK)
├── purchase_order_id: Integer (FK → PurchaseOrder)
├── invoice_id: Integer (FK → PurchaseInvoice)
├── match_status: String (enum: "matched", "held", "approved_with_exception", "rejected")
├── matched_at: DateTime
├── matched_by: Integer (FK → User, nullable — null if auto)
├── exception_approved_by: Integer (FK → User, nullable)
├── exception_notes: Text (nullable)
└── AuditMixin

ThreeWayMatchLine
├── id: Integer (PK)
├── match_id: Integer (FK → ThreeWayMatch)
├── po_line_id: Integer (FK → PurchaseOrderLine)
├── grn_ids: JSONB (array of GRN line IDs — supports multiple partial GRNs)
├── invoice_line_id: Integer (FK → PurchaseInvoiceLine)
├── po_quantity: Numeric(18,4)
├── received_quantity: Numeric(18,4)
├── invoiced_quantity: Numeric(18,4)
├── po_unit_price: Numeric(18,4)
├── invoiced_unit_price: Numeric(18,4)
├── quantity_variance_pct: Numeric(5,2)
├── quantity_variance_abs: Numeric(18,4)
├── price_variance_pct: Numeric(5,2)
├── price_variance_abs: Numeric(18,4)
├── tolerance_id: Integer (FK → MatchTolerance)
├── line_status: String (enum: "matched", "quantity_mismatch", "price_mismatch", "both_mismatch")
└── AuditMixin
```

**Relationships**: ThreeWayMatch 1→N ThreeWayMatchLine  
**Trigger**: Auto-created on PurchaseInvoice.status = "submitted"

---

### Intercompany

```
EntityGroup
├── id: Integer (PK)
├── name: String
├── parent_id: Integer (FK → EntityGroup, nullable — self-referential for hierarchy)
├── company_id: Integer (FK → Company — the company this entity represents)
├── group_currency: String (ISO 4217)
├── consolidation_level: Integer (computed from tree depth)
└── AuditMixin

IntercompanyTransaction
├── id: Integer (PK)
├── source_entity_id: Integer (FK → EntityGroup)
├── target_entity_id: Integer (FK → EntityGroup)
├── transaction_type: String (enum: "sale", "purchase", "service", "loan", "transfer")
├── source_amount: Numeric(18,4)
├── source_currency: String
├── target_amount: Numeric(18,4)
├── target_currency: String
├── exchange_rate: Numeric(18,8)
├── source_journal_entry_id: Integer (FK → JournalEntry)
├── target_journal_entry_id: Integer (FK → JournalEntry)
├── elimination_status: String (enum: "pending", "eliminated", "partial")
├── elimination_journal_entry_id: Integer (FK → JournalEntry, nullable)
├── reference_document: String (nullable — e.g., "SO-001", "PO-042")
└── AuditMixin

IntercompanyAccountMapping
├── id: Integer (PK)
├── source_entity_id: Integer (FK → EntityGroup)
├── target_entity_id: Integer (FK → EntityGroup)
├── source_account_id: Integer (FK → Account)
├── target_account_id: Integer (FK → Account)
└── AuditMixin
```

**Relationships**: EntityGroup self-referential (parent-child), IntercompanyTransaction → 2x EntityGroup, 2x JournalEntry  
**Constraint**: source_entity_id != target_entity_id  
**State**: elimination_status: pending → eliminated (after consolidation run)

---

### FIFO/LIFO Cost Layers

```
CostLayer
├── id: Integer (PK)
├── product_id: Integer (FK → Product)
├── warehouse_id: Integer (FK → Warehouse)
├── costing_method: String (enum: "fifo", "lifo")
├── purchase_date: Date
├── original_quantity: Numeric(18,4)
├── remaining_quantity: Numeric(18,4)
├── unit_cost: Numeric(18,4)
├── source_document_type: String (enum: "purchase_invoice", "opening_balance", "return", "adjustment")
├── source_document_id: Integer
├── is_exhausted: Boolean (default: false)
└── AuditMixin

CostLayerConsumption
├── id: Integer (PK)
├── cost_layer_id: Integer (FK → CostLayer)
├── quantity_consumed: Numeric(18,4)
├── sale_document_type: String (enum: "sales_invoice", "pos_order", "adjustment")
├── sale_document_id: Integer
├── consumed_at: DateTime
└── AuditMixin
```

**Relationships**: CostLayer 1→N CostLayerConsumption  
**Constraint**: remaining_quantity >= 0 (CHECK constraint — prevents negative inventory)  
**Index**: (product_id, warehouse_id, is_exhausted, purchase_date) for FIFO layer lookup  
**Ordering**: FIFO = ASC purchase_date, LIFO = DESC purchase_date

---

## Tier 2 — Competitive Parity

### Cash Flow Forecast

```
CashFlowForecast
├── id: Integer (PK)
├── name: String
├── forecast_date: Date (when generated)
├── horizon_days: Integer (e.g., 30, 60, 90)
├── mode: String (enum: "contractual", "expected")
├── generated_by: Integer (FK → User)
└── AuditMixin

CashFlowForecastLine
├── id: Integer (PK)
├── forecast_id: Integer (FK → CashFlowForecast)
├── date: Date
├── bank_account_id: Integer (FK → TreasuryAccount, nullable — null for consolidated)
├── source_type: String (enum: "ar", "ap", "recurring", "manual")
├── source_document_id: Integer (nullable)
├── projected_inflow: Numeric(18,4) (default: 0)
├── projected_outflow: Numeric(18,4) (default: 0)
├── projected_balance: Numeric(18,4) (running balance)
└── AuditMixin
```

---

### Employee Self-Service

```
SelfServiceRequest
├── id: Integer (PK)
├── employee_id: Integer (FK → Employee)
├── request_type: String (enum: "leave", "profile_update", "document_request")
├── details: JSONB (type-specific payload)
├── status: String (enum: "draft", "pending", "approved", "rejected", "completed")
├── approver_id: Integer (FK → Employee, nullable)
├── approved_at: DateTime (nullable)
├── rejection_reason: Text (nullable)
└── AuditMixin
```

**State machine**: draft → pending → approved/rejected → completed  
**Note**: Leave requests use existing `LeaveRequest` model; this extends with self-service wrapper and profile update tracking.

---

### Subscription Billing

```
SubscriptionPlan
├── id: Integer (PK)
├── name: String
├── description: Text
├── billing_frequency: String (enum: "monthly", "quarterly", "annual")
├── base_amount: Numeric(18,4)
├── currency: String (ISO 4217)
├── trial_period_days: Integer (default: 0)
├── auto_renewal: Boolean (default: true)
├── is_active: Boolean (default: true)
└── AuditMixin

SubscriptionEnrollment
├── id: Integer (PK)
├── customer_id: Integer (FK → Party)
├── plan_id: Integer (FK → SubscriptionPlan)
├── enrollment_date: Date
├── trial_end_date: Date (nullable)
├── next_billing_date: Date
├── status: String (enum: "trial", "active", "paused", "cancelled", "at_risk")
├── cancelled_at: DateTime (nullable)
├── cancellation_reason: Text (nullable)
├── failed_payment_count: Integer (default: 0)
└── AuditMixin

SubscriptionInvoice
├── id: Integer (PK)
├── enrollment_id: Integer (FK → SubscriptionEnrollment)
├── invoice_id: Integer (FK → Invoice — links to existing invoicing)
├── billing_period_start: Date
├── billing_period_end: Date
├── is_prorated: Boolean (default: false)
├── proration_details: JSONB (nullable)
└── AuditMixin
```

**State machine**: trial → active → paused ↔ active, active → cancelled, active → at_risk (3 failed payments) → cancelled  
**Scheduled job**: Daily check for billing due dates, trial expirations, payment retries

---

### BI Dashboard

```
Dashboard
├── id: Integer (PK)
├── name: String
├── description: Text
├── is_system: Boolean (default: false — system dashboards are pre-built)
├── access_roles: JSONB (array of role IDs)
├── branch_scope: String (enum: "all", "assigned" — branch-level access control)
├── refresh_interval_minutes: Integer (default: 15)
└── AuditMixin

DashboardWidget
├── id: Integer (PK)
├── dashboard_id: Integer (FK → Dashboard)
├── widget_type: String (enum: "kpi_card", "bar_chart", "line_chart", "pie_chart", "table", "gauge")
├── title: String
├── data_source: String (enum: "revenue", "expenses", "cash_position", "top_customers", "inventory_turnover", "ar_aging", "ap_aging", "sales_pipeline", "custom_query")
├── filters: JSONB (date range, branch, etc.)
├── position: JSONB ({row, col, width, height})
├── sort_order: Integer
└── AuditMixin
```

---

### Mobile Sync

```
SyncQueue
├── id: Integer (PK)
├── device_id: String
├── user_id: Integer (FK → User)
├── entity_type: String (e.g., "quotation", "sales_order")
├── entity_id: Integer
├── operation: String (enum: "create", "update")
├── payload: JSONB
├── device_timestamp: DateTime
├── server_timestamp: DateTime (nullable — set on sync)
├── sync_status: String (enum: "pending", "synced", "conflict", "resolved")
├── conflict_resolution: JSONB (nullable — stores both versions if conflict)
└── AuditMixin
```

---

## Tier 3 — Market Differentiation

### Blanket Purchase Order

```
BlanketPurchaseOrder
├── id: Integer (PK)
├── supplier_id: Integer (FK → Party)
├── agreement_number: String (unique)
├── total_quantity: Numeric(18,4)
├── unit_price: Numeric(18,4)
├── total_amount: Numeric(18,4)
├── released_quantity: Numeric(18,4) (default: 0)
├── released_amount: Numeric(18,4) (default: 0)
├── remaining_quantity: Numeric(18,4) (computed)
├── remaining_amount: Numeric(18,4) (computed)
├── valid_from: Date
├── valid_to: Date
├── status: String (enum: "draft", "active", "expired", "completed", "cancelled")
├── price_amendment_history: JSONB (array of {effective_date, old_price, new_price})
└── AuditMixin

BlanketPOReleaseOrder
├── id: Integer (PK)
├── blanket_po_id: Integer (FK → BlanketPurchaseOrder)
├── purchase_order_id: Integer (FK → PurchaseOrder)
├── release_quantity: Numeric(18,4)
├── release_amount: Numeric(18,4)
├── release_date: Date
└── AuditMixin
```

---

### Campaign Management

```
Campaign
├── id: Integer (PK)
├── name: String
├── campaign_type: String (enum: "email", "sms", "both")
├── segment_id: Integer (FK → CrmCustomerSegment)
├── subject: String (email subject / SMS header)
├── content: Text (template with merge fields)
├── scheduled_date: DateTime (nullable)
├── executed_at: DateTime (nullable)
├── status: String (enum: "draft", "scheduled", "executing", "completed", "cancelled")
├── total_sent: Integer (default: 0)
├── total_delivered: Integer (default: 0)
├── total_opened: Integer (default: 0)
├── total_clicked: Integer (default: 0)
├── total_responded: Integer (default: 0)
├── estimated_cost: Numeric(18,4)
├── actual_cost: Numeric(18,4)
└── AuditMixin

CampaignRecipient
├── id: Integer (PK)
├── campaign_id: Integer (FK → Campaign)
├── contact_id: Integer (FK → Party)
├── channel: String (enum: "email", "sms")
├── delivery_status: String (enum: "pending", "sent", "delivered", "bounced", "failed")
├── opened_at: DateTime (nullable)
├── clicked_at: DateTime (nullable)
├── responded_at: DateTime (nullable)
└── AuditMixin

CampaignLeadAttribution
├── id: Integer (PK)
├── campaign_id: Integer (FK → Campaign)
├── lead_id: Integer (FK → CrmLead)
├── attributed_at: DateTime
└── AuditMixin
```

---

### Performance Reviews

```
ReviewCycle
├── id: Integer (PK)
├── name: String
├── period_start: Date
├── period_end: Date
├── self_assessment_deadline: Date
├── manager_review_deadline: Date
├── status: String (enum: "draft", "active", "completed")
└── AuditMixin

PerformanceReview
├── id: Integer (PK)
├── cycle_id: Integer (FK → ReviewCycle)
├── employee_id: Integer (FK → Employee)
├── reviewer_id: Integer (FK → Employee — manager)
├── status: String (enum: "pending_self", "pending_manager", "completed")
├── self_assessment: JSONB (array of {goal_id, score, comments})
├── manager_assessment: JSONB (array of {goal_id, score, comments})
├── composite_score: Numeric(5,2) (nullable — calculated after both assessments)
├── final_comments: Text (nullable)
└── AuditMixin

PerformanceGoal
├── id: Integer (PK)
├── review_id: Integer (FK → PerformanceReview)
├── title: String
├── description: Text
├── weight: Numeric(5,2) (percentage, all goals sum to 100)
├── target: String
└── AuditMixin
```

**State machine**: ReviewCycle: draft → active → completed  
**State machine**: PerformanceReview: pending_self → pending_manager → completed

---

### CPQ (Configure Price Quote)

```
ProductConfiguration
├── id: Integer (PK)
├── product_id: Integer (FK → Product)
├── name: String
├── is_active: Boolean (default: true)
└── AuditMixin

ConfigOptionGroup
├── id: Integer (PK)
├── configuration_id: Integer (FK → ProductConfiguration)
├── name: String (e.g., "Size", "Color", "Material")
├── is_required: Boolean (default: true)
├── sort_order: Integer
└── AuditMixin

ConfigOption
├── id: Integer (PK)
├── group_id: Integer (FK → ConfigOptionGroup)
├── name: String (e.g., "Large", "Red", "Steel")
├── price_adjustment: Numeric(18,4) (default: 0 — added to base price)
├── is_default: Boolean (default: false)
├── sort_order: Integer
└── AuditMixin

ConfigValidationRule
├── id: Integer (PK)
├── configuration_id: Integer (FK → ProductConfiguration)
├── rule_type: String (enum: "requires", "excludes")
├── source_option_id: Integer (FK → ConfigOption)
├── target_option_id: Integer (FK → ConfigOption)
├── error_message: String
└── AuditMixin

CpqPricingRule
├── id: Integer (PK)
├── configuration_id: Integer (FK → ProductConfiguration)
├── rule_type: String (enum: "volume_discount", "customer_discount", "bundle_discount")
├── min_quantity: Integer (nullable)
├── max_quantity: Integer (nullable)
├── discount_percent: Numeric(5,2) (nullable)
├── discount_amount: Numeric(18,4) (nullable)
├── customer_group_id: Integer (FK → PartyGroup, nullable)
├── priority: Integer (evaluation order)
└── AuditMixin

CpqQuote
├── id: Integer (PK)
├── customer_id: Integer (FK → Party)
├── quotation_id: Integer (FK → Quotation, nullable — links to standard quotation)
├── total_amount: Numeric(18,4)
├── discount_total: Numeric(18,4)
├── final_amount: Numeric(18,4)
├── pdf_document_id: Integer (FK → Attachment, nullable)
├── status: String (enum: "draft", "sent", "accepted", "expired", "rejected")
├── valid_until: Date
└── AuditMixin

CpqQuoteLine
├── id: Integer (PK)
├── quote_id: Integer (FK → CpqQuote)
├── product_id: Integer (FK → Product)
├── selected_options: JSONB (array of option IDs)
├── quantity: Numeric(18,4)
├── base_unit_price: Numeric(18,4)
├── option_adjustments: Numeric(18,4)
├── discount_applied: Numeric(18,4)
├── final_unit_price: Numeric(18,4)
├── line_total: Numeric(18,4)
└── AuditMixin
```

---

### Demand Forecast

```
DemandForecast
├── id: Integer (PK)
├── product_id: Integer (FK → Product)
├── warehouse_id: Integer (FK → Warehouse, nullable — null for all warehouses)
├── forecast_method: String (enum: "moving_average", "exponential_smoothing", "seasonal_decomposition")
├── generated_date: Date
├── generated_by: Integer (FK → User)
├── history_months_used: Integer
└── AuditMixin

DemandForecastPeriod
├── id: Integer (PK)
├── forecast_id: Integer (FK → DemandForecast)
├── period_start: Date
├── period_end: Date
├── projected_quantity: Numeric(18,4)
├── confidence_lower: Numeric(18,4)
├── confidence_upper: Numeric(18,4)
├── manual_adjustment: Numeric(18,4) (default: 0)
├── adjusted_quantity: Numeric(18,4) (projected + manual_adjustment)
└── AuditMixin
```

---

### Shop Floor & Routing

```
Routing
├── id: Integer (PK)
├── name: String
├── product_id: Integer (FK → Product)
├── bom_id: Integer (FK → BillOfMaterial, nullable)
├── is_default: Boolean (default: false)
├── is_active: Boolean (default: true)
└── AuditMixin

RoutingOperation
├── id: Integer (PK)
├── routing_id: Integer (FK → Routing)
├── sequence: Integer
├── name: String (e.g., "Cutting", "Assembly", "QC")
├── work_center_id: Integer (FK → WorkCenter)
├── setup_time_minutes: Numeric(10,2)
├── run_time_per_unit_minutes: Numeric(10,2)
├── labor_rate_per_hour: Numeric(18,4)
└── AuditMixin

ShopFloorLog
├── id: Integer (PK)
├── work_order_id: Integer (FK → ManufacturingOrder)
├── routing_operation_id: Integer (FK → RoutingOperation)
├── operator_id: Integer (FK → Employee)
├── started_at: DateTime
├── completed_at: DateTime (nullable)
├── output_quantity: Numeric(18,4) (default: 0)
├── scrap_quantity: Numeric(18,4) (default: 0)
├── downtime_minutes: Numeric(10,2) (default: 0)
├── status: String (enum: "in_progress", "completed", "paused")
├── notes: Text (nullable)
└── AuditMixin
```

**Constraint**: sequence is enforced — operation N cannot start until N-1 is completed (unless supervisor override)

---

### Time Tracking

```
TimesheetEntry
├── id: Integer (PK)
├── employee_id: Integer (FK → Employee)
├── project_id: Integer (FK → Project)
├── task_id: Integer (FK → ProjectTask, nullable)
├── date: Date
├── hours: Numeric(5,2)
├── is_billable: Boolean (default: true)
├── billing_rate: Numeric(18,4) (nullable — from project or employee default)
├── description: Text (nullable)
├── status: String (enum: "draft", "submitted", "approved", "rejected")
├── approved_by: Integer (FK → Employee, nullable)
├── rejection_reason: Text (nullable)
└── AuditMixin
```

**Constraint**: hours > 0 AND hours <= 24  
**State machine**: draft → submitted → approved/rejected

---

### Resource Planning

```
ResourceAllocation
├── id: Integer (PK)
├── employee_id: Integer (FK → Employee)
├── project_id: Integer (FK → Project)
├── role: String (e.g., "developer", "designer", "qa")
├── allocation_percent: Numeric(5,2)
├── start_date: Date
├── end_date: Date
└── AuditMixin
```

**Validation**: Sum of allocation_percent per employee across overlapping date ranges must trigger warning at > 100%  
**Constraint**: start_date <= end_date, allocation_percent > 0 AND allocation_percent <= 100

---

### Unified Notifications

```
Notification
├── id: Integer (PK)
├── recipient_id: Integer (FK → User)
├── channel: String (enum: "email", "in_app", "push")
├── event_type: String (e.g., "leave_approved", "invoice_held", "review_reminder", "subscription_expiring")
├── feature_source: String (e.g., "self_service", "matching", "performance", "subscription")
├── title: String
├── body: Text
├── reference_type: String (nullable — entity type)
├── reference_id: Integer (nullable — entity ID)
├── status: String (enum: "pending", "sent", "delivered", "read", "failed")
├── sent_at: DateTime (nullable)
├── read_at: DateTime (nullable)
└── AuditMixin

NotificationPreference
├── id: Integer (PK)
├── user_id: Integer (FK → User)
├── event_type: String
├── email_enabled: Boolean (default: true)
├── in_app_enabled: Boolean (default: true)
├── push_enabled: Boolean (default: true)
└── AuditMixin
```

**Uniqueness**: (user_id, event_type) unique per NotificationPreference  
**Default**: If no preference exists for an event type, all channels are enabled

---

## Migration Summary

| Model | Domain File | New Tables | New Indexes |
|-------|-------------|------------|-------------|
| SSO | core.py | 3 | 2 |
| 3-Way Match | procurement.py | 3 | 4 |
| Intercompany | finance.py | 3 | 3 |
| Cost Layers | inventory.py | 2 | 3 |
| Cash Flow | finance.py | 2 | 2 |
| Self-Service | hr.py | 1 | 2 |
| Subscription | finance.py | 3 | 3 |
| BI Dashboard | operations.py | 2 | 1 |
| Mobile Sync | operations.py | 1 | 3 |
| Blanket PO | procurement.py | 2 | 2 |
| Campaign | projects_crm.py | 3 | 3 |
| Performance | hr.py | 3 | 2 |
| CPQ | sales.py | 6 | 4 |
| Demand Forecast | inventory.py | 2 | 2 |
| Shop Floor + Routing | manufacturing.py | 3 | 3 |
| Time Tracking | projects_crm.py | 1 | 3 |
| Resource Planning | projects_crm.py | 1 | 2 |
| Notifications | operations.py | 2 | 3 |
| **Total** | | **41 tables** | **47 indexes** |
