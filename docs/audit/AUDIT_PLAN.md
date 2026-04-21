# خطة فحص مرحلية شاملة لنظام ERP (Aman)

> **وضع التخطيط** — هذه وثيقة تخطيطية جاهزة للتنفيذ لاحقًا. لا يوجد فحص فعلي في هذه الوثيقة.

---

## ملاحظة تمهيدية: الوحدات المكتشفة في النظام

بناءً على استكشاف سابق للكود، نظام Aman يحتوي على وحدات إضافية يجب إدراجها في الخطة بالإضافة للوحدات المذكورة صراحة:

- **التصنيع (Manufacturing)** — BOM, Work Orders, Production
- **العقود (Contracts)** — إدارة العقود والالتزامات
- **الأصول الثابتة (Fixed Assets)** — الإهلاك، الصيانة
- **الموازنات (Budgets)** — التخطيط المالي
- **تعدد العملات (Multi-currency)** — أسعار الصرف
- **المصفوفات والموافقات (Approval Workflows)** — SLA, Escalation
- **سير العمل والإشعارات (Notifications)**
- **التقارير التحليلية (BI/Analytics)** — Materialized Views
- **الطباعة والقوالب (Print Templates)**
- **التكامل والضرائب الإلكترونية (E-invoicing/ZATCA)** — إن وُجد
- **إدارة الأدوار والصلاحيات الدقيقة (RBAC/Permissions)**
- **Multi-tenancy** — عزل بيانات الشركات
- **النسخ الاحتياطي والاسترداد (Backup/Restore)**
- **التدقيق (Audit Logs)**
- **الترجمة والتوطين (i18n/L10n)** — AR/EN, RTL
- **المصادقة الثنائية (2FA/MFA)** — pyotp
- **تطبيق الجوال (Mobile)** — React Native

تم دمج هذه الوحدات في المراحل المناسبة أدناه.

---

## المرحلة 1: تحديد النطاق والأهداف (Scoping)

### الهدف
توثيق حدود النظام، تحديد الوحدات المشمولة/المستثناة، والاتفاق على معايير القبول قبل بدء الفحص الفعلي.

### نطاق الملفات
- `/README.md`, `/CLAUDE.md`, `/specs/**`
- `/backend/main.py`, `/backend/config.py`
- `/backend/routers/__init__.py` (قائمة الـ routers المسجّلة)
- `/frontend/package.json`, `/frontend/src/App.{tsx,jsx}`, `frontend/src/routes/**`
- `/mobile/package.json`, `/mobile/App.tsx` (إن وُجد)
- `docker-compose.yml`, `Dockerfile*`, `.env.example`

### Checklist
- [ ] جرد جميع الوحدات الوظيفية من `backend/routers/`
- [ ] جرد جميع الصفحات/المسارات في `frontend/src/pages/`
- [ ] جرد شاشات تطبيق الجوال
- [ ] تصنيف الوحدات: Critical / Secondary / Experimental
- [ ] تحديد البيئات: dev / staging / prod
- [ ] تعريف مقياس الخطورة: P0 (Blocker) / P1 (High) / P2 (Medium) / P3 (Low)
- [ ] تعريف "Definition of Done" لكل وحدة

- [ ] تحديد الأدوار المستهدفة (Admin, Accountant, Sales, POS Cashier, HR, Warehouse, Manager)
- [ ] تحديد اللغات/الدول المدعومة (AR/EN، RTL/LTR، SY/SA/AE/EG)
- [ ] تحديد الوحدات المستثناة من هذه الدورة مع مبرراتها

### KPIs
| المقياس | القيمة المستهدفة |
|---|---|
| عدد الوحدات الداخلة في النطاق | يُحدّد ≥ 20 وحدة |
| عدد endpoints في OpenAPI | يُحصى كرقم مرجعي |
| عدد الجداول في شركة نموذجية | مرجعي: 282 |
| تغطية الفحص للوحدات الحرجة | ≥ 95% |
| نسبة الوحدات المصنّفة | 100% |

