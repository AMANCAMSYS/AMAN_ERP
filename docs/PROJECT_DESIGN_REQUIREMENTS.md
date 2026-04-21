<div dir="rtl">

# وثيقة تصميم ومتطلبات المشروع — نظام أمان ERP
## Project Design & Requirements (PDR)

- **الإصدار:** 1.0
- **تاريخ الإصدار:** 20 أبريل 2026
- **الحالة:** معتمدة للقراءة الداخلية
- **الملفات المرتبطة:** `docs/20-4-2026-audit.md` (تقرير التدقيق الأمني)، `docs/TESTING_SCENARIOS.md` (سيناريوهات الاختبار الكاملة)، `docs/RUNBOOK.md` (دليل التشغيل)

---

## 1. الملخص التنفيذي

**أمان ERP** هو نظام تخطيط موارد مؤسسات (Enterprise Resource Planning) متعدد المستأجرين (Multi-tenant) موجّه لأسواق **الخليج العربي ومصر وشمال أفريقيا**، ويدعم اللغتين العربية والإنجليزية بشكل كامل (RTL/LTR) والعملات المتعددة والفروع المتعددة والمستودعات المتعددة.

يغطي النظام الدورات التشغيلية والمحاسبية الكاملة:

- **المالية:** دليل حسابات هرمي، قيود يومية، ذمم مدينة/دائنة، إدارة نقدية وخزينة، ضرائب (VAT/WHT/Zakat)، أصول ثابتة، تكاليف، ميزانيات، إقفال فترات، توحيد مالي بين الشركات.
- **المبيعات والعملاء:** عروض أسعار، أوامر بيع، فواتير، مرتجعات، POS، CRM، عقود، CPQ، اشتراكات متكررة.
- **المشتريات:** عروض موردين، أوامر شراء، استلام (GRN)، مطابقة ثلاثية (3-way)، فواتير موردين، تكاليف مستوردة (Landed Costs).
- **المخازن:** منتجات وتصنيفات، دفعات (Batches)، أرقام تسلسلية (Serials)، FIFO/LIFO/WAvg بطبقات (Layers)، تحويلات بين المستودعات، جرد، تنبؤ بالطلب.
- **التصنيع:** BOM متعدد المستويات، أوامر إنتاج، MRP، توجيه عمليات (Routing)، أرض المصنع (Shop Floor)، معدات وصيانة.
- **الموارد البشرية:** موظفون، رواتب (WPS متوافق مع KSA/UAE)، حضور، إجازات، تقييم أداء، بوابة الخدمة الذاتية.
- **المشاريع والخدمات:** مشاريع، مهام، أوراق دوام، مراحل، تكلفة/إيراد، اعتراف بالإيراد (ASC 606/IFRS 15).
- **التقارير واللوحات:** ميزان مراجعة، قائمة دخل، ميزانية، تدفقات نقدية (13 أسبوع)، 57 تقريراً، 11 لوحة مبنية على الأدوار.

### 1.1 النطاق الجغرافي والتشريعي المدعوم

| المنطقة | التوافق التنظيمي |
|---------|-------------------|
| السعودية (KSA) | ZATCA Phase 1 + Phase 2 (فاتورة إلكترونية B2B)، حاسبة الزكاة، VAT 15% |
| الإمارات (UAE) | FTA VAT 5%، WPS SIF لملف الرواتب |
| مصر (EG) | مصلحة الضرائب المصرية، VAT 14%، خصم المنبع |
| الأردن/الكويت/قطر/البحرين | VAT أو Sales Tax قابل للتهيئة |

### 1.2 المقاييس والحجم

- **56** ملف راوتر (Backend routers)
- **~872** نقطة نهاية API
- **178+** جدول قاعدة بيانات
- **~300** مسار واجهة أمامية (Frontend routes)
- **11** لوحة تحكم مبنية على الأدوار
- **57** تقريراً جاهزاً
- **8** Materialized Views للتحليلات (تحديث كل 15 دقيقة)

---

## 2. المعمارية العامة (Architecture Overview)

### 2.1 الطبقات الرئيسية

