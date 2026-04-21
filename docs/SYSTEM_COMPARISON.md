# AMAN ERP — مقارنة شاملة مع الأنظمة العالمية

> **تاريخ المقارنة:** 21 أبريل 2026
> **إصدار AMAN:** `main` @ latest
> **الغرض:** تقييم موضوعي لموقع نظام AMAN مقابل أبرز أنظمة تخطيط موارد المؤسسات عالمياً (Odoo, SAP Business One, Microsoft Dynamics 365 Business Central, NetSuite, Zoho Books, QuickBooks Enterprise).

---

## 1 · الملخّص التنفيذي

| المقياس | AMAN ERP | التقييم |
|---|---|---|
| **نطاق الوحدات** | 10 وحدات رئيسية + 56 router + ~872 endpoint | يعادل Odoo Enterprise / Dynamics 365 BC |
| **قاعدة الكود** | FastAPI + React 18 + PostgreSQL + Redis | Stack حديث full‑open‑source |
| **اللغات/التوطين** | عربي/إنجليزي كامل مع RTL | متفوّق على معظم المنافسين الغربيين |
| **الامتثال السعودي/الخليجي** | ZATCA Phase 2، WPS، GOSI، السعودة، WHT | **أفضل من الجميع في GCC** عدا SAP المحلية |
| **الأمان** | JWT + 2FA + CSRF + HttpOnly + gitleaks CI | على مستوى المؤسسات |
| **التعدّدية** | Multi‑tenant + Multi‑company + Multi‑branch + Multi‑currency | يطابق NetSuite/Dynamics |
| **النضج الوظيفي** | 95%+ مكتمل في المحاسبة/المبيعات/المخزون/HR | قابل للإنتاج |
| **نقاط ضعف** | لا يوجد AI/ML جاهز، لا Marketplace extensions عامة | فجوة أمام Odoo/NetSuite |

---

## 2 · مصفوفة المقارنة بالوحدات

> ✅ = مكتمل ومطابق للمعيار &nbsp;&nbsp; ⚠️ = موجود جزئياً &nbsp;&nbsp; ❌ = غير موجود &nbsp;&nbsp; 🏆 = ميزة تنافسية لـ AMAN

### 2.1 المحاسبة والتمويل

| الميزة | AMAN | Odoo EE | SAP B1 | D365 BC | NetSuite | Zoho Books | QuickBooks |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| دليل حسابات متعدّد المستويات | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| قيود يومية متعدّدة العملات | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| فترات مالية + قفل | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| إقفال سنوي مع reversals | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| مطابقة بنكية + CSV import | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| موازنات + cost centers | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ❌ |
| IFRS 15 (revenue recognition) | ✅ | ⚠️ | ✅ | ✅ | ✅ | ❌ | ❌ |
| IFRS 9 (ECL provisions) | ✅ | ❌ | ✅ | ⚠️ | ✅ | ❌ | ❌ |
| IAS 36 (impairment) | ✅ | ❌ | ✅ | ⚠️ | ✅ | ❌ | ❌ |
| Subscription MRR/ARR | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅ | ⚠️ | ❌ |
| Intercompany | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| FX revaluation | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| ZATCA Phase 2 QR | 🏆 | ⚠️ | ✅ (localization) | ⚠️ | ⚠️ | ⚠️ | ❌ |

**موقع AMAN:** يتفوّق على Zoho و QuickBooks في المعايير الدولية (IFRS 15/9، IAS 36). يعادل SAP B1/Dynamics/NetSuite في المحاسبة الأساسية مع أفضلية في ZATCA.

### 2.2 المبيعات و CRM و POS

