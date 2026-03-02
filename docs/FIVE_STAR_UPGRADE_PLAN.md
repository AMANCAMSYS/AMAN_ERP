# خطة ترقية AMAN ERP إلى ★★★★★

> **التاريخ:** 1 مارس 2026
> **الهدف:** رفع جميع الفئات العشرين إلى تقييم ★★★★★
> **الحالة الحالية:** ✅ 20 من 20 فئة — جميع المراحل A + B + C مكتملة
> **آخر تحديث:** 1 مارس 2026
> **آخر تدقيق تكامل:** 1 مارس 2026

---

## الوضع الراهن (بعد إكمال المراحل A + B + C)

| الفئة | التقييم | التكامل BE↔FE↔DB | الحالة |
|-------|---------|-------------------|--------|
| 🔐 الأمان والمصادقة | ⭐⭐⭐⭐⭐ | ✅ 15+ endpoint ↔ FE methods ↔ صفحة SecurityEvents | ✅ مكتمل (B1) |
| 🏢 الشركات والفروع | ⭐⭐⭐⭐⭐ | ✅ endpoints modules + sidebar ديناميكي | ✅ مكتمل (B2) |
| 👥 الأدوار والصلاحيات | ⭐⭐⭐⭐⭐ | ✅ مكتمل | ✅ |
| 📊 المحاسبة العامة | ⭐⭐⭐⭐⭐ | ✅ 45+ endpoints + intercompany + revenue recognition | ✅ |
| 💰 الخزينة والبنوك | ⭐⭐⭐⭐⭐ | ✅ مكتمل | ✅ |
| 🧾 الشيكات | ⭐⭐⭐⭐⭐ | ✅ 16+ endpoint + check_status_log | ✅ مكتمل (B3) |
| 📦 المخزون | ⭐⭐⭐⭐⭐ | ✅ مكتمل | ✅ |
| 🛒 المبيعات | ⭐⭐⭐⭐⭐ | ✅ مكتمل | ✅ |
| 🛍️ المشتريات | ⭐⭐⭐⭐⭐ | ✅ مكتمل | ✅ |
| 👥 الموارد البشرية | ⭐⭐⭐⭐⭐ | ✅ مكتمل | ✅ |
| 🏭 التصنيع | ⭐⭐⭐⭐⭐ | ✅ 52+ endpoint + OEE + CapacityPlanning | ✅ مكتمل (B4) |
| 📐 المشاريع | ⭐⭐⭐⭐⭐ | ✅ 46+ endpoint + ProjectRisks + TaskDeps | ✅ مكتمل (B5) |
| 💵 الضرائب (VAT/ZATCA) | ⭐⭐⭐⭐⭐ | ✅ مكتمل | ✅ |
| 🏢 الأصول الثابتة | ⭐⭐⭐⭐⭐ | ✅ 31+ endpoint + IFRS 16 + IAS 36 + قيود محاسبية | ✅ مكتمل (B6) |
| 🖥️ نقطة البيع (POS) | ⭐⭐⭐⭐⭐ | ✅ 34+ endpoint + PWA manifest/config | ✅ مكتمل (B7) |
| 📞 CRM | ⭐⭐⭐⭐⭐ | ✅ 46 endpoint ↔ 46 FE method | ✅ |
| 📊 التقارير | ⭐⭐⭐⭐⭐ | ✅ 47+ endpoint + KPIDashboard | ✅ مكتمل (B8) |
| ⚙️ الإعدادات | ⭐⭐⭐⭐⭐ | ✅ مكتمل | ✅ |
| 💳 المصاريف | ⭐⭐⭐⭐⭐ | ✅ 15+ endpoint + ExpensePolicies + CRUD سياسات | ✅ مكتمل (C1) |
| 📝 العقود | ⭐⭐⭐⭐⭐ | ✅ 12+ endpoint + ContractAmendments + KPIs | ✅ مكتمل (C2) |

---

## ✅ المرحلة A — إصلاح الفجوات الحالية (مكتملة)

