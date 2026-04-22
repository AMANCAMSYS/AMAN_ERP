# خطة الفحص المرحلية الشاملة لنظام AMAN ERP

> **الإصدار:** 2.0 — 22 أبريل 2026
> **الحالة:** خطة جاهزة للتنفيذ (لم يبدأ الفحص الفعلي)
> **المرجع:** مصفوفة [SYSTEM_COMPARISON.md](../SYSTEM_COMPARISON.md) ذات الـ17 قسماً
> **المبدأ الأساسي:** ملف مخرجات **واحد** لكل مرحلة لتسهيل المتابعة

---

## 0 · المبادئ الحاكمة للخطة

### 0.1 قواعد التنفيذ
1. **لا تُبدأ مرحلة قبل إتمام سابقتها** باستثناء المراحل المتوازية الموسومة `∥`.
2. **كل مرحلة ملف مخرجات واحد** في `docs/audit/` مُسمّى `PHASE-{NN}-{slug}.md` ويحتوي كل الجداول والنتائج المتعلقة بتلك المرحلة.
3. **مصفوفة الخطورة الموحّدة** (P0/P1/P2/P3) تُطبّق في جميع المراحل.
4. **كل finding يجب أن يُسجَّل** في ملف المرحلة مع: `ID | Module | Severity | Evidence | Proposed Fix | Owner | ETA`.
5. **أرقام مرجعية (Baseline Numbers)** تُلتقط في المرحلة 1 وتُعاد المقارنة بها في المرحلة 11.

### 0.2 مصفوفة الخطورة

| المستوى | الوصف | SLA للإصلاح |
|---|---|---|
| **P0** Blocker | ثغرة أمنية حرجة · فقدان بيانات · Tenant leakage · عدم توازن محاسبي · فشل build | قبل أي إطلاق |
| **P1** High | Auth weak · RBAC ناقص · حسابات ضريبية خاطئة · MV معطلة · غياب audit log | قبل الإصدار القادم |
| **P2** Medium | أداء بطيء · i18n ناقص · تقارير ناقصة · UX issues | Sprint 2-3 |
| **P3** Low | Code quality · documentation · refactoring · nice-to-have | Backlog |

### 0.3 شجرة المخرجات النهائية
```
docs/audit/
├── AUDIT_PLAN.md                   ← هذه الوثيقة
├── PHASE-01-scope-baseline.md      ← النطاق + الأساس المرجعي
├── PHASE-02-security-rbac.md       ← الأمان + الصلاحيات + Multi-tenancy
├── PHASE-03-platform-devops.md     ← المنصّة + CI + DB + أداء + مراقبة
├── PHASE-04-accounting-core.md     ← المحاسبة + Multi-book + IFRS + الأصول + الموازنات
├── PHASE-05-treasury-tax.md        ← الخزينة + الشيكات + الضرائب + ZATCA/FTA/ETA/Zakat
├── PHASE-06-supply-chain.md        ← المخزون + المشتريات + التصنيع + الجودة
├── PHASE-07-sales-hub.md           ← المبيعات + CRM + POS + CPQ + العقود + الاشتراكات
├── PHASE-08-workforce.md           ← HR + Payroll + المشاريع + الخدمات + DMS
├── PHASE-09-integrations-ux.md     ← التكاملات + الإشعارات + التقارير + الموبايل + i18n + UX
├── PHASE-10-e2e-regression.md      ← اختبار E2E + Regression + UAT
└── PHASE-11-executive-report.md    ← التقرير التنفيذي + Backlog + Roadmap
```

### 0.4 الجدول الزمني المقترح
```
Week 1 : Phase 1
Week 2 : Phase 2 ∥ Phase 3          (متوازيتان)
Week 3 : Phase 4
Week 4 : Phase 5
Week 5 : Phase 6 ∥ Phase 7          (متوازيتان)
Week 6 : Phase 8 ∥ Phase 9          (متوازيتان)
Week 7 : Phase 10
Week 8 : Phase 11
```

---

## المرحلة 1 · النطاق والأساس المرجعي (Scope & Baseline)

### الهدف
توثيق حدود النظام "كما هو" والتقاط كل الأرقام المرجعية قبل بدء الفحص.

### نطاق الملفات
- `README.md`, `CLAUDE.md`, `docs/PROJECT_DESIGN_REQUIREMENTS.md`, `docs/SYSTEM_COMPARISON.md`
- `backend/main.py`, `backend/config.py`, `backend/routers/__init__.py`
- جميع `backend/routers/**/*.py` + `backend/services/**` + `backend/integrations/**`
- `frontend/src/App.jsx`, `frontend/src/pages/**`
- `mobile/App.jsx`, `mobile/src/**`
- `docker-compose.yml`, `docker-compose.prod.yml`, `nginx/`, `monitoring/`
- `backend/alembic/versions/`, `backend/migrations/versions/`

### Checklist

**A. جرد الوحدات (مقابل 17 قسم المقارنة)**
- [ ] جرد 56+ router وربطها بأقسام SYSTEM_COMPARISON.md
- [ ] جرد 170+ صفحة React وربطها بالوحدات
- [ ] جرد شاشات الموبايل
- [ ] تصنيف: Critical (مالية، أمان، tenant) / Secondary / Experimental
- [ ] تحديد Definition of Done لكل وحدة

**B. أرقام مرجعية (Baseline Metrics)**
- [ ] `alembic current` — أحدث migration
- [ ] عدد الجداول في شركة نموذجية (مرجعي: 282)
- [ ] عدد endpoints في OpenAPI (مرجعي: ~872)
- [ ] عدد permissions في registry (مرجعي: 192)
- [ ] عدد sections في roles router (مرجعي: 37)
- [ ] عدد aliases (مرجعي: 46)
- [ ] LOC لكل مجلد (backend/routers, backend/services, frontend/src/pages)
- [ ] dependencies (requirements.txt + package.json) + إصدارات Python/Node/PG/Redis
- [ ] عدد TODO/FIXME/XXX في الكود
- [ ] حجم قاعدة بيانات شركة نموذجية (MB)
- [ ] عدد ملفات الترجمة + عدد المفاتيح (ar/en)
- [ ] p50/p95/p99 لـ10 endpoints حرجة (قياس أولي)

