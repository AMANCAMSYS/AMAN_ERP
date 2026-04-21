<div dir="rtl">

# تقرير المقارنة بالأنظمة العالمية + خطة الإصلاح التنفيذية
## World-Class ERP Benchmark Audit & Remediation Tasks

- **الإصدار:** 1.0
- **التاريخ:** 21 أبريل 2026
- **المُدقِّق:** Senior ERP Systems Architect / Financial Systems Auditor (20+ years)
- **المراجع الأساسية:** [PROJECT_DESIGN_REQUIREMENTS.md](PROJECT_DESIGN_REQUIREMENTS.md) · [20-4-2026-audit.md](20-4-2026-audit.md)

---

## 1. الحكم التنفيذي

نظام **أمان** متكامل النطاق (56 راوتر، ~872 endpoint، 178+ جدول) ويقترب من **Odoo Enterprise** و **Dynamics 365 BC** في الاتساع، ويتفوّق إقليمياً (ZATCA Phase 2، WPS، الزكاة، RTL كامل). لكن **صلابة المحاسبة على مستوى قاعدة البيانات** و **عزل المستأجرين** و **دقة الأرقام المالية** لم تبلغ بعد مستوى الأنظمة المُدقَّقة (SAP S/4HANA، Oracle NetSuite).

| البُعد | أمان | المعيار العالمي | الحكم |
|---|---|---|---|
| اتساع الوحدات | ممتاز | مطابق NetSuite/D365 | ✅ |
| التوافق الإقليمي | متميز | ميزة تنافسية | ✅ |
| Double-entry enforcement عند DB | غائب | SAP/Oracle: Triggers | ❌ حرج |
| Idempotency على DB | غائب | UNIQUE + retry | ❌ حرج |
| Multi-tenant isolation | قابل للاختراق | tenant من JWT فقط | ❌ حرج |
| دقة Decimal vs float | خلل موجود | Decimal/NUMERIC | ❌ حرج |
| Immutability للقيود | غير محمية | BKPF-style | ❌ عالٍ |
| Period-close مركزي | متفرّق | مسار واحد | ❌ عالٍ |
| IFRS 15/16 | جزئي (16 مُنفّذ) | NetSuite ARM/SAP RAR | ⚠️ |
| Scheduler خارج العملية | داخل العملية | Celery/RQ/Queue | ⚠️ |

**المستوى الحالي:** Late Beta / GA محدود.
**بعد إغلاق الحرج:** GA Production-grade.
**بعد Multi-Book + Dimensions + SDK:** Regional NetSuite Challenger.

---

## 2. مقارنة بالأنظمة العالمية (ملخّص)

### 2.1 SAP S/4HANA
- ينقص أمان: Universal Journal، Parallel Ledgers (Local GAAP + IFRS)، Material Ledger، Document Principle/Immutability على DB.
- أمان يتقدّم: ZATCA out-of-the-box، RTL أصلي.

### 2.2 Oracle NetSuite
- ينقص أمان: SuiteTax متعدد الولايات، Revenue Management (ARM)، Multi-Book، SuiteScript SDK.
- أمان يتقدّم: IFRS 16 مُنفّذ، Subscription/MRR/ARR أولي، ZATCA.

### 2.3 Microsoft Dynamics 365 BC / F&O
- ينقص أمان: Analytical Dimensions (8+)، Posting Groups الموحّدة، Power Platform.
- أمان يتقدّم: Role-based dashboards، Approval workflow.

### 2.4 Odoo Enterprise (المنافس المباشر)
- ينقص أمان: App Ecosystem، Studio، أقوى enforcement في ORM.
- أمان يتقدّم: ZATCA/WPS، اللغة والاتجاه، Industry templates.

### 2.5 Sage Intacct / X3
- ينقص أمان: Dimensional accounting، Multi-entity consolidation.

---

## 3. فجوات محاسبية معيارية

