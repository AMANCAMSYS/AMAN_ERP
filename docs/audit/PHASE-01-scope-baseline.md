# PHASE-01 · النطاق والأساس المرجعي (Scope & Baseline)

> **التاريخ:** 22 أبريل 2026
> **الحالة:** مكتملة ✅
> **المرجع:** [AUDIT_PLAN.md](./AUDIT_PLAN.md) § المرحلة 1
> **الغرض:** توثيق حدود النظام "كما هو" والتقاط كل الأرقام المرجعية قبل بدء الفحص

---

## 1 · ملخّص تنفيذي

نظام **AMAN ERP** نظام متعدد المستأجرين (multi-tenant) قائم على FastAPI + React + PostgreSQL + Redis، بنيته الحالية:

| البعد | القيمة |
|---|---|
| Backend routers | **85 ملف** (بعد تقسيم finance/hr/inventory/manufacturing/sales إلى وحدات فرعية) |
| Endpoints (حسّاب `@router.*`) | **899** |
| Services | 22 ملف |
| Schemas (Pydantic) | 46 ملف |
| Models (SQLAlchemy/raw) | 56 ملف |
| Integrations | 26 ملف (einvoicing + bank_feeds + payments + shipping + sms) |
| Frontend pages | **341 صفحة** jsx |
| Frontend components | 36 مكوّن مشترك |
| Mobile (React Native) | 24 ملف |
| Alembic revisions | 13 revision · head = `0012_phase5_world_comparison` |
| Legacy migrations/ | 5 ملفات (hotfix-style) |

> **📌 ملاحظة حرجة (P0):** عُثر على **انحرافات Alembic بين قواعد الشركات** — راجع § 5.1.

---

## 2 · جرد الوحدات (Routers × أقسام SYSTEM_COMPARISON)

### 2.1 تحت `backend/routers/finance/` (20 ملف)

| Router | قسم المقارنة | Criticality | ملاحظة |
|---|---|---|---|
| `accounting.py`, `accounting_depth.py` | 2.1 المحاسبة | Critical | قيد اليومية + IFRS |
| `advanced_workflow.py` | 2.16 Workflows | Critical | SLA + Escalation |
| `assets.py` | 2.9 الأصول | Critical | استهلاك + revaluation |
| `bank_feeds.py` | 2.15 التكاملات | High | MT940 |
| `budgets.py` | 2.1 المحاسبة | High | Budget vs Actual |
| `cashflow.py` | 2.2 الخزينة | High | Forecasting |
| `checks.py`, `notes.py` | 2.2 الخزينة | Critical 🏆 | MENA checks |
| `cost_centers.py`, `costing_policies.py` | 2.1/2.5 | High | Cost Layer Policy |
| `currencies.py` | 2.1 المحاسبة | High | FX Reval |
| `expenses.py` | 2.1 المحاسبة | High | سياسات المصروفات |
| `intercompany_v2.py` | 2.1 المحاسبة | Critical | دمج + مطابقة |
| `payments.py` | 2.2 الخزينة | Critical | Stripe/Tap/PayTabs |
| `reconciliation.py` | 2.2 الخزينة | Critical | Bank Recon |
| `revenue_recognition.py` | 2.1/2.11 | Critical | IFRS 15 |
| `subscriptions.py` | 2.12 Subscriptions | Critical | MRR/ARR/Dunning |
| `tax_compliance.py`, `taxes.py` | 2.14 Multi-jurisdiction Tax | Critical 🏆 | ZATCA/FTA/ETA/WHT |
| `treasury.py` | 2.2 الخزينة | Critical | Master |

### 2.2 تحت `backend/routers/inventory/` (16 ملف)

| Router | قسم المقارنة | Criticality |
|---|---|---|
| `products.py`, `categories.py`, `suppliers.py`, `warehouses.py` | 2.5 المخزون | Critical |
| `stock_movements.py`, `adjustments.py`, `transfers.py`, `batches.py` | 2.5 المخزون | Critical |
| `costing.py` | 2.5/2.1 | Critical | FIFO/LIFO/WAC |
| `price_lists.py` | 2.3/2.5 | High | per-customer |
| `shipments.py` | 2.5 + 2.15 | Critical | Incoming lifecycle |
| `advanced.py` | 2.5 | High | variants/bins/kits |
| `forecast.py` | 2.5 | High 🏆 | Demand forecast |
| `reports.py`, `notifications.py`, `schemas.py` | 2.5 | High | - |

### 2.3 تحت `backend/routers/sales/` (9 ملفات)

