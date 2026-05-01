# تقرير التدقيق الشامل لقاعدة البيانات والأداء (Database & Performance)
# Comprehensive Database Schema & Performance Audit Report

> **التاريخ**: 2026-04-28
> **النطاق**: Schema Design, Indexes, Foreign Keys, Query Optimization, N+1 Detection, Audit Trail, Backup
> **المراجع**: خبير قواعد بيانات PostgreSQL + مهندس أداء

---

## 1. الفهارس (Indexes)

### 1.1 الإحصائيات

| العنصر | العدد |
|--------|-------|
| إجمالي الفهارس | **~250+** |
| فهارس مركبة (composite) | ~45 |
| فهارس جزئية (partial WHERE) | ~12 |
| فهارس فريدة جزئية (UNIQUE partial) | ~5 |
| فهارس على materialized views | 8 |
| جداول بدون أي فهارس (باستثناء PK) | `leave_requests`, `production_orders`, `mrp_items` |

### 1.2 فهارس حرجة مفقودة

| # | الجدول | الحقول المفقودة | التأثير |
|---|--------|-----------------|---------|
| 1.2.1 | `payroll_entries` | `(employee_id, period_id)` | تقارير رواتب الموظف عبر الفترات |
| 1.2.2 | `leave_requests` | `(status, start_date)` | قائمة الإجازات المعلقة/المعتمدة حسب التاريخ |
| 1.2.3 | `leave_requests` | `(employee_id, start_date)` | سجل إجازات الموظف — لا يوجد أي فهرس على هذا الجدول |
| 1.2.4 | `production_orders` | `(status, due_date)` | تصفية أوامر الإنتاج حسب الحالة والتاريخ للـ shop floor |
| 1.2.5 | `attendance` | `(date)` فقط | البحث بنطاق تاريخي لكل الموظفين — الفهرس الحالي `(employee_id, date)` لا يساعد |
| 1.2.6 | `pos_orders` | `(order_date, status)` | تقارير POS الشهرية حسب الحالة |
| 1.2.7 | `pos_orders` | `(customer_id)` | سجل طلبات العميل في POS |
| 1.2.8 | `inventory_transactions` | `(product_id, transaction_date)` | تقارير حركة المنتج الزمنية |
| 1.2.9 | `journal_lines` | `(is_reconciled)` | استعلامات التسوية البنكية للبنود غير المسواة |
| 1.2.10 | `payment_vouchers` | `(party_type, party_id)` | جميع مدفوعات طرف معين |

### 1.3 فهارس ممتازة تستحق الإشادة

| # | الفهرس | الجدول | لماذا |
|---|--------|--------|-------|
| 1.3.1 | `uq_je_idempotency` (UNIQUE partial) | `journal_entries` | يمنع القيود المكررة دون إهدار مساحة على NULLs ✅ |
| 1.3.2 | `uq_currency_one_base` (UNIQUE partial) | `currencies` | يضمن عملة أساسية واحدة فقط لكل شركة ✅ |
| 1.3.3 | `idx_audit_logs_live` (partial) | `audit_logs` | استعلامات التدقيق للسجلات الحية فقط — ⚡ سريع ✅ |
| 1.3.4 | `ix_cost_layers_product_wh_exhausted_date` | `cost_layers` | مركب رباعي — مثالي لاستهلاك FIFO/LIFO ✅ |
| 1.3.5 | `idx_event_outbox_undelivered` (partial) | `event_outbox` | أحداث غير مرسلة فقط — موفر للمساحة ✅ |
| 1.3.6 | `idx_bsl_unreconciled` (partial) | `bank_statement_lines` | بنود غير مسواة فقط ✅ |
| 1.3.7 | `idx_je_source_srcid_date` | `journal_entries` | المصدر + المعرف + التاريخ — تستخدم في إلغاء الازدواجية ✅ |

---

## 2. سلامة البيانات (Data Integrity — Foreign Keys)

### 2.1 إحصائيات

| العنصر | العدد |
|--------|-------|
| إجمالي FK مع CASCADE | ~28 |
| إجمالي FK مع SET NULL | ~10 |
| إجمالي FK مع RESTRICT (صريح) | ~3 |
| إجمالي FK بدون ON DELETE (افتراضي NO ACTION) | ~45+ |

### 2.2 ثغرات FK حرجة