### المخرجات
- `docs/audit/01-scope.md` — وثيقة النطاق والاستثناءات
- `docs/audit/module-inventory.csv` — جرد الوحدات مع التصنيف
- `docs/audit/severity-matrix.md` — مصفوفة تعريف الخطورة
- `docs/audit/roles-matrix.md` — الأدوار × الوحدات

---

## المرحلة 2: خط الأساس Baseline (الوضع الحالي)

### الهدف
تصوير حالة النظام "كما هي" قبل أي تعديل، وتوثيق الأرقام المرجعية التي ستُقارن عليها نتائج الفحص.

### نطاق الملفات
- `backend/**/*.py` (إحصاءات LOC/Cyclomatic)
- `frontend/src/**/*.{ts,tsx,js,jsx}`
- `backend/alembic/versions/*.py`
- `backend/database.py` (SQL blocks)
- `backend/tests/**`, `frontend/**/*.test.*`
- لقطة DB: `pg_dump --schema-only` لشركة نموذجية
- `backend/backend.log`, سجلات التشغيل

### Checklist
- [ ] تشغيل `alembic current` والتحقق من أحدث migration مُطبّق
- [ ] استخراج قائمة الجداول الفعلية من DB شركة نموذجية (`\dt`)
- [ ] مقارنة الجداول الفعلية مع ما ينتجه `create_company_tables()`
- [ ] جرد جميع الـ FK constraints الفعلية
- [ ] جرد جميع الـ triggers, functions, sequences
- [ ] قياس LOC لكل وحدة backend/frontend
- [ ] قياس تعقيد الدوال الكبرى (> 50 سطر)
- [ ] جرد الـ dependencies (requirements.txt, package.json) وإصداراتها
- [ ] التقاط إصدارات Python/Node/PostgreSQL/Redis المستخدمة
- [ ] استخراج بيانات أداء أولية (response time لـ 10 endpoints حرجة)
- [ ] جرد TODO/FIXME/XXX في الكود
- [ ] توثيق حجم قاعدة البيانات لشركة نموذجية

### KPIs
| المقياس | القيمة المرجعية |
|---|---|
| عدد الجداول الفعلية | يُقاس |
| عدد الـ migrations | يُقاس |
| عدد endpoints | يُقاس |
| عدد dependencies (backend/frontend) | يُقاس |
| عدد TODO/FIXME | يُقاس |
| حجم قاعدة البيانات (MB) | يُقاس |
| عدد ملفات backend/frontend | يُقاس |

### المخرجات
- `docs/audit/02-baseline.md` — التقرير المرجعي
- `docs/audit/baseline-schema.sql` — لقطة schema
- `docs/audit/baseline-deps.json` — جرد التبعيات
- `docs/audit/baseline-metrics.csv` — الأرقام المرجعية

---

## المرحلة 3: الفحص الأمني والصلاحيات (Security & RBAC)

### الهدف
التأكد من أن النظام يحمي البيانات، يطبّق مبدأ أقل الامتيازات، ويصمد أمام الهجمات الشائعة.

### نطاق الملفات
- `backend/auth/**`, `backend/utils/security.py`
- `backend/utils/limiter.py`, `backend/utils/permissions.py`
- `backend/routers/auth.py`, `backend/routers/users.py`, `backend/routers/roles.py`
- `backend/middleware/**`
- `backend/routers/companies.py` (multi-tenancy isolation)
- `frontend/src/contexts/AuthContext.*`, `frontend/src/utils/axios.*`
- `backend/models/` (الحقول الحساسة)
- `.env.example`, `config.py`

### Checklist

**المصادقة (Authentication)**
- [ ] آلية JWT: عمر التوكن، refresh token، إلغاء التوكن
- [ ] تخزين كلمات المرور (bcrypt/argon2 + salt)
- [ ] سياسة تعقيد كلمة المرور
- [ ] 2FA/MFA (pyotp) — التفعيل، الاسترداد، backup codes
- [ ] آلية "نسيت كلمة المرور" (token expiry, rate limit)
- [ ] Session fixation, CSRF protection

