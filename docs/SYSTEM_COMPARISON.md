# AMAN ERP — مقارنة شاملة مع الأنظمة العالمية

> **تاريخ المقارنة:** 22 أبريل 2026
> **إصدار AMAN:** `main` @ latest
> **الغرض:** تقييم موضوعي لموقع نظام AMAN مقابل أبرز أنظمة تخطيط موارد المؤسسات عالمياً (Odoo EE, SAP Business One, Microsoft Dynamics 365 Business Central, NetSuite, Zoho Books, QuickBooks Enterprise).

---

## 1 · الملخّص التنفيذي

| المقياس | AMAN ERP | التقييم |
|---|---|---|
| **نطاق الوحدات** | 17 قسم وظيفي · 56+ router · ~872 endpoint · 170+ صفحة React · 12 صناعة مؤهلة | يعادل Odoo Enterprise / D365 BC ويتفوّق على Zoho / QuickBooks |
| **قاعدة الكود** | FastAPI + React 18 + PostgreSQL + Redis + Nginx | Stack حديث مفتوح بالكامل |
| **اللغات/التوطين** | عربي/إنجليزي كامل مع RTL layout + formulas + printout | متفوّق على معظم المنافسين الغربيين |
| **الامتثال GCC/MENA** | ZATCA Ph2 · UAE FTA · Egypt ETA · WPS · GOSI · السعودة · WHT · الزكاة | **الأعلى في GCC/MENA** بدون localization مدفوعة |
| **الأمان** | JWT + 2FA TOTP + CSRF + HttpOnly + gitleaks + SQL‑safety linter + فحص GL discipline CI | مستوى مؤسسات |
| **التعدّدية** | Multi‑tenant (DB‑per‑company) + Multi‑company + Multi‑branch + Multi‑currency + Multi‑book (IFRS/Local GAAP) | يطابق NetSuite/D365 |
| **التكاملات** | Stripe · Tap · PayTabs · DHL · Aramex · Taqnyat · Unifonic · Twilio · MT940 Bank Feeds | 🏆 تغطية خليجية نادرة |
| **النضج الوظيفي** | 95%+ مكتمل في المحاسبة/المبيعات/المخزون/HR/التصنيع | قابل للإنتاج |
| **نقاط ضعف** | AI/ML حقيقي محدود · Marketplace عام غير موجود · MES real‑time جزئي | فجوة أمام NetSuite/SAP S4 |

---

## 2 · مصفوفة المقارنة بالوحدات

> ✅ = مكتمل ومطابق للمعيار &nbsp;&nbsp; ⚠️ = موجود جزئياً &nbsp;&nbsp; ❌ = غير موجود &nbsp;&nbsp; 🏆 = ميزة تنافسية لـ AMAN

### 2.1 المحاسبة والتمويل

| الميزة | AMAN | Odoo EE | SAP B1 | D365 BC | NetSuite | Zoho Books | QuickBooks |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| دليل حسابات متعدّد المستويات | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| قيود يومية متعدّدة العملات | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| قوالب قيود متكرّرة (Recurring Templates) | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ❌ |
| فترات مالية + Fiscal Lock | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| إقفال سنوي + Closing Entries + Reversals | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| أرصدة افتتاحية (Opening Balances) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| مقارنة الفترات (Period Comparison) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| مطابقة بنكية + CSV + **MT940 Bank Feeds** | 🏆 | ⚠️ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| موازنات + cost centers + cost center hierarchy | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ❌ |
| IFRS 15 (Revenue Recognition) | ✅ | ⚠️ | ✅ | ✅ | ✅ | ❌ | ❌ |
| IFRS 9 (ECL Provisions) | ✅ | ❌ | ✅ | ⚠️ | ✅ | ❌ | ❌ |
| **IAS 2 (NRV Inventory Write‑Down)** | ✅ | ❌ | ✅ | ⚠️ | ✅ | ❌ | ❌ |
| IAS 36 (Impairment) | ✅ | ❌ | ✅ | ⚠️ | ✅ | ❌ | ❌ |
| IFRS 16 (Lease Contracts) | ✅ | ⚠️ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Multi‑Book (IFRS + Local GAAP)** | ✅ | ⚠️ | ✅ | ⚠️ | 🏆 | ❌ | ❌ |
| Intercompany Reciprocal JE | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Consolidation + Elimination Entries + Entity Tree** | ✅ | ⚠️ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Industry CoA Templates** (12 نشاط SOCPA/IFRS) | 🏆 | ⚠️ | ⚠️ | ⚠️ | ✅ (SuiteSuccess) | ❌ | ❌ |
| **Industry GL Auto‑Posting Rules** | 🏆 | ❌ | ⚠️ (FMS) | ⚠️ | ⚠️ (SuiteScript) | ❌ | ❌ |
| FX Revaluation | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |

**موقع AMAN:** يتفوّق على Zoho و QuickBooks في كل المعايير الدولية. يعادل SAP B1/D365/NetSuite في المحاسبة الأساسية مع أفضلية Multi‑book + MT940.

### 2.2 الخزينة والعمليات المالية (Treasury)

> **قسم جديد:** عمق الخزينة في AMAN هو أحد أقوى نقاطه التنافسية في MENA.

| الميزة | AMAN | Odoo EE | SAP B1 | D365 BC | NetSuite | Zoho | QB |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **شيكات تحت التحصيل + دورة حياة كاملة** | 🏆 | ⚠️ localization | ✅ (MENA) | ⚠️ | ⚠️ | ⚠️ | ❌ |
| **شيكات دفع آجلة (Post‑dated)** | 🏆 | ⚠️ | ✅ (MENA) | ⚠️ | ⚠️ | ⚠️ | ❌ |
| Notes Receivable / Payable | ✅ | ⚠️ | ✅ | ✅ | ✅ | ⚠️ | ❌ |
| سجل تقادم الشيكات (Checks Aging) | ✅ | ❌ | ✅ | ⚠️ | ⚠️ | ❌ | ❌ |
| Cash Flow Forecasting (بنظام دوري) | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅ | ⚠️ | ⚠️ |
| Payment Gateways (Stripe + **Tap + PayTabs**) | 🏆 | ✅ (Stripe) | ⚠️ | ⚠️ | ✅ | ✅ | ✅ |
| Bank Feeds (MT940 + CSV + OFX) | ✅ | ⚠️ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| FX Revaluation دورية | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |

**موقع AMAN:** 🏆 **الأقوى في MENA** — دورة شيكات آجلة كاملة + بوابات دفع خليجية داخلية، وهي مميزات تتطلب localization مدفوعة في SAP وغير متوفّرة في Zoho/QB.

### 2.3 المبيعات و CRM و POS

| الميزة | AMAN | Odoo EE | SAP B1 | D365 BC | NetSuite | Zoho | QuickBooks |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| عروض أسعار → SO → **Delivery Order** → فاتورة | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| Credit / Debit Notes | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **فوترة جزئية (Partial Invoicing)** | ✅ | ⚠️ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **حد ائتمان ذكي (Smart Credit Limit Check)** | ✅ | ⚠️ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **CPQ Engine** (Configurator + Rules + PDF) | 🏆 | ⚠️ | ⚠️ | ⚠️ | ✅ | ❌ | ❌ |
| قوائم أسعار (عميل/فرع/تاريخ) | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| عمولات المبيعات + قواعد | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ❌ |
| مبيعات متعدّدة الفروع | 🏆 | ⚠️ | ✅ | ✅ | ✅ | ⚠️ | ❌ |
| **CRM:** Leads + Opportunities + Pipeline | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ❌ |
| **Lead Scoring + Customer Segmentation** | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ |
| **Knowledge Base + Tickets + Campaigns** | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ |
| **POS** + طباعة حرارية + QR ZATCA | ✅ | ✅ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ❌ |
| **POS Offline Mode + Sync** | ✅ | ✅ | ⚠️ | ❌ | ❌ | ❌ | ❌ |
| **POS Kitchen Display (KDS) + Customer Display** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **POS Table Management** (مطاعم) | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| إدارة ورديّات POS + Cash Count | ✅ | ✅ | ⚠️ | ❌ | ⚠️ | ❌ | ❌ |
| **Loyalty Programs + Points** | ✅ | ✅ | ❌ | ⚠️ | ✅ | ⚠️ | ❌ |
| **Promotions Engine** (rules‑based) | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | ⚠️ | ❌ |

**موقع AMAN:** يغطّي طيفاً نادراً: CPQ + CRM + POS offline + KDS + Loyalty + Promotions في نظام واحد مفتوح — يضاهي NetSuite/Odoo ويتفوّق بوضوح على Zoho/QB/SAP B1.

### 2.4 المشتريات وإدارة الموردين

| الميزة | AMAN | Odoo EE | SAP B1 | D365 BC | NetSuite | Zoho | QuickBooks |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| PR → RFQ → PO → GRN | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| استلام + مرتجعات + Shipments | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Blanket PO + Releases | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Purchase Agreements (اتفاقيات إطارية) | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Landed Cost (شحن + جمارك + تأمين) | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Three‑Way Matching** (PO/GRN/Invoice + Tolerances) | ✅ | ⚠️ | ✅ | ✅ | ✅ | ❌ | ❌ |
| تقييم أداء المورّد (Supplier Ratings) | ✅ | ⚠️ | ✅ | ✅ | ✅ | ⚠️ | ❌ |
| موافقات متعدّدة المستويات + SLA + Escalation | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ❌ |

