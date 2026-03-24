# Product Requirements Document (PRD)
# AMAN ERP — نظام تخطيط موارد المؤسسات

**Version:** 7.0  
**Last Updated:** 5 مارس 2026  
**Status:** Production Ready (85%)  
**Language:** Arabic (RTL) + English  

---

## 1. Product Overview

### 1.1 Purpose
AMAN ERP is a comprehensive, multi-tenant enterprise resource planning system built specifically for Arabic-speaking markets, with deep compliance for Saudi Arabian regulations (ZATCA, GOSI, WPS, Zakat). It covers 16 integrated modules in a single platform, eliminating the need for multiple disconnected software solutions.

### 1.2 Target Users
| User Type | Role | Primary Modules |
|-----------|------|----------------|
| Business Owner / CEO | Strategic overview | Dashboard, Reports, KPI |
| Accountant | Financial operations | Accounting, Treasury, Taxes |
| Sales Manager | Revenue operations | Sales, CRM, Contracts |
| Purchasing Manager | Procurement | Buying, Inventory |
| Warehouse Manager | Stock control | Inventory, Manufacturing |
| HR Manager | People management | HR, Payroll |
| Cashier | Point of sale | POS |
| System Admin | Configuration | Admin, Settings |

### 1.3 Key Value Propositions
- **Saudi Compliance First:** Built-in ZATCA, GOSI, WPS, Nitaqat, End-of-Service calculations
- **Full Arabic RTL:** Designed natively in Arabic — not a translation
- **Zero Licensing Cost:** Self-hosted, company-owned infrastructure
- **Industry Adaptive:** 12 industry templates that automatically show/hide relevant features
- **Integrated Accounting:** Every transaction auto-generates balanced journal entries

---

## 2. System Architecture

### 2.1 Technical Stack
| Layer | Technology |
|-------|-----------|
| Backend | Python (FastAPI) — 88,268 lines |
| Frontend | React JSX — 98,760 lines |
| Database | PostgreSQL (DB-per-tenant) |
| Cache | Redis |
| Container | Docker + Docker Compose |
| Web Server | Nginx (Reverse Proxy) |
| Auth | JWT (Bearer Token) |

### 2.2 System Scale
| Metric | Value |
|--------|-------|
| API Endpoints | 767 (392 GET + 244 POST + 79 PUT + 52 DELETE) |
| Frontend Pages | 277 JSX pages / ~270 routes |
| Database Tables | 244 tables per company |
| Auto Journal Entry Points | 75+ triggers |
| Industry Templates | 12 |
| Default Roles | 8 |

### 2.3 Multi-Tenancy Model
- Each company gets a dedicated PostgreSQL database: `aman_{company_id}`
- System-level index DB (`postgres`) stores company registry and user routing
- Login uses O(1) lookup via `system_user_index` table

---

## 3. Authentication & Security

### 3.1 Login Flow
**Endpoint:** `POST /auth/login`  
**Input:** `{ username, password }`  
**Output:** `{ access_token, user }`

**Security Features:**
- Rate limiting: 10 req/min, 5 req/IP, 15-minute lockout
- JWT contains: user_id, company_id, role, permissions, enabled_modules, allowed_branches
- Two-Factor Authentication (2FA) via TOTP
- Redis-backed rate limiter (production)
- Password history tracking
- Session management with active session listing

### 3.2 Token Management
| Token | Expiry | Endpoint |
|-------|--------|---------|
| Access Token | 30 minutes | `/auth/login` |
| Refresh Token | 7 days | `/auth/refresh` |
| Reset Token | Single use | `/auth/reset-password` |

### 3.3 Roles & Permissions
| Role | Arabic | Access Level |
|------|--------|-------------|
| `superuser` | مدير النظام | Full access (`["*"]`) |
| `admin` | مدير | Full access |
| `manager` | مدير فرع | Sales, Purchases, Inventory, POS, Reports |
| `accountant` | محاسب | Accounting, Treasury, Taxes, Reports |
| `sales` | مبيعات | Sales, Products, POS, Contracts |
| `inventory` | أمين مستودع | Inventory, Products, Manufacturing (view) |
| `cashier` | كاشير | POS, Sales (view) |
| `user` | مستخدم | Dashboard only |

**Permission Format:** `module.action` (e.g., `sales.create`, `accounting.manage`)

---

## 4. Core Modules

### 4.1 Accounting (المحاسبة)

**Base URL:** `/finance/accounting`