```
┌─────────────────────────────────────────────────────────────┐
│  العملاء (Clients)                                          │
│  - Web SPA (React 18 + Vite + Tailwind + i18next)          │
│  - Mobile (React Native / Expo) مع مزامنة Offline          │
│  - External API Clients (OAuth2 / API Keys)                 │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTPS
┌───────────────────────▼─────────────────────────────────────┐
│  Nginx Reverse Proxy (TLS termination, rate limiting)       │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│  FastAPI Backend (Gunicorn + Uvicorn workers)               │
│  - 56 Routers    - APScheduler (daemon)                    │
│  - GL Service    - Permissions Engine                       │
│  - Tenant Router (DB-per-company)                           │
└──────┬──────────────────────┬──────────────────┬────────────┘
       │                      │                  │
┌──────▼───────┐       ┌──────▼──────┐    ┌──────▼──────────┐
│ PostgreSQL 15│       │   Redis 7    │    │  Prometheus     │
│ - aman_system│       │ - Cache      │    │  + Grafana      │
│ - aman_{cid} │       │ - Sessions   │    │  + Sentry       │
│   (لكل شركة)│       │ - Rate limit │    │                 │
└──────────────┘       └─────────────┘    └─────────────────┘
```

### 2.2 تقنيات المكدس (Tech Stack)

| الطبقة | التقنية | الإصدار |
|--------|---------|---------|
| لغة الباك إند | Python | 3.11 |
| إطار الباك إند | FastAPI | 0.115+ |
| ORM | SQLAlchemy | 2.x |
| الترحيلات | Alembic | latest |
| التحقق من البيانات | Pydantic | v2 |
| قاعدة البيانات | PostgreSQL | 15 |
| الكاش/الطوابير | Redis | 7 |
| الجدولة | APScheduler | متضمن في العملية |
| الواجهة الأمامية | React | 18 |
| أداة البناء | Vite | latest |
| التنسيق | TailwindCSS | 3.x |
| الترجمة | i18next | v23 |
| التطبيق المحمول | React Native / Expo | SDK 50 |
| النشر | Docker Compose | v2 |
| المراقبة | Prometheus + Grafana + Sentry | — |

### 2.3 نموذج تعدد المستأجرين (Multi-Tenancy)

يستخدم النظام نموذج **قاعدة بيانات لكل شركة (Database per Tenant)**:

- **قاعدة نظام موحدة (System DB):** `aman_system`
  - `system_companies` — سجل الشركات
  - `system_user_index` — فهرس المستخدمين عبر الشركات (للـ SSO وتحويل الدخول)
  - `industry_templates` — قوالب صناعية (دليل حسابات افتراضي، ضرائب، وحدات قياس)

- **قاعدة لكل شركة:** `aman_{company_id}`
  - تحتوي كل بيانات الشركة: الفروع، المستودعات، المستخدمون، الحسابات، الحركات، المستندات.
  - يتم إنشاؤها تلقائياً عند تسجيل شركة جديدة.
  - الاتصال يتم ديناميكياً عبر `TenantRouter` في `backend/database.py`.

- **ذاكرة اتصالات (Engine Cache):** LRU بحجم 50 شركة نشطة لتقليل زمن الاستجابة.

> **ملاحظة أمنية:** راجع `docs/20-4-2026-audit.md` — بند F-002 بخصوص استخدام معامل `?company_id=` الذي يسمح بتحويل السياق (قيد المعالجة).

### 2.4 نشر الحاويات (Docker Compose)

| الخدمة | الصورة/الوصف | المنفذ |
|--------|---------------|--------|
| `db` | postgres:15-alpine | 5432 |
| `redis` | redis:7-alpine | 6379 |
| `backend` | FastAPI + Gunicorn (4 workers) | 8000 |
| `frontend` | Nginx يخدم build Vite | 80/443 |
| `prometheus` | prom/prometheus | 9090 |
| `grafana` | grafana/grafana | 3000 |

---

## 3. نموذج البيانات (Data Model)

### 3.1 السياقات المحدودة (Bounded Contexts)

ينقسم نموذج البيانات إلى سياقات محددة في `backend/models/domain_models/`:

| السياق | الجداول الرئيسية |
|--------|-------------------|
| **الهوية والمنصة** | `users`, `roles`, `permissions`, `branches`, `audit_logs`, `notifications`, `sso_providers`, `approval_flows` |
| **المحاسبة الأساسية** | `accounts` (دليل الحسابات), `journals`, `journal_lines`, `fiscal_years`, `fiscal_periods`, `currencies`, `exchange_rates`, `cost_centers` |
| **المالية المتقدمة** | `budgets`, `budget_lines`, `fixed_assets`, `asset_depreciation`, `taxes`, `tax_returns`, `zatca_invoices`, `cashflow_forecasts`, `reconciliation_records`, `intercompany_entities`, `intercompany_transactions`, `elimination_entries` |
| **الخزينة** | `bank_accounts`, `cash_accounts`, `checks_issued`, `checks_received`, `notes_payable`, `notes_receivable`, `vouchers` |
| **المبيعات** | `customers`, `quotations`, `sales_orders`, `delivery_orders`, `invoices`, `invoice_lines`, `credit_notes`, `sales_returns`, `cpq_configurations`, `contracts`, `subscriptions` |
| **CRM** | `leads`, `opportunities`, `campaigns`, `activities`, `support_tickets` |
| **POS** | `pos_sessions`, `pos_transactions`, `pos_payments`, `pos_cash_movements` |
| **المشتريات** | `suppliers`, `rfqs`, `purchase_orders`, `goods_receipts` (GRN), `supplier_invoices`, `matching_records` (3-way), `landed_costs`, `blanket_pos` |
| **المخازن** | `products`, `product_categories`, `uoms`, `warehouses`, `stock_movements`, `stock_layers` (FIFO/LIFO), `batches`, `serials`, `stock_adjustments`, `stock_transfers`, `shipments`, `price_lists`, `demand_forecasts`, `costing_policies` |
| **التصنيع** | `boms`, `bom_operations`, `production_orders`, `work_orders`, `job_cards`, `routing_operations`, `workstations`, `equipment`, `maintenance_logs` |
| **الموارد البشرية** | `employees`, `departments`, `positions`, `payrolls`, `payroll_components`, `attendance`, `leaves`, `performance_cycles`, `performance_reviews`, `wps_files`, `self_service_requests` |
| **المشاريع والخدمات** | `projects`, `project_tasks`, `project_phases`, `timesheets`, `services`, `service_requests`, `revenue_recognition_schedules` |
| **الأصول** | `asset_categories`, `fixed_assets`, `asset_movements`, `asset_revaluations`, `asset_disposals` |

### 3.2 القيود المحاسبية الأساسية (Invariants)

- **تساوي الطرفين:** كل قيد يومية يجب أن يحقق `SUM(debit) = SUM(credit)` على مستوى القيد.
- **قفل الفترة:** لا يسمح بالترحيل في فترات مقفلة (`fiscal_periods.status = 'closed'`).
- **تسلسل المرجعية:** لكل مستند مرجع فريد حسب النوع والفرع والسنة المالية.
- **العملة الوظيفية:** تخزين مزدوج — العملة الأصلية + العملة الوظيفية للشركة + سعر الصرف المستخدم.
- **طبقات التكلفة:** حركات الصرف تستهلك طبقات التكلفة حسب سياسة المستودع (FIFO/LIFO/WAvg) مع قفل `policy_version`.

---

## 4. الوحدات الوظيفية (Functional Modules)

### 4.1 المالية والمحاسبة

#### 4.1.1 دليل الحسابات والقيود
- **الراوتر:** `backend/routers/finance/accounting.py` (31 نقطة نهاية، 2660 سطر)
- **الخدمة المركزية:** `backend/services/gl_service.py`
- **الخصائص:**
  - دليل حسابات هرمي غير محدود العمق.
  - قيود يدوية وآلية (من الفواتير، المستودعات، الرواتب).
  - قيود متكررة (Recurring Journals) بجدولة زمنية.
  - قيود عكسية (Reversal) مع تتبع المنشأ (`reversed_from`).
  - إقفال الفترات مع قفل نهائي (`fiscal_lock`).