| # | الجدول | FK | المشكلة | الخطورة |
|---|--------|----|---------|---------|
| 2.2.1 | `attendance` | `employee_id -> employees(id)` | **بدون ON DELETE** — حذف موظف بسجلات حضور يفشل بدون رسالة واضحة | P1 |
| 2.2.2 | `leave_requests` | `employee_id -> employees(id)` | **بدون ON DELETE** — حذف موظف بطلبات إجازة يفشل | P1 |
| 2.2.3 | `payroll_entries` | `employee_id -> employees(id)` | **بدون ON DELETE** — حذف موظف بسجلات رواتب يفشل | P1 |
| 2.2.4 | `journal_entries` | `created_by -> company_users(id)` | **بدون ON DELETE** — حذف مستخدم أنشأ قيودًا يفشل | P2 |
| 2.2.5 | `pos_orders` | `session_id -> pos_sessions(id)` | **بدون ON DELETE** — حذف جلسة POS بطلبات يفشل | P2 |
| 2.2.6 | `accounts` | `parent_id -> accounts(id)` | **بدون ON DELETE** — self-referencing بدون حماية | P2 |
| 2.2.7 | `inventory` | `product_id -> products(id)` | **بدون ON DELETE** — حذف منتج بمخزون يفشل | P2 |
| 2.2.8 | `journal_lines` | `journal_entry_id -> journals(id)` | تم تغييره من CASCADE إلى RESTRICT في migration 0009 — **صحيح** | ✅ |

### 2.3 تناقض ON DELETE بين DDL و ORM

```python
# DDL: ON DELETE CASCADE
payroll_entries.period_id -> payroll_periods(id) ON DELETE CASCADE

# ORM model: لا يذكر CASCADE
ForeignKey("payroll_periods.id"), nullable=False
```

الفجوة بين `database.py` (DDL) و `models/domain_models/hr_core_payroll.py` (ORM) تعني أن قاعدة البيانات ستسمح بـ CASCADE لكن الـ ORM لا يعكس هذا السلوك — قد يؤدي لسلوك غير متوقع في التطبيق.

---

## 3. قيود التحقق (CHECK Constraints)

| # | الجدول | القيد | التقييم |
|---|--------|-------|---------|
| 3.1 | `journal_lines` | `chk_jl_nonneg` (debit>=0, credit>=0) + `chk_jl_exclusive` + `chk_jl_nonzero` | ✅ ممتاز |
| 3.2 | `journal_entries` | `chk_je_status` IN (draft,posted,void,reversed) | ✅ |
| 3.3 | `inventory` | `quantity >= 0`, `reserved_quantity >= 0` | ✅ |
| 3.4 | `accounts` | `account_type` IN 5 types | ✅ |
| 3.5 | `bom_components` | `waste_percentage BETWEEN 0 AND 100` | ✅ |
| 3.6 | `production_orders` | `status` IN 5 states | ✅ |
| 3.7 | `fiscal_periods` | **GiST exclusion** on daterange — يمنع تداخل الفترات | ✅ نادر وممتاز |

---

## 4. مشكلة N+1 Queries

### 4.1 أنماط N+1 مؤكدة

| # | الملف | السطر | النمط | الخطورة |
|---|-------|-------|-------|---------|
| 4.1.1 | `invoices.py` | 368-389 | **حلقة INSERT فردية** لأسطر الفاتورة: N استعلام لكل سطر. يجب استخدام `executemany` أو `INSERT INTO ... SELECT ...` دفعة واحدة | 🔴 P1 |
| 4.1.2 | `purchases.py` | 1343-1449 | نفس النمط — INSERT فردي لكل سطر فاتورة مشتريات + تحديث مخزون لكل منتج | 🔴 P1 |
| 4.1.3 | `returns.py` | 187-198 | INSERT فردي لكل سطر مرتجع | 🟠 P2 |
| 4.1.4 | `pos.py` | 491-525 | INSERT فردي لكل سطر طلب POS | 🟠 P2 |
| 4.1.5 | `invoices.py` | 278-285 | **استعلام `information_schema` مرتين** عند كل إنشاء فاتورة — لجلب أسماء الأعمدة ديناميكيًا. بطيء وغير ضروري | 🔴 P1 |
| 4.1.6 | `purchases.py` | 1870 | شراء مرتجع: `FOR UPDATE` لكل منتج في حلقة منفصلة — يجب تجميعها في استعلام واحد | 🟠 P2 |
| 4.1.7 | `core.py` (HR) | 809-913 | `generate_payroll`: حلقة لكل موظف مع استعلامات فرعية (مكونات، عمل إضافي، مخالفات، قروض) — 6+ استعلامات لكل موظف | 🔴 P1 |

### 4.2 آلية الكشف

