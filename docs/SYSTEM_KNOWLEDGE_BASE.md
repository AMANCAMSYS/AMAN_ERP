# 📖 AMAN ERP — قاعدة المعرفة الشاملة للنظام
# SYSTEM KNOWLEDGE BASE

> **آخر تحديث:** 5 مارس 2026  
> **المُعدّ بواسطة:** تحليل كامل للكود المصدري (Backend + Frontend + Database) + فحص قاعدة البيانات + فحص شامل للتغييرات  
> **الغرض:** مرجع شامل يُغني عن إعادة الفحص — يحتوي على كل صفحة، كل API، كل جدول، كل قيد، كل تقرير  
> **حالة النظام:** البيانات الأساسية (Master Data) مكتملة — تم الترقية إلى ★★★★★ (Phase 7 مكتملة: إصلاحات الزكاة ZATCA + Responsive Design متكامل + Docker Production)

---

## 📍 حالة النظام الحالية — أين وصلنا؟

### النظام بالأرقام
| المقياس | القيمة |
|---------|--------|
| إجمالي الـ Endpoints (Backend) | **767** (392 GET + 244 POST + 79 PUT + 52 DELETE) |
| إجمالي الصفحات (Frontend) | **277 JSX** + ~270 route |
| إجمالي ملفات JS | **44** ملف |
| إجمالي الجداول | **244** (240 جدول شركة + 4 جداول نظام) |
| إجمالي سطور الكود (Backend) | **88,268** سطر Python |
| إجمالي سطور الكود (Frontend) | **98,760** سطر (JSX+JS+JSON) |
| ملفات الـ Router (Backend) | **73** ملف |
| ملفات الخدمات (Backend) | **7** ملفات (4,143 سطر) |
| ملفات الأدوات (Backend) | **15** ملف (3,007 سطر) |
| ملفات الـ Schema (Backend) | **22** ملف (2,031 سطر) |
| قوالب الصناعة | **12** نشاط (RT, WS, FB, MF, CN, SV, PH, WK, EC, LG, AG, GN) |
| ميزات مشروطة حسب النشاط | **16** قاعدة في INDUSTRY_FEATURES |
| الجداول المملوءة | 30 (بيانات أساسية) |
| الجداول الفارغة | ~214 (بيانات تشغيلية) |
| اكتمال الكود | ~100% (★★★★★) |

### ✅ ما تم إدخاله (البيانات الأساسية)
| البيان | العدد | التفاصيل |
|--------|-------|----------|
| المستخدمون | 10 | omar (مشرف) + 9 موظفين |
| الفروع | 3 | الرياض (HQ) + جدة + دبي |
| الأقسام | 7 | مالية، مبيعات، مشتريات، مستودعات، HR، إنتاج، POS |
| الوظائف | 8 | لكل قسم |
| الأدوار | 8 | admin, superuser, hr, accountant, sales, inventory, cashier, user |
| شجرة الحسابات | 121 | 40 أصول + 21 التزامات + 6 حقوق ملكية + 14 إيرادات + 40 مصاريف |
| المنتجات | 7 | ألمنيوم، خشب، باب، نافذة، مسامير، لابتوب، خدمة تركيب |
| فئات المنتجات | 5 | مواد خام، منتجات تامة، مستلزمات، خدمات، أصول ثابتة |
| وحدات القياس | 5 | قطعة، كيلوغرام، لتر، متر، صندوق |
| الأطراف | 11 | 6 عملاء + 5 موردون |
| مجموعات العملاء | 3 | جملة (5%) + تجزئة + خارجيين (3%) |
| مجموعات الموردون | 2 | محليون (30 يوم) + خارجيون (60 يوم) |
| المستودعات | 5 | رئيسي + مواد خام + تامة (الرياض) + جدة + دبي |
| حسابات الخزينة | 7 | 4 بنوك + 3 صناديق (أرصدة = 0) |
| العملات | 5 | SAR (أساسية) + USD + EUR + AED + EGP |
| أسعار الصرف | 4 | مُحدّثة |
| السنة المالية | 1 | 2026 (مفتوحة) |
| الفترات المالية | 12 | يناير - ديسمبر 2026 |
| ضريبة القيمة المضافة | 1 | 15% |
| معدلات الاستقطاع | 8 | خدمات، إيجار، استشارات... |
| القيود الافتتاحية | 8 | أرصدة بنوك + مخزون + أصول + ذمم |
| إعدادات الشركة | 79 | جميعها مُهيّأة |

### ❌ ما لم يُدخل بعد (190 جدول فارغ)
**لا توجد أي عمليات تشغيلية:** 0 فواتير، 0 أوامر بيع/شراء، 0 مدفوعات، 0 جلسات POS، 0 أوامر إنتاج، 0 مشاريع، 0 أصول، 0 رواتب، 0 حضور/إجازات، 0 حركات مخزون، 0 تسويات بنكية.

---

## 🗺️ خطة إدخال البيانات التشغيلية — بالترتيب

> **ابدأ من هنا:** البيانات الأساسية جاهزة — الخطوات التالية لبدء الاستخدام الفعلي

### المرحلة أ: المبيعات (الأولوية الأولى)
| الخطوة | الصفحة | المسار | ماذا تفعل |
|--------|--------|--------|-----------|
| 1 | إنشاء عرض سعر | `/sales/quotations/new` | اختر عميل + منتجات + أسعار |
| 2 | تحويل لأمر بيع | `/sales/orders` | تحويل العرض المقبول لأمر |
| 3 | إصدار فاتورة | `/sales/invoices/new` | فاتورة من أمر البيع |
| 4 | تسجيل مقبوض | `/sales/receipts/new` | تسجيل استلام المبلغ من العميل |
| 5 | أمر تسليم | `/sales/delivery-orders/new` | إنشاء أمر تسليم البضاعة |

### المرحلة ب: المشتريات
| الخطوة | الصفحة | المسار | ماذا تفعل |
|--------|--------|--------|-----------|
| 1 | طلب عرض سعر (RFQ) | `/buying/rfq` | إرسال طلب سعر للموردين |
| 2 | أمر شراء | `/buying/orders/new` | إنشاء أمر شراء |
| 3 | استلام البضاعة | `/buying/orders/:id/receive` | تسجيل استلام المواد |
| 4 | فاتورة شراء | `/buying/invoices/new` | تسجيل فاتورة المورد |
| 5 | دفع للمورد | `/buying/payments/new` | تسجيل الدفعة |

### المرحلة ج: المخزون
| الخطوة | الصفحة | المسار | ماذا تفعل |
|--------|--------|--------|-----------|
| 1 | تعديل أرصدة | `/stock/adjustments/new` | ضبط كميات المخزون الفعلية |
| 2 | تحويل مخزون | `/stock/transfer` | نقل بين المستودعات |
| 3 | شحنة واردة | `/stock/shipments/incoming` | تسجيل شحنة من مورد |

### المرحلة د: الخزينة
| الخطوة | الصفحة | المسار | ماذا تفعل |
|--------|--------|--------|-----------|
| 1 | مصروف | `/treasury/expense` | تسجيل مصروف من حساب خزينة |
| 2 | تحويل بين حسابات | `/treasury/transfer` | تحويل بين البنوك/الصناديق |
| 3 | تسوية بنكية | `/treasury/reconciliation` | مطابقة كشف البنك |

### المرحلة هـ: التصنيع (إذا كان مُفعّلاً)
| الخطوة | الصفحة | المسار | ماذا تفعل |
|--------|--------|--------|-----------|
| 1 | مراكز العمل | `/manufacturing/work-centers` | تعريف مراكز الإنتاج |
| 2 | مسارات الإنتاج | `/manufacturing/routes` | تعريف خطوات التصنيع |
| 3 | قائمة المواد (BOM) | `/manufacturing/boms` | تحديد مكونات المنتج |
| 4 | أمر إنتاج | `/manufacturing/orders` | بدء عملية التصنيع |

### المرحلة و: الموارد البشرية
| الخطوة | الصفحة | المسار | ماذا تفعل |
|--------|--------|--------|-----------|
| 1 | هياكل الرواتب | `/hr/salary-structures` | تعريف مكونات الراتب |
| 2 | تسجيل حضور | `/hr/attendance` | بدء تتبع الحضور |
| 3 | مسيرة رواتب | `/hr/payroll` | إنشاء وترحيل الرواتب الشهرية |
| 4 | طلبات إجازة | `/hr/leaves` | إدارة الإجازات |

### المرحلة ز: نقاط البيع (POS)
| الخطوة | الصفحة | المسار | ماذا تفعل |
|--------|--------|--------|-----------|
| 1 | فتح جلسة | `/pos/interface` | افتح جلسة POS + حدد المستودع |
| 2 | بيع مباشر | `/pos/interface` | أضف منتجات + اقبض المبلغ |
| 3 | إغلاق الجلسة | `/pos/interface` | إغلاق + مطابقة النقدية |

### المرحلة ح: المتقدمة
| الخطوة | الصفحة | المسار | ماذا تفعل |
|--------|--------|--------|-----------|
| 1 | الأصول الثابتة | `/assets/new` | تسجيل الأصول + جداول الإهلاك |
| 2 | المشاريع | `/projects/new` | إنشاء مشروع + مهام + ميزانية |
| 3 | الميزانيات | `/accounting/budgets` | وضع ميزانية سنوية |
| 4 | مراكز التكلفة | `/accounting/cost-centers` | تعريف مراكز التكلفة |
| 5 | العقود | `/sales/contracts/new` | إنشاء عقود مع العملاء |
| 6 | CRM | `/crm` | إدارة فرص المبيعات والدعم |

---

## 📑 فهرس المحتويات — Table of Contents