**C. الأدوار واللغات**
- [ ] 10 أدوار (role_dashboards)
- [ ] صناعات (Industry Setup) — retail/manufacturing/services/…
- [ ] AR/EN + RTL + التحقّق من errors.{ar,en}.json

### KPIs
| المقياس | القيمة المستهدفة |
|---|---|
| تغطية الوحدات الحرجة | ≥ 95% |
| نسبة التصنيف المكتمل | 100% |
| ربط routers بأقسام المقارنة | 100% |

### المخرجات → `docs/audit/PHASE-01-scope-baseline.md`
يحتوي على:
- جدول الوحدات (Module × Section × Criticality × Owner × Status)
- جدول الأرقام المرجعية (Metric × Value × Timestamp)
- مصفوفة الأدوار × الوحدات
- قائمة الاستثناءات مع المبرّرات

---

## المرحلة 2 · الأمان والصلاحيات و Multi-tenancy (Security) ∥

### الهدف
التأكد من حماية البيانات، تطبيق مبدأ أقل الامتيازات، وصمود النظام أمام OWASP Top 10.

### نطاق الملفات
- `backend/routers/auth.py`, `security.py`, `roles.py`, `sso.py`
- `backend/utils/security.py`, `permissions.py`, `csrf_middleware.py`, `security_middleware.py`, `auth_cookies.py`, `limiter.py`, `tenant_isolation.py`, `optimistic_lock.py`, `fiscal_lock.py`, `field_encryption.py`, `masking.py`, `duplicate_detection.py`, `audit.py`
- `backend/middleware/**`
- `frontend/src/context/AuthContext.jsx`, `utils/axios*.js`, `utils/auth.js`
- `nginx/production.conf` (security headers)
- `.env.example`, CI workflows

### Checklist

**A. المصادقة (Authentication)**
- [ ] JWT: عمر التوكن، refresh، revoke
- [ ] كلمات المرور: bcrypt/argon2 + salt + Password Policy
- [ ] 2FA TOTP (pyotp) — التفعيل، backup codes، الاسترداد
- [ ] Session Management + إنهاء الجلسات النشطة
- [ ] SSO: SAML 2.0 + OAuth2 + LDAP + Group→Role mapping
- [ ] "نسيت كلمة المرور": token expiry + rate limit
- [ ] HttpOnly Cookies + CSRF Token

**B. الصلاحيات (RBAC)**
- [ ] `require_permission()` على **كل** endpoint حسّاس (192 permission)
- [ ] مصفوفة Roles × Permissions × Endpoints
- [ ] IDOR: التحقّق من company_id + user_id
- [ ] صلاحيات خاصة (حذف، تصدير، تقارير مالية، Zakat، VAT)
- [ ] Fiscal Lock: منع التعديل بعد الإغلاق

**C. Multi-tenancy**
- [ ] عزل `aman_{company_id}` — لا cross-tenant queries
- [ ] Tenant Isolation Middleware يرفض الطلبات بدون claim صحيح
- [ ] JWT claims تحتوي company_id
- [ ] اختبار اختراق: محاولة قراءة بيانات شركة أخرى

**D. Hardening (OWASP Top 10)**
- [ ] A01 Broken Access — RBAC + IDOR tests
- [ ] A02 Crypto — Field Encryption at Rest + TLS
- [ ] A03 Injection — **SQL Safety Linter CI** ينجح + فحص كل raw SQL
- [ ] A04 Insecure Design — threat model
- [ ] A05 Misconfig — CORS + CSP + Security Headers (Nginx)
- [ ] A06 Vulnerable Deps — `pip-audit` + `npm audit`
- [ ] A07 Auth Failures — rate limit login/register/reset
- [ ] A08 Integrity — gitleaks CI + signed commits
- [ ] A09 Logging — audit log + PII masking + no secrets in logs
- [ ] A10 SSRF — external calls validation

**E. Audit Trail**
- [ ] كل CRUD حسّاس مُسجّل (user, timestamp, before/after diff)
- [ ] Immutable audit log (لا DELETE/UPDATE)
- [ ] PII masking في log viewer
- [ ] Duplicate Detection على parties/products

### KPIs
| المقياس | الهدف |
|---|---|
| endpoints حرجة بدون require_permission | 0 |
| raw SQL بدون parameterization | 0 |
| secrets في repo (gitleaks) | 0 |
| CVE حرجة في dependencies | 0 |
| endpoints بدون rate limit (login/register/reset) | 0 |
| Tenant isolation tests passing | 100% |
| PII masking coverage | 100% من الحقول الحساسة |

### المخرجات → `docs/audit/PHASE-02-security-rbac.md`
يحتوي: RBAC matrix · OWASP findings · Tenant isolation test results · CVE report · Audit trail coverage.

---

## المرحلة 3 · المنصّة و DevOps والصحة التقنية (Platform) ∥

### الهدف
تقييم جودة الكود، CI/CD، الأداء، قاعدة البيانات، والمراقبة.

### نطاق الملفات
- `backend/` (كل الكود) + `frontend/` + `mobile/`
- `backend/tests/**`, `frontend/**/*.test.*`, `e2e/**`
- `backend/alembic/`, `backend/migrations/`, `backend/database.py`
- `backend/utils/redis_event_bus.py`, `outbox_relay.py`, `webhooks.py`, `ws_manager.py`, `plugin_registry.py`
- `backend/plugins/**`
- `Dockerfile*`, `docker-compose*.yml`, `.github/workflows/**`
- `monitoring/prometheus.yml`, `monitoring/alerts/aman_alerts.yml`, `monitoring/grafana/**`
- `nginx/production.conf`
- `scripts/backup_postgres.sh`, `restore_postgres.sh`, `full_code_scanner.py`, `check_sql_parameterization.py`, `check_gl_posting_discipline.py`

