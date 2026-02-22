# 📋 قائمة المهام الشاملة - نظام أمان ERP

> **آخر تحديث:** 21 فبراير 2026  
> **الحالة:** قيد التنفيذ (المرحلة 9 + 10 جارية)  
> **عدد المهام:** 150+ مهمة (تم إنجاز 115+)

---

## 🔴 المرحلة 1: إصلاح المشاكل الحرجة (أولوية قصوى)
**المدة المقدرة:** 2-3 أسابيع

### 1.1 إصلاحات قاعدة البيانات الحرجة ✅

- [x] **[DB-001]** إصلاح تكرار جدول `budgets` - توحيد التعريف وحذف التكرار ✅
- [x] **[DB-002]** إصلاح تكرار جدول `fiscal_periods` - توحيد التعريف ✅
- [x] **[DB-003]** إصلاح تكرار جدول `payroll_periods` - توحيد التعريف ✅
- [x] **[DB-004]** إصلاح تكرار جدول `payroll_entries` - توحيد التعريف ✅
- [x] **[DB-005]** إصلاح `acc_map_acc_depr` - إنشاء حساب الإهلاك المتراكم الصحيح (1207) ✅
- [x] **[DB-006]** إصلاح `acc_map_asset_loss` - إنشاء حسابات 55 و 5501 لخسائر الأصول ✅
- [x] **[DB-007]** نقل ضريبة المدخلات (VAT-IN) من الخصوم إلى الأصول المتداولة (حساب 1107) ✅
- [x] **[DB-008]** إضافة Foreign Key Constraints لجدول `pos_sessions` ✅
- [x] **[DB-009]** إضافة Foreign Key Constraints لجدول `pos_orders` ✅
- [x] **[DB-010]** إضافة Foreign Key Constraints لجدول `pos_order_lines` ✅
- [x] **[DB-011]** إضافة Foreign Key Constraints لجدول `pos_returns` ✅
- [x] **[DB-012]** إصلاح قيمة `retention` - تم التحقق: غير موجودة في الكود الحالي ✅ (N/A)
- [x] **[DB-013]** إضافة 25+ فهرس مركب للاستعلامات الشائعة ✅
- [x] **[DB-014]** إضافة `updated_at` trigger تلقائي لـ 25 جدول ✅
- [x] **[DB-015]** إنشاء فهرس مركزي للمستخدمين `system_user_index` + تحسين تسجيل الدخول O(1) ✅

> 📝 **سكربت الترحيل:** `backend/migrations/migrate_db_fixes_v1.py`  
> لتطبيق الإصلاحات على قواعد البيانات الموجودة: `cd backend && python -m migrations.migrate_db_fixes_v1`

### 1.2 إصلاحات الأمان الحرجة ✅

- [x] **[SEC-001]** إزالة fallback password للـ admin من كود الإنتاج ✅
- [x] **[SEC-002]** تشفير كلمات المرور المخزنة في قاعدة البيانات (bcrypt) ✅ (موجود مسبقاً)
- [x] **[SEC-003]** تعزيز rate limiting لـ login endpoint (IP + username tracking) ✅
- [x] **[SEC-004]** إضافة تحذير أمني عند بدء التشغيل إذا كان SECRET_KEY ضعيف ✅
- [x] **[SEC-005]** إضافة الصلاحية المفقودة `audit.manage` + 10 صلاحيات أخرى مفقودة ✅
- [x] **[SEC-006]** إضافة الصلاحية المفقودة `admin.branches.manage` ✅
- [x] **[SEC-007]** حماية 55 endpoint غير محمي بصلاحيات `require_permission` ✅
- [x] **[SEC-008]** تطبيق التحكم في الوصول على مستوى الفروع `validate_branch_access` في كافة المودولات ✅
  - [x] الأصول موازنة (Assets & Budgets)
  - [x] نقاط البيع (POS)
  - [x] الشيكات وأوراق القبض/الدفع (Checks & Notes)
  - [x] القيود المحاسبية (Journal Entries)

### 1.3 إصلاحات الواجهة ✅

- [x] **[UI-001]** إصلاح الروابط المكسورة في `AccountingHome.jsx` (`/accounting/sales-invoices`) ✅
- [x] **[UI-002]** إصلاح الروابط المكسورة في `AccountingHome.jsx` (`/accounting/vouchers`) ✅
- [x] **[UI-003]** حذف المكونات الميتة (Coming Soon) من `Pages.jsx` ✅
- [x] **[UI-004]** إضافة الترجمات المفقودة في ملفات `ar.json` و `en.json` ✅
- [x] **[UI-005]** إضافة pagination للصفحات التي تفتقدها ✅

### 1.4 إصلاحات البنية التقنية

- [x] **[ARCH-001]** تقسيم ملف `routers/inventory.py` (2,754 سطر) إلى ملفات أصغر ✅
- [x] **[ARCH-002]** تقسيم ملف `routers/sales.py` إلى ملفات أصغر ✅
- [x] **[ARCH-003]** نقل Schemas من ملفات routers إلى مجلد `schemas/` مخصص ✅
- [x] **[ARCH-004]** توحيد نموذج Customers/Suppliers (حذف التكرار مع Parties) ✅
- [x] **[ARCH-005]** توحيد نموذج المدفوعات (5 جداول → نموذج موحد) ✅
- [x] **[ARCH-006]** توحيد `bank_accounts` و `treasury_accounts` ✅

---

## 🔴 المرحلة 2: الميزات المحاسبية الأساسية (حرجة)
**المدة المقدرة:** 1-2 شهر

### 2.1 المحاسبة المالية

- [x] **[ACC-001]** إقفال نهاية السنة المالية (Year-End Closing) ✅
  - [x] واجهة إقفال السنة
  - [x] ترحيل الأرباح/الخسائر إلى حقوق الملكية
  - [x] منع التعديل على السنوات المقفلة
  - [x] إعادة فتح السنة (Reopen Year)
- [x] **[ACC-002]** مسودة القيود اليومية (Draft Journal Entries) ✅
  - [x] حالة "مسودة" للقيود
  - [x] workflow اعتماد القيود
  - [x] منع ترحيل المسودات إلى GL
- [x] **[ACC-003]** القيود المتكررة (Recurring Journal Entries) ✅
  - [x] إنشاء قالب قيد متكرر
  - [x] جدولة (يومي/أسبوعي/شهري/سنوي)
  - [x] توليد تلقائي حسب الجدول
- [x] **[ACC-004]** تقارير مقارنة الفترات ✅
  - [x] مقارنة سنة بسنة
  - [x] مقارنة ربع بربع
  - [x] مقارنة شهر بشهر
- [x] **[ACC-005]** تتبع الأرصدة الافتتاحية ✅
  - [x] واجهة إدخال أرصدة افتتاحية
  - [x] تقرير الأرصدة الافتتاحية
- [x] **[ACC-006]** قيود الإقفال التلقائي (Closing Entries) ✅
  - [x] إقفال الإيرادات والمصاريف تلقائياً
  - [x] ترحيل إلى ملخص الدخل

### 2.2 المبيعات والمشتريات

- [x] **[INV-001]** إشعار دائن - Credit Note (مبيعات)
  - [x] جدول قاعدة بيانات
  - [x] API endpoints (CRUD)
  - [x] واجهة مستخدم
  - [x] قيود GL تلقائية
  - [x] تقارير
- [x] **[INV-002]** إشعار مدين - Debit Note (مبيعات)
  - [x] جدول قاعدة بيانات
  - [x] API endpoints (CRUD)
  - [x] واجهة مستخدم
  - [x] قيود GL تلقائية
- [x] **[INV-003]** إشعار دائن - Credit Note (مشتريات)
  - [x] نفس خطوات INV-001
- [x] **[INV-004]** إشعار مدين - Debit Note (مشتريات)
  - [x] نفس خطوات INV-002

### 2.3 الخزينة والبنوك

- [x] **[TRS-001]** إدارة الشيكات - تحت التحصيل
  - [x] جدول `checks_receivable`
  - [x] حالات (معلق/محصل/مرتجع)
  - [x] workflow التحصيل
  - [x] تسجيل الشيك المرتجع
- [x] **[TRS-002]** إدارة الشيكات - تحت الدفع
  - [x] جدول `checks_payable`
  - [x] تتبع تواريخ الاستحقاق
  - [x] إشعارات الاستحقاق
- [x] **[TRS-003]** استيراد كشف البنك (CSV/Excel)
  - [x] رفع ملف كشف حساب
  - [x] Parser لصيغات البنوك الشائعة
  - [x] معاينة قبل الاستيراد
  - [x] استيراد وربط بالحركات
- [x] **[TRS-004]** المطابقة التلقائية للبنك
  - [x] مطابقة تلقائية بناءً على المبلغ والتاريخ
  - [x] قواعد مطابقة قابلة للتخصيص
- [x] **[TRS-005]** أوراق القبض والدفع
  - [x] جدول قاعدة بيانات
  - [x] تتبع الاستحقاقات
  - [x] تنبيهات

---

## 🔴 المرحلة 3: المخزون المتقدم (حرج) ✅
**المدة المقدرة:** 2-3 أشهر  
**الحالة:** مكتمل - 13 فبراير 2026

### 3.1 التتبع والجودة ✅

- [x] **[INV-101]** أرقام الدفعات (Batch Numbers) ✅
  - [x] جدول `product_batches` + `batch_serial_movements`
  - [x] ربط مع حركات المخزون
  - [x] تتبع كامل للدفعات
  - [x] تقرير حركة الدفعة
  - [x] FEFO (First Expired First Out)
  - [x] واجهة BatchList.jsx مع فلترة وعرض FEFO
- [x] **[INV-102]** الأرقام التسلسلية (Serial Numbers) ✅
  - [x] جدول `product_serials`
  - [x] رقم تسلسلي فريد لكل وحدة
  - [x] تتبع كامل من الشراء للبيع
  - [x] تقرير تاريخ المنتج التسلسلي
  - [x] واجهة SerialList.jsx مع bulk creation وquick lookup
- [x] **[INV-103]** تاريخ الصلاحية (Expiry Date) ✅
  - [x] حقل expiry_date في الدفعات
  - [x] تنبيهات المنتجات قريبة الانتهاء (30/60/90 يوم)
  - [x] منع بيع منتجات منتهية (validation في API)
  - [x] تقرير المنتجات منتهية/قريبة الانتهاء
  - [x] سياسة FEFO مدمجة في batch listing
- [x] **[INV-104]** مراقبة الجودة (Quality Control) ✅
  - [x] جدول `quality_inspections` + `quality_inspection_criteria`
  - [x] فحص عند الاستلام (GRN)
  - [x] فحص قبل الشحن (outgoing/in_process/random)
  - [x] حالات (pending/in_progress/pass/fail/conditional)
  - [x] أسباب الرفض
  - [x] واجهة QualityInspections.jsx مع dynamic criteria

### 3.2 المخزون المتقدم ✅

- [x] **[INV-105]** الجرد الدوري (Cycle Count) ✅
  - [x] جدول `cycle_counts` + `cycle_count_items`
  - [x] جدولة الجرد (full/partial/random)
  - [x] تعيين منتجات للجرد
  - [x] إدخال العد الفعلي
  - [x] حساب الفروقات تلقائياً
  - [x] تسوية تلقائية عند completion
  - [x] واجهة CycleCounts.jsx مع inline editing