| Router | قسم المقارنة | Criticality |
|---|---|---|
| `quotations.py`, `orders.py`, `invoices.py`, `credit_notes.py`, `returns.py`, `vouchers.py`, `customers.py` | 2.3 المبيعات | Critical |
| `cpq.py` | 2.11 العقود و CPQ | Critical 🏆 |
| `sales_improvements.py` | 2.3 | High | DO, price lists, commissions |

### 2.4 تحت `backend/routers/hr/` (4) و `manufacturing/` (3)

| Router | قسم | Criticality |
|---|---|---|
| `hr/core.py`, `hr/advanced.py`, `hr/performance.py`, `hr/self_service.py` | 2.7 HR | Critical |
| `hr_wps_compliance.py` | 2.7/2.14 | Critical 🏆 | GOSI/WPS/Saudization |
| `manufacturing/core.py`, `routing.py`, `shopfloor.py` | 2.6 التصنيع | Critical |

### 2.5 Routers مسطّحة جذرية (33 ملف)

| Router | قسم | Criticality |
|---|---|---|
| `auth.py`, `security.py`, `roles.py`, `sso.py` | 2.17 الأمان | Critical |
| `approvals.py`, `audit.py` | 2.16/2.17 | Critical |
| `crm.py`, `pos.py`, `contracts.py` | 2.3 | Critical |
| `purchases.py`, `matching.py`, `landed_costs.py`, `delivery_orders.py` | 2.4 | Critical |
| `parties.py`, `companies.py`, `branches.py` | 2.17 | Critical |
| `projects.py`, `services.py` | 2.8/2.10 | High |
| `notifications.py`, `sms.py`, `shipping.py`, `external.py`, `mobile.py` | 2.15 التكاملات | High |
| `dashboard.py`, `role_dashboards.py`, `reports.py`, `scheduled_reports.py` | 2.13 BI | High |
| `data_import.py` | 2.13/2.15 | High |
| `settings.py`, `system_completion.py` | 2.17/2.14 | High |

### 2.6 خلاصة التغطية

- 17/17 قسم من SYSTEM_COMPARISON.md له router/خدمة مرتبطة.
- **Frontend pages (341):** توزيع تقديري يتطابق مع المجموعات أعلاه (سيُدقّق في المرحلة 9).
- **Mobile (24 ملف):** تغطية جزئية — POS/Inventory/Approvals/HR Self-service (تُدقّق في المرحلة 9).

---

## 3 · الأرقام المرجعية (Baseline Metrics)

### 3.1 الكود

| المقياس | القيمة | المصدر |
|---|---:|---|
| LOC `backend/routers/` | **67,496** | `find + wc -l` |
| LOC `backend/services/` | 8,854 | ↑ |
| LOC `backend/schemas/` | 4,164 | ↑ |
| LOC `backend/models/` | 6,064 | ↑ |
| LOC `backend/integrations/` | 1,948 | ↑ |
| LOC `backend/utils/` | 5,012 | ↑ |
| LOC `frontend/src/pages/` | **86,856** | ↑ |
| LOC `frontend/src/components/` | 4,227 | ↑ |
| LOC `mobile/src/` | 3,483 | ↑ |
| TODO/FIXME/XXX/HACK | **3 فقط** | grep |

> **ملاحظة:** الرقم المنخفض جداً للـ TODOs يستحق التحقق — قد يعكس أن التعليقات محذوفة أو المشاكل مُسجّلة خارج الكود.

### 3.2 Endpoints والصلاحيات

| المقياس | القيمة | مرجعي الخطة | فارق |
|---|---:|---:|---:|
| `@router.*` (backend) | **899** | ~872 | +27 (نموّ منذ الخطة) |
| `require_permission` dependencies | 1,084 | — | |
| Unique permission strings (المستخدمة فعلاً) | **137** | 192 | **-55 ⚠️** |
| Permission aliases | 48 | 46 | +2 |
| PERMISSION_SECTIONS keys | 148 | 37 | مختلف (قراءة أخرى) |
| DEFAULT_ROLES | **12 دور** | 10 | +2 (employee, manufacturing_user إلخ) |
| ROLE_DASHBOARD_MAP entries | 13 | 10 | — |

> **ملاحظة:** الخطة ذكرت 192 صلاحية — الفجوة 55 بين **ما هو معرّف** و**ما يُستعمل فعلاً** يجب أن يُدقَّق في المرحلة 2 (هل هي صلاحيات ميتة أم ناقصة الإنفاذ؟).

### 3.3 الأدوار الافتراضية (DEFAULT_ROLES)

`admin · manager · accountant · sales · purchasing · inventory · hr_manager · employee · cashier · manufacturing_user · project_manager · viewer`