### 2.5 المخزون وسلسلة الإمداد

| الميزة | AMAN | Odoo EE | SAP B1 | D365 BC | NetSuite | Zoho | QuickBooks |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| مستودعات متعدّدة + تحويلات | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| **Bin Locations** (مواقع داخل المستودع) | ✅ | ✅ | ⚠️ | ✅ | ✅ | ❌ | ❌ |
| **Product Variants** (مقاس/لون/مادة) | ✅ | 🏆 | ⚠️ | ✅ | ✅ | ⚠️ | ❌ |
| **Product Kits** (مجموعات منتجات) | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ❌ |
| Batch/Lot + Serial tracking | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| FIFO / LIFO / WAC | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| **Cost Layer Policy Versioning** | 🏆 | ❌ | ⚠️ | ❌ | ⚠️ | ❌ | ❌ |
| Reorder Points + MRP الأساسي | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| **Demand Forecasting** (إحصائي) | ✅ | ⚠️ | ✅ | ⚠️ | ✅ | ⚠️ | ❌ |
| Cycle Count + Stock Adjustments | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ❌ |
| **Quality Inspections** | ✅ | ✅ | ✅ | ⚠️ | ✅ | ❌ | ❌ |
| Barcode + QR + Scanning UI | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| GL Entry على التحويلات متعدّدة الأصناف | ✅ (INV‑L04) | ✅ | ✅ | ✅ | ✅ | ⚠️ | ❌ |
| Product Ledger (سجلّ حركة تفصيلي) | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |

### 2.6 التصنيع

| الميزة | AMAN | Odoo EE | SAP B1 | D365 BC | NetSuite | Zoho | QB |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| BOM متعدّد المستويات + Phantom | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Work Orders + Routing + Operations | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Work Centers + Equipment Registry | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **MRP‑II Planning** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Capacity Planning + Load** | ✅ | ⚠️ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Production Scheduler** (drag‑and‑drop) | ✅ | ✅ | ⚠️ | ✅ | ✅ | ❌ | ❌ |
| **Job Cards + Shop‑floor Entry** | ✅ | ✅ | ⚠️ | ✅ | ✅ | ❌ | ❌ |
| Standard Costing + Variance Analysis | ✅ | ⚠️ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Direct Labor Report** | ✅ | ⚠️ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Equipment Maintenance + CMMS** | ✅ | ✅ | ⚠️ | ✅ | ✅ | ❌ | ❌ |
| Production Analytics + WO Status Report | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| MES Real‑time (IoT على أرض المصنع) | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ❌ | ❌ |

### 2.7 الموارد البشرية والرواتب

| الميزة | AMAN | Odoo EE | SAP B1 | D365 BC | NetSuite | Zoho | QuickBooks |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| بيانات موظّفين + هيكل تنظيمي + Documents | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ⚠️ |
| حضور + انصراف + Geo‑fencing | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ❌ |
| إجازات + Accruals + **Leave Carryover** | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ❌ |
| **Salary Structures** (مركّبات راتب مرنة) | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | ✅ | ⚠️ |
| Payroll + Payslips + مسيرات | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | ✅ | ⚠️ |
| **GOSI** (9.75% + 12% automatic) | 🏆 | ⚠️ | localization | ❌ | ⚠️ | Zoho People only | ❌ |
| **WPS SIF Export** (بنك مركزي سعودي) | 🏆 | ❌ | localization | ❌ | ❌ | ⚠️ | ❌ |
| **لوحة السعودة + نسب الاحتساب** | 🏆 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| WHT | ✅ | ⚠️ | ✅ | ⚠️ | ✅ | ⚠️ | ❌ |
| **Custody Management** (عهد الموظفين) | 🏆 | ❌ | ⚠️ | ❌ | ❌ | ❌ | ❌ |
| **Violations / Disciplinary Actions** | 🏆 | ❌ | ❌ | ❌ | ⚠️ | ⚠️ | ❌ |
| **EOS Settlement** (نهاية خدمة خليجية) | 🏆 | ❌ | localization | ❌ | ❌ | ⚠️ | ❌ |
| **Loans + Advances** | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅ | ⚠️ | ❌ |
| **Overtime Requests + Approvals** | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ❌ |
| Self‑service Portal | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ❌ |
| Recruitment + Training Programs | ✅ | ✅ | ❌ | ⚠️ | ✅ | ✅ (Recruit) | ❌ |
| **Performance Reviews + Goals + Composite Scoring** | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ (People) | ❌ |
| تقييم ذاتي + تقييم مدير + دورات مراجعة | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ❌ |