- [x] **[INV-106]** إدارة الأبعاد (Product Variants) ✅
  - [x] جدول `product_attributes` + `product_attribute_values`
  - [x] جدول `product_variants` + `product_variant_attributes`
  - [x] إنشاء variants مع attributes
  - [x] أسعار منفصلة لكل متغير (cost/selling)
  - [x] SKU وbarcode منفصل للمتغيرات
  - [x] API endpoints: list/create/delete variants + attributes
- [x] **[INV-107]** إدارة المواقع داخل المستودع (Bin Locations) ✅
  - [x] جدول `bin_locations` + `bin_inventory`
  - [x] تعيين موقع لكل منتج (zone/aisle/rack/shelf/position)
  - [x] حركات بين المواقع (update bin inventory)
  - [x] تقرير المخزون حسب الموقع
  - [x] API endpoints: list/get/create/update bins + inventory
- [x] **[INV-108]** تجميع/تفكيك المنتجات (Kits/Bundles) ✅
  - [x] جدول `product_kits` + `product_kit_items`
  - [x] تعريف المنتجات المكونة (components)
  - [x] أنواع kits (fixed/variable/subscription)
  - [x] حساب total cost من المكونات
  - [x] API endpoints: list/get/create/delete kits + items
- [x] **[INV-109]** سياسات FIFO/LIFO ✅
  - [x] endpoint لعرض costing policies (FIFO/LIFO/WAC/Specific ID)
  - [x] إعدادات per-warehouse WAC وglobal WAC
  - [x] دعم طرق التكلفة المتعددة
- [x] **[INV-110]** كشف حساب المنتج ✅
  - [x] تقرير حركات منتج معين (product ledger)
  - [x] رصيد افتتاحي ونهائي (running balance)
  - [x] تفاصيل كل حركة (qty_in/qty_out/running_balance)
  - [x] فلترة حسب warehouse وdate range

> 📝 **الملفات المُنشأة:**
> - `backend/migrations/migrate_advanced_inventory.py` - Phase 1 (7 tables + 5 columns)
> - `backend/migrations/migrate_advanced_inventory_phase2.py` - Phase 2 (8 tables + 2 columns)
> - `backend/routers/inventory/batches.py` - Phase 1 router (71 routes)
> - `backend/routers/inventory/advanced.py` - Phase 2 router (12 routes)
> - `frontend/src/pages/Stock/BatchList.jsx` - Batch management UI
> - `frontend/src/pages/Stock/SerialList.jsx` - Serial tracking UI
> - `frontend/src/pages/Stock/QualityInspections.jsx` - Quality control UI
> - `frontend/src/pages/Stock/CycleCounts.jsx` - Cycle count UI
> - إجمالي: **15 جدول جديد + 83 inventory route**

---

## ✅ المرحلة 4: الموارد البشرية المتقدمة (مهم)
**المدة المقدرة:** 2-3 أشهر
**الحالة:** ✅ تم إنشاء الباكند (11 جدول + 35 endpoint) - بانتظار واجهات المستخدم

### 4.1 الرواتب المتقدمة

- [x] **[HR-001]** هيكل الرواتب المرن (Salary Structure) ✅
  - [x] جدول `salary_structures`
  - [x] مكونات الراتب (أساسي/بدلات/استقطاعات)
  - [x] صيغ حساب مخصصة
  - [x] ربط بالموظفين
  - [x] نماذج جاهزة (إداري/مبيعات/عمال)
- [x] **[HR-002]** العلاوات والاستقطاعات المتقدمة ✅
  - [x] جدول `salary_components`
  - [x] أنواع (ثابت/نسبة مئوية/صيغة)
  - [x] شروط تطبيق (حضور/غياب/تأخير)
  - [x] علاوات متغيرة (عمولات/حوافز)
- [x] **[HR-003]** العمل الإضافي (Overtime) ✅
  - [x] جدول `overtime_requests`
  - [x] تسجيل ساعات إضافية
  - [x] معدلات مضاعفة (1.5x عادي، 2x عطلة)
  - [x] اعتماد من المدير
  - [x] احتساب تلقائي في الراتب
- [x] **[HR-004]** التأمينات الاجتماعية (GOSI) ✅
  - [x] جدول إعدادات GOSI
  - [x] نسب الاشتراك (موظف/صاحب عمل)
  - [x] حساب تلقائي شهري
  - [x] تقرير GOSI شهري
  - [ ] ملف تصدير للتقديم
  - [x] خطر المهنة (حسب القطاع)
- [~] **[HR-005]** مسيرات الرواتب المطبوعة (Payslip) ✅ باكند — ⬜ فرونتإند
  - [x] قالب مسير راتب (باكند)
  - [ ] طباعة PDF (فرونتإند)
  - [ ] إرسال بالبريد الإلكتروني (فرونتإند)
  - [ ] بوابة موظف لتحميل المسير (فرونتإند)

### 4.2 الحضور والإجازات

- [~] **[HR-006]** رصيد الإجازات المرحّل ✅ باكند — ⬜ فرونتإند
  - [x] ترحيل رصيد نهاية السنة (باكند)
  - [x] حد أقصى للترحيل (باكند)
  - [x] انتهاء صلاحية الرصيد المرحّل (باكند)
  - [ ] واجهة ترحيل الإجازات (فرونتإند)
- [x] **[HR-007]** إدارة المستندات (جواز/إقامة) ✅
  - [x] جدول `employee_documents`
  - [x] أنواع (جواز/إقامة/رخصة/شهادة)
  - [x] تاريخ الإصدار والانتهاء
  - [x] رفع ملفات
  - [x] تنبيهات قبل الانتهاء (90/60/30 يوم)
- [x] **[HR-008]** تقييم الأداء ✅
  - [x] جدول `performance_reviews`
  - [x] معايير التقييم
  - [x] دورات تقييم (ربع سنوية/سنوية)
  - [x] تقييم من المدير
  - [x] تقييم ذاتي
- [x] **[HR-009]** التدريب والتطوير ✅
  - [x] جدول `training_programs`
  - [x] تسجيل الموظفين
  - [x] تتبع الحضور
  - [x] شهادات الإكمال
- [x] **[HR-010]** إدارة المخالفات والجزاءات ✅
  - [x] جدول `employee_violations`
  - [x] أنواع المخالفات
  - [x] إجراءات تأديبية
  - [x] خصم من الراتب
- [x] **[HR-011]** إدارة العهد ✅
  - [x] جدول `employee_custody`
  - [x] أصناف العهد (جوال/لابتوب/سيارة)
  - [x] تسليم واستلام
  - [x] تقرير العهد

### 4.3 التوظيف (اختياري)

- [~] **[HR-012]** التوظيف والاستقطاب ✅ باكند — ⬜ فرونتإند
  - [x] جدول `job_openings` (باكند)
  - [x] نشر إعلان وظيفي (باكند)
  - [x] استقبال السير الذاتية (باكند)
  - [x] مراحل المقابلات (باكند)
  - [x] تقييم المرشحين (باكند)
  - [x] قبول/رفض (باكند)
  - [ ] واجهة التوظيف (فرونتإند)

> 📝 **الملفات المُنشأة:**
> - `backend/database.py` - إضافة 11 جدول HR جديد
> - `backend/schemas/hr_advanced.py` - Pydantic schemas (~300 سطر)
> - `backend/routers/hr_advanced.py` - 35 endpoint (~500 سطر)
> - `backend/main.py` - تسجيل الراوتر
> - إجمالي: **11 جدول جديد + 35 HR Advanced endpoint**

---

## 🟡 المرحلة 5: التصنيع المتقدم (مهم)
**المدة المقدرة:** 2-3 أشهر

### 5.1 البنية الأساسية

- [x] **[MFG-001]** محطات العمل (Work Centers) ✅
  - [x] جدول `work_centers`
  - [x] سعة المحطة (ساعات/يوم)
  - [x] تكلفة الساعة
  - [x] حالة (متاح/مشغول/صيانة)
  - [x] ربط بالموظفين
- [x] **[MFG-002]** مسارات التصنيع (Routing) ✅
  - [x] جدول `manufacturing_routes`
  - [x] خطوات التصنيع (Operations)
  - [x] ترتيب الخطوات
  - [x] محطة العمل لكل خطوة
  - [x] الوقت المقدر لكل خطوة
  - [x] ربط بـ BOM
- [x] **[MFG-003]** BOM متعدد المستويات ✅
  - [x] BOM داخل BOM
  - [x] حساب متطلبات متعدد المستويات
  - [x] تفجير BOM (BOM Explosion) - (مدعوم عبر الهيكلية)

### 5.2 التخطيط

- [x] **[MFG-004]** تخطيط الإنتاج (Production Orders) ✅
  - [x] جدول `production_orders`
  - [x] خطة إنتاج (مخطط/قيد التنفيذ/مكتمل)
  - [x] توليد أوامر إنتاج
  - [x] واجهة `ProductionOrders.jsx`
- [x] **[MFG-005]** MRP - تخطيط متطلبات المواد ✅
  - [x] حساب متطلبات المواد الخام
  - [x] مقارنة بالمخزون الحالي
  - [x] توليد طلبات شراء تلقائية
  - [x] Lead Time للموردين
  - [x] Safety Stock
- [x] **[MFG-006]** جدولة الإنتاج ✅
  - [x] تعيين أوامر لمحطات العمل
  - [x] تحسين الجدولة
  - [x] تجنب الاختناقات

### 5.3 التتبع والجودة

- [x] **[MFG-007]** تتبع وقت الإنتاج (Job Cards) ✅
  - [x] جدول `job_cards`
  - [x] بدء/إيقاف الوقت لكل خطوة
  - [x] تسجيل الموظف المنفذ
  - [x] الوقت الفعلي vs المقدر
- [x] **[MFG-008]** تكاليف العمالة ✅
  - [x] احتساب تكلفة العمالة لكل أمر
  - [x] تكلفة ساعة العامل
  - [x] ربط بالرواتب
- [x] **[MFG-009]** المصاريف العامة (Overhead) ✅
  - [x] توزيع مصاريف التشغيل
  - [x] معدل التحميل
  - [x] احتساب في تكلفة المنتج
- [x] **[MFG-010]** المنتجات الفرعية (By-products) ✅
  - [x] تعريف منتجات فرعية في BOM
  - [x] إضافة تلقائية للمخزون
  - [x] توزيع التكلفة
- [x] **[MFG-011]** صيانة المعدات ✅
  - [x] جدول `equipment`
  - [x] جدول الصيانة الدورية
  - [x] تسجيل الأعطال
  - [x] تكاليف الصيانة

---

## 🟡 المرحلة 6: المشاريع والتقارير (مهم)
**المدة المقدرة:** 1-2 شهر

### 6.1 إدارة المشاريع

- [x] **[PRJ-001]** مخطط جانت (Gantt Chart) ✅
  - [x] مكتبة Gantt (مثل: Frappe Gantt)
  - [x] عرض المهام على الخط الزمني
  - [x] تبعيات المهام
  - [x] النسبة المئوية للإنجاز
- [x] **[PRJ-002]** تتبع الوقت (Timesheet) ✅
  - [x] جدول `timesheets`
  - [x] تسجيل ساعات العمل على المهام
  - [x] تسجيل يومي/أسبوعي
  - [x] اعتماد من مدير المشروع
  - [x] احتساب في التكلفة
- [x] **[PRJ-003]** فوترة المشاريع
  - [x] فوترة حسب الوقت (hourly rate)
  - [x] فوترة حسب المعالم (milestones)
  - [x] فوترة ثابتة (fixed price)
  - [x] توليد فاتورة من المشروع
