# 📖 AMAN ERP — قاعدة المعرفة الشاملة للنظام
# SYSTEM KNOWLEDGE BASE

> **آخر تحديث:** يونيو 2026  
> **المُعدّ بواسطة:** تحليل كامل للكود المصدري (Backend + Frontend + Database) + فحص قاعدة البيانات  
> **الغرض:** مرجع شامل يُغني عن إعادة الفحص — يحتوي على كل صفحة، كل API، كل جدول، كل قيد، كل تقرير  
> **حالة النظام:** البيانات الأساسية (Master Data) مكتملة — بانتظار إدخال البيانات التشغيلية

---

## 📍 حالة النظام الحالية — أين وصلنا؟

### النظام بالأرقام
| المقياس | القيمة |
|---------|--------|
| إجمالي الـ Endpoints (Backend) | 800 |
| إجمالي الصفحات (Frontend) | ~229 route + ~246 ملف |
| إجمالي الجداول | 220 |
| الجداول المملوءة | 30 (بيانات أساسية) |
| الجداول الفارغة | 190 (بيانات تشغيلية) |
| اكتمال الكود | ~98% |

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

# 📊 ملخص إحصائي

| البند | قبل Phase 4 | بعد Phase 4 |
|-------|------------|-------------|
| صفحات الواجهة الأمامية | ~230 صفحة JSX | ~248 صفحة JSX |
| مسارات (Routes) | ~145 route | ~165 route |
| جداول قاعدة البيانات | ~205 جدول | ~216 جدول |
| API Endpoints | ~500+ endpoint | ~542+ endpoint |
| القيود التلقائية | 65 نقطة توليد | 70+ نقطة توليد |
| حسابات شجرة الحسابات الافتراضية | ~80 حساب | ~80 حساب |
| ربط حسابات تلقائي (Mappings) | ~45 mapping | ~45 mapping |
| الأدوار الافتراضية | 8 أدوار | 8 أدوار |
| التقارير | ~43 تقرير + مخصصة | ~46 تقرير + مخصصة |
| قوالب الصناعة | 7 قوالب | 7 قوالب |
| ملفات الترجمة | ar.json + en.json | +13 قسم جديد لكل ملف |

---

*نهاية قاعدة المعرفة — هذا الملف يُغني عن إعادة الفحص ويُستخدم كمرجع دائم*