#### 4.1.2 الميزانيات
- **الراوتر:** `backend/routers/finance/budgets.py`
- ميزانيات سنوية/ربعية/شهرية على مستوى الحساب/الفرع/مركز التكلفة.
- مقارنة فعلي/موازنة مع حساب الانحرافات.

#### 4.1.3 الأصول الثابتة
- **الراوتر:** `backend/routers/finance/assets.py` (32 نقطة نهاية، 1631 سطر)
- فئات أصول، اقتناء، إهلاك (قسط ثابت، متناقص، وحدات إنتاج)، إعادة تقييم، استبعاد.
- ترحيل قيود الإهلاك الشهرية تلقائياً.

#### 4.1.4 الضرائب
- **الراوتر:** `backend/routers/finance/taxes.py` + `tax_compliance.py`
- إدارة أنواع الضرائب (VAT، WHT، Excise، Zakat).
- إقرارات دورية (شهرية/ربعية).
- ZATCA Phase 2: توليد XML، توقيع رقمي، إرسال للفوترة الإلكترونية.
- حاسبة الزكاة الشرعية (KSA).

#### 4.1.5 الخزينة والمصرف
- **الراوترات:** `treasury.py`, `checks.py`, `notes.py`, `reconciliation.py`
- حسابات بنكية ونقدية متعددة العملات.
- شيكات صادرة/واردة (تحت التحصيل، محصلة، مرتجعة).
- أوراق قبض/دفع بجداول استحقاق.
- تسوية بنكية (استيراد كشف + مطابقة آلية/يدوية).

#### 4.1.6 المطابقة بين الشركات (Intercompany)
- **Intercompany v1:** `backend/routers/finance/intercompany.py` (قديم)
- **Intercompany v2:** `backend/routers/finance/intercompany_v2.py` (جديد — أبريل 2026)
  - مجموعات كيانات (Entity Groups).
  - معاملات داخلية مع ترحيل متزامن في الشركتين.
  - قيود الاستبعاد (Elimination) عند التوحيد.
  - قوائم مالية موحدة (Consolidated Financials).

> **ملاحظة:** راجع تقرير التدقيق — كلا النسختين نشطتان حالياً وينبغي إهمال v1.

#### 4.1.7 التدفقات النقدية (Cash Flow Forecast)
- **الراوتر:** `backend/routers/finance/cashflow.py` (13 نقطة نهاية، جديد)
- توقع 13 أسبوع قادم بناء على:
  - فواتير العملاء المستحقة.
  - فواتير الموردين المستحقة.
  - الرواتب المجدولة.
  - الاشتراكات المتكررة.
- سيناريوهات متعددة (متفائل/متشائم/أساسي).

#### 4.1.8 الاشتراكات المتكررة
- **الراوتر:** `backend/routers/finance/subscriptions.py`
- خطط اشتراك شهرية/سنوية.
- توليد فواتير آلي.
- حساب MRR / ARR.
- حماية التخصيص (Voucher Allocation Guards) — أبريل 9.

#### 4.1.9 مراكز التكلفة وسياسات التكلفة
- **الراوترات:** `cost_centers.py`, `costing_policies.py`
- مراكز تكلفة هرمية.
- سياسات تكلفة لكل مستودع (FIFO/LIFO/WAvg) مع قفل الإصدار.

### 4.2 المبيعات والعملاء

#### 4.2.1 الدورة الأساسية
- **الراوترات:** `sales/orders.py`, `invoices.py`, `quotations.py`, `returns.py`, `credit_notes.py`, `vouchers.py`
- دورة كاملة: عرض سعر → أمر بيع → إذن تسليم → فاتورة → قبض → مرتجع/إشعار دائن.

#### 4.2.2 CRM
- **الراوتر:** `backend/routers/crm.py` (51 نقطة نهاية)
- العملاء المحتملون (Leads) → الفرص → الصفقات → العملاء.
- حملات تسويقية، أنشطة، تذاكر دعم.

#### 4.2.3 POS
- **الراوتر:** `backend/routers/pos.py` (34 نقطة نهاية، 1707 سطر)
- جلسات كاشير، مبيعات نقدية/بطاقات، مرتجعات، حركات نقدية (إيداع/سحب).
- عمل Offline مع مزامنة عند الاتصال.