**الصلاحيات (Authorization / RBAC)**
- [ ] وجود `require_permission()` في جميع الـ endpoints الحساسة
- [ ] مصفوفة الأدوار × الصلاحيات
- [ ] التحقق من company_id في كل طلب (منع tenant leakage)
- [ ] حماية موارد مستخدم آخر (IDOR)
- [ ] صلاحيات خاصة: حذف، تصدير، تقارير مالية

**Hardening**
- [ ] Rate limiting على endpoints الحرجة (login, register, reset)
- [ ] CORS configuration
- [ ] HTTPS enforcement, HSTS
- [ ] SQL Injection: فحص جميع استخدامات raw SQL (النظام يستخدم raw SQL)
- [ ] XSS في frontend (dangerouslySetInnerHTML)
- [ ] Secrets في `.env` لا في الكود
- [ ] Logs لا تحتوي بيانات حساسة (كلمات مرور، tokens، PII)
- [ ] File upload: نوع الملف، الحجم، مسار التخزين
- [ ] Audit log للعمليات الحساسة

**Multi-tenancy**
- [ ] عزل قواعد البيانات `aman_{company_id}`
- [ ] منع cross-tenant queries
- [ ] التحقق من company_id في JWT claims

### KPIs
| المقياس | الهدف |
|---|---|
| endpoints محمية بـ `require_permission` | 100% من الحساسة |
| استعلامات raw SQL بدون parameterization | 0 |
| secrets في repo | 0 |
| endpoints بدون rate limit للدخول/التسجيل | 0 |
| ثغرات حرجة (Critical CVE) في dependencies | 0 |
| تغطية audit log للعمليات المالية | 100% |
| test cases أمنية | ≥ 20 |

### المخرجات
- `docs/audit/03-security.md` — التقرير الأمني
- `docs/audit/rbac-matrix.xlsx` — مصفوفة الصلاحيات
- `docs/audit/security-findings.csv` — الثغرات المُصنّفة
- `docs/audit/pen-test-cases.md` — حالات اختبار الاختراق المقترحة

---

## المرحلة 4: فحص النواة المالية (Financial Core)

### الهدف
ضمان صحة ودقة وتوازن جميع العمليات المحاسبية (Double Entry, Balance, Taxes, Treasury).

### نطاق الملفات
- `backend/routers/finance/**` — accounts, journal, invoices, expenses
- `backend/routers/treasury.py`, `backend/routers/banks.py`
- `backend/routers/tax*.py`, `backend/routers/currency*.py`
- `backend/routers/budgets.py`, `backend/routers/assets.py`
- `backend/routers/payroll.py` (جانب القيود)
- `backend/services/accounting/**` (إن وُجد)
- جداول: `accounts`, `journal_entries`, `journal_lines`, `invoices`, `invoice_lines`, `treasury_accounts`, `treasury_transactions`, `bank_reconciliations`, `tax_rates`, `currencies`, `fiscal_years`, `budgets`, `assets`, `expenses`, `expense_policies`
- `frontend/src/pages/finance/**`

### Checklist

**دليل الحسابات (Chart of Accounts)**
- [ ] هيكل شجري صحيح (parent_id)
- [ ] منع حذف حساب له رصيد أو حركات
- [ ] تصنيفات: Asset/Liability/Equity/Revenue/Expense
- [ ] ترقيم آلي متسق

**القيود المحاسبية (Journal Entries)**
- [ ] توازن Debit = Credit لكل قيد
- [ ] منع الترحيل على حسابات header/parent
- [ ] reversing entries تعمل بشكل صحيح
- [ ] ربط القيد بمصدره (Invoice, Payment, Payroll...)
- [ ] إغلاق الفترة يمنع التعديل
- [ ] عملة القيد، سعر الصرف، مبلغ بالعملة الأساسية