- [x] **[PRJ-004]** KPIs ومؤشرات الأداء
  - [x] نسبة الإنجاز
  - [x] التكلفة الفعلية vs المقدرة
  - [x] الوقت المستهلك vs المقدر
  - [x] الربحية (صافي الربح وهامش الربح)
  - [x] لوحة مراقبة تخصيص الموارد (Resource Allocation)
- [x] **[PRJ-005]** مستندات المشروع
  - [x] رفع ملفات
  - [x] تصنيف المستندات
  - [x] مشاركة مع الفريق
- [x] **[PRJ-006]** إشعارات المواعيد
  - [x] تنبيه قبل موعد المهمة
  - [x] تنبيه بالمهام المتأخرة
  - [x] تنبيه بانتهاء المشروع

### 6.2 التقارير المتقدمة

- [x] **[RPT-001]** تقارير مقارنة الفترات ✅
  - [x] مقارنة شهر بشهر
  - [x] مقارنة ربع بربع
  - [x] مقارنة سنة بسنة
  - [x] رسوم بيانية للمقارنة
- [x] **[RPT-002]** تخصيص التقارير (Report Builder)
  - [x] واجهة سحب وإفلات
  - [x] اختيار الحقول
  - [x] الفلترة والترتيب
  - [x] حفظ التقارير المخصصة
  - [x] مشاركة التقارير
- [x] **[RPT-003]** تصدير التقارير ✅
  - [x] تصدير PDF
  - [x] تصدير Excel
  - [x] تصدير CSV
  - [x] طباعة مباشرة
- [x] **[RPT-004]** جدولة التقارير ✅
  - [x] إرسال تلقائي (يومي/أسبوعي/شهري)
  - [x] البريد الإلكتروني للمستلمين
  - [x] تصدير تلقائي

---

## 🟡 المرحلة 7: تحسينات النظام (مهم) ✅
**المدة المقدرة:** 2-3 أشهر
**الحالة:** ✅ مكتمل - 16 فبراير 2026

### 7.1 Workflows والاعتمادات ✅

- [x] **[WF-001]** سلسلة اعتمادات متعددة المستويات ✅
  - [x] جدول `approval_workflows`
  - [x] تعريف مراحل الاعتماد
  - [x] شروط الانتقال
  - [x] تعيين المعتمدين
  - [x] إشعارات تلقائية
- [x] **[WF-002]** workflow لأوامر الشراء ✅
  - [x] اعتماد مدير القسم
  - [x] اعتماد المدير المالي (فوق مبلغ معين)
  - [x] اعتماد المدير العام (فوق مبلغ أكبر)
- [x] **[WF-003]** workflow للمصاريف ✅
  - [x] مستويات حسب المبلغ
  - [x] اعتماد متعدد المراحل

### 7.2 الإشعارات ✅

- [x] **[NOT-001]** إشعارات البريد الإلكتروني الفعلية ✅
  - [x] إعداد SMTP
  - [x] قوالب البريد (Email Templates)
  - [x] إشعارات الاعتمادات
  - [x] إشعارات المواعيد
  - [x] إشعارات الانتهاء (إقامات/وثائق)
- [x] **[NOT-002]** إشعارات SMS الفعلية ✅
  - [x] تكامل مع بوابة SMS سعودية
  - [x] إشعارات الموظفين
  - [x] إشعارات العملاء (فواتير/مدفوعات)
  - [x] رموز OTP للمصادقة
- [x] **[NOT-003]** الإشعارات داخل النظام ✅
  - [x] مركز إشعارات
  - [x] أيقونة الجرس مع العدد
  - [x] تصنيف الإشعارات
  - [x] تحديد كمقروء/غير مقروء

### 7.3 الأمان والمصادقة ✅

- [x] **[SEC-101]** المصادقة الثنائية (2FA) ✅
  - [x] TOTP (Google Authenticator)
  - [x] SMS OTP
  - [x] إلزامي للمسؤولين
  - [x] اختياري للمستخدمين
- [x] **[SEC-102]** سجل التغييرات (Audit Trail - تحسين) ✅
  - [x] تسجيل جميع التغييرات
  - [x] قبل/بعد التغيير
  - [x] تفاصيل المستخدم والوقت
  - [x] عرض سجل التغييرات لكل سجل
- [x] **[SEC-103]** سياسات كلمات المرور ✅
  - [x] حد أدنى للطول
  - [x] تعقيد (أحرف/أرقام/رموز)
  - [x] انتهاء الصلاحية (90 يوم)
  - [x] منع إعادة استخدام كلمات قديمة
- [x] **[SEC-104]** جلسات المستخدم ✅
  - [x] عرض الجلسات النشطة
  - [x] إنهاء جلسات أخرى
  - [x] مدة الجلسة قابلة للتعديل
  - [x] تسجيل خروج تلقائي عند عدم النشاط

### 7.4 استيراد/تصدير البيانات ✅

- [x] **[DATA-001]** استيراد البيانات من Excel/CSV ✅
  - [x] قوالب Excel للاستيراد
  - [x] معاينة قبل الاستيراد
  - [x] التحقق من البيانات
  - [x] تقرير الأخطاء
  - [x] استيراد دفعات (chunks)
- [x] **[DATA-002]** تصدير البيانات ✅
  - [x] تصدير أي جدول إلى Excel
  - [x] تصدير إلى CSV
  - [x] تصدير مخصص (اختيار الحقول)
- [x] **[DATA-003]** النسخ الاحتياطي التلقائي (مجدول) ✅
  - [x] جدولة النسخ الاحتياطي (يومي/أسبوعي)
  - [x] رفع إلى S3 أو Google Drive
  - [x] الاحتفاظ بـ N نسخة
  - [x] تشفير النسخ الاحتياطية

### 7.5 الأداء ✅

- [x] **[PERF-001]** تحسين استعلامات قاعدة البيانات ✅
  - [x] مراجعة الاستعلامات البطيئة
  - [x] إضافة فهارس مركبة
  - [x] استخدام JOINs بدلاً من استعلامات متعددة
- [x] **[PERF-002]** Caching ✅
  - [x] Redis للـ cache
  - [x] cache للبيانات المستخدمة بكثرة (Settings)
  - [x] cache لشجرة الحسابات
  - [x] cache للإعدادات
- [x] **[PERF-003]** Pagination للجداول الكبيرة ✅
  - [x] Cursor-based pagination (Limit/Offset)
  - [x] الحد من عدد السجلات المعروضة
- [x] **[PERF-004]** تحسين الواجهة ✅
  - [x] Lazy loading للصور
  - [x] Code splitting
  - [x] تقليل حجم bundle
  - [x] استخدام Virtual scrolling للجداول الطويلة

> 📝 **الملفات المُنشأة:**
> - `backend/routers/approvals.py` - Workflow logic, definitions & actions
> - `backend/services/email_service.py` - SMTP & SMS service with templates
> - `backend/routers/notifications.py` - Updated with Email/SMS support + Settings
> - `backend/routers/security.py` - 2FA, Password Policy, Session Management
> - `backend/routers/data_import.py` - Universal CSV/Excel import/export
> - `backend/database.py` - Updated with 6 new tables + Performance Indexes
> - إجمالي: **6 جداول جديدة + 4 راوترات جديدة + 1 خدمة**

---

## 🟢 المرحلة 8: إكمال الوحدات الأساسية للوصول إلى 100%
**المدة المقدرة:** 3-6 أشهر  
**الحالة:** قيد التنفيذ  
**الهدف:** رفع نسبة اكتمال كل وحدة أساسية إلى 100%

### 8.1 إكمال وحدة التصنيع (Manufacturing) — من 40% إلى 100%

#### 8.1.1 الحسابات المحاسبية للتصنيع

- [x] **[MFG-101]** ربط الحسابات المحاسبية للتصنيع في `company_settings` ✅
  - [x] حساب المواد الخام (Raw Materials) — مفتاح: `acc_map_raw_materials`
  - [x] حساب إنتاج قيد التنفيذ (WIP) — مفتاح: `acc_map_wip`
  - [x] حساب المنتجات التامة (Finished Goods) — مفتاح: `acc_map_finished_goods`
  - [x] حساب العمالة المباشرة (Direct Labor) — مفتاح: `acc_map_labor_cost` *(كان موجود بالفعل)*
  - [x] حساب الأعباء الصناعية (Manufacturing Overhead) — مفتاح: `acc_map_mfg_overhead`
  - [ ] إضافة واجهة إعداد الحسابات في صفحة الإعدادات *(واجهة أمامية)*

> **[x] تم توسيع `AccountingMappingSettings.jsx`**: مبيعات, مشتريات, خزينة, مخزون, تصنيع, موارد بشرية, مشاريع, أصول ثابتة

#### 8.1.2 القيود التلقائية للتصنيع

- [x] **[MFG-102]** قيد إصدار أمر إنتاج (Material Issue) ✅
  - [x] مدين: حساب إنتاج قيد التنفيذ (WIP)
  - [x] دائن: حساب المواد الخام / المخزون
  - [x] تسجيل في `journal_entries` برمز `MFG-START-`
  - [x] خصم الكميات من المخزون تلقائياً + فحص كفاية المواد
- [x] **[MFG-103]** قيد إنهاء أمر إنتاج (Production Complete) ✅
  - [x] مدين: حساب المنتجات التامة
  - [x] دائن: حساب إنتاج قيد التنفيذ (WIP)
  - [x] تسجيل في `journal_entries` برمز `MFG-COMP-`
  - [x] إضافة الكميات المنتجة للمخزون تلقائياً + تحديث تكلفة المنتج WAC
- [x] **[MFG-104]** قيد تكاليف العمالة المباشرة ✅
  - [x] مدين: حساب إنتاج قيد التنفيذ (WIP)
  - [x] دائن: حساب العمالة المباشرة
  - [x] احتساب من ساعات Job Cards × سعر الساعة
- [x] **[MFG-105]** قيد الأعباء الصناعية ✅
  - [x] مدين: حساب إنتاج قيد التنفيذ (WIP)
  - [x] دائن: حساب الأعباء الصناعية
  - [x] معدل تحميل قابل للتعديل (`mfg_overhead_rate` في company_settings)

#### 8.1.3 الوظائف البرمجية للتصنيع

- [x] **[MFG-106]** دالة `calculate_production_cost` في `manufacturing.py` ✅
  - [x] حساب تكلفة المواد المستهلكة (من cost_price مع waste_percentage)
  - [x] حساب تكلفة العمالة المباشرة (ساعات × سعر الساعة)
  - [x] حساب الأعباء الصناعية (معدل تحميل × تكلفة العمالة)
  - [x] إرجاع تفاصيل التكلفة الكلية (مواد + عمالة + أعباء)
  - [x] نقطة API: `GET /manufacturing/orders/cost-estimate`
  - [x] نقطة API: `GET /manufacturing/orders/check-materials`
- [x] **[MFG-107]** دعم BOM المتغيرة (Variable BOM)
  - [x] حقل `is_percentage BOOLEAN` في `bom_components` (مع MIGRATION)
  - [x] عند `is_percentage=true`: الكمية = `quantity%` من كمية الأمر
  - [x] تحديث `check_inventory_sufficiency` ومنطق الاستهلاك
  - [x] `GET /boms/{id}/compute-materials?quantity=X` — يحسب الكميات الفعلية وتحقق المخزون
- [x] **[MFG-108]** فحص جودة أثناء الإنتاج (In-Process QC)
  - [x] جدول `mfg_qc_checks` (مع MIGRATION)
  - [x] `GET /orders/{id}/qc-checks` — فحوصات أمر الإنتاج
  - [x] `POST /orders/{id}/qc-checks` — إضافة فحص (بصلاحية `manufacturing.manage`)
  - [x] `POST /qc-checks/{id}/record-result` — تسجيل النتيجة مع إجراء `failure_action`
  - [x] `GET /qc-checks/failures` — لوحة الفحوصات الفاشلة/المعلقة