| المعيار | الموقف | المطلوب |
|---|---|---|
| IFRS 9 (ECL) | غير موجود | مخصصات ديون متوقعة على AR aging |
| IFRS 15 / ASC 606 | scaffold | Performance Obligations, Variable Consideration |
| IFRS 16 (Leases) | **مُنفّذ** | إكمال إعادة التقييم والإنهاء المبكر |
| IAS 2 (NRV) | غائب | Job دوري لـ NRV write-down |
| IAS 21 (FX) | جزئي | exchange_rates immutable + worker |
| IAS 36 (Impairment) | غائب | دورة اختبار هبوط للأصول |
| IFRS 8 (Segments) | غائب | بُعد segment على كل سطر |
| SOX SoD | غير صريح | Matrix صلاحيات متعارضة |
| E-Invoicing Egypt (ETA) | غائب | إلزام قريب |
| E-Invoicing UAE 2026 | غائب | إلزام قادم |

---

## 4. نقاط القوة

1. ZATCA Phase 2 مُنفّذ فعلياً.
2. WPS SIF + KSA bank formats.
3. 11 role dashboards + 57 تقرير + 8 MViews.
4. i18n كامل RTL/LTR.
5. Layer-based Costing (FIFO/LIFO) مع `policy_version` lock.
6. PDR + RUNBOOK + Deep Audit Report.
7. IFRS 16 Lease مُنفّذ في `assets.py`.
8. Subscription + MRR/ARR.

---

## 5. خطة الإصلاح على شكل مهام (Tasks)

> الرمز `[C]` = Critical (قبل أي إنتاج جديد) · `[H]` = High · `[M]` = Medium · `[L]` = Low
> كل مهمة لها: **الملف/الموقع**، **الفحص قبل**، **التنفيذ**، **الفحص بعد**.

### المرحلة 1 — إيقاف النزيف (Week 1)

#### TASK-001 [C] — ربط Decimal بدلاً من float في GL
- **الموقع:** [backend/services/gl_service.py](../backend/services/gl_service.py) أسطر 138, 174–189
- **المشكلة:** `float(_dec(...))` قبل إرسال القيم إلى SQL → فقدان دقة.
- **التنفيذ:** إزالة `float(...)` حول `debit_base`, `credit_base`, `input_debit`, `input_credit`, `line_amount_currency`, `rate` وتمرير `Decimal` مباشرةً (psycopg2 يتعامل معه).
- **التحقق بعد:** `python -c "from backend.services import gl_service; ..."` + اختبار قيد متوازن.

#### TASK-002 [C] — UNIQUE constraints للـ Idempotency
- **الموقع:** Alembic migration جديدة.
- **التنفيذ:**
  ```sql
  ALTER TABLE journal_entries
    ADD CONSTRAINT uq_je_idempotency UNIQUE (idempotency_key);
  CREATE UNIQUE INDEX uq_je_source ON journal_entries (source, source_id, entry_date)
    WHERE source <> 'Manual' AND source_id IS NOT NULL;
  ```
  + `try/except IntegrityError` في `gl_service.create_journal_entry` → إعادة القراءة.

#### TASK-003 [C] — CHECK constraints على `journal_lines`
- **التنفيذ:**
  ```sql
  ALTER TABLE journal_lines
    ADD CONSTRAINT chk_jl_nonneg  CHECK (debit >= 0 AND credit >= 0),
    ADD CONSTRAINT chk_jl_exclusive CHECK (NOT (debit > 0 AND credit > 0)),
    ADD CONSTRAINT chk_jl_nonzero CHECK (debit + credit > 0);
  ```

#### TASK-004 [C] — Deferred balanced-trigger (Σ debit = Σ credit)
- **التنفيذ:** Constraint trigger on `journal_lines` يتحقق بعد commit.