**الفواتير**
- [ ] حساب الضريبة (VAT) صحيح — inclusive vs exclusive
- [ ] خصم مدى الفاتورة / السطر
- [ ] ترحيل الفاتورة ينشئ قيدًا متوازنًا
- [ ] إلغاء/تعديل الفاتورة يعكس القيد
- [ ] ترقيم متسلسل قانوني (بدون فجوات)
- [ ] تقرير AR/AP aging

**الخزينة والبنوك**
- [ ] الإيداع/السحب/التحويل بين الحسابات
- [ ] التسوية البنكية (bank reconciliation) تطابق الكشوفات
- [ ] الشيكات: صادر/وارد، حالات (pending/cleared/bounced)
- [ ] أوراق القبض/الدفع (notes receivable/payable)

**الضرائب**
- [ ] جدول VAT صحيح (نسب، فئات: Standard/Zero/Exempt)
- [ ] WHT (withholding tax) إن وُجد
- [ ] تقارير ضريبية (Tax Return) تطابق المجاميع
- [ ] توافق ZATCA/E-invoicing (للسعودية)

**تعدد العملات**
- [ ] تحديث أسعار الصرف
- [ ] فروقات العملة (realized/unrealized gain/loss)
- [ ] إعادة تقييم الأرصدة في نهاية الفترة

**التقارير المالية**
- [ ] Trial Balance متوازن
- [ ] Balance Sheet = Assets = Liabilities + Equity
- [ ] Income Statement
- [ ] Cash Flow Statement
- [ ] تقرير الموازنة الفعلية vs المخططة
- [ ] تقارير الأصول والإهلاك

### KPIs
| المقياس | الهدف |
|---|---|
| قيود غير متوازنة في DB | 0 |
| فواتير بدون قيد مقابل | 0 |
| فجوات ترقيم الفواتير | 0 |
| انحراف Trial Balance | 0.00 |
| فروقات التسوية البنكية | 0 |
| accuracy حساب VAT في sample من 100 فاتورة | 100% |
| تغطية unit tests للوحدة المالية | ≥ 80% |
| فواتير معلقة الترحيل | موثّقة |

### المخرجات
- `docs/audit/04-finance.md` — التقرير المالي
- `docs/audit/finance-reconciliation.xlsx` — تسويات مرجعية
- `docs/audit/tax-compliance-report.md` — التوافق الضريبي
- `docs/audit/finance-findings.csv` — الملاحظات

---

## المرحلة 5: فحص العمليات التشغيلية (Operations)

### الهدف
ضمان صحة تدفق المواد/الطلبات من المشتريات → المخزون → المبيعات → POS → التسليم، وصحة ربطها بالمالية.

### نطاق الملفات
- `backend/routers/inventory*.py`, `warehouses.py`, `products.py`
- `backend/routers/purchase*.py` — PO, RFQ, GRN, supplier_ratings
- `backend/routers/sales*.py` — SO, SQ, SR, delivery
- `backend/routers/pos*.py` — sessions, orders, shifts
- `backend/routers/manufacturing*.py` — BOM, Work Orders
- `backend/routers/contracts*.py`
- `backend/routers/pricing*.py`, `customer_price_lists`
- جداول: `products`, `inventory`, `inventory_transactions`, `warehouses`, `stock_transfers`, `purchase_orders`, `sales_orders`, `pos_sessions`, `pos_orders`, `bom`, `work_orders`, `landed_costs`
- `frontend/src/pages/{inventory,sales,purchase,pos,manufacturing}/**`

### Checklist

**المخزون**
- [ ] حركات المخزون (IN/OUT/TRANSFER/ADJUSTMENT) تحافظ على الأرصدة
- [ ] دقة التكلفة: FIFO / Weighted Average / Standard (تطابق السياسة)
- [ ] Landed costs تُضاف للتكلفة بشكل صحيح
- [ ] Stock transfers بين المستودعات (in-transit)
- [ ] Reorder level & low stock alerts
- [ ] Serial/Batch tracking إن وُجد
- [ ] Expiry date للأصناف القابلة للانتهاء
- [ ] Stock count / physical inventory / adjustments