**موقع AMAN:** 🏆 **الأقوى في GCC** — GOSI + WPS + السعودة + Custody + Violations + EOS خليجي مبنية داخلياً. SAP وOdoo يطلبان localization apps مدفوعة؛ Zoho/QB لا يغطّيان هذه المنطقة أصلاً.

### 2.8 المشاريع

| الميزة | AMAN | Odoo EE | SAP B1 | D365 BC | NetSuite SRP | Zoho | QB |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| WBS + **Gantt Chart** | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | ⚠️ | ❌ |
| Timesheets + Approval | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ⚠️ |
| مصروفات مشروع + فواتير | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ⚠️ |
| Revenue Recognition (IFRS 15 على المشروع) | ✅ | ⚠️ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Resource Planning + Allocation + Calendar** | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | ⚠️ | ❌ |
| **Risk Register** | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅ | ❌ | ❌ |
| **Project Financials Report** (P&L على المشروع) | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ❌ |
| **Resource Utilization Report** | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | ⚠️ | ❌ |

### 2.9 الأصول الثابتة

| الميزة | AMAN | Odoo EE | SAP B1 | D365 BC | NetSuite | Zoho | QB |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| FA Register + Categories + Tags | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| Straight‑line Depreciation | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| Declining‑balance / Units‑of‑production | ⚠️ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ❌ |
| Disposal + Gain/Loss Entry | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| Maintenance + Equipment Registry | ✅ | ✅ | ⚠️ | ✅ | ✅ | ❌ | ❌ |
| **Lease Contracts (IFRS 16)** + جدول إطفاء | ✅ | ⚠️ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Revaluation + Impairment (IAS 36) | ✅ | ❌ | ✅ | ⚠️ | ✅ | ❌ | ❌ |

### 2.10 الخدمات وإدارة الوثائق (Service & DMS)

> **قسم جديد:** Field Service + Document Management غير مغطّى في المقارنات السابقة.

| الميزة | AMAN | Odoo EE | SAP B1 | D365 BC | NetSuite | Zoho | QB |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Service Requests + Work Orders | ✅ | ✅ | ✅ | ✅ (Field Service) | ✅ | ⚠️ (Desk) | ❌ |
| Technician Assignment + Routing | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ❌ |
| Service Costs + Billing | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ❌ |
| **Document Management** (رفع + إصدارات + بحث) | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | ✅ | ❌ |
| Document Versioning + Audit | ✅ | ✅ | ❌ | ⚠️ | ✅ | ⚠️ | ❌ |

### 2.11 العقود و CPQ (Contract Lifecycle + Configure‑Price‑Quote)

> **قسم جديد:** CLM + CPQ كوحدات مستقلة.

| الميزة | AMAN | Odoo EE | SAP B1 | D365 BC | NetSuite | Zoho | QB |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Contract Master + Terms + Milestones | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | ⚠️ | ❌ |
| **Contract Amendments** + إصدارات | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅ | ❌ | ❌ |
| Contract → Invoice Automation | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ❌ |
| **CPQ Product Configurator** | 🏆 | ⚠️ | ⚠️ | ⚠️ | ✅ | ❌ | ❌ |
| Configuration Rules + Validation | 🏆 | ⚠️ | ⚠️ | ⚠️ | ✅ | ❌ | ❌ |
| CPQ → Quote → PDF | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅ | ❌ | ❌ |

### 2.12 الاشتراكات والفوترة المتكرّرة (Subscription Billing)

> **قسم جديد:** ليست مجرّد MRR/ARR بل دورة كاملة.

| الميزة | AMAN | Odoo Subs | SAP B1 | D365 BC | NetSuite SuiteBilling | Zoho Billing | QB |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Subscription Plans + Tiers | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | ✅ | ❌ |
| Enrollments + Customer Lifecycle | ✅ | ✅ | ❌ | ⚠️ | ✅ | ✅ | ❌ |
| Plan Changes + **Prorations** | ✅ | ⚠️ | ❌ | ❌ | ✅ | ✅ | ❌ |
| Recurring Invoicing + Auto‑charge | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | ✅ | ⚠️ |
| Dunning + Retry Logic | ✅ | ⚠️ | ❌ | ❌ | ✅ | ✅ | ❌ |
| MRR / ARR / Churn Metrics | ✅ | ⚠️ | ❌ | ⚠️ | ✅ | ⚠️ | ❌ |

### 2.13 التقارير والذكاء الأعمالي