#### 4.2.4 CPQ (Configure-Price-Quote)
- **الراوتر:** `backend/routers/cpq.py`
- تكوين منتجات معقدة بخيارات متعددة.
- قواعد تسعير ديناميكية.
- توليد عرض سعر جاهز للتوقيع.

#### 4.2.5 العقود والاشتراكات
- عقود طويلة الأمد مع بنود SLA.
- اشتراكات متكررة (انظر 4.1.8).

### 4.3 المشتريات

#### 4.3.1 الدورة الأساسية
- **الراوتر:** `backend/routers/purchases.py` (49 نقطة نهاية، 3625 سطر)
- RFQ → مقارنة عروض → PO → GRN → فاتورة مورد → دفع.

#### 4.3.2 المطابقة الثلاثية (3-Way Matching)
- **الراوتر:** `backend/routers/matching.py` (جديد — Phase 2)
- مطابقة `PO ↔ GRN ↔ Invoice` مع تسامح كمية/سعر قابل للتهيئة.
- تعليق الفواتير المخالفة حتى الموافقة.

#### 4.3.3 التكاليف المستوردة (Landed Costs)
- **الراوتر:** `backend/routers/landed_costs.py`
- توزيع الشحن/الجمارك/التأمين على تكلفة البضاعة (بالقيمة/الوزن/الكمية).

#### 4.3.4 أوامر شراء مفتوحة (Blanket POs)
- عقود سنوية مع إطلاقات دفعية.

### 4.4 المخازن

#### 4.4.1 المنتجات والهيكل
- **الراوترات الفرعية تحت** `inventory/`: `products.py`, `categories.py`, `warehouses.py`, `uoms.py`
- منتجات مخزنية/خدمية/مجمعة.
- تصنيفات هرمية.
- وحدات قياس متعددة مع معاملات تحويل.

#### 4.4.2 الحركات والتكلفة
- `stock_movements.py`, `costing.py` (جديد — Phase 4)
- حركات دخول/خروج/تحويل/تعديل.
- **تكلفة بالطبقات (Layer-based Costing):**
  - FIFO: استهلاك أقدم طبقة أولاً.
  - LIFO: استهلاك أحدث طبقة أولاً.
  - WAvg: تحديث متوسط عند كل دخول.
  - قفل `policy_version` لمنع التغيير بأثر رجعي.

#### 4.4.3 الدفعات والأرقام التسلسلية
- `batches.py` — تتبع تاريخ إنتاج/انتهاء.
- تتبع أرقام تسلسلية للأصول والأجهزة.

#### 4.4.4 التحويلات والجرد
- `transfers.py`, `adjustments.py`, `shipments.py`
- تحويلات بين مستودعات مع حالة "في الطريق" (In Transit).
- جرد دوري/دائم مع قيود التسوية.

#### 4.4.5 قوائم الأسعار والتنبؤ
- `price_lists.py` — قوائم متعددة لكل عميل/منطقة/عملة.
- `forecast.py` — تنبؤ بالطلب (Moving Average، Exponential Smoothing).

### 4.5 التصنيع

- **الراوترات:** `manufacturing/core.py` (52 نقطة نهاية), `routing.py`, `shopfloor.py`
- BOM متعدد المستويات مع نسخ (Versions).
- أوامر إنتاج مربوطة بأوامر بيع أو مخزون أمان.
- MRP لحساب احتياجات المواد.
- توجيه عمليات (Routing) مع محطات عمل وأزمنة قياسية.
- أرض المصنع (Shop Floor Control) — بطاقات عمل، تسجيل أوقات، هالك.
- إدارة معدات وصيانة وقائية/علاجية.

### 4.6 الموارد البشرية

#### 4.6.1 الأساسيات
- **الراوتر:** `backend/routers/hr/core.py` (39 نقطة نهاية)
- الموظفون، الإدارات، الوظائف، العقود.

#### 4.6.2 الرواتب والحضور
- **الراوتر:** `backend/routers/hr/advanced.py` (36 نقطة نهاية)
- مكونات راتب مرنة (أساسي، بدلات، حسميات).
- حضور/انصراف، إجازات بأرصدة.
- ملفات WPS: SIF لـ UAE، بنوك KSA — `hr_wps_compliance.py`.