### Checklist

**A. Build & Dependencies**
- [ ] `pip install` + `npm install` + `npm run build` كلها تنجح من نظيف
- [ ] Lockfiles موحّدة + مشروحة
- [ ] لا Deprecated حرجة

**B. Tests & Coverage**
- [ ] `pytest` — pass/fail/skip counts
- [ ] `npm test` — نتائج
- [ ] coverage backend ≥ 70% · frontend ≥ 60%
- [ ] integration tests موجودة
- [ ] E2E (Playwright/Cypress) — عدد السيناريوهات

**C. Code Quality**
- [ ] `ruff check` · `mypy` · `eslint` · `tsc --noEmit`
- [ ] **SQL Safety Linter** يمرّ (scripts/check_sql_parameterization.py)
- [ ] **GL Posting Discipline Checker** يمرّ
- [ ] cyclomatic complexity > 15 موثّق
- [ ] ملف `database.py` (~6281 سطر) — خطة تقسيم

**D. Database**
- [ ] `alembic upgrade head` من صفر ينجح
- [ ] `downgrade base` ينجح
- [ ] FK ordering صحيح في `create_company_tables()`
- [ ] indexes موجودة على الأعمدة شائعة الاستعلام
- [ ] N+1 queries مكشوفة ومُوثّقة
- [ ] **Materialized Views**: الـ16 المعطلة — حالة كل واحدة

**E. Performance**
- [ ] p50/p95/p99 لـ10 endpoints حرجة (مالية + POS + reports)
- [ ] bundle size < 2MB gzipped
- [ ] Lighthouse score على 3 صفحات رئيسية
- [ ] استعلامات > 500ms — قائمة

**F. Infrastructure & Observability**
- [ ] Docker images تُبنى وتعمل
- [ ] docker-compose prod: DB/Redis بدون ports مكشوفة + resource limits
- [ ] Nginx: SSL + HTTP/2 + Security Headers + Rate Limiting
- [ ] Prometheus metrics + **alert rules** (BackendDown, HighErrorRate, GL discipline)
- [ ] Grafana dashboards
- [ ] Health check endpoints
- [ ] Structured logging (JSON) + Request ID / tracing
- [ ] Error reporting (Sentry)

**G. بنية الأحداث والتوسعة**
- [ ] Redis Event Bus يعمل (is_enabled + install)
- [ ] Outbox Relay pattern يُسلّم الأحداث
- [ ] Webhooks retry logic
- [ ] WebSocket Manager (notifications + shop floor)
- [ ] Plugin Registry — تحميل plugins (e.g., gl_posting_metrics)

**H. Backup & Restore**
- [ ] `scripts/backup_postgres.sh` يعمل
- [ ] `scripts/restore_postgres.sh` يعمل
- [ ] UI في `Admin/BackupManagement.jsx` تعمل
- [ ] سياسة backup دورية موثّقة

### KPIs
| المقياس | الهدف |
|---|---|
| نسبة نجاح pytest | ≥ 95% |
| coverage backend / frontend | ≥ 70% / 60% |
| CVE حرجة | 0 |
| bundle size | < 2MB gz |
| p95 endpoints حرجة | < 500ms |
| MV معطلة | من 16 → 0 |
| alert rules تعمل | 100% |

### المخرجات → `docs/audit/PHASE-03-platform-devops.md`
يحتوي: test results · coverage · CVE report · performance baseline · DB schema diff · MV status · infra checklist.

---

## المرحلة 4 · المحاسبة والنواة المالية (Accounting Core)

### الهدف
ضمان صحة ودقة الـ Double-Entry، التوازن، IFRS، Multi-book، والموازنات والأصول الثابتة.

### نطاق الملفات
- `backend/routers/finance/accounts.py`, `journal.py`, `invoices.py`, `expenses.py`, `advanced_workflow.py`, `accounting_depth.py`
- `backend/services/multibook_service.py`, `forecast_service.py`
- `backend/routers/budgets.py`, `assets.py`
- `backend/routers/contracts.py` (IFRS 15 side)
- جداول: `accounts`, `journal_entries`, `journal_lines`, `invoices`, `invoice_lines`, `fiscal_years`, `periods`, `budgets`, `assets`, `asset_depreciation`, `lease_contracts`, `expenses`, `expense_policies`, `cost_centers`, `currencies`, `exchange_rates`
- `frontend/src/pages/Accounting/**`, `pages/Assets/**`, `pages/Budgets/**`

### Checklist

**A. دليل الحسابات (CoA)**
- [ ] شجري بمستويات متعدّدة + parent_id صحيح
- [ ] Industry CoA Templates تعمل
- [ ] منع حذف حساب له أرصدة أو حركات
- [ ] تصنيفات Asset/Liability/Equity/Revenue/Expense
- [ ] ترقيم آلي متسق

**B. القيود اليومية (Journal Entries)**
- [ ] Debit = Credit لكل قيد
- [ ] منع الترحيل على حسابات header
- [ ] Reversing Entries
- [ ] **Recurring Templates** (قوالب دورية)
- [ ] ربط القيد بمصدره (Invoice/Payment/Payroll/WO)
- [ ] Fiscal Lock يمنع التعديل بعد الإغلاق
- [ ] Opening Balances
- [ ] Period Comparison
- [ ] Closing Entries سنوي

**C. الفواتير**
- [ ] VAT inclusive/exclusive — حسابات صحيحة
- [ ] خصم السطر / الفاتورة
- [ ] الترحيل ينشئ قيداً متوازناً
- [ ] الإلغاء يعكس القيد
- [ ] ترقيم متسلسل قانوني (بدون فجوات)
- [ ] AR/AP Aging

**D. Multi-currency**
- [ ] تحديث أسعار الصرف (يدوي + API)
- [ ] FX Revaluation دوري (realized/unrealized)
- [ ] إعادة تقييم أرصدة نهاية الفترة