| الميزة | AMAN | Odoo EE | SAP B1 | D365 BC | NetSuite | Zoho | QB |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| الميزانية العمومية + P&L | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Cashflow Statement | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| AR/AP Aging | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Dashboard معرّف بالدور (10 أدوار) | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ⚠️ |
| **Custom Dashboard Builder** (widgets + 8 data sources) | ✅ | ⚠️ | ⚠️ | ✅ | ✅ SuiteAnalytics | ✅ Analytics | ❌ |
| KPI Dashboard + **Industry KPI Widgets** (7 قطاعات وفق NRF/USALI/PMI/AICPA) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Report Builder** (self‑service) | ✅ | ⚠️ Studio | ⚠️ | ✅ | 🏆 SuiteAnalytics | ✅ Analytics | ⚠️ |
| **Industry Reports** (صناعة‑محدّدة) | ✅ | ⚠️ | ✅ | ⚠️ | ✅ | ⚠️ | ❌ |
| **Shared Reports** + صلاحيات | ✅ | ⚠️ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Scheduled Reports + Email + 11 أنواع | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| تقارير عربية RTL | 🏆 | ⚠️ | localization | ⚠️ | ⚠️ | ⚠️ | ❌ |
| AI‑driven Forecasting & Anomaly Detection | ⚠️ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ⚠️ |
| Power BI / Looker embed | ❌ | ⚠️ | ✅ | ✅ | ✅ | ⚠️ | ❌ |

### 2.14 الامتثال الضريبي متعدّد الولايات (Multi‑Jurisdiction Tax)

> **قسم جديد:** AMAN يملك محرّك ضرائب فريد مع فوترة إلكترونية متعدّدة الدول.

| الميزة | AMAN | Odoo EE | SAP B1 | D365 BC | NetSuite | Zoho | QB |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **ZATCA Phase 2 + QR** (السعودية) | 🏆 | ⚠️ loc | ✅ loc | ⚠️ | ⚠️ | ⚠️ | ❌ |
| **UAE FTA E‑invoicing** | 🏆 | ⚠️ loc | ✅ loc | ⚠️ | ⚠️ | ⚠️ | ❌ |
| **Egypt ETA E‑invoicing** | 🏆 | ⚠️ loc | ⚠️ | ⚠️ | ❌ | ⚠️ | ❌ |
| **Zakat Calculator** (السعودية) | 🏆 | ❌ | loc | ❌ | ❌ | ❌ | ❌ |
| VAT Report (تقرير ضريبة مضافة) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| Tax Calendar + Reminders | ✅ | ⚠️ | ✅ | ✅ | ✅ | ⚠️ | ❌ |
| Tax Audit Trail | ✅ | ⚠️ | ✅ | ✅ | ✅ | ⚠️ | ❌ |
| **Tax Regimes per‑Branch** (multi‑jurisdiction) | 🏆 | ⚠️ | ✅ | ✅ | ✅ | ❌ | ❌ |
| WHT (استقطاعات مصدر) | ✅ | ⚠️ | ✅ | ⚠️ | ✅ | ⚠️ | ❌ |
| Tax Compliance non‑GCC (EU VAT / US SalesTax) | ⚠️ | ✅ | ✅ | ✅ | ✅ (Avalara) | ⚠️ | ✅ (Avalara) |

**موقع AMAN:** 🏆 **الأعلى في MENA** — الدولة الوحيدة التي تبني ZATCA + FTA + ETA معاً داخل النواة، مع حاسبة زكاة أصلية. خارج MENA يجب إدراج Avalara/Vertex.

### 2.15 التكاملات الخارجية (Integrations)

> **قسم جديد:** ناقل تكاملات AMAN قوي إقليمياً.

| الفئة | AMAN | Odoo EE | SAP B1 | D365 BC | NetSuite | Zoho | QB |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **E‑Invoicing متعدّد الدول** (ZATCA + FTA + ETA) | 🏆 | ⚠️ loc | ✅ loc | ⚠️ | ⚠️ | ⚠️ | ❌ |
| **Payment Gateways:** Stripe / **Tap / PayTabs** | 🏆 | ✅ Stripe | ⚠️ | ⚠️ | ✅ | ✅ | ✅ |
| **Shipping Carriers:** DHL / **Aramex** | 🏆 | ✅ DHL | ⚠️ | ✅ | ✅ | ⚠️ | ❌ |
| **SMS Gateways:** **Taqnyat / Unifonic** / Twilio | 🏆 | ⚠️ Twilio | ⚠️ | ⚠️ | ✅ | ✅ | ❌ |
| **Bank Feeds:** MT940 + CSV + OFX | ✅ | ⚠️ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| REST API + OpenAPI Spec | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **API Key Lifecycle** (scopes + rate‑limit + expiry + revoke) | ✅ | ⚠️ OAuth | ⚠️ | ✅ | ✅ | ✅ | ❌ |
| **Webhooks + Outbox Relay Pattern** | ✅ | ⚠️ | ⚠️ | ✅ | ✅ | ✅ | ⚠️ |
| **Event Bus (Redis Streams)** | ✅ | ❌ | ⚠️ | ⚠️ | ✅ | ❌ | ❌ |
| **WebSocket Real‑time** | ✅ | ⚠️ | ❌ | ⚠️ | ⚠️ | ⚠️ | ❌ |