**المشتريات**
- [ ] دورة RFQ → PO → GRN → Invoice → Payment
- [ ] Three-way match (PO/GRN/Invoice)
- [ ] تسعير المورد، خصومات، شروط الدفع
- [ ] Supplier rating تحديث تلقائي

**المبيعات**
- [ ] دورة Quotation → SO → Delivery → Invoice → Payment
- [ ] قوائم أسعار العملاء (customer_price_lists)
- [ ] حجز المخزون عند SO (reservation)
- [ ] Sales returns وتأثيرها على المخزون والمالية
- [ ] Commissions للمندوبين

**POS**
- [ ] فتح/إغلاق الوردية (session) مع التسوية
- [ ] طرق الدفع المتعددة (cash/card/mixed)
- [ ] خصومات، عروض، كوبونات
- [ ] طباعة الفاتورة، QR code (ZATCA)
- [ ] العمل دون اتصال (offline mode) إن وُجد
- [ ] مزامنة عند عودة الاتصال

**التصنيع**
- [ ] BOM متعدد المستويات
- [ ] Work Order: materials issue, finished goods receipt
- [ ] احتساب تكلفة الإنتاج (material + labor + overhead)
- [ ] Scrap/Waste

**العقود والتسليم**
- [ ] دورة العقد: draft → active → expired/renewed
- [ ] ربط العقد بـ SO/Invoice
- [ ] Delivery orders وتتبع الحالة

### KPIs
| المقياس | الهدف |
|---|---|
| فروقات بين stock ledger و inventory table | 0 |
| PO بدون GRN ولا closure | موثّقة |
| SO بدون delivery ولا cancellation | موثّقة |
| دقة تكلفة المخزون في عينة 100 صنف | ≥ 99% |
| POS sessions بدون closure | 0 |
| Three-way match success rate | ≥ 95% |
| متوسط زمن استجابة POS checkout | < 500ms |
| تغطية tests للوحدات التشغيلية | ≥ 70% |

### المخرجات
- `docs/audit/05-operations.md` — التقرير التشغيلي
- `docs/audit/inventory-reconciliation.xlsx`
- `docs/audit/po-so-flow-findings.csv`
- `docs/audit/pos-audit.md`

---

## المرحلة 6: فحص الصحة التقنية (Technical Health)

### الهدف
تقييم جودة الكود، البنية، الأداء، الاختبارات، والبنية التحتية.

### نطاق الملفات
- كامل `backend/`, `frontend/`, `mobile/`
- `requirements.txt`, `package.json`, `pyproject.toml`
- `backend/tests/**`, `frontend/**/*.test.*`, `e2e/**`
- `alembic/**`, `database.py`
- `Dockerfile*`, `docker-compose*.yml`, `.github/workflows/**`
- ملفات CI/CD

### Checklist

**Build & Dependencies**
- [ ] `pip install` ينجح من requirements نظيفة
- [ ] `npm install` و`npm run build` ينجحان
- [ ] لا تبعيات deprecated حرجة
- [ ] فحص CVE (`pip-audit`, `npm audit`)
- [ ] توحيد lockfiles (poetry.lock / package-lock.json)

**Tests**
- [ ] تشغيل `pytest` — عدد الناجح/الفاشل/التخطي
- [ ] تشغيل `npm test`
- [ ] قياس coverage (backend/frontend)
- [ ] وجود integration tests
- [ ] وجود e2e tests (Playwright/Cypress)

**Code Quality**
- [ ] `ruff check .` على backend
- [ ] `mypy` إن كان مستخدمًا
- [ ] `eslint` / `tsc --noEmit` على frontend
- [ ] فحص التعقيد الدوراني (cyclomatic complexity)
- [ ] فحص التكرار (duplication)