`utils/query_counter.py` — عداد استعلامات لكل request:
- يُحذر عند **50+ استعلام** في request واحد
- يُعرض عدد الاستعلامات في هيدر `X-DB-Query-Count`
- معطل افتراضيًا — يُفعل بـ `ENABLE_QUERY_COUNTER=1`

### 4.3 تقدير الحمل عند 100,000 سجل

| العملية | الاستعلامات الحالية | استعلامات مع 100K سجل | الحل |
|---------|-------------------|----------------------|------|
| إنشاء فاتورة (10 أسطر) | ~25 | ~25 (ثابت — جيد) | تحسين INSERT الدفعي |
| إنشاء مسير رواتب (50 موظف) | ~350 | ~350 (ثابت) | تجميع استعلامات المكونات |
| قائمة الفواتير (صفحة 50) | ~3 | ~3 مع فهرس ✓ | — |
| تقرير الأستاذ العام (سنة) | ~5 | ~5 → بطيء بدون فهرس التاريخ | إضافة `idx_je_entry_date` (موجود ✓) |
| MRP لأمر إنتاج | ~15 | ~15 (ثابت — جيد) | — |

---

## 5. تصميم الجداول (Normalization)

### 5.1 تطبيع زائد عن الحاجة (Denormalization مقبول للأداء)

| # | الجدول | الأعمدة غير المطبعة | التقييم |
|---|--------|---------------------|---------|
| 5.1.1 | `accounts` | `balance` | ✅ مقبول — يُحدث مع كل قيد لسرعة الاستعلام |
| 5.1.2 | `parties` | `current_balance`, `balance_currency` | ✅ مقبول — يُحدث مع كل حركة |
| 5.1.3 | `treasury_accounts` | `current_balance` | ✅ مقبول — للخزائن |
| 5.1.4 | `products` | `cost_price` | ✅ مقبول — تكلفة متوسطة متجددة |
| 5.1.5 | `projects` | `actual_cost`, `progress_percentage` | 🟡 يحتاج مزامنة دورية مع الواقع |
| 5.1.6 | `budgets` | `total_budget`, `used_budget`, `remaining_budget` | 🟡 يحتاج إعادة حساب مع كل تعديل |

### 5.2 مشكلات التصميم

| # | المشكلة | الخطورة |
|---|---------|---------|
| 5.2.1 | **أعمدة قديمة مكررة**: `customer_id` + `supplier_id` بجانب `party_id` في جداول `invoices`, `sales_quotations`, `sales_orders`, `purchase_orders` — عملية انتقال غير مكتملة من العملاء/الموردين إلى جدول `parties` الموحد | P1 |
| 5.2.2 | **3 جداول لنفس الغرض**: `customer_transactions` + `supplier_transactions` + `party_transactions` — ثلاثة جداول لحركات الأطراف | P2 |
| 5.2.3 | **نوع البيانات**: `company_settings.setting_value TEXT` — تُخزن المفاتيح الرقمية (account IDs) كنصوص، مما يمنع FK والتحقق من الصحة | P2 |
| 5.2.4 | **JSONB للمصفوفات**: `tax_groups.tax_ids JSONB DEFAULT '[]'` — مصفوفة JSON بدل جدول وسيط (many-to-many). لا يمكن استخدام FK أو INDEX على العناصر الفردية | P2 |
| 5.2.5 | **غياب soft delete موحد**: بعض الجداول تستخدم `is_deleted` (BOM, Routes, Work Centers)، والبعض `status = 'cancelled'` (Invoices)، والبعض لا يملك أيًا منهما | P2 |

---

## 6. مسار التدقيق (Audit Trail)

### 6.1 بنية سجل التدقيق

| الجدول | المحتوى | عدد الفهارس |
|--------|---------|-------------|
| `audit_logs` | لكل شركة: user_id, username, action, resource_type, resource_id, details (JSONB), ip_address, branch_id, is_archived, created_at | 4 (مركبان + 2 جزئيان) |
| `security_events` | أحداث أمنية: event_type, user_id, details (JSONB) | 3 |
| `login_attempts` | محاولات الدخول: IP, success/failure | 1 |
| `system_activity_log` | أنشطة النظام المركزية (إنشاء/حذف شركات) | — |

### 6.2 دالة `log_activity` (`utils/audit.py`)

```python
log_activity(db_conn, user_id, username, action, resource_type, resource_id,
             details={}, request=request, branch_id=None, critical=False)
```

- **351+ نقطة استدعاء** عبر كل routers
- **critical=True**: للعمليات المالية — يرفع `HTTPException(503)` إذا فشل تسجيل التدقيق
- **critical=False**: للعمليات غير المالية — يسجل خطأ فقط
- يخمن `branch_id` تلقائيًا من `user_branches` أو الفرع الافتراضي

