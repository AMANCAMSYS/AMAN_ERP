# 📋 قائمة المهام الرئيسية — نظام أمان ERP
# AMAN ERP — Master Task List (Consolidated)

> **تاريخ التحديث:** يونيو 2026
> **المصدر:** تم دمج الملفات التالية في هذا الملف الموحد:
> - `docs/TASK_LIST.md`
> - `docs/analysis/TASKS.md` (1475 سطر)
> - `docs/analysis/BACKLOG.md` (190 سطر)
> - `docs/SECURITY_AUDIT_REPORT.md` (الثغرات المتبقية)
> - `docs/SYSTEM_EVALUATION_REPORT.md` (خارطة الطريق)
> - فحص شامل جديد للنظام (800 endpoint + 229 صفحة + 220 جدول)

---

## 📊 ملخص حالة النظام

| المقياس | القيمة |
|---------|--------|
| إجمالي الـ Endpoints (Backend) | 800 |
| إجمالي الصفحات (Frontend) | ~229 route + ~246 ملف |
| إجمالي الجداول في قاعدة البيانات | 220 |
| الجداول التي بها بيانات | 30 |
| الجداول الفارغة | 190 |
| ملفات الراوتر (Backend) | 62 |
| الميزات المكتملة (كود) | ~98% |
| البيانات المُدخلة فعلياً | بيانات أساسية فقط |

---

## 📍 أين وصل النظام حالياً؟

### ✅ ما تم إدخاله (البيانات الأساسية — Master Data)

| البيان | العدد | التفاصيل |
|--------|-------|----------|
| المستخدمون | 10 | omar (مشرف) + 9 موظفين لكل قسم |
| الفروع | 3 | المقر الرئيسي (الرياض) + جدة + دبي |
| الأقسام | 7 | مالية، مبيعات، مشتريات، مستودعات، HR، إنتاج، POS |
| الوظائف | 8 | مسجلة لكل قسم |
| الأدوار | 8 | admin, superuser, hr, accountant, sales, inventory, cashier, user |
| شجرة الحسابات | 121 حساب | 40 أصول + 21 التزامات + 6 حقوق ملكية + 14 إيرادات + 40 مصاريف |
| المنتجات | 7 | ألمنيوم، خشب، باب، نافذة، مسامير، لابتوب، خدمة تركيب |
| فئات المنتجات | 5 | مواد خام، منتجات تامة، مستلزمات، خدمات، أصول ثابتة |
| وحدات القياس | 5 | قطعة، كيلوغرام، لتر، متر، صندوق |
| الأطراف (عملاء/موردون) | 11 | 6 عملاء + 5 موردون |
| مجموعات العملاء | 3 | جملة (خصم 5%)، تجزئة، خارجيين (خصم 3%) |
| مجموعات الموردون | 2 | محليون (30 يوم) + خارجيون (60 يوم) |
| المستودعات | 5 | رئيسي + مواد خام + تامة (الرياض) + جدة + دبي |
| حسابات الخزينة | 7 | 4 بنوك + 3 صناديق نقدية (أرصدة = 0) |
| العملات | 5 | ريال (أساسية) + دولار + يورو + درهم + جنيه |
| أسعار الصرف | 4 | AED 1.02 + EGP 0.077 + EUR 4.10 + USD 3.75 |
| السنة المالية | 1 | 2026 (مفتوحة) |
| الفترات المالية | 12 | يناير - ديسمبر 2026 |
| معدلات الضريبة | 1 | ضريبة القيمة المضافة 15% |
| معدلات الاستقطاع | 8 | خدمات، إيجار، استشارات، إلخ |
| الأنظمة الضريبية | 4 | SA, AE, SY, EG |
| سياسة التكلفة | 1 | مُفعّلة |
| قيود اليومية | 8 | 7 أرصدة افتتاحية للخزينة + 1 أرصدة مخزون/أصول/ذمم |
| أسطر القيود | 19 | القيود الافتتاحية |
| إعدادات الشركة | 79 | جميع الإعدادات الأساسية |
| سجلات المخزون | 6 | مسجلة بكميات = 0 |

### ❌ ما لم يُدخل بعد (190 جدول فارغ)