#### Chart of Accounts
- 3-level hierarchy (Group > Account > Sub-account)
- 121 default accounts across 5 types: Assets, Liabilities, Equity, Revenue, Expenses
- Account mapping for automatic journal entry routing (45 mappings)

#### Journal Entries
| Action | Endpoint | Effect |
|--------|---------|--------|
| Create (Draft) | `POST /journal-entries` | Saves to DB, no balance impact |
| Post | `POST /journal-entries/{id}/post` | Updates account balances |
| Void/Reverse | `POST /journal-entries/{id}/void` | Creates reverse entry `REV-{original}` |

**Validation:** sum(debits) must equal sum(credits) using `Decimal` with `ROUND_HALF_UP`

#### Financial Reports
- Trial Balance (with comparison)
- Income Statement (detailed/summary)
- Balance Sheet
- Cash Flow Statement
- General Ledger
- Budget vs. Actual
- Cost Center Report
- Horizontal Analysis
- Financial Ratios

#### Saudi-Specific Features
- **Zakat Calculator:** ZATCA-compliant formula — `Base = Equity - Fixed Assets - Intangibles - WIP`
  - Hijri rate: 2.5%
  - Gregorian rate: 2.5775%
  - Endpoint: `POST /accounting/zakat/calculate`
- **Fiscal Period Lock:** Prevent entries in closed periods
- **Consolidation Reports:** Unified trial balance and income statement across all companies

---

### 4.2 Sales (المبيعات)

**Base URL:** `/sales`

#### Sales Cycle
```
Quotation -> Sales Order -> Invoice -> Receipt -> Reports
```

#### Key Documents
| Document | Endpoint | Auto Journal Entry |
|----------|---------|-------------------|
| Sales Invoice | `POST /sales/invoices` | Dr: AR/Cash + COGS -> Cr: Revenue + VAT + Inventory |
| Sales Return | `POST /sales/returns/{id}/approve` | Reversal of original entry + inventory return |
| Customer Receipt | `POST /sales/receipts` | Dr: Cash/Bank -> Cr: AR |
| Credit Note | `POST /sales/credit-notes` | Dr: Revenue (reverse) -> Cr: Customer |
| Delivery Order | `POST /sales/delivery-orders/{id}/invoice` | Dr: AR + COGS -> Cr: Revenue + VAT + Inventory |

#### Additional Features
- Commission rules and calculation
- Customer credit limit checking
- Contracts with auto-invoicing
- Partial invoicing from sales orders
- Customer aging report (AR)

---

### 4.3 Buying (المشتريات)

**Base URL:** `/purchases`

#### Purchase Cycle
```
RFQ -> Purchase Order -> GRN (Receive) -> Purchase Invoice -> Supplier Payment
```

| Document | Endpoint | Auto Journal Entry |
|----------|---------|-------------------|
| GRN (Goods Receipt) | `POST /purchases/orders/{id}/receive` | Dr: Inventory -> Cr: AP |
| Purchase Invoice | `POST /purchases/invoices` | Dr: Inventory + VAT Input -> Cr: AP/Cash |
| Supplier Payment | `POST /purchases/payments` | Dr: AP -> Cr: Cash/Bank |
| Landed Costs | `POST /purchases/landed-costs/{id}/post` | Dr: Inventory -> Cr: AP/Expense |

#### Landed Cost Distribution Methods
1. By Value
2. By Quantity
3. By Weight
4. Equal Distribution

---

### 4.4 Inventory (المخزون)

**Base URL:** `/inventory`

#### Core Features
- Multi-warehouse management
- Batch tracking (lot numbers)
- Serial number tracking
- Product variants (color, size, etc.)
- Kit/Bundle products
- Bin location management
- Quality inspections
- Cycle counting

#### Costing Policy
- Default: **Global WAC** (Weighted Average Cost)
- Options: Per-warehouse WAC, Hybrid, Smart

#### Auto Journal Entries
| Operation | Entry |
|-----------|-------|
| Stock Transfer | Dr: Destination Warehouse -> Cr: Source Warehouse |
| Stock Adjustment (increase) | Dr: Inventory -> Cr: Inventory Adjustment Expense |
| Stock Adjustment (decrease) | Dr: Inventory Adjustment Expense -> Cr: Inventory |

---

### 4.5 Treasury (الخزينة)

**Base URL:** `/finance/treasury`