**موقع AMAN:** 🏆 **مجموعة تكاملات خليجية أصلية** لا يوفّرها أيّ من المنافسين دون وسيط.

### 2.16 Workflows والموافقات المتقدّمة

| الميزة | AMAN | Odoo EE | SAP B1 | D365 BC | NetSuite SuiteFlow | Zoho | QB |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Workflows متعدّدة الخطوات | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ Blueprint | ❌ |
| Min/Max Amount Triggers | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ❌ |
| **SLA Hours + Escalation Tree** | ✅ | ⚠️ | ⚠️ | ✅ | ✅ | ⚠️ | ❌ |
| **Parallel Approvals** | ✅ | ⚠️ | ⚠️ | ✅ | ✅ | ⚠️ | ❌ |
| **Auto‑approve Threshold** | ✅ | ⚠️ | ⚠️ | ✅ | ✅ | ⚠️ | ❌ |
| موافقات عبر كل الوحدات (PO/HR/GL) | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ❌ |

### 2.17 المنصّة (البنية والأمان والتشغيل)

| الميزة | AMAN | Odoo EE | SAP B1 | D365 BC | NetSuite | Zoho | QB |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Multi‑tenant (DB‑per‑company)** | ✅ | ⚠️ row‑level | ⚠️ | ✅ | ✅ | ✅ | ❌ |
| **Tenant Isolation Middleware** | ✅ | ⚠️ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Multi‑company + Multi‑branch | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| JWT + 2FA TOTP + Session Mgmt | ✅ | ⚠️ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| SSO (SAML 2.0 + OAuth + LDAP + Group→Role) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| RBAC بصلاحيات دقيقة (192 permission + aliases) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| Password Policy + Security Events Log | ✅ | ⚠️ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| Audit Trail (field‑level diff + immutable) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| CSRF + HttpOnly Cookies + CSP Headers | ✅ | ⚠️ | — | — | — | — | — |
| Rate Limiting (login + global + per‑endpoint) | ✅ | ⚠️ | ⚠️ | ✅ | ✅ | ✅ | ⚠️ |
| **Field Encryption at Rest** | ✅ | ⚠️ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| **PII Masking** (GDPR/PDPL‑aligned) | ✅ | ⚠️ | ⚠️ | ✅ | ✅ | ⚠️ | ❌ |
| **Optimistic Lock + Fiscal Lock** | ✅ | ⚠️ | ✅ | ✅ | ✅ | ⚠️ | ❌ |
| **SQL Safety Linter في CI** | 🏆 | ❌ | — | — | — | — | — |
| **GL Posting Discipline Checker** (CI) | 🏆 | ❌ | ⚠️ | ⚠️ | ⚠️ | ❌ | ❌ |
| gitleaks CI + Secret Scanning | ✅ | ❌ | — | — | — | — | — |
| **Duplicate Detection** (parties/products) | ✅ | ⚠️ | ✅ | ✅ | ✅ | ⚠️ | ❌ |
| Prometheus Metrics + **Alerting Rules** + Grafana | ✅ | ⚠️ | ⚠️ | ✅ | ⚠️ | ❌ | ❌ |
| **Nginx Hardening** (SSL + SecHeaders + HTTP/2 + RL) | ✅ | ⚠️ | — | — | — | — | — |
| **Backup / Restore UI + Scripts** | ✅ | ⚠️ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| Docker Compose prod (isolated net + no exposed DB) | ✅ | ⚠️ | — | — | — | — | — |
| Alembic DB Migrations (versioned schema) | ✅ | ✅ | ✅ | ✅ | ✅ | — | ⚠️ |
| **Plugin Registry** (internal extension SDK) | ✅ | 🏆 Apps | ⚠️ | ⚠️ | ✅ | ⚠️ | ⚠️ |
| App Marketplace عام | ❌ | 🏆 | ❌ | ⚠️ | ✅ | ⚠️ | ⚠️ |
| Mobile App (React Native) + Offline Sync + Conflict Resolution | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Mobile Device Registration + Push Notifications | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ✅ |
| **i18n AR/EN + RTL كامل** (Layout+Formulas+Printout) | 🏆 | ⚠️ | localization | ⚠️ | ⚠️ | ⚠️ | ❌ |
| Localized Error Messages (errors.ar.json) | ✅ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ❌ |
| **Global Search** (cross‑module) | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ⚠️ |
| **Dark Mode + Theme Toggle** | ✅ | ✅ | ❌ | ✅ | ⚠️ | ✅ | ⚠️ |
| **Onboarding Wizard + Industry Setup** | ✅ | ✅ | ⚠️ | ⚠️ SuiteSuccess | ✅ | ✅ | ⚠️ |
| **Per‑Tenant Module Customization** (Industry‑driven module set) | ✅ | ⚠️ | ⚠️ | ✅ Extensions | ✅ Feature Flags | ❌ | ❌ |
| Notifications (WS + Email + SMS + In‑app) | ✅ | ⚠️ | ⚠️ | ✅ | ✅ | ✅ | ⚠️ |
| **Data Import Framework** (per‑entity configs) | ✅ | ✅ | ✅ DTW | ✅ RapidStart | ✅ SmartBundles | ✅ | ⚠️ |