### 6.3 أرشفة سجل التدقيق

| الميزة | التفصيل |
|--------|---------|
| أرشفة تلقائية | لا — يدوية عبر `POST /admin/audit/archive` |
| فهرس جزئي للسجلات الحية | `idx_audit_logs_live ON (created_at DESC) WHERE NOT is_archived` ✅ |
| فهرس جزئي للسجلات المؤرشفة | `idx_audit_logs_archival ON (created_at) WHERE is_archived = TRUE` ✅ |
| سياسة استبقاء | غير محددة — لا يوجد cleanup تلقائي |

### 6.4 صلابة المعاملات (Transactions)

**Triggers على مستوى قاعدة البيانات:**
- `trg_je_balanced`: يضمن Σdebit = Σcredit للقيود المنشورة (مؤجل DEFERRED)
- `trg_je_immutable`: يمنع تعديل القيود المنشورة
- `trg_jl_immutable`: يمنع تعديل أسطر القيود المنشورة
- `trg_exchange_rates_immutable`: أسعار الصرف للإضافة فقط (append-only)
- `trg_je_period_open`: يمنع الترحيل في فترات مغلقة

**Auto-update triggers**: ~30 جدولًا مع `updated_at` تلقائي عند التعديل ✅

---

## 7. النسخ الاحتياطي (Backup)

| الميزة | التفصيل |
|--------|---------|
| النوع | يدوي عبر `POST /admin/backup` |
| الأداة | `pg_dump -Fc --no-owner --no-privileges` |
| المهلة | 300 ثانية |
| المسار | `backend/backups/{company_id}/aman_{company_id}_{timestamp}.sql.gz` |
| الأمان | `PGPASSWORD` متغير بيئة (ليس في الأمر). Company ID يتحقق منه عبر regex `^[a-f0-9]+$` |
| السجل | جدول `backup_history` مع status, file_size, error_message |
| التحميل | `GET /admin/backup/{id}/download` — streaming |

**ثغرات:**
- **لا يوجد نسخ احتياطي تلقائي** — لا scheduler، لا cron job
- **لا يوجد restore endpoint** — النسخ الاحتياطي موجود لكن لا واجهة للاستعادة
- **لا توجد سياسة استبقاء** — الملفات تتراكم دون حذف تلقائي

---

## 8. تجمع الاتصالات (Connection Pooling)

| نوع المحرك | pool_size | max_overflow | pool_recycle | pool_pre_ping | أقصى اتصالات |
|-----------|-----------|-------------|-------------|--------------|-------------|
| نظام DDL | 5 (افتراضي) | 10 (افتراضي) | 3600s | ✅ | 15 |
| نظام عادي | 5 (افتراضي) | 10 (افتراضي) | 3600s | ✅ | 15 |
| لكل مستأجر | 5 | 10 | 300s | ✅ | 15 |
| **أقصى إجمالي (50 مستأجر)** | 250 | 500 | — | — | **~750** |

**آلية LRU Eviction**: عند تجاوز 50 مستأجر، يُطرد الأقدم استخدامًا مع `engine.dispose()` لمنع استنزاف الاتصالات ✅

---

## 9. SQL Injection Risks

### 9.1 الممارسات الآمنة (95%+ من الكود)

- استعلامات parameterized مع `:param` bind parameters ✅
- `utils/sql_safety.py`: `validate_sql_identifier()` + `validate_aman_identifier()` ✅
- تحقق من company_id قبل `pg_dump` subprocess ✅

### 9.2 المخاطر المتبقية

| # | الملف | النمط | الخطورة |
|---|-------|-------|---------|
| 9.2.1 | `data_import.py:340` | `f"SELECT {col_list} FROM {config['table']}"` — إذا `config['table']` من مدخلات المستخدم، قابل للحقن | 🔴 P1 |
| 9.2.2 | `dashboard.py:1174` | `f"SELECT ... FROM {mv_name} {where_clause}"` — اسم MV من مصدر موثوق لكن النمط غير آمن | 🟠 P2 |
| 9.2.3 | متعدد | `f"UPDATE table SET {', '.join(updates)} WHERE id = :id"` — أسماء الأعمدة من التطبيق (آمنة) لكن النمط خطر إذا تغير المصدر | 🟡 |
| 9.2.4 | متعدد | `f"SELECT ... WHERE {where}"` — بناء WHERE ديناميكي من عوامل تصفية | 🟡 |

---

## 10. تقدير الأداء عند مليون سجل