**E. IFRS المتقدّمة**
- [ ] **IFRS 15** (Revenue Recognition) — contracts + performance obligations
- [ ] **IFRS 9** (ECL Provisions)
- [ ] **IAS 36** (Impairment)
- [ ] **IFRS 16** (Lease Contracts) — جدول إطفاء + ROU asset
- [ ] **Multi-book** (IFRS + Local GAAP بالتوازي)

**F. Intercompany**
- [ ] قيود بين الشركات تتوازن عند الدمج
- [ ] مطابقة Intercompany balances

**G. التقارير المالية**
- [ ] Trial Balance متوازن
- [ ] Balance Sheet (A = L + E)
- [ ] Income Statement
- [ ] Cash Flow Statement
- [ ] Budget vs Actual

**H. الأصول الثابتة**
- [ ] FA Register + Categories + Tags
- [ ] Straight-line ✅ / Declining-balance ⚠️ / Units-of-production ⚠️
- [ ] Disposal + Gain/Loss entry
- [ ] Revaluation + Impairment
- [ ] Maintenance + Equipment Registry

**I. الموازنات**
- [ ] Budget per cost-center
- [ ] Budget periods
- [ ] Budget vs Actual variance

### KPIs
| المقياس | الهدف |
|---|---|
| قيود غير متوازنة | 0 |
| فواتير بدون قيد | 0 |
| فجوات ترقيم | 0 |
| انحراف Trial Balance | 0.00 |
| دقة VAT في عينة 100 فاتورة | 100% |
| Multi-book parity (IFRS vs Local) | 100% |
| coverage tests للمالية | ≥ 80% |
| IFRS 15/9/16/IAS 36 endpoints مغطاة tests | 100% |

### المخرجات → `docs/audit/PHASE-04-accounting-core.md`
يحتوي: CoA audit · JE balance · Invoices audit · FX audit · IFRS compliance · FA audit · Budgets audit · Financial Reports reconciliation.

---

## المرحلة 5 · الخزينة والامتثال الضريبي (Treasury & Tax)

### الهدف
فحص دورة الخزينة MENA الكاملة (شيكات + Notes + Bank Feeds + Cash Forecast) والامتثال الضريبي متعدّد الولايات.

### نطاق الملفات
- `backend/routers/finance/checks.py`, `notes.py`, `cashflow.py`, `tax_compliance.py`, `payments.py`
- `backend/routers/system_completion.py` (Zakat)
- `backend/integrations/einvoicing/` (ZATCA + UAE FTA + Egypt ETA)
- `backend/integrations/bank_feeds/` (MT940)
- جداول: `checks_payable`, `checks_receivable`, `notes_receivable`, `notes_payable`, `bank_accounts`, `bank_transactions`, `bank_reconciliations`, `tax_regimes`, `company_tax_settings`, `branch_tax_settings`, `jurisdictions`, `tax_returns`, `withholding_taxes`, `zakat_calculations`, `cash_flow_forecasts`
- `frontend/src/pages/Treasury/**`, `pages/Taxes/**`, `pages/Accounting/ZakatCalculator.jsx`, `pages/CashFlow/**`

### Checklist

**A. الشيكات (Checks) — MENA 🏆**
- [ ] Checks Receivable: pending/deposited/cleared/bounced/returned
- [ ] Checks Payable: post-dated lifecycle
- [ ] Status Log (كل انتقال حالة موثّق + صلاحية treasury.view)
- [ ] Checks Aging Report
- [ ] قيود GL لكل انتقال حالة

**B. أوراق القبض والدفع (Notes)**
- [ ] Notes Receivable + Payable
- [ ] Discounting / Endorsement
- [ ] قيود GL صحيحة

**C. البنوك والمطابقة**
- [ ] Bank reconciliation ضد كشوفات
- [ ] **MT940 Parser** يستورد SWIFT
- [ ] CSV + OFX imports
- [ ] Auto-matching rules

**D. التنبؤ النقدي (Cash Flow Forecasting)**
- [ ] Generate Forecast (by period)
- [ ] Forecast Lines
- [ ] Scenarios (optimistic/base/pessimistic)

**E. بوّابات الدفع (Payment Gateways)**
- [ ] Stripe — charge/refund/webhook
- [ ] **Tap** — معاملة خليجية
- [ ] **PayTabs** — معاملة خليجية
- [ ] فشل الدفع → retry + dunning

**F. الضرائب متعدّدة الولايات**
- [ ] **Tax Regimes per-branch** (jurisdictions table)
- [ ] VAT Return — مجاميع تطابق Ledger
- [ ] WHT calculations
- [ ] Tax Calendar + Reminders
- [ ] Tax Audit Trail

**G. الفوترة الإلكترونية متعدّدة الدول 🏆**
- [ ] **ZATCA Phase 2** (السعودية) — QR + UBL XML + Invoice Hash
- [ ] **UAE FTA** — submission + acknowledgment
- [ ] **Egypt ETA** — submission + signing
- [ ] فشل الإرسال → retry + queue

**H. الزكاة 🏆**
- [ ] Zakat Calculator — الأساس + نسبة 2.5%
- [ ] ربط بـ Balance Sheet
- [ ] تقرير الزكاة السنوي

### KPIs
| المقياس | الهدف |
|---|---|
| شيكات بدون GL mirror | 0 |
| فروقات Bank Reconciliation | 0 |
| e-invoice submissions فاشلة | 0 |
| دقة VAT Return ضد Trial Balance | 100% |
| ZATCA QR verification | 100% |
| WHT accuracy على عينة 50 | 100% |

### المخرجات → `docs/audit/PHASE-05-treasury-tax.md`
يحتوي: Checks audit · Notes audit · Bank Recon results · Cash Forecast validation · Payment gateways tests · Tax Compliance · E-invoicing test results · Zakat validation.

---

## المرحلة 6 · سلسلة الإمداد (Supply Chain) ∥