| الخطوة | الوصف | الحالة |
|--------|-------|--------|
| A1 | إصلاح جداول `marketing_campaigns` + `crm_knowledge_base` في database.py | ✅ مكتمل |
| A2 | إنشاء `backend/routers/finance/intercompany.py` (9 endpoints) | ✅ مكتمل |
| A3 | إنشاء `backend/routers/finance/advanced_workflow.py` (6 endpoints) | ✅ مكتمل |
| A4 | تحديث `finance/__init__.py` — تسجيل 3 routers جديدة | ✅ مكتمل |
| A5 | إنشاء 6 صفحات CRM | ✅ مكتمل |
| A6 | إنشاء 2 صفحة محاسبية | ✅ مكتمل |
| A7 | ربط 8 routes جديدة في App.jsx | ✅ مكتمل |
| A8 | إضافة ~80 مفتاح ترجمة | ✅ مكتمل |
| A9 | حفظ الخطة في docs/ | ✅ مكتمل |

---

## ✅ المرحلة B — ترقية ★★★★½ إلى ★★★★★ (مكتملة)

### B1 · الأمان 🔐 ✅
| العنصر | الحالة |
|--------|--------|
| 2FA + سياسة كلمات مرور + جلسات | ✅ موجود سابقاً |
| جدول `security_events` + `login_attempts` في DB | ✅ تم إنشاؤه |
| Backend endpoints: listSecurityEvents, getSecurityEventsSummary, listLoginAttempts, getBlockedIPs | ✅ مكتمل |
| Frontend service methods في security.js | ✅ مكتمل |
| صفحة SecurityEvents.jsx (Admin/SecurityEvents) | ✅ تم إنشاؤها |
| Route `/admin/security-events` في App.jsx | ✅ مكتمل |
| تصدير securityAPI في api.js | ✅ مكتمل |
| ترجمة ar/en | ✅ مكتمل |

### B2 · الشركات والفروع 🏢 ✅
| العنصر | الحالة |
|--------|--------|
| Backend endpoints: getEnabledModules, updateEnabledModules | ✅ مكتمل |
| عمود `enabled_modules` (JSONB) + `industry_template` في company_settings | ✅ تم إنشاؤه |
| Frontend service methods في companies.js | ✅ مكتمل |
| Sidebar ديناميكي: `isModuleEnabled()` | ✅ موجود ومفعّل |

### B3 · الشيكات 🧾 ✅
| العنصر | الحالة |
|--------|--------|
| جدول `check_status_log` في DB | ✅ تم إنشاؤه |
| Backend endpoints: getCheckStatusLog, getCheckStatusSummary | ✅ مكتمل |
| Frontend service methods في checks.js | ✅ مكتمل |

### B4 · التصنيع 🏭 ✅
| العنصر | الحالة |
|--------|--------|
| جدول `capacity_plans` في DB | ✅ تم إنشاؤه |
| Backend endpoints: calculateOEE, listCapacityPlans, createCapacityPlan, updateCapacityPlan | ✅ مكتمل |
| Frontend service methods في manufacturing.js | ✅ مكتمل |
| صفحة CapacityPlanning.jsx (Manufacturing/CapacityPlanning) | ✅ تم إنشاؤها |
| Route `/manufacturing/capacity` في App.jsx | ✅ مكتمل |
| معادلة OEE: Availability × Performance × Quality | ✅ مع معايير world-class |

### B5 · المشاريع 📐 ✅
| العنصر | الحالة |
|--------|--------|
| جداول `project_risks` + `task_dependencies` في DB | ✅ تم إنشاؤها |
| Backend endpoints: Risks CRUD (4) + Dependencies CRUD (3) | ✅ مكتمل |
| Frontend service methods في projects.js (7 methods جديدة) | ✅ مكتمل |
| صفحة ProjectRisks.jsx (Projects/ProjectRisks) | ✅ تم إنشاؤها |
| Route `/projects/risks` في App.jsx | ✅ مكتمل |
| مصفوفة مخاطر: احتمالية × تأثير + ترميز لوني | ✅ مكتمل |
| أنواع تبعيات: FS, SS, FF, SF + lag days | ✅ مكتمل |

### B6 · الأصول الثابتة 🏢 ✅
| العنصر | الحالة |
|--------|--------|
| جداول `lease_contracts` + `asset_impairments` في DB | ✅ تم إنشاؤها |
| IFRS 16: إنشاء عقد + PV حساب + جدول استهلاك | ✅ مكتمل |
| IFRS 16 قيد محاسبي تلقائي: Dr. ROU Asset (1600) / Cr. Lease Liability (2300) | ✅ مكتمل |
| IAS 36: اختبار انخفاض القيمة + recoverable amount = MAX(FV-costs, VIU) | ✅ مكتمل |
| IAS 36 قيد محاسبي تلقائي: Dr. Impairment Loss (6800) / Cr. Accumulated Impairment (1699) | ✅ مكتمل |
| صفحة LeaseContracts.jsx (Assets/LeaseContracts) | ✅ تم إنشاؤها |
| صفحة ImpairmentTest.jsx (Assets/ImpairmentTest) | ✅ تم إنشاؤها |
| Routes `/assets/leases` + `/assets/impairment` في App.jsx | ✅ مكتمل |