#### Operations
| Operation | Endpoint | Journal Entry |
|-----------|---------|--------------|
| Expense | `POST /treasury/transactions/expense` | Dr: Expense Account -> Cr: Treasury |
| Transfer | `POST /treasury/transactions/transfer` | Dr: Destination -> Cr: Source |
| Bank Reconciliation | `POST /reconciliation/{id}/finalize` | Confirms match |
| Bank Statement Import | `POST /bank-import/upload` | CSV import + auto-matching |

#### Negotiable Instruments
| Type | Create | Collect/Clear | Bounce/Protest |
|------|--------|--------------|----------------|
| Checks Receivable | `POST /checks/receivable` | `/collect` | `/bounce` |
| Checks Payable | `POST /checks/payable` | `/clear` | `/bounce` |
| Notes Receivable | `POST /notes/receivable` | `/collect` | `/protest` |
| Notes Payable | `POST /notes/payable` | `/pay` | — |

---

### 4.6 HR & Payroll (الموارد البشرية)

**Base URL:** `/hr`

#### Core HR Features
- Employee management with full profiles
- Department and position hierarchy
- Attendance tracking
- Leave requests and approval
- Overtime management
- Salary structures with components
- Employee loans (advances)
- Performance reviews
- Training programs
- Violations and penalties
- Custody management
- Recruitment pipeline

#### Payroll Posting Journal Entry
- Dr: Salaries (gross) + Employer GOSI
- Cr: GOSI Payable + Loan Deductions + Penalties + Net Bank Transfer

#### Saudi-Specific HR Features
| Feature | Endpoint | Description |
|---------|---------|-------------|
| WPS Export | `POST /hr/wps/export-sif` | Wage Protection System SIF file |
| Saudization Dashboard | `GET /hr/saudization/dashboard` | Nitaqat compliance monitoring |
| End-of-Service | `POST /hr/eos/calculate` | Articles 84/85 Saudi Labor Law |
| GOSI Settings | `/hr/gosi` | Social insurance configuration |

---

### 4.7 Point of Sale (نقاط البيع)

**Base URL:** `/pos`

#### POS Features
| Feature | Description |
|---------|-------------|
| Session Management | Open/close cashier sessions with drawer reconciliation |
| Fast Sales Interface | Product search, barcode, quick add |
| Split Payment | Cash + Card + Mada simultaneously |
| Table Management | For restaurants (industry-conditional) |
| Kitchen Display | Order management for F&B |
| Customer Display | Live cart via BroadcastChannel API |
| Loyalty Programs | Points accumulation and redemption |
| Promotions | Discount rules and bundles |
| Thermal Printing | Receipt printer support |
| Offline Mode | IndexedDB queue with auto-sync on reconnect |

**ZATCA VAT Compliance:** Tax calculated on `(price x qty) - discount` — not on pre-discount amount

---

### 4.8 Manufacturing (التصنيع)

**Base URL:** `/manufacturing`

#### Production Cycle
```
Work Centers -> Routings -> BOM -> Production Order -> Start -> Complete
                                                         |          |
                                                   Dr: WIP    Dr: Finished Goods
                                                   Cr: RM     Cr: WIP
```

#### Features
- Bill of Materials (BOM) with by-products
- MRP (Material Requirements Planning)
- Job cards
- OEE (Overall Equipment Effectiveness)
- Cost variance report (estimated vs. actual)
- Production scheduling
- Equipment maintenance logs

---

### 4.9 Projects (المشاريع)

**Base URL:** `/projects`

#### Features
- Project and task management
- Budget vs. actual tracking
- Earned Value Management (EVM): PV, EV, AC, CPI, SPI, EAC
- Project-based invoicing and retainer invoices
- Change orders
- Resource management and utilization
- Risk management
- Timesheets

---

### 4.10 Fixed Assets (الأصول الثابتة)

**Base URL:** `/finance/assets`

| Operation | Endpoint | Journal Entry |
|-----------|---------|--------------|
| Create Asset | `POST /assets` | Dr: Fixed Asset -> Cr: Cash/Bank |
| Depreciation | `POST /assets/{id}/depreciate/{schedule_id}` | Dr: Depreciation Expense -> Cr: Accumulated Depreciation |
| Disposal | `POST /assets/{id}/dispose` | Dr: Accum. Depr. + Cash +/- Gain/Loss -> Cr: Asset Cost |
| Transfer | `POST /assets/{id}/transfer` | Dr: Dest. Branch Asset -> Cr: Source Branch Asset |
| Revaluation | `POST /assets/{id}/revalue` | Dr: Asset -> Cr: Revaluation Reserve |