**Database**
- [ ] جميع الـ migrations قابلة للتطبيق من الصفر
- [ ] `alembic upgrade head` ثم `downgrade base` يعمل
- [ ] FK ordering صحيح في `create_company_tables()`
- [ ] indexes على الأعمدة كثيرة الاستعلام
- [ ] لا N+1 queries في endpoints حرجة
- [ ] Materialized views تعمل (ملاحظة: 16 MV حاليًا معطلة)

**Performance**
- [ ] قياس p50/p95/p99 لـ 10 endpoints حرجة
- [ ] حجم bundle للـ frontend
- [ ] Lighthouse score
- [ ] استعلامات > 500ms

**Infrastructure**
- [ ] Docker images تُبنى وتعمل
- [ ] docker-compose up كامل النظام
- [ ] Redis, PostgreSQL, Backend, Frontend متصلون
- [ ] سياسة backup للـ DB
- [ ] monitoring & logging (structured logs)
- [ ] Health check endpoints

**Observability**
- [ ] Structured logging (JSON)
- [ ] Request ID / tracing
- [ ] Error reporting (Sentry/equivalent)
- [ ] Metrics (Prometheus/equivalent)

### KPIs
| المقياس | الهدف |
|---|---|
| نسبة نجاح pytest | ≥ 95% |
| Code coverage backend | ≥ 70% |
| Code coverage frontend | ≥ 60% |
| ثغرات CVE حرجة | 0 |
| تحذيرات ruff | < 50 |
| أخطاء eslint | 0 |
| حجم bundle | < 2MB gzipped |
| p95 latency للـ endpoints الحرجة | < 500ms |
| Docker build time | < 5min |
| MV معطلة | من 16 → 0 |

### المخرجات
- `docs/audit/06-tech-health.md`
- `docs/audit/test-coverage-report.html`
- `docs/audit/cve-report.json`
- `docs/audit/performance-baseline.csv`
- `docs/audit/lint-report.txt`

---

## المرحلة 7: فحص الوحدات الإدارية (HR, CRM, Projects, Approvals, etc.)

### الهدف
التحقق من اكتمال ودقة الوحدات الإدارية والمساندة، وتكاملها مع النواة.

### نطاق الملفات

**HR**
- `backend/routers/hr*.py`, `employees.py`, `payroll.py`, `attendance.py`, `leaves.py`, `performance*.py`
- جداول: `employees`, `departments`, `attendance`, `leave_requests`, `payroll_entries`, `employee_loans`, `review_cycles`, `performance_reviews`

**CRM**
- `backend/routers/crm*.py`, `customers.py`, `marketing*.py`
- جداول: `crm_customer_segments`, `marketing_campaigns`, `customer_groups`, `customer_price_lists`

**Projects**
- `backend/routers/projects*.py`, `tasks*.py`
- جداول: `projects`, `project_tasks`, `cost_centers`

**Approvals & Workflows**
- `backend/routers/approvals*.py`
- جداول: `approval_workflows`, `approval_requests`

**Notifications, Audit, Settings**
- `backend/routers/notifications*.py`, `audit*.py`, `settings*.py`, `print_templates*.py`
- `backend/routers/backup*.py`, `imports*.py`, `exports*.py`

**Mobile**
- `mobile/src/**`

### Checklist

**HR**
- [ ] دورة حياة الموظف (hire → active → terminated)
- [ ] الحضور والانصراف، OT, late, absence
- [ ] الإجازات (types, balance, approval)
- [ ] الرواتب: حساب الراتب، استقطاعات، بدلات، قيد الرواتب
- [ ] السلف (loans) وجدول السداد
- [ ] دورات المراجعة والتقييم
- [ ] تكامل مع Approvals (إجازة، سلفة، OT)

**CRM**
- [ ] تقسيم العملاء (segments)
- [ ] الحملات التسويقية
- [ ] قوائم الأسعار حسب الفئة
- [ ] سجل التواصل مع العميل (activities/notes)
- [ ] Pipeline المبيعات (stages)