#### 8.1.4 تقارير التصنيع

- [x] **[MFG-109]** تقارير التصنيع الشاملة ✅
  - [x] تقرير تكلفة الإنتاج الفعلي vs المقدر (`GET /manufacturing/reports/production-cost`)
  - [x] تقرير كفاءة الإنتاج - أداء مراكز العمل (`GET /manufacturing/reports/work-center-efficiency`)
  - [x] تقرير المواد المستهلكة (`GET /manufacturing/reports/material-consumption`)
  - [x] تقرير ملخص الإنتاج (`GET /manufacturing/reports/production-summary`)
  - [ ] تقرير العمالة المباشرة (Direct Labor Report) — *(مرحلة لاحقة)*

#### 8.1.5 إصلاح الأخطاء والنواقص *(مكتمل)*

- [x] إصلاح خطأ المتغير `order` في `get_production_order` (كان `o`)
- [x] إصلاح `create_route` — كان يرجع آخر عنصر من القائمة بدلاً من العنصر المنشأ
- [x] إصلاح `create_bom` — كان يرجع أول عنصر من القائمة بدلاً من العنصر المنشأ
- [x] إضافة waste_percentage في حساب استهلاك المواد (start و complete)
- [x] إضافة تحديث cost_price بطريقة WAC بعد إنهاء الإنتاج
- [x] إضافة فحص كفاية المواد قبل بدء الإنتاج
- [x] إضافة endpoints: Cancel / Delete / Update Production Orders
- [x] إضافة endpoints: Delete Work Center / Route / BOM
- [x] حذف الملفات الميتة: `manufacturing_part2_content.py` و `schemas/manufacturing.py`
- [x] إضافة 3 مفاتيح ربط مفقودة: `acc_map_inventory_adjustment`, `acc_map_intercompany`, `acc_map_fx_difference`
- [x] إضافة حساب `5503` (تسوية المخزون) و `1111` (حسابات بين الفروع) في شجرة الحسابات

### 8.2 إكمال وحدة المشاريع (Projects) — من 35% إلى 100%

#### 8.2.1 الحسابات المحاسبية للمشاريع

- [x] **[PRJ-101]** ربط الحسابات المحاسبية للمشاريع في `company_settings`
  - [x] المشاريع تستخدم مفاتيح عامة موجودة: `acc_map_sales_rev`, `acc_map_ar`, `acc_map_salaries_exp` (لا داعي لمفاتيح مخصصة)
  - [x] مفتاح `acc_map_project_pl` مدعوم كـ fallback عند إغلاق المشروع
  - [ ] إضافة واجهة إعداد الحسابات في صفحة الإعدادات (Frontend)

> **[x] تم توسيع `AccountingMappingSettings.jsx`**: مبيعات+AR, مشتريات+AP, خزينة+بنك, مخزون, تصنيع (5 حسابات), رواتب, مشاريع, أصول ثابتة

#### 8.2.2 القيود التلقائية للمشاريع

- [x] **[PRJ-102]** قيد تسجيل تكلفة مشروع
  - [x] Dr: حساب المصروفات — Cr: حساب النقدية/الدائنون (كان موجوداً، تم التحقق)
  - [x] ربط بـ project_id وcost_center_id في journal_entries
- [x] **[PRJ-103]** قيد إصدار فاتورة مشروع
  - [x] create_project_invoice ينشئ السجل في invoices وproject_revenues تلقائياً
  - [ ] قيد GL مباشر عند الإصدار (يُسجَّل عند ترحيل الفاتورة من وحدة المبيعات)
- [x] **[PRJ-104]** قيد ربح/خسارة المشروع عند الإغلاق
  - [x] `POST /{project_id}/close` — يقارن إيرادات vs مصاريف
  - [x] قيد GL: PCLOSE-YYYY مع Dr/Cr للإيرادات والأرباح المحولة
  - [x] تحديث status=completed وprogress=100%

#### 8.2.3 الوظائف المفقودة في المشاريع

- [x] **[PRJ-105]** Earned Value Management (EVM)
  - [x] `GET /{project_id}/evm` — يحسب PV, EV, AC
  - [x] SPI = EV/PV, CPI = EV/AC, EAC, ETC, VAC, TCPI
  - [x] تفسير نصي: ahead/behind/on_track + under_budget/over_budget
- [x] **[PRJ-106]** نظام Change Orders (تغيير نطاق المشروع)
  - [x] جدول `project_change_orders` (تم إنشاؤه في DB وعلى الشركات)
  - [x] `POST /{project_id}/change-orders` — إنشاء أمر تغيير
  - [x] `PUT /change-orders/{id}` — تعديل
  - [x] `POST /change-orders/{id}/approve` — موافقة + تعديل الميزانية تلقائياً
  - [x] `GET /{project_id}/change-orders` — قائمة الأوامر
- [x] **[PRJ-107]** أنواع عقود متعددة
  - [x] حقل `contract_type VARCHAR(30)` في جدول projects (مع MIGRATION)
  - [x] قيم: fixed_price, time_and_materials, retainer, milestone
  - [ ] فوترة دورية تلقائية للعقود من نوع Retainer
- [x] **[PRJ-108]** تنبيهات التأخر في الجدول (Schedule Alerts)
  - [x] `GET /projects/alerts/overdue-tasks` — المهام المتأخرة مرتبة حسب درجة التأخر
  - [x] `GET /projects/alerts/over-budget` — المشاريع التي تجاوزت الميزانية + نسبة التجاوز
  - [x] `GET /projects/alerts/dashboard` — لوحة شاملة: متأخرة, تجاوزت ميزانية, أوامر تغيير معلقة, مشاريع قاربت من الانتهاء

#### 8.2.4 تقارير المشاريع

- [x] **[PRJ-109]** تقارير المشاريع الشاملة
  - [x] `GET /reports/profitability` — ربحية جميع المشاريع (Budget vs Actual, Margin%)
  - [x] `GET /reports/variance` — انحرافات التكلفة والجدول الزمني
  - [x] `GET /reports/resource-utilization` — استخدام الموارد وساعات العمل
  - [x] EVM داخل `GET /{project_id}/evm` يوفر أداء الجدول والتكلفة

### 8.3 إكمال وحدة التقارير — من 50% إلى 100%

#### 8.3.1 محرك تصدير التقارير

- [x] **[RPT-101]** تصدير PDF احترافي ✅
  - [x] استخدام مكتبة ReportLab أو WeasyPrint
  - [x] تخطيط تقارير احترافي (Header/Footer/Logo)
  - [ ] دعم اللغة العربية (RTL) في PDF
  - [x] قوالب قابلة للتخصيص لكل نوع تقرير
- [x] **[RPT-102]** تصدير Excel متقدم ✅
  - [x] تنسيق الخلايا والألوان
  - [ ] رسوم بيانية مدمجة (Charts)
  - [x] أوراق عمل متعددة (Multi-sheet)
  - [x] صيغ حسابية تلقائية

#### 8.3.2 أنواع التقارير المفقودة

- [x] **[RPT-103]** التقارير المالية المتقدمة ✅
  - [x] تقرير التحليل الأفقي (Horizontal Analysis) — `GET /reports/accounting/horizontal-analysis`
  - [x] تقرير تحليل النسب المالية (Financial Ratios) — `GET /reports/accounting/financial-ratios`
  - [x] تقرير مركز التكلفة (Cost Center Report) — `GET /reports/accounting/cost-center-report`
  - [ ] تقرير الأرباح والخسائر التفصيلي (حسب المنتج / العميل / الفئة)
  - [x] تقرير التدفقات النقدية التفاعلي — `GET /reports/accounting/cashflow/export`
- [x] **[RPT-104]** تقارير المخزون المفقودة ✅
  - [x] تقييم المخزون بالتكلفة المتوسطة — `GET /reports/inventory/valuation`
  - [x] تقرير دوران المخزون (Inventory Turnover) — `GET /reports/inventory/turnover`
  - [x] تقرير المخزون الراكد (Dead Stock) — `GET /reports/inventory/dead-stock`
  - [x] تقرير تكلفة البضاعة المباعة (COGS Report) — `GET /reports/inventory/cogs`
- [x] **[RPT-105]** تقارير المبيعات والمشتريات المفقودة ✅
  - [x] تقرير أداء البائعين (Sales by Cashier) — `GET /reports/sales/by-cashier`
  - [ ] تقرير عمولات المبيعات
  - [x] تقرير المبيعات المستهدفة vs الفعلية — `GET /reports/sales/target-vs-actual`

#### 8.3.3 منشئ التقارير (Report Builder)

- [x] **[RPT-106]** Report Builder — واجهة إنشاء تقارير مخصصة ✅ (كان موجود مسبقاً)
  - [x] اختيار الجداول والحقول بالسحب والإفلات
  - [x] الفلترة والترتيب والتجميع
  - [x] حفظ التقارير المخصصة
  - [ ] مشاركة التقارير مع المستخدمين
  - [ ] جدولة التقارير (يومي/أسبوعي/شهري)

### 8.4 إكمال شجرة الحسابات (COA) — من 50% إلى 100%

#### 8.4.1 الأصول غير الملموسة (Intangible Assets)

- [x] **[COA-001]** إنشاء فئة الأصول غير الملموسة ✅
  - [x] شهرة (Goodwill) — `1301`
  - [x] براءات الاختراع والعلامات التجارية — `1302`
  - [x] حقوق التأليف والنشر — `1303`
  - [x] الإطفاء المتراكم (Accumulated Amortization) — `1304`
  - [x] أصل حق الاستخدام (ROU) لعقود الإيجار — `1305`

#### 8.4.2 حسابات الضرائب الشاملة

- [x] **[COA-002]** إنشاء شجرة حسابات الضرائب ✅
  - [x] ضريبة القيمة المضافة - مخرجات (VAT Output) — `210301` (كان موجود)
  - [x] ضريبة القيمة المضافة - مدخلات (VAT Input) — `1107` (كان موجود)
  - [x] ضريبة القيمة المضافة - مستحقة (VAT Payable) — `2103` (كان موجود)
  - [x] ضريبة القيمة المضافة - مدينة (VAT Receivable) — `1107`
  - [x] ضريبة الاستقطاع (Withholding Tax) — `2108` + `acc_map_withholding_tax`
  - [x] ضريبة الدخل (Income Tax) — `2109` + `acc_map_income_tax`
  - [x] الزكاة (Zakat) — `2111` + `acc_map_zakat`
  - [x] تسوية ضريبة القيمة المضافة — `2112` + `acc_map_vat_settlements`

#### 8.4.3 حسابات المصروفات الشاملة

- [x] **[COA-003]** إنشاء حسابات المصروفات التشغيلية ✅ (معظمها كان موجود + إضافات)
  - [x] إيجار مباني / مصروفات المياه والكهرباء — `5202`/`5203`
  - [x] صيانة وإصلاح / تأمين / اتصالات — `5205`/`5211`/`5204`
  - [x] مصروفات بنكية / إهلاك — `5401`/`53`
- [x] **[COA-004]** إنشاء حسابات المصروفات التسويقية والإدارية ✅
  - [x] إعلان وتسويق / علاقات عامة / عمولات — `5207`/`5218`/`5217`
  - [x] مستلزمات مكتبية / فرق صندوق / مصروفات قانونية / تدقيق — `5213`/`5502`/`5215`/`5216`