---

### 4.11 CRM

**Base URL:** `/crm`

| Page | Route | Features |
|------|-------|---------|
| Dashboard | `/crm` | KPIs: pipeline value, win rate, avg deal size |
| Lead Scoring | `/crm/lead-scoring` | Automated scoring rules |
| Customer Segments | `/crm/customer-segments` | Segment definition and membership |
| Pipeline Analytics | `/crm/pipeline` | Visual funnel with conversion rates |
| Contacts | `/crm/contacts` | Independent contact management |
| Sales Forecasts | `/crm/forecasts` | Period-based revenue forecasting |
| Support Tickets | `/crm/tickets` | Customer support workflow |
| Marketing Campaigns | `/crm/campaigns` | Campaign ROI tracking |
| Knowledge Base | `/crm/knowledge-base` | Support articles |

---

### 4.12 Taxes (الضرائب)

**Base URL:** `/finance/taxes`

| Feature | Description |
|---------|-------------|
| VAT (15%) | Input/output tax tracking, settlement |
| Tax Returns | Periodic filing preparation |
| Withholding Tax (WHT) | 8 default rates |
| Tax Calendar | Filing deadline reminders |
| ZATCA QR Code | E-invoice QR generation |
| ZATCA Signature | Hash + cryptographic signature |

---

## 5. Industry Templates

### 5.1 Available Templates
| Code | Industry | Key Conditional Features |
|------|----------|--------------------------|
| RT | Retail | POS Loyalty, Promotions, Customer Display |
| WS | Wholesale | RFQ, Purchase Agreements, Contracts |
| FB | Food & Beverage | Table Management, Kitchen Display, Loyalty |
| MF | Manufacturing | BOM, MRP, Work Centers, OEE |
| CN | Construction | Projects, EVM, Contracts, Assets |
| SV | Services | CRM, Contracts, Projects, Knowledge Base |
| PH | Pharmacy | Batch Tracking, Customer Display, Promotions |
| WK | Workshop | Service Requests, Contracts, Overtime |
| EC | E-Commerce | CRM Campaigns, Multi-warehouse |
| LG | Logistics | Contracts, Supplier Ratings, Custody |
| AG | Agriculture | RFQ, Agreements, Supplier Ratings |
| GN | General | All features enabled |

---

## 6. Reports

### 6.1 Financial Reports
| Report | Endpoint |
|--------|---------|
| Trial Balance | `GET /reports/accounting/trial-balance` |
| Income Statement | `GET /reports/accounting/profit-loss` |
| Balance Sheet | `GET /reports/accounting/balance-sheet` |
| Cash Flow | `GET /reports/accounting/cashflow` |
| General Ledger | `GET /reports/accounting/general-ledger` |
| Budget vs. Actual | `GET /reports/accounting/budget-vs-actual` |

### 6.2 KPI Dashboard
**Endpoint:** `GET /reports/kpi/dashboard`

Metrics: Total Sales, AR Collection Rate, Inventory Turnover, Project Profitability, Production OEE, Customer Satisfaction

### 6.3 Report Features
- PDF + Excel export (all financial reports, Arabic RTL)
- Scheduled reports via email
- Custom report builder
- Shared reports across users
- Multi-company consolidation reports

---

## 7. Integrations

### 7.1 Built & Available
| Integration | Status | Endpoint |
|-------------|--------|---------|
| ZATCA QR Code | Live | `POST /external/zatca/generate-qr` |
| ZATCA Keypair | Live | `POST /external/zatca/generate-keypair` |
| WHT | Live | `/external/wht/*` |
| REST API | Live | 767 endpoints |
| API Keys | Live | `POST /external/api-keys` |
| Webhooks | Live | `POST /external/webhooks` |
| Bank Statement CSV Import | Live | `POST /bank-import/upload` |
| Email (SMTP) | Live | Notifications, reports, password reset |
| WPS SIF Export | Live | `POST /hr/wps/export-sif` |

### 7.2 Planned
| Integration | Priority |
|-------------|---------|
| ZATCA e-Invoicing (live portal) | Critical — legally required |
| Payment Gateways (mada, Apple Pay, Stripe) | High |
| Mobile App (iOS/Android) | High |
| E-Commerce (Salla, Shopify) | Medium |
| WhatsApp Business API | Medium |
| Shipping (Aramex, DHL) | Medium |
| Biometric Attendance (ZKTeco) | Medium |
| PWA / Full Offline Support | Medium |
| AI Demand Forecasting | Future |