### الهدف
فحص دورة المشتريات → المخزون → التصنيع → الجودة مع صحة التكاليف والقيود.

### نطاق الملفات
- `backend/routers/purchases.py`, `matching.py`, `landed_costs.py`, `delivery_orders.py`
- `backend/routers/inventory/shipments.py`, `advanced.py`, `forecast.py`, `price_lists.py`
- `backend/routers/manufacturing/**` (BOM, WO, WC, Equipment, MRP, Capacity, Scheduler, JobCards)
- `backend/services/matching_service.py`, `demand_forecast_service.py`
- جداول: `products`, `product_variants`, `product_kits`, `bin_locations`, `inventory`, `inventory_transactions`, `warehouses`, `stock_transfers`, `purchase_orders`, `po_lines`, `rfq`, `purchase_agreements`, `grn`, `three_way_matches`, `landed_costs`, `supplier_ratings`, `bom`, `work_orders`, `work_centers`, `equipment`, `job_cards`, `quality_inspections`
- `frontend/src/pages/Buying/**`, `Stock/**`, `Manufacturing/**`, `Forecast/**`

### Checklist

**A. المخزون الأساسي**
- [ ] IN/OUT/TRANSFER/ADJUSTMENT تحافظ على الأرصدة
- [ ] FIFO / LIFO / WAC — تطابق السياسة
- [ ] **Cost Layer Policy Versioning** 🏆
- [ ] Landed Costs (shipping/customs/insurance) تُضاف للتكلفة
- [ ] GL entry على التحويلات متعدّدة الأصناف (INV-L04)
- [ ] Product Ledger كامل

**B. مخزون متقدّم**
- [ ] **Product Variants** (مقاس/لون/مادة)
- [ ] **Bin Locations** داخل المستودع
- [ ] **Product Kits** (BOM sales kit)
- [ ] Batch/Lot + Serial tracking
- [ ] Expiry date alerts
- [ ] Reorder points + low stock alerts

**C. العدّ الدوري والجودة**
- [ ] Cycle Count + Stock Adjustments
- [ ] **Quality Inspections** — pass/fail + corrective action
- [ ] Incoming Shipments lifecycle

**D. التنبؤ بالطلب**
- [ ] **Demand Forecasting** (إحصائي — moving average/seasonal)
- [ ] ربط بالـ Reorder points

**E. المشتريات الكاملة**
- [ ] PR → RFQ → PO → GRN → Invoice → Payment
- [ ] **Three-Way Matching** (PO/GRN/Invoice + Tolerances)
- [ ] **Blanket PO + Releases**
- [ ] **Purchase Agreements** (إطارية)
- [ ] **Supplier Ratings** (auto update + KPIs)
- [ ] موافقات متعدّدة المستويات + SLA + Escalation

**F. التصنيع الكامل**
- [ ] BOM متعدّد المستويات + Phantom
- [ ] Work Orders + Routing + Operations
- [ ] Work Centers + Equipment Registry
- [ ] **MRP-II Planning**
- [ ] **Capacity Planning + Load**
- [ ] **Production Scheduler** (drag-and-drop)
- [ ] **Job Cards + Shop-floor Entry**
- [ ] Standard Costing + Variance Analysis
- [ ] Direct Labor Report
- [ ] **Equipment Maintenance (CMMS)**
- [ ] Production Analytics + WO Status Report

### KPIs
| المقياس | الهدف |
|---|---|
| فروقات stock ledger vs inventory | 0 |
| PO بدون GRN ولا closure | موثّقة |
| Three-Way Match success rate | ≥ 95% |
| دقة تكلفة عينة 100 صنف | ≥ 99% |
| Quality inspections coverage (for quality-tracked items) | 100% |
| MRP يقترح PR صحيحة | ≥ 95% |
| WO variances ضمن tolerance | يُقاس |

### المخرجات → `docs/audit/PHASE-06-supply-chain.md`
يحتوي: Inventory reconciliation · Variants/Bins/Kits audit · Forecast accuracy · Purchasing flow · 3-Way matching results · Supplier ratings audit · Manufacturing audit · Quality inspections.

---

## المرحلة 7 · مركز المبيعات (Sales Hub) ∥

### الهدف
فحص دورة المبيعات الكاملة + CRM + POS + CPQ + Contracts + Subscriptions.

### نطاق الملفات
- `backend/routers/sales/**` (orders, commissions, cpq, pricing)
- `backend/routers/crm.py`, `contracts.py`, `pos.py`
- `backend/routers/finance/subscriptions.py`, `backend/services/subscription_service.py`, `cpq_service.py`
- جداول: `sales_orders`, `so_lines`, `delivery_orders`, `quotations`, `customer_price_lists`, `commissions`, `commission_rules`, `cpq_configurations`, `cpq_rules`, `cpq_quotes`, `contracts`, `contract_amendments`, `contract_milestones`, `subscription_plans`, `subscriptions`, `subscription_invoices`, `pos_sessions`, `pos_orders`, `pos_payments`, `loyalty_programs`, `loyalty_points`, `promotions`, `leads`, `opportunities`, `pipelines`, `campaigns`, `tickets`, `knowledge_base`, `customer_segments`
- `frontend/src/pages/Sales/**`, `CRM/**`, `POS/**`, `CPQ/**`, `Subscription/**`, `Campaign/**`

### Checklist

**A. دورة المبيعات الأساسية**
- [ ] Quotation → SO → **Delivery Order** → Invoice → Payment
- [ ] Credit / Debit Notes
- [ ] Customer Price Lists (per customer/branch/date)
- [ ] Reserve stock عند SO
- [ ] Sales Returns → أثر على المخزون والمالية
- [ ] Sales Commissions + Rules

**B. CRM متقدّم**
- [ ] Leads + **Lead Scoring**
- [ ] Opportunities + **Pipeline Analytics**
- [ ] **Customer Segmentation**
- [ ] Campaigns (marketing)
- [ ] Tickets / Helpdesk
- [ ] **Knowledge Base**
- [ ] Activities/Notes log