- [x] **[COA-005]** إنشاء حسابات الإيرادات الأخرى ✅
  - [x] فوائد محصلة / توزيعات أرباح / ربح بيع أصول / خصومات مكتسبة — `4203`/`4204`/`4205`/`4206`

#### 8.4.4 حسابات الموارد البشرية والمصروفات المسبقة

- [x] **[COA-006]** ربط حسابات HR والمخصصات في `company_settings` ✅
  - [x] بدلات الموظفين — `5219` + `acc_map_allowances`
  - [x] العمل الإضافي — `5220` + `acc_map_overtime`
  - [x] مكافآت نهاية الخدمة — `5221` + `acc_map_termination_benefits`
  - [x] مخصص الإجازات — `2203` + `acc_map_provision_holiday`
  - [x] الإيجار المدفوع مقدماً — `110501` + `acc_map_prepaid_rent`
  - [x] التأمين المدفوع مقدماً — `110502` + `acc_map_prepaid_insurance`
  - [x] المصروفات المستحقة — `2102` + `acc_map_accrued_expenses`
  - [x] مخصص الديون المعدومة — `2204` + `acc_map_provision_doubtful`

### 8.5 إكمال القيود التلقائية المفقودة

- [x] **[GL-001]** قيد COGS التلقائي عند بيع منتج ✅ (كان موجود في sales/invoices.py)
  - [x] مدين: تكلفة البضاعة المباعة (COGS)
  - [x] دائن: المخزون
  - [x] حساب التكلفة بناءً على WAC أو FIFO
  - [x] تفعيل تلقائي عند تأكيد فاتورة المبيعات
- [x] **[GL-002]** قيد بيع أصل ثابت (ربح/خسارة) ✅ (كان موجود في assets.py)
  - [x] مدين: النقدية/المدينون (بسعر البيع)
  - [x] مدين: الإهلاك المتراكم
  - [x] دائن: الأصل الثابت (بالقيمة الأصلية)
  - [x] الفرق → ربح أو خسارة بيع أصل
- [x] **[GL-003]** قيد نقل أصل بين فروع ✅ `POST /assets/{id}/transfer`
  - [x] مدين: حساب الأصول في الفرع المستقبل
  - [x] دائن: حساب الأصول في الفرع المُرسل
  - [x] تسجيل عبر الحساب البيني (`acc_map_intercompany`)
- [x] **[GL-004]** قيد مخصص ديون معدومة ✅ `POST /accounting/provisions/bad-debt`
  - [x] مدين: مصروف ديون معدومة
  - [x] دائن: مخصص الديون المعدومة
- [x] **[GL-005]** قيد مخصص إجازات ✅ `POST /accounting/provisions/leave`
  - [x] مدين: مصروف إجازات
  - [x] دائن: مخصص الإجازات
- [x] **[GL-006]** قيد تسوية العملات الأجنبية ✅ `POST /accounting/fx-revaluation`
  - [x] فروقات إيجابية → ربح تحويل عملة
  - [x] فروقات سلبية → خسارة تحويل عملة
- [x] **[GL-007]** قيد إعادة تقييم أصل ✅ `POST /assets/{id}/revalue`
  - [x] تحديث قيمة الأصل الدفترية
  - [x] تسجيل الزيادة في احتياطي إعادة التقييم (`35 REVAL`)

### 8.6 تنظيف قاعدة البيانات ✅

- [x] **[DB-101]** إزالة الأعمدة Deprecated ✅
  - [x] ترحيل `customer_id` و `supplier_id` → `party_id` في جميع الجداول
  - [x] الجداول المتأثرة: `invoices`, `sales_orders`, `sales_quotations`, `sales_returns`, `purchase_invoices`, `purchase_orders`, `payment_vouchers`
  - [x] تحديث جميع الاستعلامات في الكود
- [x] **[DB-102]** إصلاح References الخاطئة ✅
  - [x] تحديث `pos_orders.customer_id` → `party_id`
  - [x] تحديث `projects.customer_id` → `party_id`
  - [x] إضافة Foreign Keys على الأعمدة المتبقية
- [x] **[DB-103]** تنظيف جداول Legacy ✅
  - [x] نقل بيانات `customers` و `suppliers` إلى `parties` (إذا لم تنقل)
  - [x] إنشاء `customer_view` و `supplier_view` من جدول `parties`
  - [x] الحفاظ على التوافقية مع الكود القديم

> 📝 **سكربت الترحيل:** `backend/migrations/migrate_db_cleanup_phase86.py`

### 8.7 إكمال وحدة الأمان — من 75% إلى 100% ✅

- [x] **[SEC-201]** Token Blacklist ✅
  - [x] جدول `token_blacklist` في قاعدة النظام (DB-backed + in-memory cache)
  - [x] إضافة التوكن للقائمة السوداء عند `logout` (مع hash SHA-256)
  - [x] فحص القائمة السوداء عند كل طلب مُصادق (`is_token_blacklisted`)
  - [x] تنظيف تلقائي للتوكنات المنتهية (background worker كل ساعة)
- [x] **[SEC-202]** تعزيز سياسات كلمات المرور ✅
  - [x] حد أدنى 8 أحرف + أحرف كبيرة وصغيرة + أرقام + رموز (كان موجود)
  - [x] تاريخ انتهاء كلمات المرور (90 يوم) (كان موجود)
  - [x] منع إعادة استخدام آخر 5 كلمات مرور (كان موجود)
  - [x] إشعار قبل انتهاء كلمة المرور بـ 7 أيام — `GET /security/password-expiry`
  - [x] دالة `check_password_expiry_on_login` لفحص الانتهاء عند الدخول
- [x] **[SEC-203]** HTTPS Enforcement ✅
  - [x] فرض HTTPS في بيئة الإنتاج (`HTTPSRedirectMiddleware`)
  - [x] إعادة توجيه HTTP → HTTPS تلقائياً (301 redirect)
  - [x] HSTS Headers + Security Headers (X-Frame-Options, CSP, X-XSS-Protection)
- [x] **[SEC-204]** Input Sanitization شامل ✅
  - [x] `InputSanitizationMiddleware` — كشف XSS في query params + path + body
  - [x] كشف SQL Injection patterns
  - [x] حماية CSRF عبر JWT (لا حاجة لـ CSRF tokens)
  - [x] تسجيل المحاولات المشبوهة في السجل

> 📝 **الملفات:** `utils/security_middleware.py` + تحديثات `routers/auth.py` + `routers/security.py`

### 8.8 إكمال وحدة الأدوار والصلاحيات — من 75% إلى 100% ✅

- [x] **[PERM-001]** صلاحيات على مستوى الحقول (Field-Level Permissions) ✅
  - [x] جدول `user_field_permissions` + `role_field_permissions` (JSONB)
  - [x] `get_field_restrictions()` + `filter_fields()` — فلترة الحقول المحظورة
  - [x] منع `salesperson` من رؤية `cost_price`, `average_cost` (default rules)
  - [x] منع المحاسب من رؤية تفاصيل رواتب الموظفين (default rules)
- [x] **[PERM-002]** صلاحيات على مستوى المستودع (Warehouse-Level Permissions) ✅
  - [x] جدول `user_warehouses` — تحديد مستودعات لكل مستخدم
  - [x] `get_allowed_warehouses()` + `build_warehouse_filter()` — فلترة SQL تلقائية
- [x] **[PERM-003]** صلاحيات على مستوى مركز التكلفة ✅
  - [x] جدول `user_cost_centers` — تحديد مراكز التكلفة لكل مستخدم
  - [x] `get_allowed_cost_centers()` + `build_cost_center_filter()` — فلترة SQL تلقائية
- [x] **[PERM-004]** تسجيل الصلاحيات في Audit Log ✅
  - [x] `_log_permission_denied()` — تسجيل محاولات الوصول المرفوضة تلقائياً
  - [x] `log_permission_change()` — تسجيل تغييرات الصلاحيات
  - [x] الأحداث تُسجل في `audit_logs` مع `resource_type = 'security'`

> 📝 **سكربت الترحيل:** `backend/migrations/migrate_permissions_phase88.py`
> **الملفات:** `utils/permissions.py` (موسّع بالكامل)

### 8.9 لوحة التحكم — تحسينات ✅

- [x] **[DASH-001]** لوحة معلومات قابلة للتخصيص ✅
  - [x] جدول `dashboard_layouts` — حفظ التخطيط والـ widgets (JSONB)
  - [x] API: `GET/POST/PUT/DELETE /dashboard/layouts` — CRUD للتخطيطات
  - [x] دعم إضافة/إزالة/ترتيب/تغيير حجم الـ widgets (x, y, w, h)
  - [x] حفظ تخطيطات متعددة لكل مستخدم
  - [x] `GET /dashboard/widgets/available` — قائمة 13 widget متاح
  - [x] Default widgets عند أول تسجيل دخول
- [x] **[DASH-002]** Widgets إضافية ✅
  - [x] `GET /dashboard/widgets/sales-summary?period=today|week|month|quarter|year`
  - [x] `GET /dashboard/widgets/top-products?period=month&limit=10`
  - [x] `GET /dashboard/widgets/low-stock?limit=10`
  - [x] `GET /dashboard/widgets/pending-tasks` (فواتير، طلبات، اعتمادات، إجازات)
  - [x] `GET /dashboard/widgets/cash-flow?days=30`

> 📝 **الملفات:** `routers/dashboard.py` (موسّع من 436 → 850+ سطر)

### 8.10 نقاط البيع (POS) — تحسينات

> 📝 **الملفات:** `routers/pos.py` (موسّع) + `migrations/migrate_phases_8_10_to_8_15.py`

- [ ] **[POS-001]** وضع عدم الاتصال (Offline Mode)
  - [ ] Service Worker
  - [ ] IndexedDB للتخزين المحلي
  - [ ] مزامنة تلقائية عند الاتصال
  - [ ] قائمة انتظار للمعاملات
- [ ] **[POS-002]** طباعة فاتورة حرارية
  - [ ] تكامل مع طابعات حرارية (ESC/POS)
  - [ ] قوالب طباعة قابلة للتخصيص
  - [ ] طباعة تلقائية بعد البيع
  - [ ] حجم ورق مخصص + دعم شعار الشركة
- [x] **[POS-003]** خصومات وعروض متقدمة ✅ (باكند)
  - [x] خصم نسبة مئوية / خصم قيمة ثابتة
  - [x] عرض اشتر X واحصل على Y
  - [x] خصم على الفئات / كوبونات خصم
  - [x] صلاحية العروض (تاريخ بداية ونهاية)
- [x] **[POS-004]** برنامج ولاء (Loyalty) ✅ (باكند)
  - [x] نقاط لكل عملية شراء
  - [x] استبدال النقاط بخصومات
  - [x] مستويات العملاء (ذهبي/فضي/برونزي)
  - [x] مكافآت خاصة
- [ ] **[POS-005]** شاشة عرض للعميل + فتح/إغلاق درج النقد
  - [ ] عرض المنتجات والأسعار والإجمالي
  - [ ] أمر فتح الدرج وتكامل مع الأجهزة
- [x] **[POS-006]** تقارير الجلسة المفصلة ✅ (باكند)
  - [x] تقرير المبيعات حسب المنتج / الفئة / طرق الدفع
  - [x] تقرير أداء كل بائع (Sales by Cashier)
  - [x] تقرير حركة كل درج نقدي (Drawer Movement)
  - [x] تقرير مقارنة الفترات (Period Comparison)
- [x] **[POS-007]** إدارة الطاولات (Table Management) للمطاعم ✅ (باكند)
  - [x] تخطيط القاعة وترتيب الطاولات
  - [x] حجز الطاولات وتعيين الطلبات