| الميزة | AMAN | Odoo EE | SAP B1 | D365 BC | NetSuite | Zoho | QuickBooks |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| عروض أسعار → SO → فاتورة | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Credit / Debit notes | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| CPQ (Configure-Price-Quote) | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅ | ❌ | ❌ |
| قوائم أسعار العميل/الفرع | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| عمولات مبيعات | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ❌ |
| POS مع طباعة حرارية + QR | ✅ | ✅ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ❌ |
| إدارة ورديّات POS | ✅ | ✅ | ⚠️ | ❌ | ⚠️ | ❌ | ❌ |
| CRM (فرص، تذاكر، حملات) | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ❌ |
| مبيعات متعدّدة الفروع | 🏆 | ⚠️ | ✅ | ✅ | ✅ | ⚠️ | ❌ |

**موقع AMAN:** يغطي طيفاً أوسع من POS + CRM + CPQ في نظام واحد، ممّا يشبه NetSuite لكن بتكلفة مفتوحة المصدر.

### 2.3 المشتريات وإدارة الموردين

| الميزة | AMAN | Odoo EE | SAP B1 | D365 BC | NetSuite | Zoho | QuickBooks |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| طلب شراء (PR) → RFQ → PO | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| استلام + مرتجعات | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Blanket PO | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Landed cost | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| موافقات متعدّدة المستويات | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ❌ |
| تقييم أداء المورّد | ✅ | ⚠️ | ✅ | ✅ | ✅ | ⚠️ | ❌ |

### 2.4 المخزون وسلسلة الإمداد

| الميزة | AMAN | Odoo EE | SAP B1 | D365 BC | NetSuite | Zoho | QuickBooks |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| مستودعات متعدّدة + تحويلات | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| Batch/Lot + serials | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| FIFO / LIFO / WAC | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| Cost layer policy versioning | 🏆 | ❌ | ⚠️ | ❌ | ⚠️ | ❌ | ❌ |
| Reorder points / MRP | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| Cycle count | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ❌ |
| Barcode + QR | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| GL entry على التحويل متعدّد‑الأصناف | ✅ (جديد: INV‑L04) | ✅ | ✅ | ✅ | ✅ | ⚠️ | ❌ |

### 2.5 التصنيع

| الميزة | AMAN | Odoo EE | SAP B1 | D365 BC | NetSuite | Zoho | QB |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| BOM متعدّد المستويات | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Work orders + Routing | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Work centers + equipment | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Shop‑floor entry | ✅ | ✅ | ⚠️ | ✅ | ✅ | ❌ | ❌ |
| Standard costing + variance | ✅ | ⚠️ | ✅ | ✅ | ✅ | ❌ | ❌ |
| MES real‑time | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ❌ | ❌ |

### 2.6 الموارد البشرية والرواتب

| الميزة | AMAN | Odoo EE | SAP B1 | D365 BC | NetSuite | Zoho | QuickBooks |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| بيانات موظّفين + هيكل | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ⚠️ |
| حضور + انصراف | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ❌ |
| إجازات + Accruals | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ❌ |
| Payroll + Payslips | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | ✅ | ⚠️ |
| **GOSI** (9.75% + 12%) | 🏆 | ⚠️ | localization | ❌ | ⚠️ | Zoho People only | ❌ |
| **WPS SIF export** | 🏆 | ❌ | localization | ❌ | ❌ | ⚠️ | ❌ |
| **لوحة السعودة** | 🏆 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| WHT | ✅ | ⚠️ | ✅ | ⚠️ | ✅ | ⚠️ | ❌ |
| Self‑service | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ❌ |
| Recruiting + Training | ✅ | ✅ | ❌ | ⚠️ | ✅ | ✅ (Zoho Recruit) | ❌ |

**موقع AMAN:** الأقوى في GCC HR — GOSI + WPS + السعودة مبنية داخل النظام، وهذا يحتاج دفع إضافي في SAP/Odoo.

### 2.7 المشاريع

| الميزة | AMAN | Odoo EE | SAP B1 | D365 BC | NetSuite SRP | Zoho | QB |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| WBS + Gantt | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | ⚠️ | ❌ |
| Timesheets | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ⚠️ |
| مصروفات مشروع | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ⚠️ |
| Revenue Recognition على المشروع | ✅ | ⚠️ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Resource planning | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | ⚠️ | ❌ |