---

## 3 · المقارنة حسب النموذج الاقتصادي

| البعد | AMAN | Odoo EE | SAP B1 | D365 BC | NetSuite | Zoho Books | QuickBooks |
|---|---|---|---|---|---|---|---|
| **الترخيص** | مملوك خاص / مفتوح داخلياً | Odoo EE ($) + Community (مجاني) | Perpetual + SaaS | SaaS per‑user | SaaS per‑user | SaaS per‑user | Desktop + SaaS |
| **التكلفة ($/user/month)** | 0 (self‑hosted) | ~31 | ~94 | ~70 | ~99+ | ~15 | ~30 |
| **النشر** | Docker / Cloud / On‑prem | SaaS / On‑prem | SAP Cloud / On‑prem | Azure Cloud | Oracle Cloud فقط | SaaS فقط | Desktop / SaaS |
| **التخصيص** | مفتوح كامل + Plugin Registry | Python Modules | SDK | AL / Extensions | SuiteScript | محدود | محدود جداً |
| **البيانات** | تحت تحكّم العميل | عميل/مستضاف | متنوّع | Microsoft DC | Oracle Cloud | Zoho Cloud | Intuit Cloud |
| **اللغات GCC** | 🏆 كامل داخلي | ⚠️ عبر localization apps | ✅ localization مدفوعة | ⚠️ Partner Add‑ons | ⚠️ Partner | ⚠️ partial | ❌ |
| **بوّابات GCC** (Tap/PayTabs/Aramex/Taqnyat) | 🏆 مدمج | ❌ | ⚠️ | ❌ | ❌ | ⚠️ | ❌ |

---

## 4 · المميّزات التنافسية لـ AMAN (🏆)

1. **الامتثال MENA العميق داخل النواة** — ZATCA Phase 2 + UAE FTA + Egypt ETA + WPS + GOSI + السعودة + WHT + **الزكاة**، بدون شراء localization modules منفصلة.
2. **الخزينة الخليجية الكاملة** — دورة شيكات آجلة (post‑dated) + Notes Receivable/Payable + Checks Aging، ميزة نادرة خارج SAP B1 localization.
3. **بوّابات إقليمية أصلية** — Tap + PayTabs + Aramex + Taqnyat + Unifonic مدمجة داخل النواة.
4. **Multi‑tenant Database‑per‑Company** — عزل بياني حقيقي أقوى أمنياً من row‑level tenancy في Odoo/Zoho.
5. **Multi‑Book Accounting** (IFRS + Local GAAP) — par مع NetSuite، فوق Odoo/D365/Zoho/QB.
6. **Policy‑versioned Cost Layers (FIFO/LIFO)** — إصدارات سياسات التكلفة مع تاريخ صلاحية، نادرة خارج SAP.
7. **IFRS 15 / 9 / 16 + IAS 36 مبنية داخلياً** — تمييز واضح على Zoho/QB وحتى Odoo.
8. **RTL عربي حقيقي** — ليس ترجمة نصوص فحسب، بل Layout كامل + Formulas + Printout + Invoice templates.
9. **CPQ Engine أصلي** + Three‑Way Matching + Advanced Workflow (SLA/Escalation/Parallel) — يُضاهي NetSuite بتكلفة صفر.
10. **POS متكامل** مع Offline + KDS + Customer Display + Table Mgmt + Loyalty + Promotions.
11. **HR خليجي شامل** — Custody + Violations + EOS + Loans + Leave Carryover — ميزات لا توجد حتى في localization apps المدفوعة.
12. **منصّة DevSecOps أصلية** — SQL Safety Linter CI + GL Posting Discipline Checker + gitleaks + CSRF + HttpOnly + CSP + Field Encryption + PII Masking + Fiscal Lock + Optimistic Lock.
13. **Event Bus (Redis) + Outbox Pattern + WebSocket Real‑time** — بنية enterprise للأحداث والإشعارات المباشرة.
14. **Plugin Registry + Industry Setup** — هيكل قابل للتوسعة جاهز لـ marketplace داخلي مستقبلاً.
15. **Industry‑Ready فعليًا** — 12 قالب دليل حسابات (SOCPA/IFRS) + قواعد ترحيل GL حسب النشاط + KPIs وفق NRF/USALI/PMI/AICPA/DSCSA.
16. **المحاسبة المتقدّمة** — IAS 2 NRV + Consolidation مع Elimination Entries + Entity Tree — ميزات enterprise نادرة خارج NetSuite/SAP.
17. **Open stack** (FastAPI + React + PG + Redis + Nginx) — صفر lock‑in.