#### TASK-005 [C] — Immutability trigger للقيود المرحّلة
- **التنفيذ:** `BEFORE UPDATE/DELETE` على `journal_entries`/`journal_lines` يرفض أي تغيير عند `status='posted'` (ما عدا `posted→void`).

#### TASK-006 [C] — Closed-period guard على DB
- **التنفيذ:** `BEFORE INSERT` على `journal_entries` يرفض `entry_date` داخل فترة مغلقة.

#### TASK-007 [C] — partial UNIQUE على `is_base`
- **التنفيذ:**
  ```sql
  CREATE UNIQUE INDEX uq_currency_one_base ON currencies ((TRUE)) WHERE is_base = TRUE;
  ```

#### TASK-008 [C] — إزالة `?company_id=` override
- **الملفات:** [backend/routers/roles.py](../backend/routers/roles.py) (أسطر 484, 555, 592, 627, 677, 740) · [backend/routers/audit.py](../backend/routers/audit.py) (43, 192, 220).
- **التنفيذ:** استخراج `company_id` من `current_user` فقط. رفض أي query param يحمل هذا الاسم أو 403 عند الاختلاف.

#### TASK-009 [C] — منع كتابة `role` من HR
- **الملف:** [backend/routers/hr/core.py](../backend/routers/hr/core.py) سطر 452–454.
- **التنفيذ:** إزالة أي إسناد لـ `company_users.role` من هذا الـ endpoint. نقله إلى `/api/roles` المحمي بـ `admin.roles` + rank check.

#### TASK-010 [C] — كلمة مرور عشوائية لـ tenant DB role
- **الملف:** [backend/database.py](../backend/database.py) سطر 164–167.
- **التنفيذ:** `secrets.token_urlsafe(32)` + تخزين مشفّر في `system_companies.db_password_enc`.

#### TASK-011 [C] — إصلاح `save_opening_balances` (NameError)
- **الملف:** [backend/routers/finance/accounting.py](../backend/routers/finance/accounting.py) ~سطر 2012.
- **التنفيذ:** تعريف Pydantic `OpeningBalancesPayload`، تمريره عبر `Body(...)`، التحقق من `Σ dr = Σ cr`، الترحيل عبر `gl_service`.

#### TASK-012 [C] — Refresh token يقرأ الصلاحيات من DB
- **الملف:** [backend/routers/auth.py](../backend/routers/auth.py) سطر 1203–1220.
- **التنفيذ:** إعادة قراءة `role`, `permissions`, `enabled_modules`, `is_active` من DB على كل refresh.

#### TASK-013 [C] — إصلاح SSO broken import (`_set_auth_cookies`)
- **الملف:** [backend/routers/sso.py](../backend/routers/sso.py) سطر 236.
- **التنفيذ:** استبدال بـ authorization-code exchange (`/sso/exchange`) يُعيد tokens للـ SPA.

#### TASK-014 [C] — إصلاح forgot-password tenant-picking
- **الملف:** [backend/routers/auth.py](../backend/routers/auth.py) سطر 1289–1312.
- **التنفيذ:** طلب `company_code`؛ lookup واحد؛ constant-time response.

---

### المرحلة 2 — قفل المحاسبة (Week 2)

- **TASK-015 [H]** — توجيه كل الترحيلات عبر `gl_service` وحذف raw INSERT. **تمت إضافة CI guard:** [scripts/check_gl_posting_discipline.py](../scripts/check_gl_posting_discipline.py). **المسح أظهر 30 نقطة انتهاك** في الملفات التالية يجب تحويلها تباعًا:
    - [backend/routers/system_completion.py](../backend/routers/system_completion.py) — 3 sites
    - [backend/routers/delivery_orders.py](../backend/routers/delivery_orders.py) — 6 sites
    - [backend/routers/manufacturing/core.py](../backend/routers/manufacturing/core.py) — 8 sites
    - [backend/routers/sales/sales_improvements.py](../backend/routers/sales/sales_improvements.py) — 3 sites
    - [backend/routers/sales/credit_notes.py](../backend/routers/sales/credit_notes.py) — 4 sites
    - [backend/routers/sales/vouchers.py](../backend/routers/sales/vouchers.py) — 4 sites
    - [backend/routers/sales/returns.py](../backend/routers/sales/returns.py) — 2 sites
    - CI guard يمنع الإضافات الجديدة حتى يتم التحويل الكامل.