**C. POS شامل**
- [ ] فتح/إغلاق الوردية + Cash Count + تسوية
- [ ] طرق دفع متعدّدة
- [ ] طباعة حرارية + QR ZATCA
- [ ] **Offline Mode + Sync + Conflict Resolution**
- [ ] **Kitchen Display (KDS)** + **Customer Display**
- [ ] **Table Management** (مطاعم)
- [ ] **Loyalty Programs + Points**
- [ ] **Promotions Engine** (rules)

**D. CPQ (Configure-Price-Quote) 🏆**
- [ ] Product Configurator UI
- [ ] Configuration Rules + Validation
- [ ] Price Calculation engine
- [ ] Quote PDF generation
- [ ] Quote → SO conversion

**E. العقود (Contract Lifecycle)**
- [ ] Contract Master + Terms + Milestones
- [ ] **Contract Amendments** + إصدارات
- [ ] Contract → Auto-Invoice
- [ ] Renewal reminders

**F. الاشتراكات (Subscription Billing)**
- [ ] Subscription Plans + Tiers
- [ ] Enrollments + Customer lifecycle
- [ ] Plan Changes + **Prorations**
- [ ] Recurring Invoicing + Auto-charge
- [ ] **Dunning + Retry Logic**
- [ ] MRR / ARR / Churn metrics

### KPIs
| المقياس | الهدف |
|---|---|
| SO بدون DO ولا cancellation | موثّقة |
| POS sessions بدون closure | 0 |
| POS offline sync conflicts resolved | 100% |
| CPQ rules validation accuracy | 100% |
| Contract amendments preserve history | 100% |
| Subscription proration accuracy | 100% |
| Loyalty points calculations | 100% |
| متوسط زمن POS checkout | < 500ms |

### المخرجات → `docs/audit/PHASE-07-sales-hub.md`
يحتوي: Sales flow · CRM depth · POS audit · CPQ test cases · Contract lifecycle · Subscription billing validation · Loyalty/Promotions.

---

## المرحلة 8 · القوى العاملة والخدمات (Workforce) ∥

### الهدف
فحص HR + Payroll (GCC compliance) + المشاريع + Field Services + DMS.

### نطاق الملفات
- `backend/routers/hr/**` (employees, payroll, attendance, leaves, recruiting, training, performance, loans, custody, violations, eos, overtime, salary_structures)
- `backend/routers/hr_wps_compliance.py`
- `backend/routers/projects.py`, `services.py`
- `backend/routers/approvals.py`, `backend/utils/approval_utils.py`
- جداول: `employees`, `departments`, `positions`, `attendance`, `leave_requests`, `leave_balances`, `leave_carryover`, `payroll_entries`, `payslips`, `salary_structures`, `employee_loans`, `overtime_requests`, `custody_assignments`, `violations`, `eos_settlements`, `gosi_contributions`, `wps_batches`, `saudization_reports`, `wht_payments`, `review_cycles`, `performance_reviews`, `recruitment_openings`, `training_programs`, `projects`, `project_tasks`, `project_risks`, `timesheets`, `resource_allocations`, `service_requests`, `documents`, `document_versions`
- `frontend/src/pages/HR/**`, `Projects/**`, `Services/**`, `ResourcePlanning/**`, `Approvals/**`

### Checklist

**A. HR الأساسي**
- [ ] دورة حياة الموظف (hire → active → terminated)
- [ ] Documents (ID, contract, certifications) + expiry alerts
- [ ] Attendance + Geo-fencing + Late/Absence
- [ ] Leave types + Accruals + **Leave Carryover** + Approvals
- [ ] **Salary Structures** (مركّبات مرنة per employee)
- [ ] **Overtime Requests + Approvals**

**B. Payroll (GCC) 🏆**
- [ ] حساب الراتب الشامل
- [ ] **GOSI** (9.75% + 12%) تلقائي
- [ ] **WPS SIF Export** (بنك مركزي سعودي)
- [ ] **لوحة السعودة + نسب الاحتساب**
- [ ] WHT calculations
- [ ] قيود الرواتب تطابق الـ GL

**C. HR خليجي شامل 🏆**
- [ ] **Custody Management** (عهد الموظفين) + إرجاع
- [ ] **Violations / Disciplinary Actions** + خصومات
- [ ] **EOS Settlement** (نهاية خدمة خليجية — Labor Law formula)
- [ ] **Loans + Advances** + جدول سداد
- [ ] Self-service Portal

**D. التوظيف والتدريب**
- [ ] Recruitment: openings → candidates → offers
- [ ] Training Programs + enrollment + certification
- [ ] Performance Reviews

**E. المشاريع**
- [ ] WBS + **Gantt Chart**
- [ ] Timesheets + Approval + Billing
- [ ] مصروفات المشروع
- [ ] Revenue Recognition على المشروع (IFRS 15)
- [ ] Resource Planning + Allocation + **Calendar**
- [ ] **Risk Register**
- [ ] **Project Financials Report** (P&L)
- [ ] **Resource Utilization Report**

**F. الخدمات الميدانية (Field Service)**
- [ ] Service Requests + Priority + SLA
- [ ] Technician Assignment + Routing
- [ ] Service Costs + Billing
- [ ] ربط Work Orders

**G. إدارة الوثائق (DMS)**
- [ ] Upload + categorization + tags
- [ ] **Versioning** + audit
- [ ] Search (full-text)
- [ ] Permission-based access

**H. Advanced Workflows**
- [ ] Workflows متعدّدة الخطوات
- [ ] **SLA Hours + Escalation Tree**
- [ ] **Parallel Approvals**
- [ ] **Auto-approve Threshold**
- [ ] Min/Max Amount Triggers
- [ ] موافقات عبر كل الوحدات (PO/HR/GL/Expense)

