# تقرير التدقيق الموحّد — AMAN ERP
# Consolidated Audit Report

> **التاريخ**: 2026-04-28
> **النطاق**: جميع الوحدات (22 تقريرًا مجمّعًا — يشمل تقرير التقييم العام والمعايرة)
> **العدد الإجمالي للخلل**: 519 بندًا

---

## 🔴 P0 — حرج (يمنع تشغيل النظام أو يؤدي لاختلال مالي فادح)

### الخزينة والمحاسبة (Treasury & Accounting)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 1 | Treasury | `currencies.py` | 297-305 | **[FIXED in T1.2 — 2026-05-01]** فحص تكرار إعادة التقييم معطل تمامًا: `entry_number LIKE 'REV-{code}-%'` لن يتطابق مع الصيغة الفعلية `JE-XXXXX` أبدًا. **الحل**: استبدل بـ `source='currency_revaluation' AND source_id=:currency_id`. |
| 2 | Treasury | `currencies.py` | 314-318 | **[FIXED in T1.2 — 2026-05-01]** حسابات UFX-GAIN/UFX-LOSS غير موجودة في قوالب COA. **الحل**: أُضيف `42021 Unrealized FX Gains` و `71011 Unrealized FX Losses` إلى `CORE_ACCOUNTS` في `industry_coa_templates.py` + resolver بـ 4 مستويات fallback (mapping/legacy/numeric/name) + migration `0013_add_ufx_accounts.py` لباكفيل الشركات القائمة + HTTP 422 بدل 500. |
| 3 | Treasury | `treasury.py` + 8 ملفات | 17 موقع | **[FIXED in T1.3a — 2026-05-01]** ازدواجية الرصيد: `treasury_accounts.current_balance` كان يُحدَّث يدويًا في 17 موقعًا (sales/invoices, sales/vouchers, sales/returns, pos x2, projects, finance/notes x2, finance/checks x4, finance/treasury x4 شاملاً opening_balance) منفصلاً عن `accounts.balance` المُدار بـ GL. **الحل**: helper جديد `utils/treasury_balance.recalc_treasury_from_gl(db, treasury_id)` يحسب الرصيد من `journal_lines` لـ `gl_account_id` (FC: SUM ±amount_currency حيث currency=treasury.currency؛ SAR: SUM debit-credit). استُبدلت كل المواقع الـ17 لاستدعاء الـhelper بعد إنشاء JE. opening_balance نُقل من قبل JE إلى بعده. migration `0014_backfill_treasury_balance.py` يعيد حساب جميع الخزائن من `journal_lines` المنشورة عبر correlated subquery (يستبعد drafts بشكل قطعي). idempotent. تم التحقق عمليًا على Postgres: SAR=1200، USD=500، خزينة بدون JL=0، draft 99999 مُستبعد. |

### التصنيع (Manufacturing)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 4 | Manufacturing | `core.py` | 1053, 1176, 1199 | ~~**`ON CONFLICT DO UPDATE` بمرجع خاطئ للجدول**~~ — **[INVALID — verified empirically 2026-05-01]**: الصياغة `tablename.column` في `ON CONFLICT DO UPDATE` صحيحة وموثقة رسميًا في PostgreSQL ([SQL-INSERT docs](https://www.postgresql.org/docs/current/sql-insert.html#SQL-ON-CONFLICT)). تم التحقق عمليًا بتشغيل INSERT/UPDATE على Postgres حقيقي. القيد `UNIQUE(product_id, warehouse_id)` موجود في `database.py:632`. الكود سليم — لا تغيير |
| 5 | Manufacturing | `core.py` | 634-635 | ~~**معادلة `check_inventory_sufficiency` خاطئة**~~ — **[INVALID — verified empirically 2026-05-01]**: التعبير الشرطي `if not comp.is_percentage` يمنع الضرب المزدوج. عند `is_percentage=True`: `base_qty` يحتوي `order_quantity` ضمنيًا و `required = base_qty * waste`. عند `is_percentage=False`: `base_qty = comp.quantity` (لوحدة واحدة) و `required = base_qty * order_quantity * waste`. النتيجة مطابقة بالضبط لـ `manufacture_consume` (اختُبر عمليًا). الكود سليم — لا تغيير |

### المبيعات ونقاط البيع (Sales & POS)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 6 | Sales/POS | `routers/sales/invoices.py` + `utils/zatca_clearance.py` | - | **[FIXED in T1.5c — 2026-05-01]** ZATCA Phase 2 clearance: helper جديد `utils/zatca_clearance.attempt_clearance(db, invoice_id, jurisdiction, payload)` يُستدعى بعد `process_invoice_for_zatca` في `routers/sales/invoices.py`. يتحكم به `settings.ZATCA_PHASE2_ENFORCE` (default OFF لطرح تدريجي). السلوك: cleared/reported → `invoices.zatca_clearance_status='cleared'`؛ rejected → HTTP 422 + rollback؛ offline/transient → `pending_clearance` + enqueue في `einvoice_outbox`. عمود `zatca_clearance_status` مستقل عن `zatca_status` (الذي يعكس توليد artifacts محليًا فقط) لمنع الخلط بين الحالتين. migration `0016_invoice_clearance_fields.py`. اختُبر ببرنامج محاكاة 6 سيناريوهات: flag-off / non-SA / cleared / rejected / offline / error — جميعها تعطي القيم المتوقعة. |
| 7 | Sales/POS | `services/scheduler.py` + alembic 0015 | - | **[FIXED in T1.5b — 2026-05-01]** إدارة CSID: جدول جديد `zatca_csid` (environment, pcsid, secret_encrypted, issued_at, expires_at, status, last_alert_threshold_days, renewed_to_id) مع UNIQUE INDEX على `(environment) WHERE status='active'`. Scheduler job جديد `check_zatca_csid_expiry` يعمل كل 12 ساعة عبر جميع tenant DBs، يضبط الـCSIDs المنتهية تلقائيًا إلى `expired`، ويرسل تنبيهات عند 30/7/1 يومًا متبقيًا (يُسجَّل في `notifications` إن وُجدت + `logger.warning`). آلية `last_alert_threshold_days` تمنع التكرار. forward-compatible: tenants بدون الجدول تُتخطى بصمت. |

### نقاط البيع (POS) — إضافة من تقرير الأمن

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 7b | POS | `pos.py` | 1049 | ~~**`ON CONFLICT DO UPDATE` بمرجع خاطئ للجدول**~~ — **[INVALID — verified empirically 2026-05-01]**: نفس فئة #4 — الصياغة صحيحة في PostgreSQL. الكود سليم — لا تغيير |

---

## 🔴 P1 — عالي (خطأ في المنطق الحسابي أو ثغرة أمنية كبيرة)

### لوحة التحكم (Dashboard)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 8 | Dashboard | `dashboard.py` | 135-136 | **إجمالي المبيعات في الداشبورد ليس من الفواتير بل من GL**: `total_income = -(SUM(balance) FROM accounts WHERE account_type='revenue')`. بينما تقرير المبيعات يحسبها من `SUM(total) FROM invoices + pos_orders`. الرقمان مختلفان بالضرورة |
| 9 | Dashboard | `dashboard.py` | 78-94 | الإيرادات والمصروفات في الفرع من `journal_lines` بالفترة، لكن المبيعات المتراكمة من `accounts.balance` (بدون فترة). `sales` تراكمي لكن `sales_change` شهري — تضارب في وحدات القياس |
| 10 | Dashboard | `dashboard.py` | 793-877 | **`widget_pending_tasks` لا يطبق فلتر الفرع إطلاقًا**. مدير فرع يرى مهام كل الفروع — تسريب بيانات |
| 11 | Dashboard | `dashboard.py` | 1137-1145 | **BI Analytics Dashboards تعتمد على Materialized Views** تُحدث كل 15 دقيقة. لا يوجد مؤشر في الواجهة يوضح أن البيانات قديمة حتى 15 دقيقة |
| 12 | Dashboard | `dashboard.py` | 309-311 | الرسم البياني المالي: `profit = s - e` لا يشمل تكلفة المبيعات (COGS). تسمية مضللة للـ "أرباح" الظاهرة |
| 13 | Dashboard | - | - | **لا وجود لنظام Smart Alerts**. لا جداول `alerts` ولا `alert_rules` ولا `alert_history`. النظام لا يعرف مفهوم "تنبيه ذكي" |
| 14 | Dashboard | `scheduler.py` | 492-505 | **لا يوجد أي مجدول للتنبيهات الذكية**. KPI Alerts functions موجودة في `kpi_service.py` لكنها غير مربوطة بأي مجدول أو إشعار |

### المحاسبة (Accounting)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 15 | Accounting | `invoices.py` | 225-229, 558-571 | **خلل جسيم في قيد المبيعات مع markup**: الـ markup يُضاف إلى `grand_total` (الطرف المدين) لكنه لا يُضاف إلى الأطراف الدائنة (Revenue + VAT). عند وجود markup، القيد الناتج غير متوازن بقيمة الـ markup |
| 16 | Accounting | `currencies.py` | 331-341 | **اتجاه FC balance معكوس للخصوم**: الكود يحسب رصيد العملة الأجنبية وكأن جميع الحسابات أصول. للخصوم، إعادة التقييم ستحسب أرباح/خسائر بعكس الاتجاه الصحيح |
| 17 | Accounting | `fiscal_lock.py` + `gl_service.py` + `invoices.py:590` | - | **آليتا قفل مختلفتان لنفس الغرض**: `fiscal_periods.is_closed` ≠ `fiscal_period_locks.is_locked`. فاتورة المبيعات لا تستدعي `check_fiscal_period_open` أبدًا، وتعتمد فقط على `gl_service.py` الداخلي. إذا أقفل المدير فترة عبر `fiscal_period_locks`، ستمر فواتير المبيعات دون منع |
| 18 | Accounting | `taxes.py` | 1030-1044 | **التسوية الضريبية لا تشمل المرتجعات**: `create_tax_settlement` يحسب VAT من `sales` و `purchase` فقط، لا يشمل `sales_return` و `purchase_return`. التسوية غير دقيقة |
| 19 | Accounting | `utils/accounting.py` | 20-61 | **دالتا تحقق مختلفتان**: `validate_je_lines` في `gl_service.py` تقبل سطرًا واحدًا (`if not lines`)، بينما نظيرتها في `utils/accounting.py` ترفض إذا `len(valid) < 2`. تناقض خطير — قيد ذاتي التوليد قد يُرفض في مكان ويُقبل في آخر |
| 20 | Accounting | `database.py` + `models/` | - | **تعريف الجداول مكرر**: SQLAlchemy ORM + raw SQL في `database.py`. خطر انحراف المخطط (schema drift) |

### سجلات التدقيق (Audit Trail)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 21 | Audit Trail | `audit.py` | 58-77 | **لا يوجد أي ضمان لعدم قابلية التعديل على مستوى قاعدة البيانات**. سجلات التدقيق يمكن تعديلها أو حذفها عبر SQL مباشر بدون أي trigger مانع |
| 22 | Audit Trail | - | - | **لا يوجد تسلسل تجزئة (Hash Chain) ولا Blockchain**. لا حقل `prev_hash` أو `checksum`. أي مسؤول نظام يمكنه تعديل أي سجل تدقيق دون أثر |
| 23 | Audit Trail | `audit.py` | 17, 56 | **لا يوجد تسجيل للقيمة القديمة والجديدة**. حقل `details` JSONB يُستخدم بطرق عشوائية. لا يوجد نمط `{"old": {...}, "new": {...}}` موحد |
| 24 | Audit Trail | - | - | **لا يوجد أي نظام لكشف الاحتيال إطلاقًا**. لا قواعد، لا أنماط، لا تحليل سلوك، لا scoring. سجلات التدقيق مجرد سجل أحداث passive |
| 25 | Audit Trail | - | - | **الكتابة متزامنة (Synchronous) مع commit مستقل**: كل `log_activity` تنفذ `INSERT` + `db_conn.commit()`. إذا فشل commit التدقيق، السجل يُفقد. والعكس: قد يُلتزم سجل التدقيق حتى لو أُلغيت المعاملة الأصلية |
| 26 | Audit Trail | `permissions.py` | 612-621 | **مسار جانبي يتجاوز `log_activity`**: `log_permission_denied` و `log_permission_change` ينفذان `INSERT INTO audit_logs` مباشرة بدون المرور بدالة `log_activity` |
| 27 | Audit Trail | - | - | **صلاحية `audit.manage` خطر رقابي**: مستخدم لديه هذه الصلاحية يمكنه الوصول لسجلات التدقيق وتعديلها عبر API. لا يوجد حظر على تعديل سجلات التدقيق لمن يملك هذه الصلاحية — "الحارس يمكن رشوته" |

### المهام الخلفية (Background Jobs)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 27 | Background Jobs | `main.py` | 217-220 | **`asyncio.create_task` بدون `try/except` شامل**: إذا حدث خطأ، الحلقة تموت بصمت ولن تعود أبدًا. لا supervisor يعيد تشغيلها |
| 28 | Background Jobs | - | - | **لا متانة (Persistence) للمجدول نفسه**: APScheduler يستخدم `MemoryJobStore`. إذا انقطع الخادم، المهمة التي كانت في منتصف التنفيذ تضيع |
| 29 | Background Jobs | `scheduler.py` | 13, 53, 395 | **`BackgroundScheduler()` بدون timezone**: يستخدم توقيت نظام التشغيل المحلي. لا يوجد دعم لتعدد المناطق الزمنية للشركات |
| 30 | Background Jobs | `scheduler.py` + `worker.py` | - | **جميع أخطاء المجدول تُسجل فقط في `logger.error()`**: لا Sentry في `worker.py`، لا بريد، لا Slack. أي خطأ في مهمة خلفية لن يُكتشف أبدًا |
| 31 | Background Jobs | - | - | **لا يوجد نظام أولويات ولا طابور انتظار حقيقي**: لا Celery، لا Redis Queue، لا RabbitMQ. كل شيء APScheduler + asyncio tasks مباشرة |
| 32 | Background Jobs | - | - | **لا يوجد Health Check للمجدول**: لا endpoint `GET /health/scheduler` للتحقق من أن جميع المهام تعمل |

### استراتيجية الكاش (Cache/Redis)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 33 | Cache | `accounting.py:627,906` + `invoices.py:642,849` + `vouchers.py:196,393` + `purchases.py:2339` | - | **إبطال شامل يمسح كاش الشركة بالكامل**: `invalidate_company_cache` يُستدعى بعد كل قيد محاسبي أو فاتورة أو سند، ويمسح كل مفاتيح الكاش (تقارير + داشبورد + كل شيء). Overkill يجعل الكاش عديم الفائدة عمليًا |
| 34 | Cache | `cache.py` | 183-206 | **لا يوجد أي حماية من Cache Stampede**: الـ `@cached` هو `get-if-miss-then-set` بسيط بدون Lock/Mutex. عند انتهاء صلاحية مفتاح، كل الطلبات المتزامنة ستحسب نفس النتيجة الثقيلة في نفس الوقت |
| 35 | Cache | `cache.py` | 27-61 | **MemoryCache لكل عامل دون تزامن**: في بيئة متعددة العمال، كل عامل لديه `MemoryCache` مستقل. مستخدمون مختلفون قد يرون بيانات مختلفة |
| 36 | Cache | - | - | **الكاش لا يُبطل بالحدث (Event-Driven)**: المجدول يُجري عمليات بدون استدعاء `invalidate_cache`. المستخدمون قد يرون بيانات قديمة بعد عملية المجدول |
| 37 | Cache | - | - | **`?no_cache=1` موثق لكنه غير مُنفذ**: الـ decorator لا يقرأ هذا البارامتر فعليًا. المستخدم لا يمكنه تجاوز الكاش |