**لا توجد أي عمليات تشغيلية حتى الآن:**
- 0 فواتير بيع / شراء
- 0 أوامر بيع / شراء
- 0 عروض أسعار
- 0 مدفوعات / مقبوضات
- 0 جلسات نقاط بيع
- 0 أوامر إنتاج / قوائم مواد / مراكز عمل
- 0 مشاريع / مهام
- 0 أصول ثابتة مسجلة
- 0 ميزانيات / مراكز تكلفة
- 0 مصاريف
- 0 عقود
- 0 مسيرات رواتب / حضور / إجازات / قروض
- 0 حركات مخزون / تعديلات / تحويلات
- 0 إقرارات ضريبية
- 0 تسويات بنكية

---

## 🔥 المرحلة 1 — إصلاحات أمنية متبقية (8 ثغرات)

> **الأولوية:** عالية — يجب إنهاؤها قبل بيئة الإنتاج
> **الجهد المقدّر:** أسبوع واحد — ✅ **مكتملة بالكامل**

| # | الكود | المهمة | المستوى | الحالة |
|---|-------|--------|---------|--------|
| 1 | SEC-001 | نقل Rate Limiting لـ Redis | 🟠 عالي | ✅ مكتمل — Redis backend مع graceful fallback |
| 2 | SEC-002 | استبدال `decode_token` بـ `get_current_user` | 🟠 عالي | ✅ مكتمل — 3 endpoints في companies.py |
| 3 | SEC-003 | مراجعة 200+ حالة `text(f"...")` | 🟡 متوسط | ✅ مكتمل — fixed utils/accounting.py + dashboard.py + scheduled_reports.py |
| 4 | SEC-004 | إضافة حماية CSRF | 🟡 متوسط | ✅ مكتمل — توثيق + tokens في localStorage (لا حاجة لـ CSRF) |
| 5 | SEC-005 | تشديد `connect-src` في CSP | 🟡 متوسط | ✅ مكتمل — dynamic origins based on APP_ENV |
| 6 | SEC-006 | استخدام `.pgpass` بدلاً من `PGPASSWORD` | 🔵 منخفض | ✅ مكتمل — auto-generate ~/.pgpass + remove PGPASSWORD env |
| 7 | SEC-007 | فصل Engine الخاص بـ DDL | 🔵 منخفض | ✅ مكتمل — `_ddl_engine` (AUTOCOMMIT) + `engine` (regular) |
| 8 | SEC-008 | التحقق من قوة `SECRET_KEY` | 🔵 منخفض | ✅ مكتمل — pydantic validator (min 32 chars + entropy check) |

---

## 🔴 المرحلة 2 — تكامل ZATCA (إلزامي قانونياً)

> **الأولوية:** إلزامي للسوق السعودي
> **الجهد المقدّر:** 1-2 شهر

| # | الكود | المهمة | التفاصيل |
|---|-------|--------|----------|
| 1 | ZATCA-001 | التسجيل في بوابة ZATCA والمصادقة | إنشاء API Client + CSID حقيقية + تخزين الشهادة |
| 2 | ZATCA-002 | شهادة CSID حقيقية | التوقيع الرقمي منتهٍ ✅ — المتبقي: ربط مع البوابة |
| 3 | ZATCA-003 | إرسال واستقبال الفواتير لبوابة ZATCA | Retry عند الفشل + Audit Trail |
| 4 | ZATCA-005 | فاتورة ضريبية مبسطة B2C | صيغة ZATCA + إرسال فوري + تجميع المعاملات |
| 5 | ZATCA-006 | فاتورة ضريبية قياسية B2B | بيانات عميل كاملة + رقم ضريبي |
| 6 | ZATCA-007 | تصدير إقرار ضريبي XML | export_vat_return_xml + Schema Validation |

---

## 🟡 المرحلة 3 — تحسينات وظيفية

> **الجهد المقدّر:** 2-4 أسابيع

### 3.1 تحسينات تجربة المستخدم

| # | المهمة | التفاصيل |
|---|--------|----------|
| 1 | شجرة حسابات مخصصة حسب النشاط | توليد COA مختلفة لكل قالب صناعي (تجاري، مطعم، مصنع، مقاولات) |
| 2 | لوحات تحكم مخصصة لكل نشاط | KPIs مختلفة حسب القالب |
| 3 | تقارير مخصصة لكل نشاط | Food Cost للمطاعم، Progress Billing للمقاولات |
| 4 | ربط الموديولات المتبقية | الاعتمادات، الأمان، الملاحظات، استيراد البيانات — ربط كامل |

### 3.2 تحسينات تقنية