---

## 8. Database Summary

### 8.1 Company Database (244 tables)
| Category | Tables |
|----------|--------|
| Core (users, branches, parties) | 7 |
| Accounting (accounts, journal entries) | 6 |
| Sales & Invoicing | 14 |
| Purchases | 11 |
| Inventory | 25 |
| Treasury | 8 |
| HR | 22 |
| Fixed Assets | 8 |
| Manufacturing | 13 |
| POS | 14 |
| Projects | 8 |
| Taxes | 10 |
| CRM | 10 |
| Other | 28 |

### 8.2 Default Chart of Accounts
- **1xxx Assets:** Current assets, Fixed assets, Intangibles
- **2xxx Liabilities:** Current, Long-term
- **3xxx Equity:** Capital, Retained Earnings, Revaluation Reserve
- **4xxx Revenue:** Operating, Other Income
- **5xxx Expenses:** COGS, Operating, Depreciation, Financial

---

## 9. Non-Functional Requirements

### 9.1 Performance
| Metric | Target |
|--------|--------|
| API Response Time | < 500ms |
| POS Transaction | < 200ms |
| Report Generation | < 5s standard, < 30s heavy |
| Concurrent Users | 50+ per instance |

### 9.2 Security
| Requirement | Implementation |
|-------------|---------------|
| Authentication | JWT Bearer + optional 2FA |
| Rate Limiting | Redis-backed |
| Encryption | TLS 1.2/1.3 |
| Audit Trail | `audit_logs` table |
| HSTS | Nginx enforced |

### 9.3 Responsive Design
| Device | Breakpoint | Behavior |
|--------|-----------|---------|
| Desktop | >= 1024px | Sidebar always visible |
| Tablet | 768–1023px | Hamburger menu + overlay |
| Mobile | < 768px | Hamburger menu + full overlay |

---

## 10. Production Readiness

| Task | Status |
|------|--------|
| Fiscal Period Lock (enforced) | Done |
| Inventory Row Locking (FOR UPDATE) | Done |
| POS Race Condition Fix | Done |
| ZATCA VAT Calculation | Done |
| Cache Security (pickle -> json) | Done |
| Redis Rate Limiting | Done |
| DB Engine LRU Cache | Done |
| Decimal Arithmetic (financial) | Done |
| Alembic Migrations | Done |
| CI/CD Pipeline | Done |
| JSON Logging + Request-ID | Done |
| Automated Daily Backup | Done |
| SSL/TLS + Nginx | Done |
| Docker Production Config | Done |
| Monitoring (Prometheus + Grafana) | Done |
| Runbook Documentation | Done |
| PgBouncer | Infrastructure pending |
| Load Testing | Infrastructure pending |
| Server Provisioning | Infrastructure pending |
| Disaster Recovery Test | Infrastructure pending |

**Overall: 85% complete (22/26 tasks)**

---

## 11. Glossary

| Term | Arabic | Definition |
|------|--------|-----------|
| COA | شجرة الحسابات | Chart of Accounts |
| GL | دفتر الأستاذ | General Ledger |
| AR | ذمم مدينة | Accounts Receivable |
| AP | ذمم دائنة | Accounts Payable |
| GRN | إشعار استلام | Goods Receipt Note |
| BOM | قائمة المواد | Bill of Materials |
| MRP | تخطيط المتطلبات | Material Requirements Planning |
| WIP | أعمال تحت التشغيل | Work In Progress |
| COGS | تكلفة البضاعة المباعة | Cost of Goods Sold |
| EVM | القيمة المكتسبة | Earned Value Management |
| OEE | كفاءة المعدات | Overall Equipment Effectiveness |
| WAC | المتوسط المرجح | Weighted Average Cost |
| WHT | ضريبة الاستقطاع | Withholding Tax |
| WPS | حماية الأجور | Wage Protection System |
| GOSI | التأمينات الاجتماعية | General Organization for Social Insurance |
| ZATCA | هيئة الزكاة والضريبة | Zakat, Tax and Customs Authority |
| JE | قيد يومي | Journal Entry |
| POS | نقطة البيع | Point of Sale |

---

*Generated from AMAN ERP Knowledge Base v7.0 — 5 مارس 2026*