- [x] **[POS-008]** Kitchen Display System (KDS) ✅ (باكند)
  - [x] إرسال الطلبات للمطبخ إلكترونياً
  - [x] تتبع حالة التحضير
  - [x] إشعارات جاهزية الطلب

### 8.11 المشتريات — تحسينات

> 📝 **الملفات:** `routers/purchases.py` (موسّع) + `migrations/migrate_phases_8_10_to_8_15.py`

- [x] **[PUR-001]** طلب عروض أسعار (RFQ) ✅ (باكند)
  - [x] جدول `request_for_quotations`
  - [x] إرسال RFQ لموردين متعددين
  - [x] استقبال ومقارنة العروض
  - [x] تحويل إلى أمر شراء
- [x] **[PUR-002]** تقييم الموردين ✅ (باكند)
  - [x] جدول `supplier_ratings`
  - [x] معايير التقييم (جودة/سعر/توصيل)
  - [x] تقييم بعد كل شراء + تقرير أفضل الموردين
- [x] **[PUR-003]** عقود الشراء وأوامر شراء شاملة (Blanket PO) ✅ (باكند)
  - [x] جدول `purchase_agreements`
  - [x] أسعار وكميات متفق عليها لفترة محددة
  - [x] استدعاءات متعددة (Call-offs) مع تتبع المتبقي

### 8.12 المبيعات — تحسينات

> 📝 **الملفات:** `routers/sales/sales_improvements.py` (جديد) + `routers/sales/__init__.py` (محدّث)

- [x] **[SALES-001]** تحويل عرض السعر لأمر بيع تلقائي ✅ (باكند)
  - [x] زر "تحويل" في عرض السعر
  - [x] نسخ جميع البيانات مع الربط بين السجلين
- [x] **[SALES-002]** تتبع العمولات ✅ (باكند)
  - [x] جدول `sales_commissions`
  - [x] نسبة عمولة لكل مندوب + حساب تلقائي
  - [x] تقرير العمولات + دفع العمولات
- [x] **[SALES-003]** فاتورة جزئية + شحن جزئي ✅ (باكند)
  - [x] تحويل جزء من أمر البيع إلى فاتورة
  - [x] شحن جزء من أمر البيع
  - [x] تتبع الكميات المفوترة والمشحونة
- [x] **[SALES-004]** حد ائتمان ذكي ✅ (باكند)
  - [x] منع تجاوز حد الائتمان تلقائياً
  - [x] إشعار عند الاقتراب + تعليق الفواتير عند التجاوز
- [ ] **[SALES-005]** طباعة فواتير بتنسيقات متعددة
  - [ ] قوالب متعددة (رسمي/مبسط/تجاري)
  - [ ] تخصيص حسب العميل + شعار + ألوان مخصصة

### 8.13 الميزانيات — تحسينات

> 📝 **الملفات:** `routers/budgets.py` (موسّع)

- [x] **[BDG-001]** ميزانيات حسب مركز التكلفة ✅ (باكند)
  - [x] ميزانية منفصلة لكل مركز + مقارنة الفعلي بالميزانية
- [x] **[BDG-002]** ميزانيات متعددة السنوات وربع سنوية ✅ (باكند)
  - [x] ميزانية 3-5 سنوات مع زيادة سنوية (growth rate)
  - [x] تقسيم الميزانية السنوية لأرباع + مقارنة ربع بربع

### 8.14 الأصول الثابتة — تحسينات

> 📝 **الملفات:** `routers/assets.py` (موسّع) + `migrations/migrate_phases_8_10_to_8_15.py`