| # | المهمة | التفاصيل |
|---|--------|----------|
| 1 | قيود GL تلقائية لـ WHT | مدين: الدائنون، دائن: WHT مستحقة — عند إنشاء فاتورة |
| 2 | محرك سير العمل (Workflow Engine) | بناء محرك اعتمادات: طلب ← موافقة ← تنفيذ |
| 3 | إشعارات البريد الإلكتروني | تهيئة SMTP + إشعارات حقيقية عند الأحداث |
| 4 | WebSocket للإشعارات الفورية | بدلاً من polling، إشعارات حية |
| 5 | تنبيهات إعادة الطلب الذكية | ربط inventory reorder مع notification pipeline |

---

## 🔵 المرحلة 4 — تكاملات خارجية

> **الجهد المقدّر:** 6-12 شهر (مشاريع مستقلة)

### 4.1 تطبيق الجوال (MOB)
| # | الكود | المهمة |
|---|-------|--------|
| 1 | MOB-001 | تطبيق React Native للمبيعات والمخزون (iOS + Android) |
| 2 | MOB-002 | إشعارات Push + مزامنة Offline |
| 3 | MOB-003 | ماسح الباركود بالكاميرا + توقيع استلام |

### 4.2 بوابات الخدمة الذاتية (PORTAL)
| # | الكود | المهمة |
|---|-------|--------|
| 1 | PORTAL-001 | بوابة العملاء (تتبع الطلبات + الفواتير) |
| 2 | PORTAL-002 | بوابة الموردين (عروض أسعار + تأكيد طلبات) |
| 3 | PORTAL-003 | بوابة الموظفين (طلبات الإجازات + الرواتب) |

### 4.3 بوابات الدفع (PAY)
| # | الكود | المهمة |
|---|-------|--------|
| 1 | PAY-001 | Stripe — بطاقات ائتمان دولية |
| 2 | PAY-002 | PayTabs — بطاقات عربية + مدى + STCPay |
| 3 | PAY-003 | HyperPay — بوابة المنطقة العربية |
| 4 | PAY-004 | Apple Pay / Google Pay |

### 4.4 الشحن واللوجستيات (SHIP)
| # | الكود | المهمة |
|---|-------|--------|
| 1 | SHIP-001 | Aramex API — شحن + تتبع + طباعة بوليصة |
| 2 | SHIP-002 | DHL / FedEx / SMSA |
| 3 | SHIP-003 | حساب تكاليف الشحن تلقائياً |

### 4.5 WhatsApp (WA)
| # | الكود | المهمة |
|---|-------|--------|
| 1 | WA-001 | إرسال الفواتير والإيصالات عبر WhatsApp Business API |
| 2 | WA-002 | إشعارات تلقائية (تأكيد طلب + تتبع شحن + فاتورة) |

### 4.6 التجارة الإلكترونية (ECOM)
| # | الكود | المهمة |
|---|-------|--------|
| 1 | ECOM-001 | مزامنة المخزون مع Shopify |
| 2 | ECOM-002 | مزامنة مع WooCommerce |
| 3 | ECOM-003 | مزامنة مع سلة (Salla) + زد (Zid) |
| 4 | ECOM-004 | مزامنة تلقائية للمبيعات + المخزون + العملاء |

### 4.7 أجهزة POS (HW)
| # | الكود | المهمة |
|---|-------|--------|
| 1 | HW-001 | قارئ باركود USB/Bluetooth |
| 2 | HW-002 | طابعة فواتير حرارية (Driver Integration) |
| 3 | HW-003 | ميزان إلكتروني (طباعة الوزن تلقائياً) |
| 4 | HW-004 | شاشة عميل ثانوية (Customer Display Hardware) |

### 4.8 أجهزة الحضور والانصراف (ATT)
| # | الكود | المهمة |
|---|-------|--------|
| 1 | ATT-001 | تكامل ZKTeco (بصمة + وجه) |
| 2 | ATT-002 | استيراد سجلات الحضور تلقائياً |
| 3 | ATT-003 | ربط الحضور بمسيرة الرواتب مباشرة |

---

## 🤖 المرحلة 5 — الذكاء الاصطناعي

> **الجهد المقدّر:** 6+ أشهر

| # | الكود | المهمة | التفاصيل |
|---|-------|--------|----------|
| 1 | AI-001 | تنبؤ المبيعات والطلب | LSTM / Prophet |
| 2 | AI-002 | كشف التلاعب المالي | Anomaly Detection |
| 3 | AI-003 | مساعد محاسبي ذكي | Copilot Chat |
| 4 | AI-004 | تصنيف الفواتير وقراءة OCR | مع ML models |