### CRM والمبيعات (CRM & Sales)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 38 | CRM | `crm.py` | 297-306 | **حذف الفرصة يحذفها نهائيًا** (hard delete) بدون فحص للتبعيات. يفقد بيانات تاريخية ثمينة للتحليل |
| 39 | CRM | `crm.py` | 569-616 | **فقدان بيانات عند تحويل الفرصة إلى عرض سعر**: يُنشأ سطر واحد فقط (`quantity=1, unit_price=expected_value`) بغض النظر عن تفاصيل الفرصة |
| 40 | CRM | - | - | **الفرص لا تُنشئ أي قيد محاسبي**. القيمة المتوقعة لا تظهر في أي تقرير مالي. لا يوجد اعتراف بالإيراد المتوقع |
| 41 | CRM | `scheduler.py` | 492-505 | **لا يوجد أي مجدول لمتابعة CRM**: لا تنبيه للمواعيد (`due_date`)، لا كشف للفرص المتوقفة (Stale Opportunities)، لا إشعار باقتراب `expected_close_date` |
| 42 | Sales/POS | - | - | **POS: المبيعات غير المتصلة لا تُعالج أبدًا**: `pos_offline_inbox` موجود في قاعدة البيانات لكن لا يوجد worker لمعالجتها. التعليق يشير لـ "POS worker" غير المنفذ |
| 43 | Sales/POS | - | - | **لا يوجد كشف تعارض (conflict detection) للمزامنة**: عند عودة الاتصال، لا يتم فحص تغير المخزون أو الأسعار أثناء فترة عدم الاتصال |
| 44 | Sales/POS | - | - | **لا يوجد API لتعديل فاتورة مؤكدة**: أي خطأ يتطلب إلغاءها وإعادة إنشائها من الصفر. لا `PUT /invoices/{id}` |
| 45 | Sales/POS | `invoices.py` | 667-672 | **ZATCA غير إلزامي عند إنشاء الفاتورة**: فشل ZATCA في `try/except` صامت — الفاتورة تُنشأ بدون علامة ZATCA |

### الأمن والصلاحيات (Security & Authorization)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 46 | Security | `invoices.py` | 756 | **صلاحية `sales.create` للإلغاء**: أي كاشير يمكنه إلغاء أي فاتورة مؤكدة لأي موظف آخر دون رقابة. لا توجد صلاحية `sales.delete` أو `sales.void` |
| 47 | Security | `returns.py` | 92, 224 | **صلاحية المرتجعات `sales.create`**: لا تمييز بين إنشاء مرتجع (مسودة) واعتماده (ينشئ قيودًا ويُعدل المخزون). لا يوجد حد زمني للمرتجعات |
| 48 | Security | `credit_notes.py` | 150 | **صلاحية الإشعار الدائن `sales.create`**: إشعار دائن يُنشئ قيدًا محاسبيًا ويُعدل رصيد العميل — يجب أن يتطلب صلاحية محاسبية أعلى |
| 49 | Security | `core.py` (HR) | 214-223 | **صلاحية `hr.view` تعرض جميع البيانات المالية الحساسة**: salary, housing_allowance, bank_account, IBAN لكل الموظفين لأي مستخدم لديه صلاحية `hr.view` |
| 50 | Security | - | - | **التشفير غير مستخدم فعليًا**: `field_encryption.py` يحتوي على AES-256-GCM ممتاز لكن `encrypt`/`decrypt` لم تُستدعَ في أي endpoint. جميع رواتب، IBAN، أرقام حسابات، مفاتيح ZATCA مخزنة كنص واضح |
| 51 | Security | `data_import.py` | 246, 254, 262, 267, 340 | **SQL Injection خطر**: `config['table']` يُمرر مباشرة إلى SQL بدون تحقق بـ `validate_sql_identifier` |
| 52 | Security | `pos.py` | 756-757 | **Silent exception swallowing**: فشل تحديث رصيد العميل في POS `except Exception: pass` — العملية تفشل دون إشعار المستخدم |
| 53 | Security | `invoices.py` | 667-672 | **Silent exception swallowing في ZATCA**: فشل تجهيز الفاتورة لـ ZATCA لا يُمنع إنشاء الفاتورة ولا يُبلغ المستخدم |

### إدارة المستندات (DMS)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 54 | DMS | `main.py` | 474-476 | **`/uploads` مخدوم كـ StaticFiles عام بدون أي مصادقة**: أي شخص يعرف UUID ملف يمكنه تحميله مباشرة بدون تسجيل دخول |
| 55 | DMS | `services.py` | 714-736 | **`download_document` بدون فحص مسار ولا `access_level`**: لا يتحقق من أن المسار داخل `UPLOAD_DIR`، ولا يراعي قيود `access_level` (مثل `admin_only`) |
| 56 | DMS | - | - | **لا يوجد تشفير للملفات على القرص (Encryption at Rest)**: العقود، كشوف المرتبات، المستندات السرية — كلها plaintext |
| 57 | DMS | `services.py` | 739-760 | **حذف المستند (soft delete) لا يحذف الملف من القرص**: الملفات المتراكمة تملأ القرص للأبد |
| 58 | DMS | - | - | **لا يوجد منظف ملفات يتيمة (Orphan File Cleaner)**: الملفات المرفوعة الفاشلة والـ soft-deleted تبقى للأبد |
| 59 | DMS | `reconciliation.py` | 287-334 | **استيراد كشوف البنك بدون أي فحص أمني**: `preview_import` و `confirm_import` لا يستدعيان `validate_file_extension` أو `validate_file_size` أو `validate_file_mime_and_signature` |
| 60 | DMS | `bank_feeds.py` | 35-74 | **استيراد MT940/CSV بدون أي فحص أمني**: نفس الثغرة في نقاط استيراد بيانات البنك |
| 61 | DMS | `reconciliation.py` | 287-334 | **استيراد كشوف البنك بدون حد حجم**: ملف 500 MB سيُقرأ كاملاً في الذاكرة وقد يقتل الخادم. لا يوجد حد حجم على نقاط استيراد البيانات المالية |

### مستودع البيانات (Database)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 59 | Database | `invoices.py` | 368-389 | **حلقة INSERT فردية لأسطر الفاتورة**: N استعلام لكل سطر. يجب استخدام `executemany` أو `INSERT INTO ... SELECT` دفعة واحدة |
| 60 | Database | `purchases.py` | 1343-1449 | **نفس النمط — INSERT فردي لكل سطر فاتورة مشتريات** + تحديث مخزون لكل منتج |
| 61 | Database | `core.py` (HR) | 809-913 | **`generate_payroll`: حلقة لكل موظف مع 6+ استعلامات فرعية لكل موظف**. 50 موظف = ~350 استعلامًا |
| 62 | Database | `invoices.py` | 278-285 | **استعلام `information_schema` مرتين** عند كل إنشاء فاتورة — لجلب أسماء الأعمدة ديناميكيًا. بطيء وغير ضروري |
| 63 | Database | - | - | **جدول `leave_requests` بدون أي فهارس**: أي استعلام سيمسح الجدول كاملًا. يحتاج `(status, start_date)` + `(employee_id, start_date)` فورًا |

### الموارد البشرية (HR & Payroll)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 64 | HR | - | - | **لا يوجد ربط بين الحضور والرواتب على الإطلاق**: `generate_payroll` لا يستعلم عن `attendance` أبدًا. لا خصم أيام غياب، لا خصم تأخير، لا احتساب ساعات عمل فعلية |
| 65 | HR | - | - | **لا يوجد مفهوم "يوم عمل" أو "سياسة دوام"** في النظام. لا تعريف لساعات العمل الرسمية أو أيام العطل الأسبوعية |
| 66 | HR | `field_encryption.py` | - | **التشفير غير مُستخدم فعليًا**: جميع بيانات الرواتب والموظفين تُخزَّن وتُقرأ كنص واضح |
| 67 | HR | `wps_compliance.py` | 563-594 | **مخصص نهاية الخدمة لا يُبنى بشكل دوري**: لا قيد شهري/سنوي لتكوين المخصص. عند التسوية يُعكس رصيد غير موجود في الدفاتر |

### المصروفات (Expenses)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 68 | Expenses | `treasury.py` | 448-579 | **مسار موازٍ للمصروفات يتجاوز نظام الاعتماد تمامًا**: `POST /treasury/transactions/expense` يُنشئ قيدًا محاسبيًا فوريًا بدون أي تدفق اعتماد |
| 69 | Expenses | `expenses.py` | 488-489 | **`requires_approval=False` يمرر المصروف فورًا**: المصروف يُنشأ ويُنشأ القيد المحاسبي فورًا بدون أي اعتماد |
| 70 | Expenses | - | - | **لا يوجد تتبع لتسوية السلف النقدية (Cash Advance Settlement)**: لا نموذج "تسوية سلفة". السلفة إما مسددة بالكامل عبر خصم الراتب فقط |
| 71 | Expenses | - | - | **لا يوجد تنبيه للسلف المتأخرة التسوية**: لا مجدول يفحص السلف التي مضى عليها وقت بدون تسوية |
| 72 | Expenses | - | - | **لا توجد عهدة (Custody) محاسبية**: عند تسليم عهدة (جهاز، مركبة) لا يُنشأ قيد محاسبي |
| 73 | Expenses | `scheduler.py` | 492-505 | **المجدول لا يشغّل المصروفات المتكررة**: `generate_all_due_templates` موجودة لكن المجدول لا يحتوي على أي وظيفة لتوليد القيود المتكررة تلقائيًا. يجب تشغيلها يدويًا كل فترة |

### التصنيع (Manufacturing)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 73 | Manufacturing | `core.py` | 1804-1809 | **استعلام MRP خاطئ**: `on_order` يقرأ من `purchase_invoice_items` بدل `purchase_order_lines`. فواتير الشراء ≠ أوامر الشراء |
| 74 | Manufacturing | - | - | **العائد (yield_quantity) غير مستخدم**: حقل `yield_quantity` في BOM لا يُطبق في أي معادلة إنتاج. النظام يفترض أن كل الكمية تُنتج بنجاح |
| 75 | Manufacturing | - | - | **alembic تعارض أعمدة**: migration `0012_phase5_world_comparison.py` يضيف أعمدة `yield_quantity`, `waste_percentage` معرفة مسبقًا في `database.py` — قد يسبب فشل migration |

### الخدمات الميدانية (FSM)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 76 | FSM | `services.py` | 360-407 | **تكاليف قطع الغيار لا تخصم من المخزون إطلاقًا**: `add_service_cost` يُسجل فقط سطر تكلفة بدون أي تأثير على المخزون. القطعة المستهلكة تبقى في المخزون |
| 77 | FSM | - | - | **لا يوجد نظام "قطع غيار خدمية" (Service Parts)**: لا جدول `service_parts` أو `spare_parts`. لا يمكن تتبع استهلاك القطع في الصيانة مقابل المخزون |
| 78 | FSM | - | - | **لا يوجد نظام صيانة وقائية (Preventive Maintenance) آلية**: لا جداول `pm_schedules`، لا توليد تلقائي لأوامر الخدمة حسب المواعيد |
| 79 | FSM | - | - | **لا يوجد مجدول يولد أوامر خدمة من عقود الصيانة الدورية** |
| 80 | FSM | - | - | **لا يوجد SLA على أوامر الخدمة الميدانية**: لا وقت استجابة (`response_time`)، لا وقت إصلاح (`resolution_time`)، لا تنبيه عند الاقتراب من خرق SLA |
| 81 | FSM | - | - | **لا يوجد نموذج تسعير للخدمات**: لا قائمة أسعار للخدمات أو أسعار موحدة للعمالة/القطع. كل شيء يدوي |

### التقارير وذكاء الأعمال (Reports & BI)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 82 | Reports/BI | `reports.py` | 2472-2530 | **التحليل الأفقي يُنفذ استعلامًا لكل حساب × كل فترة**: O(n²) استعلامات. مع 200 حساب و3 فترات = 600 استعلام منفصل. قد يجمّد النظام |
| 83 | Reports/BI | `reports.py` | 1226-1229 | **الميزانية العمومية: `LEFT JOIN` بدون تصفية زمنية**: ينضم مع كل `journal_lines` التاريخية أولاً ثم يصفي. مع ملايين السجلات قد يستغرق دقائق |
| 84 | Reports/BI | `reports.py` | 1532-1556 | **تصنيف IAS 7 يعتمد على استدلال نصي (Heuristics) من اسم الحساب**: `'قرض' in name_lower` → تمويلي. لا يوجد عمود `cash_flow_classification` في جدول الحسابات |

### التكاملات (Integrations)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 85 | Integrations | `zatca_adapter.py` | 24-60 | **ZATCA: لا يوجد تدفق CSID onboarding**. الـ adapter يفترض أن PCSID/secret موجودان مسبقًا. لا تجديد شهادة تلقائي |
| 86 | Integrations | `zatca_adapter.py` | 270-278 | **ZATCA offline mode لا يسجل في outbox**: الفاتورة قد لا تُرسل أبدًا عند عودة الاتصال |
| 87 | Integrations | - | - | **ETA/FTA (مصر والإمارات) غير منفذين**: كلا المحولين stubs مع `dry_run: True` فقط |
| 88 | Integrations | - | - | **لا يوجد CAMT.053 parser**: معظم البنوك الحديثة تستخدم ISO 20022. غياب هذا المحلل يمنع التكامل مع هذه البنوك |
| 89 | Integrations | - | - | **Payment gateways لا retry**: فشل واحد في Stripe/Tap/PayTabs = فشل نهائي بدون إعادة محاولة |

### محرك الإشعارات (Notifications)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 90 | Notifications | `notification_service.py` | 54-75 | **لا يوجد كشف للحلقات البرمجية (Loop Detection)**: خطأ برمجي يسبب حلقة في `dispatch()` سيرسل آلاف الإيميلات والإشعارات الفورية |
| 91 | Notifications | - | - | **لا يوجد حد إرسال لكل مستخدم/فترة**: يمكن إرسال 10,000 إشعار لنفس المستخدم في دقيقة واحدة |
| 92 | Notifications | `email_service.py` | 157-196 | **حقن HTML مباشر بدون ترميز في كل القوالب**: `{requester}`, `{description}`, `{notes}` وغيرها تُحقن في HTML الإيميل بدون `html.escape()` |
| 93 | Notifications | `auth.py` | 1521-1533 | **حقن HTML في إيميل forgot-password**: `{found_user.full_name}` يُحقن مباشرة بدون ترميز |

### محرك البحث (Search)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 94 | Search | جميع الراوترز | - | **`ILIKE '%query%'` مع Leading Wildcard يمنع استخدام الفهارس تمامًا**. كل استعلام بحث هو Full Table Scan |
| 95 | Search | - | - | **لا يوجد نظام فهرسة إطلاقًا**: لا PostgreSQL Full-Text Search (tsvector)، لا pg_trgm، ولا محرك بحث خارجي. لا GIN/GiST indexes |
| 96 | Search | - | - | **لا يوجد بحث في محتوى الملفات (PDF/Excel)**: محتوى الملفات المرفوعة غير مفهرس وغير قابل للبحث |
| 97 | Search | `duplicate_detection.py` | 46-47 | **`REGEXP_REPLACE` في WHERE على الهاتف**: Regex على عمود الهاتف داخل WHERE يمنع أي فهرس ويُجبر Full Table Scan مع معالجة regex لكل صف |