- [x] **[ASSET-001]** طرق إهلاك إضافية ✅ (باكند)
  - [x] القسط المتناقص (Declining Balance)
  - [x] وحدات الإنتاج (Units of Production)
  - [x] مجموع أرقام السنوات (Sum of Years' Digits)
- [x] **[ASSET-002]** نقل الأصول بين الفروع ✅ (باكند)
  - [x] جدول `asset_transfers_branches`
  - [x] تتبع الموقع الحالي + تاريخ النقل
  - [x] قيد محاسبي تلقائي عند النقل
- [x] **[ASSET-003]** إعادة تقييم الأصول ✅ (باكند)
  - [x] تحديث قيمة الأصل + قيد الزيادة/النقصان
  - [x] تعديل الإهلاك المستقبلي تلقائياً
- [x] **[ASSET-004]** تأمين وصيانة الأصول ✅ (باكند)
  - [x] جدول `asset_insurance` + `asset_maintenance`
  - [x] جدولة صيانة دورية + إشعارات تجديد التأمين
  - [x] تسجيل تكاليف الصيانة
- [x] **[ASSET-005]** باركود/QR للأصول ✅ (باكند)
  - [x] توليد QR Code لكل أصل + طباعة ملصقات
  - [x] مسح سريع لعرض التفاصيل

### 8.15 الموارد البشرية — المهام المتبقية

> 📝 **الملفات:** `routers/hr.py` (موسّع) + `migrations/migrate_phases_8_10_to_8_15.py`

- [x] **[HR-005]** مسيرات الرواتب المطبوعة (Payslip) ✅ (باكند)
  - [x] قالب مسير راتب احترافي
  - [x] طباعة PDF + إرسال بالبريد الإلكتروني
  - [x] بوابة موظف لتحميل المسير
- [x] **[HR-006]** رصيد الإجازات المرحّل ✅ (باكند)
  - [x] ترحيل رصيد نهاية السنة
  - [x] حد أقصى للترحيل + انتهاء صلاحية الرصيد المرحّل
- [x] **[HR-012]** التوظيف والاستقطاب ✅ (باكند)
  - [x] جدول `job_openings`
  - [x] نشر إعلان وظيفي + استقبال السير الذاتية
  - [x] مراحل المقابلات + تقييم المرشحين
  - [x] قبول/رفض + إنشاء ملف موظف تلقائياً

> 📝 **الحسابات المطلوبة لإكمال المرحلة 8:**
>
> | مفتاح الربط | اسم الحساب | الوحدة | الأولوية |
> |---|---|---|---|
> | `acc_map_raw_materials` | المواد الخام | التصنيع | عالية |
> | `acc_map_wip` | إنتاج قيد التنفيذ (WIP) | التصنيع | عالية |
> | `acc_map_finished_goods` | المنتجات التامة | التصنيع | عالية |
> | `acc_map_direct_labor` | العمالة المباشرة | التصنيع | عالية |
> | `acc_map_mfg_overhead` | الأعباء الصناعية | التصنيع | عالية |
> | `acc_map_project_costs` | تكاليف المشاريع | المشاريع | عالية |
> | `acc_map_project_revenue` | إيرادات المشاريع | المشاريع | عالية |
> | `acc_map_billable_expenses` | مصروفات قابلة للفوترة | المشاريع | متوسطة |
> | `acc_map_vat_settlements` | تسوية ضريبة القيمة المضافة | الضرائب | عالية |
> | `acc_map_withholding_tax` | ضريبة الاستقطاع | الضرائب | عالية |
> | `acc_map_income_tax` | ضريبة الدخل | الضرائب | متوسطة |
> | `acc_map_allowances` | بدلات الموظفين | الموارد البشرية | عالية |
> | `acc_map_overtime` | العمل الإضافي | الموارد البشرية | عالية |
> | `acc_map_termination_benefits` | مكافآت نهاية الخدمة | الموارد البشرية | متوسطة |
> | `acc_map_prepaid_rent` | الإيجار المدفوع مقدماً | المصروفات | متوسطة |
> | `acc_map_prepaid_insurance` | التأمين المدفوع مقدماً | المصروفات | متوسطة |
> | `acc_map_accrued_expenses` | المصروفات المستحقة | المصروفات | عالية |
> | `acc_map_provision_doubtful` | مخصص الديون المعدومة | المحاسبة | متوسطة |
> | `acc_map_provision_holiday` | مخصص الإجازات | الموارد البشرية | متوسطة |

---

## 🔵 المرحلة 9: التكامل مع الأنظمة والأجهزة الخارجية
**المدة المقدرة:** 3-6 أشهر

### 9.1 API الخارجي

> 📝 **الملفات المُنشأة (Phase 9 - فبراير 2026):**
> - `backend/utils/zatca.py` — ZATCA TLV + QR + RSA signing + hash chain
> - `backend/utils/webhooks.py` — Webhook dispatch + HMAC-SHA256 + retry
> - `backend/migrations/migrate_phase9.py` — 11 جدول جديد
> - `backend/routers/external.py` — API Keys + Webhooks + ZATCA + WHT endpoints
> - `backend/routers/crm.py` — Opportunities + Support Tickets CRUD
> - `frontend/src/pages/CRM/CRMHome.jsx` — لوحة CRM
> - `frontend/src/pages/CRM/Opportunities.jsx` — إدارة الفرص البيعية  
> - `frontend/src/pages/CRM/SupportTickets.jsx` — دعم العملاء
> - `frontend/src/pages/Settings/ApiKeys.jsx` — إدارة مفاتيح API
> - `frontend/src/pages/Settings/Webhooks.jsx` — إدارة Webhooks
> - `frontend/src/pages/Taxes/WithholdingTax.jsx` — ضريبة الاستقطاع

- [x] **[API-001]** REST API عام ✅ (باكند + فرونتإند)
  - [x] Endpoints موثقة (Swagger/OpenAPI) — `/api/docs` موجود مسبقاً
  - [x] مصادقة بـ API Keys — جدول `api_keys` + إنشاء/حذف مفاتيح + SHA-256 hashing
  - [x] Rate limiting — `slowapi` middleware مضاف
  - [ ] Versioning (v1, v2)
  - [x] CORS configuration — موجود مسبقاً
  - [x] واجهة إدارة مفاتيح API — `pages/Settings/ApiKeys.jsx`
- [x] **[API-002]** Webhooks ✅ (باكند + فرونتإند)
  - [x] تسجيل webhooks — جدول `webhooks` CRUD كامل
  - [x] 20 حدث قابل للتخصيص (invoice.created / payment.received / ...)
  - [x] إرسال POST عند الحدث — HMAC-SHA256 signature
  - [x] إعادة المحاولة عند الفشل — Exponential backoff في خيوط منفصلة
  - [x] سجل Webhooks — جدول `webhook_logs` + عرض في الواجهة
  - [x] واجهة إدارة Webhooks — `pages/Settings/Webhooks.jsx`

### 9.2 تطبيق الجوال

- [ ] **[MOB-001]** تطبيق جوال رئيسي (React Native / Flutter)
  - [ ] إعداد المشروع + تسجيل دخول
  - [ ] لوحة تحكم + عرض الفواتير + عرض المخزون
  - [ ] POS على الجوال
  - [ ] نشر على Google Play + App Store
- [ ] **[MOB-002]** تطبيق جوال للموظفين
  - [ ] تسجيل الحضور + طلب إجازة
  - [ ] عرض مسير الراتب + الإشعارات
- [ ] **[MOB-003]** تطبيق جوال للعملاء
  - [ ] عرض الفواتير + الدفع أونلاين
  - [ ] تتبع الطلبات + كشف الحساب

### 9.3 بوابات الخدمة الذاتية

- [ ] **[PORTAL-001]** بوابة العملاء (Customer Portal)
  - [ ] تسجيل دخول العميل
  - [ ] عرض وتحميل الفواتير PDF
  - [ ] عرض كشف الحساب + طلب عروض أسعار
  - [ ] تتبع الطلبات + الدفع أونلاين
- [ ] **[PORTAL-002]** بوابة الموردين (Vendor Portal)
  - [ ] تسجيل دخول المورد
  - [ ] عرض وتأكيد أوامر الشراء
  - [ ] رفع فواتير الشراء + عرض كشف الحساب
- [ ] **[PORTAL-003]** بوابة الموظفين (Employee Self-Service)
  - [ ] عرض بيانات الموظف + طلب إجازة/قرض/سلفة
  - [ ] عرض وتحميل مسير الراتب
  - [ ] تحديث البيانات الشخصية + عرض رصيد الإجازات

### 9.4 التكامل مع خدمات الدفع

- [ ] **[PAY-001]** بوابة الدفع - Moyasar
  - [ ] إعداد Moyasar + رابط دفع للفواتير
  - [ ] استقبال callback + تحديث حالة الدفع
- [ ] **[PAY-002]** بوابة الدفع - HyperPay
  - [ ] نفس خطوات Moyasar
- [ ] **[PAY-003]** بوابة الدفع - Stripe
  - [ ] نفس خطوات Moyasar
- [ ] **[PAY-004]** تقسيط - Tabby/Tamara
  - [ ] تكامل Tabby + Tamara + عرض خيار التقسيط

### 9.5 التكامل مع أنظمة الشحن

- [ ] **[SHIP-001]** تكامل مع SMSA
  - [ ] إنشاء شحنة + طباعة AWB
  - [ ] تتبع الشحنة + webhook حالة الشحنة
- [ ] **[SHIP-002]** تكامل مع Aramex
  - [ ] نفس خطوات SMSA
- [ ] **[SHIP-003]** تكامل مع DHL
  - [ ] نفس خطوات SMSA

### 9.6 التكامل مع WhatsApp

- [ ] **[WA-001]** WhatsApp Business API
  - [ ] إعداد WABA + قوالب رسائل (Templates)
  - [ ] إرسال إشعارات + فواتير + تأكيد طلبات + تنبيهات دفع
- [ ] **[WA-002]** Chatbot للعملاء
  - [ ] الرد التلقائي + استعلام عن الطلب/الرصيد
  - [ ] طلب دعم فني

### 9.7 التكامل مع التجارة الإلكترونية

- [ ] **[ECOM-001]** ربط مع Salla
  - [ ] مزامنة المنتجات والمخزون
  - [ ] استيراد الطلبات + تحديث حالة الطلب
  - [ ] webhook للطلبات الجديدة
- [ ] **[ECOM-002]** ربط مع Zid
  - [ ] نفس خطوات Salla
- [ ] **[ECOM-003]** ربط مع WooCommerce
  - [ ] نفس خطوات Salla
- [ ] **[ECOM-004]** ربط مع Shopify
  - [ ] نفس خطوات Salla

### 9.8 التكامل مع أجهزة POS

- [ ] **[HW-001]** قارئ الباركود
  - [ ] دعم USB + Bluetooth scanners
  - [ ] مسح تلقائي وإضافة للسلة
- [ ] **[HW-002]** طابعة حرارية + درج النقد
  - [ ] تكامل ESC/POS + طباعة تلقائية + قوالب مخصصة
  - [ ] أمر فتح الدرج عبر الطابعة
- [ ] **[HW-003]** شاشة عرض العميل + جهاز POS Terminal
  - [ ] عرض ثانوي للمنتجات والإجمالي
  - [ ] تكامل مع Verifone/Ingenico + دفع بالبطاقة
- [ ] **[HW-004]** ميزان إلكتروني
  - [ ] قراءة الوزن تلقائياً + حساب السعر حسب الوزن
  - [ ] دعم RS232/USB

### 9.9 التكامل مع أنظمة بصمة الحضور

- [ ] **[ATT-001]** تكامل مع ZKTeco
  - [ ] قراءة البصمات + استيراد سجلات الحضور
  - [ ] مزامنة تلقائية + webhook للحضور الفوري
- [ ] **[ATT-002]** تكامل مع Anviz
  - [ ] نفس خطوات ZKTeco
- [ ] **[ATT-003]** بصمة الوجه (Face Recognition)
  - [ ] تكامل مع أجهزة Face Recognition + استيراد الحضور

### 9.10 الذكاء الاصطناعي والتنبؤات

- [ ] **[AI-001]** التنبؤ بالمبيعات
  - [ ] نموذج Machine Learning + تدريب على البيانات التاريخية
  - [ ] توقع المبيعات القادمة + تقرير التنبؤات
- [ ] **[AI-002]** التنبؤ بالطلب على المخزون
  - [ ] توقع الطلب على المنتجات
  - [ ] اقتراح كميات إعادة الطلب + تحسين المخزون
- [ ] **[AI-003]** كشف الاحتيال
  - [ ] كشف أنماط غير عادية + تنبيهات الاحتيال + فواتير مشبوهة
- [ ] **[AI-004]** مساعد ذكي (Chatbot داخلي)
  - [ ] الرد على الأسئلة + البحث في البيانات
  - [ ] اقتراحات ذكية + مساعدة المستخدمين

### 9.11 CRM متكامل

- [ ] **[CRM-001]** إدارة العملاء المتقدمة
  - [ ] نقاط اتصال (Touchpoints) + تاريخ التفاعل
  - [ ] تصنيف العملاء + دورة حياة العميل
- [x] **[CRM-002]** الفرص البيعية (Opportunities) ✅ (باكند + فرونتإند)
  - [x] جدول `sales_opportunities` + `opportunity_activities`
  - [x] مراحل البيع (Lead → Qualified → Proposal → Negotiation → Won/Lost)
  - [x] القيمة المتوقعة + احتمالية النجاح (تلقائية حسب المرحلة)
  - [x] تسجيل الأنشطة (مكالمة/بريد/اجتماع/مهمة)
  - [x] لوحة Pipeline بملخص الفرص حسب المرحلة
  - [x] واجهة `pages/CRM/Opportunities.jsx` + `pages/CRM/CRMHome.jsx`
  - [ ] تحويل إلى عرض سعر
- [ ] **[CRM-003]** الحملات التسويقية
  - [ ] جدول `marketing_campaigns`
  - [ ] استهداف شرائح العملاء + إرسال بريد جماعي
  - [ ] تتبع النتائج (Open Rate, Click Rate)
- [x] **[CRM-004]** دعم العملاء (Tickets) ✅ (باكند + فرونتإند)
  - [x] جدول `support_tickets` + `ticket_comments`
  - [x] فتح تذكرة + تعيين للموظف + ترقيم تلقائي (TKT-YYYY-XXX)
  - [x] حالات (open / in_progress / resolved / closed) + timestamps تلقائية
  - [x] أولوية (critical/high/medium/low) + SLA بالساعات + كشف الخرق
  - [x] تعليقات + is_internal للتعليقات الداخلية
  - [x] إحصائيات: avg_resolution_hours + critical_open
  - [x] واجهة `pages/CRM/SupportTickets.jsx`
- [ ] **[CRM-005]** قاعدة المعرفة
  - [ ] جدول `knowledge_base`
  - [ ] أسئلة شائعة (FAQ) + مقالات مساعدة + بحث

### 9.12 إدارة الخدمات (Service Management)

- [ ] **[SVC-001]** إدارة طلبات الصيانة
  - [ ] جدول `service_requests`
  - [ ] فتح طلب صيانة + تعيين فني
  - [ ] تتبع حالة الطلب + تكاليف الصيانة
- [ ] **[SVC-002]** إدارة المستندات (Document Management)
  - [ ] رفع وتخزين المستندات + إدارة الإصدارات
  - [ ] البحث في المستندات + وصول آمن حسب الصلاحيات

---

## 🔵 المرحلة 10: الامتثال الضريبي — ZATCA والفوترة الإلكترونية
**المدة المقدرة:** 1-2 شهر  
**الأهمية:** إلزامي للسوق السعودي

### 10.1 ZATCA Phase 2 — الفوترة الإلكترونية

- [ ] **[ZATCA-001]** تكامل ZATCA الفعلي — التسجيل والمصادقة
  - [ ] التسجيل في بوابة ZATCA
  - [ ] إنشاء API Client للتواصل مع خوادم هيئة الزكاة والضريبة والجمارك
  - [ ] الحصول على شهادة CSID حقيقية (إزالة المحاكاة)
  - [ ] دالة `registration_request` لإرسال طلب التسجيل
  - [ ] دالة `compliance_check` للتحقق من حالة الشركة
  - [ ] تخزين الشهادة والمفاتيح بشكل آمن

- [x] **[ZATCA-002]** التوقيع الرقمي للفواتير ✅ (باكند)
  - [x] `utils/zatca.py` — Signature Service كامل
  - [x] توقيع رقمي RSA-2048 + SHA-256
  - [x] `compute_invoice_hash()` — Hash فريد لكل فاتورة
  - [x] تخزين hash في عمود `zatca_hash` على جدول invoices
  - [x] سلسلة الهاشات (Invoice Hash Chain) — ربط بـ hash الفاتورة السابقة
  - [x] `generate_rsa_keypair()` + تخزين المفاتيح في company_settings
  - [x] `verify_invoice_signature()` — endpoint للتحقق
  - [ ] شهادة CSID حقيقية من ZATCA (يتطلب تسجيل فعلي)

- [ ] **[ZATCA-003]** إرسال واستقبال الفواتير
  - [ ] إرسال الفواتير إلى بوابة ZATCA
  - [ ] استقبال ردود ZATCA (Accepted / Rejected / Warning)
  - [ ] إعادة المحاولة عند الفشل
  - [ ] Audit Trail لجميع عمليات الإرسال والاستقبال

- [x] **[ZATCA-004]** QR Code على الفواتير ✅ (باكند + فرونتإند)
  - [x] `generate_zatca_qr_base64()` في `utils/zatca.py`
  - [x] TLV encoding حسب مواصفات ZATCA (Tags 1-7)
  - [x] `build_zatca_tlv()` + `decode_zatca_tlv()` للتشفير والفك
  - [x] Seller Name — Tag 1
  - [x] VAT Registration Number — Tag 2
  - [x] Timestamp ISO 8601 — Tag 3
  - [x] Total Amount — Tag 4
  - [x] VAT Amount — Tag 5
  - [x] Invoice Hash — Tag 6
  - [x] Digital Signature — Tag 7
  - [x] توليد تلقائي عند إنشاء كل فاتورة (`process_invoice_for_zatca` في invoices.py)
  - [x] عرض QR Code في `pages/Sales/InvoiceDetails.jsx` مع حالة ZATCA
  - [x] endpoint `POST /external/zatca/generate-qr` + `GET /external/zatca/verify/{id}`

- [ ] **[ZATCA-005]** Simplified Tax Invoice — B2C
  - [ ] صيغة فاتورة مبسطة حسب مواصفات ZATCA
  - [ ] QR Code إلزامي على كل فاتورة
  - [ ] إرسال فوري لبوابة ZATCA
  - [ ] لا تتطلب بيانات العميل الكاملة
  - [ ] إمكانية تجميع عدة معاملات في فاتورة واحدة

- [ ] **[ZATCA-006]** Standard Tax Invoice — B2B
  - [ ] صيغة فاتورة قياسية حسب مواصفات ZATCA
  - [ ] بيانات العميل كاملة (اسم + عنوان + رقم ضريبي)
  - [ ] رقم التسجيل الضريبي للعميل إلزامي
  - [ ] إرسال فوري لبوابة ZATCA
  - [ ] تضمين معلومات الخصم إن وجدت

- [ ] **[ZATCA-007]** تصدير التقارير بصيغة ZATCA
  - [ ] دالة `export_vat_return_xml` لتصدير الإقرار الضريبي بصيغة XML
  - [ ] دالة `validate_invoice_schema` للتحقق من صحة بيانات الفاتورة
  - [ ] Schema Validation قبل الإرسال

### 10.2 الضرائب الأخرى

- [x] **[TAX-001]** ضريبة الاستقطاع (Withholding Tax — WHT) ✅ (باكند + فرونتإند)
  - [x] جدول `wht_rates` مع 8 نسب سعودية جاهزة (خدمات، إيجار، استشارات...)
  - [x] جدول `wht_transactions` لتسجيل كل معاملة استقطاع
  - [x] `POST /external/wht/calculate` — حساب الاستقطاع بدون حفظ
  - [x] `POST /external/wht/transactions` — إنشاء معاملة استقطاع
  - [x] واجهة `pages/Taxes/WithholdingTax.jsx` — حاسبة + جداول النسب والمعاملات
  - [ ] قيود GL تلقائية (مدين: الدائنون، دائن: WHT مستحقة)
  - [ ] إقرار WHT + شهادة استقطاع للمورد

- [ ] **[TAX-002]** إشعارات مواعيد التقديم الضريبي
  - [ ] تقويم المواعيد الضريبية
  - [ ] إشعارات قبل الموعد (7/3/1 أيام)
  - [ ] تكامل مع البريد الإلكتروني + الإشعارات الداخلية

---

## 📚 التوثيق والأدلة

- [x] **[DOC-001]** دليل المستخدم التشغيلي الشامل (عربي) (`docs/analysis/system_integration_guide.md`)
  - [x] خطوات العمل التفصيلية للمبيعات، المشتريات، الموارد البشرية، المشاريع، والتصنيع
  - [x] "دليل الأزرار" المفصل لشرح عناصر الواجهة
  - [x] تم تحديث المحتوى ليكون دليلاً تشغيلياً حسب الطلب
- [x] **[DOC-002]** أدلة المستخدم لكل وحدة (شاملة)
  - [x] 🏠 مساحة العمل (Workspace)
  - [x] 📊 المحاسبة (Accounting)
  - [x] 🏢 الأصول الثابتة (Fixed Assets)
  - [x] 🏦 الخزينة والمصروفات (Treasury & Expenses)
  - [x] ⚖️ تسوية البنك (Bank Reconciliation)
  - [x] 💰 المبيعات (Sales)
  - [x] 🏪 نقاط البيع (POS)
  - [x] 🛒 المشتريات (Purchasing)
  - [x] 📦 المخزون (Inventory)
  - [x] 🏭 التصنيع (Manufacturing)
  - [x] 📐 المشاريع (Projects)
  - [x] 🧾 الضرائب (Taxes)
  - [x] 📈 التقارير (Reports)
  - [x] 👥 الموارد البشرية (HR)
  - [x] 📋 سجلات المراقبة (Audit Logs)
  - [x] 🔐 الأدوار والصلاحيات (Roles & Permissions)
  - [x] 🏢 الفروع (Branches)
  - [x] 💲 سياسة التكلفة (Costing Policy)
  - [x] ⚙️ الإعدادات (Settings)

---

## 📊 ملخص الإحصائيات

### عدد المهام حسب المرحلة

| الفئة | عدد المهام | الحالة |
|-------|-----------|--------|
| 🔴 المرحلة 1: إصلاح المشاكل الحرجة | 23 | ✅ مكتمل |
| 🔴 المرحلة 2: الميزات المحاسبية الأساسية | 19 | ✅ مكتمل |
| 🔴 المرحلة 3: المخزون المتقدم | 14 | ✅ مكتمل |
| ✅ المرحلة 4: الموارد البشرية المتقدمة | 16 | ✅ مكتمل (باكند) |
| 🟡 المرحلة 5: التصنيع المتقدم | 11 | ✅ مكتمل |
| 🟡 المرحلة 6: المشاريع والتقارير | 10 | ✅ مكتمل |
| ✅ المرحلة 7: تحسينات النظام | 18 | ✅ مكتمل |
| ✅ المرحلة 8: إكمال الوحدات للوصول إلى 100% | 65+ | ✅ مكتمل (باكند) — بقي POS-001/002/005 + SALES-005 |
| 🔵 المرحلة 9: التكامل الخارجي | 50+ | 🟡 جارٍ (API Keys ✅ + Webhooks ✅ + CRM-002 ✅ + CRM-004 ✅) |
| 🔵 المرحلة 10: الامتثال الضريبي (ZATCA) | 11 | 🟡 جارٍ (ZATCA-002 ✅ + ZATCA-004 ✅ + WHT ✅) |
| **الإجمالي** | **~237 مهمة** | |

### نسبة اكتمال كل وحدة

| الوحدة | النسبة الحالية | المستهدف | الملاحظات |
|--------|---------------|----------|-----------|
| المخزون | 85% | 100% | ينقصه تقارير متقدمة |
| المبيعات | **95%** | 100% | ✅ عمولات + فوترة جزئية + حد ائتمان (باكند) — بقي طباعة |
| المشتريات | **95%** | 100% | ✅ RFQ + تقييم موردين + Blanket PO (باكند) |
| المحاسبة | 70% | 100% | ينقصه COGS تلقائي + شجرة حسابات |
| الخزينة | 75% | 100% | جيد — تحسينات طفيفة |
| الموارد البشرية | **95%** | 100% | ✅ Payslip + ترحيل إجازات + توظيف (باكند) |
| الأصول الثابتة | **95%** | 100% | ✅ 3 طرق إهلاك + نقل/تقييم/تأمين/QR (باكند) |
| التصنيع | 95% | 100% | ✅ مكتمل تقريباً |
| المشاريع | 90% | 100% | ✅ مكتمل تقريباً |
| الضرائب | 75% | 100% | ✅ ZATCA QR + توقيع رقمي + WHT (باكند) — بقي ZATCA-001/003/005-007 |
| نقاط البيع | **85%** | 100% | ✅ خصومات + ولاء + طاولات + KDS (باكند) — بقي Offline/طباعة |
| التقارير | 85% | 100% | ✅ تم إضافة 15 تقرير جديد |
| الأمان | **100%** | 100% | ✅ مكتمل (Token Blacklist + HTTPS + Sanitization) |
| الأدوار والصلاحيات | **100%** | 100% | ✅ مكتمل (Field/Warehouse/CC + Audit) |
| الفروع | 90% | 100% | جيد جداً |
| شجرة الحسابات | **100%** | 100% | ✅ مكتمل (102 حساب + 25 ربط) |
| قاعدة البيانات | **100%** | 100% | ✅ مكتمل (DB-101→103 تنظيف + party_id) |
| لوحة التحكم | **100%** | 100% | ✅ مكتمل (تخطيطات + 5 widgets جديدة) |

### إحصائيات النظام الحالية

| الفئة | العدد |
|-------|-------|
| إجمالي API Endpoints | ~380+ |
| إجمالي صفحات Frontend | ~163+ |
| إجمالي أسطر Backend | ~26,000+ |
| جداول قاعدة البيانات | 122+ |
| Triggers | 25 |
| Indexes | 40+ |

---

## 🎯 الأولويات الموصى بها (محدّثة)

### أولوية فورية — مكتمل ✅
1. ~~جميع مهام المرحلة 1 (إصلاح المشاكل الحرجة)~~ ✅
2. ~~جميع مهام المرحلة 2 (الميزات المحاسبية)~~ ✅
3. ~~جميع مهام المرحلة 3 (المخزون المتقدم)~~ ✅
4. ~~جميع مهام المرحلة 7 (تحسينات النظام)~~ ✅

### الأولوية القصوى — المرحلة 8A (شهر 1-3) 🔴
1. **ZATCA Phase 2** — إلزامي للسوق السعودي (ZATCA-001 → ZATCA-007)
2. **إكمال شجرة الحسابات** — الضرائب، التصنيع، المشاريع (COA-001 → COA-006)
3. **تنظيف قاعدة البيانات** — إزالة deprecated columns (DB-101 → DB-103)
4. **إكمال القيود التلقائية** — COGS، التصنيع، المشاريع (GL-001 → GL-007)

### الأولوية العالية — المرحلة 8B (شهر 3-6) 🟡
1. **إكمال التصنيع** — حسابات محاسبية + قيود + تقارير (MFG-101 → MFG-109)
2. **إكمال المشاريع** — حسابات محاسبية + EVM + تقارير (PRJ-101 → PRJ-109)
3. **إكمال الأمان** — Token Blacklist + HTTPS (SEC-201 → SEC-204)
4. **إكمال الصلاحيات** — Field-level + Warehouse-level (PERM-001 → PERM-004)
5. **إكمال التقارير** — PDF/Excel export + Report Builder (RPT-101 → RPT-106)

### الأولوية المتوسطة — المرحلة 8C (شهر 6-9) 🟢
1. **تحسينات POS** — Offline + طباعة حرارية + Loyalty (POS-001 → POS-008)
2. **تحسينات المبيعات** — عمولات + فوترة جزئية (SALES-001 → SALES-005)
3. **تحسينات المشتريات** — RFQ + تقييم موردين (PUR-001 → PUR-003)
4. **تحسينات الأصول** — إهلاك متقدم + نقل فروع (ASSET-001 → ASSET-005)
5. **الموارد البشرية المتبقية** — Payslip + ترحيل إجازات (HR-005, HR-006, HR-012)

### أولوية منخفضة — المرحلة 9 (شهر 9-12) 🔵
1. REST API + Webhooks (API-001, API-002)
2. CRM متكامل (CRM-001 → CRM-005)
3. تطبيق الجوال (MOB-001 → MOB-003)
4. لوحة تحكم قابلة للتخصيص (DASH-001, DASH-002)

### آخر أولوية — سنة 2+ ⚪
1. بوابات الخدمة الذاتية (PORTAL-001 → PORTAL-003)
2. التكامل مع التجارة الإلكترونية (ECOM-001 → ECOM-004)
3. التكامل مع WhatsApp (WA-001, WA-002)
4. الذكاء الاصطناعي (AI-001 → AI-004)
5. أجهزة POS المتقدمة (HW-001 → HW-004)
6. التكامل مع أنظمة بصمة الحضور (ATT-001 → ATT-003)

---

## 📝 ملاحظات مهمة

1. **الترتيب ليس صارماً** — يمكن تقديم/تأخير مهام حسب احتياجات العمل
2. **التبعيات** — بعض المهام تعتمد على إكمال مهام أخرى أولاً
3. **الاختبار** — كل مهمة يجب أن تتضمن اختبارات Unit Tests + Integration Tests
4. **التوثيق** — تحديث التوثيق بعد إكمال كل مهمة
5. **Code Review** — مراجعة الكود قبل الدمج
6. **Migration Scripts** — إنشاء scripts للتحديثات على قاعدة البيانات
7. **Backward Compatibility** — الحفاظ على التوافق مع الإصدارات السابقة قدر الإمكان
8. **ZATCA إلزامي** — يجب إعطاء أولوية قصوى لتكامل ZATCA Phase 2 كونه إلزامي في السعودية

---

**آخر تحديث:** 21 فبراير 2026  
**الحالة:** المرحلة 8 مكتملة ✅ — المرحلة 9 جارية (API Keys + Webhooks + CRM-002/004) — المرحلة 10 بدأت (ZATCA-002/004 + WHT)  
**التقييم:** تم إنجاز حوالي 94% من النظام الأساسي — الجديد: نظام CRM + مفاتيح API + Webhooks + ZATCA QR + WHT