### B7 · نقطة البيع POS 🖥️ ✅
| العنصر | الحالة |
|--------|--------|
| Backend endpoints: getPWAManifest, getPWAConfig | ✅ مكتمل |
| Frontend service methods في pos.js | ✅ مكتمل |

### B8 · التقارير 📊 ✅
| العنصر | الحالة |
|--------|--------|
| Backend endpoint: getKPIDashboard (7 مؤشرات) | ✅ مكتمل |
| Frontend service method في reports.js | ✅ مكتمل |
| صفحة KPIDashboard.jsx (Reports/KPIDashboard) | ✅ تم إنشاؤها |
| Route `/reports/kpi` في App.jsx | ✅ مكتمل |
| نسب مالية: صافي الدخل، هامش الربح، نسبة التداول، دوران الذمم | ✅ مكتمل |
| مرجعية محاسبية: IFRS 15, IAS 1, IFRS 9, IAS 37, IAS 7, IAS 2, IAS 19, IFRS 16 | ✅ مكتمل |

---

## ✅ المرحلة C — ترقية ★★★½ إلى ★★★★★ (مكتملة)

### C1 · المصاريف 💳 ✅
| العنصر | الحالة |
|--------|--------|
| جدول `expense_policies` في DB | ✅ تم إنشاؤه |
| Backend endpoints: Policies CRUD (5) + validatePolicy | ✅ مكتمل |
| Frontend service methods في expenses.js (5 methods جديدة) | ✅ مكتمل |
| صفحة ExpensePolicies.jsx (Expenses/ExpensePolicies) | ✅ تم إنشاؤها |
| Route `/expenses/policies` في App.jsx | ✅ مكتمل |
| حدود: يومي/شهري/سنوي + اعتماد تلقائي + إيصال مطلوب | ✅ مكتمل |

### C2 · العقود 📝 ✅
| العنصر | الحالة |
|--------|--------|
| جدول `contract_amendments` في DB | ✅ تم إنشاؤه |
| Backend endpoints: Amendments CRUD + getContractKPIs | ✅ مكتمل |
| Frontend service methods في contracts.js (3 methods جديدة) | ✅ مكتمل |
| صفحة ContractAmendments.jsx (Sales/ContractAmendments) | ✅ تم إنشاؤها |
| Routes `/sales/contract-amendments` + `/sales/contracts/:id/amendments` في App.jsx | ✅ مكتمل |
| أنواع التعديل: نطاق، سعر، تمديد، تقليص، بند، طرف، إنهاء | ✅ مكتمل |
| KPIs: استخدام %, أيام متبقية, فواتير, معلقات, هامش ربح | ✅ مكتمل |
| الأثر المحاسبي: IAS 8 + IFRS 15.18 + مخصصات غرامات | ✅ موثق |

---

## ملخص التكامل المحاسبي

### القيود المحاسبية التلقائية المُنشأة

| العملية | المعيار | القيد |
|---------|---------|-------|
| **إنشاء عقد إيجار** | IFRS 16 | Dr. ROU Asset (1600) / Cr. Lease Liability (2300) |
| **انخفاض قيمة أصل** | IAS 36 | Dr. Impairment Loss (6800) / Cr. Accumulated Impairment (1699) |
| **استبعاد أصل** | IAS 16 | Dr. Cash + Acc.Dep / Cr. Fixed Asset ± Gain/Loss |
| **إعادة تقييم** | IAS 16 | Dr. Fixed Asset / Cr. Revaluation Surplus (أو العكس) |
| **إنشاء شيك** | — | Dr. Checks Under Collection (1205) / Cr. AR (1200) |
| **تحصيل شيك** | — | Dr. Bank / Cr. Checks Under Collection |

### الصفحات الجديدة المُنشأة (8 صفحات)