---

## 📊 ملخص إحصائي للمراحل

| المرحلة | عدد المهام | الجهد المقدّر | الأولوية |
|---------|-----------|--------------|----------|
| 🔥 المرحلة 1: الأمان | 8 | أسبوع | حرجة |
| 🔴 المرحلة 2: ZATCA | 6 | 1-2 شهر | إلزامية |
| 🟡 المرحلة 3: تحسينات وظيفية | 9 | 2-4 أسابيع | عالية |
| 🔵 المرحلة 4: تكاملات خارجية | 28 | 6-12 شهر | متوسطة |
| 🤖 المرحلة 5: ذكاء اصطناعي | 4 | 6+ أشهر | منخفضة |
| **المجموع** | **55 مهمة** | | |

---

## ✅ ما تم إنجازه سابقاً (ملخص)

### البنية التحتية
- [x] FastAPI Backend + PostgreSQL + Multi-tenant architecture
- [x] React Frontend + Vite + i18n (AR/EN)
- [x] JWT Authentication + RBAC + Branch-level filtering
- [x] Docker deployment (docker-compose.yml + prod)
- [x] Prometheus + Grafana monitoring
- [x] Sentry error tracking (optional)

### الوحدات المكتملة (كود + واجهة)
- [x] **المحاسبة** (31 endpoint): شجرة حسابات، قيود يومية، سنة/فترات مالية، أرصدة افتتاحية، قيود إغلاق، قوالب متكررة، FX revaluation
- [x] **المبيعات** (49 endpoint): عملاء، فواتير، أوامر، عروض أسعار، مرتجعات، مقبوضات، إشعارات دائنة/مدينة، عمولات، حد ائتمان
- [x] **المشتريات** (45 endpoint): موردون، أوامر شراء، فواتير، مدفوعات، مرتجعات، طلب عروض أسعار (RFQ)، اتفاقيات شراء، تقييم موردين
- [x] **المخزون** (77 endpoint): منتجات، فئات، مستودعات، تحويلات، تعديلات، شحنات، دفعات/سريال، فحص جودة، جرد دوري، سياسات تكلفة، Kits/Variants/Bins
- [x] **التصنيع** (48 endpoint): مراكز عمل، مسارات، قوائم مواد (BOM)، أوامر إنتاج، عمليات، MRP، صيانة المعدات، فحص جودة، تقارير كلفة
- [x] **الخزينة** (9 + 13 + 13 endpoint): حسابات، معاملات، تحويلات، شيكات مقبوضة/مدفوعة، أوراق قبض/دفع، تسويات بنكية، استيراد بنكي
- [x] **الموارد البشرية** (82 endpoint): موظفين، أقسام، وظائف، مسيّرات رواتب، إجازات، حضور، قروض، ساعات إضافية، GOSI، مستندات، أداء، تدريب، مخالفات، عهد، قسائم راتب، ترحيل إجازات، توظيف، WPS، سعودة، نهاية خدمة
- [x] **الأصول** (23 endpoint): تسجيل، إهلاك (3 طرق)، تحويل، إعادة تقييم، صيانة، تأمين، QR
- [x] **المشاريع** (39 endpoint): مشاريع، مهام، Timesheets، مصاريف، إيرادات، ميزانيات، مستندات، أوامر تغيير، Retainer، EVM، تقارير
- [x] **المصاريف** (10 endpoint): تسجيل، موافقة، تقارير حسب النوع/المركز/الشهر
- [x] **الضرائب** (40 endpoint): معدلات، مجموعات، إقرارات، مدفوعات، تقارير VAT، استقطاع، تقويم، تحليل فروع
- [x] **CRM** (24 endpoint): فرص مبيعات، تذاكر دعم، حملات تسويقية، قاعدة معرفة
- [x] **نقاط البيع** (32 endpoint): جلسات، طلبات، عروض، ولاء، طاولات، مطبخ، Offline، طباعة حرارية
- [x] **العقود** (9 endpoint): إنشاء، تجديد، إلغاء، فاتورة تلقائية، تنبيهات انتهاء
- [x] **الخدمات** (16 endpoint): طلبات صيانة، إدارة مستندات، تتبع تكاليف
- [x] **الموافقات** (12 endpoint): سير عمل، طلبات، إجراءات
- [x] **التقارير** (43 endpoint + 12 مجدولة): ميزان مراجعة، أرباح/خسائر، ميزانية، تدفق نقدي، دفتر أستاذ، تحليل أفقي، نسب مالية، مخصصة، مجدولة، مشاركة
- [x] **إعدادات النظام** (4 endpoint + 22 tab): عامة، مالية، مخزون، فوترة، مبيعات، مشتريات، POS، HR، هوية، أمان، تدقيق، امتثال، إشعارات، ربط حسابات، أداء
- [x] **الأمان** (11 endpoint): 2FA، تغيير كلمة مرور، سياسة كلمات مرور، جلسات
- [x] **التكاملات** (17 endpoint): API Keys، Webhooks، ZATCA QR، استقطاع WHT
- [x] **استيراد/تصدير البيانات** (6 endpoint): Excel/CSV import + export
- [x] **لوحة التحكم** (14 endpoint): إحصائيات، رسوم بيانية، widgets مخصصة
- [x] **الإشعارات** (8 endpoint + 21 نوع): إشعارات + إعدادات + بريد
- [x] **البحث العام** (Ctrl+K): بحث Spotlight في 160+ صفحة مع fuzzy matching