### سلسلة التوريد (Supply Chain)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 98 | Supply Chain | - | - | **لا يوجد نظام تنبيه تلقائي للمخزون المنخفض**: إعداد `notify_low_stock` معطل فعليًا. لا scheduler ولا webhook |
| 99 | Supply Chain | `dashboard.py` + `kpi_service.py` | - | **المخزون المنخفض لا يطرح `reserved_quantity`**: الكميات المحجوزة مهملة في حساب المخزون المتاح فعليًا |
| 100 | Supply Chain | `stock_movements.py` | 87-90 | **`POST /receipt` لا يمنع الكميات السالبة**: يمكن إدخال قيمة سالبة عن طريق الخطأ لخصم المخزون دون فحص |
| 101 | Supply Chain | `shipments.py` | 344-354 | **الشحنات لا تُنشئ طبقات تكلفة FIFO/LIFO للوجهة**: منتجات FIFO تصل للوجهة بدون طبقة تكلفة |

### الخزينة (Treasury)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 102 | Treasury | `expenses.py` | 513-553 | **المصروف لا يُنشئ قيدًا محاسبيًا فوريًا عند `requires_approval=True`**: الصندوق قد صُرف منه المبلغ فعلاً لكنه لا يظهر في الدفاتر حتى الاعتماد |
| 103 | Treasury | `treasury.py` + `core_business.py` | 448-579, 78 | **`current_balance` يُحدَّث يدويًا** في كل عملية خزينة، بينما GL يُحدَّث عبر `update_account_balance`. رصيدان منفصلان لنفس الحساب |
| 104 | Treasury | - | - | **لا يوجد نموذج صندوق نقدي (Petty Cash Fund) منفصل**: الصناديق النقدية مجرد `treasury_accounts`. لا حد أقصى للصندوق، ولا إعادة تغذية، ولا عهدة |
| 105 | Treasury | `checks.py` | - | **لا يوجد تفعيل تلقائي للشيكات في تاريخ الاستحقاق**: لا مجدول يغير حالة الشيك من `pending` أو يصدر قيدًا محاسبيًا تلقائيًا عند حلول التاريخ |
| 106 | Treasury | `forecast_service.py` | 72-93 | **التنبؤ بالتدفقات النقدية لا يشمل**: الشيكات تحت التحصيل/الدفع، أوراق القبض/الدفع، المرتبات المستحقة، الالتزامات التعاقدية |

### الواجهة الأمامية (Frontend)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 107 | Frontend | - | - | **نقص حاد في سمات ARIA**: 19 مرجعًا فقط لـ `aria-*` و `role=` في ~450 ملف. معظم الأزرار والنماذج والجداول بدون accessibility labels |
| 108 | Frontend | - | - | **لا يوجد skip-link**: لا رابط "تخطي إلى المحتوى" — إلزامي لـ WCAG 2.1 AA |
| 109 | Frontend | - | - | **لا تحديثات متفائلة (optimistic updates)**: بعد كل عملية (إنشاء/تعديل/حذف)، إعادة تحميل كاملة من الخادم. تجربة مستخدم بطيئة |
| 110 | Frontend | `OvertimeRequests.jsx` | 18, 140 | **مضاعفات العمل الإضافي صلبة (`1.5`, `2.0`)** في الواجهة وتختلف عن `overtime_rates_config` في الباك |