| الصفحة | المسار | الوصف |
|--------|--------|-------|
| SecurityEvents.jsx | `/admin/security-events` | سجل أحداث الأمان + محاولات دخول + IPs محظورة |
| ExpensePolicies.jsx | `/expenses/policies` | إدارة سياسات المصروفات + حدود + اعتماد تلقائي |
| LeaseContracts.jsx | `/assets/leases` | عقود إيجار IFRS 16 + جدول استهلاك + PV |
| ImpairmentTest.jsx | `/assets/impairment` | اختبار انخفاض القيمة IAS 36 + قيد تلقائي |
| ProjectRisks.jsx | `/projects/risks` | سجل مخاطر (احتمالية × تأثير) + تبعيات مهام |
| CapacityPlanning.jsx | `/manufacturing/capacity` | OEE + خطط سعة إنتاجية |
| ContractAmendments.jsx | `/sales/contract-amendments` | تعديلات العقود + KPIs |
| KPIDashboard.jsx | `/reports/kpi` | مؤشرات أداء مالية + نسب محاسبية |

### الجداول الجديدة في قاعدة البيانات (10 جداول)

| الجدول | الوصف |
|--------|-------|
| security_events | أحداث أمنية (نوع، خطورة، IP، مستخدم) |
| login_attempts | محاولات دخول (ناجح/فاشل) |
| check_status_log | سجل تغيير حالة الشيكات |
| capacity_plans | خطط السعة الإنتاجية |
| project_risks | مخاطر المشاريع (احتمالية × تأثير) |
| task_dependencies | تبعيات المهام (FS, SS, FF, SF) |
| lease_contracts | عقود إيجار IFRS 16 |
| asset_impairments | اختبارات انخفاض قيمة IAS 36 |
| expense_policies | سياسات المصروفات |
| contract_amendments | تعديلات العقود |

---

## المرحلة D — ميزات تنافسية متقدمة (التالي)

> بعد اكتمال A + B + C ✅

| الميزة | الوصف | الأولوية |
|--------|-------|---------|
| **محرك سير عمل مرئي** | Drag & Drop Workflow Designer | عالية |
| **بوابة العملاء** | عرض فواتير + دفع أونلاين + تذاكر | عالية |
| **API متقدم** | OAuth2 + versioning + Rate limiting | متوسطة |
| **OCR للمصاريف** | استخراج بيانات الفاتورة تلقائياً | متوسطة |
| **مطابقة بطاقات** | استيراد كشف + مطابقة تلقائية | متوسطة |

---

## المرحلة E — تكاملات خارجية (آخر مرحلة)

| التكامل | الوصف |
|---------|-------|
| 📱 تطبيق جوال | React Native أو PWA |
| 🛒 تجارة إلكترونية | Salla / Zid / WooCommerce |
| 🤖 ذكاء اصطناعي | تنبؤ مبيعات + توصيات مخزون |
| 💳 بوابات دفع | Moyasar + Tap Payments |
| 💬 WhatsApp | فواتير + تنبيهات |
| 🖥️ أجهزة POS | طابعات + باركود |
| ⌚ حضور وانصراف | بصمة + RFID |

---

## ترتيب التنفيذ

```
A (فجوات حالية) ✅ مكتمل
├── A1-A9: جميعها مكتملة

تدقيق التكامل ✅ مكتمل
├── إصلاح 9 مسارات API + 10 methods مفقودة
└── تحقق: 20 فئة — كل الـ endpoints متطابقة مع FE methods

B (★★★★½ → ★★★★★) ✅ مكتمل
├── B1: الأمان — security_events + brute force + صفحة ✅
├── B2: الشركات — sidebar ديناميكي + modules endpoints ✅
├── B3: الشيكات — check_status_log + endpoints ✅
├── B4: التصنيع — OEE + capacity planning + صفحة ✅
├── B5: المشاريع — project_risks + task dependencies + صفحة ✅
├── B6: الأصول — IFRS 16 leases + IAS 36 impairment + صفحتين + قيود محاسبية ✅
├── B7: POS — PWA manifest/config ✅
└── B8: التقارير — KPI Dashboard + نسب مالية + صفحة ✅

C (★★★½ → ★★★★★) ✅ مكتمل
├── C1: المصاريف — سياسات + CRUD + صفحة ✅
└── C2: العقود — ملحقات + KPIs + صفحة ✅

D (تنافسي) — التالي
└── Workflow Builder + Customer Portal + API + OCR

E (تكاملات — آخراً)
└── جوال + إلكترونية + ذكاء اصطناعي + أجهزة
```