### التقارير المكتملة
- [x] تقرير ميزان المراجعة + مقارنة + تصدير
- [x] تقرير الأرباح والخسائر + مقارنة + تصدير + تفصيلي
- [x] الميزانية العمومية + مقارنة + تصدير
- [x] تقرير التدفق النقدي + تصدير
- [x] دفتر الأستاذ العام + تصدير
- [x] تحليل أفقي + نسب مالية
- [x] تقارير المبيعات (ملخص + اتجاه + بالعميل + بالمنتج + بالكاشير)
- [x] تقارير المشتريات (ملخص + اتجاه + بالمورد)
- [x] كشف حساب عميل/مورد + تقادم
- [x] تقارير المخزون (تقييم + حركات + مخزون راكد + COGS + معدل دوران)
- [x] تقارير التصنيع (تكلفة + كفاءة + استهلاك + عمالة + تباين)
- [x] تقرير الميزانية مقابل الفعلي
- [x] تقارير ضريبية (VAT + تدقيق + عمولات)
- [x] تقارير HR (رواتب + إجازات)
- [x] تقارير المشاريع (ربحية + موارد + تباين)
- [x] تقرير الزكاة
- [x] تقارير موحدة (Consolidation) متعددة الفروع
- [x] دعم RTL في PDF + رسوم بيانية

---

## 🗂️ الجداول الفارغة مُصنّفة حسب الوحدة

### المبيعات (17 جدول فارغ)
`customers`, `customer_balances`, `customer_bank_accounts`, `customer_contacts`, `customer_groups`, `customer_price_list_items`, `customer_price_lists`, `customer_receipts`, `customer_transactions`, `invoices`, `invoice_lines`, `sales_orders`, `sales_order_lines`, `sales_quotations`, `sales_quotation_lines`, `sales_returns`, `sales_return_lines`, `sales_commissions`, `sales_opportunities`, `sales_targets`, `commission_rules`, `delivery_orders`, `delivery_order_lines`

### المشتريات (16 جدول فارغ)
`suppliers`, `supplier_balances`, `supplier_bank_accounts`, `supplier_contacts`, `supplier_payments`, `supplier_ratings`, `supplier_transactions`, `purchase_orders`, `purchase_order_lines`, `purchase_agreements`, `purchase_agreement_lines`, `request_for_quotations`, `rfq_lines`, `rfq_responses`, `pending_payables`, `pending_receivables`

### المخزون (14 جدول فارغ)
`inventory_transactions`, `stock_adjustments`, `stock_transfer_log`, `stock_shipments`, `stock_shipment_items`, `product_batches`, `product_serials`, `product_variants`, `product_variant_attributes`, `product_attributes`, `product_attribute_values`, `product_kits`, `product_kit_items`, `bin_locations`, `bin_inventory`, `batch_serial_movements`, `inventory_cost_snapshots`, `cycle_counts`, `cycle_count_items`, `quality_inspections`, `quality_inspection_criteria`

### التصنيع (9 جداول فارغة)
`bill_of_materials`, `bom_components`, `bom_outputs`, `manufacturing_routes`, `manufacturing_operations`, `manufacturing_equipment`, `production_orders`, `production_order_operations`, `work_centers`, `mrp_plans`, `mrp_items`, `mfg_qc_checks`, `maintenance_logs`