### 2.8 الأصول الثابتة

| الميزة | AMAN | Odoo EE | SAP B1 | D365 BC | NetSuite | Zoho | QB |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| FA register | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| Straight‑line depreciation | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| Declining‑balance / Units | ⚠️ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ❌ |
| Disposal + gain/loss | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| صيانة + سجلّ معدات | ✅ | ✅ | ⚠️ | ✅ | ✅ | ❌ | ❌ |

### 2.9 التقارير والذكاء الأعمالي

| الميزة | AMAN | Odoo EE | SAP B1 | D365 BC | NetSuite | Zoho | QB |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| الميزانية العمومية + P&L | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Cashflow statement | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| AR/AP Aging | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Dashboard معرّف بالدور | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ⚠️ |
| KPI Dashboard | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Scheduled reports + email | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| تقارير عربية RTL | 🏆 | ⚠️ | localization | ⚠️ | ⚠️ | ⚠️ | ❌ |
| AI‑driven forecasting | ⚠️ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ⚠️ |
| Power BI / Looker embed | ❌ | ⚠️ | ✅ | ✅ | ✅ | ⚠️ | ❌ |

### 2.10 المنصّة (البنية والأمان)

| الميزة | AMAN | Odoo EE | SAP B1 | D365 BC | NetSuite | Zoho | QB |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Multi‑tenant (DB‑per‑company) | ✅ | ⚠️ (row‑level) | ⚠️ | ✅ | ✅ | ✅ | ❌ |
| Multi‑company + branches | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| JWT + 2FA TOTP | ✅ | ⚠️ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| SSO (SAML/OAuth) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| RBAC بصلاحيات دقيقة | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| Audit trail كامل | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| CSRF / HttpOnly cookies | ✅ | ⚠️ | — | — | — | — | — |
| Rate limiting (login + global) | ✅ | ⚠️ | ⚠️ | ✅ | ✅ | ✅ | ⚠️ |
| gitleaks CI + secret scanning | ✅ | ❌ | — | — | — | — | — |
| Prometheus + Grafana | ✅ | ⚠️ | ⚠️ | ✅ | ⚠️ | ❌ | ❌ |
| Mobile app (iOS/Android) | ✅ (RN) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| i18n AR/EN + RTL كامل | 🏆 | ⚠️ | localization | ⚠️ | ⚠️ | ⚠️ | ❌ |
| REST API + webhooks | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| App marketplace | ❌ | 🏆 | ❌ | ⚠️ | ✅ | ⚠️ | ⚠️ |

---

## 3 · المقارنة حسب النموذج الاقتصادي

| البعد | AMAN | Odoo EE | SAP Business One | Dynamics 365 BC | NetSuite | Zoho Books | QuickBooks |
|---|---|---|---|---|---|---|---|
| **الترخيص** | مملوك خاص / مفتوح داخلياً | Odoo EE ($) + Community (مجاني) | Perpetual + SAAS | SAAS per‑user | SAAS per‑user | SAAS per‑user | Desktop + SAAS |
| **التكلفة ($/user/month)** | 0 (self‑hosted) | ~31 | ~94 | ~70 | ~99+ | ~15 | ~30 |
| **النشر** | Docker / cloud / on‑prem | SaaS / on‑prem | SAP Cloud / on‑prem | Azure cloud | Oracle cloud فقط | SaaS فقط | Desktop / SaaS |
| **التخصيص** | مفتوح كامل | Python modules | SDK | AL / Extensions | SuiteScript | محدود | محدود جداً |
| **البيانات** | تحت تحكّم العميل | عميل/مستضاف | متنوّع | Microsoft data center | Oracle cloud | Zoho cloud | Intuit cloud |
| **اللغات GCC** | 🏆 كامل | ⚠️ عبر localization apps | ✅ localization | ⚠️ partner add‑ons | ⚠️ partner | ⚠️ partial | ❌ |