### إضافات P1 من التقارير الفردية

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 110a | Security | `core.py` (HR) | 1878 | **`GET /payslips` يعرض رواتب جميع الموظفين لأي مستخدم `hr.view`**: نقطة نهاية منفصلة عن `GET /employees/{id}` (P1 #49) — تعرض بيانات الرواتب بالجملة |
| 110b | Cache | التقارير + الكاش | - | **مفارقة البيانات القديمة**: مع 50 قيدًا يوميًا و `invalidate_company_cache` بعد كل قيد، الكاش يُمسح 50 مرة. لكن بين القيود (60 ثانية TTL) المستخدمون يرون أرقامًا قديمة — قرارات مبنية على بيانات متأخرة |
| 110c | Audit Trail | - | - | **لا يوجد كشف للأنماط الزمنية المشبوهة (Temporal Correlation)**: النظام لا يكتشف أنماطًا مثل: إنشاء مورد + فاتورة شراء + اعتمادها خلال دقيقة واحدة |
| 110d | Database | `production_orders` | - | **فهرس مفقود `(status, due_date)`**: تصفية أوامر الإنتاج حسب الحالة والتاريخ في أرضية المصنع تمسح الجدول كاملاً |
| 110e | Sales/POS | `returns.py` | 224 | **لا يوجد حد زمني للمرتجعات (Return Window)**: يمكن إنشاء مرتجع على فاتورة عمرها سنوات بدون أي قيد زمني قابل للتكوين |
| 110f | Supply Chain | `stock_movements.py` | 29-131 | **نقاط `/receipt` و `/delivery` القديمة لا تُنشئ قيودًا محاسبية**: حركات مخزون بدون أثر في الدفاتر — انحراف بين المخزون الفعلي والمالي |
| 110g | Treasury | - | - | **لا يوجد فحص مطابقة تلقائي بين `treasury_accounts.current_balance` و `accounts.balance`**: الاختلاف بين رصيد الخزينة ورصيد GL قد يستمر لأشهر بدون اكتشاف |
| 110h | Reports/BI | `reports.py` | 2467-2510 | **التحليل الأفقي: فشل استعلام واحد يُسقط الحساب بصمت**: لا `try/except` حول الاستعلامات الداخلية — تقرير ناقص بدون تحذير للمستخدم |
| 110i | Search | `products.py` | 122-124 | **بحث المنتجات ثقيل جدًا**: `ILIKE '%query%'` + `LEFT JOIN inventory` + `GROUP BY` — من أثقل نقاط النهاية. 5 عمليات بحث متزامنة قد تشل قاعدة البيانات |
| 110j | FSM | `governance.py` | 1010-1014 | **قيد GL لأمر الخدمة يسجل COGS بدون استهلاك مخزون**: يستخدم `acc_map_cogs_services` لكن لا يسجل خصم المخزون عبر `acc_map_inventory` — القيد المحاسبي لاستهلاك القطع غير مكتمل |

---

## 🟠 P2 — متوسط (خلل في المنطق أو نقص وظيفي)

### لوحة التحكم (Dashboard)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 111 | Dashboard | `dashboard.py` | 309-311 | الرسم البياني المالي: `profit = s - e` لا يشمل COGS. تسمية "أرباح" مضللة (يجب تسميتها `gross_profit`) |
| 112 | Dashboard | `dashboard.py` | 180-188 | الرصيد النقدي يُحسب مرتين مختلفتين: من `accounts.balance` ومن `treasury_accounts JOIN accounts`. الرقمان قد يختلفان |
| 113 | Dashboard | `dashboard.py` | 134-141 | عند عدم تحديد تاريخ، المصروفات = `SUM(balance)` بدون إشارة سالبة. إذا كان هناك مصروفات بإشارات مختلفة، النتيجة خاطئة |
| 114 | Dashboard | `dashboard.py` | 229 | `cash_status = "Stable"` ما دام الرصيد > 0. حتى لو الرصيد 1 ريال والمصروفات الشهرية 100,000 |
| 115 | Dashboard | `dashboard.py` | 170-178 | `calc_change` مقصوص عند ±999%. المدير لا يرى قفزات كبيرة |
| 116 | Dashboard | `dashboard.py` | 740-790, 793-877 | `widget_low_stock` و `widget_pending_tasks` قوائم ساكنة — لا إشعارات نشطة |
| 117 | Dashboard | `dashboard.py` | 80-163 | دالة `calculate_period_stats` تُستدعى 3 مرات، كل استدعاء 3-4 استعلامات. المجموع ≈ 10-12 استعلامًا |
| 118 | Dashboard | `dashboard.py` | 259-298 | الرسم البياني المالي: استعلامان ثقيلان (UNION + treasury_transactions). لا تجميع مسبق أو MV |
| 119 | Dashboard | `kpi_service.py` | 1429-1606 | `_build_executive_alerts()` و `_build_financial_alerts()` قادرة على كشف المشاكل لكنها غير مربوطة بأي مجدول أو إشعار |

### المحاسبة (Accounting)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 120 | Accounting | `utils/accounting.py` | 50-51 | استخدام جمع `float` مباشر `sum(l.get("debit", 0))` بدل `Decimal` — يُعرّض لخطأ الفاصلة العائمة |
| 121 | Accounting | `purchases.py` | 1276-1284 | استدعاء `compute_invoice_totals` بدون تمرير `markup_amount` و `header_discount_pct` — خصم رأسي أو هامش ربح في فاتورة مشتريات لن يُحتسب |
| 122 | Accounting | `accounting.py` | 1426-1431 | `close_fiscal_year` يغلق `fiscal_periods.is_closed` لكنه لا يُحدِّث `fiscal_period_locks.is_locked` — تناقض بين الجدولين |
| 123 | Accounting | `gl_service.py` | 168 | العملة الأساسية الافتراضية `SYP` عند فقدان الإعدادات — غير متسقة مع الزرع الافتراضي SAR |
| 124 | Accounting | `utils/accounting.py` | 131 | نفس السقوط إلى `SYP` في `get_base_currency` |
| 125 | Accounting | `industry_coa_templates.py` | 60, 77 | مفاتيح ربط VAT (`acc_map_vat_in`, `acc_map_vat_out`) لا تُسجل تلقائيًا في `company_settings` عند زراعة COA |
| 126 | Accounting | `invoices.py` | 520-602 | فاتورة مبيعات → قيد تلقائي. الخلل الوحيد: markup غير متوازن (انظر P1 #15) |
| 127 | Accounting | `fiscal_lock.py` + `gl_service.py` | - | نظاما قفل متوازيان لنفس الغرض دون تنسيق |
| 128 | Accounting | `accounting.py` | 598 | استيراد مكرر لـ `gl_create_journal_entry` داخل الدالة مع وجود استيراد على مستوى الموديول |

### سجلات التدقيق (Audit Trail)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 129 | Audit Trail | `database.py` | 6713-6741 | القيود المحاسبية محمية بـ `trg_je_immutable` لكن سجلات التدقيق غير محمية. الحارس ليس لديه حارس |
| 130 | Audit Trail | `scheduler.py` | 284-288 | المجدول يحذف سجلات التدقيق بعد 7 سنوات بـ `DELETE` مباشر بدون أرشفة خارجية |
| 131 | Audit Trail | `permissions.py` | 612-621 | `log_permission_denied` و `log_permission_change` ينفذان `INSERT INTO audit_logs` مباشرة بدون `log_activity` |
| 132 | Audit Trail | `crm.py:266`, `expenses.py:557-562`, `gl_service.py:277-285` | - | تفاصيل التغيير عشوائية: أحيانًا أسماء الحقول فقط، أحيانًا القيم الجديدة فقط. لا نمط موحد old/new |
| 133 | Audit Trail | `audit.py` | 77 | كل `log_activity` ينفذ `commit()` مستقل — خطر تناقض معاملاتي |
| 134 | Audit Trail | - | - | لا كتابة غير متزامنة للتدقيق: لا `@background`، لا message queue، لا outbox pattern لسجلات التدقيق |
| 135 | Audit Trail | - | - | **لا يوجد كشف لتسجيل الدخول من موقع جغرافي مختلف** (Impossible Travel) |
| 136 | Audit Trail | - | - | **التوقيت من خادم التطبيق** وليس `CURRENT_TIMESTAMP` من قاعدة البيانات — قابل للتلاعب بساعة الخادم |
| 137 | Audit Trail | - | - | **هندسة اجتماعية + فشل التدقيق الصامت**: في الوضع الافتراضي (`critical=False`)، فشل كتابة سجل التدقيق لا يُلغي العملية. محتال يمكنه تعمّد إرسال `details` بحجم هائل لفشل التسجيل وتجاوز الرقابة |
| 138 | Audit Trail | - | - | **لا يوجد batching أو buffering لسجلات التدقيق**: كل `log_activity` استدعاء منفصل. عملية واحدة قد تستدعي `log_activity` 3 مرات = 3 INSERTs منفصلة مع commit لكل منها |

### المهام الخلفية (Background Jobs)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 137 | Background Jobs | `main.py` | 306 | عملية الويب لا توقف المجدول بشكل صحيح: `engine.dispose()` بعد `yield` بدون `scheduler.shutdown()` |
| 138 | Background Jobs | `scheduler.py` | 493-504 | جميع المهام تستخدم `misfire_grace_time=60`. مهمة شهرية لها 300 ثانية فقط من السماح — إذا كان الخادم مشغولاً 5 دقائق، الدورة الشهرية تفوّت |
| 139 | Background Jobs | `scheduler.py` | 108-115 | `check_scheduled_reports` — سباق عند تحديث `next_run_at` بدون `FOR UPDATE` |
| 140 | Background Jobs | - | - | المهام 1-4, 8 ليس لديها `idempotency_key`. `max_instances=1` يحمي داخل نفس العملية فقط، وليس عبر العمال |
| 141 | Background Jobs | - | - | تعدد العمال × `max_instances=1`: 4 عمال = 4 مثيلات من نفس المهمة تعمل في نفس الوقت في وضع `in_process` |
| 142 | Background Jobs | `outbox_relay.py` | 85-97 | بعد `MAX_ATTEMPTS=10`، صفوف outbox تُترك بدون `delivered_at` ولا status خاص. لا يمكن التمييز بين "سينعالج" و"مهمل" |
| 143 | Background Jobs | - | - | لا supervisor للـ worker المخصص: إذا مات (OOM, segfault) لا أحد يعرف |
| 144 | Background Jobs | - | - | **لا آلية إعادة تشغيل للمجدول عند فشل التهيئة**: إذا فشل `start_scheduler()` في `main.py` لأي سبب (خطأ Redis مثلاً)، كل الـ 6 مهام لن تعمل أبدًا. لا retry للتهيئة |

### استراتيجية الكاش (Cache/Redis)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 144 | Cache | جميع التقارير + الداشبورد | - | الإبطال الشامل يجعل الكاش عديم الفائدة في البيئات النشطة: 90% من طلبات التقارير cache miss |
| 145 | Cache | `cache.py` | 116-119 | إذا فشل Redis، النظام يقع على `MemoryCache`. في الإنتاج، كل عامل لديه حالة كاش مختلفة تمامًا |
| 146 | Cache | `cache.py` | 27-61 | `MemoryCache` قواميس Python بدون حد أقصى. في وضع fallback، سينمو بلا حدود حتى Out of Memory |
| 147 | Cache | - | - | لا توجد تدفئة (Warm-up): عند بدء التشغيل، أول مستخدم يتحمل كامل وقت الحساب |
| 148 | Cache | `scheduler.py` | 492-505 | المجدول يحدث `mv_*` كل 15 دقيقة لكنه لا يُبطل أي كاش API. بيانات قديمة إضافية فوق الـ 15 دقيقة |

### CRM والمبيعات (CRM & Sales)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 149 | CRM | `invoices.py` | - | **لا يوجد رابط تلقائي من طلب البيع إلى الفاتورة**: لا `Order → Invoice Conversion` endpoint |
| 150 | CRM | `crm.py` | - | **لا يوجد endpoint لتحديث حالة نشاط** (تسجيل الاكتمال). الأنشطة تُنشأ فقط ولا تُحدَّث |
| 151 | CRM | `crm.py` | 55-59 | نموذج `ActivityCreate` ينقصه حقول: `outcome`, `duration`, `is_completed` |
| 152 | CRM | - | - | **لا يوجد إشعار عند تعيين فرصة لمندوب جديد**. بينما يوجد إشعار عند تعيين تذكرة دعم |
| 153 | CRM | `sales_improvements.py` | 37-80 | تحويل عرض السعر → طلب لا يتحقق من الحد الائتماني قبل التحويل |
| 154 | CRM | `sales_rfq.py` | 47-63 | تحويل الفرصة لا يُسجِّل المندوب تلقائيًا في العمولة. يجب ربط `assigned_to` بحقل `salesperson_id` في العمولة |
| 155 | CRM | - | - | التذكيرات (Reminders) غير مفعلة: `due_date` موجود في الأنشطة لكن لا يُستخدم تشغيليًا |
| 156 | CRM | - | - | الحملات التسويقية لها `budget` لكن لا قيد محاسبي عند إنفاق الميزانية |
| 157 | CRM | `crm.py` | 577-593 | **عرض السعر المُنشأ من الفرصة بحالة `draft` دائمًا**: لا ينتقل تلقائيًا إلى `sent` أو `accepted`، مما يتطلب تغييرًا يدويًا للحالة |

### الأمن والصلاحيات (Security & Authorization)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 157 | Security | 40+ موقع | `roles.py:820`, `crm.py:264,499...`, `projects.py:1005,1175...`, `pos.py:1245...`, `advanced.py:88,174...` | **Dynamic UPDATE بدون `validate_sql_identifier`**: أسماء الأعمدة من مدخلات المستخدم تُحقن مباشرة في SQL عبر f-string |
| 158 | Security | `ThermalPrintSettings.jsx` | 150 | **XSS عبر `document.write`**: بيانات من state/react props تمرر عبر template literals. بيانات المنتج غير موثوقة قابلة للحقن |
| 159 | Security | `CustomerDisplay.jsx` | 145 | نفس نمط `document.write` مع بيانات غير موثوقة |
| 160 | Security | `auth.js` | 14 | **JWT access token في localStorage** — عرضة لـ XSS. Refresh token في HttpOnly cookie لكن access token لا يزال في localStorage |
| 161 | Security | `stock_movements.py` | 29 | صلاحية `stock.manage` واسعة جدًا للـ `/receipt` و `/delivery` — تسمح بالتلاعب بالمخزون دون قيد محاسبي |
| 162 | Security | `settings.py` / `company_settings` | - | ZATCA private key + certificate + SMTP password مخزنة كنص واضح |
| 163 | Security | `adjustments.py` | 272 | `detail=f"حدث خطأ: {str(e)}"` — يمرر تفاصيل استثناء SQLAlchemy للمستخدم |
| 164 | Security | `main.py` | 340-342 | Swagger UI + ReDoc متاحان في production بدون حماية |
| 165 | Security | `auth.py` | - | لا rate limiting مخصص لمحاولات login الفاشلة |
| 166 | Security | - | - | **منطق الأعمال مبعثر**: نفس العملية (مثلاً إنشاء قيد محاسبي) منفذة في 15+ router مختلف مع duplicate code — غياب service layer موحد |
| 167 | Security | `database.py` + `models/` | - | **SQL خام + ORM مختلطان**: تعريفان للـ schema في مكانين مختلفين (DDL + نماذج SQLAlchemy) = خطر انحراف المخطط |

### إدارة المستندات (DMS)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 166 | DMS | `sql_safety.py` | 173-201 | **هجوم الامتداد المزدوج (Double Extension) غير مكشوف**: `os.path.splitext("file.php.pdf")` يُرجع `.pdf`. المهاجم يمكنه رفع `shell.php.pdf` |
| 167 | DMS | `main.py` | 474-476 | **`/uploads` و `/api/uploads`**: الملفات متاحة عبر مسارين — يضاعف سطح الهجوم بدون فائدة |
| 168 | DMS | - | - | **لا يوجد سجل تدقيق لتحميل الملفات (Download Audit Log)**: لا يُسجل من حمّل أي مستند ومتى |
| 169 | DMS | - | - | **لا يوجد فحص فيروسات (Anti-Malware Scan)**: لا ClamAV ولا VirusTotal |
| 170 | DMS | `services.py` | 287-306, 739-760 | حذف طلب الخدمة لا يمس المستندات المرتبطة. حذف المستند (soft delete) لا ينظف الإصدارات |
| 171 | DMS | - | - | لا يوجد حد أقصى لحجم الطلب على مستوى الخادم. لا Quota تخزين للمستخدمين |
| 172 | DMS | - | - | **لا يوجد حد أقصى لحجم جسم الطلب (MaximumFileSize middleware)**: FastAPI قد يقبل تحميلات ضخمة قبل أن تصل لأي دالة تحقق في التطبيق |
| 173 | DMS | `services.py` | 562-564 | **تحميل المستندات يقرأ المحتوى كاملاً في الذاكرة**: 50 MB لكل تحميل في الذاكرة دفعة واحدة — عبء تحت التحميل المتزامن |
| 174 | DMS | `services.py` | 714-736 | **`download_document` ينقل الملفات عبر HTTP**: إذا لم يُفرض TLS/HTTPS، المستندات الحساسة تنتقل plaintext |
| 175 | DMS | `projects.py` | 1915 | **تحميل مستندات المشاريع بمسار نسبي**: يعتمد على CWD وقد يُحل إلى مسار غير متوقع في بيئات مختلفة |
| 176 | DMS | `system_completion.py` | 55-99 | **استيراد كشف البنك بفحص بدائي فقط**: `.endswith(('.csv', '.txt'))` بدون MIME أو magic byte validation |

### قاعدة البيانات (Database)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 172 | Database | `attendance` | - | FK `employee_id -> employees(id)` بدون ON DELETE RESTRICT صريح |
| 173 | Database | `leave_requests` | - | FK `employee_id -> employees(id)` بدون ON DELETE |
| 174 | Database | `payroll_entries` | - | FK `employee_id -> employees(id)` بدون ON DELETE |
| 175 | Database | فهارس مفقودة | - | `payroll_entries(employee_id, period_id)`, `attendance(date)` مستقل, `pos_orders(customer_id)` + `(order_date, status)`, `journal_lines(is_reconciled)` |
| 176 | Database | متعدد | - | **أعمدة قديمة مكررة**: `customer_id` + `supplier_id` بجانب `party_id` في جداول invoices/quotations/orders |
| 177 | Database | متعدد | - | **3 جداول لنفس الغرض**: `customer_transactions` + `supplier_transactions` + `party_transactions` |
| 178 | Database | `company_settings` | - | `setting_value TEXT` — تخزين المفاتيح الرقمية (account IDs) كنصوص، مما يمنع FK والتحقق |
| 179 | Database | `tax_groups` | - | `tax_ids JSONB DEFAULT '[]'` — مصفوفة JSON بدل جدول وسيط (many-to-many). لا FK أو INDEX على العناصر الفردية |
| 180 | Database | - | - | **لا يوجد نسخ احتياطي تلقائي** — لا scheduler، لا cron job. لا سياسة استبقاء للملفات |
| 181 | Database | `returns.py:187-198`, `pos.py:491-525` | - | INSERT فردي لكل سطر مرتجع ولكل سطر POS |
| 182 | Database | - | - | **غياب نمط soft delete موحد**: بعض الجداول تستخدم `is_deleted` (BOM, Routes)، والبعض `status='cancelled'` (Invoices)، والبعض لا يملك أيًا منهما |

### الموارد البشرية (HR & Payroll)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 182 | HR | `advanced.py` | 269 | المضاعفات `1.5` و `2.0` صلبة رغم وجود جدول `overtime_rates_config` غير المستخدم |
| 183 | HR | `core.py` | 841-850 | تجميع العمل الإضافي لا يتحقق من أن الطلب يقع ضمن فترة الرواتب — أي طلب معتمد من أي تاريخ يُضاف |
| 184 | HR | `core.py` | 994-999 | حالة `'processed'` للعمل الإضافي غير مُعرّفة في قيم status enum |
| 185 | HR | `advanced.py` | 323 | تناقض: GOSI صاحب العمل `11.75%` في الواجهة و `12.00%` في الحساب الفعلي |
| 186 | HR | `advanced.py` | 385 | المخاطر المهنية (`occupational_hazard_percentage`) غير مُضمّنة في `generate_payroll` |
| 187 | HR | `core.py` | 1820 | أجر أساس نهاية الخدمة يشمل `basic + housing + transport` بينما القانون ينص على الأجر الأساسي فقط |
| 188 | HR | `wps_compliance.py` | 68-216 | صيغة WPS ملف CSV وليس SIF حقيقي (fixed-width). البنوك السعودية قد ترفضه |
| 189 | HR | `wps_compliance.py` | 589 | حساب التسوية البنكي يستخدم `acc_map_cash` بدل `acc_map_bank` |
| 190 | HR | `core.py` (HR) | 214-223 | `GET /employees/{id}` يعيد salary, IBAN لأي مستخدم `hr.view` بدون فلترة |
| 191 | HR | `wps_compliance.py` | 563-594 | EOS settlement: `je_result` معامل كـ dict أو tuple — خطأ محتمل في unpacking |
| 192 | HR | - | - | **لا يوجد API لعكس/إلغاء فترة رواتب مرحلة** (reverse payroll). بمجرد الترحيل لا يمكن التراجع |
| 193 | HR | - | - | **لا يوجد زيادة جماعية للرواتب** (mass salary increment) — يجب تعديل كل موظف يدويًا |

### المصروفات (Expenses)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 192 | Expenses | `expenses.py` | 432-460 | فحص السياسات يُرجع `policy_warning` فقط — لا يمنع المصروف المخالف |
| 193 | Expenses | `expenses.py` | 328-363 | `validate_expense_against_policy` لا تُستدعى تلقائيًا عند إنشاء المصروف |
| 194 | Expenses | `expenses.py` | 445-460 | التحقق من الحد الشهري يفحص مجموع مصروفات الموظف فقط — لا يفحص الحد الشهري للقسم |
| 195 | Expenses | `accounting.py` | 1978 | قالب متكرر بـ `auto_post=True` يُنشئ قيودًا مرحَّلة تلقائيًا بدون مراجعة بشرية |
| 196 | Expenses | `accounting.py` | 1720-1973 | القوالب المتكررة تُنشئ قيودًا مباشرة لكنها لا تُنشئ سجلاً في جدول `expenses` — تقارير المصروفات لا تشملها |
| 197 | Expenses | - | - | **لا يوجد ربط بين السلفة والمصروفات**: لا يمكن للموظف تقديم إيصالات لتسوية جزء من السلفة |
| 198 | Expenses | `expenses.py` | 835-874 | لا واجهة للقيد العكسي (reversal) للمصروفات المعتمدة التي تحتاج تراجع |
| 199 | Expenses | `approval_utils.py` | 55-56 | **غياب سير عمل لا يمنع المصروف**: إذا لم يوجد `approval_workflow` مطابق، `try_submit_for_approval` تُرجع `None` — لكن المصروف يُنشأ بحالة `pending` وينتظر اعتمادًا لن يأتي أبدًا |
| 200 | Expenses | `expenses.py` | 432-460 | **لا تحقق فعلي من وجود إيصال مرفوع**: `requires_receipt` في السياسة يعطي تحذيرًا فقط. لا يوجد تحقق من وجود مستند مرفوع فعليًا قبل تقديم المصروف |

### التصنيع (Manufacturing)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 199 | Manufacturing | `core.py` | 1047 | خصم المخزون بدون قفل `FOR UPDATE` — سباق بيانات بين أمرين إنتاج |
| 200 | Manufacturing | `core.py` | 598 | التكاليف العامة (overhead) مبسطة: 30% ثابت من العمالة — لا تعكس التكلفة الحقيقية |
| 201 | Manufacturing | - | - | لا يوجد endpoint للاعتماد (`POST /orders/{id}/confirm`) للانتقال من draft إلى confirmed |
| 202 | Manufacturing | `core.py` | 1164 | لا يوجد إنتاج جزئي — `produced_quantity = quantity` دائمًا |
| 203 | Manufacturing | `core.py` | 1765 | MRP لمستوى واحد فقط — لا يتحقق من المكونات الفرعية (sub-assemblies) |
| 204 | Manufacturing | `core.py` | 1189-1210 | المنتجات الثانوية (by-products) لا تُكلَّف — تُضاف للمخزون بدون تكلفة |
| 205 | Manufacturing | `core.py` | 1312-1316 | WAC يحسب من جميع المستودعات وليس مستودع الوجهة فقط |
| 206 | Manufacturing | `core.py` | 1106 | `total_material_cost` خارج النطاق في `log_activity` — سيسبب `NameError` إذا لم يوجد BOM |
| 207 | Manufacturing | - | - | لا يوجد تخطيط سعة (capacity planning) آلي |
| 208 | Manufacturing | - | - | لا يوجد فحص جودة إلزامي قبل إكمال الإنتاج |
| 209 | Manufacturing | - | - | إنشاء أمر إنتاج بدون التحقق من صلاحية المستودع المصدر/الوجهة للفرع |
| 210 | Manufacturing | `shopfloor.py` | 147 | بدء العملية لا يتحقق من صحة `work_order_id` مقابل `routing_operation_id` |

### الخدمات الميدانية (FSM)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 211 | FSM | `services.py` | 255-261 | الانتقال إلى `completed` لا يشترط وجود تكاليف مسجلة أو ساعات فعلية |
| 212 | FSM | `schemas/services.py` | 46-50 | نموذج `ServiceCostCreate` لا يحتوي على `product_id` أو `inventory_item_id` |
| 213 | FSM | `governance.py` | 987-1014 | فوترة الخدمة: `revenue_amount` من المستخدم مباشرة، لا تحتسب من التكاليف + هامش ربح |
| 214 | FSM | `services.py` | 360-406 | التكاليف تُحسب كـ `qty × unit_cost` — لا يوجد هامش ربح (markup) |
| 215 | FSM | - | - | **لا يوجد إشعار تلقائي عند خرق SLA**: فقط علامة `sla_breached` في الاستجابة بدون إشعار |
| 216 | FSM | `services.py` | 763-773 | قائمة الفنيين تُرجع كل المستخدمين النشطين بدون فلترة — لا دور "فني" متخصص |
| 217 | FSM | - | - | **لا يوجد نموذج "فني" مستقل**: لا مهارات، لا مناطق تغطية، لا جدول مواعيد، لا تتبع موقع GPS |
| 218 | FSM | `governance.py` | 234-277 | `scan_and_escalate_sla` يفحص طلبات الاعتماد فقط — ليس لأوامر الخدمة |

### التقارير وذكاء الأعمال (Reports & BI)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 219 | Reports/BI | `reports.py` | 2535-2629 | النسب المالية تعتمد على `account_number LIKE '11%'` لتحديد الأصول المتداولة. إذا لم يلتزم دليل الحسابات بهذا الترقيم، النسب خاطئة |
| 220 | Reports/BI | `reports.py` | 1140-1144 | قائمة الدخل والميزانية تستخدمان `LEFT JOIN ... (je.id IS NULL OR ...)`. هذا يجبر مسحًا كاملًا للجدول |
| 221 | Reports/BI | `reports.py` | 1968-2008 | مقارنة قائمة الدخل: استعلام منفصل لكل فترة. مع 5 فترات = 5 استعلامات كاملة |
| 222 | Reports/BI | `reports.py` | 2328-2355 | `_build_comparison_table` تحتسب التغير لأول فترتين فقط — لا تشمل الفترات الإضافية |
| 223 | Reports/BI | `reports.py` | 1550-1554 | تصنيف IAS 7: كل أصل لا يحتوي على كلمات محددة يُصنف "تشغيلي" — قد يشمل استثمارات طويلة الأجل |

### التكاملات (Integrations)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 224 | Integrations | `payments.py` | - | توقيع webhook المدفوعات اختياري — إذا فشل `verify_webhook`، يتم تجاهل الحدث بصمت |
| 225 | Integrations | - | - | لا يوجد استيراد تلقائي لـ MT940/CSV مع مطابقة المعاملات |
| 226 | Integrations | Swagger | - | نقص `response_model` في بعض الـ endpoints — لا يظهر شكل response في Swagger |
| 227 | Integrations | جميع المحولات | - | اعتماد API Keys/Secrets من `company_settings` مباشرة — إذا تسربت قاعدة البيانات تتسرب جميع المفاتيح |
| 228 | Integrations | جميع المحولات | - | لا يوجد تناوب للمفاتيح (Key Rotation) ولا آلية لإبطال المفاتيح القديمة |
| 229 | Integrations | `email_service.py` | - | البريد الإلكتروني: لا retry على مستوى الإرسال |
| 230 | Integrations | - | - | لا يوجد Circuit Breaker pattern للتكاملات الخارجية |

### محرك الإشعارات (Notifications)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 231 | Notifications | `scheduler.py` | 348-361 | retry للبريد فقط — إشعارات in-app و push الفاشلة لا تُعاد محاولتها |
| 232 | Notifications | `notification_service.py` | 258-272 | `_mark_delivery_failed` تُحدِّث أحدث إشعار للمستخدم — ليس الإشعار المحدد الذي فشل |
| 233 | Notifications | `notification_service.py` | 186 | `_send_in_app` ينفذ `commit()` قبل WebSocket — إذا فشل الإرسال بعد الـ commit لا يمكن استرجاع الإشعار |
| 234 | Notifications | - | - | **لا يوجد رابط "إلغاء الاشتراك" في الإيميلات**: لا `List-Unsubscribe` header. مخالف لـ CAN-SPAM و GDPR |
| 235 | Notifications | - | - | **لا يوجد "إلغاء اشتراك بنقرة واحدة" (One-Click Unsubscribe)** |
| 236 | Notifications | - | - | **لا يوجد HTML Escaping** في أي قالب إيميل. كل المتغيرات تُحقن مباشرة |
| 237 | Notifications | `email_service.py` | 165 | رابط الاعتماد `{approval_url}` بدون توقيع رقمي — لا HMAC للتحقق من عدم التلاعب |
| 238 | Notifications | - | - | إعادة محاولة SMS الفاشلة غير موجودة — retry يغطي البريد فقط |
| 239 | Notifications | `notification_service.py` | 69-75 | **فشل قناة الإشعارات لا يوقف القنوات الأخرى**: إذا فشل البريد، يستمر الإشعار الداخلي والـ Push. صحيح تصميميًا لكن لا يوجد إيقاف شامل إذا كان هناك هجوم |

### محرك البحث (Search)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 239 | Search | `GlobalSearch.jsx` | 20-276 | البحث الشامل (Ctrl+K) يعتمد على قائمة صفحات ثابتة في الكود. الصفحات الجديدة لا تظهر حتى recompile |
| 240 | Search | `parties.py` | - | البحث في العملاء لا يحتوي على فلتر `branch_id` — قد يشمل عملاء من فروع أخرى |
| 241 | Search | - | - | لا بحث موحد عبر الكيانات (Unified Search): لا يمكن البحث في العملاء + الموردين + الفواتير دفعة واحدة |
| 242 | Search | - | - | لا ترتيب حسب الصلة (Relevance Ranking): نتائج ILIKE غير مرتبة حسب الأهمية |
| 243 | Search | - | - | لا بحث في محتوى المستندات المرفوعة (PDF, Word, Excel) |
| 244 | Search | - | - | البحث لا يُسجل في سجل التدقيق |

### سلسلة التوريد (Supply Chain)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 245 | Supply Chain | `purchases.py` | - | مرتجع المشتريات لا يستخدم `CostingService.handle_return` لـ FIFO/LIFO |
| 246 | Supply Chain | `adjustments.py` | 193 | قيمة تسوية الجرد تستخدم `cost_price` من `products` وليس WAC المستودع الفعلي |
| 247 | Supply Chain | `transfers.py` | 103 | حساب WAC في التحويلات يستخدم `float` مباشرة بدل `Decimal` |
| 248 | Supply Chain | `stock_movements.py` | 29, 134 | 4 واجهات مختلفة لتسوية المخزون (`/receipt`, `/delivery`, `/adjustment`, `/adjustments`) بمنطق وصلاحيات مختلفة |
| 249 | Supply Chain | `settings.py` | 74, 77, 130 | **ثلاثة إعدادات مختلفة** للمخزون السلبي (`inventory_negative_stock`, `stock_negative_allowed`, `allow_negative_stock`) لا يقرأها أحد فعليًا |
| 250 | Supply Chain | `stock_movements.py` | 87-90 | `POST /receipt` بدون `FOR UPDATE` — سباق بيانات محتمل عند استلام وشحن نفس المنتج |
| 251 | Supply Chain | `settings.py` | 75 | `inventory_auto_reorder` إعداد بدون كود منفذ فعليًا |

### الخزينة (Treasury)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 252 | Treasury | `reconciliation.py` | 510-520 | `auto_match` جلب القيود بدون قفل `FOR UPDATE` — مطابقة مزدوجة محتملة |
| 253 | Treasury | `forecast_service.py` | 118-133 | القيود الدورية تُؤخذ بقيمتها الكلية `total_amount` — لا تحلل سطور القيد لاستخراج الحسابات النقدية فقط |
| 254 | Treasury | `forecast_service.py` | 72-93 | التنبؤ لا يشمل الشيكات المؤجلة في توقعات السيولة |
| 255 | Treasury | `expenses.py` | 775-777 | اعتماد المصروف: لا `FOR UPDATE` على سجل المصروف نفسه — اعتماد مزدوج نظري |
| 256 | Treasury | `reconciliation.py` | 543-551 | **مقارنة التاريخ في `auto_match` تتعامل مع `str` و `date` معًا**: إذا كان `sl_date` بصيغة غير `'%Y-%m-%d'`، يُسقط التاريخ إلى 999 — تُستبعد الحركات غير القياسية من المطابقة التلقائية بصمت |

### الواجهة الأمامية (Frontend)

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 256 | Frontend | `utils/format.js` | 17 | استخدام `parseFloat` قبل `toLocaleString` يُفقد الدقة للأرقام الكبيرة جدًا (>2^53) |
| 257 | Frontend | عدة صفحات | - | استخدم متباين للتقريب: بعض الصفحات `formatNumber()` وأخرى `.toFixed(2)` مباشرة |
| 258 | Frontend | عدة صفحات | - | قيم عملة ودول صلبة في 3+ أماكن (Register, Onboarding, Branches) بدل API الإعدادات |
| 259 | Frontend | 4 نماذج مالية | - | `exchange_rate: 1.0` صلبة في InvoiceForm, JournalEntryForm, PurchaseInvoiceForm, CurrencyList |
| 260 | Frontend | 99+ استخدام | - | ملاحة `window.location` بدل `useNavigate()` — يفقد حالة التطبيق |
| 261 | Frontend | عدة صفحات | - | عدم Debounce في حقول البحث — طلب API مع كل ضغطة مفتاح |
| 262 | Frontend | ~340 صفحة | - | نمط `fetchData/setLoading` مكرر 1950+ مرة — لا hook مخصص `useApi` |
| 263 | Frontend | عدة صفحات | - | `catch(console.error)` و `catch(() => {})` الصامت في عشرات الصفحات |
| 264 | Frontend | `index.css` | - | نسبة تباين `--text-muted` منخفضة (3.1:1) — لا تتوافق مع WCAG AA (4.5:1) |
| 265 | Frontend | `index.css` | - | CSS 68KB في ملف واحد — يُحمّل على كل صفحة |
| 266 | Frontend | `utils/api.js` | - | Barrel export يُبطل tree-shaking ويُحمّل كل الخدمات معًا |
| 267 | Frontend | `GOSISettings.jsx` | 112 | **حساب نسبة GOSI الإجمالية في الواجهة الأمامية**: `employer_share + occupational_hazard` تُحسب في الفرونت ولا تأتي من API الباك |
| 268 | Frontend | - | - | **لا يوجد أنماط `:focus-visible` مخصصة**: بعض العناصر التفاعلية قد لا تكون مرئية عند التنقل بلوحة المفاتيح (Tab) — فجوة في إمكانية الوصول |
| 269 | Frontend | `apiClient.js` | 194 | **فشل refresh token → `window.location.href = '/login'`**: إعادة توجيه قاسية تفقد حالة التطبيق. الأفضل React Router `navigate()` |
| 270 | Frontend | - | - | **صور أيقونات بدون `alt` نص بديل**: مكون `LazyImage` يدعم `alt` لكن العديد من الاستخدامات تهمله في الأيقونات التزيينية |
| 271 | Frontend | - | - | **لا Code Splitting للمكونات المشتركة**: كل `common/` تُحمّل بشكل متزامن. مكونات ثقيلة مثل DataTable لا تُحمّل كسولاً |
| 272 | Frontend | `main.jsx` | - | **`React.StrictMode` غير مستخدم**: 1950+ استدعاء `useState` بدون تنظيف للمكونات غير المرئية — استهلاك ذاكرة |

### إضافات P2 من التقارير الفردية — الأمن والبيانات

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 272a | Security | `data_import.py` | 280 | **تسريب معلومات هيكلية**: `f"خطأ في السطر {i + 2}"` يكشف أرقام الصفوف الداخلية للمستخدم — موقع إضافي غير مذكور في #163 |
| 272b | Security | `company_settings` | - | **كلمة مرور SMTP مخزنة كنص واضح**: بالإضافة لمفاتيح ZATCA (#162)، كلمة مرور SMTP مخزنة بدون تشفير في `company_settings` |
| 272c | Cache | `role_dashboards.py` | 70-354 | **13 لوحة تحكم حسب الدور تُمسح بالإبطال الشامل**: كاش 13 داشبورد بـ TTL 60-300 ثانية يُمسح كله بعد كل عملية. متوسط بقاء الكاش ~30 ثانية في الشركات النشطة |
| 272d | DMS | `services.py` | 443-498 | **`list_documents` يكشف `download_url`**: قائمة المستندات تعرض رابط التحميل المباشر — يُضخم ثغرة `/uploads` العامة (#54) بتوفير مسارات التحميل |
| 272e | DMS | `services.py` | 739-760 | **الحذف الناعم لا يمتد لإصدارات المستند على القرص**: `document_versions` لديها `ON DELETE CASCADE` على مستوى DB لكن الحذف الناعم لا يُفعّلها. إصدارات المستندات المحذوفة تبقى على القرص |
| 272f | Database | `inventory_transactions` | - | **فهرس مفقود `(product_id, transaction_date)`**: تقارير حركة المنتجات الزمنية تمسح الجدول كاملاً |
| 272g | Database | `payment_vouchers` | - | **فهرس مفقود `(party_type, party_id)`**: استعلام جميع مدفوعات طرف معين يمسح الجدول كاملاً |
| 272h | Database | `purchases.py` | 1870 | **`FOR UPDATE` لكل منتج في حلقة منفصلة عند مرتجع المشتريات**: يجب تجميعها في استعلام واحد بدل N استعلام |
| 272i | Database | - | - | **لا يوجد endpoint لاستعادة النسخ الاحتياطية**: `POST /admin/backup` موجود لكن لا يوجد API للاستعادة |
| 272j | HR | `self_service.py` | 161-196 | **لا يوجد سجل تدقيق لعرض قسائم الرواتب**: الموظف يرى تفاصيل راتبه الكاملة في الخدمة الذاتية لكن لا يُسجل من شاهد القسيمة ومتى |

### إضافات P2 — المبيعات والتصنيع

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 272k | Sales/POS | `pos.py` | 528-538 | **فحص المخزون في POS يفترض اتصال DB**: `FOR UPDATE` يتطلب اتصالاً بقاعدة البيانات. في وضع عدم الاتصال، لا يوجد تحقق محلي بديل |
| 272l | Manufacturing | `core.py` | 1272-1280 | **غياب `acc_map_labor_cost`/`acc_map_mfg_overhead` يترك WIP غير متوازن**: قيد امتصاص العمالة يفترض وجود هذه الحسابات. إذا كانت فارغة، لا يُنشأ قيد — WIP لا يتوازن مع المنتج النهائي |
| 272m | Manufacturing | `core.py` | 909-918 | **لا يوجد منطق لتخطي العمليات الاختيارية في المسار**: نسخ عمليات المسار عند إنشاء أمر الإنتاج يفترض أن جميع العمليات إلزامية (مثل فحص الجودة الاختياري) |
| 272n | Manufacturing | - | - | **MRP لا يأخذ مخزون الأمان (Safety Stock) بالاعتبار**: `reorder_level` موجود في جدول المنتجات لكنه غير مستخدم في حسابات MRP |
| 272o | Manufacturing | - | - | **MRP لا يُنشئ أوامر شراء تلقائيًا**: يقترح `purchase_order` كإجراء لكنه لا يُنشئ PO فعليًا — مجرد اقتراح بدون تنفيذ |
| 272p | Manufacturing | `core.py` | 1765 | **MRP لأمر واحد فقط**: لا يوجد MRP شامل لجميع أوامر الإنتاج المعلقة (Net Requirements Planning). كل أمر يُحسب بمعزل عن الآخرين |
| 272q | Manufacturing | `core.py` | 1316 | **طرح كمية هش**: `existing_qty = SUM(quantity) - order.quantity` — الأفضل قراءة الكمية قبل الإضافة بدل الطرح بعدها |

### إضافات P2 — سلسلة التوريد والخزينة والخدمات الميدانية

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 272r | Supply Chain | `costing_service.py` | 118-121 | **`per_warehouse_wac` يستبعد المستودعات ذات الرصيد السالب**: إذا كان لمستودع رصيد سالب (نظريًا)، يُستبعد من حساب المتوسط العام بدون تحذير |
| 272s | Supply Chain | `costing_service.py` | 320-335 | **`handle_return` يُنشئ طبقة تكلفة جديدة بدل عكس الأصلية**: الطبقة الأصلية المستهلكة تبقى كما هي والمرتجع يُنشئ طبقة جديدة |
| 272t | Supply Chain | `shipments.py` | 345 | **خلط دقة `Decimal`/`float`**: `total_transit_value` يستخدم `Decimal` لكن `source_cost` يأتي كـ `float` من `get_cogs_cost` |
| 272u | Treasury | `reconciliation.py` | 797-871 | **إنهاء المطابقة لا يتحقق من رصيد GL مقابل رصيد الخزينة**: يتحقق أن الرصيد المحسوب = الرصيد المُدخل، لكن لا يتحقق من تطابق `accounts.balance` مع `treasury_accounts.current_balance` |
| 272v | FSM | `contracts.py` | 25-100 | **لا يوجد نموذج عقود خدمة متخصص**: العقود عامة (مبيعات/خدمات/اشتراكات). لا يمكن تعريف جداول صيانة وقائية أو شروط SLA أو قوائم معدات مغطاة على مستوى العقد |
| 272w | FSM | `governance.py` | 971-976 | **فوترة الخدمة تسمح بإيراد صفري مع تكلفة موجبة**: يمكن إغلاق أمر خدمة وترحيله كخسارة صافية بدون تحذير أو بوابة اعتماد. الشرط يتحقق فقط أن أحدهما > 0 |
| 272x | FSM | `crm.py` | 430-439 | **SLA موجود فقط على تذاكر الدعم وليس أوامر الخدمة**: `support_tickets` لديها `sla_hours` لكن `service_requests` لا تحتوي على أي حقول SLA |
| 272y | FSM | `assets.py` | 1588-1606 | **`scheduled_date` في صيانة الأصول خامل**: نموذج البيانات يدعم `maintenance_type='preventive'` و `scheduled_date` لكن لا مجدول يتحقق من المواعيد لتوليد أوامر عمل تلقائيًا |

### إضافات P2 — التقارير والتكاملات والإشعارات

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 272z | Reports/BI | `reports.py` | 1045-1056 | **توزيع الرصيد الافتتاحي في ميزان المراجعة هش**: حسابات الأصول ذات الرصيد الدائن (مثل المخصصات) تُعرض بشكل خاطئ |
| 272aa | Reports/BI | `database.py` | 6528-6531 | **فهارس أداء حرجة مفقودة**: `journal_lines(account_id, journal_entry_id)` و `journal_entries(entry_date, branch_id, status)` — ضرورية لجميع استعلامات التقارير |
| 272ab | Integrations | جميع الراوترز | - | **لا يوجد OpenAPI spec مخصص**: كل التوثيق مولّد تلقائيًا. لا أمثلة، لا وصف تفصيلي لنقاط النهاية |
| 272ac | Notifications | `email_service.py` | 199-212 | **`invoice_template`: `{customer_name}` بدون `html.escape()`**: قالب منفصل عن قوالب الاعتماد المذكورة في #92 — ثغرة حقن HTML إضافية |

---

## 🟡 P3 — منخفض (تحسينات جودة / ملاحظات)

### عام

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 267 | متعدد | - | - | `invoice_type='sale'` خطأ إملائي في `dashboard.py:1046` — النتيجة دائمًا 0 (الصحيح `sales`) |
| 268 | متعدد | - | - | الرابط `overdue=true` في dashboard معطل — لا يوجد فلتر `overdue` في صفحة الفواتير |
| 269 | Dashboard | `dashboard.py` | 1008-1016 | النسب المالية مرتبطة بترقيم صلب (`510%`, `410%`) — إذا استخدم العميل ترقيمًا مختلفًا النسبة = 0 |
| 270 | Dashboard | `dashboard.py` | 35-36, 240 | TTL 60 ثانية مقبول لكن لا مؤشر `_cache_meta` يوضح أن البيانات مخزنة وقديمة |
| 271 | Accounting | `gl_service.py` | 52 | التسامح `> _D2` (0.01) واسع جدًا — فروق 0.009 تمر دون إنذار |
| 272 | Accounting | `invoices.py` | 589-599 | `source="Sales-Invoice"` حالة أحرف مختلطة — باقي المصادر lowercase |
| 273 | Accounting | `accounting.py` | 606 | القيود المسودة تُفحص ضد الفترة المغلقة — منطقيًا لا تؤثر على الأرصدة لكن النظام يمنعها |
| 274 | Audit Trail | `audit.py` | 34-36 | `request.client.host` يُستخدم مباشرة بدون `_get_client_ip` — في بيئات reverse proxy قد يُسجل IP الـ proxy |
| 275 | Audit Trail | - | - | لا يُسجل نوع الجهاز (Device Fingerprinting). لا يُحلل `user_agent` لاستخراج OS/Browser/Device |
| 276 | Audit Trail | - | - | لا تسجيل مصدر الاستدعاء (endpoint/route/HTTP method) في `log_activity` |
| 277 | Audit Trail | - | - | غياب سجل تدقيق لعمليات القراءة (GET requests) |
| 278 | Background Jobs | - | - | لا عرض مرئي لحالة المهام الخلفية — لا صفحة تظهر كم مهمة معلقة، ناجحة، فاشلة |
| 279 | Background Jobs | `main.py` | 118 | `timezone` في جدول الشركات (`Asia/Riyadh`) غير مستخدمة في أي مهمة |
| 280 | Cache | `cache.py` | 30-32 | `MemoryCache` لا ينظف المفاتيح منتهية الصلاحية إلا عند `get()`. المفاتيح الميتة تبقى في الذاكرة |
| 281 | Cache | `auth.py` | 236 | `_token_blacklist_cache` — `set()` في الذاكرة بدون حد حجم |
| 282 | Cache | - | - | لا مراقبة (Monitoring) للكاش: لا metrics لـ hit/miss ratio، لا memory usage، لا eviction rate |
| 283 | CRM | `crm.py` | 551-553 | تحويل الفرصة إلى عرض سعر ينقل المرحلة إلى `proposal` حتى لو كانت الفرصة في مرحلة متقدمة |
| 284 | CRM | `sales_rfq.py` | 122 | `SalesOrder` لا يحتوي على `converted_to_invoice_id` — لا يمكن تتبع أن الطلب تمت فوتترته |
| 285 | CRM | `crm.py` | 1705-1711 | سرعة المبيعات تُحسب كـ `updated_at - created_at` وليس الزمن الفعلي من أول اتصال |
| 286 | CRM | `crm.py` | 1920-1961 | معدل التحويل ليس تحويلاً بينيًا بين المراحل بل نسبة الربح من الإغلاق فقط |
| 287 | CRM | - | - | الأنشطة بدون pagination ولا فلترة حسب النوع أو التاريخ أو الاكتمال |
| 288 | CRM | - | - | لا رابط بين الأنشطة وجهات الاتصال (`crm_contacts`) |
| 289 | CRM | - | - | توقعات المبيعات غير مربوطة بتوقعات التدفق النقدي |
| 290 | CRM | - | - | فحص الحد الائتماني لا يُطبَّق على الفرص عند الإنشاء |
| 291 | Sales/POS | `pos.py` | 423-431 | POS: الخصم العام بعد الضريبة — مخالف لـ ZATCA التي تفرض خصمًا نسبيًا قبل الضريبة |
| 292 | Sales/POS | `pos.py` | 397-487 | العروض/الكوبونات لا تُطبق تلقائيًا على الإجمالي — يجب على الواجهة الأمامية حساب الخصم يدويًا |
| 293 | Sales/POS | `invoices.py` | 807-816 | عكس المخزون عند الإلغاء لا يتحقق من وجود سجل المخزون |
| 294 | Sales/POS | `invoices.py` | 819-843 | البحث عن القيد المحاسبي عند الإلغاء: يستخدم `reference` بدل `source + source_id` |
| 295 | Sales/POS | `pos.py` | 653-676 | معالجة الخصم في POS: إذا لم يوجد حساب خصم مخصص، يُخصم من الإيرادات مباشرة |
| 296 | Sales/POS | - | - | لا صلاحية `price_override` — أي مستخدم `sales.create` يمكنه إدخال أي سعر |
| 297 | Sales/POS | - | - | **ازدواجية جداول المرتجعات**: `sales_returns`/`sales_return_lines` و `pos_returns`/`pos_return_items` — جدولان منفصلان لنفس المفهوم بمخططات مختلفة (P2) |
| 298 | Sales/POS | `pos.py` | 624, 1038 | **POS يستخدم مفاتيح ربط مختلفة عن فواتير المبيعات**: `acc_map_sales` في POS مقابل `acc_map_sales_rev` في invoices — مفتاحان مختلفان لنفس مفهوم الحساب (P2) |
| 299 | DMS | `services.py` | 548-564 | `validate_file_mime_and_signature` تُستدعى قبل حفظ الملف على القرص — الترتيب صحيح لكنه يستهلك ذاكرة |
| 298 | DMS | `sql_safety.py` | 204-214 | دالة `validate_file_path_safety` كود ميت — لا تُستدعى من أي مكان |
| 299 | DMS | - | - | لا Quota تخزين للمستخدمين/الشركات |
| 300 | DMS | - | - | لا فحص طول اسم الملف (>255 حرف قد يسبب مشاكل) |
| 301 | Database | - | - | لا يوجد BRIN indexes للجداول الضخمة (audit_logs, journal_lines) |
| 302 | Database | - | - | لا يوجد Partitioning لـ `audit_logs` و `journal_lines` |
| 303 | HR | `core.py` | 837-838 | إذا فشل استعلام `employee_salary_components`، يتم تجاهل الخطأ بصمت |
| 304 | HR | `wps_compliance.py` | 128 | `mol_establishment_id` قد تكون `'0000000000'` إذا لم تُضبط — سيرفض الملف من وزارة العمل |
| 305 | HR | `wps_compliance.py` | 129 | كود البنك الافتراضي `'RJHI'` (الراجحي) — غير مناسب لجميع الشركات |
| 306 | HR | `self_service.py` | 251 | استحقاق الإجازة في self-service مُرمّز إلى `21` يومًا بدل قراءة `annual_leave_entitlement` من الموظف |
| 307 | HR | `field_encryption.py` | 49-61 | إذا لم يُضبط `FIELD_ENCRYPTION_KEY` ولا `MASTER_SECRET`، الدالة تعيد `None` مما يؤدي لرفض التشفير |
| 308 | HR | `core.py` | 1967-2085 | `generate_single_payslip` لا يتحقق من وجود فترة منشأة مسبقًا لنفس الشهر |
| 309 | HR | `core.py` | 1341-1343 | جلسة الحضور المفتوحة تمنع Check-in جديد لكن لا معالج تلقائي لإغلاق الجلسات المنسية |
| 310 | Expenses | `advanced_workflow.py` | 158-191 | `auto_approve_below_threshold` دالة API يدوية — لا يعمل تلقائيًا. لا مجدول يشغلها |
| 311 | Expenses | `expenses.py` | 471-482 | ربط المصروف بمركز التكلفة (`cost_center_id`) اختياري. يمكن إنشاء مصروف بدون مركز تكلفة |
| 312 | Expenses | - | - | لا سياسات مركبة (compound policies): مثلاً "موظف من قسم المبيعات + نوع مصروف سفر = حد معين" |
| 313 | Manufacturing | `core.py` | 876 | إنشاء رقم أمر الإنتاج `PO-` — البادئة تشبه Purchase Order. الأفضل `WO-` أو `MO-` |
| 314 | Manufacturing | `shopfloor.py` | - | لا يوجد ربط بين ساعات العمل المسجلة في Shop Floor وسجلات حضور الموظفين |
| 315 | FSM | `operations_financial_support.py` | 159-183 | القفل المتفائل (Optimistic Locking) معطل فعليًا — الرسالة لا تُستخدم في كود التحديث |
| 316 | FSM | `contracts.py` | 457+ | فاتورة العقد لا تشير إلى أمر الخدمة إذا كان العقد خدميًا |
| 317 | FSM | `schemas/services.py` | 46-50 | `ServiceCostCreate` لا يحتوي على `markup_pct` أو `selling_price`. يُسجل التكلفة فقط |
| 318 | Reports/BI | `reports.py` | 983-1102 | إشارات ميزان المراجعة معقدة والكود غير نظيف وقد يؤدي لخطأ في حالات نادرة |
| 319 | Reports/BI | `reports.py` | 1105, 1190, 1294 | الكاش لكل عامل وليس مشتركًا — في بيئة متعددة العمال قد تُحسب التقارير 3 مرات |
| 320 | Reports/BI | `reports.py` | 101-103 | تقرير المبيعات: إذا لم يُحدد تواريخ، يفترض آخر 30 يوم — وليس "كل الوقت" |
| 321 | Reports/BI | `reports.py` | 1162-1168 | دالة `rollup` بها خلط أنواع بين `int` و `Decimal` |
| 322 | Reports/BI | - | - | لا تدقيق وصول للتقارير (Report Access Audit). لا يُسجل من شاهد أي تقرير |
| 323 | Integrations | Swagger | - | ReDoc و Swagger UI متاحان في production بدون حماية |
| 324 | Integrations | - | - | لا Health Check موحد لجميع التكاملات |
| 325 | Integrations | - | - | لا Metrics/Logging موحد للتكاملات |
| 326 | Notifications | `notifications.py` | 122 | `POST /notifications/send` لا يحتوي على rate limiter |
| 327 | Notifications | - | - | القوالب صلبة في الكود (hardcoded) — لا محرر قوالب للمستخدم |
| 328 | Notifications | - | - | جدول `email_templates` موجود في قاعدة البيانات لكنه غير مستخدم في أي قالب فعلي |
| 329 | Notifications | - | - | لا Dead Letter Queue منفصل للإشعارات الفاشلة نهائيًا |
| 330 | Search | `GlobalSearch.jsx` | 281-309 | البحث الشامل (Ctrl+K) هو بحث أمامي فقط — لا يبحث في قاعدة البيانات |
| 331 | Search | - | - | لا اقتراحات تلقائية (Autocomplete) أثناء الكتابة |
| 332 | Search | - | - | لا بحث صوتي (Voice Search) |
| 333 | Supply Chain | `stock_movements.py` | 29, 134 | الواجهات القديمة (`/receipt`, `/delivery`) موسومة deprecated لكنها غير معطلة |
| 334 | Supply Chain | `shipments.py` | 362-378 | إضافة كمية الوجهة مكررة — يتحقق من وجود صف المخزون مرتين |
| 335 | Supply Chain | `reconciliation.py` | 491-493 | `tolerance_amount` ثابت 0.01 غير قابل للتعديل من واجهة API |
| 336 | Treasury | `forecast_service.py` | 39-56 | الرصيد الابتدائي للتنبؤ يبدأ من الصفر — لا يستخدم الرصيد الحالي للحسابات البنكية |
| 337 | Treasury | `forecast_service.py` | 80-84 | إزاحة التحصيل (+7 أيام) وإزاحة الدفع (+3 أيام) ثوابت صلبة |
| 338 | Frontend | `DataTable.jsx` | 111 | مكون DataTable لا يدعم التمرير الأفقي أو عرض/إخفاء الأعمدة على الشاشات الصغيرة |
| 339 | Frontend | - | - | لا يوجد استراتيجية للجداول على الموبايل — معظم الجداول تستخدم `<table>` تقليدية |
| 340 | Frontend | `index.css` | - | لا يوجد `print` stylesheet مخصص لطباعة قسائم الرواتب والتقارير |
| 341 | Frontend | - | - | **نمط `fetchData/setLoading` مكرر 1950+ مرة**: لا hook مخصص `useApi` أو `useFetch` |
| 342 | Frontend | - | - | عدم استخدام `<form>` الدلالية مع `onSubmit` في معظم النماذج |
| 343 | Frontend | `main.jsx` | - | `React.StrictMode` غير مستخدم |
| 344 | Frontend | `i18n` | - | مفاتيح i18n تمرر نصوصًا إنجليزية افتراضية — تظهر إنجليزية في الواجهة العربية عند فقدان المفتاح |

### لوحة التحكم (Dashboard) — P3

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 345 | Dashboard | `dashboard.py` | 626-633 | `widget_sales_summary` يستخدم `exchange_rate` قد لا يكون 1 — يضخم أو يقلص المبيعات بالعملات الأجنبية |
| 346 | Dashboard | `dashboard.py` | 806-816 | `widget_pending_tasks` الفواتير غير المدفوعة تستخدم `exchange_rate` — تطبيق غير متسق لأسعار الصرف عبر الداشبورد |
| 347 | Dashboard | `dashboard.py` | 960-977 | `get_available_widgets` يعرض كل الـ widgets لكل المستخدمين — مستخدم بدون صلاحية خزينة يرى widget "الرصيد النقدي" |
| 348 | Dashboard | `dashboard.py` | 189-205 | `low_stock` في `get_dashboard_stats` يُرجع عددًا فقط — لا تفاصيل منتجات ولا إشعار |
| 349 | Dashboard | `dashboard.py` | 189-217 | استعلام المخزون المنخفض بـ `LEFT JOIN (SELECT ... GROUP BY)` — subquery غير محسّن |
| 350 | Dashboard | - | - | لا Lazy Loading للـ widgets — كل بيانات الـ widgets تُجلب معًا عند تحميل الصفحة |

### سجلات التدقيق (Audit Trail) — P3

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 351 | Audit Trail | `audit.py` | 20-21, 86-97 | `critical=True` يُستخدم فقط في 4 endpoints للصلاحيات — غير مستخدم في العمليات المالية |
| 352 | Audit Trail | `services.py` | 209-212 | `request=request` يُمرَّر لـ `log_activity` لكن POST body/JSON لا يُستخرج ولا يُسجل — فقط IP |
| 353 | Audit Trail | - | - | لا كشف "Ghost Employee": نمط إنشاء موظف → كشف راتب → صرف الراتب لا يُكتشف ولا يُربط |

### استراتيجية الكاش (Cache/Redis) — P3

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 354 | Cache | `treasury.py` | 189, 195 | مفتاح `chart_of_accounts:{cid}` يُحذف مرتين متتاليتين — تكرار غير ضار لكنه إهدار |
| 355 | Cache | `cache.py` | 140 | TTL الافتراضي للـ `@cached` هو 300 ثانية — إذا نسي أحد TTL صريحًا، 5 دقائق كثيرة جدًا |

### CRM والمبيعات (CRM & Sales) — P3

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 356 | CRM | `crm.py` | 1708 | `AVG(EXTRACT(DAY FROM (updated_at - created_at)))` يُرجع 0 بدل NULL إذا لم توجد فرص مكتسبة |

### إدارة المستندات (DMS) — P3

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 357 | DMS | - | - | لا ربط CASCADE بين السجلات والمستندات: `related_module + related_id` مرجع نصي بدون FK. حذف فاتورة لا يؤثر على مستنداتها |
| 358 | DMS | `services.py` | 560, 664 | مسار التخزين محسوب وقت الاستيراد (`__file__`). إذا تغير المسار مع ترقية الكود، الملفات القديمة تُفقد |

### المصروفات (Expenses) — P3

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 359 | Expenses | `expenses.py` | 510 | ربط المصروف بالمشروع (`project_id`) أحادي الاتجاه: لا يمكن رؤية مصروفات المشروع من صفحة المشروع |
| 360 | Expenses | `expenses.py` | 514-553 | عند `auto_approve` بدون `treasury_id`، يُستخدم الحساب النقدي الافتراضي — المصروف يمر دون معرفة مصدر النقدية الحقيقي |

### الواجهة الأمامية (Frontend) — P3

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 361 | Frontend | عدة صفحات | - | بعض الصفحات تنسى `finally` وتعجز عن `setLoading(false)` عند الخطأ — يترك spinner للأبد |
| 362 | Frontend | `ErrorBoundary.jsx` | 23 | `handleReload` يستخدم `window.location.reload()` — يفقد حالة التطبيق بالكامل |
| 363 | Frontend | `POSInterface.css` | 1253+ | أنماط طباعة POS الحرارية خارج `@media print` |
| 364 | Frontend | ~340 صفحة | - | `useState` محلي فقط — لا Redux/Zustand/useReducer. الانتقال بين الصفحات يعيد جلب البيانات بالكامل |
| 365 | Frontend | `main.jsx` | - | `React.StrictMode` غير مستخدم — لا تنظيف للمكونات غير المرئية |
| 366 | Frontend | - | - | 1950+ استدعاء `useState` بدون تنظيف — استهلاك ذاكرة تدريجي |

### الخدمات الميدانية (FSM) — P3

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 367 | FSM | `contracts.py` | 383-454 | تجديد العقد (`renew`) لا يُنشئ أوامر خدمة دورية جديدة — يجدد المدة فقط |
| 368 | FSM | `contracts.py` | 457+ | `generate_contract_invoice` يُنشئ فاتورة مبيعات لكن لا يُنشئ أوامر خدمة |
| 369 | FSM | `services.py` | 246-250 | نموذج `ServiceRequestUpdate` يحتوي على `actual_hours` لكن لا `hourly_rate` — لا يمكن احتساب تكلفة العمالة |
| 370 | FSM | `assets.py` | 1577-1612 | صيانة الأصول نظام منفصل عن أوامر الخدمة — نظاما صيانة غير متكاملين |
| 371 | FSM | `manufacturing/core.py` | 2028-2107 | سجلات صيانة معدات التصنيع نظام ثالث منفصل عن أوامر الخدمة والأصول |
| 372 | FSM | `manufacturing/core.py` | 1937-2068 | المعدات لديها `next_maintenance_date` لكن لا مجدول يولّد `service_request` عند حلول التاريخ |

### الموارد البشرية (HR & Payroll) — P3

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 373 | HR | - | - | لا ربط بين سجلات الحضور وتتبع وقت المشاريع (`timetracking`) — نظامان منفصلان تمامًا |
| 374 | HR | - | - | لا يوجد حساب بدل تذكرة سفر سنوية — `ticket_allowance` غير مدعوم |
| 375 | HR | - | - | لا يوجد تكامل مع أجهزة البصمة الخارجية (ZKTeco/Suprema) — لا API لاستيراد سجلات الحضور |
| 376 | HR | - | - | قسائم الرواتب لا تحتوي على ترويسة/شعار الشركة — معلومات محدودة |
| 377 | HR | `wps_compliance.py` | 252 | WPS Preview لا يتطلب صلاحية `hr.pii` — يعرض IBAN مقنع للمستخدمين العاديين |
| 378 | HR | - | - | لا تكامل مع بوابة نطاقات (Nitaqat) الرسمية — البيانات للعرض الداخلي فقط |

### التكاملات (Integrations) — P3

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 379 | Integrations | `stripe_adapter.py` | 42 | `api_base` صلب: `"https://api.stripe.com"` — يفترض أنه قابل للتجاوز لكن لا override |
| 380 | Integrations | `tap_adapter.py` | 29 | `endpoint` صلب: `"https://api.tap.company/v2"` |
| 381 | Integrations | `paytabs_adapter.py` | 31 | `base_url` صلب: `"https://secure.paytabs.sa"` |
| 382 | Integrations | `zatca_adapter.py` | 17-19 | XMLDSig detached signature معتمد على حقن signer callback خارجي — إذا لم يُحقن لا يوجد توقيع XML |
| 383 | Integrations | `eta_adapter.py` | 33 | ETA `base_url` صلب: `"https://api.invoicing.eta.gov.eg"` |
| 384 | Integrations | `csv_feed.py` | - | لا auto-detection لتنسيق CSV — يجب تكوينه يدويًا لكل بنك |

### محرك الإشعارات (Notifications) — P3

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 385 | Notifications | `email_service.py` | 62-71 | `send_bulk` يحتوي على fail/success counters لكن لا يُرجع تفاصيل فشل كل مستخدم |
| 386 | Notifications | `notification_service.py` | 111-143 | تفضيلات المستخدم تُقرأ من قاعدة البيانات لكل إرسال — لا caching |
| 387 | Notifications | - | - | لا إلغاء اشتراك عالمي (global opt-out) — كل نوع حدث يحتاج تعطيل منفصل |
| 388 | Notifications | - | - | SPF/DKIM/DMARC غير موثق/مكوّن — قابلية تسليم البريد في خطر |
| 389 | Notifications | - | - | أرقام الهواتف في سجلات SMS — تُرسل للبوابات الخارجية بدون قناع في السجلات |

### المبيعات ونقاط البيع (Sales & POS) — P3

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 390 | Sales/POS | `vouchers.py` | 374 | مفتاح Idempotency للدفع يعتمد على رقم السند المتسلسل — إذا فشل commit وأعيد الرقم يحدث تعارض |
| 391 | Sales/POS | - | - | `get_acc_id(code)` معرفة محليًا في 3 أماكن — يجب توحيدها |
| 392 | Sales/POS | - | - | لا State Machine صريح لدورة حياة الفاتورة — الانتقالات تُدار ضمنيًا |
| 393 | Sales/POS | - | - | POS session concurrency: لا قفل متفائل على المخزون عبر جلسات POS متعددة |

### محرك البحث (Search) — P3

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 394 | Search | جميع الراوترز | - | لا `LIMIT` صارم على نتائج البحث — بحث عن حرف واحد قد يُرجع آلاف النتائج |
| 395 | Search | `GlobalSearch.jsx` | 20-276 | قائمة الصفحات القابلة للبحث مصفوفة JavaScript صلبة — تحتاج recompile لإضافة صفحات جديدة |

### سلسلة التوريد (Supply Chain) — P3

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 396 | Supply Chain | `dashboard.py` | 202 | منتجات بدون `reorder_level` تُعتبر منخفضة إذا كان المخزون ≤ 5 — الحد 5 ثابت وغير قابل للتكوين |
| 397 | Supply Chain | `webhooks.py` | 110 | `inventory.low_stock` webhook مُعرّف كحدث لكن لا كود يُطلقه فعليًا |
| 398 | Supply Chain | `invoices.py` | 807-816 | إلغاء الفاتورة يعيد المخزون بدون فحص الحدود القصوى — سلوك صحيح للإلغاء لكن جدير بالملاحظة |
| 399 | Supply Chain | `transfers.py` | 23, 240 | واجهتا تحويل مختلفتان: `/transfers` (مفرد) و `/transfer` (متعدد) — ازدواجية لنفس المفهوم |

### الخزينة (Treasury) — P3

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 400 | Treasury | `reconciliation.py` | 472-592 | المطابقة التلقائية (`auto_match`) تشغيل يدوي فقط — لا مجدول يومي/أسبوعي |
| 401 | Treasury | `forecast_service.py` | 159-176 | كل سطور التنبؤ بـ `bank_account_id = None` — لا توزيع للتدفقات حسب الحساب البنكي |
| 402 | Treasury | `checks.py` | 208-234 | فحص تكرار رقم الشيك يقتصر على نفس الفرع — شيك بنفس الرقم في فرعين مختلفين لا يُكتشف |

### التقارير وذكاء الأعمال (Reports & BI) — P3

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 403 | Reports/BI | `reports.py` | 1996-1997 | مقارنة قائمة الدخل: `total_rev += bal` و `total_exp += bal` تجمع كل الحسابات بما فيها الرؤوس — احتمال ازدواجية |
| 404 | Reports/BI | `reports.py` | 1101 | إغلاق ميزان المراجعة: `net_total = (o_dr + p_dr) - (o_cr + p_cr)` صحيح لكن خطأ تقريب محتمل قرب الصفر |
| 405 | Reports/BI | `reports.py` | 1162-1169 | دالة `rollup`: `child_sum = 0` (نوع `int`) ثم إضافة `Decimal` — خلط أنواع غير نظيف |
| 406 | Reports/BI | `reports.py` | 1981-1988 | مقارنة قائمة الدخل: شرط التاريخ في جملة `ON` بدل `WHERE` — صحيح لـ LEFT JOIN لكن fragile |
| 407 | Reports/BI | `reports.py` | 1641-1645 | `closing_cash = opening_cash + net_change` — إذا كان `opening_cash` سالبًا فالنتيجة خاطئة مفاهيميًا |

### الأمن والصلاحيات (Security) — P3

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 408 | Security | `permissions.py` | 199-205 | `SENSITIVE_PERMISSIONS` و `require_sensitive_permission` مُعرّفان لكن غير مستخدمين فعليًا في أي endpoint |
| 409 | Security | - | - | لا Repository Pattern — الوصول للبيانات مباشر في routers عبر `db.execute(text(...))` |
| 410 | Security | - | - | God Routers: `purchases.py` (3700+ سطر) يحتوي PO, PI, Returns, Payments, Suppliers في ملف واحد |
| 411 | Security | - | - | لا DTOs صريحة — `dict(row._mapping)` مستخدم في كل مكان بدل كائنات محددة النوع |
| 412 | Security | - | - | نمط `try/trans.begin()/except/trans.rollback()/finally/conn.close()` مكرر 200+ مرة — يجب Context Manager |
| 413 | Security | `sso_service.py` | - | LDAP bind password في body الطلب — غير مشفر أثناء النقل إذا لم يُستخدم HTTPS |
| 414 | Security | `reports.py` | 3266 | `f"SELECT ... FROM {src['table']}"` — `src['table']` من قاموس ثابت (آمن حاليًا) لكن النمط خطر |

### قاعدة البيانات (Database) — P3

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 415 | Database | - | - | FK `journal_entries.created_by → company_users(id)` بدون ON DELETE |
| 416 | Database | - | - | FK `pos_orders.session_id → pos_sessions(id)` بدون ON DELETE |
| 417 | Database | - | - | FK `accounts.parent_id → accounts(id)` self-referencing بدون حماية ON DELETE |
| 418 | Database | - | - | FK `inventory.product_id → products(id)` بدون ON DELETE |
| 419 | Database | - | - | `payroll_entries.period_id` في DDL بـ ON DELETE CASCADE لكن ORM لا يذكرها — mismatch بين DDL و ORM |

### إضافات P3 من التقارير الفردية

| # | المصدر | الملف | السطر | التفصيل |
|---|--------|-------|-------|---------|
| 419a | Security | `dashboard.py` | 1174-1188 | **نمط حقن اسم Materialized View**: `f"SELECT ... FROM {mv_name}"` — المصدر حاليًا مصفوفة ثابتة (آمن) لكن النمط خطر إذا تغير المصدر. لا `validate_sql_identifier` |
| 419b | Background Jobs | `scheduler.py` + `scheduled_reports.py` | - | **تعارض بين مجدولين للتقارير المجدولة**: `check_scheduled_reports` موجود في `scheduler.py` (نشط) وآخر في `scheduled_reports.py` (غير نشط). تفعيل الثاني يُرسل التقارير مرتين |
| 419c | Background Jobs | `subscription_service.py` | 689-697 | **فوترة الاشتراكات تستخدم `date.today()` (توقيت الخادم)**: التجديدات تحدث حسب توقيت الخادم وليس توقيت الشركة |
| 419d | Background Jobs | `accounting_depth.py` | 576-585 | **حالة `giveup` في outbox الفاتورة الإلكترونية بدون إشعار**: عند وصول صف لحالة `giveup` بعد أقصى محاولات، لا يوجد تنبيه للمسؤولين. المراجعة يدوية فقط عبر API |
| 419e | Cache | إعدادات Redis | - | **لا يوجد `maxmemory-policy` لـ Redis**: إذا امتلأت ذاكرة Redis، قد يرفض جميع عمليات الكتابة. لا `allkeys-lru` أو `volatile-lru` مُعدّ |
| 419f | DMS | - | - | **لا يوجد تشفير على مستوى نظام الملفات**: لا LUKS، لا eCryptfs، لا تشفير أقراص سحابي (AWS EBS) مذكور في إعدادات النشر |
| 419g | HR | `core.py` | 714-774 | **حساب القروض `acc_map_loans_adv` يُستخدم للصرف والاسترداد**: نفس الحساب للطرف المدين عند الصرف والطرف الدائن عند خصم الراتب — صحيح محاسبيًا لكن يسبب ارتباكًا في كشف الحساب |
| 419h | HR | `wps_compliance.py` | 1831 | **أيام الإجازة بدون راتب تُحسب في نهاية الخدمة لكن لا تُخصم**: `calculate_end_of_service` يحسب أيام الإجازة غير المدفوعة لكنها تُعرض فقط ولا تُطبق على المكافأة |
| 419i | HR | `core.py` | 1813 | **حساب سنوات الخدمة تقريبي**: `days/365.25` — المادة 84 من نظام العمل السعودي تحدد الحساب بالسنوات. التقريب مقبول لكن قد يختلف عن التوقع القانوني |
| 419j | Sales/POS | `utils/accounting.py` | 175-198 | **`compute_line_amounts` تحسب الضريبة بعد الخصم دائمًا**: لا يوجد خيار "خصم قبل الضريبة" مقابل "خصم بعد الضريبة" — يحد من المرونة |
| 419k | Sales/POS | `mobile.py` | - | **نظام `sync_queue` للموبايل لا يشمل POS**: المزامنة مصممة لعروض الأسعار والطلبات فقط. POS ليس لديه آلية حل تعارضات |
| 419l | Sales/POS | `zatca_adapter.py` | 24-60 | **بنية UBL XML الحد الأدنى**: المُنشئ يبني هيكلاً بسيطًا قد لا يجتاز جميع متطلبات التحقق في بيئة ZATCA الإنتاجية |
| 419m | Database | - | - | **تجمع الاتصالات عند 50+ مستأجر**: الحد الأقصى ~750 اتصال. لا توصية بـ PgBouncer لـ 100+ مستأجر |
| 419n | Supply Chain | `purchases.py` | 1881 | **رسالة خطأ مرتجع المشتريات بالعربية فقط**: قد لا تُعرض بشكل صحيح في سجلات النظام الإنجليزية |
| 419o | Supply Chain | - | - | **لا يوجد أرشفة لسجل حركات المخزون**: `inventory_transactions` تتراكم بدون تنظيف أو أرشفة للبيانات القديمة |
| 419p | Treasury | `treasury.py` | 704-705 | **تقريب أسعار الصرف في التحويلات بين العملات**: الأرصدة الإجمالية عبر الحسابات بالعملة الموحدة قد تنحرف قليلاً بسبب فروق التقريب |
| 419q | Expenses | `hr/advanced.py` | 1001-1016 | **إرجاع العهدة بدون أثر مالي**: يُسجل فقط `return_date` و `condition_on_return`. لا حساب لفرق القيمة (تلف) ولا قيد شطب. لابتوب بـ 5000 ريال يُرجع تالفًا بدون أي أثر مالي |
| 419r | Reports/BI | `reports.py` | 3598-3685 | **KPI Dashboard: `_gl_balance` لا يراعي نوع الحساب**: يستخدم `jl.debit - jl.credit` فقط — قد يُنتج قيمًا سالبة لحسابات النقد ذات الطبيعة المدينة |
| 419s | Reports/BI | `reports.py` | 1813-1892 | **دفتر الأستاذ العام بدون ترقيم صفحات**: لا `LIMIT` أو pagination لسطور الحركات. سنة كاملة قد تُرجع آلاف السجلات في استجابة واحدة |
| 419t | Search | `duplicate_detection.py` | 55-56 | **كود trigram ميت**: التعليق يقول "trigram if available, else LIKE" لكن `pg_trgm` غير مُفعّل أبدًا — المسار دائمًا LIKE |
| 419u | Integrations | جميع الراوترز | - | **لا `summary` أو `description` على معظم الراوترز**: Swagger/ReDoc يعرض توثيقًا مولّدًا تلقائيًا فقط بدون وصف |
| 419v | Manufacturing | `core.py` | 1830 | **`lead_time_days` غير مستخدم في MRP**: حقل وقت التسليم موجود في المنتج لكنه لا يُستخدم في حساب تاريخ التسليم — لا MRP مرحلي زمنيًا (Time-Phased) |
| 419w | Sales/POS | `pos.py` | 397-487 | **POS لا يطبق العروض/الكوبونات تلقائيًا على الإجمالي**: حقول `coupon_code` و `promotion_id` موجودة في نموذج `PosOrder` لكن كود إنشاء الطلب لا يستخدمها لحساب الخصم — يجب على الواجهة الأمامية حساب الخصم يدويًا وإرساله كـ `discount_amount` (P2) |
| 419x | Treasury | `reconciliation.py` | 797-871 | **اعتماد التسوية (`finalize`) لا يتحقق من رصيد GL الفعلي**: يتحقق فقط أن الرصيد المحسوب = الرصيد المدخل، لكن لا يقارن مع `treasury_accounts.current_balance` ولا مع `accounts.balance` للحساب الموازي — قد يُعتمد توازن شكلي مع اختلاف فعلي بين الخزينة و GL (P2) |
| 419y | Treasury | `forecast_service.py` | 118-133 | **القيود الدورية تُؤخذ بقيمتها الكلية في التنبؤ النقدي**: `total_amount` لكل قالب دوري يُستخدم مباشرة دون تحليل سطور القيد لاستخراج الحسابات النقدية فقط — التدفق المُتنبأ به منحاز ولا يعكس الحركة النقدية الفعلية للقيد (P2) |
| 419z | Sales/POS | `zatca_adapter.py` + `accounting_depth.py:einvoice_submit` + relay | - | **[FIXED in T1.5a — 2026-05-01]** Offline mode → outbox: `einvoice_submit` الآن يكتشف `result.response.offline` ويُدخله في `einvoice_outbox` كحالة `pending` مع تأخير 5 دقائق. relay loop أيضًا يرفض اعتبار `submitted+offline` نجاحًا (يبقى pending ويزيد attempts للـ exponential backoff). يضمن عدم فقدان الفواتير المُولّدة في وضع offline. |
| 419aa | Supply Chain | `costing_service.py` | 320-335 | **`handle_return` يُنشئ طبقة تكلفة جديدة بدل عكس الطبقة الأصلية**: المرتجع يُضاف كـ layer جديد بتكلفة الوحدة الأصلية، والطبقة الأصلية المستهلكة تبقى مستهلكة — قد يُربك تتبع FIFO/LIFO على المدى الطويل (P3) |
| 419ab | Supply Chain | `shipments.py` | 358-367 | **فحص وجود صف المخزون مكرر**: عند إضافة كمية الوجهة في تأكيد الشحنة، يتم التحقق من وجود الصف مرتين (سطر 358 و 367) — أحدهما زائد ولا يضيف قيمة لكنه قد يُخفي حالة سباق إذا أُدخل صف بين الفحصين (P3) |
| 419ac | Manufacturing | `core.py` | 1122-1127 | **استثناء صامت يستر فشل أمر التصنيع**: `except Exception: trans.rollback() ... raise HTTPException(400)` يعيد رسالة عامة 400 دون تسجيل التفاصيل في Sentry وبدون إبلاغ السبب الحقيقي للمستخدم (P2) |
| 419ad | Treasury | `expenses.py` | 513-553 | **مساران مختلفان لإنشاء المصروف**: `expenses.py` يُنشئ القيد فقط بعد الاعتماد، بينما `treasury.py:448-579` يُنشئ القيد فورًا — سلوك محاسبي متناقض حسب نقطة الإدخال (P1) |
| 419ae | Treasury | `expenses.py` | 775-777 | **اعتماد المصروف بدون قفل `FOR UPDATE` على سجل المصروف نفسه**: يقفل رصيد الخزينة لكن لا يقفل صف المصروف — اعتماد متزامن في جلستين قد يخصم من الخزينة مرتين نظريًا (P2) |
| 419af | Treasury | `expenses.py` | 835-874 | **حذف المصروف بعد الاعتماد غير ممكن وبدون واجهة قيد عكسي**: المصروفات المعتمدة لا يمكن حذفها (صحيح محاسبيًا) لكن لا يوجد API لإصدار قيد عكسي — التصحيح يتطلب SQL يدوي (P2) |
| 419ag | System | متعدد | - | **التقييم العام للنظام (Gartner-equivalent) قبل الإصلاح**: 51/100 — تصنيف "Visionary" (تغطية 21 وحدة لكن جودة تنفيذية متفاوتة). توزيع الأبعاد: الوظائف 72/100، الأمان 38/100، الأداء 42/100، الموثوقية 35/100، UX 55/100، التكاملات 58/100. **يحتاج 90 يومًا من الإصلاحات للوصول إلى 84/100 (Leader)** — مرجع: `SYSTEM_EVALUATION_AND_BENCHMARK.md` |
| 419ah | System | متعدد | - | **درجات الوحدات الفردية (قبل الإصلاح)**: التقارير 69، الخزينة 65، المحاسبة 65، CRM 58، سلسلة التوريد 68، التكاملات 58، قاعدة البيانات 55، HR 55، Dashboard 48، المصروفات 53، الإشعارات 54، DMS 42، Sales/POS 58، التصنيع 38، FSM 38، البحث 37، المهام الخلفية 33، الكاش 43، Frontend 55، الأمن 38، التدقيق 32 — أضعف 4 وحدات: التدقيق، المهام الخلفية، البحث، الأمن (مرجع: `SYSTEM_EVALUATION_AND_BENCHMARK.md` 8.5) |

---

## 📊 إحصائيات عامة

| الأولوية | العدد | النسبة |
|----------|-------|--------|
| 🔴 P0 (حرج) | 5 | 1.0% | (8 في الأصل — بنود #4، #5، #7b أُبطلت بعد التحقق العملي؛ #1، #2 أُغلقت في T1.2) |
| 🔴 P1 (عالي) | 120 | 23.1% |
| 🟠 P2 (متوسط) | 215 | 41.4% |
| 🟡 P3 (منخفض) | 176 | 33.9% |
| ℹ️ ملاحظات تقييمية (System) | 2 | — |
| **المجموع** | **519** | **100%** |

### توزيع المخاطر حسب الوحدة

| الوحدة | P0 | P1 | P2 | P3 | المجموع |
|--------|----|----|----|----|----|
| المحاسبة (Accounting) | 0 | 8 | 9 | 3 | 20 |
| سجلات التدقيق (Audit Trail) | 0 | 11 | 10 | 7 | 28 |
| المهام الخلفية (Background Jobs) | 0 | 6 | 8 | 2 | 16 |
| استراتيجية الكاش (Cache/Redis) | 0 | 5 | 5 | 5 | 15 |
| CRM والمبيعات (CRM & Sales) | 0 | 8 | 9 | 8 | 25 |
| لوحة التحكم (Dashboard) | 0 | 7 | 9 | 8 | 24 |
| قاعدة البيانات (Database) | 0 | 5 | 11 | 7 | 23 |
| إدارة المستندات (DMS) | 0 | 8 | 11 | 6 | 25 |
| المصروفات (Expenses) | 0 | 6 | 9 | 5 | 20 |
| الواجهة الأمامية (Frontend) | 0 | 4 | 17 | 13 | 34 |
| الخدمات الميدانية (FSM) | 0 | 6 | 8 | 9 | 23 |
| الموارد البشرية (HR & Payroll) | 0 | 4 | 12 | 13 | 29 |
| التكاملات (Integrations) | 0 | 5 | 7 | 10 | 22 |
| التصنيع (Manufacturing) | 2 | 3 | 12 | 2 | 19 |
| الإشعارات (Notifications) | 0 | 4 | 9 | 9 | 22 |
| التقارير وذكاء الأعمال (Reports & BI) | 0 | 3 | 5 | 11 | 19 |
| المبيعات ونقاط البيع (Sales & POS) | 2 | 4 | 6 | 10 | 22 |
| محرك البحث (Search) | 0 | 4 | 6 | 5 | 15 |
| الأمن والصلاحيات (Security) | 0 | 8 | 11 | 7 | 26 |
| سلسلة التوريد (Supply Chain) | 0 | 4 | 7 | 7 | 18 |
| الخزينة (Treasury) | 3 | 5 | 5 | 5 | 18 |

---

> **الخلاصة العامة**: النظام يعاني من 5 مشكلات حرجة (P0) تمنع تشغيل بعض أجزائه بشكل صحيح (بعد إبطال 3 بنود ثبت تقنيًا أنها false-positives وإغلاق بندين في T1.2). أكبر فجوة هي P1 (120 مشكلة) و P2 (215 مشكلة) التي تتضمن تناقضات محاسبية خطيرة، ثغرات أمنية، وأنظمة معطلة فعليًا. إجمالي **519 بندًا** بين حرج وعالٍ ومتوسط ومنخفض ومُلاحَظات تقييمية — يغطي جميع الوحدات الـ 21 إضافةً إلى التقييم الكلي للنظام (`SYSTEM_EVALUATION_AND_BENCHMARK.md`).
>
> **الدرجة الإجمالية الحالية للنظام**: 51/100 (Gartner-equivalent: "Visionary"). الفجوة بين "التغطية الوظيفية" (85/100) و"الجودة التنفيذية" (38/100) هي التحدي الأكبر. الهدف بعد الإصلاح: 84/100 (Leader) — منافس مباشر لـ Microsoft Dynamics 365 ومتفوّق على Odoo Enterprise و ERPNext و Zoho ERP.
>
> الأولوية القصوى للإصلاح: (1) توحيد مصادر بيانات المبيعات بين Dashboard والتقارير، (2) بناء نظام Smart Alerts وتنبيهات، (3) تفعيل ZATCA Phase 2 clearance + outbox للوضع غير المتصل، (4) إصلاح أخطاء ON CONFLICT في التصنيع و POS، (5) إغلاق الثغرات الأمنية في `/uploads` وصلاحيات الإلغاء/المرتجعات/الإشعارات الدائنة، (6) تفعيل التشفير على البيانات الحساسة (رواتب، IBAN، مفاتيح ZATCA)، (7) تفعيل `pg_trgm` وفهرسة النصوص، (8) توحيد مساري المصروفات (`expenses.py` vs `treasury.py`)، (9) إلغاء ازدواجية `treasury_accounts.current_balance` ↔ `accounts.balance` (Treasury R1/R2)، (10) تطبيق العروض/الكوبونات تلقائيًا في POS backend.