---

## 5 · فجوات AMAN (لا يوجد أو جزئي)

| الفجوة | الخطر | الحل المقترح |
|---|---|---|
| AI‑driven Forecasting & Anomaly Detection حقيقي | متوسّط | إضافة scikit‑learn/Prophet/ARIMA على Cash Flow + Demand Forecast |
| **App Marketplace عام** (مقابل Plugin Registry الداخلي) | منخفض | تحويل Plugin Registry إلى SDK + store عام |
| Power BI / Looker / Metabase embed | منخفض | REST API جاهز — يحتاج مجرّد توثيق |
| **MES Real‑time** (IoT على أرض المصنع) | للصناعة الثقيلة فقط | MQTT / OPC‑UA plugin |
| **Declining‑balance / Units‑of‑production** depreciation | منخفض | إضافة method enum + formula (أسبوع عمل) |
| E‑signature مدمج (DocuSign‑like) | منخفض | تكامل خارجي عبر webhooks |
| Tax compliance **خارج GCC** (EU VAT / US SalesTax) | مرتفع لو targeting أسواق أخرى | Avalara/Vertex plugin |
| Deep Reporting Designer (Crystal/SSRS grade) | منخفض | Report Builder يغطّي 80%، متبقّي formulas معقّدة |

---

## 6 · الخلاصة والتصنيف السوقي

> **AMAN ERP يقف في الفئة الوسطى‑العليا بين Odoo Enterprise و Dynamics 365 BC من حيث نطاق المزايا، ويتفوّق على الجميع (بما فيهم SAP B1) في الامتثال MENA واللغة العربية والبوابات الخليجية.**

**التصنيف حسب السوق المستهدف:**

| السوق / الحجم | البديل الأمثل | موقع AMAN |
|---|---|---|
| SMB خليجي/سعودي (≤ 200 موظف) | **AMAN** | 🥇 الأفضل (GOSI + WPS + ZATCA + Tap + PayTabs + Aramex) |
| SMB مصري | **AMAN** | 🥇 الأفضل (ETA e‑invoicing أصلي) |
| SMB إماراتي | **AMAN** | 🥇 الأفضل (FTA e‑invoicing أصلي) |
| Mid‑market إقليمي (200–2000) | AMAN / D365 BC | 🥈 منافس قوي مع Multi‑book + Subscriptions + CPQ |
| Enterprise عالمي (+2000) | SAP S/4HANA / Oracle Fusion | فجوة: يحتاج MES real‑time + AI forecasting |
| خدمات محترفة + Projects | AMAN / NetSuite SRP | 🥇 منافس قوي (Gantt + Risk + Rev Rec + Resource Planning) |
| تجارة تجزئة + POS | AMAN / Odoo | 🥇 POS قوي (Offline + KDS + Loyalty) |
| تصنيع متوسّط/خفيف | AMAN / Odoo MRP | 🥇 MRP‑II + Capacity + Scheduler |
| تصنيع ثقيل متقدّم (MES) | SAP / Infor | فجوة MES real‑time |
| مكاتب محاسبة + مراجعين | AMAN / Zoho | 🥇 Multi‑company + Audit Trail عميق |

**التوصية:** AMAN ERP **جاهز للإنتاج** للسوق السعودي/الخليجي/المصري في SMB و Mid‑market بكفاءة تضاهي الأنظمة التجارية بتكلفة ترخيص صفرية، ومع **تمييز تنافسي حقيقي** في 17 نقطة موثّقة أعلاه.

---

_آخر تحديث: 22 أبريل 2026_


















































