#### 4.6.3 تقييم الأداء
- **الراوتر:** `backend/routers/hr/performance.py` (12 نقطة نهاية)
- دورات تقييم (ربع/نصف/سنوية).
- تقييم 360 درجة، KPIs فردية.

#### 4.6.4 الخدمة الذاتية
- **الراوتر:** `backend/routers/hr/self_service.py` (10 نقاط نهاية، جديد — Phase 6)
- بوابة الموظف: طلبات الإجازة، كشف الراتب، ساعات العمل، المصروفات.

### 4.7 المشاريع والخدمات

- **الراوتر:** `backend/routers/projects.py` (59 نقطة نهاية، 3457 سطر)
- مشاريع بمراحل، مهام، Gantt، تبعيات.
- أوراق دوام ربط بالمشاريع.
- تكلفة فعلية مقابل ميزانية.
- **الاعتراف بالإيراد:** ASC 606 / IFRS 15 — جداول استحقاق حسب نسبة الإنجاز أو نقاط زمنية.
- الخدمات (Services): طلبات خدمة، SLA، فوترة.

### 4.8 التقارير واللوحات

#### 4.8.1 التقارير
- **الراوتر:** `backend/routers/reports.py` (57 تقرير، 4441 سطر)
- تقارير مالية: ميزان مراجعة، قائمة دخل، ميزانية، تدفقات نقدية، حركة حساب.
- تقارير ضريبية: إقرار VAT، WHT، ZATCA.
- تقارير مخازن: أعمار المخزون، حركة مخزنية، قيمة مخزون.
- تقارير مبيعات ومشتريات: أعمار ذمم، تحصيلات متوقعة.
- **تقارير مجدولة:** `scheduled_reports.py` — إرسال بريد دوري.

#### 4.8.2 اللوحات
- **الراوتر:** `role_dashboards.py` (14 نقطة نهاية، 11 شخصية)
  - المدير التنفيذي، المدير المالي، مدير المبيعات، مدير المشتريات، مدير المخازن، مدير التصنيع، مدير HR، مدير المشاريع، الكاشير، المحاسب، الموظف.
- **Materialized Views:** 8 عروض مادية لتحليلات سريعة (تحديث كل 15 دقيقة).

### 4.9 التكاملات الخارجية

- **SSO (Phase 1):** `backend/routers/sso.py` — SAML 2.0، LDAP، OAuth2 (Google، Microsoft).
- **Webhooks:** `webhooks.py` — أحداث مخصصة.
- **External API:** `external_api.py` — OAuth2 Client Credentials + API Keys.
- **Mobile Sync:** `mobile.py` — مزامنة Offline مع حل تضارب (Last-Write-Wins + conflict queue).
- **ZATCA:** إرسال XML موقّع إلى بوابة الفوترة الإلكترونية السعودية.
- **WPS:** توليد ملفات SIF للبنوك (UAE) وملفات CSV (KSA).

---

## 5. الأدوار والصلاحيات (RBAC)

### 5.1 نموذج الصلاحيات

- **صلاحيات سلسلة (String Permissions):** مثل `finance.journals.create`, `sales.invoices.approve`.
- **حروف بديلة (Wildcards):** `finance.*`, `*.read`.
- **أسماء مستعارة (Aliases):** مجموعات معرّفة مسبقاً (مثل `sales_manager_pack`).
- **قيود على مستوى الحقل (PERM-001):** إخفاء الحقول الحساسة (الراتب، الرقم القومي).
- **قيود على مستوى الصف (PERM-002):** حصر الوصول للمستودعات المخصصة للمستخدم.
- **قيود مراكز التكلفة (PERM-003):** حصر الوصول لمراكز تكلفة محددة.

### 5.2 الأدوار الافتراضية

| الدور | المجال |
|-------|--------|
| `system_admin` | كل الصلاحيات عبر كل الشركات |
| `company_admin` | كل الصلاحيات داخل شركة |
| `accountant` | المحاسبة، التقارير المالية |
| `sales_manager` | المبيعات، CRM، عملاء |
| `purchasing_manager` | المشتريات، الموردون |
| `warehouse_manager` | المخازن، الحركات، الجرد |
| `production_manager` | التصنيع، BOM، أوامر إنتاج |
| `hr_manager` | الموارد البشرية، الرواتب |
| `project_manager` | المشاريع، المهام، المصروفات |
| `cashier` | POS، قبض نقدي |
| `employee` | بوابة الخدمة الذاتية فقط |