- **TASK-016 [H]** — تحويل `ON DELETE CASCADE` → `RESTRICT` على FKs لـ `journal_lines`, `accounts`, `fiscal_periods`.
- **TASK-017 [H]** — `journal_entries.status` CHECK ∈ {draft, posted, void, reversed}.
- **TASK-018 [H]** — جدول `exchange_rates(currency_id, effective_date, rate)` مع `UNIQUE (currency_id, effective_date)` — بديل عن تعديل `currencies.current_rate` في مكانه.
- **TASK-019 [H]** — `fiscal_periods` exclusion constraint ضد التداخل (`btree_gist`).
- **TASK-020 [H]** — `version INTEGER` على الجداول التي يستخدمها `utils/optimistic_lock.py`.
- **TASK-021 [H]** — `audit_log` fail-closed على العمليات الحرجة (`critical=True`).

---

### المرحلة 3 — توحيد المسارات (Week 3)

- **TASK-022 [H]** — حذف [intercompany.py](../backend/routers/finance/intercompany.py) v1؛ إعادة تسمية v2 إلى `intercompany.py`. Alembic migration لترحيل السجلات.
- **TASK-023 [H]** — توحيد شجرة النماذج: حذف `backend/models/core_accounting.py` و `backend/models/domains/finance.py`؛ الإبقاء على `backend/models/domain_models/`.
- **TASK-024 [H]** — Alembic baseline موحّد مولَّد من الـ metadata الحالية؛ تعطيل `create_all()` عند bootstrap.
- **TASK-025 [H]** — FIFO/LIFO consumption داخل `SELECT ... FOR UPDATE` على `cost_layers`.
- **TASK-026 [H]** — حساب "Inventory in Transit" للتحويلات بين المستودعات.
- **TASK-027 [H]** — توحيد حساب VAT مع `compute_invoice_totals` (منع override اليدوي).

---

### المرحلة 4 — Hardening (Week 4)

- **TASK-028 [H]** ✅ — فصل APScheduler إلى Worker منفصل. تم عبر `SCHEDULER_MODE` flag في [config.py](../backend/config.py) + [worker.py](../backend/worker.py) + خدمة `worker` في [docker-compose.prod.yml](../docker-compose.prod.yml). الإنتاج يشغّل `SCHEDULER_MODE=dedicated` والـ worker في replica واحد.
- **TASK-029 [H]** ✅ — إصلاح XSS في [Sales/InvoicePrintModal.jsx](../frontend/src/pages/Sales/InvoicePrintModal.jsx) و [HR/Payslips.jsx](../frontend/src/pages/HR/Payslips.jsx) و [Taxes/WithholdingTax.jsx](../frontend/src/pages/Taxes/WithholdingTax.jsx): استبدال `document.write`/template-literals بـ DOM APIs (`createElement` + `textContent` + `setAttribute`).
- **TASK-030 [H]** ✅ — refresh token في HttpOnly Secure SameSite=Strict cookie + CSRF double-submit. ملفات جديدة: [utils/auth_cookies.py](../backend/utils/auth_cookies.py) و [utils/csrf_middleware.py](../backend/utils/csrf_middleware.py)؛ `CSRF_ENFORCEMENT` flag (`permissive` افتراضياً). [apiClient.js](../frontend/src/services/apiClient.js) يقرأ الـ CSRF cookie ويُرسله في `X-CSRF-Token`.
- **TASK-031 [H]** ✅ — composite index `(source, source_id, entry_date)` على `journal_entries` (مطابق لاستعلام duplicate-guard في `gl_service`). إضافة canonical SQL في [database.py](../backend/database.py) + migration [0011_je_source_composite_index.py](../backend/alembic/versions/0011_je_source_composite_index.py) باستخدام `CREATE INDEX CONCURRENTLY`. ملاحظة: `company_id` غير قابل للتطبيق في architecture DB-per-tenant.
- **TASK-032 [H]** ✅ — Property-based tests باستخدام `hypothesis` في [test_46_gl_balance_property.py](../backend/tests/test_46_gl_balance_property.py). استخراج `validate_je_lines()` كدالة نقية في [gl_service.py](../backend/services/gl_service.py). 7 tests تُؤكد الـ invariants (الميزان، رفض السالب، رفض المختلط، …).
- **TASK-033 [H]** ✅ — إزالة `detect_sql_injection` و `SQL_PATTERNS` من [security_middleware.py](../backend/utils/security_middleware.py). CI lint جديد [check_sql_parameterization.py](../scripts/check_sql_parameterization.py) مع baseline [sql_lint_baseline.txt](../scripts/sql_lint_baseline.txt) (349 موقع موروث). الـ XSS detection متبقٍ.