**Projects**
- [ ] هيكل المشروع والمهام
- [ ] تتبع الوقت (time tracking) إن وُجد
- [ ] تكلفة المشروع الفعلية vs المخططة
- [ ] ربط المشروع بـ cost_centers و invoices

**Approvals**
- [ ] سلاسل الموافقات (parallel/sequential)
- [ ] SLA والتصعيد (escalation)
- [ ] auto-approve below threshold
- [ ] سجل قرارات الموافقة

**Notifications**
- [ ] إرسال إشعارات في الأحداث المهمة
- [ ] قنوات: in-app, email, SMS, WhatsApp
- [ ] تفضيلات المستخدم

**Audit Logs**
- [ ] تسجيل CREATE/UPDATE/DELETE للكيانات الحساسة
- [ ] من فعل ماذا ومتى (user, timestamp, before/after)
- [ ] حماية الـ audit log من التعديل

**Settings & Templates**
- [ ] إعدادات الشركة (logo, address, tax info)
- [ ] قوالب الطباعة (invoice, receipt, PO)
- [ ] i18n: ترجمة واجهات AR/EN، RTL/LTR

**Backup/Restore**
- [ ] تصدير DB لشركة
- [ ] استعادة DB
- [ ] Import/Export Excel/CSV

**Mobile**
- [ ] مسارات الدخول والصلاحيات
- [ ] شاشات: POS, Inventory, Approvals, HR self-service
- [ ] العمل دون اتصال + المزامنة

### KPIs
| المقياس | الهدف |
|---|---|
| موظفون بدون قسم أو منصب | 0 |
| قيود رواتب غير مرحّلة | 0 |
| approvals معلقة > SLA | يُقاس |
| notifications غير مرسلة | 0 |
| entities بدون audit log (حساسة) | 0 |
| i18n keys مفقودة (AR/EN) | 0 |
| شاشات mobile مكتملة | ≥ 90% |
| تغطية tests للوحدات الإدارية | ≥ 60% |

### المخرجات
- `docs/audit/07-admin-modules.md`
- `docs/audit/hr-compliance.md`
- `docs/audit/crm-gap-analysis.md`
- `docs/audit/approvals-matrix.md`
- `docs/audit/i18n-coverage.csv`
- `docs/audit/mobile-audit.md`

---

## المرحلة 8: تقرير الإغلاق التنفيذي و Backlog

### الهدف
دمج نتائج جميع المراحل في تقرير تنفيذي واحد مع خطة إصلاح مُرتّبة الأولويات.

### نطاق الملفات
- جميع مخرجات المراحل 1-7
- `docs/audit/**`

### Checklist
- [ ] دمج جميع الـ findings في سجل موحد
- [ ] تصنيف كل finding: Module / Severity / Effort / Impact
- [ ] حساب Risk Score = Severity × Impact / Effort
- [ ] تجميع الأنماط المتكررة (systemic issues)
- [ ] تحديد Quick Wins (أثر عالي، جهد منخفض)
- [ ] تحديد Strategic Items (أثر عالي، جهد عالي)
- [ ] بناء Roadmap زمني (Sprint 1, 2, 3...)
- [ ] تحديد dependencies بين المهام
- [ ] تقدير الجهد (story points / days)
- [ ] ملخص تنفيذي للإدارة (1 صفحة)
- [ ] مراجعة مع أصحاب المصلحة

### KPIs
| المقياس | الهدف |
|---|---|
| تغطية الـ findings بأولوية واضحة | 100% |
| عناصر P0 لها owner و ETA | 100% |
| عناصر Quick Wins محددة | ≥ 10 |
| Roadmap للربع القادم | جاهز |

### المخرجات
- `docs/audit/08-executive-report.pdf` — تقرير تنفيذي (≤ 10 صفحات)
- `docs/audit/backlog.xlsx` — Backlog مُصنّف بالكامل
- `docs/audit/roadmap.md` — خطة الإصلاح الزمنية
- `docs/audit/risk-register.xlsx` — سجل المخاطر