### 3.4 الصناعات (Industry KPIs)

`retail · fnb · manufacturing · construction · services · wholesale · general` — **7 صناعات** مدعومة في `industry_kpi_service.py`.

### 3.5 الترجمة (i18n)

| ملف | مفاتيح |
|---|---:|
| `frontend/src/locales/ar.json` | 137 |
| `frontend/src/locales/en.json` | 137 |
| `backend/locales/errors.ar.json` | 496 |
| `backend/locales/errors.en.json` | 496 |

- `hardcoded_strings.json` يحتوي 7 إدخالات (قائمة الفحص).
- `keys_to_translate.json` يحتوي 2 إدخالات.

> **ملاحظة:** 137 مفتاح فقط في ملفات i18n الأمامية مقابل 341 صفحة — يُحتمل نقص تغطية كبير (سيتم فحصه في المرحلة 9).

### 3.6 قاعدة البيانات (الحالة الفعلية)

| DB | الحجم | Alembic version | عدد الجداول |
|---|---:|---|---:|
| `aman_06f7cf0f` | 18 MB | ❌ لا يوجد `alembic_version` | 222 |
| `aman_636aa03a` | 18 MB | ❌ لا يوجد `alembic_version` | 222 |
| `aman_866fad11` | 24 MB | `0002_drop_campaign_cols` (قديم/غريب) | 281 |
| `aman_dbad0e8e` | 23 MB | `0012_phase5_world_comparison` ✅ | **292** |

**المرجع من الخطة:** 282 جدولاً في شركة نموذجية — الشركة الأحدث بها **292 جدولاً** (زيادة طبيعية).

### 3.7 البنية التحتية

| المكوّن | الحالة |
|---|---|
| PostgreSQL | ✅ listening on `127.0.0.1:5432` (local, not Docker) |
| Redis 7-alpine | ✅ container `aman_local_redis` on `0.0.0.0:6379` |
| docker-compose services | db · redis · backend · frontend · prometheus · grafana |
| Python | 3.12.3 |
| Node | v22.22.2 |
| CI Workflows | **1 فقط:** `security-scan.yml` |

### 3.8 Dependencies

- `backend/requirements.txt`: **40 سطر** — FastAPI · SQLAlchemy · Alembic · Pydantic v2 · psycopg2-binary · Redis · pyotp · uvicorn[standard]
- `frontend/package.json`: 21 dependencies + 10 devDependencies (scripts: dev, build, preview, test, test:watch, test:coverage)

### 3.9 Raw SQL usage

- **3,328 موقع** في كل backend يحتوي `text(` أو `.execute("...")` — ستُفحص كلها في SQL Safety Linter بالمرحلة 2 & 3.

### 3.10 الاختبارات

- `backend/tests/**/*.py` = **65 ملف**
- Frontend test/spec files = **336 ملف** (قد تكون من node_modules — يحتاج تحقق)

---

## 4 · مصفوفة الأدوار × الوحدات (خريطة تقديرية)

| الدور | Finance | Inventory | Sales | Purchases | HR | Manuf. | Projects | POS | Admin |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| admin | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| manager | R | R | R | R | R | R | R | R | — |
| accountant | ✅ | R | R | R | — | — | R | R | — |
| sales | R | R | ✅ | — | — | — | — | ✅ | — |
| purchasing | — | R | — | ✅ | — | R | — | — | — |
| inventory | — | ✅ | — | R | — | R | — | — | — |
| hr_manager | R | — | — | — | ✅ | — | — | — | — |
| cashier | — | R | R | — | — | — | — | ✅ | — |
| manufacturing_user | — | R | — | — | — | ✅ | — | — | — |
| project_manager | R | — | — | — | — | — | ✅ | — | — |
| employee | — | — | — | — | R (self) | — | — | — | — |
| viewer | R | R | R | R | R | R | R | R | — |

(✅ = full / R = read-only / — = none). ستُتحقَّق في المرحلة 2 عبر مصفوفة Roles × Permissions × Endpoints الفعلية.

---

## 5 · مخاطر اكتُشفت أثناء المرحلة 1 (حمراء قبل المرحلة 2)

### 5.1 🚨 P0 — انحراف Alembic عبر قواعد المستأجرين