---

### المرحلة 5 — عمق محاسبي عالمي (شهر 2+)

- **TASK-034 [M]** — **Multi-Book Accounting:** دفاتر متوازية (Local GAAP + IFRS) — عمود `ledger_id` على `journal_entries`.
- **TASK-035 [M]** — **Dimensional Accounting:** 6–8 analytical dimensions على كل JL (segment, project, product_line, customer_group, ...).
- **TASK-036 [M]** — **IFRS 15 / ASC 606** كامل: Performance Obligations، Contract Modifications، Variable Consideration، SSP.
- **TASK-037 [M]** — **IFRS 9 ECL:** مخصصات ديون متوقعة على AR aging buckets.
- **TASK-038 [M]** — **IAS 2 NRV:** job دوري لتخفيض المخزون إلى أقل التكلفة والقيمة القابلة للتحقق.
- **TASK-039 [M]** — **IAS 36 Impairment:** دورة اختبار هبوط CGU.
- **TASK-040 [M]** — **E-Invoicing Egypt (ETA)** + **UAE E-Invoicing 2026**.
- **TASK-041 [M]** — **SDK/Plugin System:** hooks على أحداث GL/Sales/Purchase + Settings UI.
- **TASK-042 [M]** — **Event Bus** داخلي (domain events) بدلاً من الاستدعاء المتزامن بين الوحدات.
- **TASK-043 [L]** — تنظيف `.opencode`, `.venv-audit`, `__pycache__`, `fix_db.py`, `test_*.py` من جذر المشروع.
- **TASK-044 [L]** — إتمام i18n (`hardcoded_strings.json`, `keys_to_translate.json`).

---

## 6. معايير القبول (Verification)

- [ ] كل tenant DB: `SELECT journal_entry_id FROM journal_lines GROUP BY journal_entry_id HAVING ROUND(SUM(debit)-SUM(credit),2) <> 0` = 0 rows.
- [ ] `SELECT 1 FROM journal_entries WHERE status='posted' AND entry_date < (SELECT MAX(end_date) FROM fiscal_periods WHERE is_closed=true)` = 0.
- [ ] Pen-test: `?company_id=` → 403 على كل endpoint.
- [ ] Pen-test: HR update `{role:"admin"}` → 403.
- [ ] SSO round-trip بدون 500.
- [ ] tenant DB password ≠ admin password.
- [ ] Trial Balance من API = Σ line postings = Assets = Liabilities + Equity.
- [ ] `pg_stat_user_indexes` يُظهر استخدام composite indexes.

---

**نهاية التقرير — 21 أبريل 2026**

</div>