---

## 6. الواجهة الأمامية (Frontend)

### 6.1 الهيكل

```
frontend/src/
├── App.jsx              # ~300 route مع AuthGuard + PermissionGuard
├── pages/
│   ├── Accounting/      # دليل حسابات، قيود، فترات
│   ├── Sales/           # عروض، أوامر، فواتير
│   ├── Purchases/       # عروض موردين، PO، GRN
│   ├── Inventory/       # منتجات، مخازن، حركات
│   ├── Manufacturing/   # BOM، أوامر إنتاج، shop floor
│   ├── HR/              # موظفون، رواتب، حضور
│   ├── Projects/        # مشاريع، مهام، أوراق دوام
│   ├── POS/             # واجهة كاشير
│   ├── CRM/             # leads، opportunities
│   ├── Reports/         # 57 تقرير
│   ├── Settings/        # إعدادات الشركة
│   ├── Admin/           # مستخدمون، أدوار، فروع
│   ├── CashFlow/        # توقع 13 أسبوع
│   ├── Intercompany/    # كيانات، استبعاد، توحيد
│   ├── Matching/        # 3-way matching
│   ├── SSO/             # مزودو SSO
│   ├── SelfService/     # بوابة الموظف
│   ├── Subscription/    # اشتراكات متكررة
│   ├── CPQ/             # configurator
│   ├── Forecast/        # تنبؤ بالطلب
│   ├── BlanketPO/       # أوامر شراء مفتوحة
│   ├── Costing/         # سياسات وطبقات التكلفة
│   ├── Performance/     # تقييم أداء
│   ├── ShopFloor/       # أرض المصنع
│   ├── Routing/         # توجيه عمليات
│   ├── Analytics/       # لوحات ومتسيوز
│   └── ...
└── components/          # مكتبة مكونات مشتركة
```

### 6.2 الترجمة والاتجاه

- **i18next** مع ملفات `ar.json` و `en.json`.
- التبديل التلقائي لـ `dir="rtl"` عند اختيار العربية.
- خطوط عربية محسّنة (Cairo, Tajawal).

### 6.3 التطبيق المحمول

- **Phase 9 (أبريل 2026):** React Native / Expo.
- وظائف: POS، استلام بضائع (GRN)، جرد، موافقات، طلبات الخدمة الذاتية.
- تخزين محلي SQLite مع مزامنة تفاضلية.
- حل التضارب: Last-Write-Wins مع طابور مراجعة يدوية للتعارض المالي.

---

## 7. الأمان والامتثال

### 7.1 ضوابط الأمان

- **المصادقة:** JWT + Refresh Tokens، SSO (SAML/LDAP/OAuth).
- **التشفير:** TLS 1.3 على الشبكة، `pgcrypto` للحقول الحساسة (الراتب، IBAN).
- **كلمات المرور:** Bcrypt مع سياسات تعقيد قابلة للتهيئة.
- **سجل التدقيق (Audit Log):** كل عملية كتابة تسجّل (من، متى، ماذا، IP).
- **Rate Limiting:** على Redis، قابل للتهيئة لكل نقطة نهاية.

### 7.2 الامتثال التنظيمي

- **ZATCA Phase 2 (KSA):** Fatoora compliant.
- **WPS (UAE/KSA):** ملفات رواتب معتمدة من البنوك المركزية.
- **GDPR/PDPL:** تصدير بيانات الموظف، الحذف الآمن، تسجيل الموافقات.
- **SOX-like controls:** فصل المهام (Segregation of Duties)، سير عمل الموافقات.

### 7.3 المخاطر المعروفة

راجع `docs/20-4-2026-audit.md` — **129 ملاحظة** (29 حرجة، 45 عالية، 41 متوسطة، 14 منخفضة). أبرزها:

- **F-001:** تصعيد عبر `?company_id=`.
- **F-002:** كلمة مرور DB المستأجر = كلمة مرور admin التطبيق.
- **F-003:** Race condition في `gl_service` idempotency.
- **F-004:** عدم وجود CHECK constraint على مستوى DB لتساوي طرفي القيد.
- **F-005:** فحص الفترة المقفلة في `gl_service` فقط (قابل للتجاوز).
- **F-006:** `float` في حسابات نقدية (Backend + Frontend).
- **F-007:** XSS في قوالب الطباعة.
- **F-008:** JWT في `localStorage` (عرضة لـ XSS).

---

## 8. النشر والتشغيل

### 8.1 البيئات

- **Development:** Docker Compose محلي + قاعدة بيانات اختبار.
- **Staging:** نسخة كاملة مع بيانات مقنعة (Masked).
- **Production:** Docker Swarm / Kubernetes (مستقبلاً)، مع نسخ احتياطية مشفرة يومية.

### 8.2 المراقبة

- **Prometheus:** جمع metrics من Backend (endpoint `/metrics`).
- **Grafana:** لوحات جاهزة (latency, error rate, DB pool, Redis).
- **Sentry (اختياري):** تتبع الأخطاء والاستثناءات.
- **Logs:** JSON structured logs → stdout → مجمّع خارجي (ELK/Loki).

### 8.3 النسخ الاحتياطي والتعافي

- **PostgreSQL:** `pg_dump` يومي + WAL archiving.
- **RPO:** 15 دقيقة.
- **RTO:** 4 ساعات.
- **اختبار التعافي:** ربع سنوي.

### 8.4 الجدولة (APScheduler)

- وظائف دورية: ترحيل الإهلاك الشهري، تحديث Materialized Views، تنفيذ الاشتراكات، إرسال التقارير المجدولة، تنبيهات الانتهاء.

> **ملاحظة:** راجع التدقيق — التشغيل داخل نفس عملية FastAPI يمثل مخاطرة (ينبغي فصلها إلى Worker منفصل).

---

## 9. الإصدارات والمراحل

### 9.1 المراحل المكتملة

| المرحلة | المحتوى | التاريخ |
|---------|---------|---------|
| **Phase 0** | الأساس المحاسبي + المخازن + المبيعات + المشتريات | 2025 |
| **Phase 1** | SSO (SAML/LDAP/OAuth) | أبريل 2026 |
| **Phase 2** | 3-way Matching | أبريل 2026 |
| **Phase 3** | Intercompany v2 + توحيد | أبريل 2026 |
| **Phase 4** | FIFO/LIFO Layer-based Costing | أبريل 2026 |
| **Phase 5** | 13-week Cash Flow Forecast | أبريل 2026 |
| **Phase 6** | Employee Self-Service Portal | أبريل 2026 |
| **Phase 7** | Advanced Workflow Engine | أبريل 2026 |
| **Phase 8** | Reporting Polish + Analytics MViews | أبريل 2026 |
| **Phase 9** | Mobile App (Offline-first) | أبريل 2026 |
| **feat(006)** | Accounting Audit: Fiscal Locks, Period Closing, Reversal Audit, Journal Provenance (71 tasks) | 14 أبريل 2026 |
| **Subscription + Voucher Guards** | MRR/ARR + حماية التخصيص | 9 أبريل 2026 |

### 9.2 الخريطة المستقبلية (Roadmap)

- فصل Scheduler Worker.
- استبدال `float` بـ `Decimal` في كل المسارات المالية.
- إهمال Intercompany v1.
- إضافة CHECK constraints على مستوى DB للقيود.
- HttpOnly Cookies بدلاً من localStorage لـ JWT.
- Multi-region deployment.

---

## 10. المراجع

- `docs/20-4-2026-audit.md` — تقرير التدقيق الأمني والوظيفي.
- `docs/TESTING_SCENARIOS.md` — سيناريوهات الاختبار التفصيلية (3 فروع + 5 مستودعات).
- `docs/RUNBOOK.md` — دليل التشغيل اليومي.
- `docs/audit/` — مستندات التدقيق التاريخية.

---

**انتهت الوثيقة — Version 1.0 — 20 أبريل 2026**

</div>