---

## ترتيب الأولويات النهائي للإصلاح (P0 → P3)

### P0 — Blocker (يجب الإصلاح فورًا، يمنع الإنتاج)
1. **ثغرات أمنية حرجة**: SQL Injection, Auth bypass, secrets مكشوفة, tenant leakage
2. **فقدان سلامة البيانات المالية**: قيود غير متوازنة، فواتير بدون قيد، فجوات ترقيم
3. **خلل في عزل Multi-tenancy**: أي تسرب بين الشركات
4. **فشل Build أو Migrations**: النظام لا يُنصب من الصفر
5. **فقدان بيانات محتمل**: عمليات حذف بدون حماية، لا backup

### P1 — High (يجب الإصلاح قبل الإطلاق/الإصدار القادم)
6. **ثغرات أمنية عالية**: XSS، CSRF، rate-limit ناقص، ضعف كلمات المرور
7. **أخطاء في النواة المالية**: حساب ضريبة خاطئ، تسوية بنكية لا تطابق، إهلاك خاطئ
8. **أخطاء تشغيلية تؤثر على الأرصدة**: تكلفة مخزون خاطئة، POS لا يُغلق، 3-way match مفقود
9. **غياب Audit Log** للعمليات الحساسة
10. **RBAC ناقص** على endpoints حرجة
11. **Materialized Views معطلة** (16 MV حاليًا)
12. **عدم توافق ZATCA/E-invoicing** (حسب السوق)

### P2 — Medium (يُجدوَل في السبرينت 2-3)
13. **ثغرات متوسطة**: logs تحتوي PII، CORS فضفاض
14. **Performance**: استعلامات بطيئة، N+1، غياب indexes
15. **UX/i18n**: ترجمات مفقودة، RTL issues
16. **Approvals workflows**: SLA، escalation، parallel
17. **تقارير ناقصة**: Cash Flow، Aging، Budget variance
18. **Mobile app**: شاشات ناقصة
19. **Test coverage** أقل من الهدف
20. **CVE متوسطة** في dependencies

### P3 — Low (Backlog عام، تحسينات)
21. **Code quality**: duplication، cyclomatic complexity
22. **Documentation**: README، API docs
23. **Observability**: metrics، tracing
24. **Refactoring**: كسر ملفات كبيرة (database.py ~6281 سطر)
25. **Nice-to-have features**: AI، BI متقدم، integrations إضافية

---

## تسلسل التنفيذ المقترح للمراحل

```
Week 1:   Phase 1 (Scope)          ──► Phase 2 (Baseline)
Week 2-3: Phase 3 (Security)       ║ Phase 6 (Tech Health)    [متوازيتان]
Week 4-5: Phase 4 (Finance)        ──► Phase 5 (Operations)
Week 6:   Phase 7 (Admin Modules)
Week 7:   Phase 8 (Executive Report + Backlog)
```

---

## أسئلة للمستخدم قبل البدء

1. **السوق المستهدف**: هل التوافق مع ZATCA (السعودية) مطلوب في هذه الدورة، أم فقط السوق السوري؟
2. **تطبيق الجوال**: هل هو ضمن النطاق أم مؤجل؟
3. **مستوى التعمق الأمني**: فحص ذاتي فقط أم اختبار اختراق خارجي (Pen-test)؟
4. **الموارد**: كم شخصًا/فريقًا سيُشارك في الفحص؟
5. **الجدول الزمني**: هل 7 أسابيع مقبول أم مطلوب تقصير/تمديد؟
6. **البيئة المستهدفة**: هل الفحص على بيئة dev فقط أم staging أيضًا؟
7. **معايير الامتثال**: هل هناك معايير خارجية (ISO 27001, SOC 2) يجب التحقق منها؟

---

**آخر تحديث:** 2026-04-20
**الحالة:** خطة جاهزة للتنفيذ — لم يبدأ أي فحص فعلي بعد.