| الجدول | السجلات عند النمو | الفهارس الحالية | هل يكفي لمليون سجل؟ |
|--------|------------------|-----------------|-------------------|
| `journal_entries` | عالي (آلاف/يوم) | 14 فهرس ✅ | **نعم** — الفهارس الجزئية والمركبة تغطي معظم الاستعلامات |
| `journal_lines` | عالي جدًا (2-5x entries) | 10 فهارس ✅ | **نعم** — مع فهارس مركبة على account_id |
| `invoices` | متوسط (مئات/يوم) | 13 فهرس ✅ | **نعم** |
| `inventory_transactions` | عالي جدًا (كل حركة) | 3 فهارس 🟡 | **يحتاج** `(product_id, transaction_date)` |
| `payroll_entries` | منخفض (شهري) | 1 فهرس 🟡 | **يحتاج** `(employee_id, period_id)` |
| `attendance` | عالي (يومي لكل موظف) | 1 فهرس 🟡 | **يحتاج** `(date)` مستقل |
| `audit_logs` | عالي جدًا (كل عملية) | 4 فهارس ✅ | **نعم** — مع الفهارس الجزئية |
| `pos_orders` | متوسط-عالي | 2 فهارس 🟡 | **يحتاج** `(customer_id)` + `(order_date, status)` |
| `leave_requests` | منخفض | **0 فهارس** 🔴 | **يحتاج فهارس فورًا** — أي استعلام سيمسح الجدول كاملًا |

---

## 11. توصيات تحسين الأداء (حسب الأولوية)

### 🔴 P0 — فوري (للاستعلامات تحت المليون سجل)

1. **فهارس leave_requests**: `(status, start_date)` + `(employee_id, start_date)` — الجدول بدون أي فهرس حاليًا مما يعني مسح كامل للجدول في كل استعلام
2. **فهرس payroll_entries**: `(employee_id, period_id)` — تقارير الموظفين الشهرية
3. **فهرس attendance**: `(date)` مستقل لتقارير الحضور اليومية لجميع الموظفين
4. **إزالة استعلام `information_schema`** من `invoices.py:278` — يُنفذ مرتين عند كل إنشاء فاتورة. استبدله بقائمة أعمدة ثابتة أو caching

### 🔴 P1 — عاجل (لتحسين الإنتاجية)

5. **تجميع INSERTات أسطر الفواتير** — استخدام `executemany` أو CTE بدل حلقة INSERT في 4 ملفات (`invoices.py`, `purchases.py`, `returns.py`, `pos.py`)
6. **تجميع استعلامات `generate_payroll`** — استعلام واحد لكل المكونات/العمل الإضافي/المخالفات/القروض بدل 6N استعلام
7. **إصلاح SQL Injection في `data_import.py:340`** — التحقق من `config['table']` قبل الاستخدام
8. **إضافة ON DELETE RESTRICT صريح** للجداول الحرجة: `attendance`, `leave_requests`, `payroll_entries` — مع رسائل خطأ واضحة
9. **فهارس production_orders**: `(status, due_date)` + `(product_id, status)`

### 🟠 P2 — هام (لتحسين الصيانة)

10. **إكمال الانتقال إلى `parties`** — إزالة أعمدة `customer_id`/`supplier_id` المهملة من جداول invoices/quotations/orders
11. **توحيد جداول المعاملات**: دمج `customer_transactions` + `supplier_transactions` في `party_transactions`
12. **فهارس inventory_transactions**: `(product_id, transaction_date)` + `(warehouse_id, product_id)`
13. **إضافة نسخ احتياطي تلقائي** — cron job أسبوعي + سياسة استبقاء (حذف النسخ الأقدم من 90 يومًا)
14. **إضافة restore endpoint** لاستعادة النسخ الاحتياطية
15. **استبدال `tax_ids JSONB`** بجدول وسيط `tax_group_members` للسماح بـ FK و INDEX

### 🟡 P3 — تحسينات متقدمة

16. **Covering Indexes**: إضافة أعمدة INCLUDE للفهارس المستخدمة بكثرة (مثلاً: `idx_invoices_type_status` مع INCLUDE للتاريخ والإجمالي)
17. **BRIN Indexes**: للجداول الضخمة جدًا (audit_logs, journal_lines) — أصغر حجمًا وأسرع للبيانات المرتبة زمنيًا
18. **Partitioning**: تقسيم `audit_logs` و `journal_lines` حسب الشهر/السنة عند تجاوز 10 مليون سجل
19. **Connection pooling**: External pooler مثل PgBouncer عند 100+ مستأجر
20. **Query plan caching**: تفعيل `pg_stat_statements` لتحليل الاستعلامات البطيئة في الإنتاج