- [1. خريطة الصفحات والواجهات (Frontend Map)](#1-خريطة-الصفحات-والواجهات)
  - [1.1 لوحة التحكم (Dashboard)](#11-لوحة-التحكم)
  - [1.2 المحاسبة (Accounting)](#12-المحاسبة)
  - [1.3 المبيعات (Sales)](#13-المبيعات)
  - [1.4 المشتريات (Buying)](#14-المشتريات)
  - [1.5 المخزون (Stock/Inventory)](#15-المخزون)
  - [1.6 الخزينة (Treasury)](#16-الخزينة)
  - [1.7 الموارد البشرية (HR)](#17-الموارد-البشرية)
  - [1.8 الأصول الثابتة (Assets)](#18-الأصول-الثابتة)
  - [1.9 المشاريع (Projects)](#19-المشاريع)
  - [1.10 التصنيع (Manufacturing)](#110-التصنيع)
  - [1.11 نقاط البيع (POS)](#111-نقاط-البيع)
  - [1.12 المصروفات (Expenses)](#112-المصروفات)
  - [1.13 الضرائب (Taxes)](#113-الضرائب)
  - [1.14 CRM](#114-crm)
  - [1.15 الخدمات (Services)](#115-الخدمات)
  - [1.16 التقارير (Reports)](#116-التقارير)
  - [1.17 الموافقات (Approvals)](#117-الموافقات)
  - [1.18 الإدارة (Admin)](#118-الإدارة)
  - [1.19 الإعدادات (Settings)](#119-الإعدادات)
  - [1.20 استيراد البيانات (Data Import)](#120-استيراد-البيانات)
- [2. خريطة الـ Backend والـ API](#2-خريطة-الباكند-والـ-api)
- [3. خريطة قاعدة البيانات (Database Schema)](#3-خريطة-قاعدة-البيانات)
- [4. شجرة الحسابات (Chart of Accounts)](#4-شجرة-الحسابات)
- [5. القيود المحاسبية (Journal Entries)](#5-القيود-المحاسبية)
- [6. التقارير (Reports)](#6-التقارير)
- [7. الحركات والتأثيرات المتسلسلة (Transaction Flows)](#7-الحركات-والتأثيرات-المتسلسلة)
- [8. الصلاحيات والمستخدمون (Roles & Permissions)](#8-الصلاحيات-والمستخدمون)
- [9. الإعدادات والتهيئة (Settings & Configuration)](#9-الإعدادات-والتهيئة)
- [10. التكاملات الخارجية (Integrations)](#10-التكاملات-الخارجية)
- [11. الميزات الجديدة — Phase 4 (System Completion)](#11-الميزات-الجديدة)
- [12. الميزات الجديدة — Phase 5 (★★★★★ Upgrade)](#12-الميزات-الجديدة--phase-5-)
- [13. الميزات الجديدة — Phase 7 (Responsive + Zakat + DevOps)](#13-الميزات-الجديدة--phase-7-5-مارس-2026)

---

# 1. خريطة الصفحات والواجهات

## 1.1 لوحة التحكم

| الصفحة | المسار | الغرض | الصلاحية |
|--------|--------|--------|----------|
| Dashboard | `/dashboard` | لوحة تحكم رئيسية مع ودجات قابلة للتخصيص | `dashboard.view` |

**الودجات المتاحة:**
- ملخص المبيعات → `GET /dashboard/widgets/sales-summary`
- المنتجات الأكثر مبيعاً → `GET /dashboard/widgets/top-products`
- المخزون المنخفض → `GET /dashboard/widgets/low-stock`
- المهام المعلقة → `GET /dashboard/widgets/pending-tasks`
- التدفق النقدي → `GET /dashboard/widgets/cash-flow`
- رسوم بيانية مالية → `GET /dashboard/charts/financial`
- رسوم بيانية للمنتجات → `GET /dashboard/charts/products`

**الجداول المتأثرة:** `dashboard_layouts` (تخصيص المستخدم)

**الأزرار:**
| الزر | الوظيفة | API | التأثير |
|------|---------|-----|---------|
| حفظ التخطيط | حفظ ترتيب الودجات | `POST /dashboard/layouts` | يكتب في `dashboard_layouts` |
| تعديل التخطيط | تغيير الودجات المعروضة | `PUT /dashboard/layouts/{id}` | يحدّث `dashboard_layouts` |

---

## 1.2 المحاسبة

### الصفحة الرئيسية
| الصفحة | المسار | الغرض | الصلاحية |
|--------|--------|--------|----------|
| AccountingHome | `/accounting` | بوابة المحاسبة — روابط سريعة لكل الأقسام | `accounting.view` |

### شجرة الحسابات
| الصفحة | المسار | الغرض | الصلاحية |
|--------|--------|--------|----------|
| ChartOfAccounts | `/accounting/coa` | عرض / إنشاء / تعديل / حذف الحسابات | `accounting.view` |

**الأزرار:**
| الزر | الوظيفة | API | الجداول |
|------|---------|-----|---------|
| إنشاء حساب | إضافة حساب جديد | `POST /finance/accounting/accounts` | `accounts` |
| تعديل حساب | تحديث بيانات الحساب | `PUT /finance/accounting/accounts/{id}` | `accounts` |
| حذف حساب | حذف حساب (بشرط عدم وجود حركات) | `DELETE /finance/accounting/accounts/{id}` | `accounts` |

**الحقول:**
| الحقل | النوع | الجدول.العمود |
|-------|-------|--------------|
| رقم الحساب | text | `accounts.account_number` |
| رمز الحساب | text | `accounts.account_code` |
| اسم الحساب (عربي) | text | `accounts.name` |
| اسم الحساب (إنجليزي) | text | `accounts.name_en` |
| نوع الحساب | select (asset/liability/equity/revenue/expense) | `accounts.account_type` |
| الحساب الأب | select | `accounts.parent_id` |
| العملة | select | `accounts.currency` |
| نشط | boolean | `accounts.is_active` |

### القيود اليومية
| الصفحة | المسار | الغرض | الصلاحية |
|--------|--------|--------|----------|
| JournalEntryList | `/accounting/journal-entries` | قائمة القيود | `accounting.view` |
| JournalEntryForm | `/accounting/journal-entries/new` | إنشاء قيد يدوي | `accounting.view` |

**الأزرار:**
| الزر | الوظيفة | API | الجداول |
|------|---------|-----|---------|
| حفظ كمسودة | حفظ قيد بحالة draft | `POST /finance/accounting/journal-entries` | `journal_entries` + `journal_lines` |
| ترحيل | تغيير الحالة إلى posted | `POST /finance/accounting/journal-entries/{id}/post` | `journal_entries` + `accounts` (تحديث الأرصدة) |
| إلغاء/عكس | إنشاء قيد عكسي | `POST /finance/accounting/journal-entries/{id}/void` | `journal_entries` + `journal_lines` + `accounts` |

**الحقول:**
| الحقل | النوع | الجدول.العمود |
|-------|-------|--------------|
| رقم القيد | auto | `journal_entries.entry_number` |
| التاريخ | date | `journal_entries.entry_date` |
| المرجع | text | `journal_entries.reference` |
| الوصف | text | `journal_entries.description` |
| العملة | select | `journal_entries.currency` |
| سعر الصرف | number | `journal_entries.exchange_rate` |
| الفرع | select | `journal_entries.branch_id` |
| سطور القيد: الحساب | select | `journal_lines.account_id` |
| سطور القيد: مدين | number | `journal_lines.debit` |
| سطور القيد: دائن | number | `journal_lines.credit` |
| سطور القيد: مركز تكلفة | select | `journal_lines.cost_center_id` |
| سطور القيد: وصف | text | `journal_lines.description` |

### السنوات المالية
| الصفحة | المسار | الغرض | الصلاحية |
|--------|--------|--------|----------|
| FiscalYears | `/accounting/fiscal-years` | إدارة السنوات والفترات المالية | `accounting.view` |

**الأزرار:**
| الزر | الوظيفة | API | الجداول |
|------|---------|-----|---------|
| إنشاء سنة مالية | إضافة سنة جديدة | `POST /finance/accounting/fiscal-years` | `fiscal_years` + `fiscal_periods` |
| إقفال السنة | إقفال وترحيل الأرباح | `POST /finance/accounting/fiscal-years/{year}/close` | `fiscal_years` + `journal_entries` + `accounts` |
| إعادة فتح السنة | عكس قيد الإقفال | `POST /finance/accounting/fiscal-years/{year}/reopen` | `fiscal_years` + `journal_entries` |
| فتح/إغلاق فترة | تبديل حالة الفترة | `POST /finance/accounting/fiscal-periods/{id}/toggle-close` | `fiscal_periods` |

### القوالب المتكررة
| الصفحة | المسار | الغرض | الصلاحية |
|--------|--------|--------|----------|
| RecurringTemplates | `/accounting/recurring-templates` | قيود تلقائية دورية | `accounting.view` |

**الأزرار:**
| الزر | الوظيفة | API | الجداول |
|------|---------|-----|---------|
| إنشاء قالب | إضافة قالب متكرر | `POST /finance/accounting/recurring-templates` | `recurring_journal_templates` + `recurring_journal_lines` |
| توليد قيد | إنشاء قيد من القالب | `POST /finance/accounting/recurring-templates/{id}/generate` | `journal_entries` + `journal_lines` |
| توليد المستحقات | توليد كل القيود المستحقة | `POST /finance/accounting/recurring-templates/generate-due` | `journal_entries` + `journal_lines` |

### مقارنة الفترات
| الصفحة | المسار | الغرض | الصلاحية |
|--------|--------|--------|----------|
| PeriodComparison | `/accounting/period-comparison` | مقارنة أداء فترتين ماليتين | `accounting.view` |

### أرصدة افتتاحية
| الصفحة | المسار | الغرض | الصلاحية |
|--------|--------|--------|----------|
| OpeningBalances | `/accounting/opening-balances` | تسجيل الأرصدة الافتتاحية | `accounting.manage` |

**الأزرار:**
| الزر | الوظيفة | API | الجداول |
|------|---------|-----|---------|
| حفظ الأرصدة | إنشاء قيد أرصدة افتتاحية | `POST /finance/accounting/opening-balances` | `journal_entries` + `journal_lines` + `accounts` |

### قيود الإقفال
| الصفحة | المسار | الغرض | الصلاحية |
|--------|--------|--------|----------|
| ClosingEntries | `/accounting/closing-entries` | توليد قيود إقفال نهاية السنة | `accounting.manage` |

**الأزرار:**
| الزر | الوظيفة | API | الجداول |
|------|---------|-----|---------|
| معاينة | عرض قيود الإقفال قبل التنفيذ | `GET /finance/accounting/closing-entries/preview` | قراءة فقط |
| توليد قيود الإقفال | إنشاء 3 قيود (إيرادات، مصروفات، ملخص دخل) | `POST /finance/accounting/closing-entries/generate` | `journal_entries` + `journal_lines` + `accounts` |

### مراكز التكلفة
| الصفحة | المسار | الغرض | الصلاحية |
|--------|--------|--------|----------|
| CostCenterList | `/accounting/cost-centers` | إدارة مراكز التكلفة | `accounting.view` |

### الموازنات
| الصفحة | المسار | الغرض | الصلاحية |
|--------|--------|--------|----------|
| Budgets | `/accounting/budgets` | إدارة الموازنات | `accounting.view` |
| BudgetAdvanced | `/accounting/budgets/advanced` | موازنات متقدمة (متعددة السنوات، مقارنة) | `accounting.view` |
| BudgetItems | `/accounting/budgets/:id/items` | تفاصيل بنود الموازنة | `accounting.view` |
| BudgetReport | `/accounting/budgets/:id/report` | تقرير الموازنة مقابل الفعلي | `accounting.view` |

### التقارير المحاسبية (الصفحات)
| الصفحة | المسار | الغرض | الصلاحية |
|--------|--------|--------|----------|
| TrialBalance | `/accounting/trial-balance` | ميزان المراجعة | `accounting.view` |
| GeneralLedger | `/accounting/general-ledger` | دفتر الأستاذ العام | `accounting.view` |
| IncomeStatement | `/accounting/income-statement` | قائمة الدخل | `accounting.view` |
| BalanceSheet | `/accounting/balance-sheet` | الميزانية العمومية | `accounting.view` |
| VATReport | `/accounting/vat-report` | تقرير ضريبة القيمة المضافة | `accounting.view` |
| TaxAudit | `/accounting/tax-audit` | تقرير التدقيق الضريبي | `accounting.view` |
| CashFlowReport | `/accounting/cashflow` | قائمة التدفقات النقدية | `accounting.view` |
| CurrencyList | `/accounting/currencies` | إدارة العملات وأسعار الصرف | `currencies.view` |
| InventoryValuation | `/stock/valuation-report` | تقرير تقييم المخزون | `reports.view` |

### الزكاة وقفل الفترات (جديد — Phase 4)
| الصفحة | المسار | الغرض | الصلاحية |
|--------|--------|--------|----------|
| ZakatCalculator | `/accounting/zakat` | حساب الزكاة (طريقة GAZT + الربح المعدّل) | `accounting.zakat` |
| FiscalPeriodLocks | `/accounting/fiscal-locks` | قفل/فتح الفترات المحاسبية | `accounting.fiscal_locks` |

**الزكاة — الأزرار:**
| الزر | الوظيفة | API | القيد |
|------|---------|-----|-------|
| حساب | حساب وعاء الزكاة والزكاة المستحقة | `POST /system/zakat/calculate` | لا |
| ترحيل قيد الزكاة | إنشاء قيد محاسبي للزكاة | `POST /system/zakat/post-journal-entry` | ✅ Dr: مصروف زكاة → Cr: زكاة مستحقة |

---

## 1.3 المبيعات

### الصفحة الرئيسية
| الصفحة | المسار | الغرض | الصلاحية |
|--------|--------|--------|----------|
| SalesHome | `/sales` | بوابة المبيعات | `sales.view` |

### العملاء
| الصفحة | المسار | الغرض |
|--------|--------|--------|
| CustomerList | `/sales/customers` | قائمة العملاء |
| CustomerForm | `/sales/customers/new` | إنشاء عميل جديد |
| CustomerForm | `/sales/customers/:id/edit` | تعديل عميل |
| CustomerDetails | `/sales/customers/:id` | تفاصيل العميل + الحركات |
| CustomerGroups | `/sales/customer-groups` | مجموعات العملاء |

**الأزرار (العملاء):**
| الزر | الوظيفة | API | الجداول |
|------|---------|-----|---------|
| إنشاء عميل | إضافة عميل جديد | `POST /sales/customers` | `parties` (is_customer=true) + `customers` (legacy) |
| تعديل عميل | تحديث البيانات | `PUT /sales/customers/{id}` | `parties` + `customers` |
| فحص الائتمان | التحقق من حد الائتمان | `POST /sales/credit-check` | قراءة `parties` + `invoices` |
| تعديل حد الائتمان | تغيير الحد | `PUT /sales/customers/{id}/credit-limit` | `parties.credit_limit` |

### عروض الأسعار
| الصفحة | المسار | الغرض |
|--------|--------|--------|
| SalesQuotations | `/sales/quotations` | قائمة عروض الأسعار |
| SalesQuotationForm | `/sales/quotations/new` | إنشاء عرض سعر |
| SalesQuotationDetails | `/sales/quotations/:id` | تفاصيل عرض السعر |

**الأزرار:**
| الزر | الوظيفة | API | الجداول | التأثير |
|------|---------|-----|---------|---------|
| إنشاء عرض سعر | حفظ عرض جديد | `POST /sales/quotations` | `sales_quotations` + `sales_quotation_lines` | لا يؤثر على الحسابات |
| تحويل إلى أمر بيع | إنشاء أمر بيع من العرض | `POST /sales/quotations/{id}/convert` | `sales_orders` + `sales_order_lines` | تغيير حالة العرض |

### أوامر البيع
| الصفحة | المسار | الغرض |
|--------|--------|--------|
| SalesOrders | `/sales/orders` | قائمة أوامر البيع |
| SalesOrderForm | `/sales/orders/new` | إنشاء أمر بيع |
| SalesOrderDetails | `/sales/orders/:id` | تفاصيل أمر البيع |

**الأزرار:**
| الزر | الوظيفة | API | الجداول |
|------|---------|-----|---------|
| إنشاء أمر بيع | حفظ أمر جديد | `POST /sales/orders` | `sales_orders` + `sales_order_lines` |
| فوترة جزئية | إنشاء فاتورة من جزء من الأمر | `POST /sales/orders/{id}/partial-invoice` | `invoices` + `invoice_lines` + `journal_entries` |

### الفواتير
| الصفحة | المسار | الغرض |
|--------|--------|--------|
| InvoiceList | `/sales/invoices` | قائمة فواتير البيع |
| InvoiceForm | `/sales/invoices/new` | إنشاء فاتورة بيع |
| InvoiceDetails | `/sales/invoices/:id` | تفاصيل الفاتورة |

**الأزرار:**
| الزر | الوظيفة | API | الجداول | القيد التلقائي |
|------|---------|-----|---------|---------------|
| إنشاء فاتورة | حفظ وترحيل الفاتورة | `POST /sales/invoices` | `invoices` + `invoice_lines` + `journal_entries` + `journal_lines` + `accounts` + `party_transactions` + `inventory` + `inventory_transactions` | ✅ Dr: نقد/بنك/عملاء، COGS → Cr: إيرادات مبيعات، ضريبة مخرجات، مخزون |
| إلغاء فاتورة | إبطال الفاتورة وعكس القيد | `POST /sales/invoices/{id}/cancel` | `invoices` + `journal_entries` + `accounts` + `inventory` | ✅ عكس القيد الأصلي |
| طباعة | نافذة طباعة الفاتورة | — | — | لا (عرض فقط) |

### المرتجعات
| الصفحة | المسار | الغرض |
|--------|--------|--------|
| SalesReturns | `/sales/returns` | قائمة مرتجعات المبيعات |
| SalesReturnForm | `/sales/returns/new` | إنشاء مرتجع |
| SalesReturnDetails | `/sales/returns/:id` | تفاصيل المرتجع |

**الأزرار:**
| الزر | الوظيفة | API | الجداول | القيد التلقائي |
|------|---------|-----|---------|---------------|
| إنشاء مرتجع | حفظ المرتجع | `POST /sales/returns` | `sales_returns` + `sales_return_lines` | لا (حتى الموافقة) |
| موافقة | اعتماد المرتجع وتنفيذه | `POST /sales/returns/{id}/approve` | `sales_returns` + `journal_entries` + `inventory` + `accounts` | ✅ Dr: إيرادات (عكس)، مخزون → Cr: نقد/عملاء، COGS (عكس) |

### سندات القبض والصرف
| الصفحة | المسار | الغرض |
|--------|--------|--------|
| CustomerReceipts | `/sales/receipts` | قائمة سندات القبض |
| ReceiptForm | `/sales/receipts/new` | إنشاء سند قبض |
| ReceiptDetails | `/sales/receipts/:id` | تفاصيل السند |

**الأزرار:**
| الزر | الوظيفة | API | الجداول | القيد التلقائي |
|------|---------|-----|---------|---------------|
| إنشاء سند قبض | تسجيل تحصيل | `POST /sales/receipts` | `payment_vouchers` + `payment_allocations` + `journal_entries` + `accounts` + `party_transactions` | ✅ Dr: نقد/بنك → Cr: العملاء (ذمم مدينة) |
| إنشاء سند صرف | تسجيل رد للعميل | `POST /sales/payments` | `payment_vouchers` + `journal_entries` + `accounts` | ✅ Dr: العملاء → Cr: نقد/بنك |

### إشعارات الخصم والائتمان
| الصفحة | المسار | الغرض |
|--------|--------|--------|
| SalesCreditNotes | `/sales/credit-notes` | إشعارات دائنة (خصم للعميل) |
| SalesDebitNotes | `/sales/debit-notes` | إشعارات مدينة (إضافة على العميل) |

**الأزرار:**
| الزر | الوظيفة | API | القيد |
|------|---------|-----|-------|
| إنشاء إشعار دائن | خصم من رصيد العميل | `POST /sales/credit-notes` | ✅ Dr: إيرادات (عكس)، ضريبة (عكس) → Cr: العملاء |
| إنشاء إشعار مدين | إضافة على رصيد العميل | `POST /sales/debit-notes` | ✅ Dr: العملاء → Cr: إيرادات، ضريبة |

### العمولات
| الصفحة | المسار | الغرض |
|--------|--------|--------|
| SalesCommissions | `/sales/commissions` | إدارة عمولات المبيعات |

**الأزرار:**
| الزر | الوظيفة | API | الجداول |
|------|---------|-----|---------|
| إنشاء قاعدة عمولة | تحديد نسبة العمولة | `POST /sales/commissions/rules` | `commission_rules` |
| احتساب العمولات | حساب عمولات الفترة | `POST /sales/commissions/calculate` | `sales_commissions` |
| صرف العمولات | دفع العمولات المستحقة | `POST /sales/commissions/pay` | ✅ Dr: مصروف عمولات → Cr: بنك/نقد |

### العقود
| الصفحة | المسار | الغرض |
|--------|--------|--------|
| ContractList | `/sales/contracts` | قائمة العقود |
| ContractForm | `/sales/contracts/new` | إنشاء عقد |
| ContractDetails | `/sales/contracts/:id` | تفاصيل العقد |

**الأزرار:**
| الزر | الوظيفة | API | الجداول |
|------|---------|-----|---------|
| إنشاء عقد | حفظ عقد جديد | `POST /contracts` | `contracts` + `contract_items` |
| تجديد | تجديد العقد | `POST /contracts/{id}/renew` | `contracts` |
| إنشاء فاتورة من العقد | فوترة تلقائية | `POST /contracts/{id}/generate-invoice` | `invoices` + `journal_entries` |
| إلغاء العقد | إلغاء | `POST /contracts/{id}/cancel` | `contracts` |

### أوامر التسليم — Delivery Orders (جديد — Phase 4)
| الصفحة | المسار | الغرض | الصلاحية |
|--------|--------|--------|----------|
| DeliveryOrders | `/sales/delivery-orders` | قائمة أوامر التسليم مع فلتر الحالة | `sales.delivery_orders` |
| DeliveryOrderDetails | `/sales/delivery-orders/:id` | تفاصيل + تأكيد/تسليم/فاتورة/إلغاء | `sales.delivery_orders` |
| DeliveryOrderForm | `/sales/delivery-orders/new` | إنشاء من أمر بيع أو يدويًا | `sales.delivery_orders` |

**الأزرار:**
| الزر | الوظيفة | API | القيد |
|------|---------|-----|-------|
| إنشاء أمر تسليم | إنشاء DO من أمر بيع أو يدويًا | `POST /sales/delivery-orders` | لا |
| تأكيد | تأكيد الأمر | `POST /sales/delivery-orders/{id}/confirm` | لا |
| تسليم | تسجيل التسليم | `POST /sales/delivery-orders/{id}/deliver` | لا |
| إنشاء فاتورة | فاتورة أمر التسليم | `POST /sales/delivery-orders/{id}/invoice` | ✅ Dr: عملاء، COGS → Cr: إيرادات، ضريبة، مخزون |
| إلغاء | إلغاء الأمر | `POST /sales/delivery-orders/{id}/cancel` | لا |

**الجداول:** `delivery_orders`, `delivery_order_lines`

### تقارير المبيعات
| الصفحة | المسار | الغرض |
|--------|--------|--------|
| SalesReports | `/sales/reports/analytics` | تحليلات المبيعات |
| CustomerStatement | `/sales/reports/customer-statement` | كشف حساب العميل |
| AgingReport | `/sales/reports/aging` | تقرير أعمار الديون |

---

## 1.4 المشتريات

### الصفحة الرئيسية
| الصفحة | المسار | الغرض | الصلاحية |
|--------|--------|--------|----------|
| BuyingHome | `/buying` | بوابة المشتريات | `buying.view` |

### الموردون
| الصفحة | المسار | الغرض |
|--------|--------|--------|
| SupplierList | `/buying/suppliers` | قائمة الموردين |
| SupplierForm | `/buying/suppliers/new` | إنشاء مورد |
| SupplierDetails | `/buying/suppliers/:id` | تفاصيل المورد |
| SupplierGroups | `/buying/supplier-groups` | مجموعات الموردين |

### طلبات الشراء
| الصفحة | المسار | الغرض |
|--------|--------|--------|
| BuyingOrders | `/buying/orders` | قائمة طلبات الشراء |
| BuyingOrderForm | `/buying/orders/new` | إنشاء طلب شراء |
| BuyingOrderDetails | `/buying/orders/:id` | تفاصيل الطلب |
| PurchaseOrderReceive | `/buying/orders/:id/receive` | استلام بضاعة |

**الأزرار:**
| الزر | الوظيفة | API | الجداول | القيد |
|------|---------|-----|---------|-------|
| إنشاء طلب شراء | حفظ الطلب | `POST /purchases/orders` | `purchase_orders` + `purchase_order_lines` | لا |
| اعتماد الطلب | تأكيد الطلب | `PUT /purchases/orders/{id}/approve` | `purchase_orders` | لا |
| استلام البضاعة | تسجيل استلام | `POST /purchases/orders/{id}/receive` | `purchase_order_lines` + `inventory` + `inventory_transactions` + `journal_entries` | ✅ Dr: مخزون → Cr: ذمم دائنة |

### فواتير المشتريات
| الصفحة | المسار | الغرض |
|--------|--------|--------|
| PurchaseInvoiceList | `/buying/invoices` | قائمة فواتير المشتريات |
| PurchaseInvoiceForm | `/buying/invoices/new` | إنشاء فاتورة شراء |
| PurchaseInvoiceDetails | `/buying/invoices/:id` | تفاصيل الفاتورة |

**الأزرار:**
| الزر | الوظيفة | API | القيد |
|------|---------|-----|-------|
| إنشاء فاتورة شراء | حفظ وترحيل | `POST /purchases/invoices` | ✅ Dr: مخزون/مصروف، ضريبة مدخلات → Cr: ذمم دائنة/نقد |

### مرتجعات المشتريات
| الصفحة | المسار | الغرض |
|--------|--------|--------|
| BuyingReturns | `/buying/returns` | قائمة المرتجعات |
| BuyingReturnForm | `/buying/returns/new` | إنشاء مرتجع |
| BuyingReturnDetails | `/buying/returns/:id` | تفاصيل المرتجع |

**الأزرار:**
| الزر | الوظيفة | API | القيد |
|------|---------|-----|-------|
| إنشاء مرتجع | إرجاع بضاعة للمورد | `POST /purchases/returns` | ✅ Dr: ذمم دائنة → Cr: مخزون، ضريبة مدخلات (عكس) |

### دفعات الموردين
| الصفحة | المسار | الغرض |
|--------|--------|--------|
| SupplierPayments | `/buying/payments` | قائمة دفعات الموردين |
| PaymentForm | `/buying/payments/new` | إنشاء سند صرف |
| PaymentDetails | `/buying/payments/:id` | تفاصيل الدفعة |

**الأزرار:**
| الزر | الوظيفة | API | القيد |
|------|---------|-----|-------|
| إنشاء سند صرف | دفع للمورد | `POST /purchases/payments` | ✅ Dr: ذمم دائنة → Cr: نقد/بنك |

### إشعارات دائنة/مدينة
| الصفحة | المسار | الغرض |
|--------|--------|--------|
| PurchaseCreditNotes | `/buying/credit-notes` | إشعارات دائنة (خصم من المورد) |
| PurchaseDebitNotes | `/buying/debit-notes` | إشعارات مدينة (إضافة على المورد) |

### طلبات عروض الأسعار (RFQ)
| الصفحة | المسار | الغرض |
|--------|--------|--------|
| RFQList | `/buying/rfq` | طلبات عروض أسعار من الموردين |

### تقييم الموردين
| الصفحة | المسار | الغرض |
|--------|--------|--------|
| SupplierRatings | `/buying/supplier-ratings` | تقييم أداء الموردين |

### اتفاقيات الشراء
| الصفحة | المسار | الغرض |
|--------|--------|--------|
| PurchaseAgreements | `/buying/agreements` | اتفاقيات الشراء الإطارية |

### التكاليف المحمّلة — Landed Costs (جديد — Phase 4)
| الصفحة | المسار | الغرض | الصلاحية |
|--------|--------|--------|----------|
| LandedCosts | `/buying/landed-costs` | قائمة التكاليف المحمّلة + إنشاء | `buying.landed_costs` |
| LandedCostDetails | `/buying/landed-costs/:id` | تفاصيل + توزيع + ترحيل | `buying.landed_costs` |

**الأزرار:**
| الزر | الوظيفة | API | القيد |
|------|---------|-----|-------|
| إنشاء تكلفة محمّلة | إنشاء LC مع بنود التكلفة | `POST /purchases/landed-costs` | لا |
| توزيع التكاليف | توزيع بـ 4 طرق (بالقيمة/بالكمية/بالوزن/بالتساوي) | `POST /purchases/landed-costs/{id}/allocate` | لا |
| ترحيل | ترحيل القيد المحاسبي | `POST /purchases/landed-costs/{id}/post` | ✅ Dr: مخزون → Cr: ذمم دائنة/مصروف |

**الجداول:** `landed_costs`, `landed_cost_items`, `landed_cost_allocations`

### تقارير المشتريات
| الصفحة | المسار | الغرض |
|--------|--------|--------|
| BuyingReports | `/buying/reports/analytics` | تحليلات المشتريات |
| SupplierStatement | `/buying/reports/supplier-statement` | كشف حساب المورد |

---

## 1.5 المخزون

| الصفحة | المسار | الغرض | الصلاحية |
|--------|--------|--------|----------|
| StockHome | `/stock` | بوابة المخزون | `stock.view` |
| ProductList | `/stock/products` | قائمة المنتجات | `stock.view` |
| ProductForm | `/stock/products/new` | إنشاء منتج | `stock.view` |
| ProductForm | `/stock/products/:id` | تعديل منتج | `stock.view` |
| CategoryList | `/stock/categories` | التصنيفات | `stock.view` |
| WarehouseList | `/stock/warehouses` | المستودعات | `stock.view` |
| WarehouseDetails | `/stock/warehouses/:id` | تفاصيل مستودع + الأرصدة | `stock.view` |
| StockTransferForm | `/stock/transfer` | تحويل مخزون بين مستودعات | `stock.view` |
| StockAdjustments | `/stock/adjustments` | تسويات المخزون | `stock.view` |
| StockAdjustmentForm | `/stock/adjustments/new` | إنشاء تسوية | `stock.view` |
| ShipmentList | `/stock/shipments` | قائمة الشحنات | `stock.view` |
| StockShipmentForm | `/stock/shipments/new` | إنشاء شحنة | `stock.view` |
| IncomingShipments | `/stock/shipments/incoming` | شحنات واردة | `stock.view` |
| ShipmentDetails | `/stock/shipments/:id` | تفاصيل شحنة | `stock.view` |
| PriceLists | `/stock/price-lists` | قوائم الأسعار | `stock.view` |
| PriceListItems | `/stock/price-lists/:id` | بنود قائمة الأسعار | `stock.view` |
| BatchList | `/stock/batches` | أرقام الدُفعات | `stock.view` |
| SerialList | `/stock/serials` | الأرقام التسلسلية | `stock.view` |
| QualityInspections | `/stock/quality` | فحوصات الجودة | `stock.view` |
| CycleCounts | `/stock/cycle-counts` | الجرد الدوري | `stock.view` |
| StockReports | `/stock/reports/balance` | تقرير أرصدة المخزون | `stock.reports` |
| StockMovements | `/stock/reports/movements` | حركات المخزون | `stock.reports` |

**أزرار رئيسية:**
| الزر | الوظيفة | API | القيد |
|------|---------|-----|-------|
| تحويل مخزون | نقل بين مستودعات | `POST /inventory/transfer` | ✅ Dr: مخزون المستودع المستلم → Cr: مخزون المستودع المصدر |
| تسوية مخزون | تعديل الكمية | `POST /inventory/adjustments` | ✅ Dr/Cr: مخزون ↔ مصروف تسوية |
| منتج جديد | إضافة صنف | `POST /inventory/products` | `products` |

---

## 1.6 الخزينة

| الصفحة | المسار | الغرض | الصلاحية |
|--------|--------|--------|----------|
| TreasuryHome | `/treasury` | بوابة الخزينة | `treasury.view` |
| TreasuryAccountList | `/treasury/accounts` | حسابات الخزينة (صندوق/بنك) | `treasury.view` |
| ExpenseForm | `/treasury/expense` | صرف مصروف من الخزينة | `treasury.view` |
| TransferForm | `/treasury/transfer` | تحويل بين حسابات الخزينة | `treasury.view` |
| ReconciliationList | `/treasury/reconciliation` | قائمة المطابقات البنكية | `reconciliation.view` |
| ReconciliationForm | `/treasury/reconciliation/:id` | نموذج المطابقة | `reconciliation.view` |
| TreasuryBalancesReport | `/treasury/reports/balances` | تقرير أرصدة الخزينة | `treasury.view` |
| TreasuryCashflowReport | `/treasury/reports/cashflow` | تقرير التدفق النقدي | `treasury.view` |
| ChecksReceivable | `/treasury/checks-receivable` | شيكات تحت التحصيل | `treasury.view` |
| ChecksPayable | `/treasury/checks-payable` | شيكات تحت الدفع | `treasury.view` |
| NotesReceivable | `/treasury/notes-receivable` | أوراق القبض | `treasury.view` |
| NotesPayable | `/treasury/notes-payable` | أوراق الدفع | `treasury.view` |

**أزرار الخزينة:**
| الزر | الوظيفة | API | القيد |
|------|---------|-----|-------|
| إنشاء حساب خزينة | صندوق/بنك جديد | `POST /finance/treasury/accounts` | ✅ إذا كان هناك رصيد ابتدائي |
| مصروف | صرف من الخزينة | `POST /finance/treasury/transactions/expense` | ✅ Dr: مصروف → Cr: خزينة |
| تحويل | تحويل بين حسابات | `POST /finance/treasury/transactions/transfer` | ✅ Dr: خزينة مستلمة → Cr: خزينة مرسلة |

**أزرار الشيكات:**
| الزر | الوظيفة | API | القيد |
|------|---------|-----|-------|
| إنشاء شيك مستلم | تسجيل شيك من عميل | `POST /finance/checks/receivable` | ✅ Dr: شيكات تحت التحصيل → Cr: العملاء |
| تحصيل شيك | إيداع في البنك | `POST /finance/checks/receivable/{id}/collect` | ✅ Dr: بنك → Cr: شيكات تحت التحصيل |
| ارتداد شيك | شيك مرتد | `POST /finance/checks/receivable/{id}/bounce` | ✅ عكس التحصيل + Dr: شيكات مرتدة |
| إصدار شيك | شيك للمورد | `POST /finance/checks/payable` | ✅ Dr: الموردين → Cr: شيكات تحت الدفع |
| مقاصة شيك | خصم من البنك | `POST /finance/checks/payable/{id}/clear` | ✅ Dr: شيكات تحت الدفع → Cr: بنك |

**أزرار أوراق القبض/الدفع:**
| الزر | الوظيفة | API | القيد |
|------|---------|-----|-------|
| إنشاء ورقة قبض | تسجيل كمبيالة | `POST /finance/notes/receivable` | ✅ Dr: أوراق قبض → Cr: العملاء |
| تحصيل | استلام المبلغ | `POST /finance/notes/receivable/{id}/collect` | ✅ Dr: بنك → Cr: أوراق قبض |
| بروتستو | احتجاج الورقة | `POST /finance/notes/receivable/{id}/protest` | ✅ Dr: أوراق مبروتستة → Cr: أوراق قبض |
| إنشاء ورقة دفع | إصدار كمبيالة | `POST /finance/notes/payable` | ✅ Dr: الموردين → Cr: أوراق دفع |
| سداد | دفع الورقة | `POST /finance/notes/payable/{id}/pay` | ✅ Dr: أوراق دفع → Cr: بنك |

### استيراد كشف البنك — Bank Import (جديد — Phase 4)
| الصفحة | المسار | الغرض | الصلاحية |
|--------|--------|--------|----------|
| BankImport | `/treasury/bank-import` | رفع CSV كشف بنكي + مطابقة تلقائية | `treasury.bank_import` |

**الأزرار:**
| الزر | الوظيفة | API | الجداول |
|------|---------|-----|---------|
| رفع CSV | رفع ملف كشف بنكي | `POST /system/bank-import/upload` | `bank_import_batches` + `bank_import_lines` |
| مطابقة تلقائية | مطابقة مع قيود الخزينة | `POST /system/bank-import/batches/{id}/auto-match` | `bank_import_lines` |

---

## 1.7 الموارد البشرية

| الصفحة | المسار | الغرض | الصلاحية |
|--------|--------|--------|----------|
| HRHome | `/hr` | بوابة الموارد البشرية | `hr.view` |
| Employees | `/hr/employees` | إدارة الموظفين | `hr.view` |
| DepartmentList | `/hr/departments` | الأقسام | `hr.view` |
| PositionList | `/hr/positions` | المناصب | `hr.view` |
| PayrollList | `/hr/payroll` | مسيرات الرواتب | `hr.view` |
| PayrollDetails | `/hr/payroll/:id` | تفاصيل المسير | `hr.view` |
| LoanList | `/hr/loans` | سلف الموظفين | `hr.view` |
| LeaveList | `/hr/leaves` | طلبات الإجازات | `hr.view` |
| Attendance | `/hr/attendance` | الحضور والانصراف | `hr.view` |
| SalaryStructures | `/hr/salary-structures` | هياكل الرواتب | `hr.view` |
| OvertimeRequests | `/hr/overtime` | العمل الإضافي | `hr.view` |
| GOSISettings | `/hr/gosi` | إعدادات التأمينات الاجتماعية | `hr.view` |
| EmployeeDocuments | `/hr/documents` | وثائق الموظفين | `hr.view` |
| PerformanceReviews | `/hr/performance` | تقييم الأداء | `hr.view` |
| TrainingPrograms | `/hr/training` | البرامج التدريبية | `hr.view` |
| Violations | `/hr/violations` | المخالفات والجزاءات | `hr.view` |
| CustodyManagement | `/hr/custody` | العهد والممتلكات | `hr.view` |
| Payslips | `/hr/payslips` | قسائم الرواتب (PDF) | `hr.view` |
| LeaveCarryover | `/hr/leave-carryover` | ترحيل رصيد الإجازات | `hr.view` |
| Recruitment | `/hr/recruitment` | التوظيف والاستقطاب | `hr.view` |
| HRReports | `/hr/reports` | تقارير الموارد البشرية | `hr.reports` |
| WPSExport | `/hr/wps` | تصدير ملف WPS (SIF) — خاص بالسعودية 🇸🇦 | `hr.wps` |
| SaudizationDashboard | `/hr/saudization` | لوحة السعودة ونطاقات — خاص بالسعودية 🇸🇦 | `hr.saudization` |
| EOSSettlement | `/hr/eos-settlement` | تسوية نهاية الخدمة (نظام العمل السعودي مواد 84/85) | `hr.eos` |

**صفحات جديدة (Phase 4) — WPS / السعودة / نهاية الخدمة:**
| الزر | الوظيفة | API | القيد |
|------|---------|-----|-------|
| تصدير SIF | تصدير ملف WPS بصيغة SIF | `POST /hr/wps/export-sif` | لا (ملف فقط) |
| معاينة | معاينة بيانات WPS قبل التصدير | `POST /hr/wps/preview` | لا |
| عرض السعودة | بيانات نسبة السعودة ونطاقات | `GET /hr/saudization/dashboard` | لا |
| تسوية نهاية الخدمة | حساب مكافأة نهاية الخدمة | `POST /hr/eos/calculate` | ✅ Dr: مكافأة نهاية خدمة → Cr: بنك/نقد |

**الجداول:** `employees` (iban, nationality مُستخدمة)

**أزرار رئيسية:**
| الزر | الوظيفة | API | القيد |
|------|---------|-----|-------|
| اعتماد سلفة | الموافقة على سلفة | `PUT /hr/loans/{id}/approve` | ✅ Dr: سلف موظفين → Cr: نقد |
| توليد المسير | حساب الرواتب للفترة | `POST /hr/payroll-periods/{id}/generate` | لا (تحضير فقط) |
| ترحيل المسير | تأكيد وترحيل الرواتب | `POST /hr/payroll-periods/{id}/post` | ✅ Dr: رواتب (إجمالي)، تأمينات صاحب عمل → Cr: تأمينات مستحقة، سلف، جزاءات، خصومات، بنك (صافي) |

---

## 1.8 الأصول الثابتة

| الصفحة | المسار | الغرض | الصلاحية |
|--------|--------|--------|----------|
| AssetList | `/assets` | قائمة الأصول | `assets.view` |
| AssetForm | `/assets/new` | إنشاء أصل | `assets.view` |
| AssetDetails | `/assets/:id` | تفاصيل الأصل | `assets.view` |
| AssetManagement | `/assets/management` | إدارة متقدمة (إعادة تقييم، تأمين، صيانة) | `assets.view` |

**أزرار رئيسية:**
| الزر | الوظيفة | API | القيد |
|------|---------|-----|-------|
| إنشاء أصل | تسجيل أصل جديد | `POST /finance/assets` | ✅ Dr: أصول ثابتة → Cr: نقد/بنك |
| إهلاك | تسجيل قسط إهلاك | `POST /finance/assets/{id}/depreciate/{schedule_id}` | ✅ Dr: مصروف إهلاك → Cr: إهلاك متراكم |
| استبعاد | بيع أو إتلاف الأصل | `POST /finance/assets/{id}/dispose` | ✅ Dr: إهلاك متراكم + نقد (ثمن البيع) + خسارة → Cr: تكلفة الأصل + ربح |
| تحويل بين فروع | نقل أصل لفرع آخر | `POST /finance/assets/{id}/transfer` | ✅ Dr: أصل فرع المستلم → Cr: أصل فرع المرسل |
| إعادة تقييم | تعديل القيمة السوقية | `POST /finance/assets/{id}/revalue` | ✅ Dr: أصل (زيادة) → Cr: احتياطي إعادة تقييم |

---

## 1.9 المشاريع

| الصفحة | المسار | الغرض | الصلاحية |
|--------|--------|--------|----------|
| ProjectList | `/projects` | قائمة المشاريع | `projects.view` |
| ProjectForm | `/projects/new` | إنشاء مشروع | `projects.create` |
| ProjectDetails | `/projects/:id` | تفاصيل المشروع (مهام، مالية، مستندات) | `projects.view` |
| ResourceManagement | `/projects/resources` | إدارة الموارد | `projects.view` |
| ProjectFinancialsReport | `/projects/reports/financials` | تقرير مالي للمشروع | `projects.view` |
| ResourceUtilizationReport | `/projects/reports/resources` | تقرير استخدام الموارد | `projects.view` |

**أزرار رئيسية:**
| الزر | الوظيفة | API | القيد |
|------|---------|-----|-------|
| إضافة مصروف | مصروف مشروع | `POST /projects/{id}/expenses` | ✅ Dr: مصروف مشروع → Cr: نقد/بنك |
| إضافة إيراد | إيراد مشروع | `POST /projects/{id}/revenues` | ✅ Dr: نقد/عملاء → Cr: إيراد مشروع |
| إنشاء فاتورة مشروع | فوترة المشروع | `POST /projects/{id}/create-invoice` | ✅ Dr: عملاء → Cr: إيراد مشروع |
| إقفال المشروع | إقفال والاعتراف بالإيراد المتبقي | `POST /projects/{id}/close` | ✅ إن وجد إيراد غير مُعترف به |
| فاتورة دفعة مقدمة | Retainer | `POST /projects/retainer/generate-invoices` | ✅ Dr: عملاء → Cr: إيراد مؤجل |

---

## 1.10 التصنيع

| الصفحة | المسار | الغرض | الصلاحية |
|--------|--------|--------|----------|
| ManufacturingHome | `/manufacturing` | بوابة التصنيع | `manufacturing.view` |
| WorkCenters | `/manufacturing/work-centers` | مراكز العمل | `manufacturing.view` |
| Routings | `/manufacturing/routes` | مسارات التصنيع | `manufacturing.view` |
| BOMs | `/manufacturing/boms` | قوائم المواد (BOM) | `manufacturing.view` |
| ProductionOrders | `/manufacturing/orders` | أوامر الإنتاج | `manufacturing.view` |
| ProductionOrderDetails | `/manufacturing/orders/:id` | تفاصيل أمر الإنتاج | `manufacturing.view` |
| JobCards | `/manufacturing/job-cards` | بطاقات العمل | `manufacturing.view` |
| MRPPlanning | `/manufacturing/mrp` | تخطيط احتياجات المواد | `manufacturing.view` |
| MRPView | `/manufacturing/mrp/:id` | عرض خطة MRP | `manufacturing.view` |
| EquipmentMaintenance | `/manufacturing/equipment` | المعدات والصيانة | `manufacturing.view` |
| ProductionSchedule | `/manufacturing/schedule` | جدول الإنتاج | `manufacturing.view` |
| DirectLaborReport | `/manufacturing/reports/direct-labor` | تقرير العمالة المباشرة | `manufacturing.view` |
| ProductionAnalytics | `/manufacturing/reports/analytics` | تحليلات الإنتاج | `manufacturing.view` |
| WorkOrderStatusReport | `/manufacturing/reports/work-orders` | تقرير حالة أوامر الإنتاج | `manufacturing.view` |
| ManufacturingCosting | `/manufacturing/costing` | حساب تكاليف الإنتاج + تقرير الانحرافات | `manufacturing.costing` |

**أزرار رئيسية:**
| الزر | الوظيفة | API | القيد |
|------|---------|-----|-------|
| بدء الإنتاج | صرف مواد أولية | `POST /manufacturing/orders/{id}/start` | ✅ Dr: أعمال تحت التشغيل (WIP) → Cr: مخزون مواد أولية |
| إتمام الإنتاج | استلام المنتج التام | `POST /manufacturing/orders/{id}/complete` | ✅ Dr: مخزون إنتاج تام → Cr: أعمال تحت التشغيل (WIP) |
| حساب التكلفة | حساب تكلفة أمر الإنتاج | `POST /manufacturing/calculate-cost` | لا |
| تقرير الانحرافات | مقارنة التكلفة التقديرية بالفعلية | `GET /manufacturing/cost-variance-report` | لا |

---

## 1.11 نقاط البيع

| الصفحة | المسار | الغرض | الصلاحية |
|--------|--------|--------|----------|
| POSHome | `/pos` | بوابة نقطة البيع | `pos.view` |
| POSInterface | `/pos/interface` | واجهة البيع السريع | `pos.sessions` |
| Promotions | `/pos/promotions` | العروض الترويجية | `pos.view` |
| LoyaltyPrograms | `/pos/loyalty` | برامج الولاء | `pos.view` |
| TableManagement | `/pos/tables` | إدارة الطاولات (مطاعم) | `pos.view` |
| KitchenDisplay | `/pos/kitchen` | شاشة المطبخ | `pos.view` |
| POSOfflineManager | `/pos/offline` | إدارة العمل بدون إنترنت | `pos.view` |
| ThermalPrintSettings | `/pos/thermal` | إعدادات الطباعة الحرارية | `pos.view` |
| CustomerDisplay | `/pos/customer-display` | شاشة العميل | `pos.view` |

**أزرار واجهة POS:**
| الزر | الوظيفة | API | القيد |
|------|---------|-----|-------|
| فتح وردية | بدء جلسة بيع | `POST /pos/sessions/open` | لا |
| إتمام البيع | تسجيل طلب POS | `POST /pos/orders` | ✅ Dr: نقد/بنك، COGS → Cr: إيرادات، ضريبة، مخزون |
| مرتجع POS | إرجاع من POS | `POST /pos/orders/{id}/return` | ✅ عكس قيد البيع + إعادة المخزون |
| إغلاق وردية | إنهاء الجلسة | `POST /pos/sessions/{id}/close` | ✅ إذا كان فرق صندوق: Dr/Cr فروقات صندوق |

---

## 1.12 المصروفات

| الصفحة | المسار | الغرض | الصلاحية |
|--------|--------|--------|----------|
| ExpenseList | `/expenses` | قائمة المصروفات | `expenses.view` |
| ExpenseForm | `/expenses/new` | إنشاء مصروف | `expenses.create` |
| ExpenseDetails | `/expenses/:id` | تفاصيل المصروف | `expenses.view` |

**أزرار:**
| الزر | الوظيفة | API | القيد |
|------|---------|-----|-------|
| إنشاء مصروف | تسجيل مصروف | `POST /finance/expenses` | ✅ Dr: حساب المصروف → Cr: نقد/بنك |
| اعتماد مصروف | الموافقة | `POST /finance/expenses/{id}/approve` | ✅ إنشاء القيد عند الموافقة |

---

## 1.13 الضرائب

| الصفحة | المسار | الغرض | الصلاحية |
|--------|--------|--------|----------|
| TaxHome | `/taxes` | بوابة الضرائب | `taxes.view` |
| TaxReturnForm | `/taxes/returns/new` | إنشاء إقرار ضريبي | `taxes.manage` |
| TaxReturnDetails | `/taxes/returns/:id` | تفاصيل الإقرار | `taxes.view` |
| WithholdingTax | `/taxes/wht` | ضريبة الاستقطاع | `taxes.view` |
| TaxCompliance | `/taxes/compliance` | الامتثال الضريبي | `taxes.view` |
| TaxCalendar | `/taxes/calendar` | تقويم المواعيد الضريبية | `taxes.view` |

---

## 1.14 CRM

| الصفحة | المسار | الغرض | الصلاحية |
|--------|--------|--------|----------|
| CRMHome | `/crm` | بوابة CRM | `sales.view` |
| Opportunities | `/crm/opportunities` | فرص المبيعات | `sales.view` |
| SupportTickets | `/crm/tickets` | تذاكر الدعم | `sales.view` |
| MarketingCampaigns | `/crm/campaigns` | حملات تسويقية | `sales.view` |
| KnowledgeBase | `/crm/knowledge-base` | قاعدة المعرفة | `sales.view` |

---

## 1.15 الخدمات

| الصفحة | المسار | الغرض | الصلاحية |
|--------|--------|--------|----------|
| ServicesHome | `/services` | بوابة الخدمات | `services.view` |
| ServiceRequests | `/services/requests` | طلبات الصيانة | `services.view` |
| DocumentManagement | `/services/documents` | إدارة المستندات | `services.view` |

---

## 1.16 التقارير

| الصفحة | المسار | الغرض | الصلاحية |
|--------|--------|--------|----------|
| ReportCenter | `/reports` | مركز التقارير | `reports.view` |
| ReportBuilder | `/reports/builder` | منشئ التقارير المخصصة | `reports.create` |
| ScheduledReports | `/reports/scheduled` | التقارير المجدولة | `reports.view` |
| DetailedProfitLoss | `/reports/detailed-pl` | أرباح وخسائر تفصيلي | `accounting.view` |
| SharedReports | `/reports/shared` | التقارير المشتركة | `reports.view` |
| ConsolidationReports | `/reports/consolidation` | تقارير التوحيد المالي (ميزان مراجعة/دخل موحّد) | `reports.consolidation` |

---

## 1.17 الموافقات

| الصفحة | المسار | الغرض | الصلاحية |
|--------|--------|--------|----------|
| ApprovalsPage | `/approvals` | طلبات الموافقة | `approvals.view` |
| WorkflowEditor | `/approvals/new` | إنشاء سير عمل | `approvals.create` |
| WorkflowEditor | `/approvals/:id/edit` | تعديل سير عمل | `approvals.manage` |

---

## 1.18 الإدارة

| الصفحة | المسار | الغرض | الصلاحية |
|--------|--------|--------|----------|
| CompanyList | `/admin/companies` | إدارة الشركات | `system_admin` |
| AuditLogs | `/admin/audit-logs` | سجل التدقيق | `audit.view` |
| RoleManagement | `/admin/roles` | إدارة الأدوار والصلاحيات | `admin.roles` |
| CompanyProfile | `/admin/company-profile` | ملف الشركة | — |
| BackupManagement | `/admin/backups` | النسخ الاحتياطية (إنشاء/تحميل/عرض) | `admin.backup` |

---

## 1.19 الإعدادات

| الصفحة | المسار | الغرض | الصلاحية |
|--------|--------|--------|----------|
| CompanySettings | `/settings` | إعدادات الشركة (تبويبات متعددة) | `settings.view` |
| Branches | `/settings/branches` | إدارة الفروع | `branches.view` |
| CostingPolicy | `/settings/costing-policy` | سياسة التكلفة | `settings.view` |
| ApiKeys | `/settings/api-keys` | مفاتيح API | `settings.view` |
| Webhooks | `/settings/webhooks` | روابط الويب (Webhooks) | `settings.view` |
| PrintTemplates | `/settings/print-templates` | قوالب الطباعة (فواتير، عروض، أوامر) | `settings.print_templates` |

---

## 1.20 استيراد البيانات

| الصفحة | المسار | الغرض | الصلاحية |
|--------|--------|--------|----------|
| DataImportPage | `/data-import` | استيراد/تصدير البيانات (Excel/CSV) | `data_import.view` |

---

# 2. خريطة الباكند والـ API

## 2.1 المصادقة والأمان (Auth / Security)

### `/auth`
| Method | المسار | الغرض | المدخلات | المخرجات | الجداول |
|--------|--------|--------|----------|----------|---------|
| POST | `/login` | تسجيل الدخول | `{username, password}` | `{access_token, user}` | `company_users`, `system_user_index` |
| GET | `/me` | بيانات المستخدم الحالي | Header: Bearer token | `{user, permissions, settings}` | `company_users`, `company_settings` |
| POST | `/logout` | تسجيل الخروج | Header: Bearer token | `{message}` | Token blacklist |
| POST | `/refresh` | تجديد التوكن | Header: Bearer token | `{access_token}` | — |
| POST | `/forgot-password` | طلب إعادة تعيين كلمة المرور | `{email}` | `{message}` | `password_reset_tokens` (system DB) |
| POST | `/reset-password` | إعادة تعيين عبر توكن | `{token, new_password}` | `{message}` | `company_users`, `password_reset_tokens` |

**آلية تسجيل الدخول:**
1. Rate limit: 10 محاولات/الدقيقة، 5 محاولات/IP، 10 محاولات/اسم مستخدم مع حظر 15 دقيقة
2. فحص admin النظام أولاً (bcrypt مقابل `ADMIN_PASSWORD_HASH`)
3. بحث في `system_user_index` للعثور على الشركة بسرعة O(1)
4. إرجاع JWT يحتوي: `sub`, `user_id`, `company_id`, `role`, `permissions`, `enabled_modules`, `allowed_branches`

### `/security`
| Method | المسار | الغرض |
|--------|--------|--------|
| POST | `/2fa/setup` | تفعيل المصادقة الثنائية |
| POST | `/2fa/verify` | التحقق من رمز 2FA |
| POST | `/2fa/disable` | تعطيل 2FA |
| GET | `/2fa/status` | حالة 2FA |
| POST | `/change-password` | تغيير كلمة المرور |
| GET/PUT | `/password-policy` | سياسة كلمات المرور |
| GET | `/sessions` | الجلسات النشطة |
| DELETE | `/sessions/{id}` | إنهاء جلسة |

## 2.2 الشركات والفروع

### `/companies`
| Method | المسار | الغرض |
|--------|--------|--------|
| POST | `/register` | تسجيل شركة جديدة (إنشاء قاعدة بيانات + 91 جدول + بيانات افتراضية) |
| GET | `/list` | قائمة الشركات (admin فقط) |
| GET | `/{company_id}` | تفاصيل شركة |
| PUT | `/update/{company_id}` | تحديث بيانات الشركة |
| POST | `/upload-logo/{company_id}` | رفع شعار |
| GET | `/public/templates` | قوالب الصناعة |

### `/branches`
| Method | المسار | الغرض |
|--------|--------|--------|
| GET/POST | `/` | قائمة / إنشاء فرع |
| PUT/DELETE | `/{branch_id}` | تعديل / حذف فرع |

## 2.3 المحاسبة والمالية

### `/finance/accounting` — (انظر القسم 5 للقيود التفصيلية)
| Method | المسار | الغرض |
|--------|--------|--------|
| GET/POST | `/accounts` | إدارة شجرة الحسابات |
| POST/GET | `/journal-entries` | القيود اليومية |
| POST | `/journal-entries/{id}/post` | ترحيل القيد |
| POST | `/journal-entries/{id}/void` | عكس القيد |
| GET/POST | `/fiscal-years` | السنوات المالية |
| POST | `/fiscal-years/{year}/close` | إقفال السنة |
| POST | `/fiscal-years/{year}/reopen` | إعادة فتح السنة |
| GET/POST | `/recurring-templates` | القوالب المتكررة |
| POST | `/opening-balances` | الأرصدة الافتتاحية |
| POST | `/closing-entries/generate` | قيود الإقفال |
| POST | `/provisions/bad-debt` | مخصص ديون معدومة |
| POST | `/provisions/leave` | مخصص إجازات |
| POST | `/fx-revaluation` | إعادة تقييم العملات |

### `/finance/treasury`
| Method | المسار | الغرض |
|--------|--------|--------|
| GET/POST | `/accounts` | حسابات الخزينة |
| POST | `/transactions/expense` | مصروف خزينة |
| POST | `/transactions/transfer` | تحويل بين حسابات |
| GET | `/reports/balances` | تقرير الأرصدة |
| GET | `/reports/cashflow` | تقرير التدفق النقدي |

### `/system/bank-import` (جديد — Phase 4)
| Method | المسار | الغرض |
|--------|--------|--------|
| POST | `/upload` | رفع ملف CSV كشف بنكي |
| GET | `/batches` | قائمة الدفعات المستوردة |
| GET | `/batches/{id}` | تفاصيل الدفعة + السطور |
| POST | `/batches/{id}/auto-match` | مطابقة تلقائية مع القيود |

**الجداول:** `bank_import_batches`, `bank_import_lines`

### `/finance/checks`
| POST | `/receivable` | إنشاء شيك مستلم |
| POST | `/receivable/{id}/collect` | تحصيل |
| POST | `/receivable/{id}/bounce` | ارتداد |
| POST | `/payable` | إنشاء شيك صادر |
| POST | `/payable/{id}/clear` | مقاصة |
| POST | `/payable/{id}/bounce` | ارتداد |

### `/finance/notes`
| POST | `/receivable` | إنشاء ورقة قبض |
| POST | `/receivable/{id}/collect` | تحصيل |
| POST | `/receivable/{id}/protest` | بروتستو |
| POST | `/payable` | إنشاء ورقة دفع |
| POST | `/payable/{id}/pay` | سداد |

### `/finance/assets`
| POST | `/` | إنشاء أصل |
| POST | `/{id}/depreciate/{schedule_id}` | إهلاك |
| POST | `/{id}/dispose` | استبعاد |
| POST | `/{id}/transfer` | تحويل فرعي |
| POST | `/{id}/revalue` | إعادة تقييم |

### `/finance/budgets`
| POST/GET | `/` | موازنات |
| POST | `/{id}/items` | بنود الموازنة |
| GET | `/{id}/report` | تقرير الموازنة مقابل الفعلي |

### `/finance/taxes`
| GET/POST | `/rates` | معدلات الضريبة |
| GET/POST | `/returns` | الإقرارات الضريبية |
| POST | `/payments` | دفعات ضريبية |
| POST | `/settle` | تسوية الضريبة |
| GET | `/calendar` | تقويم ضريبي |

### `/finance/currencies`
| GET/POST | `/` | إدارة العملات |
| POST | `/rates` | أسعار الصرف |
| POST | `/revaluate` | إعادة تقييم العملة |

### `/finance/reconciliation`
| POST | `/` | إنشاء مطابقة بنكية |
| POST | `/{id}/auto-match` | مطابقة تلقائية |
| POST | `/{id}/finalize` | إنهاء المطابقة |

### `/system/zakat` (جديد — Phase 4)
| Method | المسار | الغرض |
|--------|--------|--------|
| POST | `/calculate` | حساب الزكاة (طريقة صافي الأصول ZATCA + طريقة الربح المعدّل) |
| POST | `/post-journal-entry` | ترحيل قيد الزكاة |

**الجداول:** `zakat_calculations` — **ملاحظة:** حساب متوافق مع هيئة الزكاة GAZT، يدعم التقويم الهجري (2.5%) والميلادي (2.5775%)

### `/system/fiscal-locks` (جديد — Phase 4)
| Method | المسار | الغرض |
|--------|--------|--------|
| GET | `/` | قائمة الفترات المحاسبية |
| POST | `/` | إنشاء فترة |
| POST | `/{id}/lock` | قفل الفترة |
| POST | `/{id}/unlock` | فتح الفترة |

**الجداول:** `fiscal_period_locks`

### `/system/consolidation` (جديد — Phase 4)
| Method | المسار | الغرض |
|--------|--------|--------|
| GET | `/trial-balance` | ميزان مراجعة موحّد لجميع الشركات |
| GET | `/income-statement` | قائمة دخل موحّدة |

### `/system/backup` (جديد — Phase 4)
| Method | المسار | الغرض |
|--------|--------|--------|
| POST | `/create` | إنشاء نسخة احتياطية |
| GET | `/list` | قائمة النسخ الاحتياطية |
| GET | `/download/{filename}` | تحميل نسخة |

**الجداول:** `backup_history`

### `/system/print-templates` (جديد — Phase 4)
| Method | المسار | الغرض |
|--------|--------|--------|
| GET | `/` | قائمة قوالب الطباعة |
| POST | `/` | إنشاء قالب |
| PUT | `/{id}` | تعديل قالب |
| DELETE | `/{id}` | حذف قالب |

**الجداول:** `print_templates`

### `/system/duplicate-detection` (جديد — Phase 4)
| Method | المسار | الغرض |
|--------|--------|--------|
| GET | `/scan/{entity_type}` | فحص التكرارات (parties, products, invoices) |

### `/auth/forgot-password` و `/auth/reset-password` (جديد — Phase 4)
| Method | المسار | الغرض |
|--------|--------|--------|
| POST | `/forgot-password` | طلب إعادة تعيين كلمة المرور (بريد إلكتروني) |
| POST | `/reset-password` | إعادة تعيين كلمة المرور عبر التوكن |

**الجداول:** `password_reset_tokens` (في قاعدة البيانات المركزية)

## 2.4 المبيعات والمشتريات

### `/sales` — (انظر القسم 1.3 للتفاصيل)
**ملخص الـ Endpoints:** ~45 endpoint تشمل العملاء، العروض، الأوامر، الفواتير، المرتجعات، سندات القبض/الصرف، إشعارات الخصم/الائتمان، العمولات، العقود، **أوامر التسليم (جديد)**

### `/sales/delivery-orders` (جديد — Phase 4)
| POST | `/` | إنشاء أمر تسليم |
| GET | `/` | قائمة أوامر التسليم |
| GET | `/{id}` | تفاصيل أمر التسليم |
| POST | `/{id}/confirm` | تأكيد |
| POST | `/{id}/deliver` | تسليم |
| POST | `/{id}/invoice` | فوترة (ينشئ قيد) |
| POST | `/{id}/cancel` | إلغاء |

### `/purchases` — (انظر القسم 1.4 للتفاصيل)
**ملخص الـ Endpoints:** ~40 endpoint تشمل الموردين، طلبات الشراء، الفواتير، المرتجعات، الدفعات، RFQ، تقييم الموردين، الاتفاقيات، **التكاليف المحمّلة (جديد)**

### `/purchases/landed-costs` (جديد — Phase 4)
| POST | `/` | إنشاء تكلفة محمّلة |
| GET | `/` | قائمة التكاليف المحمّلة |
| GET | `/{id}` | تفاصيل |
| POST | `/{id}/allocate` | توزيع (4 طرق) |
| POST | `/{id}/post` | ترحيل القيد |

## 2.5 المخزون (`/inventory`)

~50 endpoint تشمل: المنتجات، المستودعات، التصنيفات، الموردين، حركات المخزون، التحويلات، التسويات، الشحنات، الدُفعات، الأرقام التسلسلية، فحوصات الجودة، الجرد الدوري، التقارير، قوائم الأسعار، المتغيرات، صناديق التخزين (Bins)، المجموعات (Kits)

## 2.6 الموارد البشرية (`/hr`)

~55 endpoint تشمل: الموظفين، الأقسام، المناصب، المسيرات، السلف، الإجازات، الحضور، هياكل الرواتب، العمل الإضافي، التأمينات، الوثائق، الأداء، التدريب، المخالفات، العهد، التوظيف، قسائم الرواتب، ترحيل الإجازات، **WPS + السعودة + نهاية الخدمة (جديد)**

### `/hr/wps` + `/hr/saudization` + `/hr/eos` (جديد — Phase 4)
| POST | `/wps/preview` | معاينة بيانات WPS |
| POST | `/wps/export-sif` | تصدير ملف SIF |
| GET | `/saudization/dashboard` | لوحة نسبة السعودة ونطاقات |
| POST | `/eos/calculate` | حساب تسوية نهاية الخدمة |

## 2.7 التصنيع (`/manufacturing`)

~40 endpoint: مراكز العمل، المسارات، قوائم المواد (BOM)، أوامر الإنتاج، العمليات، MRP، المعدات، الصيانة، تقارير الإنتاج، فحوصات الجودة، **تكاليف التصنيع (جديد)**

### `/manufacturing/calculate-cost` + `/manufacturing/cost-variance-report` (جديد — Phase 4)
| POST | `/calculate-cost` | حساب تكلفة أمر إنتاج (مواد + عمالة + overhead) |
| GET | `/cost-variance-report` | تقرير انحرافات التكلفة (تقديري vs فعلي) |

## 2.8 المشاريع (`/projects`)

~30 endpoint: المشاريع، المهام، المصروفات، الإيرادات، الجداول الزمنية، المستندات، أوامر التغيير، فوترة المشروع، Retainer، EVM، تقارير الربحية

## 2.9 نقاط البيع (`/pos`)

~25 endpoint: الجلسات، الطلبات، المرتجعات، العروض، برامج الولاء، الطاولات، شاشة المطبخ

## 2.10 الخدمات الأخرى

| Router | Prefix | عدد الـ Endpoints |
|--------|--------|-------------------|
| `/crm` | CRM | ~20 (فرص، تذاكر، حملات، معرفة) |
| `/services` | Services | ~15 (طلبات صيانة، مستندات) |
| `/notifications` | Notifications | ~8 |
| `/approvals` | Approvals | ~12 |
| `/audit` | Audit | ~3 |
| `/data-import` | Data Import | ~6 |
| `/scheduled-reports` | Scheduled Reports | ~12 |
| `/external` | External/Integrations | ~20 (API keys, webhooks, ZATCA, WHT) |
| `/reports` | Reports | ~43 |
| `/roles` | Roles | ~8 |
| `/dashboard` | Dashboard | ~15 |
| `/settings` | Settings | ~4 |

---

# 3. خريطة قاعدة البيانات

## 3.1 قاعدة البيانات المركزية (System DB: `postgres`)

| الجدول | الغرض | الأعمدة الرئيسية |
|--------|--------|------------------|
| `system_user_index` | فهرس مستخدمين سريع لتسجيل الدخول O(1) | `username`, `company_id`, `is_active` |
| `system_companies` | سجل الشركات | `id`, `company_name`, `database_name`, `status`, `plan_type`, `enabled_modules` |
| `industry_templates` | قوالب الصناعة | `key`, `name`, `enabled_modules` |
| `system_activity_log` | سجل نشاط عام | `company_id`, `action_type`, `performed_by` |

## 3.2 قاعدة بيانات الشركة (Company DB: `aman_{company_id}`)

### الجداول الأساسية (Core — 7 جداول)

| # | الجدول | الغرض | PK | FKs | الأعمدة الرئيسية |
|---|--------|--------|-----|-----|------------------|
| 1 | `company_users` | المستخدمون | `id` | — | `username` UNIQUE, `password`, `email`, `role`, `permissions` JSONB, `is_active` |
| 2 | `branches` | الفروع | `id` | — | `branch_code` UNIQUE, `branch_name`, `country_code`, `default_currency`, `is_default` |
| 3 | `user_branches` | ربط المستخدم بالفروع | `id` | `user_id→company_users`, `branch_id→branches` | UNIQUE(user_id, branch_id) |
| 4 | `party_groups` | مجموعات الأطراف | `id` | `branch_id→branches` | `group_code`, `group_name`, `discount_percentage` |
| 5 | `parties` | الأطراف (موحّد: عميل+مورد) | `id` | `party_group_id→party_groups`, `branch_id→branches` | `party_type`, `party_code` UNIQUE, `name`, `is_customer`, `is_supplier`, `credit_limit`, `current_balance` |
| 6 | `party_transactions` | حركات الأطراف | `id` | `party_id→parties`, `created_by→company_users` | `transaction_type`, `debit`, `credit`, `balance` |
| 7 | `company_settings` | إعدادات (key-value) | `id` | — | `setting_key` UNIQUE, `setting_value` |

### المحاسبة (Accounting — 6 جداول)

| # | الجدول | الغرض | PK | FKs |
|---|--------|--------|-----|-----|
| 8 | `accounts` | شجرة الحسابات | `id` | `parent_id→accounts` |
| 9 | `treasury_accounts` | حسابات الخزينة (صندوق/بنك) | `id` | `gl_account_id→accounts`, `branch_id→branches` |
| 10 | `journal_entries` | القيود اليومية | `id` | `branch_id→branches`, `created_by→company_users` |
| 11 | `journal_lines` | سطور القيد | `id` | `journal_entry_id→journal_entries`, `account_id→accounts` |
| 12 | `fiscal_years` | السنوات المالية | `id` | `retained_earnings_account_id→accounts` |
| 13 | `fiscal_periods` | الفترات المالية | `id` | — |

### الفواتير والمبيعات (Invoicing & Sales — 14 جدول)

| # | الجدول | الغرض | PK | FKs |
|---|--------|--------|-----|-----|
| 14 | `invoices` | الفواتير (بيع + شراء) | `id` | `party_id→parties`, `branch_id→branches` |
| 15 | `invoice_lines` | سطور الفاتورة | `id` | `invoice_id→invoices`, `product_id→products` |
| 16 | `sales_quotations` | عروض الأسعار | `id` | `party_id→parties` |
| 17 | `sales_quotation_lines` | سطور العرض | `id` | `sq_id→sales_quotations` |
| 18 | `sales_orders` | أوامر البيع | `id` | `party_id→parties`, `quotation_id→sales_quotations` |
| 19 | `sales_order_lines` | سطور أمر البيع | `id` | `so_id→sales_orders` |
| 20 | `sales_returns` | مرتجعات المبيعات | `id` | `party_id→parties`, `invoice_id→invoices` |
| 21 | `sales_return_lines` | سطور المرتجع | `id` | `return_id→sales_returns` |
| 22 | `payment_vouchers` | سندات القبض/الصرف | `id` | `treasury_account_id→treasury_accounts` |
| 23 | `payment_allocations` | تخصيص الدفعات على الفواتير | `id` | `voucher_id→payment_vouchers`, `invoice_id→invoices` |
| 24 | `commission_rules` | قواعد العمولات | `id` | `branch_id→branches` |
| 25 | `sales_commissions` | العمولات المحسوبة | `id` | `branch_id→branches` |
| 26 | `contracts` | العقود | `id` | `party_id→parties` |
| 27 | `contract_items` | بنود العقد | `id` | `contract_id→contracts` |

### المشتريات (Purchases — 11 جدول)

| # | الجدول | الغرض |
|---|--------|--------|
| 28 | `purchase_orders` | طلبات الشراء |
| 29 | `purchase_order_lines` | سطور طلب الشراء |
| 30 | `request_for_quotations` | طلبات عروض الأسعار (RFQ) |
| 31 | `rfq_lines` | سطور RFQ |
| 32 | `rfq_responses` | ردود الموردين |
| 33 | `supplier_ratings` | تقييم الموردين |
| 34 | `purchase_agreements` | اتفاقيات الشراء الإطارية |
| 35 | `purchase_agreement_lines` | سطور الاتفاقية |

### العملاء والموردون (Legacy — 10 جداول)

| # | الجدول | الغرض | ملاحظة |
|---|--------|--------|--------|
| 36 | `customers` | العملاء | Legacy — يُستخدم بالتوازي مع `parties` |
| 37 | `customer_groups` | مجموعات العملاء | |
| 38 | `customer_contacts` | جهات اتصال العملاء | |
| 39 | `customer_bank_accounts` | حسابات بنكية للعملاء | |
| 40 | `customer_transactions` | حركات العملاء | |
| 41 | `customer_receipts` | إيصالات العملاء | |
| 42 | `customer_price_lists` | قوائم أسعار العملاء | |
| 43 | `customer_price_list_items` | بنود قائمة الأسعار | |
| 44 | `suppliers` | الموردون | Legacy |
| 45 | `supplier_groups` | مجموعات الموردين | |
| 46 | `supplier_contacts` | جهات اتصال الموردين | |
| 47 | `supplier_bank_accounts` | حسابات بنكية للموردين | |
| 48 | `supplier_transactions` | حركات الموردين | |
| 49 | `supplier_payments` | دفعات الموردين | |

### المالية المتقدمة (AR/AP + Balances — 6 جداول)

| # | الجدول | الغرض |
|---|--------|--------|
| 50 | `customer_balances` | أرصدة العملاء (denormalized) |
| 51 | `supplier_balances` | أرصدة الموردين (denormalized) |
| 52 | `pending_receivables` | ذمم مدينة معلقة |
| 53 | `pending_payables` | ذمم دائنة معلقة |
| 54 | `receipts` | إيصالات (legacy) |
| 55 | `payments` | دفعات (legacy) |

### المنتجات والمخزون (Products & Inventory — 15+ جدول)

| # | الجدول | الغرض |
|---|--------|--------|
| 56 | `product_categories` | تصنيفات المنتجات |
| 57 | `product_units` | وحدات القياس |
| 58 | `products` | المنتجات — يتضمن: `cost_price`, `selling_price`, `tax_rate`, `is_track_inventory`, `has_batch_tracking`, `has_serial_tracking`, `has_variants`, `is_kit` |
| 59 | `warehouses` | المستودعات |
| 60 | `inventory` | أرصدة المخزون (product × warehouse) — UNIQUE(product_id, warehouse_id) |
| 61 | `inventory_transactions` | حركات المخزون (الدفتر) |
| 62 | `stock_adjustments` | تسويات المخزون |
| 63 | `stock_shipments` | شحنات المخزون |
| 64 | `stock_shipment_items` | بنود الشحنة |
| 65 | `stock_transfer_log` | سجل تحويلات المخزون |
| 66 | `product_batches` | أرقام الدُفعات |
| 67 | `product_serials` | الأرقام التسلسلية |
| 68 | `batch_serial_movements` | حركات الدُفعات والتسلسلي |
| 69 | `quality_inspections` | فحوصات الجودة |
| 70 | `quality_inspection_criteria` | معايير الفحص |
| 71 | `cycle_counts` | الجرد الدوري |
| 72 | `cycle_count_items` | بنود الجرد |
| 73 | `product_attributes` | صفات المنتج (لون، حجم...) |
| 74 | `product_attribute_values` | قيم الصفات |
| 75 | `product_variants` | المتغيرات |
| 76 | `product_variant_attributes` | ربط المتغير بالصفات |
| 77 | `bin_locations` | مواقع التخزين |
| 78 | `bin_inventory` | مخزون الموقع |
| 79 | `product_kits` | المجموعات |
| 80 | `product_kit_items` | مكونات المجموعة |

### الخزينة والأوراق التجارية (Treasury — 8 جداول)

| # | الجدول | الغرض |
|---|--------|--------|
| 81 | `treasury_transactions` | حركات الخزينة |
| 82 | `bank_reconciliations` | المطابقات البنكية |
| 83 | `bank_statement_lines` | سطور كشف البنك |
| 84 | `checks_receivable` | شيكات تحت التحصيل |
| 85 | `checks_payable` | شيكات تحت الدفع |
| 86 | `notes_receivable` | أوراق القبض |
| 87 | `notes_payable` | أوراق الدفع |
| 88 | `expenses` | المصروفات |

### الموارد البشرية (HR — 18 جدول)

| # | الجدول | الغرض |
|---|--------|--------|
| 89 | `departments` | الأقسام |
| 90 | `employee_positions` | المناصب |
| 91 | `employees` | الموظفون |
| 92 | `payroll_periods` | فترات الرواتب |
| 93 | `payroll_entries` | قيود الرواتب |
| 94 | `attendance` | الحضور والانصراف |
| 95 | `employee_loans` | سلف الموظفين |
| 96 | `leave_requests` | طلبات الإجازات |
| 97 | `salary_structures` | هياكل الرواتب |
| 98 | `salary_components` | مكونات الراتب |
| 99 | `employee_salary_components` | ربط المكون بالموظف |
| 100 | `overtime_requests` | العمل الإضافي |
| 101 | `gosi_settings` | إعدادات التأمينات |
| 102 | `employee_documents` | وثائق الموظفين |
| 103 | `performance_reviews` | تقييمات الأداء |
| 104 | `training_programs` | البرامج التدريبية |
| 105 | `training_participants` | المشاركون في التدريب |
| 106 | `employee_violations` | المخالفات |
| 107 | `employee_custody` | العهد والممتلكات |
| 108 | `job_openings` | الوظائف الشاغرة |
| 109 | `job_applications` | طلبات التوظيف |
| 110 | `leave_carryover` | ترحيل الإجازات |

### الأصول الثابتة (Assets — 6 جداول)

| # | الجدول | الغرض |
|---|--------|--------|
| 111 | `asset_categories` | تصنيفات الأصول |
| 112 | `assets` | الأصول |
| 113 | `asset_depreciation_schedule` | جدول الإهلاك |
| 114 | `asset_disposals` | استبعاد الأصول |
| 115 | `asset_transfers` | تحويلات الأصول بين الفروع |
| 116 | `asset_revaluations` | إعادة تقييم |
| 117 | `asset_insurance` | تأمين الأصول |
| 118 | `asset_maintenance` | صيانة الأصول |

### الضرائب (Tax — 8 جداول)

| # | الجدول | الغرض |
|---|--------|--------|
| 119 | `tax_rates` | معدلات الضريبة |
| 120 | `tax_groups` | مجموعات ضريبية |
| 121 | `tax_returns` | الإقرارات الضريبية |
| 122 | `tax_payments` | دفعات ضريبية |
| 123 | `tax_regimes` | أنظمة ضريبية (per country) |
| 124 | `branch_tax_settings` | إعدادات ضريبة الفرع |
| 125 | `company_tax_settings` | إعدادات ضريبة الشركة |
| 126 | `tax_calendar` | تقويم ضريبي |
| 127 | `wht_rates` | معدلات ضريبة الاستقطاع |
| 128 | `wht_transactions` | حركات ضريبة الاستقطاع |

### المشاريع (Projects — 7 جداول)

| # | الجدول | الغرض |
|---|--------|--------|
| 129 | `projects` | المشاريع |
| 130 | `project_tasks` | مهام المشروع |
| 131 | `project_budgets` | موازنة المشروع |
| 132 | `project_expenses` | مصروفات المشروع |
| 133 | `project_revenues` | إيرادات المشروع |
| 134 | `project_documents` | مستندات المشروع |
| 135 | `project_change_orders` | أوامر تغيير |
| 136 | `project_timesheets` | الجداول الزمنية |

### التصنيع (Manufacturing — 10 جداول)

| # | الجدول | الغرض |
|---|--------|--------|
| 137 | `work_centers` | مراكز العمل |
| 138 | `manufacturing_routes` | مسارات التصنيع |
| 139 | `manufacturing_operations` | العمليات |
| 140 | `bill_of_materials` | قوائم المواد (BOM) |
| 141 | `bom_components` | مكونات BOM |
| 142 | `bom_outputs` | مخرجات فرعية (By-products) |
| 143 | `production_orders` | أوامر الإنتاج |
| 144 | `production_order_operations` | عمليات أمر الإنتاج |
| 145 | `mrp_plans` | خطط MRP |
| 146 | `mrp_items` | بنود MRP |
| 147 | `mfg_qc_checks` | فحوصات جودة التصنيع |
| 148 | `manufacturing_equipment` | المعدات |
| 149 | `maintenance_logs` | سجلات الصيانة |

### نقاط البيع (POS — 10 جداول)

| # | الجدول | الغرض |
|---|--------|--------|
| 150 | `pos_sessions` | جلسات البيع |
| 151 | `pos_orders` | طلبات POS |
| 152 | `pos_order_lines` | سطور طلب POS |
| 153 | `pos_payments` | دفعات POS |
| 154 | `pos_order_payments` | تفصيل دفعات الطلب |
| 155 | `pos_returns` | مرتجعات POS |
| 156 | `pos_return_items` | بنود مرتجع POS |
| 157 | `pos_promotions` | العروض الترويجية |
| 158 | `pos_loyalty_programs` | برامج الولاء |
| 159 | `pos_loyalty_points` | نقاط ولاء العميل |
| 160 | `pos_loyalty_transactions` | حركات النقاط |
| 161 | `pos_tables` | الطاولات (مطاعم) |
| 162 | `pos_table_orders` | طلبات الطاولة |
| 163 | `pos_kitchen_orders` | طلبات المطبخ |

### أخرى (Other — 20+ جدول)

| # | الجدول | الغرض |
|---|--------|--------|
| 164 | `roles` | الأدوار |
| 165 | `audit_logs` | سجل التدقيق |
| 166 | `cost_centers` | مراكز التكلفة |
| 167 | `budgets` | الموازنات |
| 168 | `budget_items` | بنود الموازنة |
| 169 | `budget_lines` | سطور الموازنة |
| 170 | `cost_centers_budgets` | موازنات مراكز التكلفة |
| 171 | `notifications` | الإشعارات |
| 172 | `custom_reports` | تقارير مخصصة |
| 173 | `scheduled_reports` | تقارير مجدولة |
| 174 | `shared_reports` | تقارير مشتركة |
| 175 | `recurring_journal_templates` | قوالب قيود متكررة |
| 176 | `recurring_journal_lines` | سطور القالب المتكرر |
| 177 | `currencies` | عملات |
| 178 | `exchange_rates` | أسعار الصرف |
| 179 | `currency_transactions` | حركات العملات |
| 180 | `costing_policies` | سياسات التكلفة |
| 181 | `costing_policy_details` | تفاصيل السياسة |
| 182 | `costing_policy_history` | سجل تغيير السياسة |
| 183 | `inventory_cost_snapshots` | لقطات تكلفة المخزون |
| 184 | `approval_workflows` | سير عمل الموافقات |
| 185 | `approval_requests` | طلبات الموافقة |
| 186 | `approval_actions` | إجراءات الموافقة |
| 187 | `user_2fa_settings` | إعدادات المصادقة الثنائية |
| 188 | `password_history` | سجل كلمات المرور |
| 189 | `user_sessions` | جلسات المستخدم |
| 190 | `api_keys` | مفاتيح API |
| 191 | `webhooks` | Webhooks |
| 192 | `webhook_logs` | سجلات Webhook |
| 193 | `sales_opportunities` | فرص المبيعات (CRM) |
| 194 | `opportunity_activities` | أنشطة الفرص |
| 195 | `support_tickets` | تذاكر الدعم |
| 196 | `ticket_comments` | تعليقات التذكرة |
| 197 | `sales_targets` | أهداف المبيعات |
| 198 | `dashboard_layouts` | تخطيط لوحة التحكم |
| 199 | `financial_reports` | تقارير مالية محفوظة |
| 200 | `report_templates` | قوالب التقارير |
| 201 | `document_types` | أنواع المستندات |
| 202 | `attachments` | المرفقات |
| 203 | `document_templates` | قوالب المستندات |
| 204 | `messages` | الرسائل الداخلية |
| 205 | `email_templates` | قوالب البريد |

### Triggers

يوجد Trigger واحد يُطبق على ~25 جدول:
```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';
```
يُطبق BEFORE UPDATE على: `company_users`, `accounts`, `customers`, `suppliers`, `products`, `invoices`, `journal_entries`, `budgets`, `assets`, `employees`, `employee_loans`, `leave_requests`, `projects`, `project_tasks`, `contracts`, `sales_orders`, `purchase_orders`, `warehouses`, `treasury_accounts`, `tax_rates`, `currencies`, `parties`, `sales_quotations`, `expenses`, `pos_sessions`

---

# 4. شجرة الحسابات

## 4.1 الهيكل (3 مستويات)

```
1 — الأصول (Assets)
├── 11 — أصول متداولة (Current Assets)
│   ├── 1101 — النقد وما في حكمه
│   │   ├── 110101 — الصندوق الرئيسي
│   │   └── 110102 — البنك
│   ├── 1102 — العملاء والذمم المدينة (AR)
│   ├── 1103 — المخزون
│   │   ├── 110301 — مخزون المواد الأولية
│   │   └── 110302 — مخزون الإنتاج التام
│   ├── 1104 — سلف وقروض الموظفين
│   ├── 1105 — مصروفات مدفوعة مقدماً
│   │   ├── 110501 — إيجار مدفوع مقدماً
│   │   └── 110502 — تأمين مدفوع مقدماً
│   ├── 1106 — مدفوعات مقدمة للموردين
│   ├── 1107 — ضريبة المدخلات (VAT Input)
│   ├── 1108 — شيكات تحت التحصيل
│   ├── 1109 — أوراق قبض
│   ├── 1110 — أعمال تحت التشغيل (WIP)
│   └── 1111 — حسابات بين الفروع
├── 12 — أصول ثابتة (Fixed Assets)
│   ├── 1201 — الآلات والمعدات
│   ├── 1202 — السيارات
│   ├── 1203 — الأثاث
│   ├── 1204 — المباني
│   ├── 1205 — الأراضي
│   ├── 1206 — أجهزة حاسوب
│   └── 1207 — الإهلاك المتراكم
└── 13 — أصول غير ملموسة (Intangible)
    ├── 1301 — شهرة
    ├── 1302 — براءات اختراع
    ├── 1303 — حقوق تأليف
    ├── 1304 — الإطفاء المتراكم
    └── 1305 — أصل حق الاستخدام

2 — الخصوم (Liabilities)
├── 21 — خصوم متداولة
│   ├── 2101 — الموردين والذمم الدائنة (AP)
│   ├── 2102 — مصاريف مستحقة
│   ├── 2103 — ضريبة القيمة المضافة
│   │   └── 210301 — ضريبة المخرجات (VAT Output)
│   ├── 2104 — مشتريات مستلمة غير مفوترة
│   ├── 2105 — شيكات تحت الدفع
│   ├── 2106 — التأمينات الاجتماعية المستحقة (GOSI)
│   ├── 2107 — دفعات مقدمة من العملاء
│   ├── 2108 — ضريبة الاستقطاع (WHT)
│   ├── 2109 — ضريبة الدخل المستحقة
│   ├── 2110 — أوراق دفع
│   ├── 2111 — الزكاة المستحقة
│   └── 2112 — تسوية ضريبة القيمة المضافة
└── 22 — خصوم غير متداولة
    ├── 2201 — قروض طويلة الأجل
    ├── 2202 — مخصص نهاية الخدمة
    ├── 2203 — مخصص الإجازات
    └── 2204 — مخصص الديون المعدومة

3 — حقوق الملكية (Equity)
├── 31 — رأس المال
├── 32 — الأرباح المبقاة
├── 33 — أرباح العام الحالي
├── 34 — الجاري والمسحوبات
└── 35 — احتياطي إعادة التقييم

4 — الإيرادات (Revenue)
├── 41 — إيرادات التشغيل
│   ├── 4101 — مبيعات البضائع
│   ├── 4102 — إيرادات الخدمات
│   ├── 4103 — مردودات المبيعات
│   └── 4104 — خصم مبيعات
└── 42 — إيرادات أخرى
    ├── 4201 — أرباح فروقات عملة (محققة)
    ├── 4202 — أرباح فروقات عملة (غير محققة)
    ├── 4203 — فوائد محصلة
    ├── 4204 — توزيعات أرباح
    ├── 4205 — ربح بيع أصول
    └── 4206 — خصومات مكتسبة

5 — المصروفات (Expenses)
├── 51 — تكلفة البضاعة المباعة (COGS)
│   ├── 5101 — تكلفة مبيعات البضائع
│   ├── 5102 — تكلفة التصنيع
│   ├── 5103 — تكلفة العمالة المباشرة
│   └── 5104 — المصاريف الصناعية العامة
├── 52 — المصروفات التشغيلية
│   ├── 5201 — الرواتب والأجور
│   ├── 5202 — مصروف الإيجار
│   ├── 5203 — الكهرباء والمياه
│   ├── 5204 — الاتصالات والإنترنت
│   ├── 5205 — الصيانة
│   ├── 5206 — الرسوم الحكومية
│   ├── 5207 — التسويق والإعلان
│   ├── 5208 — السفر والتنقل
│   ├── 5209 — مصروفات عمومية
│   ├── 5210 — مصروف التأمينات الاجتماعية
│   ├── 5211 — مصروف التأمين
│   ├── 5212-5218 — (مصروفات فرعية أخرى)
│   ├── 5219 — بدلات الموظفين
│   ├── 5220 — العمل الإضافي
│   ├── 5221 — مكافآت نهاية الخدمة
│   ├── 5222 — مصروف الإجازات
│   └── 5223 — مصروف ديون معدومة
├── 53 — الإهلاك
├── 54 — المصروفات المالية والبنكية
│   ├── 5401 — الرسوم البنكية
│   ├── 5402 — خسائر فروقات عملة (محققة)
│   └── 5403 — خسائر فروقات عملة (غير محققة)
└── 55 — مصروفات أخرى
    ├── 5501 — خسائر استبعاد الأصول
    ├── 5502 — فروقات صندوق
    └── 5503 — فروقات تسوية المخزون
```

## 4.2 ربط الحسابات بالعمليات التلقائية (Account Mappings)

يتم تخزين الربط في `company_settings` بمفاتيح `acc_map_*`:

| المفتاح | الحساب الافتراضي | الاستخدام |
|---------|------------------|-----------|
| `acc_map_ar` | 1102 (العملاء) | فواتير البيع، سندات القبض |
| `acc_map_ap` | 2101 (الموردين) | فواتير الشراء، سندات الصرف |
| `acc_map_cash_main` | 110101 (الصندوق) | عمليات النقد |
| `acc_map_bank` | 110102 (البنك) | عمليات البنك |
| `acc_map_sales_rev` | 4101 (مبيعات بضائع) | فواتير البيع |
| `acc_map_service_rev` | 4102 (إيرادات خدمات) | فواتير الخدمات |
| `acc_map_vat_out` | 210301 (ضريبة مخرجات) | فواتير البيع |
| `acc_map_vat_in` | 1107 (ضريبة مدخلات) | فواتير الشراء |
| `acc_map_cogs` | 5101 (تكلفة المبيعات) | فواتير البيع |
| `acc_map_inventory` | 1103 (المخزون) | حركات المخزون |
| `acc_map_raw_materials` | 110301 (مواد أولية) | التصنيع |
| `acc_map_finished_goods` | 110302 (إنتاج تام) | التصنيع |
| `acc_map_wip` | 1110 (أعمال تحت التشغيل) | التصنيع |
| `acc_map_salaries_exp` | 5201 (رواتب) | مسير الرواتب |
| `acc_map_gosi_expense` | 5210 (تأمينات) | مسير الرواتب |
| `acc_map_gosi_payable` | 2106 (تأمينات مستحقة) | مسير الرواتب |
| `acc_map_loans_adv` | 1104 (سلف) | سلف الموظفين |
| `acc_map_depr_exp` | 53 (إهلاك) | إهلاك الأصول |
| `acc_map_acc_depr` | 1207 (إهلاك متراكم) | إهلاك الأصول |
| `acc_map_checks_receivable` | 1108 (شيكات مستلمة) | الشيكات |
| `acc_map_checks_payable` | 2105 (شيكات صادرة) | الشيكات |
| `acc_map_notes_receivable` | 1109 (أوراق قبض) | الأوراق التجارية |
| `acc_map_notes_payable` | 2110 (أوراق دفع) | الأوراق التجارية |
| `acc_map_customer_deposits` | 2107 (دفعات مقدمة) | الدفعات المقدمة |
| `acc_map_inventory_adjustment` | 5503 (فروقات مخزون) | تسوية المخزون |
| `acc_map_cash_over_short` | 5502 (فروقات صندوق) | POS |
| `acc_map_withholding_tax` | 2108 (ضريبة استقطاع) | WHT |
| `acc_map_revaluation_reserve` | 35 (احتياطي إعادة تقييم) | إعادة تقييم الأصول |

---

# 5. القيود المحاسبية

## 5.1 القيود اليدوية

- **الإنشاء:** `POST /finance/accounting/journal-entries` → يُنشئ بحالة `draft`
- **الترحيل:** `POST /finance/accounting/journal-entries/{id}/post` → يُحدّث أرصدة الحسابات
- **العكس:** `POST /finance/accounting/journal-entries/{id}/void` → يُنشئ قيد عكسي `REV-{original}`
- **التحقق:** يجب أن يكون مجموع المدين = مجموع الدائن

## 5.2 القيود التلقائية — الجدول الكامل (65 نقطة)

| # | العملية | رقم القيد | المدين (Dr) | الدائن (Cr) | الجداول المتأثرة |
|---|---------|-----------|-------------|-------------|-----------------|
| **المبيعات** |
| 1 | فاتورة بيع | `JE-SALE-{inv}` | نقد/بنك/عملاء + COGS | إيرادات مبيعات + ضريبة مخرجات + مخزون | `invoices`, `journal_entries`, `accounts`, `inventory`, `party_transactions` |
| 2 | إلغاء فاتورة بيع | — | يُبطل القيد (voided) | — | `invoices`, `journal_entries`, `accounts`, `inventory` |
| 3 | سند قبض من عميل | `JE-RCV-{num}` | نقد أو بنك | العملاء (ذمم مدينة) | `payment_vouchers`, `journal_entries`, `accounts`, `party_transactions` |
| 4 | سند صرف لعميل (رد) | `JE-PAY-{num}` | العملاء | نقد أو بنك | `payment_vouchers`, `journal_entries`, `accounts` |
| 5 | اعتماد مرتجع مبيعات | `JE-RET-{num}` | إيرادات (عكس) + مخزون | نقد/عملاء + COGS (عكس) | `sales_returns`, `journal_entries`, `inventory` |
| 6 | إشعار دائن مبيعات | `JE-SCN-{num}` | إيرادات + ضريبة (عكس) | العملاء | `invoices`, `journal_entries` |
| 7 | إشعار مدين مبيعات | `JE-SDN-{num}` | العملاء | إيرادات + ضريبة | `invoices`, `journal_entries` |
| 8 | صرف عمولات | `COMPAY-{year}-{num}` | مصروف عمولات | بنك/نقد | `sales_commissions`, `journal_entries` |
| **المشتريات** |
| 9 | استلام بضاعة (GRN) | `JE-GRN-{po}` | مخزون/مصروف | ذمم دائنة | `purchase_order_lines`, `inventory`, `journal_entries` |
| 10 | فاتورة شراء | `JE-PINV-{inv}` | مخزون/مصروف + ضريبة مدخلات | ذمم دائنة/نقد | `invoices`, `journal_entries`, `inventory` |
| 11 | مرتجع مشتريات | `JE-PRET-{num}` | ذمم دائنة | مخزون + ضريبة (عكس) | `invoices`, `journal_entries`, `inventory` |
| 12 | دفعة للمورد | `JE-PPAY-{num}` | ذمم دائنة | نقد/بنك | `payment_vouchers`, `journal_entries`, `accounts` |
| 13 | إشعار دائن مشتريات | `JE-PCN-{num}` | ذمم دائنة | مرتجعات مشتريات + ضريبة | `invoices`, `journal_entries` |
| 14 | إشعار مدين مشتريات | `JE-PDN-{num}` | مصروف/تكلفة إضافية | ذمم دائنة | `invoices`, `journal_entries` |
| **نقاط البيع** |
| 15 | طلب POS | `JE-POS-{order}` | نقد/بنك + COGS | إيرادات + ضريبة + مخزون | `pos_orders`, `journal_entries`, `inventory` |
| 16 | مرتجع POS | `JE-POS-RET-{order}` | إيرادات + مخزون | نقد + COGS | `pos_returns`, `journal_entries`, `inventory` |
| 17 | إغلاق وردية (فرق صندوق) | `JE-POS-CLOSE-{session}` | نقد أو فروقات صندوق | فروقات صندوق أو نقد | `pos_sessions`, `journal_entries` |
| **الموارد البشرية** |
| 18 | اعتماد سلفة | `JE-LOAN-{id}` | سلف موظفين | نقد | `employee_loans`, `journal_entries` |
| 19 | ترحيل مسير الرواتب | `PAY-{period}-{date}` | رواتب (إجمالي) + تأمينات صاحب عمل | تأمينات مستحقة + سلف + جزاءات + خصومات + بنك (صافي) | `payroll_entries`, `journal_entries` |
| **المخزون** |
| 20 | تسوية مخزون | Auto | مخزون أو مصروف تسوية | مصروف تسوية أو مخزون | `stock_adjustments`, `journal_entries`, `inventory` |
| 21 | تحويل مخزون | Auto (2 JEs) | مخزون مستودع وجهة | مخزون مستودع مصدر | `stock_transfer_log`, `journal_entries`, `inventory` |
| **التصنيع** |
| 22 | بدء الإنتاج | Auto | أعمال تحت التشغيل (WIP) | مخزون مواد أولية | `production_orders`, `journal_entries`, `inventory` |
| 23 | إتمام الإنتاج | Auto | مخزون إنتاج تام | أعمال تحت التشغيل (WIP) | `production_orders`, `journal_entries`, `inventory` |
| **الأصول** |
| 24 | شراء أصل | Auto | أصول ثابتة | نقد/بنك | `assets`, `journal_entries` |
| 25 | إهلاك أصل | `DEP-{asset}-{schedule}` | مصروف إهلاك | إهلاك متراكم | `asset_depreciation_schedule`, `journal_entries` |
| 26 | استبعاد أصل | `DISP-{asset}` | إهلاك متراكم + نقد + خسارة | تكلفة الأصل + ربح | `asset_disposals`, `journal_entries` |
| 27 | تحويل أصل | `ATRN-{asset}` | أصل فرع وجهة | أصل فرع مصدر | `asset_transfers`, `journal_entries` |
| 28 | إعادة تقييم أصل | `AREVAL-{asset}` | أصل (زيادة) | احتياطي إعادة تقييم | `asset_revaluations`, `journal_entries` |
| **الخزينة** |
| 29 | إنشاء حساب خزينة (رصيد) | Auto | حساب GL الخزينة | أرصدة افتتاحية | `treasury_accounts`, `journal_entries` |
| 30 | مصروف خزينة | Auto | حساب المصروف | حساب GL الخزينة | `treasury_transactions`, `journal_entries` |
| 31 | تحويل بين حسابات | Auto | GL الخزينة المستلمة | GL الخزينة المرسلة | `treasury_transactions`, `journal_entries` |
| **الشيكات** |
| 32 | إنشاء شيك مستلم | Auto | شيكات تحت التحصيل | العملاء/AR | `checks_receivable`, `journal_entries` |
| 33 | تحصيل شيك مستلم | Auto | بنك | شيكات تحت التحصيل | `checks_receivable`, `journal_entries` |
| 34 | ارتداد شيك مستلم | Auto (2 JEs) | عكس + شيكات مرتدة | عكس + بنك | `checks_receivable`, `journal_entries` |
| 35 | إصدار شيك | Auto | الموردين/AP | شيكات تحت الدفع | `checks_payable`, `journal_entries` |
| 36 | مقاصة شيك | Auto | شيكات تحت الدفع | بنك | `checks_payable`, `journal_entries` |
| 37 | ارتداد شيك صادر | Auto (2 JEs) | بنك + شيكات تحت الدفع | عكس المقاصة | `checks_payable`, `journal_entries` |
| **أوراق القبض/الدفع** |
| 38-43 | أوراق القبض/الدفع | Auto | مماثل للشيكات | — | `notes_receivable/payable`, `journal_entries` |
| **المشاريع** |
| 44 | مصروف مشروع | Auto | مصروف مشروع | نقد/بنك | `project_expenses`, `journal_entries` |
| 45 | إيراد مشروع | Auto | نقد/عملاء | إيراد مشروع | `project_revenues`, `journal_entries` |
| 46 | فاتورة مشروع | Auto | عملاء | إيراد مشروع | `invoices`, `journal_entries` |
| 47 | إقفال مشروع | Auto | WIP/مؤجل | اعتراف بالإيراد | `projects`, `journal_entries` |
| 48 | فاتورة Retainer | Auto | عملاء | إيراد مؤجل | `invoices`, `journal_entries` |
| **المحاسبة** |
| 49 | أرصدة افتتاحية | `OB-{year}` | أصول/مصروفات | خصوم/ملكية/إيرادات | `journal_entries`, `accounts` |
| 50-52 | قيود الإقفال (3 قيود) | `CLOSE-REV/EXP/IS-{year}` | إيرادات → ملخص دخل → أرباح مبقاة | — | `journal_entries`, `accounts`, `fiscal_years` |
| 53 | إقفال السنة | `CLOSING-{year}` | إيرادات + مصروفات (صفرية) | أرباح مبقاة | `journal_entries`, `fiscal_years` |
| 54 | مخصص ديون معدومة | `PROV-BD-{date}` | مصروف ديون معدومة | مخصص ديون معدومة | `journal_entries` |
| 55 | مخصص إجازات | `PROV-LV-{date}` | مصروف إجازات | مخصص إجازات | `journal_entries` |
| 56 | إعادة تقييم عملات | `FX-REVAL-{date}` | ربح/خسارة عملة | ربح/خسارة (عكس) | `journal_entries`, `accounts` |
| **الضرائب** |
| 57 | دفعة ضريبية | `JE-{num}` | ضريبة مستحقة | بنك/نقد | `tax_payments`, `journal_entries` |
| 58 | تسوية ضريبية | `JE-{num}` | ضريبة مستحقة (صافي) | بنك أو ضريبة مستردة | `journal_entries` |
| **العملات** |
| 59 | إعادة تقييم عملة | Auto | ربح/خسارة FX | ربح/خسارة FX (عكس) | `journal_entries`, `accounts` |
| **المصروفات** |
| 60 | مصروف | `EXP-{num}` | حساب المصروف | نقد/بنك | `expenses`, `journal_entries` |

## 5.3 علاقة القيود بالفترات المحاسبية

- كل قيد له `entry_date` يجب أن يقع ضمن فترة مالية مفتوحة (`fiscal_periods.is_closed = FALSE`)
- عند إقفال فترة (toggle-close)، لا يمكن إنشاء قيود بتاريخ ضمنها
- عند إقفال السنة المالية (`fiscal_years.status = 'closed'`)، يُنشأ قيد إقفال يرحّل الأرباح

---

# 6. التقارير

## 6.1 التقارير المحاسبية

| التقرير | API Endpoint | مصدر البيانات | الفلاتر |
|---------|-------------|---------------|---------|
| ميزان المراجعة | `GET /reports/accounting/trial-balance` | `journal_entries` + `journal_lines` + `accounts` | التاريخ، الفرع |
| ميزان مراجعة مقارن | `GET /reports/accounting/trial-balance/compare` | — | فترتان |
| قائمة الدخل | `GET /reports/accounting/profit-loss` | حسابات إيرادات + مصروفات | التاريخ، الفرع |
| قائمة دخل تفصيلية | `GET /reports/accounting/profit-loss/detailed` | — | بالمنتج/العميل |
| الميزانية العمومية | `GET /reports/accounting/balance-sheet` | حسابات أصول + خصوم + ملكية | التاريخ |
| قائمة التدفقات النقدية | `GET /reports/accounting/cashflow` | حركات الخزينة + القيود | الفترة |
| دفتر الأستاذ العام | `GET /reports/accounting/general-ledger` | `journal_lines` + `accounts` | الحساب، الفترة |
| الموازنة مقابل الفعلي | `GET /reports/accounting/budget-vs-actual` | `budgets` + `budget_items` + `journal_lines` | السنة |
| تحليل أفقي | `GET /reports/accounting/horizontal-analysis` | — | فترتان |
| نسب مالية | `GET /reports/accounting/financial-ratios` | القوائم المالية | — |
| تقرير مراكز التكلفة | `GET /reports/accounting/cost-center-report` | `journal_lines.cost_center_id` | — |

## 6.2 تقارير المبيعات

| التقرير | API Endpoint | مصدر البيانات |
|---------|-------------|---------------|
| ملخص المبيعات | `GET /reports/sales/summary` | `invoices` (type=sales) |
| اتجاه المبيعات | `GET /reports/sales/trend` | `invoices` |
| مبيعات حسب العميل | `GET /reports/sales/by-customer` | `invoices` + `parties` |
| مبيعات حسب المنتج | `GET /reports/sales/by-product` | `invoice_lines` + `products` |
| كشف حساب العميل | `GET /reports/sales/customer-statement/{id}` | `party_transactions` |
| أعمار الديون (AR) | `GET /reports/sales/aging` | `invoices` + `payment_allocations` |
| مبيعات حسب الكاشير | `GET /reports/sales/by-cashier` | `pos_orders` |
| الهدف مقابل الفعلي | `GET /reports/sales/target-vs-actual` | `sales_targets` + `invoices` |
| تقرير العمولات | `GET /reports/sales/commissions/report` | `sales_commissions` |

## 6.3 تقارير المشتريات

| التقرير | API Endpoint | مصدر البيانات |
|---------|-------------|---------------|
| ملخص المشتريات | `GET /reports/purchases/summary` | `invoices` (type=purchase) |
| اتجاه المشتريات | `GET /reports/purchases/trend` | `invoices` |
| مشتريات حسب المورد | `GET /reports/purchases/by-supplier` | `invoices` + `parties` |
| كشف حساب المورد | `GET /reports/purchases/supplier-statement/{id}` | `supplier_transactions` |

## 6.4 تقارير المخزون

| التقرير | API Endpoint | مصدر البيانات |
|---------|-------------|---------------|
| تقييم المخزون | `GET /reports/inventory/valuation` | `inventory` + `products` |
| معدل دوران المخزون | `GET /reports/inventory/turnover` | `inventory_transactions` |
| المخزون الراكد | `GET /reports/inventory/dead-stock` | `inventory_transactions` |
| تكلفة البضاعة المباعة | `GET /reports/inventory/cogs` | `invoice_lines` + `products` |

## 6.5 تقارير الموارد البشرية

| التقرير | API Endpoint | مصدر البيانات |
|---------|-------------|---------------|
| اتجاه الرواتب | `GET /reports/hr/payroll/trend` | `payroll_entries` |
| استخدام الإجازات | `GET /reports/hr/leaves/usage` | `leave_requests` |

## 6.6 التقارير المخصصة والمجدولة

| الوظيفة | API | الجداول |
|---------|-----|---------|
| إنشاء تقرير مخصص | `POST /reports/custom` | `custom_reports` |
| جدولة تقرير | `POST /scheduled-reports/scheduled/` | `scheduled_reports` |
| مشاركة تقرير | `POST /scheduled-reports/share` | `shared_reports` |
| تشغيل تقرير مجدول | `POST /scheduled-reports/scheduled/{id}/run` | — |

**تصدير التقارير:** جميع التقارير المحاسبية تدعم التصدير إلى PDF + Excel عبر endpoints `/export` مع دعم RTL العربي.

---

# 7. الحركات والتأثيرات المتسلسلة

## 7.1 دورة المبيعات الكاملة

```
عرض سعر (SQ) → أمر بيع (SO) → فاتورة بيع (INV) → سند قبض (RCV) → تقارير
     ↓                ↓                ↓                  ↓
sales_quotations  sales_orders     invoices           payment_vouchers
                                    ↓                  ↓
                              journal_entries      journal_entries
                                    ↓                  ↓
                              accounts (أرصدة)    accounts (أرصدة)
                                    ↓
                              inventory (خصم)
                                    ↓
                              party_transactions
```

**عند إنشاء فاتورة بيع:**
1. ✍️ يُنشئ سجل في `invoices` + `invoice_lines`
2. 📒 يُنشئ قيد في `journal_entries` + `journal_lines`:
   - Dr: نقد/بنك (إذا مدفوعة) أو عملاء (AR)
   - Dr: COGS (تكلفة البضاعة)
   - Cr: إيرادات مبيعات
   - Cr: ضريبة مخرجات
   - Cr: مخزون (تخفيض)
3. 📦 يُخفض المخزون في `inventory` + يُنشئ `inventory_transactions`
4. 💰 يُحدّث أرصدة الحسابات في `accounts`
5. 📊 يُنشئ حركة في `party_transactions`
6. 📈 تتأثر التقارير: ميزان المراجعة، قائمة الدخل، الميزانية العمومية، تقارير المبيعات، تقرير المخزون

## 7.2 دورة المشتريات الكاملة

```
RFQ → طلب شراء (PO) → استلام (GRN) → فاتورة شراء → سند صرف → تقارير
  ↓        ↓                ↓               ↓              ↓
rfq    purchase_orders   inventory      invoices     payment_vouchers
                            ↓               ↓              ↓
                      journal_entries  journal_entries  journal_entries
```

## 7.3 دورة مرتجع المبيعات

1. إنشاء المرتجع → `sales_returns` (حالة: draft)
2. اعتماد المرتجع → يُنشئ قيد عكسي:
   - Dr: إيرادات (عكس)
   - Dr: مخزون (إعادة)
   - Cr: نقد/عملاء (رد)
   - Cr: COGS (عكس)
3. يتأثر: `inventory` (زيادة)، `accounts`، `party_transactions`

## 7.4 دورة التصنيع

```
BOM → أمر إنتاج → بدء الإنتاج → إتمام الإنتاج
           ↓              ↓              ↓
    production_orders  صرف مواد      استلام منتج تام
                          ↓              ↓
                     Dr: WIP          Dr: FG Inventory
                     Cr: RM Inv       Cr: WIP
```

## 7.5 دورة الرواتب

```
هيكل رواتب → فترة → توليد مسير → مراجعة → ترحيل
                          ↓                    ↓
                   payroll_entries     Journal Entry:
                                       Dr: رواتب (إجمالي)
                                       Dr: تأمينات صاحب عمل
                                       Cr: تأمينات مستحقة
                                       Cr: سلف (خصم)
                                       Cr: جزاءات (خصم)
                                       Cr: بنك (صافي الراتب)
```

## 7.6 دورة الأصول الثابتة

```
شراء أصل → إنشاء جدول إهلاك → إهلاك دوري → استبعاد
    ↓              ↓                ↓            ↓
Dr: أصل       asset_depreciation   Dr: مصروف   Dr: إهلاك متراكم
Cr: نقد       _schedule            Cr: إهلاك   Dr: نقد (بيع)
                                    متراكم      Dr/Cr: ربح/خسارة
                                                Cr: تكلفة الأصل
```

---

# 8. الصلاحيات والمستخدمون

## 8.1 الأدوار الافتراضية

| الدور | الاسم العربي | الصلاحيات |
|-------|-------------|-----------|
| `superuser` | مدير النظام | `["*"]` — كل شيء |
| `admin` | مدير | `["*"]` — كل شيء |
| `manager` | مدير فرع | المبيعات، المشتريات، المخزون، العقود، POS، عرض التقارير والخزينة |
| `accountant` | محاسب | المحاسبة، الخزينة، المطابقة، الضرائب، العملات، التقارير المالية |
| `sales` | مبيعات | المبيعات، المنتجات، المخزون (عرض)، POS، العقود (عرض) |
| `inventory` | أمين مستودع | المخزون، المنتجات، التصنيع (عرض)، المشتريات (عرض) |
| `cashier` | كاشير | POS، المبيعات (عرض)، المنتجات (عرض) |
| `user` | مستخدم | لوحة التحكم فقط |

## 8.2 هيكل الصلاحيات

الصلاحيات بصيغة: `module.action`

| الوحدة | الأفعال المتاحة |
|--------|-----------------|
| `dashboard` | `view` |
| `accounting` | `view`, `manage` |
| `sales` | `view`, `create`, `reports` |
| `buying` | `view`, `create`, `receive`, `reports` |
| `stock` | `view`, `reports` |
| `treasury` | `view`, `create` |
| `reconciliation` | `view` |
| `hr` | `view`, `reports` |
| `pos` | `view`, `sessions` |
| `manufacturing` | `view` |
| `projects` | `view`, `create`, `edit` |
| `assets` | `view` |
| `expenses` | `view`, `create`, `edit`, `approve` |
| `taxes` | `view`, `manage` |
| `currencies` | `view`, `manage` |
| `reports` | `view`, `create` |
| `audit` | `view` |
| `approvals` | `view`, `create`, `manage` |
| `admin` | `roles` |
| `branches` | `view` |
| `settings` | `view` |
| `data_import` | `view` |
| `products` | `view` |
| `contracts` | `view` |
| `services` | `view` |

## 8.3 تأثير الصلاحيات على الواجهة

- كل Route محمي بـ `PrivateRoute` يتحقق من:
  - هل المستخدم مسجل الدخول (`isAuthenticated()`)
  - هل لديه الصلاحية المطلوبة (`hasPermission(permission)`)
- إذا لم تكن لديه الصلاحية → يُعاد توجيهه إلى `/dashboard` مع رسالة خطأ
- القائمة الجانبية تعرض فقط الوحدات المسموحة بناءً على `enabled_modules` + `permissions`

---

# 9. الإعدادات والتهيئة

## 9.1 إعدادات النظام (`company_settings`)

| المفتاح | القيمة الافتراضية | التأثير |
|---------|-------------------|---------|
| `default_currency` | عملة البلد | العملة الأساسية لكل الحسابات |
| `company_country` | رمز البلد (SA/SY/...) | يحدد الأنظمة الضريبية والإعدادات |
| `fiscal_year_start` | `01-01` | بداية السنة المالية |
| `invoice_prefix` | `INV-` | بادئة ترقيم الفواتير |
| `journal_prefix` | `JE-` | بادئة ترقيم القيود |
| `decimal_places` | `2` | عدد الخانات العشرية |
| `date_format` | `YYYY-MM-DD` | تنسيق التاريخ |
| `timezone` | حسب البلد | المنطقة الزمنية |
| `acc_map_*` | IDs الحسابات | ربط الحسابات بالعمليات التلقائية (انظر القسم 4.2) |

## 9.2 إعدادات البريد الإلكتروني

| المفتاح | الغرض |
|---------|--------|
| `SMTP_HOST` | خادم البريد |
| `SMTP_PORT` | المنفذ |
| `SMTP_USER` | اسم المستخدم |
| `SMTP_PASSWORD` | كلمة المرور |

## 9.3 إعدادات الأمان

| الإعداد | الموقع | التأثير |
|---------|--------|---------|
| `SECRET_KEY` | `.env` | مفتاح تشفير JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `config.py` (default 30) | مدة صلاحية التوكن |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `config.py` (default 7) | مدة صلاحية التجديد |
| Password Policy | `user_2fa_settings`, `password_history` | سياسة كلمات المرور + 2FA |
| Rate Limiting | كود `auth.py` | 10/min, 5/IP, lockout 15min |

## 9.4 قوالب الصناعة (Industry Templates)

| القالب | الوحدات المفعلة |
|--------|-----------------|
| التجزئة (Retail) | محاسبة، مبيعات، مشتريات، مخزون، POS، خزينة، ضرائب، HR |
| المطاعم (F&B) | محاسبة، مبيعات، مخزون، POS، خزينة، ضرائب، HR |
| التصنيع (Manufacturing) | + تصنيع |
| المقاولات (Construction) | + مشاريع، أصول |
| الخدمات (Services) | + CRM، خدمات، مشاريع |
| الجملة (Wholesale) | + CRM |
| نشاط عام (General) | كل الوحدات |

## 9.5 سياسات التكلفة (Costing Policies)

| السياسة | الوصف |
|---------|--------|
| `global_wac` | متوسط مرجح عام (موحد لكل المستودعات) — الافتراضي |
| `per_warehouse_wac` | متوسط مرجح لكل مستودع |
| `hybrid` | مزيج |
| `smart` | ذكي |

تُخزن في `costing_policies` + `costing_policy_details` + `costing_policy_history`

---

# 10. التكاملات الخارجية

## 10.1 ZATCA (هيئة الزكاة والضريبة والجمارك)

| الوظيفة | API | الحالة |
|---------|-----|--------|
| توليد QR Code | `POST /external/zatca/generate-qr` | ✅ مبني |
| توليد زوج مفاتيح | `POST /external/zatca/generate-keypair` | ✅ مبني |
| التحقق من الامتثال | `GET /external/zatca/verify/{invoice_id}` | ✅ مبني |
| محاكاة CSID | `POST /settings/generate-csid` | ✅ محاكاة |
| التسجيل الفعلي في البوابة | — | ⚠️ غير مكتمل |
| إرسال الفواتير للبوابة | — | ⚠️ غير مكتمل |

**أعمدة ZATCA في `invoices`:** `zatca_hash`, `zatca_signature`, `zatca_qr`, `zatca_status`, `zatca_submission_id`

## 10.2 WHT (ضريبة الاستقطاع)

| الوظيفة | API | الحالة |
|---------|-----|--------|
| قائمة المعدلات | `GET /external/wht/rates` | ✅ |
| إنشاء معدل | `POST /external/wht/rates` | ✅ |
| حساب الاستقطاع | `POST /external/wht/calculate` | ✅ |
| تسجيل حركة | `POST /external/wht/transactions` | ✅ |
| قائمة الحركات | `GET /external/wht/transactions` | ✅ |

## 10.3 API Keys & Webhooks

| الوظيفة | API | الجداول |
|---------|-----|---------|
| إنشاء مفتاح API | `POST /external/api-keys` | `api_keys` |
| إنشاء Webhook | `POST /external/webhooks` | `webhooks` |
| سجل الـ Webhooks | `GET /external/webhooks/{id}/logs` | `webhook_logs` |

**أنواع أحداث Webhook المدعومة:** `invoice.created`, `invoice.paid`, `order.created`, `payment.received`, إلخ

## 10.4 البريد الإلكتروني

- خدمة إرسال البريد عبر SMTP في `services/email_service.py`
- تُستخدم لـ: إشعارات، تقارير مجدولة، إشعارات ضريبية، **إعادة تعيين كلمة المرور (جديد)**

## 10.5 تكاملات غير مبنية بعد

| التكامل | الحالة |
|---------|--------|
| بوابات الدفع (Stripe, PayTabs, HyperPay) | ❓ غير مبني |
| WhatsApp Business API | ❓ غير مبني |
| Shopify / WooCommerce / Salla | ❓ غير مبني |
| Aramex / DHL شحن | ❓ غير مبني |
| ZKTeco بصمة | ❓ غير مبني |
| تطبيق الجوال | ❓ غير مبني |

---

# 11. الميزات الجديدة — Phase 4 (System Completion)

## 11.1 قائمة الميزات المُضافة

| الرقم | الميزة | الوحدة | الملفات الجديدة | الجداول الجديدة |
|-------|--------|--------|----------------|-----------------|
| 1 | أوامر التسليم | المبيعات | `routers/delivery_orders.py`, 3 صفحات JSX | `delivery_orders`, `delivery_order_lines` |
| 2 | التكاليف المحمّلة | المشتريات | `routers/landed_costs.py`, 2 صفحة JSX | `landed_costs`, `landed_cost_items`, `landed_cost_allocations` |
| 3 | WPS + السعودة + نهاية الخدمة | الموارد البشرية | `routers/hr_wps_compliance.py`, 3 صفحات JSX | يستخدم `employees` |
| 4 | استيراد كشف البنك | الخزينة | في `system_completion.py`, 1 صفحة JSX | `bank_import_batches`, `bank_import_lines` |
| 5 | حاسبة الزكاة | المحاسبة | في `system_completion.py`, 1 صفحة JSX | `zakat_calculations` |
| 6 | قفل الفترات | المحاسبة | في `system_completion.py`, 1 صفحة JSX | `fiscal_period_locks` |
| 7 | تقارير التوحيد | التقارير | في `system_completion.py`, 1 صفحة JSX | — (يقرأ من جميع الشركات) |
| 8 | النسخ الاحتياطية | الإدارة | في `system_completion.py`, 1 صفحة JSX | `backup_history` |
| 9 | قوالب الطباعة | الإعدادات | في `system_completion.py`, 1 صفحة JSX | `print_templates` |
| 10 | اكتشاف التكرار | النظام | `utils/duplicate_detection.py` | — |
| 11 | قفل الفترة المحاسبية | المحاسبة | `utils/fiscal_lock.py` | `fiscal_period_locks` |
| 12 | تكاليف التصنيع | التصنيع | في `routers/manufacturing/core.py`, 1 صفحة JSX | — |
| 13 | نسيت كلمة المرور | المصادقة | في `routers/auth.py` + 2 صفحة JSX | `password_reset_tokens` |

## 11.2 الجداول الجديدة المُضافة في Phase 4

| # | الجدول | الغرض | PK |
|---|--------|--------|-----|
| 206 | `delivery_orders` | أوامر التسليم | `id` |
| 207 | `delivery_order_lines` | سطور أمر التسليم | `id` |
| 208 | `landed_costs` | التكاليف المحمّلة | `id` |
| 209 | `landed_cost_items` | بنود التكلفة المحمّلة | `id` |
| 210 | `landed_cost_allocations` | توزيع التكاليف على المنتجات | `id` |
| 211 | `print_templates` | قوالب طباعة HTML | `id` |
| 212 | `bank_import_batches` | دُفعات استيراد كشف البنك | `id` |
| 213 | `bank_import_lines` | سطور كشف البنك المستورد | `id` |
| 214 | `zakat_calculations` | سجل حسابات الزكاة | `id` |
| 215 | `fiscal_period_locks` | قفل الفترات المحاسبية | `id` |
| 216 | `backup_history` | سجل النسخ الاحتياطية | `id` |
| sys | `password_reset_tokens` | رموز إعادة تعيين كلمة المرور | `id` (System DB) |

## 11.3 الملفات الجديدة والمعدّلة

### Backend:
- **إنشاء** `routers/delivery_orders.py` — 633 سطر
- **إنشاء** `routers/landed_costs.py` — 424 سطر
- **إنشاء** `routers/hr_wps_compliance.py` — ~600 سطر
- **إنشاء** `routers/system_completion.py` — ~1250 سطر
- **إنشاء** `utils/fiscal_lock.py` — 80 سطر
- **إنشاء** `utils/duplicate_detection.py` — 180 سطر
- **تعديل** `database.py` — إضافة `get_system_completion_tables_sql()` block #15
- **تعديل** `routers/auth.py` — إضافة `/forgot-password` و `/reset-password`
- **تعديل** `routers/manufacturing/core.py` — إضافة calculate-cost + variance report
- **تعديل** `main.py` — تسجيل الـ routers الجديدة

### Frontend:
- **إنشاء** `services/systemCompletion.js` — APIs للميزات الجديدة
- **تعديل** `services/sales.js`, `purchases.js`, `hr.js`, `treasury.js`, `accounting.js`, `index.js`
- **إنشاء** 17 صفحة JSX جديدة في Sales/Buying/HR/Treasury/Accounting/Reports/Admin/Settings/Manufacturing
- **تعديل** `App.jsx` — ~20 مسار جديد
- **تعديل** `locales/ar.json` و `locales/en.json` — ~250 مفتاح ترجمة جديد (13 قسم)
- **تعديل** `pages/Login.jsx` — إضافة رابط "نسيت كلمة المرور"

### وثائق:
- **إنشاء** `docs/ZAKAT_CALCULATION_METHODOLOGY.md` — منهجية حساب الزكاة (ثنائي اللغة)

## 11.4 ملاحظات إقليمية (Saudi-Specific)

الميزات التالية خاصة بالمملكة العربية السعودية (`country_code = 'SA'`):
- **WPS** — نظام حماية الأجور، ملف SIF
- **لوحة السعودة** — برنامج نطاقات
- **نهاية الخدمة** — نظام العمل السعودي مواد 84/85
- **الزكاة** — تطبق على الشركات في الدول ذات الأغلبية المسلمة (السعودية، الإمارات، إلخ)
- **GOSI** — التأمينات الاجتماعية

> الـ Backend يُرجع البيانات للجميع؛ الـ Frontend يعرض تحذيراً للميزات الإقليمية.

---

---

# 12. الميزات الجديدة — Phase 5 (★★★★★ Upgrade)

> **تاريخ الإنجاز:** 2 مارس 2026  
> **الهدف:** الترقية من ~★★★☆☆ إلى ★★★★★ عبر ثلاث مراحل (A + B + C)

## 12.1 ملخص المراحل

| المرحلة | المحتوى | الحالة |
|---------|---------|--------|
| A — توسعة CRM + محاسبة | 6 صفحات CRM جديدة + صفحتا محاسبة متقدمة + 2 router + جداول DB | ✅ مكتملة |
| B — ميزات الذكاء والإدارة | KPI Dashboard, OEE, EVM, Workflow Analytics, Checks Aging, Assets Leases, Security Events | ✅ مكتملة |
| C — سياسات + عقود + POS متقدم | Expense Policies, Contracts, POS Offline + Split Payment + Customer Display | ✅ مكتملة |

---

## 12.2 المرحلة A — توسعة CRM ومحاسبة متقدمة

### 12.2.1 صفحات CRM الجديدة (6 صفحات)

| الصفحة | المسار | الغرض | الملف |
|--------|--------|--------|-------|
| CRMDashboard | `/crm` | لوحة تحكم CRM — KPIs وإحصائيات | `pages/CRM/CRMDashboard.jsx` |
| LeadScoring | `/crm/lead-scoring` | تقييم العملاء المحتملين تلقائياً | `pages/CRM/LeadScoring.jsx` |
| CustomerSegments | `/crm/customer-segments` | تقسيم العملاء إلى شرائح | `pages/CRM/CustomerSegments.jsx` |
| PipelineAnalytics | `/crm/pipeline` | تحليل مسار المبيعات البصري | `pages/CRM/PipelineAnalytics.jsx` |
| CRMContacts | `/crm/contacts` | إدارة جهات الاتصال | `pages/CRM/CRMContacts.jsx` |
| SalesForecasts | `/crm/forecasts` | توقعات المبيعات | `pages/CRM/SalesForecasts.jsx` |

**Endpoints المستخدمة:**
```
GET  /crm/dashboard               → ملخص KPIs
GET  /crm/lead-scoring/rules      → قواعد تقييم العملاء
POST /crm/lead-scoring/calculate  → حساب النقاط
GET  /crm/segments                → الشرائح
POST /crm/segments                → إنشاء شريحة
GET  /crm/contacts                → جهات الاتصال
POST /crm/contacts                → إضافة جهة اتصال
GET  /crm/analytics/pipeline      → تحليل المسار
GET  /crm/analytics/roi           → عائد الاستثمار
GET  /crm/sales-forecasts         → توقعات المبيعات
POST /crm/sales-forecasts         → إنشاء توقع
```

### 12.2.2 صفحات المحاسبة المتقدمة (2 صفحات)

| الصفحة | المسار | الغرض | الملف |
|--------|--------|--------|-------|
| IntercompanyTransactions | `/accounting/intercompany` | معاملات ما بين الشركات | `pages/Accounting/IntercompanyTransactions.jsx` |
| RevenueRecognition | `/accounting/revenue-recognition` | جدولة الإيرادات | `pages/Accounting/RevenueRecognition.jsx` |

**Endpoints المستخدمة:**
```
GET  /accounting/intercompany/transactions        → قائمة المعاملات
POST /accounting/intercompany/transactions        → إنشاء معاملة
GET  /accounting/revenue-recognition/schedules    → جداول الاعتراف
POST /accounting/revenue-recognition/schedules    → إنشاء جدول
POST /accounting/revenue-recognition/schedules/{id}/recognize → تنفيذ الاعتراف
```

### 12.2.3 Routers الجديدة (Backend)

| الملف | البادئة | الحجم | المحتوى |
|-------|---------|-------|---------|
| `backend/routers/finance/intercompany.py` | `/accounting/intercompany` + `/accounting/revenue-recognition` | 407 سطر | معاملات intercompany + جداول revenue recognition |
| `backend/routers/finance/advanced_workflow.py` | `/workflow` | 202 سطر | محرك workflow متقدم + analytics |

**التسجيل في `finance/__init__.py`** (أسطر 26-28 و45-47):
```python
from .intercompany import router as intercompany_router, rev_router
from .advanced_workflow import router as workflow_router
```

### 12.2.4 جداول DB الجديدة (Phase A)

| # | الجدول | الغرض |
|---|--------|--------|
| 217 | `crm_lead_scoring_rules` | قواعد تقييم العملاء المحتملين |
| 218 | `crm_lead_scores` | نتائج التقييم لكل عميل |
| 219 | `crm_customer_segments` | شرائح العملاء |
| 220 | `crm_customer_segment_members` | أعضاء كل شريحة |
| 221 | `crm_contacts` | جهات الاتصال (مستقلة عن parties) |
| 222 | `crm_sales_forecasts` | توقعات المبيعات الدورية |
| 223 | `intercompany_transactions` | معاملات ما بين الشركات |
| 224 | `revenue_recognition_schedules` | جداول الاعتراف بالإيرادات |
| 225 | `marketing_campaigns` | حملات التسويق |
| 226 | `crm_knowledge_base` | قاعدة معرفة CRM |

---

## 12.3 المرحلة B — ميزات إدارية وذكاء الأعمال

### Endpoints المضافة والمتحقق منها (200 OK)

| الوظيفة | Endpoint | Router |
|---------|----------|--------|
| لوحة KPI التنفيذية | `GET /reports/kpi/dashboard` | `reports.py` |
| OEE (كفاءة التصنيع) | `GET /manufacturing/oee` | `manufacturing/core.py` |
| EVM (قيمة المكتسبة للمشاريع) | `GET /projects/{id}/evm` | `projects.py` |
| مخاطر المشاريع | `GET /projects/{id}/risks` | `projects.py` |
| تقادم الشيكات | `GET /checks/aging` | `finance/checks.py` |
| تأجير الأصول | `GET /assets/leases` | `finance/assets.py` |
| ملخص الأحداث الأمنية | `GET /security/events/summary` | `security.py` |
| تحليلات Workflow | `GET /workflow/analytics` | `finance/advanced_workflow.py` |
| تقارير مخصصة | `GET /reports/custom` | `reports.py` |

**تفاصيل لوحة KPI (`GET /reports/kpi/dashboard`):**
- إجمالي المبيعات + نسبة التغيير
- معدل تحصيل الذمم
- دوران المخزون
- ربحية المشاريع
- معدل إكمال الإنتاج (OEE)
- مستوى رضا العملاء (CRM)

**تفاصيل OEE (`GET /manufacturing/oee`):**
- Availability, Performance, Quality
- مقسّم حسب مركز العمل وفترة زمنية

**تفاصيل EVM (`GET /projects/{id}/evm`):**
- PV (القيمة المخططة), EV (القيمة المكتسبة), AC (التكلفة الفعلية)
- CPI, SPI, EAC, ETC, VAC

---

## 12.4 المرحلة C — سياسات المصروفات، العقود، POS المتقدم

### 12.4.1 سياسات المصروفات

| Endpoint | الوظيفة |
|----------|---------|
| `GET /expenses/policies` | قائمة السياسات |
| `POST /expenses/policies` | إنشاء سياسة |
| `PUT /expenses/policies/{id}` | تعديل سياسة |

**السياسات تتحكم في:** الحد الأقصى، الفئات المسموحة، آلية الموافقة، مستوى الموافق.

### 12.4.2 العقود

| Endpoint | الوظيفة |
|----------|---------|
| `GET /contracts` | قائمة العقود |
| `POST /contracts` | إنشاء عقد |
| `PUT /contracts/{id}` | تعديل عقد |
| `GET /contracts/{id}/renewals` | سجل التجديدات |

### 12.4.3 POS B7 — المبيعات المتقدمة

**الملف:** `frontend/src/pages/POS/POSInterface.jsx`

#### أ. وضع عدم الاتصال (Offline Mode)
| العنصر | التفاصيل |
|--------|---------|
| Storage | IndexedDB عبر `POSOfflineManager` |
| اكتشاف الاتصال | `window.addEventListener('online'/'offline')` |
| مؤشر بصري | `pos-connection-badge` في الـ header (أخضر/أحمر) |
| السلوك عند انقطاع الاتصال | الطلبات تُحفظ في IndexedDB بدلاً من الـ API |
| المزامنة التلقائية | عند عودة الاتصال → `syncPendingOrders()` |

> **ملاحظة مهمة:** الوضع يعمل طالما الصفحة مفتوحة في المتصفح — لا يحتاج internet لإتمام الطلبات المعلقة. لدعم فتح الصفحة بدون internet تحتاج PWA + Service Worker (مخطط له في Phase D).

#### ب. الدفع المختلط Split Payment
| الطريقة | الكود |
|---------|-------|
| نقداً | `cash` |
| بطاقة | `card` |
| مدى | `mada` |

- الجلسة تدعم **3 طرق دفع في نفس الوقت**
- يتحقق من أن مجموع المدفوعات = إجمالي الطلب
- كل طريقة لها مبلغ منفصل قابل للتعديل

#### ج. شاشة العميل (Customer Display)
| العنصر | التفاصيل |
|--------|---------|
| الملف | `pages/POS/CustomerDisplay.jsx` |
| الاتصال | `BroadcastChannel('pos-customer-display')` |
| الرسائل المعالجة | `cart_update` → تحديث السلة لحظياً |
| | `thankYou` → رسالة شكر بعد اكتمال الطلب |
| | `idle` → شاشة انتظار |
| مؤشر الاتصال | `liveConnected` badge في شاشة العميل |
| Broadcast من POSInterface | عند كل تغيير في السلة + عند اكتمال الطلب |

---

## 12.5 إصلاحات الـ Frontend (Build Fixes + UX)

### 12.5.1 تحويل alert() → showToast() (27 ملف)

تم تحويل جميع استدعاءات `alert()` المتصفحية إلى `showToast()` من `useToast` hook في الملفات التالية:

| # | الملف |
|---|-------|
| 1 | `pages/Accounting/RevenueRecognition.jsx` |
| 2 | `pages/Accounting/IntercompanyTransactions.jsx` |
| 3 | `pages/CRM/CRMContacts.jsx` |
| 4 | `pages/CRM/SupportTickets.jsx` |
| 5 | `pages/CRM/KnowledgeBase.jsx` |
| 6 | `pages/CRM/MarketingCampaigns.jsx` |
| 7 | `pages/CRM/Opportunities.jsx` |
| 8 | `pages/CRM/CRMHome.jsx` |
| 9 | `pages/Buying/PurchaseCreditNotes.jsx` |
| 10 | `pages/Buying/PurchaseDebitNotes.jsx` |
| 11 | `pages/Buying/SupplierForm.jsx` |
| 12 | `pages/CRM/CustomerSegments.jsx` |
| 13 | `pages/CRM/LeadScoring.jsx` |
| 14 | `pages/Sales/SalesCreditNotes.jsx` |
| 15 | `pages/Sales/SalesDebitNotes.jsx` |
| 16 | `pages/Documents/DocumentManagement.jsx` |
| 17 | `pages/Services/ServiceRequests.jsx` |
| 18 | `pages/Settings/ApiKeys.jsx` |
| 19 | `pages/Settings/Webhooks.jsx` |
| 20 | `pages/Inventory/CycleCounts.jsx` |
| 21 | `pages/Inventory/ProductList.jsx` |
| 22 | `pages/Taxes/TaxCalendar.jsx` |
| 23 | `pages/Taxes/TaxHome.jsx` |
| 24 | `pages/Taxes/TaxReturnDetails.jsx` |
| 25 | `pages/Taxes/WithholdingTax.jsx` |
| 26 | `pages/Finance/ChecksPayable.jsx` |
| 27 | `pages/Finance/ChecksReceivable.jsx` |

**النمط المستخدم:**
```jsx
// قبل
alert('حدث خطأ');

// بعد
const { showToast } = useToast();
showToast('حدث خطأ', 'error');
```

### 12.5.2 إصلاح modal-backdrop → modal-overlay (4 ملفات CRM)

| الملف | التغيير |
|-------|---------|
| `pages/CRM/SupportTickets.jsx` | `modal-backdrop` → `modal-overlay` |
| `pages/CRM/KnowledgeBase.jsx` | `modal-backdrop` → `modal-overlay` |
| `pages/CRM/MarketingCampaigns.jsx` | `modal-backdrop` → `modal-overlay` |
| `pages/CRM/Opportunities.jsx` | `modal-backdrop` → `modal-overlay` |

### 12.5.3 إصلاحات Build

| الملف | المشكلة | الإصلاح |
|-------|---------|---------|
| `pages/HR/PayrollList.jsx` | قوس إغلاق زائد `}}` في نهاية Modal | حذف `}` الزائدة |
| `pages/HR/LoanList.jsx` | نفس المشكلة | نفس الإصلاح |
| `pages/Settings/tabs/AccountingMappingSettings.jsx` | مسار import خاطئ `../../components/common/DateInput` | تصحيح إلى `../../../components/common/DateInput` |

---

## 12.6 التسجيل في App.jsx

**Imports المضافة (Lazy Loading):**
```jsx
// CRM Pages
const CRMDashboard = lazy(() => import('./pages/CRM/CRMDashboard'));
const LeadScoring = lazy(() => import('./pages/CRM/LeadScoring'));
const CustomerSegments = lazy(() => import('./pages/CRM/CustomerSegments'));
const PipelineAnalytics = lazy(() => import('./pages/CRM/PipelineAnalytics'));
const CRMContacts = lazy(() => import('./pages/CRM/CRMContacts'));
const SalesForecasts = lazy(() => import('./pages/CRM/SalesForecasts'));

// Accounting Advanced
const IntercompanyTransactions = lazy(() => import('./pages/Accounting/IntercompanyTransactions'));
const RevenueRecognition = lazy(() => import('./pages/Accounting/RevenueRecognition'));
```

**Routes المضافة:**
```jsx
<Route path="/accounting/intercompany" element={<IntercompanyTransactions />} />
<Route path="/accounting/revenue-recognition" element={<RevenueRecognition />} />
<Route path="/crm" element={<CRMDashboard />} />
<Route path="/crm/lead-scoring" element={<LeadScoring />} />
<Route path="/crm/customer-segments" element={<CustomerSegments />} />
<Route path="/crm/pipeline" element={<PipelineAnalytics />} />
<Route path="/crm/contacts" element={<CRMContacts />} />
<Route path="/crm/forecasts" element={<SalesForecasts />} />
```

---

## 12.7 الترجمات المضافة (ar.json)

أُضيف أكثر من **200 مفتاح ترجمة جديد** في النطاقات التالية:

| النطاق | عدد المفاتيح (تقريبي) | أمثلة |
|--------|----------------------|-------|
| `crm.*` | ~80 | `crm.leadScoring`, `crm.segments`, `crm.contacts`, `crm.forecasts` |
| `accounting.intercompany` | ~20 | `accounting.intercompanyTransactions`, `accounting.eliminations` |
| `accounting.revenueRecognition` | ~20 | `accounting.recognitionSchedule`, `accounting.recognizeRevenue` |
| `pos.offline` | ~15 | `pos.offlineMode`, `pos.pendingSync`, `pos.splitPayment` |
| `workflow.*` | ~15 | `workflow.analytics`, `workflow.steps`, `workflow.conditions` |
| `reports.kpi` | ~10 | `reports.kpiDashboard`, `reports.oee`, `reports.evm` |

---

## 12.8 نتائج اختبار الـ Endpoints (بعد Phase 5)

| Endpoint | HTTP Status | ملاحظة |
|----------|-------------|--------|
| `GET /api/checks/aging` | 200 ✅ | |
| `GET /api/manufacturing/oee` | 200 ✅ | |
| `GET /api/assets/leases` | 200 ✅ | |
| `GET /api/reports/kpi/dashboard` | 200 ✅ | |
| `GET /api/reports/custom` | 200 ✅ | |
| `GET /api/crm/dashboard` | 200 ✅ | |
| `GET /api/accounting/intercompany/transactions` | 200 ✅ | |
| `GET /api/accounting/revenue-recognition/schedules` | 200 ✅ | |
| `GET /api/workflow/analytics` | 200 ✅ | |
| `GET /api/expenses/policies` | 200 ✅ | |
| `GET /api/contracts` | 200 ✅ | |
| `GET /api/security/events/summary` | 200 ✅ | |
| `GET /api/projects/{id}/risks` | 422 ⚠️ | يحتاج project_id صحيح في المسار |

---

## 12.9 حالة الـ Git

| المعلومة | القيمة |
|---------|--------|
| Remote | `https://github.com/AMANCAMSYS/AMAN_ERP.git` |
| Branch | `main` |
| آخر commit | `3f1a356` — "feat: upgrade to ★★★★★ — Phases A+B+C complete" |
| تاريخ الـ Push | 2 مارس 2026 |
| الملفات المتغيرة | 274 ملف (+32,375 / -13,444 سطر) |

---

# 13. الميزات الجديدة — Phase 6 (نظام الميزات حسب النشاط + دمج KPI)

> **تاريخ الإنجاز:** 3 مارس 2026  
> **الهدف:** تخصيص واجهة كل وحدة بحسب نوع النشاط التجاري + دمج مؤشرات الأداء KPI في صفحات التحليلات

## 13.1 نظام الميزات حسب النشاط (INDUSTRY_FEATURES)

### المشكلة التي تم حلها
كانت جميع الميزات تظهر لجميع الشركات بغض النظر عن نوع النشاط — مثلاً "إدارة الطاولات" و"شاشة المطبخ" كانت تظهر لشركة مصنّعة أو تجارة جملة وهي خاصة بالمطاعم فقط.

### الحل: نظام مركزي للميزات المشروطة

**الملف الرئيسي:** `frontend/src/config/industryModules.js`

تمت إضافة خريطة `INDUSTRY_FEATURES` تحدد لكل ميزة الأنشطة المسموح لها بعرضها:

```javascript
export const INDUSTRY_FEATURES = {
  // POS
  'pos.table_management':  ['FB', 'GN'],
  'pos.kitchen_display':   ['FB', 'GN'],
  'pos.customer_display':  ['RT', 'FB', 'PH', 'WK', 'GN'],
  'pos.loyalty':           ['RT', 'FB', 'PH', 'GN'],
  'pos.promotions':        ['RT', 'FB', 'PH', 'WK', 'GN'],
  // Sales
  'sales.contracts':       ['SV', 'CN', 'MF', 'LG', 'WS', 'AG', 'WK', 'GN'],
  'sales.commissions':     'all',
  // Buying
  'buying.rfq':            ['WS', 'MF', 'CN', 'LG', 'AG', 'GN'],
  'buying.agreements':     ['WS', 'MF', 'CN', 'LG', 'AG', 'WK', 'GN'],
  'buying.supplier_ratings': ['WS', 'MF', 'CN', 'GN'],
  // CRM
  'crm.campaigns':         ['RT', 'FB', 'EC', 'SV', 'WK', 'WS', 'GN'],
  'crm.knowledge_base':    ['SV', 'WK', 'CN', 'LG', 'MF', 'GN'],
  // HR
  'hr.custody':            ['MF', 'CN', 'WK', 'LG', 'GN'],
  'hr.overtime':           ['MF', 'CN', 'WK', 'LG', 'FB', 'RT', 'GN'],
  'hr.gosi':               'all',
  'hr.training':           'all',
};
```

**الدوال المساعدة:**

| الدالة | الملف | النوع | الوظيفة |
|--------|-------|-------|---------|
| `hasIndustryFeature(featureKey, industryKey)` | `config/industryModules.js` | عادية | فحص إذا كانت الميزة مسموحة لنشاط معين |
| `getIndustryFeature(featureKey)` | `hooks/useIndustryType.js` | Non-hook | فحص سريع باستخدام النشاط الحالي من localStorage |
| `getIndustryType()` | `hooks/useIndustryType.js` | Non-hook | إرجاع رمز النشاط الحالي (RT/FB/MF/...) |

### الصفحات المُحدّثة (5 صفحات Home)

| الصفحة | الملف | الميزات المشروطة |
|--------|-------|------------------|
| POSHome | `pages/POS/POSHome.jsx` | إدارة الطاولات، شاشة المطبخ، شاشة العميل، الولاء، العروض |
| SalesHome | `pages/Sales/SalesHome.jsx` | العقود |
| BuyingHome | `pages/Buying/BuyingHome.jsx` | طلبات عروض الأسعار (RFQ)، اتفاقيات الشراء، تقييم الموردين |
| CRMHome | `pages/CRM/CRMHome.jsx` | الحملات التسويقية، قاعدة المعرفة |
| HRHome | `pages/HR/HRHome.jsx` | إدارة العهد |

### الأنشطة التجارية الـ 12

| الرمز | النشاط | الاسم بالعربية |
|-------|--------|---------------|
| RT | Retail | التجزئة |
| WS | Wholesale | الجملة |
| FB | Food & Beverage | المطاعم والكافيهات |
| MF | Manufacturing | التصنيع |
| CN | Construction | المقاولات |
| SV | Services | الخدمات |
| PH | Pharmacy | الصيدليات |
| WK | Workshop | الورش والصيانة |
| EC | E-Commerce | التجارة الإلكترونية |
| LG | Logistics | الخدمات اللوجستية |
| AG | Agriculture | الزراعة |
| GN | General | نشاط عام (كل الميزات) |

---

## 13.2 دمج مؤشرات الأداء KPI في صفحات التحليلات (ModuleKPISection)

### المشكلة
كان هناك تكرار بين صفحة `/module/kpi` وصفحة `/module/reports/analytics` — كل منهما يعرض بيانات متشابهة مما يربك المستخدم.

### الحل: مكوّن ModuleKPISection

**الملف:** `frontend/src/components/kpi/ModuleKPISection.jsx`

مكوّن قابل للطي (Collapsible) يُدمج داخل صفحات التحليلات:

```jsx
<ModuleKPISection roleKey="sales" color="#10b981" defaultOpen={false} />
```

**الخصائص (Props):**
| الخاصية | النوع | الوظيفة |
|---------|-------|---------|
| `roleKey` | string | مفتاح الوحدة (sales, procurement, warehouse, hr, manufacturing, projects, pos, crm, financial) |
| `color` | string | لون العنوان |
| `defaultOpen` | boolean | هل يفتح تلقائياً |

**المكونات الداخلية:** `KPICard`, `KPIChart`, `AlertBanner`, `PeriodSelector`

### الصفحات التي دُمج فيها KPI (6 صفحات)

| الصفحة | المسار | مفتاح KPI |
|--------|--------|-----------|
| SalesReports | `/sales/reports/analytics` | `sales` |
| BuyingReports | `/buying/reports/analytics` | `procurement` |
| StockReports | `/stock/reports/balance` | `warehouse` |
| HRReports | `/hr/reports` | `hr` |
| ProductionAnalytics | `/manufacturing/reports/analytics` | `manufacturing` |
| PipelineAnalytics | `/crm/pipeline` | `crm` |

### المسارات المحذوفة (6 مسارات)

تم حذف المسارات المستقلة التالية من `App.jsx` لأن KPI أصبح مدمجاً:
- `/sales/kpi`
- `/buying/kpi`
- `/stock/kpi`
- `/manufacturing/kpi`
- `/hr/kpi`
- `/crm/kpi`

**المسارات المُبقاة (3 مسارات)** — وحدات ليس لها صفحة تحليلات مخصصة:
- `/projects/kpi`
- `/pos/kpi`
- `/accounting/kpi`

---

## 13.3 تحسينات إضافية (Phase 6)

### إصلاح صفحة إعداد النشاط (IndustrySetup)
- **الملف:** `pages/Setup/IndustrySetup.jsx`
- تم إعادة كتابة الصفحة بالكامل لاستخدام CSS Variables بدلاً من Tailwind/DaisyUI
- محاذاة كاملة مع نظام التصميم الموحد للنظام

### تحديث القائمة الجانبية (Sidebar)
- **الملف:** `components/Sidebar.jsx`
- حذف رابط `/kpi` من القائمة الجانبية
- تطبيق فحص ثلاثي المستويات: `enabled_modules` → `isModuleEnabledForIndustry()` → عرض الكل

### الملفات المُعدّلة في Phase 6

| الملف | نوع التعديل |
|-------|-------------|
| `config/industryModules.js` | إضافة INDUSTRY_FEATURES + hasIndustryFeature() |
| `hooks/useIndustryType.js` | إضافة getIndustryFeature() |
| `components/kpi/ModuleKPISection.jsx` | ملف جديد |
| `components/kpi/index.js` | إضافة export |
| `pages/POS/POSHome.jsx` | ميزات مشروطة |
| `pages/Sales/SalesHome.jsx` | عقود مشروطة |
| `pages/Buying/BuyingHome.jsx` | RFQ + اتفاقيات مشروطة |
| `pages/CRM/CRMHome.jsx` | حملات + معرفة مشروطة |
| `pages/HR/HRHome.jsx` | عهد مشروطة |
| `pages/Sales/SalesReports.jsx` | دمج KPI |
| `pages/Buying/BuyingReports.jsx` | دمج KPI |
| `pages/Stock/StockReports.jsx` | دمج KPI |
| `pages/HR/HRReports.jsx` | دمج KPI |
| `pages/Manufacturing/ProductionAnalytics.jsx` | دمج KPI |
| `pages/CRM/PipelineAnalytics.jsx` | دمج KPI |
| `pages/Setup/IndustrySetup.jsx` | إعادة كتابة بالكامل |
| `components/Sidebar.jsx` | حذف /kpi + تحسين فحص الوحدات |
| `App.jsx` | حذف 6 مسارات KPI مستقلة |

---

# 14. تقييم النظام ومقارنته بالأنظمة المحاسبية العالمية

> **بتاريخ:** 3 مارس 2026 — تقييم بكل شفافية

## 14.1 المنهجية

تم مقارنة نظام AMAN ERP مع 7 أنظمة ERP/محاسبية عالمية:
1. **SAP Business One** — ألمانيا | للشركات المتوسطة
2. **Oracle NetSuite** — أمريكا | Cloud ERP
3. **Microsoft Dynamics 365** — أمريكا | Enterprise Suite
4. **Odoo** — بلجيكا | Open Source ERP
5. **QuickBooks Enterprise** — أمريكا | محاسبة SMB
6. **Xero** — نيوزيلندا | Cloud Accounting
7. **Sage X3** — بريطانيا | Mid-Market ERP

## 14.2 جدول المقارنة الشامل

### 14.2.1 الوحدات الأساسية

| الميزة | AMAN | SAP B1 | NetSuite | D365 | Odoo | QuickBooks | Xero | Sage |
|--------|------|--------|----------|------|------|------------|------|------|
| المحاسبة العامة (GL) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| شجرة حسابات متعددة المستويات | ✅ 3 مستويات | ✅ 5+ | ✅ عدد غير محدود | ✅ | ✅ | ✅ 4 | ✅ | ✅ |
| القيود التلقائية الكاملة | ✅ 75+ نقطة | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| ميزان المراجعة | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| قائمة الدخل | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| الميزانية العمومية | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| قائمة التدفقات النقدية | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| الموازنات | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ جزئي | ❌ | ✅ |
| مراكز التكلفة | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| السنوات المالية والإقفال | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| تعدد العملات | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ جزئي | ✅ | ✅ |
| إعادة تقييم العملات | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |

### 14.2.2 المبيعات والمشتريات

| الميزة | AMAN | SAP B1 | NetSuite | D365 | Odoo | QuickBooks | Xero | Sage |
|--------|------|--------|----------|------|------|------------|------|------|
| عروض أسعار → أوامر → فواتير | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ جزئي | ✅ جزئي | ✅ |
| إشعارات دائنة/مدينة | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| أوامر التسليم | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| العمولات | ✅ | ⚠️ إضافي | ✅ | ✅ | ⚠️ إضافي | ❌ | ❌ | ⚠️ |
| العقود | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| RFQ (طلبات عروض الأسعار) | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| التكاليف المحمّلة (Landed Costs) | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| تقييم الموردين | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ❌ | ❌ | ⚠️ |
| اتفاقيات الشراء الإطارية | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |

### 14.2.3 المخزون

| الميزة | AMAN | SAP B1 | NetSuite | D365 | Odoo | QuickBooks | Xero | Sage |
|--------|------|--------|----------|------|------|------------|------|------|
| تعدد المستودعات | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| التحويلات بين المستودعات | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| التسويات | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| الأرقام التسلسلية | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ❌ | ✅ |
| أرقام الدُفعات (Batches) | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| الشحنات الصادرة/الواردة | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| فحوصات الجودة | ✅ | ⚠️ إضافي | ✅ | ✅ | ✅ | ❌ | ❌ | ⚠️ |
| الجرد الدوري | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| مواقع التخزين (Bins) | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| المجموعات (Kits) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| سياسات تسعير (WAC / FIFO) | ✅ WAC فقط | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

### 14.2.4 التصنيع

| الميزة | AMAN | SAP B1 | NetSuite | D365 | Odoo | QuickBooks | Xero | Sage |
|--------|------|--------|----------|------|------|------------|------|------|
| قوائم المواد (BOM) | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| أوامر الإنتاج | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| MRP (تخطيط احتياجات المواد) | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| مراكز العمل والمسارات | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| بطاقات العمل (Job Cards) | ✅ | ⚠️ | ✅ | ✅ | ✅ | ❌ | ❌ | ⚠️ |
| OEE (كفاءة المعدات) | ✅ | ⚠️ إضافي | ✅ | ✅ | ⚠️ إضافي | ❌ | ❌ | ⚠️ |
| تكاليف التصنيع والانحرافات | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| جدول الإنتاج | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |

### 14.2.5 نقاط البيع (POS)

| الميزة | AMAN | SAP B1 | NetSuite | D365 | Odoo | QuickBooks | Xero | Sage |
|--------|------|--------|----------|------|------|------------|------|------|
| واجهة بيع سريعة | ✅ | ⚠️ إضافي | ⚠️ إضافي | ✅ | ✅ | ✅ | ❌ | ❌ |
| إدارة الطاولات (مطاعم) | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| شاشة المطبخ | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| شاشة العميل | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| العروض الترويجية | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| برامج الولاء | ✅ | ⚠️ | ⚠️ | ✅ | ✅ | ❌ | ❌ | ❌ |
| وضع عدم الاتصال | ✅ IndexedDB | ❌ | ❌ | ✅ | ✅ PWA | ❌ | ❌ | ❌ |
| Split Payment | ✅ 3 طرق | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| طباعة حرارية | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |

### 14.2.6 الموارد البشرية

| الميزة | AMAN | SAP B1 | NetSuite | D365 | Odoo | QuickBooks | Xero | Sage |
|--------|------|--------|----------|------|------|------------|------|------|
| إدارة الموظفين | ✅ | ⚠️ أساسي | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| مسيرات الرواتب | ✅ | ⚠️ | ✅ | ✅ | ✅ | ✅ | ⚠️ Gusto | ✅ |
| الإجازات والحضور | ✅ | ❌ | ✅ | ✅ | ✅ | ⚠️ | ❌ | ✅ |
| السلف والقروض | ✅ | ❌ | ⚠️ | ✅ | ✅ | ❌ | ❌ | ⚠️ |
| التأمينات الاجتماعية (GOSI) | ✅ 🇸🇦 | ❌ | ❌ | ⚠️ | ❌ | ❌ | ❌ | ❌ |
| WPS (حماية الأجور) | ✅ 🇸🇦 | ❌ | ❌ | ⚠️ | ❌ | ❌ | ❌ | ❌ |
| نسبة السعودة (نطاقات) | ✅ 🇸🇦 | ❌ | ❌ | ⚠️ | ❌ | ❌ | ❌ | ❌ |
| نهاية الخدمة (مواد 84/85) | ✅ 🇸🇦 | ❌ | ❌ | ⚠️ | ❌ | ❌ | ❌ | ❌ |
| التوظيف والاستقطاب | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | ⚠️ |
| تقييم الأداء | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | ⚠️ |
| البرامج التدريبية | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | ⚠️ |
| العهد والممتلكات | ✅ | ❌ | ⚠️ | ⚠️ | ⚠️ | ❌ | ❌ | ❌ |

### 14.2.7 الخزينة والأوراق التجارية

| الميزة | AMAN | SAP B1 | NetSuite | D365 | Odoo | QuickBooks | Xero | Sage |
|--------|------|--------|----------|------|------|------------|------|------|
| إدارة الصناديق والبنوك | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| التحويلات بين الحسابات | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| المطابقة البنكية | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| استيراد كشف البنك CSV | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| شيكات مستلمة/صادرة | ✅ | ✅ | ⚠️ | ✅ | ⚠️ | ✅ | ❌ | ✅ |
| أوراق قبض/دفع (كمبيالات) | ✅ | ⚠️ | ❌ | ⚠️ | ❌ | ❌ | ❌ | ⚠️ |
| تقادم الشيكات | ✅ | ⚠️ | ❌ | ⚠️ | ❌ | ❌ | ❌ | ❌ |

### 14.2.8 CRM

| الميزة | AMAN | SAP B1 | NetSuite | D365 | Odoo | QuickBooks | Xero | Sage |
|--------|------|--------|----------|------|------|------------|------|------|
| فرص المبيعات | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ⚠️ |
| تذاكر الدعم | ✅ | ⚠️ | ✅ | ✅ | ✅ | ❌ | ❌ | ⚠️ |
| حملات تسويقية | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ⚠️ |
| قاعدة معرفة | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| تقييم العملاء المحتملين | ✅ | ⚠️ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| شرائح العملاء | ✅ | ⚠️ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| تحليل مسار المبيعات | ✅ | ⚠️ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| توقعات المبيعات | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ⚠️ |

### 14.2.9 المشاريع والأصول

| الميزة | AMAN | SAP B1 | NetSuite | D365 | Odoo | QuickBooks | Xero | Sage |
|--------|------|--------|----------|------|------|------------|------|------|
| إدارة المشاريع والمهام | ✅ | ⚠️ | ✅ | ✅ | ✅ | ❌ | ✅ جزئي | ✅ |
| EVM (القيمة المكتسبة) | ✅ | ❌ | ⚠️ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Retainer (دفعات مقدمة) | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ❌ | ❌ | ⚠️ |
| أوامر التغيير | ✅ | ❌ | ✅ | ✅ | ⚠️ | ❌ | ❌ | ⚠️ |
| الأصول الثابتة | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| الإهلاك التلقائي | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| إعادة تقييم الأصول | ✅ | ✅ | ✅ | ✅ | ⚠️ | ❌ | ❌ | ✅ |
| تأجير الأصول | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ❌ | ❌ | ✅ |

### 14.2.10 الضرائب والامتثال

| الميزة | AMAN | SAP B1 | NetSuite | D365 | Odoo | QuickBooks | Xero | Sage |
|--------|------|--------|----------|------|------|------------|------|------|
| ضريبة القيمة المضافة (VAT) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| الإقرارات الضريبية | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| ضريبة الاستقطاع (WHT) | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| حاسبة الزكاة | ✅ 🇸🇦 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| ZATCA QR Code | ✅ | ✅ | ❌ | ✅ | ⚠️ | ❌ | ❌ | ⚠️ |
| ZATCA e-Invoicing (فاتورة) | ⚠️ جزئي | ✅ | ❌ | ✅ | ⚠️ | ❌ | ❌ | ⚠️ |
| التقويم الضريبي | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| قفل الفترات المحاسبية | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

### 14.2.11 ميزات تقنية وأمنية

| الميزة | AMAN | SAP B1 | NetSuite | D365 | Odoo | QuickBooks | Xero | Sage |
|--------|------|--------|----------|------|------|------------|------|------|
| Multi-Tenant (تعدد الشركات) | ✅ DB/شركة | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| REST API كامل | ✅ 767 API | ✅ | ✅ | ✅ | ✅ (XML-RPC + REST) | ⚠️ | ✅ | ✅ |
| Webhooks | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | ⚠️ |
| API Keys | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 2FA (مصادقة ثنائية) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| سجل التدقيق (Audit Log) | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ |
| أدوار وصلاحيات مرنة | ✅ 8 أدوار | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Workflow/الموافقات | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| تقارير مجدولة بالبريد | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ | ✅ |
| تصدير PDF + Excel | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| دعم RTL العربي | ✅ كامل | ⚠️ | ⚠️ | ✅ | ⚠️ | ❌ | ❌ | ❌ |
| Open Source | ❌ | ❌ | ❌ | ❌ | ✅ (Community) | ❌ | ❌ | ❌ |

---

## 14.3 تقييم AMAN ERP — نقاط القوة (ما يتفوق فيه على غيره)

### 🟢 متفوق بشكل واضح

| النقطة | التفاصيل |
|--------|---------|
| **1. الامتثال السعودي الشامل** | AMAN هو النظام الوحيد الذي يدمج GOSI + WPS + نطاقات + نهاية الخدمة (مواد 84/85) + حاسبة الزكاة (هجري 2.5% / ميلادي 2.5775%) في نظام واحد. الأنظمة الأخرى تحتاج شراء إضافات (add-ons) أو تطوير مخصص. |
| **2. الأوراق التجارية (شيكات + كمبيالات)** | نظام شيكات وأوراق قبض/دفع كامل مع تدفقات متعددة (إنشاء → تحصيل ← ارتداد + بروتستو). NetSuite وXero وQuickBooks لا تدعم هذا. خاصية حيوية في السوق العربي. |
| **3. التخصيص حسب النشاط (12 نشاط)** | نظام INDUSTRY_FEATURES يخفي/يعرض ميزات تلقائياً بحسب نوع الشركة (مطعم، تصنيع، صيدلية...). Odoo يقدم شيئاً مشابهاً لكن بمستوى Module وليس Feature. SAP/NetSuite يحتاجان تخصيص يدوي. |
| **4. POS متكامل مع المحاسبة** | واجهة POS + الطاولات + المطبخ + شاشة العميل + Offline + Split Payment + الولاء — مدمجة مباشرة مع المحاسبة. SAP B1 وNetSuite يحتاجان تكامل خارجي. |
| **5. دعم RTL العربي الكامل** | واجهة مصممة أصلاً بالعربية مع CSS Variables وRTL. الأنظمة الغربية تعاني من مشاكل RTL حتى عند ترجمتها. |
| **6. التكلفة** | بدون رسوم ترخيص — AMAN مملوك بالكامل. SAP B1 يبدأ من $3,213/مستخدم، NetSuite من $999/شهر. |
| **7. الاستقلالية** | Self-hosted، لا يعتمد على مزوّد سحابي. بيانات الشركة تبقى تحت سيطرتها الكاملة. |
| **8. EVM للمشاريع** | Earned Value Management مدمج — SAP B1 وOdoo لا يدعمانه بشكل أصلي. |

---

## 14.4 تقييم AMAN ERP — نقاط الضعف (ما يتفوق فيه الآخرون)

### 🔴 يحتاج تطوير

| النقطة | التفاصيل | المنافسون |
|--------|---------|-----------|
| **1. تطبيق الجوال** | لا يوجد تطبيق iOS/Android. الواجهة تعمل على المتصفح فقط. | Odoo ✅ تطبيق أصلي، D365 ✅، SAP B1 ✅، QuickBooks ✅ |
| **2. ZATCA e-Invoicing (الربط الفعلي)** | QR Code والتجزئة مبنيان، لكن إرسال الفواتير الفعلي لبوابة ZATCA غير مكتمل. | SAP B1 ✅ كامل، Odoo ✅ عبر إضافات |
| **3. بوابات الدفع الإلكتروني** | لا يوجد تكامل مع Stripe, PayTabs, HyperPay, مدى Pay. | جميع المنافسين ✅ |
| **4. تكامل التجارة الإلكترونية** | لا يوجد ربط مع Shopify, WooCommerce, Salla, Zid. | Odoo ✅، NetSuite ✅، D365 ✅ |
| **5. تكامل WhatsApp / SMS** | لا يوجد. | D365 ✅، Odoo ⚠️ إضافة |
| **6. تكامل الشحن** | لا يوجد ربط مع Aramex, DHL, SMSA Express. | NetSuite ✅، Odoo ✅ عبر إضافات |
| **7. تطبيق الحضور (بصمة)** | لا يوجد ربط مع ZKTeco أو أجهزة البصمة. | SAP ✅ عبر إضافات، D365 ✅ |
| **8. PWA / Service Worker** | وضع Offline يعمل فقط إذا الصفحة مفتوحة — لا يمكن فتح الصفحة بدون إنترنت. | Odoo POS ✅ PWA كامل |
| **9. الذكاء الاصطناعي** | لا يوجد AI/ML مدمج (لا تنبؤ طلب، لا تصنيف تلقائي، لا chatbot). | D365 ✅ Copilot AI، NetSuite ✅، SAP ✅ |
| **10. Marketplace / إضافات** | لا توجد منصة إضافات — أي ميزة جديدة تحتاج تطوير في الكود المصدري. | Odoo ✅ 44,000+ app، SAP ✅، NetSuite ✅ |
| **11. Multi-Language حقيقي** | العربية + الإنجليزية فقط. | Odoo ✅ 50+ لغة، SAP B1 ✅ 28 لغة |
| **12. سياسة التكلفة** | WAC (متوسط مرجح) فقط — لا FIFO ولا LIFO ولا Specific Identification. | جميع المنافسين يدعمون 3+ سياسات |
| **13. الاختبارات الحية** | 48 ملف اختبار موجود لكن لا CI/CD pipeline فعّال ولا اختبارات تكامل حقيقية. | أنظمة مؤسسية لديها آلاف الاختبارات + CI/CD |
| **14. توثيق للمستخدم النهائي** | لا يوجد User Manual أو Help Center أو فيديوهات تعليمية. | جميع المنافسين ✅ |
| **15. شجرة الحسابات** | 3 مستويات تقريباً — بعض الشركات تحتاج 5+ مستويات. | SAP 5+، NetSuite غير محدود |

---

## 14.5 تقييم شامل — درجات التصنيف

> **المقياس:** 1 (ضعيف) → 5 (ممتاز)

| الفئة | AMAN | SAP B1 | NetSuite | D365 | Odoo | QuickBooks | Xero |
|-------|------|--------|----------|------|------|------------|------|
| المحاسبة الأساسية | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| المبيعات والمشتريات | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| المخزون | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| التصنيع | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ | ❌ |
| نقاط البيع | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ❌ |
| الموارد البشرية | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ❌ |
| CRM | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ | ❌ |
| المشاريع | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ | ⭐⭐ |
| الضرائب السعودية | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ❌ | ❌ |
| الأوراق التجارية | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ❌ |
| واجهة المستخدم العربية | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| **التكاملات الخارجية** | **⭐⭐** | **⭐⭐⭐⭐⭐** | **⭐⭐⭐⭐⭐** | **⭐⭐⭐⭐⭐** | **⭐⭐⭐⭐⭐** | **⭐⭐⭐⭐** | **⭐⭐⭐⭐** |
| **تطبيق الجوال** | **⭐** | **⭐⭐⭐⭐** | **⭐⭐⭐⭐** | **⭐⭐⭐⭐⭐** | **⭐⭐⭐⭐** | **⭐⭐⭐⭐⭐** | **⭐⭐⭐⭐⭐** |
| **النضج والموثوقية** | **⭐⭐⭐** | **⭐⭐⭐⭐⭐** | **⭐⭐⭐⭐⭐** | **⭐⭐⭐⭐⭐** | **⭐⭐⭐⭐** | **⭐⭐⭐⭐⭐** | **⭐⭐⭐⭐⭐** |
| **المجتمع والدعم** | **⭐** | **⭐⭐⭐⭐⭐** | **⭐⭐⭐⭐⭐** | **⭐⭐⭐⭐⭐** | **⭐⭐⭐⭐⭐** | **⭐⭐⭐⭐⭐** | **⭐⭐⭐⭐** |

---

## 14.6 التقييم العام بالأرقام

| المقياس | AMAN | المتوسط العالمي (7 أنظمة) |
|---------|------|---------------------------|
| عدد الوحدات المدمجة | **16** وحدة | 10-20 وحدة |
| عدد الـ API Endpoints | **767** | 500-5,000+ |
| عدد الجداول | **244** | 200-2,000+ |
| سطور الكود | **187,028** (BE+FE) | 500K-50M+ |
| سنوات التطوير | **< 1 سنة** | **5-30 سنة** |
| فريق التطوير | **1-2 مطور** | **100-10,000+ مطور** |
| سعر الترخيص | **$0** (مملوك) | **$999-$50,000+/سنة** |
| عدد الاختبارات | **48** ملف | **1,000-100,000+** |
| توثيق المستخدم | **0** صفحة | **500-10,000+ صفحة** |

---

## 14.7 الخلاصة — تقييم صريح وشفاف

### 📌 أين يقف AMAN ERP اليوم؟

نظام AMAN ERP — بالنسبة لفريق تطوير مكوّن من شخص أو شخصين وفي أقل من سنة — هو **إنجاز تقني استثنائي**. يغطي وحدات لا تتوفر مجتمعة إلا في أنظمة تكلّف آلاف الدولارات شهرياً.

**التصنيف الإجمالي: ★★★★☆ (4 من 5)**

| الجانب | التقييم | السبب |
|--------|---------|-------|
| اكتمال الكود | ★★★★★ | 767 API, 309 صفحة, 244 جدول — اكتمال وظيفي ممتاز |
| جودة المحاسبة | ★★★★★ | 75+ قيد تلقائي، COA متعدد المستويات، إقفال سنوي، أوراق تجارية |
| الامتثال السعودي | ★★★★★ | الأفضل بين جميع المنافسين — GOSI + WPS + نطاقات + زكاة + نهاية خدمة |
| واجهة المستخدم | ★★★★☆ | جميلة ومتناسقة لكن تحتاج UX testing على مستخدمين حقيقيين |
| التكاملات الخارجية | ★★☆☆☆ | أضعف نقطة — لا بوابات دفع ولا تجارة إلكترونية ولا WhatsApp |
| الجاهزية للإنتاج | ★★★☆☆ | يحتاج: اختبارات شاملة + CI/CD + توثيق + مراجعة أمنية |
| قابلية التوسع | ★★★☆☆ | DB-per-tenant جيد لكن لا horizontal scaling ولا caching layer فعّال |
| الدعم والمجتمع | ★☆☆☆☆ | لا يوجد — يحتاج: توثيق، فيديوهات، منتدى، فريق دعم |

### 🎯 الأولويات القادمة (مُرتّبة حسب الأهمية)

| الأولوية | المهمة | التأثير |
|----------|--------|---------|
| 1 | **إكمال ZATCA e-Invoicing** | مطلوب قانونياً في السعودية |
| 2 | **تطبيق جوال (React Native / Flutter)** | 70% من المستخدمين يريدون تطبيق |
| 3 | **بوابات دفع (مدى / Apple Pay / Stripe)** | ضروري لـ POS والتجارة الإلكترونية |
| 4 | **CI/CD + اختبارات تكامل** | ضمان الجودة والاستقرار |
| 5 | **توثيق المستخدم النهائي** | شرط أساسي لبيع المنتج |
| 6 | **PWA + Service Worker** | POS يعمل بدون إنترنت بالكامل |
| 7 | **تكامل Salla/Shopify** | فتح سوق التجارة الإلكترونية |
| 8 | **FIFO + Specific Cost** | سياسات تكلفة إضافية للمخزون |
| 9 | **WhatsApp Business API** | إشعارات للعملاء |
| 10 | **Marketplace للإضافات** | قابلية توسع بدون تعديل الكود |

---

## 14.8 ملاحظات تقنية من الفحص الشامل

### مشاكل مُكتشفة (غير حرجة)

| المشكلة | الشدّة | التفاصيل |
|---------|--------|---------|
| عدد الجداول في root endpoint قديم | منخفضة | يعرض 178 بدلاً من 244 |
| 5 جداول مكررة في database.py | متوسطة | `budget_items`, `commission_rules`, `customer_price_list_items`, `sales_commissions`, `stock_transfer_log` |
| عمود `logo_url` مكرر في `system_companies` | متوسطة | يُعرّف مرتين في نفس الجدول |
| لا يوجد PATCH endpoints | معلوماتية | كل التحديثات عبر PUT (يرسل الكائن كاملاً) |
| ملف `routers/inventory/notifications.py` غير مُستخدم | منخفضة | موجود لكن غير مسجل في __init__.py |

| البند | Phase 4 | Phase 5 (★★★★★) | Phase 6 (الحالي) |
|-------|---------|----------------|------------------|
| صفحات الواجهة الأمامية | ~248 صفحة JSX | ~262 صفحة JSX | **309 صفحة JSX** |
| مسارات (Routes) | ~165 route | ~175 route | **267 route** |
| جداول قاعدة البيانات | ~216 جدول | ~226 جدول | **244 جدول** |
| API Endpoints | ~542+ endpoint | ~600+ endpoint | **767 endpoint** |
| سطور Backend | — | — | **88,268 سطر** |
| سطور Frontend | — | — | **98,760 سطر** |
| القيود التلقائية | 70+ نقطة توليد | 75+ نقطة توليد | 75+ نقطة توليد |
| حسابات شجرة الحسابات الافتراضية | ~80 حساب | ~80 حساب | ~80 حساب |
| ربط حسابات تلقائي (Mappings) | ~45 mapping | ~45 mapping | ~45 mapping |
| الأدوار الافتراضية | 8 أدوار | 8 أدوار | 8 أدوار |
| التقارير | ~46 تقرير + مخصصة | ~55 تقرير + مخصصة | ~55 تقرير + مخصصة |
| قوالب الصناعة | 7 قوالب | 7 قوالب | **12 نشاط** |
| ملفات الترجمة | +13 قسم | +19 قسم | +19 قسم |
| صفحات CRM | 3 صفحات | 9 صفحات | **11 صفحة** |
| وضع POS الغير متصل | ❌ | ✅ IndexedDB | ✅ IndexedDB |
| Split Payment | 2 طرق | 3 طرق (cash/card/mada) | 3 طرق |
| شاشة العميل (Customer Display) | ❌ | ✅ BroadcastChannel | ✅ (مشروطة بالنشاط) |
| نظام ميزات حسب النشاط | ❌ | ❌ | **✅ 16 قاعدة** |
| KPI مدمج في التحليلات | ❌ | ❌ | **✅ 6 صفحات** |

---

# 15. تقرير الفحص العميق لجاهزية الإنتاج (Production Readiness Deep Audit)

> **تاريخ الفحص:** 3 مارس 2026  
> **نوع الفحص:** فحص معماري + محاسبي + أمني + أداء  
> **المنهجية:** فحص مباشر للكود المصدري (Code-level Audit) وليس مراجعة نظرية

---

## 15.1 الثغرات المحاسبية والمالية

### 15.1.1 توازن القيد المزدوج (Double-Entry Integrity)

| # | المشكلة | الشدة | الملف | التفاصيل |
|---|---------|-------|-------|----------|
| 1 | **التحقق من التوازن يتم قبل التحويل وليس بعده** | متوسطة | `utils/accounting.py` | يتم التحقق أن `sum(debits) == sum(credits)` قبل الإدراج في DB، لكن الأرقام تُمرر كـ `float` وليس `Decimal` — أخطاء الفاصلة العائمة قد تتراكم في فواتير بعشرات البنود |
| 2 | **ترحيل الرواتب يتخطى بنود بدون حسابات** | عالية | `routers/hr/core.py` خطوط 973-1065 | إذا لم يوجد `acc_map_gosi_expense` أو `acc_map_loans_adv`، يتم تخطي السطر بدون خطأ — النتيجة: قيد غير متوازن (Dr > Cr أو العكس) يُرحل بنجاح |
| 3 | **لا يوجد فحص نهائي post-insert** | منخفضة | `utils/accounting.py` | لا يوجد `SELECT SUM(debit),SUM(credit) FROM journal_lines WHERE entry_id=X` بعد الإدراج للتأكد من التوازن |

### 15.1.2 مشاكل التقريب العشري (Rounding)

| # | المشكلة | الشدة | الملف | التفاصيل |
|---|---------|-------|-------|----------|
| 4 | **حساب الضريبة بدون `Decimal`** | عالية | `routers/sales/invoices.py` خطوط 110-125 | `tax = line_total * tax_rate / 100` — يستخدم `float` — مثال: `119.99 * 15 / 100 = 17.9985` يتم تمريره بدون تقريب ← فرق ريال في فواتير كبيرة |
| 5 | **POS: الضريبة تُحسب على المبلغ قبل الخصم** | عالية | `routers/pos.py` خطوط 376-380 | `tax = price * qty * tax_rate / 100` ثم `discount = subtotal * discount_pct / 100` — الخصم يُطبق على الإجمالي لكن الضريبة على السعر الأصلي — مخالف لأنظمة ZATCA |
| 6 | **الزكاة: جميع الحسابات بـ `float()`** | متوسطة | `routers/system_completion.py` خطوط 347-535 | حساب الزكاة يستخدم `float()` بالكامل — لالتزام ضريبي قانوني، يجب استخدام `Decimal` |
| 7 | **معدل الزكاة الميلادي تقريبي** | منخفضة | `system_completion.py` | يستخدم `2.5775%` بينما القيمة الدقيقة `2.5776...%` — الفرق 18 ريال لكل 10 مليون ريال |

### 15.1.3 مشاكل قفل الفترات المحاسبية

| # | المشكلة | الشدة | الملف | التفاصيل |
|---|---------|-------|-------|----------|
| 8 | **قفل الفترة موجود لكن غير مُفعّل!** | حرجة | `utils/fiscal_lock.py` + جميع الـ routers | الدالة `check_fiscal_period_open()` مُعرّفة بـ 50 سطر لكن **لا يتم استدعاؤها من أي router** — يمكن إنشاء فواتير وترحيل رواتب وإجراء تسويات في فترة مقفلة |
| 9 | **القيود اليدوية تستخدم جدولاً مختلفاً** | متوسطة | `routers/finance/accounting.py` خط 533 | القيود اليدوية تفحص `fiscal_periods.is_closed` بينما القفل الجديد في `fiscal_period_locks` — نظامان متوازيان لا يتحدثان |

### 15.1.4 مشاكل الزكاة وتصنيف الحسابات

| # | المشكلة | الشدة | الملف | التفاصيل |
|---|---------|-------|-------|----------|
| 10 | **تصنيف الحسابات بالبادئة خاطئ** | متوسطة | `system_completion.py` خط 443 | `account_code LIKE '13%'` يُستخدم لـ "الاستثمارات طويلة الأجل" لكن في شجرة الحسابات `13xx` = أصول غير ملموسة — الاستثمارات في `12xx` |

---

## 15.2 مخاطر التزامن والأداء (Concurrency & Performance)

### 15.2.1 مشاكل حرجة في التزامن

| # | المشكلة | الشدة | الملف | الأثر |
|---|---------|-------|-------|-------|
| 11 | **لا يوجد `SELECT FOR UPDATE` على المخزون** | حرجة | `routers/inventory/transfers.py` خطوط 60-78 | عمليتان متزامنتان تقرأان نفس الرصيد (100 وحدة) → كلاهما يخصمان 80 → الرصيد يصبح 20 بدلاً من -60 → **مخزون وهمي** |
| 12 | **POS فتح وردية — Race Condition (TOCTOU)** | عالية | `routers/pos.py` خطوط 40-46 | Check-then-insert بدون قفل → طلبان متزامنان ينشئان ورديتين مفتوحتين لنفس الكاشير |
| 13 | **POS إغلاق وردية — لا يوجد row lock** | متوسطة | `routers/pos.py` خطوط 158-206 | إغلاق مزدوج يُنشئ قيدين محاسبيين لفروقات الصندوق |
| 14 | **ترقيم الفواتير بدون قفل تسلسلي** | عالية | عدة routers في sales/purchases | `SELECT MAX(number)` ثم `+1` بدون `FOR UPDATE` → أرقام فواتير مكررة |

### 15.2.2 مشاكل اتصالات قاعدة البيانات

| # | المشكلة | الشدة | الملف | الأثر |
|---|---------|-------|-------|-------|
| 15 | **تخزين مؤقت غير محدود لمحركات الشركات** | عالية | `database.py` خطوط 50-59 | كل شركة = Engine بـ 10 pool + 20 overflow — مع 100 شركة = **3,000 اتصال** — PostgreSQL الافتراضي يدعم 100 فقط |
| 16 | **الجدولة تسرّب اتصالات** | متوسطة | `services/scheduler.py` خطوط 144-146 | `get_company_engine()` في كل دورة (5 دقائق) بدون `engine.dispose()` |
| 17 | **لا يوجد connection pooling مركزي** | متوسطة | `database.py` | كل محرك له pool مستقل — لا PgBouncer أو مجمع مركزي |

### 15.2.3 العمليات الثقيلة (Heavy Operations)

| العملية | المشكلة المحتملة | الحل المقترح |
|---------|-----------------|--------------|
| ترحيل مسير الرواتب (100+ موظف) | يُنشئ قيداً بـ 200+ سطر في transaction واحد | تقسيم إلى دفعات (batch) |
| تقارير التوحيد المالي | تقرأ من جميع قواعد بيانات الشركات | تخزين مؤقت + قراءة غير متزامنة |
| الجرد الدوري (10,000 منتج) | يقارن كل منتج فردياً | bulk update + partial indexes |
| استيراد كشف البنك (1000 سطر) | Auto-match يفحص كل سطر مقابل كل قيد | EXPLAIN ANALYZE + فهارس |
| POS Offline Sync (100 طلب) | مزامنة متسلسلة | bulk insert + conflict resolution |

---

## 15.3 النواقص الأمنية والتشغيلية

### 15.3.1 ثغرات أمنية

| # | المشكلة | الشدة | الملف | التفاصيل |
|---|---------|-------|-------|----------|
| 18 | **`pickle.loads` على بيانات Redis** | عالية | `utils/cache.py` خط 67 | إذا تم اختراق Redis → تنفيذ كود عشوائي (RCE). يجب استبداله بـ `json.loads()` |
| 19 | **Rate limiter للدخول في الذاكرة فقط** | عالية | `routers/auth.py` خطوط 29-30 | `_login_attempts` dict يُمسح عند إعادة تشغيل الخادم أو في بيئة multi-worker → brute force سهل |
| 20 | **localhost يتجاوز حماية الدخول** | متوسطة | `routers/auth.py` خطوط 41-42 | `if client_ip in ("127.0.0.1", ...): return` — خلف reverse proxy كل الطلبات تظهر من localhost |
| 21 | **JWT يحمل الصلاحيات بداخله** | متوسطة | `routers/auth.py` خطوط 432-440 | إلغاء صلاحية مستخدم لا يسري إلا بعد 30 دقيقة (انتهاء التوكن) |
| 22 | **CSP يسمح بـ `unsafe-inline`** | منخفضة | `utils/security_middleware.py` | ضعف في Content Security Policy — مطلوب عملياً لـ SPA |

### 15.3.2 نواقص تشغيلية

| # | المشكلة | الشدة | التفاصيل |
|---|---------|-------|----------|
| 23 | **لا يوجد إطار عمل للهجرات (Migrations)** | عالية | لا Alembic, لا version tracking — `CREATE TABLE IF NOT EXISTS` فقط → انحراف المخطط بين الشركات |
| 24 | **لا يوجد CI/CD pipeline** | عالية | 48 ملف اختبار لكن لا GitHub Actions, لا automated testing |
| 25 | **سجلات فقط stdout** | منخفضة | لا JSON logging, لا log rotation, لا request ID tracing |
| 26 | **لا يوجد قفل موزع للـ Scheduler** | متوسطة | في بيئة multi-instance كل نسخة ترسل التقارير المجدولة → تكرار |
| 27 | **Health check يكشف عدد الشركات** | منخفضة | `/health` يعرض `companies: N` بدون مصادقة |

---

## 15.4 قائمة تحقق الإطلاق (Go-Live Checklist) — خطة 30 يوماً

### الأسبوع الأول (الأيام 1-7): إصلاحات حرجة

| # | الحالة | المهمة | الأولوية | التفاصيل البرمجية |
|---|--------|--------|---------|-------------------|
| 1 | ✅ مُنجز | **تفعيل قفل الفترات المحاسبية** | حرجة | تم استدعاء `check_fiscal_period_open()` في: `invoices.py`, `pos.py`, `hr/core.py`, `manufacturing/core.py`, `purchases.py` |
| 2 | ✅ مُنجز | **إضافة `FOR UPDATE` على المخزون** | حرجة | تم إضافة `FOR UPDATE` في `transfers.py` (مصدر + وجهة) و `purchases.py` (مرتجعات) |
| 3 | ✅ مُنجز | **إصلاح payroll JE balance** | عالية | تم إضافة `SELECT SUM(debit),SUM(credit)` post-insert في `hr/core.py` + `trans.rollback()` عند عدم التوازن |
| 4 | ✅ مُنجز | **إصلاح POS VAT calculation** | عالية | تم تعديل `pos.py`: الضريبة الآن على `(price * qty - discount_amount)` — متوافق مع ZATCA |
| 5 | ✅ مُنجز | **استبدال `pickle.loads` بـ `json.loads`** | عالية | تم في `utils/cache.py`: إزالة `pickle` كامل، إضافة `_json_default()` لـ Decimal/UUID/datetime |
| 6 | ✅ مُنجز | **إصلاح POS session TOCTOU** | عالية | تم إضافة `FOR UPDATE SKIP LOCKED` + هجرة `UNIQUE INDEX ON pos_sessions(user_id) WHERE status='opened'` — ملف: `migrations/add_pos_session_unique_index.py` + `alembic/versions/0002_pos_session_unique.py` |

### الأسبوع الثاني (الأيام 8-14): أمان وأداء

| # | الحالة | المهمة | الأولوية | التفاصيل البرمجية |
|---|--------|--------|---------|-------------------|
| 7 | ✅ مُنجز | **نقل rate limiter إلى Redis** | عالية | تم إعادة كتابة `auth.py`: Redis pipeline مع `rl:ip:{ip}` و `rl:user:{username}` + TTL + fallback لـ dict إذا Redis غير متاح |
| 8 | ✅ مُنجز | **إضافة `X-Forwarded-For` handling** | عالية | تم في `auth.py`: قراءة XFF header + `_get_client_ip()` helper |
| 9 | ✅ مُنجز | **تحديد سقف لمحركات قواعد البيانات** | عالية | تم في `database.py`: `OrderedDict` LRU بحد أقصى `_MAX_ENGINES = 50` + `engine.dispose()` عند الإخراج |
| 10 | ⚠️ بنية تحتية | **تثبيت PgBouncer** | عالية | يتطلب تثبيت وتكوين على الخادم — ليس كوداً |
| 11 | ✅ مُنجز | **تحويل الأرقام المالية إلى `Decimal`** | متوسطة | تم في `invoices.py`, `pos.py`, `system_completion.py`: `Decimal + ROUND_HALF_UP + _dec() helper` |
| 12 | ✅ مُنجز | **إعادة التحقق من JWT عند العمليات الحساسة** | متوسطة | تم إضافة `require_sensitive_permission()` في `utils/permissions.py` — DB check لـ `is_active` |

### الأسبوع الثالث (الأيام 15-21): اختبارات وبنية تحتية

| # | الحالة | المهمة | الأولوية | التفاصيل |
|---|--------|--------|---------|----------|
| 13 | ✅ مُنجز | **كتابة اختبارات تكامل محاسبية** | عالية | `tests/test_accounting_integrity.py`: 8 فئات، 30+ اختبار (JE balance, tax precision, inventory, payroll, POS, fiscal lock, Zakat, critical APIs) |
| 14 | ✅ مُنجز | **إعداد CI/CD** | عالية | `.github/workflows/ci.yml`: 4 وظائف (lint, test, build, deploy) + Python syntax check |
| 15 | ✅ مُنجز | **تثبيت Alembic** | متوسطة | `alembic.ini` + `alembic/env.py` (multi-tenant aware) + baseline + POS unique index migration |
| 16 | ✅ مُنجز | **إعداد JSON logging** | متوسطة | `utils/logging_config.py`: JSON formatter (production) + Dev formatter + `RequestIDMiddleware` + `X-Request-ID` header |
| 17 | ✅ مُنجز | **إعداد النسخ الاحتياطي التلقائي** | عالية | `scripts/backup.sh`: pg_dump system + all company DBs, gzip, S3 optional, retention 30 يوم |
| 18 | ⚠️ بنية تحتية | **اختبار الحمل (Load Testing)** | متوسطة | يتطلب تشغيل `k6` أو `locust` على بيئة staging |

### الأسبوع الرابع (الأيام 22-30): بيئة الإنتاج

| # | الحالة | المهمة | الأولوية | التفاصيل |
|---|--------|--------|---------|----------|
| 19 | ⚠️ بنية تحتية | **إعداد الخادم** | حرجة | يتطلب provisioning فعلي — مواصفات موثقة في Runbook |
| 20 | ✅ مُنجز | **إعداد SSL/TLS** | حرجة | `nginx/production.conf`: Let's Encrypt + TLS 1.2/1.3 + HSTS + OCSP Stapling |
| 21 | ✅ مُنجز | **إعداد Nginx** | حرجة | `nginx/production.conf`: rate limiting `/api/auth/login` (5r/m), security headers, WebSocket, CSP |
| 22 | ✅ مُنجز | **إعداد Docker Compose للإنتاج** | عالية | `docker-compose.prod.yml`: replicas:2, resource limits, redis password, no exposed ports |
| 23 | ✅ مُنجز | **إعداد Gunicorn بدلاً من Uvicorn** | عالية | `Dockerfile` CMD → `gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --preload` |
| 24 | ✅ مُنجز | **إعداد المراقبة** | متوسطة | `monitoring/alerts/aman_alerts.yml`: 15 alert rule (backend, DB, Redis, infra) + Prometheus + Grafana |
| 25 | ⚠️ بنية تحتية | **اختبار الاسترداد (DR Test)** | عالية | موثق في Runbook — يتطلب تنفيذ فعلي على خادم اختبار |
| 26 | ✅ مُنجز | **توثيق إجراءات الطوارئ (Runbook)** | متوسطة | `docs/RUNBOOK.md`: 10 أقسام شاملة (طوارئ، DB، Redis، backup/restore، نشر، أمان، صيانة) |

### ملخص الأولويات

```
┌─────────────────────────────────────────────────────────────┐
│              أولويات ما قبل الإطلاق (Production Blockers)    │
├─────────────────────────────────────────────────────────────┤
│ 🔴 حرجة — يمنع الإطلاق:                                    │
│    ✅ قفل الفترات المحاسبية (fiscal lock)                   │
│    ✅ قفل صفوف المخزون (FOR UPDATE)                         │
│    ✅ SSL/TLS + Nginx reverse proxy                          │
│    ✅ إصلاح حساب ضريبة POS (ZATCA)                         │
│                                                             │
│ 🟠 عالية — يُطلق بها مع خطة إصلاح فوري:                    │
│    ✅ pickle → json في Cache (RCE fix)                      │
│    ✅ Rate limiter على Redis                                 │
│    ⚠️ PgBouncer (بنية تحتية — تثبيت على الخادم)             │
│    ✅ نسخ احتياطي تلقائي                                    │
│    ✅ X-Forwarded-For في auth.py                            │
│    ✅ LRU Engine Cache (max 50)                             │
│                                                             │
│ 🟡 متوسطة — خلال أول 90 يوم:                                │
│    ✅ Decimal للأرقام المالية                                │
│    ✅ Alembic للهجرات                                        │
│    ✅ CI/CD pipeline                                         │
│    ✅ JSON logging + Request-ID                              │
├─────────────────────────────────────────────────────────────┤
│ آخر تحديث للحالة: الجلسة الحالية                             │
│ مُنجز: 22 من 26 مهمة (85%)                                  │
│ متبقي: 4 مهام بنية تحتية (PgBouncer, Load Test, Server, DR) │
│ — تتطلب تنفيذ على خادم الإنتاج الفعلي                       │
└─────────────────────────────────────────────────────────────┘
```

---

*نهاية قاعدة المعرفة — هذا الملف يُغني عن إعادة الفحص ويُستخدم كمرجع دائم*




كلمة سر الدروبلت 
aman123321.Erp

ubuntu-s-2vcpu-4gb-nyc3-01
in  AMAN_ERP / 4 GB Memory / 80 GB Disk / NYC3 - Ubuntu 24.04 (LTS) x64
ipv4: 64.225.49.118 Copy
ipv6:  Enable now
Private IP:  10.108.0.2 Copy
Reserved IP:  Enable now


Last login: Tue Mar  3 15:24:06 2026 from 88.236.74.45
root@ubuntu-s-2vcpu-4gb-nyc3-01:~# cat /home/deploy/.ssh/github_actions
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACAq2sYOL5JsdBgieF43EWlN3HcXpc1caqzLZp4bRs3+yAAAAJinshX4p7IV
+AAAAAtzc2gtZWQyNTUxOQAAACAq2sYOL5JsdBgieF43EWlN3HcXpc1caqzLZp4bRs3+yA
AAAECc6OkqBvdiBW+nZH2mYgOVP63fsrOQuCUBknALxv4TVSraxg4vkmx0GCJ4XjcRaU3c
dxelzVxqrMtmnhtGzf7IAAAADmdpdGh1Yi1hY3Rpb25zAQIDBAUGBw==
-----END OPENSSH PRIVATE KEY-----
root@ubuntu-s-2vcpu-4gb-nyc3-01:~# 


github.com/AMANCAMSYS/AMAN_ERP.git .
chown -R deploy:deploy /opt/aman

# توليد SECRET_KEY قوي
SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
echo "SECRET_KEY المولد: $SECRET"

# إنشاء .env
cat > /opt/aman/backend/.env << EOF
POSTGRES_SERVER=db
POSTGRES_PORT=5432
POSTGRES_USER=aman
POSTGRES_PASSWORD=AmanDB$(date +%Y)Secure!
POSTGRES_DB=postgres

REDIS_PASSWORD=AmanRedis$(date +%Y)Pass!
REDIS_URL=redis://:AmanRedis$(date +%Y)Pass!@redis:6379/0

SECRET_KEY=$SECRET

APP_ENV=production
cat /opt/aman/backend/.envd/.envte +%Y)!.118
Cloning into '.'...
remote: Enumerating objects: 2294, done.
remote: Counting objects: 100% (2294/2294), done.
remote: Compressing objects: 100% (1266/1266), done.
remote: Total 2294 (delta 1538), reused 1764 (delta 1008), pack-reused 0 (from 0)
Receiving objects: 100% (2294/2294), 2.88 MiB | 16.20 MiB/s, done.
Resolving deltas: 100% (1538/1538), done.
SECRET_KEY المولد: b4e6e84cf9a8c11fb71788fb49fd1683a8b5d67b97f9e0ad2d27dc04a7950f27
✅ .env created
POSTGRES_SERVER=db
POSTGRES_PORT=5432
POSTGRES_USER=aman
POSTGRES_PASSWORD=AmanDB2026Secure!
POSTGRES_DB=postgres

REDIS_PASSWORD=AmanRedis2026Pass!
REDIS_URL=redis://:AmanRedis2026Pass!@redis:6379/0

SECRET_KEY=b4e6e84cf9a8c11fb71788fb49fd1683a8b5d67b97f9e0ad2d27dc04a7950f27

APP_ENV=production
ALLOWED_ORIGINS=http://64.225.49.118

FRONTEND_URL=http://64.225.49.118
FRONTEND_URL_PRODUCTION=http://64.225.49.118

GRAFANA_USER=admin
GRAFANA_PASSWORD=AmanGrafana2026!
root@ubuntu-s-2vcpu-4gb-nyc3-01:/opt/aman# 

---

# 13. الميزات الجديدة — Phase 7 (5 مارس 2026)

> **تاريخ الإنجاز:** 5 مارس 2026  
> **الهدف:** إصلاحات حرجة في حساب الزكاة + تطبيق Responsive Design كامل + تحسينات التشغيل

## 13.1 إصلاحات حاسبة الزكاة (ZATCA Compliant)

### التغييرات في `backend/routers/finance/accounting.py`

| الإصلاح | التفاصيل |
|---------|---------|
| صيغة ZATCA الصحيحة | وعاء الزكاة = حقوق الملكية – الأصول الثابتة – الأصول غير الملموسة |
| خصم WIP | خصم العمل قيد التنفيذ من الوعاء |
| تصفية الصفوف الفارغة | إزالة الحسابات ذات الرصيد = 0 من العرض |
| فلترة الفروع | دعم تصفية حسابات الزكاة حسب الفرع |
| مناطق بدون SA | عرض "قريباً" لشركات غير سعودية بدلاً من الحساب |

**Endpoint:** `POST /accounting/zakat/calculate`  
**الجداول:** `zakat_calculations`, `journal_entries`, `journal_lines`

### التحقق من الصحة (اختبارات ناجحة)
```
curl POST /api/accounting/zakat/calculate
  { "fiscal_year": 2027, "method": "net_assets", "use_gregorian_rate": false }
→ 200 OK | وعاء = equity - fixed_assets - intangibles
```

---

## 13.2 Responsive Design — واجهة متجاوبة كاملة

> **التغيير الأكبر:** تحويل كل صفحات النظام لتعمل بشكل صحيح على الهاتف، التابلت، الكمبيوتر

### 13.2.1 الملفات المُعدَّلة

| الملف | التغيير |
|-------|---------|
| `frontend/src/components/Layout.jsx` | إضافة `sidebarOpen` state + overlay + resize listener |
| `frontend/src/components/Sidebar.jsx` | دعم `isOpen` prop + زر إغلاق + `onClick` لكل رابط |
| `frontend/src/components/Topbar.jsx` | إضافة زر hamburger مع أنيميشن X |
| `frontend/src/index.css` | إضافة 180+ سطر CSS متجاوب |

### 13.2.2 سلوك الـ Sidebar حسب الجهاز

| الجهاز | العرض | سلوك الـ Sidebar |
|--------|-------|-----------------|
| **كمبيوتر** | ≥ 1024px | ظاهر دائماً — ثابت على اليمين |
| **تابلت** | 768–1023px | مخفي — يظهر بزر hamburger مع overlay |
| **هاتف** | < 768px | مخفي — يظهر بزر hamburger مع overlay كامل |
| **هاتف صغير** | < 480px | شريط البحث مخفي لتوفير المساحة |

### 13.2.3 مكونات Responsive المُضافة

```css
/* الزر الجديد في Topbar */
.sidebar-hamburger          /* مخفي على desktop ≥1024px */
.hamburger-line             /* 3 خطوط + أنيميشن X عند الفتح */

/* Overlay خلف Sidebar */
.sidebar-overlay            /* backdrop مع blur عند فتح القائمة */

/* زر الإغلاق داخل Sidebar */
.sidebar-close-btn          /* X button مخفي على desktop */

/* Sidebar transitions */
.sidebar                    /* transform: translateX(100%) على mobile */
.sidebar.sidebar-open       /* transform: translateX(0) عند الفتح */
```

### 13.2.4 تحسينات CSS العامة على الأجهزة الصغيرة

| العنصر | التحسين |
|--------|---------|
| `.content-area` | padding تكيّفي: 32px → 20px → 16px → 12px |
| `.workspace` | padding تكيّفي: 24px → 16px → 12px |
| `.modules-grid` | عمود واحد على ≤768px |
| `.metrics-grid` | عمودان على ≤768px، عمود واحد على ≤480px |
| `.modal-content` | عرض 96%، `max-height: 95vh` |
| `.form-row` | `flex-direction: column` على ≤768px |
| `.data-table-*` | `overflow-x: auto` للتمرير الأفقي |
| `@media print` | إخفاء Sidebar + Topbar عند الطباعة |

---

## 13.3 تحسينات DevOps والإنتاج

### 13.3.1 Docker
| التغيير | التفاصيل |
|---------|---------|
| `restart: unless-stopped` | تشغيل تلقائي عند إعادة تشغيل الخادم |
| `safe-start.sh` / `safe-stop.sh` | تشغيل/إيقاف Docker آمن |
| `backup.sh` (Docker-aware) | نسخ احتياطية تعمل داخل وخارج Docker |
| `cron` يومي | نسخ احتياطي تلقائي كل يوم |

### 13.3.2 إصلاحات أمنية (Phase 7)
| الثغرة | الإصلاح |
|--------|---------|
| Multi-company login vulnerability | تحقق صارم من `company_id` عند تسجيل الدخول |
| HTTPS redirect on IP-only server | تعطيل middleware إعادة التوجيه |
| Uploads permissions | استخدام `gosu` في entrypoint لضمان صلاحيات المجلد |

### 13.3.3 إصلاحات Backend (Phase 7)
| الملف | الإصلاح |
|-------|---------|
| `hr/core.py` | إضافة `log_activity` import المفقود |
| `finance/accounting.py` | إصلاح cache الحسابات + حساب الأرصدة لجميع الفروع |
| `budget_items` | إصلاح اسم العمود (`planned_amount`) |
| `system_companies` | إزالة عمود `logo_url` المكرر |

---

## 13.4 ملخص الصفحات الجديدة (مقارنة بـ Phase 5)

| الوحدة | الصفحات الجديدة | المسارات |
|--------|----------------|---------|
| المحاسبة | `IntercompanyTransactions`, `RevenueRecognition`, `ZakatCalculator` | `/accounting/intercompany`, `/accounting/revenue-recognition`, `/accounting/zakat` |
| POS | `POSOfflineManager`, `CustomerDisplay`, `KitchenDisplay`, `LoyaltyPrograms`, `TableManagement`, `ThermalPrintSettings` | `/pos/offline`, `/pos/customer-display`, `/pos/kitchen`, `/pos/loyalty`, `/pos/tables`, `/pos/thermal-settings` |
| CRM | `LeadScoring`, `CustomerSegments`, `PipelineAnalytics`, `CRMContacts`, `SalesForecasts`, `CRMDashboard` | `/crm/lead-scoring`, `/crm/customer-segments`, `/crm/pipeline`, `/crm/contacts`, `/crm/forecasts` |
| Assets | `ImpairmentTest`, `LeaseContracts` | `/assets/impairment`, `/assets/leases` |
| المشاريع | `GanttChart`, `ProjectRisks`, `ResourceManagement`, `ResourceUtilizationReport` | `/projects/:id/gantt`, `/projects/:id/risks`, `/projects/resources`, `/projects/utilization` |
| التصنيع | `ProductionSchedule`, `ManufacturingCosting`, `DirectLaborReport`, `WorkOrderStatusReport` | `/manufacturing/schedule`, `/manufacturing/costing`, `/manufacturing/labor`, `/manufacturing/status` |
| الموارد البشرية | `SaudizationDashboard`, `WPSExport`, `EOSSettlement`, `CustodyManagement`, `LeaveCarryover`, `Violations`, `TrainingPrograms` | `/hr/saudization`, `/hr/wps`, `/hr/eos`, `/hr/custody`, `/hr/leave-carryover`, `/hr/violations`, `/hr/training` |
| الإعدادات | `ApiKeys`, `CostingPolicy`, `PrintTemplates`, `Webhooks`, `SecuritySettings`, +20 تبويب إعدادات | `/settings/api-keys`, `/settings/costing`, `/settings/templates`, `/settings/webhooks` |
| الإدارة | `BackupManagement`, `SecurityEvents` | `/admin/backups`, `/admin/security-events` |
| الإعداد | `IndustrySetup`, `ModuleCustomization` | `/setup/industry`, `/setup/modules` |

---

## 13.5 إجمالي الأرقام المحدّثة (5 مارس 2026)

| المقياس | القيمة القديمة | القيمة الجديدة |
|---------|--------------|--------------|
| صفحات JSX | 309 | **277** (بعد حذف الملفات المتبقية من أرشيف) |
| آخر Commit | Phase 6 | **Phase 7 — 8dec57f** |
| الزكاة ZATCA | صيغة جزئية | **صيغة ZATCA كاملة** |
| Responsive Design | غير موجود | **✅ متكامل — هاتف + تابلت + كمبيوتر** |
| Docker Production | يدوي | **✅ restart تلقائي + backup يومي** |