### KPIs
| المقياس | الهدف |
|---|---|
| موظفون بدون قسم/منصب | 0 |
| GOSI/WPS accuracy على عينة 50 payslip | 100% |
| EOS calculations متطابقة مع قانون العمل | 100% |
| approvals تتجاوز SLA | موثّقة مع escalation |
| projects بدون cost-center | 0 |
| documents بدون version tracking | 0 |
| coverage tests | ≥ 60% |

### المخرجات → `docs/audit/PHASE-08-workforce.md`
يحتوي: HR lifecycle · GOSI/WPS/Saudization validation · EOS/Custody/Violations audit · Projects audit · Field Service audit · DMS audit · Approvals flow.

---

## المرحلة 9 · التكاملات والتقارير والموبايل و UX (Cross-cutting) ∥

### الهدف
فحص البنية العرضية: التكاملات الخارجية، الإشعارات، التقارير والـ BI، الموبايل، i18n، UX.

### نطاق الملفات
- `backend/integrations/einvoicing/` + `payments/` + `shipping/` + `sms/` + `bank_feeds/`
- `backend/routers/notifications.py`, `mobile.py`, `external.py`, `data_import.py`, `dashboard.py`, `role_dashboards.py`, `scheduled_reports.py`, `reports.py`
- `backend/services/kpi_service.py`, `industry_kpi_service.py`, `industry_gl_rules.py`, `industry_coa_templates.py`
- `frontend/src/pages/Reports/**`, `Setup/**`, `Admin/BackupManagement.jsx`, `components/dashboard/IndustryWidgets.jsx`, `components/GlobalSearch.jsx`, `components/Notifications/**`, `components/common/LoadingStates.jsx`
- `frontend/src/context/ThemeContext.jsx`, `components/common/FloatingThemeToggle.jsx`
- `frontend/src/locales/` + `frontend/src/i18n.js` + `backend/locales/`
- `mobile/src/**`

### Checklist

**A. التكاملات الخارجية**
- [ ] **E-Invoicing**: ZATCA + UAE FTA + Egypt ETA (submissions + retries)
- [ ] **Payment Gateways**: Stripe + Tap + PayTabs (webhooks + reconciliation)
- [ ] **Shipping**: DHL + Aramex (label printing + tracking)
- [ ] **SMS**: Taqnyat + Unifonic + Twilio (delivery receipts)
- [ ] **Bank Feeds**: MT940 + CSV + OFX (auto-matching)

**B. البنية الحدثية**
- [ ] REST API + OpenAPI Spec محدّث
- [ ] **Webhooks + Outbox Relay** — إرسال الأحداث + retry
- [ ] **Event Bus (Redis Streams)** — publish/subscribe
- [ ] **WebSocket** — real-time notifications + shop floor
- [ ] **Plugin Registry** — تحميل plugins ديناميكياً

**C. الإشعارات**
- [ ] قنوات: in-app + Email + SMS + WebSocket live
- [ ] تفضيلات المستخدم (NotificationPreferences)
- [ ] Notifications في كل الأحداث المهمة (approvals, invoices, payroll, …)

**D. التقارير و BI**
- [ ] Balance Sheet + P&L + Cash Flow
- [ ] AR/AP Aging + Checks Aging
- [ ] Dashboard معرّف بالدور (10 أدوار)
- [ ] KPI Dashboard + **Industry KPI Widgets**
- [ ] **Report Builder** (self-service)
- [ ] **Industry Reports** (صناعة-محدّدة)
- [ ] **Shared Reports** + صلاحيات
- [ ] Scheduled Reports + Email delivery (11 أنواع)
- [ ] RTL تقارير عربية

**E. Data Import/Export**
- [ ] **Data Import Framework** (configs per-entity: accounts/parties/products/…)
- [ ] Excel/CSV imports مع validation
- [ ] Export كامل

**F. الموبايل (React Native)**
- [ ] Device Registration + Push Notifications
- [ ] **Offline Sync + Conflict Resolution**
- [ ] شاشات: POS + Inventory + Approvals + HR Self-service
- [ ] Performance + startup time

**G. i18n / RTL**
- [ ] AR/EN عبر كل الصفحات — 0 hardcoded strings
- [ ] RTL Layout + Formulas + Printout
- [ ] Localized error messages (errors.ar.json)
- [ ] Hardcoded strings scanner يمرّ نظيفاً

**H. UX**
- [ ] **Global Search** (cross-module)
- [ ] **Dark Mode + Theme Toggle**
- [ ] **Onboarding Wizard + Industry Setup**
- [ ] Loading states موحّدة (LoadingStates.jsx)
- [ ] Accessibility (a11y) أساسية

### KPIs
| المقياس | الهدف |
|---|---|
| e-invoicing submission failures | 0 (مع retry) |
| Payment gateway reconciliation | 100% |
| notifications غير مُسلّمة | 0 |
| i18n keys مفقودة | 0 |
| hardcoded Arabic/English strings | 0 |
| Mobile offline sync conflicts resolved | 100% |
| Scheduled reports delivered on time | ≥ 99% |
| Dashboard load time | < 2s |

### المخرجات → `docs/audit/PHASE-09-integrations-ux.md`
يحتوي: Integrations test matrix · Event bus validation · Notifications coverage · Reports validation · Mobile audit · i18n coverage · UX checklist.

---

## المرحلة 10 · الاختبار الشامل E2E و Regression

### الهدف
تشغيل سيناريوهات End-to-End عبر كل الوحدات معاً + Regression على الإصلاحات من المراحل السابقة.

### نطاق الملفات
- `e2e/**` (Playwright/Cypress suite)
- `backend/tests/integration/**`
- أي سيناريوهات UAT موثّقة

### Checklist