---

## 4 · المميّزات التنافسية لـ AMAN (🏆)

1. **امتثال سعودي/خليجي عميق داخل النواة** — ZATCA Phase 2 + WPS + GOSI + السعودة + WHT + ضرائب متعدّدة النسب بحسب الفرع، بدون شراء localization modules منفصلة.
2. **Multi‑tenant database‑per‑company** — عزل بياني حقيقي، أقوى أمنياً من row‑level tenancy المعتمد في Odoo/Zoho.
3. **Policy‑versioned cost layers (FIFO/LIFO)** — تتبّع إصدارات سياسات التكلفة مع تاريخ صلاحية، ميزة نادرة خارج SAP.
4. **IFRS 15/9 + IAS 36 مبنية داخلياً** — تمييز على Zoho و QuickBooks، وحتى Odoo في بعض الحالات.
5. **RTL عربي حقيقي** — ليس مجرّد ترجمة نصوص؛ Layout كامل + formulas + printout.
6. **Open stack (FastAPI + React + PG + Redis)** — صفر lock‑in، سهل التوسعة.
7. **أمان جاهز للإنتاج** — CSRF + HttpOnly + gitleaks + CSP + 2FA + rate limiting بشكل إفتراضي.
8. **نظام موافقات متعدّد المستويات عبر كل الوحدات** — purchasing / HR / journal entries / expenses.

---

## 5 · فجوات AMAN (لا يوجد أو جزئي)

| الفجوة | الخطر | الحل المقترح |
|---|---|---|
| AI‑driven forecasting & anomaly detection | متوسّط | إضافة scikit‑learn/Prophet على cashflow + demand forecast |
| Marketplace للتوسعات | منخفض (نظام مغلق حالياً) | لاحقاً: plugin SDK + store |
| Power BI / Looker embed | منخفض | API موجود، يمكن توصيله |
| MES real‑time (IoT على أرض المصنع) | للصناعة الثقيلة فقط | MQTT / OPC‑UA plugin |
| Declining‑balance depreciation | منخفض | إضافة method enum + formula |
| E‑signature مدمج (DocuSign‑like) | منخفض | تكامل خارجي |
| Tax compliance non‑GCC (VAT EU, US sales tax) | مرتفع لو targeting أسواق أخرى | Tax engine plugin (Avalara/Vertex) |
| Deep reporting designer (like Crystal/SSRS) | منخفض | تم تغطيته بـ scheduled reports |

---

## 6 · الخلاصة

> **AMAN ERP يقف في الفئة الوسطى‑العليا بين Odoo Enterprise و Dynamics 365 BC من حيث نطاق المزايا، ويتفوّق على كلّيهما (وعلى SAP B1) في الامتثال السعودي/الخليجي واللغة العربية.**

**التصنيف حسب السوق المستهدف:**

| السوق / الحجم | البديل الأمثل | موقع AMAN |
|---|---|---|
| SMB خليجي/سعودي (≤ 200 موظف) | **AMAN** | 🥇 الأفضل (GOSI + WPS + ZATCA مدمج) |
| Mid‑market إقليمي (200–2000) | AMAN / D365 BC | 🥈 منافس قوي |
| Enterprise عالمي (+2000) | SAP S/4HANA / Oracle Fusion | فجوة: يحتاج MES/AI |
| خدمات محترفة + Projects | AMAN / NetSuite SRP | 🥈 منافس |
| تجارة تجزئة + POS | AMAN / Odoo | 🥇 POS قوي |
| تصنيع متقدّم (MES) | SAP / Infor | فجوة MES |

**التوصية:** AMAN جاهز للإنتاج للسوق السعودي/الخليجي في SMB و Mid‑market بكفاءة تضاهي الأنظمة التجارية بتكلفة ترخيص صفرية.

---

_آخر تحديث: 21 أبريل 2026_