- DBs: `aman_06f7cf0f` و`aman_636aa03a` **لا تحتوي جدول `alembic_version`** رغم احتوائها 222 جدولاً — أي أن مسار الـ bootstrap الأوّل عن طريق SQL blocks (كما هو موثّق في ذاكرة المستودع) لم يقم بـ `alembic stamp head` بنجاح لهاتين الشركتين.
- DB `aman_866fad11` تحمل `version_num = 0002_drop_campaign_cols` **غير موجود** في `backend/alembic/versions/` (الموجود `0002_drop_legacy_campaign_columns`) → سلسلة Alembic مكسورة.
- `alembic current` في المجلد الجذري يرجع خطأ `Can't locate revision identified by 'b2c3d4e5f6a7'` — يشير لوجود مُعرِّف قديم ميت ضمن DB المرتبط بالإعداد.
- **التأثير:** استحالة `alembic upgrade head` / `downgrade` على الشركات غير المحاذية → ترحيلات مستقبلية ستفشل.
- **الإجراء المقترح (المرحلة 3):** سكربت مُعَدِّل يقوم بـ `stamp 0012_phase5_world_comparison` بعد التحقق من مطابقة الجداول للـ schema، أو إعادة bootstrap نظيف للشركتين المتضرّرتين.

### 5.2 ⚠️ P1 — فجوة الصلاحيات (55 permission معرّف لكن غير مستعمل)

الخطة تذكر 192 permission بينما **137 فقط** تُستعمل فعلاً في `require_permission(...)`. يلزم:
- إخراج قائمة الصلاحيات الميتة (unused) والمطلوبة لكن غير المنفَّذة.
- فحص كل endpoint حسّاس بدون `require_permission`.

### 5.3 ⚠️ P1 — تغطية i18n منخفضة ظاهرياً

137 مفتاح فقط للواجهة مقابل 341 صفحة. يُحتمل وجود nested keys أو hardcoded strings كثيرة — يتضح في المرحلة 9.

### 5.4 ⚠️ P1 — CI ضعيف

ملف واحد `security-scan.yml` في `.github/workflows/`. لا pytest/build/lint/coverage CI واضح → يجب توسيعه في المرحلة 3.

### 5.5 ℹ️ P2 — docker-compose غير مستعمل محلياً

PostgreSQL يعمل من النظام المحلي (ليس من compose)، بينما Redis من container. خليط dev يجب أن يُوثَّق في RUNBOOK.

---

## 6 · Definition of Done لكل وحدة (قالب موحّد)

لكل وحدة سيُطبَّق في المراحل 4-9:

1. كل endpoint حسّاس → `require_permission("<perm>")`.
2. كل استعلام SQL → مُعلَّم (`text()` مع `:params`) — بدون f-string concatenation.
3. كل كيان mutation → يُسجَّل في `audit_log`.
4. كل endpoint حاسوبي ذو أثر مالي → ينتج/يعكس **قيداً متوازناً** ويُختبَر وحدوياً.
5. كل جدول ذو بعد مستأجرين → قيد على `company_id` أو داخل schema `aman_{id}`.
6. كل صفحة UI → i18n مُكتملة (0 hardcoded).
7. كل API → OpenAPI summary/tags عربية + إنجليزية.

---

## 7 · قائمة الاستثناءات

| البند | السبب |
|---|---|
| Pen-test خارجي | غير مُدرج (سيُقترح كمرحلة اختيارية بعد 11) |
| SOC 2 / ISO 27001 | خارج النطاق الحالي |
| الأسواق الضريبية | SA + UAE + EG فقط حالياً (لا عُمان/الكويت/قطر) |
| iOS Mobile | الموبايل حالياً Android فقط (`mobile/android/`) |

---

## 8 · الخطوة التالية

✅ **المرحلة 1 مكتملة.** ننتقل إلى **المرحلة 2 (Security) ∥ المرحلة 3 (Platform)** بالتوازي حسب الخطة.

**أهم ما سنركّز عليه فوراً في المرحلة 2:**
1. مصفوفة Roles × Permissions × Endpoints كاملة.
2. اختبار Tenant Isolation فعلي ضد الشركات الأربع الموجودة.
3. SQL Safety Linter على كل الـ 3,328 موقع.
4. فحص كل endpoint حسّاس بدون `require_permission`.

**أهم ما سنركّز عليه في المرحلة 3:**
1. **إصلاح انحراف Alembic في `aman_06f7cf0f` و`aman_636aa03a` و`aman_866fad11`** (P0 من 5.1).
2. تشغيل pytest الكامل وقياس coverage.
3. توسيع CI (build + test + lint + SQL linter + GL discipline).
4. حالة الـ 16 Materialized View المعطلة المذكورة بالخطة.

---

**آخر تحديث:** 2026-04-22 · **الكاتب:** Audit Bot · **المراجعة القادمة:** بعد اكتمال PHASE-02 و PHASE-03.