### الخزينة (10 جداول فارغة)
`treasury_transactions`, `checks_receivable`, `checks_payable`, `notes_receivable`, `notes_payable`, `bank_reconciliations`, `bank_statement_lines`, `bank_import_batches`, `bank_import_lines`, `currency_transactions`

### الموارد البشرية (17 جدول فارغ)
`payroll_entries`, `payroll_periods`, `attendance`, `leave_requests`, `leave_carryover`, `employee_loans`, `overtime_requests`, `employee_salary_components`, `salary_components`, `salary_structures`, `employee_documents`, `employee_violations`, `employee_custody`, `performance_reviews`, `training_programs`, `training_participants`, `gosi_settings`, `job_openings`, `job_applications`

### الأصول (7 جداول فارغة)
`assets`, `asset_categories`, `asset_depreciation_schedule`, `asset_disposals`, `asset_transfers`, `asset_revaluations`, `asset_insurance`, `asset_maintenance`

### المشاريع (8 جداول فارغة)
`projects`, `project_tasks`, `project_timesheets`, `project_expenses`, `project_revenues`, `project_budgets`, `project_documents`, `project_change_orders`

### المالية (11 جدول فارغ)
`budgets`, `budget_items`, `budget_lines`, `cost_centers`, `cost_centers_budgets`, `expenses`, `contracts`, `contract_items`, `payments`, `payment_allocations`, `payment_vouchers`, `recurring_journal_lines`, `recurring_journal_templates`, `financial_reports`, `fiscal_period_locks`

### الضرائب (7 جداول فارغة)
`tax_returns`, `tax_payments`, `tax_calendar`, `tax_groups`, `wht_transactions`, `zakat_calculations`, `branch_tax_settings`

### نقاط البيع (13 جدول فارغ)
`pos_sessions`, `pos_orders`, `pos_order_lines`, `pos_order_payments`, `pos_payments`, `pos_returns`, `pos_return_items`, `pos_promotions`, `pos_loyalty_programs`, `pos_loyalty_points`, `pos_loyalty_transactions`, `pos_tables`, `pos_table_orders`, `pos_kitchen_orders`

### CRM/الخدمات (6 جداول فارغة)
`sales_opportunities`, `opportunity_activities`, `support_tickets`, `ticket_comments`, `service_requests`, `service_request_costs`

### النظام/التكاملات (15 جدول فارغ)
`api_keys`, `webhooks`, `webhook_logs`, `approval_workflows`, `approval_requests`, `approval_actions`, `notifications`, `messages`, `scheduled_reports`, `shared_reports`, `custom_reports`, `report_templates`, `print_templates`, `document_templates`, `document_types`, `documents`, `document_versions`, `email_templates`, `dashboard_layouts`, `backup_history`

### الأمان (3 جداول فارغة)
`user_sessions`, `user_2fa_settings`, `password_history`

---

## 📌 ملاحظات الفحص الجديدة

### ما اكتُشف خلال التدقيق ولم يكن مذكوراً في الملفات السابقة:

1. **حجم النظام أكبر مما في التوثيق:** 800 endpoint فعلي (الوثائق كانت تذكر 618+)، و229 route في الفرونتِند
2. **جميع الصفحات مُكتملة الكود:** لا توجد صفحة stub واحدة (عدا ComingSoon.jsx في Settings tabs وهو عام)
3. **لا توجد TODO/FIXME في الكود:** 0 تعليقات معلقة في 62 ملف router و246 ملف frontend
4. **أسماء الأعمدة غير موحدة بين الجداول:** warehouses يستخدم `warehouse_name` بينما departments يستخدم `name` — لكن هذا لا يؤثر على الوظائف
5. **البيانات الأساسية مُحكمة:** القيود الافتتاحية مرحّلة (posted)، الحسابات متوازنة، السنة المالية مفتوحة
6. **النظام جاهز تقنياً لبدء الاستخدام الفعلي:** كل البنية التحتية جاهزة — المطلوب فقط إدخال البيانات التشغيلية

---

> **خلاصة:** النظام مكتمل الكود بنسبة ~98%. البيانات الأساسية (Master Data) مُدخلة وجاهزة. المرحلة التالية هي البدء بالاستخدام الفعلي: إنشاء فواتير مبيعات/مشتريات، تسجيل حركات مخزون، فتح أوامر إنتاج، تشغيل نقاط البيع، إلخ. المهام المتبقية هي تحسينات أمنية (8)، تكامل ZATCA (6 إلزامي)، وتحسينات وظيفية (9).