**A. سيناريوهات E2E الحرجة (Happy Path)**
- [ ] **Order-to-Cash**: Quote → SO → DO → Invoice → Payment → GL
- [ ] **Procure-to-Pay**: PR → RFQ → PO → GRN → 3-Way Match → Invoice → Payment
- [ ] **Hire-to-Retire**: Hire → Payroll → GOSI → WPS → EOS
- [ ] **Plan-to-Produce**: BOM → MRP → WO → Issue → FG Receipt → Costing
- [ ] **Record-to-Report**: Opening → Transactions → Closing → Financial Reports
- [ ] **POS Shift**: Open → Sales → Refunds → Close → Reconcile → GL
- [ ] **Subscription Lifecycle**: Enroll → Charge → Plan Change → Cancel → Dunning
- [ ] **Contract Lifecycle**: Draft → Sign → Amend → Renew → Close

**B. Multi-tenant Regression**
- [ ] تشغيل السيناريوهات على 3 شركات مختلفة متوازية
- [ ] لا تسرّب بيانات

**C. Multi-language / RTL Regression**
- [ ] كل السيناريوهات باللغة العربية RTL
- [ ] كل السيناريوهات بالإنجليزية LTR

**D. Multi-book / Multi-currency Regression**
- [ ] قيود Multi-book (IFRS + Local) تتطابق
- [ ] FX Revaluation دورية صحيحة

**E. إصلاحات المراحل 2-9**
- [ ] كل P0/P1 finding يملك regression test يُثبت الإصلاح

**F. الحِمل والأداء**
- [ ] Load test على 10 endpoints حرجة (100 req/s)
- [ ] Stress test على POS checkout (50 concurrent cashiers)
- [ ] soak test 24h

**G. UAT (User Acceptance Testing)**
- [ ] مستخدمون حقيقيون يختبرون سيناريوهات محدّدة
- [ ] توقيع UAT من أصحاب المصلحة

### KPIs
| المقياس | الهدف |
|---|---|
| E2E pass rate | 100% |
| P0/P1 regression tests | 100% |
| Load test p95 | ضمن SLA |
| UAT sign-off من كل module owner | 100% |

### المخرجات → `docs/audit/PHASE-10-e2e-regression.md`
يحتوي: E2E test matrix · Multi-tenant/Multi-lang/Multi-book regression · Load test results · UAT sign-offs.

---

## المرحلة 11 · التقرير التنفيذي والخطة المستقبلية

### الهدف
دمج كل نتائج المراحل 1-10 في تقرير واحد مع خطة إصلاح زمنية.

### نطاق الملفات
- كل مخرجات `PHASE-01` → `PHASE-10`

### Checklist
- [ ] دمج كل الـ findings في سجل موحد
- [ ] تصنيف: Module × Severity × Effort × Impact
- [ ] حساب Risk Score = Severity × Impact / Effort
- [ ] تحديد الأنماط المتكرّرة (systemic issues)
- [ ] **Quick Wins** (أثر عالي / جهد منخفض)
- [ ] **Strategic Items** (أثر عالي / جهد عالي)
- [ ] Roadmap زمني (Sprint 1-2-3…)
- [ ] Dependencies بين المهام
- [ ] تقدير الجهد (story points)
- [ ] ملخّص تنفيذي للإدارة (≤ 2 صفحة)
- [ ] مراجعة مع أصحاب المصلحة وتوقيع

### KPIs
| المقياس | الهدف |
|---|---|
| تغطية الـ findings بأولوية | 100% |
| عناصر P0 مع Owner + ETA | 100% |
| Quick Wins | ≥ 10 |
| Roadmap للربع القادم | جاهز |

### المخرجات → `docs/audit/PHASE-11-executive-report.md`
يحتوي: Executive Summary · Findings Register (كل findings المراحل 1-10 في جدول واحد) · Risk Matrix · Quick Wins · Strategic Roadmap · Backlog prioritized.

---

## مصفوفة تغطية المراحل × أقسام SYSTEM_COMPARISON.md

> التحقّق أن كل قسم في المقارنة يُفحص في مرحلة واحدة على الأقل.

| قسم المقارنة | المرحلة الرئيسية | مراحل مساعدة |
|---|---|---|
| 2.1 المحاسبة والتمويل | **4** | 1, 10 |
| 2.2 الخزينة | **5** | 4, 10 |
| 2.3 المبيعات/CRM/POS | **7** | 6, 10 |
| 2.4 المشتريات | **6** | 10 |
| 2.5 المخزون | **6** | 10 |
| 2.6 التصنيع | **6** | 10 |
| 2.7 HR والرواتب | **8** | 10 |
| 2.8 المشاريع | **8** | 10 |
| 2.9 الأصول الثابتة | **4** | 10 |
| 2.10 Service & DMS | **8** | 10 |
| 2.11 العقود و CPQ | **7** | 10 |
| 2.12 Subscription Billing | **7** | 4, 10 |
| 2.13 التقارير و BI | **9** | 3, 10 |
| 2.14 Multi-Jurisdiction Tax | **5** | 10 |
| 2.15 التكاملات | **9** | 5, 10 |
| 2.16 Advanced Workflows | **8** | 10 |
| 2.17 المنصّة والأمان | **2, 3** | كل المراحل |

✅ **كل الـ17 قسماً مُغطّى في مرحلة رئيسية واحدة على الأقل + اختبار E2E في المرحلة 10.**

---

## أسئلة قبل البدء

1. **السوق المستهدف**: أيّ ولايات ضريبية؟ (SA + UAE + Egypt افتراضياً)
2. **نطاق الموبايل**: كامل أم مؤجّل؟
3. **اختبار الاختراق الخارجي**: ذاتي فقط أم Pen-test مستقل؟
4. **حجم الفريق**: كم شخصاً/مرحلة؟
5. **الجدول الزمني**: 8 أسابيع مقبول؟
6. **البيئات**: dev فقط أم dev + staging؟
7. **الامتثال الخارجي**: ISO 27001 / SOC 2 / PDPL؟
8. **الصناعات المستهدفة**: retail / manufacturing / services / kontroktor ؟

---

**آخر تحديث:** 2026-04-22 · **الحالة:** v2.0 جاهزة للتنفيذ · **المرجع:** [SYSTEM_COMPARISON.md](../SYSTEM_COMPARISON.md)
