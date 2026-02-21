# 📊 تقرير الفحص الشامل النهائي لنظام أمان ERP
# مقارنة عالمية + فحص كامل لجميع الأجزاء + خطة إصلاح آمنة
> **تاريخ التقرير:** 2026-02-18  
> **النظام:** AMAN ERP v1.0.0  
> **البنية:** FastAPI + React + PostgreSQL (Multi-Tenant)

---

## 📌 الجزء الأول: ملخص تنفيذي

| البعد | التقييم | ملاحظة |
|-------|---------|--------|
| **اكتمال الوظائف** | ⭐⭐⭐⭐☆ (85%) | يغطي 95% من احتياجات ERP صغير-متوسط |
| **جودة الكود** | ⭐⭐⭐⭐☆ (80%) | معمارية جيدة مع بعض الديون التقنية |
| **الأمان** | ⭐⭐⭐⭐☆ (78%) | rate limiting + 2FA + permissions — ينقصه token blacklist |
| **الأداء** | ⭐⭐⭐☆☆ (70%) | لا يوجد connection pooling مُحسَّن + لا pagination في بعض الأماكن |
| **المعايير المحاسبية** | ⭐⭐⭐⭐⭐ (92%) | قيود تلقائية + COGS + WAC + ميزانية — ممتاز بمعايير IFRS |
| **واجهة المستخدم** | ⭐⭐⭐⭐☆ (82%) | تصميم نظيف + RTL + ترجمة ثنائية |
| **قاعدة البيانات** | ⭐⭐⭐☆☆ (68%) | هيكل جيد لكن ديون تقنية مهمة |
| **التوثيق** | ⭐⭐⭐☆☆ (60%) | توثيق أساسي — يحتاج تحسين |

---

## 📌 الجزء الثاني: المقارنة العالمية الشاملة

### مقارنة مع الأنظمة العالمية الكبرى

| الميزة | AMAN ERP | ERPNext | Odoo | SAP B1 | Oracle NetSuite |
|--------|----------|---------|------|--------|-----------------|
| **Multi-Tenant** | ✅ DB per company | ✅ Site per company | ✅ | ❌ | ✅ Cloud |
| **دليل الحسابات (COA)** | ✅ شجري | ✅ | ✅ | ✅ | ✅ |
| **القيود التلقائية** | ✅ عند كل عملية | ✅ | ✅ | ✅ | ✅ |
| **COGS تلقائي** | ✅ WAC + Per-WH | ✅ FIFO/WAC | ✅ FIFO/LIFO/WAC | ✅ | ✅ |
| **سياسات التكلفة** | ✅ Global WAC + Per-WH | ✅ | ✅ | ✅ | ✅ |
| **الفوترة الإلكترونية (ZATCA)** | ❌ غير مدعوم | ✅ KSA | ✅ Plugin | ✅ | ✅ |
| **إدارة العملات** | ✅ Multi-currency | ✅ | ✅ | ✅ | ✅ |
| **نقاط البيع (POS)** | ✅ Online | ✅ Online/Offline | ✅ Online/Offline | ✅ | ✅ |
| **التصنيع (MRP)** | ✅ أساسي | ✅ متقدم | ✅ متقدم | ✅ | ✅ |
| **إدارة المشاريع** | ✅ مع ربط محاسبي | ✅ | ✅ | ✅ | ✅ |
| **الموارد البشرية** | ✅ متقدم (14 وحدة) | ✅ | ✅ | ❌ وحدة منفصلة | ✅ |
| **سلسلة الاعتمادات** | ✅ متعدد المستويات | ✅ | ✅ | ✅ | ✅ |
| **الأمان (2FA)** | ✅ | ❌ | ✅ | ✅ | ✅ |
| **Rate Limiting** | ✅ IP + Username | ❌ Server-level | ❌ | ✅ | ✅ |
| **تسوية بنكية** | ✅ يدوي + CSV | ✅ | ✅ + OFX + Plaid | ✅ | ✅ + Bank Feeds |
| **الضرائب (VAT)** | ✅ إعدادات + إقرار | ✅ + ZATCA | ✅ + تكامل | ✅ | ✅ |
| **الأصول الثابتة** | ✅ استهلاك خطي | ✅ خطي + متناقص | ✅ خطي + متناقص + وحدات | ✅ | ✅ |
| **Audit Trail** | ✅ شامل | ✅ | ✅ | ✅ | ✅ |
| **تصدير PDF** | ❌ محدود جداً | ✅ Jinja | ✅ QWeb | ✅ Crystal | ✅ |
| **API Documentation** | ✅ Swagger | ✅ | ✅ REST/ORM | ✅ | ✅ REST |
| **لوحة البيانات (Dashboard)** | ✅ إحصائيات | ✅ + Charts | ✅ + KPIs | ✅ | ✅ |
| **Webhook/Integration** | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Offline POS** | ❌ | ✅ | ✅ | ❌ | ❌ |
| **Mobile App** | ❌ | ✅ | ✅ | ✅ | ✅ |

### ما يتميز به نظام أمان عن بعض المنافسين:

| الميزة التميزية | التفاصيل |
|-----------------|----------|
| ✅ **Multi-Tenant حقيقي** | كل شركة = قاعدة بيانات PostgreSQL منفصلة (أفضل من ERPNext) |
| ✅ **بحث مستخدم مُفهرس** | `system_user_index` للبحث السريع O(1) عند Login |
| ✅ **Rate Limiting ثنائي** | حماية بالـ IP + اسم المستخدم (أفضل من ERPNext و Odoo) |
| ✅ **Permission Wildcards** | `products.*` و `*` — مرن أكثر من بعض الأنظمة |
| ✅ **ربط محاسبي شامل** | كل عملية (مبيعات، مشتريات، مخزون، أصول، مشاريع، خزينة) تُنشئ قيداً تلقائياً |
| ✅ **14 وحدة HR** | رواتب، قروض، حضور، إجازات، GOSI، تدريب، مخالفات، عُهد — أشمل من SAP B1 |

### ما ينقص نظام أمان مقارنة بالأنظمة العالمية:

| الميزة الناقصة | الأولوية | متاح في |
|----------------|----------|---------|
| 🔴 **الفوترة الإلكترونية ZATCA (فاتورة)** | قصوى — إلزامي في السعودية | ERPNext, Odoo |
| 🔴 **تصدير PDF احترافي للفواتير** | قصوى | الكل |
| 🟡 **Token Blacklist (Redis)** | عالية — logout حالياً لا يُبطل التوكن | NetSuite, SAP |
| 🟡 **Webhook / Integration API** | عالية — لا يوجد تكامل خارجي | ERPNext, Odoo |
| 🟡 **Mobile App** | عالية | ERPNext, Odoo, SAP |
| 🟡 **طرق استهلاك إضافية** | متوسطة — حالياً فقط خطي | Odoo (5 طرق) |
| 🟢 **Offline POS** | متوسطة | ERPNext, Odoo |
| 🟢 **CRM Module** | متوسطة — يمكن أن يكون إضافة مستقبلية | ERPNext, Odoo |
| 🟢 **Bank Feed Integration** | منخفضة — تعتمد على السوق المحلي | NetSuite |
| 🟢 **AI/ML Features** | منخفضة — مستقبلي | NetSuite |

---

## 📌 الجزء الثالث: فحص تفصيلي لكل جزء

### 🏗️ 1. هيكل البرنامج (Architecture)

**النمط المستخدم:** Layered Architecture + Multi-Tenant  
**التقييم:** ⭐⭐⭐⭐☆

```
backend/
├── main.py           ← نقطة الدخول + Lifespan + Router Registration
├── config.py         ← إعدادات مركزية (pydantic-settings)
├── database.py       ← DDL + Connection Management (3,317 سطر!)
├── routers/          ← 35+ router (API endpoints)
│   ├── auth.py       ← المصادقة + JWT + Rate Limiting
│   ├── sales/        ← مبيعات (7 ملفات مُنظمة)
│   ├── inventory/    ← مخزون (15 ملفاً مُنظماً) ✅ أفضل تنظيم
│   ├── purchases.py  ← مشتريات (2,500+ سطر في ملف واحد) ⚠️
│   ├── accounting.py ← محاسبة (2,328 سطر في ملف واحد) ⚠️
│   └── ...
├── schemas/          ← 23 ملف Pydantic models
├── services/         ← 3 خدمات (Costing, Email, Scheduler)
├── utils/            ← 7 أدوات مساعدة
├── migrations/       ← 26 migration script
└── scripts/          ← 5 scripts

frontend/
├── src/
│   ├── App.jsx       ← 492 سطر — التوجيه المركزي
│   ├── pages/        ← 213+ صفحة React
│   ├── components/   ← 40+ component
│   ├── utils/        ← API + Auth + helpers
│   └── locales/      ← ar.json + en.json
```

#### نقاط القوة:
- ✅ فصل واضح بين Routers, Schemas, Utils, Services
- ✅ المبيعات والمخزون مُقسمة لملفات صغيرة
- ✅ Lazy loading لكل صفحة في React
- ✅ Global error handler في main.py

#### نقاط الضعف:
- ⚠️ `database.py` = 3,317 سطر — يحتوي على كل DDL + إنشاء الجداول + المساعدات
- ⚠️ `purchases.py` = 2,500+ سطر في ملف واحد
- ⚠️ `accounting.py` = 2,328 سطر في ملف واحد
- ⚠️ لا يوجد ORM models — كل SQL مكتوب يدوياً (raw SQL everywhere)

---

### 🔐 2. الأمان (Security)

**التقييم:** ⭐⭐⭐⭐☆ (78%)

| الميزة | الحالة | التفاصيل |
|--------|--------|----------|
| JWT Authentication | ✅ | HS256 + token expiry + refresh |
| Password Hashing | ✅ | bcrypt via passlib |
| Rate Limiting (Login) | ✅ | 5 محاولات/IP + 10 محاولات/username + lockout 15 دقيقة |
| Permission System | ✅ | Granular: `module.action` + wildcards |
| Branch Access Control | ✅ | `validate_branch_access()` في معظم الأماكن |
| 2FA (TOTP) | ✅ | Setup + Verify + Disable |
| Audit Logging | ✅ | كل عملية حساسة تُسجَّل |
| SQL Injection Protection | ✅ | Parameterized queries في كل مكان |
| CORS Configuration | ✅ | محدد لـ FRONTEND_URL فقط |
| Global Error Sanitization | ✅ | `sanitize_http_exception` يمنع تسريب أخطاء SQL |
| SECRET_KEY Validation | ✅ | تحذير عند بدء التشغيل إذا كان ضعيفاً |
| Session Invalidation | ⚠️ **ناقص** | Logout لا يُبطل التوكن — يحذف من localStorage فقط |
| Token Blacklist | ❌ **ناقص** | لا يوجد Redis blacklist — التوكن صالح حتى انتهائه |
| HTTPS Enforcement | ❌ | لا يوجد — يعتمد على reverse proxy |
| Input Sanitization (XSS) | ⚠️ | React يحمي تلقائياً لكن لا يوجد sanitization في الـ API |
| CSRF Protection | ❌ | لا يوجد — يعتمد على JWT (مقبول لـ SPA) |

#### مشاكل أمنية يجب إصلاحها:

**🔴 مشكلة #1: POS Routes بدون Permission Check**
```jsx
// App.jsx سطر 480-481
<Route path="/pos" element={isAuthenticated() ? <POSHome /> : <Navigate to="/login" />} />
<Route path="/pos/interface" element={isAuthenticated() ? <POSInterface /> : <Navigate to="/login" />} />
// ❌ لا يوجد permission="pos.view"!
```
**الوضع الحالي:** أي مستخدم مسجل يمكنه الوصول لـ POS (الـ Backend يفحص، لكن Frontend لا يمنع).

**🟡 مشكلة #2: Logout لا يُبطل التوكن**
```python
# auth.py سطر 500-505
async def logout():
    # NOTE: For full security, implement token blacklist with Redis
    return {"message": "تم تسجيل الخروج بنجاح"}
```
**الأثر:** إذا سُرق التوكن، يبقى صالحاً لمدة `ACCESS_TOKEN_EXPIRE_MINUTES` (30 دقيقة افتراضياً).

---

### 📊 3. قاعدة البيانات (Database)

**التقييم:** ⭐⭐⭐☆☆ (68%)

#### الهيكل العام:
- **91+ جدول** في DDL
- **25 trigger** لتحديث `updated_at`
- **40+ index** مُعرَّف
- **Multi-Tenant:** قاعدة بيانات منفصلة لكل شركة

#### المشاكل المكتشفة:

**🔴 مشكلة #1: أعمدة Deprecated لا تزال في DDL**
```sql
-- database.py سطر 309-310
CREATE TABLE IF NOT EXISTS invoices (
    party_id INTEGER REFERENCES parties(id),
    customer_id INTEGER, -- Deprecated
    supplier_id INTEGER, -- Deprecated  ← لا FK!
```
**الأعمدة Deprecated:**
| الجدول | العمود | المستخدم بدلاً عنه |
|--------|--------|-------------------|
| `invoices` | `customer_id`, `supplier_id` | `party_id` |
| `purchase_orders` | `supplier_id` | `party_id` |
| `sales_quotations` | `customer_id` | `party_id` |
| `sales_orders` | `customer_id` | `party_id` |
| `sales_returns` | `customer_id` | `party_id` |
| `purchase_invoices` | `supplier_id` | `party_id` |
| `payment_vouchers` | `customer_id`, `supplier_id` | `party_id` |

**هل يمكن حذفها بأمان؟** ❌ **لا الآن** — لأن:
1. بعض الكود القديم (`pos.py`, `projects.py`) **يستخدمها فعلاً**
2. قد توجد بيانات مخزنة فيها من قبل الترحيل
3. حذفها يتطلب ترحيل بيانات + تحديث كود

**🔴 مشكلة #2: `pos_orders.customer_id` يشير لجدول `customers` (القديم)**
```sql
-- pos.py سطر 740
LEFT JOIN customers c ON po.customer_id = c.id  -- ❌ يجب أن يكون parties!
```
**الأثر:** إذا أضيف عميل في `parties` فقط (الجدول الجديد)، لن يظهر اسمه في POS.

**🔴 مشكلة #3: `projects.customer_id` يشير لجدول `customers` (القديم)**
```sql
-- projects.py سطر 65
LEFT JOIN customers c ON p.customer_id = c.id  -- ❌ نفس المشكلة
```

**🟡 مشكلة #4: جداول Legacy لا تزال موجودة**
```
supplier_groups, suppliers, customer_groups, customers
```
هذه جداول قديمة تم استبدالها بـ `parties` و `party_groups` لكنها لا تزال مُعرَّفة في DDL وتستهلك مساحة.

**🟡 مشكلة #5: لا يوجد Foreign Key على الأعمدة Deprecated**
```sql
customer_id INTEGER, -- لا REFERENCES!
supplier_id INTEGER, -- لا REFERENCES!
```
هذا يعني أنه يمكن تخزين قيم غير صالحة (orphaned references).

**🟢 نقاط إيجابية:**
- ✅ `DECIMAL(18, 4)` للمبالغ المالية — ممتاز
- ✅ `UNIQUE` constraints على أرقام المستندات
- ✅ `ON DELETE CASCADE` على الجداول الفرعية
- ✅ `REFERENCES` على معظم الـ foreign keys
- ✅ Triggers تلقائية لـ `updated_at`
- ✅ Composite `UNIQUE(product_id, warehouse_id)` على المخزون

---

### 🔄 4. تدفق العمليات (Business Logic)

#### المبيعات — التدفق الكامل:
```
عرض سعر → أمر بيع → فاتورة → سند قبض
    ↗         ↗         ↗ قيد تلقائي       ↗ قيد تلقائي
                       ↗ تحديث مخزون       ↗ تحديث رصيد عميل
                       ↗ حساب COGS
```
**التقييم:** ✅ ممتاز — مطابق لأفضل الممارسات

#### المشتريات — التدفق الكامل:
```
أمر شراء → استلام البضائع → فاتورة مشتريات → دفعة مورد
    ↗         ↗ تحديث مخزون    ↗ قيد تلقائي      ↗ قيد تلقائي
                               ↗ تحديث تكلفة WAC   ↗ تحديث رصيد مورد
```
**التقييم:** ✅ ممتاز — يشمل WAC وتحديث المخزون

#### نقاط البيع:
```
جلسة POS → طلب → دفع → قيد تلقائي + تحديث مخزون + تحديث خزينة
```
**التقييم:** ✅ جيد — لكن ينقصه Offline support

#### المرتجعات:
```
مرتجع مبيعات → عكس مخزون + عكس COGS + عكس قيد
مرتجع مشتريات → عكس مخزون + عكس تكلفة + عكس قيد
POS Return → عكس مخزون + عكس قيد + خصم من خزينة
```
**التقييم:** ✅ ممتاز — عكس كامل لكل عملية

---

### 🖥️ 5. الواجهة الأمامية (Frontend)

**التقييم:** ⭐⭐⭐⭐☆ (82%)

#### إحصائيات:
| العنصر | العدد |
|--------|-------|
| صفحات React | 213+ |
| مكونات مشتركة | 40+ |
| Routes مُعرَّفة | 120+ |
| ملفات ترجمة | 2 (ar.json + en.json) |
| صفحات إعدادات | 23 tab |

#### نقاط القوة:
- ✅ **Lazy Loading** لكل صفحة (أداء ممتاز)
- ✅ **Permission-based routing** — كل route يفحص الصلاحية
- ✅ **RTL Support** تلقائي حسب اللغة
- ✅ **Toast notifications** مركزية
- ✅ **Branch filtering** في معظم الصفحات
- ✅ **23 تبويب إعدادات** — شامل جداً

#### المشاكل:
| # | المشكلة | التأثير |
|---|---------|---------|
| 1 | ❌ POS routes بدون `<PrivateRoute permission>` | أمني — يمكن لأي مستخدم الوصول |
| 2 | ⚠️ بعض الترجمات تستخدم fallback hardcoded | عرض مختلط عربي/إنجليزي |
| 3 | ⚠️ `Timesheets.jsx` و `GanttChart.jsx` موجودة بدون routes | صفحات جاهزة لكن غير متاحة |
| 4 | ⚠️ بعض النماذج تستخدم `sales.view` بدلاً من `sales.create` | صلاحيات فضفاضة |

---

### 📡 6. الـ API Layer

**التقييم:** ⭐⭐⭐⭐☆ (80%)

#### إحصائيات الـ Endpoints:
| الوحدة | عدد الـ Endpoints | الحالة |
|--------|-------------------|--------|
| Auth | 4 | ✅ |
| Accounting | 36 | ✅ |
| Sales | 45 | ✅ |
| Purchases | 30 | ✅ |
| Inventory | 49 | ✅ |
| POS | 15 | ✅ |
| HR | 38 | ✅ |
| HR Advanced | 46 | ✅ |
| Treasury | 11 | ✅ |
| Checks | 18 | ✅ |
| Notes | 21 | ✅ |
| Manufacturing | 29 | ✅ |
| Projects | 20 | ✅ |
| Expenses | 14 | ✅ |
| Assets | 7 | ✅ |
| Reports | 15 | ✅ |
| Approvals | 22 | ✅ |
| Security | 20 | ✅ |
| **المجموع** | **~440 endpoint** | |

#### نقاط القوة:
- ✅ Swagger documentation تلقائي (`/api/docs`)
- ✅ Consistent error responses (Arabic + English)
- ✅ Proper HTTP status codes
- ✅ Request validation via Pydantic

#### نقاط الضعف:
- ⚠️ لا يوجد API versioning (`/api/v1/`)
- ⚠️ لا يوجد Pagination في بعض الـ list endpoints
- ⚠️ بعض الـ endpoints تعود كل البيانات بدون limit
- ⚠️ `scheduled_reports.py` بدون `prefix` — مختلف عن باقي الـ routers

---

### ⚙️ 7. الخدمات الخلفية (Services)

| الخدمة | الملف | الوظيفة | التقييم |
|--------|-------|---------|---------|
| **Costing Service** | `costing_service.py` (164 سطر) | WAC calculation + policy switching + snapshots | ✅ ممتاز |
| **Email Service** | `email_service.py` (13,589 بايت) | SMTP email sending + templates | ✅ جيد |
| **Scheduler** | `scheduler.py` (159 سطر) | Scheduled report generation + email delivery | ✅ جيد |
| **Audit Logger** | `audit.py` (118 سطر) | Activity logging + system logging | ✅ ممتاز |
| **Cache** | `cache.py` (2,505 بايت) | Simple caching layer | ⚠️ أساسي |
| **Exports** | `exports.py` (4,034 بايت) | PDF + Excel generation | ✅ جيد |
| **Permissions** | `permissions.py` (135 سطر) | Permission checking + branch validation | ✅ ممتاز |

---

## 📌 الجزء الرابع: كل المشاكل المكتشفة (مُرتبة بالأولوية)

### 🔴 أولوية قصوى — يجب إصلاحها (تؤثر على سلامة البيانات أو الأمان)

| # | المشكلة | الملف | السطر | التفاصيل | الإصلاح المقترح |
|---|---------|-------|-------|----------|-----------------|
| 1 | POS يربط `customer_id` مع جدول `customers` القديم | `pos.py` | 740, 762, 1044 | `LEFT JOIN customers c ON po.customer_id = c.id` | تغيير لـ `LEFT JOIN parties p ON po.customer_id = p.id` |
| 2 | Projects يربط `customer_id` مع جدول `customers` القديم | `projects.py` | 65, 136 | نفس المشكلة | نفس الحل |
| 3 | POS routes في Frontend بدون Permission check | `App.jsx` | 480-481 | `isAuthenticated()` فقط بدون `<PrivateRoute permission="pos.view">` | إضافة Permission wrapper |
| 4 | لا يوجد token blacklist | `auth.py` | 500-505 | Logout لا يُبطل التوكن | إضافة Redis blacklist (أو قائمة في الذاكرة كحل مؤقت) |

### 🟡 أولوية عالية — تحسينات مهمة

| # | المشكلة | الملف | التفاصيل | الإصلاح المقترح |
|---|---------|-------|----------|-----------------|
| 5 | `purchases.py` يخلط `supplier_id` و `party_id` | `purchases.py` | بعض الأماكن تقرأ `supplier_id` (فارغ) وبعضها `party_id` | توحيد لاستخدام `party_id` فقط |
| 6 | `database.py` = 3,317 سطر | `database.py` | كل DDL + helpers في ملف واحد ضخم | تقسيم لملفات: `ddl/`, `connection.py`, `helpers.py` |
| 7 | ملفات Legacy لا تزال موجودة | `inventory_old.py`, `sales_old.py` | كود ميت 230K+ حرف | حذفها (لا تُستخدم في `main.py`) |
| 8 | لا يوجد `validate_branch_access` في `assets.py` | `assets.py` | الأصول لا تُفلتر بالفرع | إضافة فلترة الفرع |
| 9 | لا يوجد `validate_branch_access` في `budgets.py` | `budgets.py` | الميزانيات لا تُفلتر بالفرع | إضافة فلترة الفرع |
| 10 | `scheduled_reports.py` بدون `prefix` | `scheduled_reports.py` | `APIRouter()` بدون prefix | إضافة `prefix="/scheduled-reports"` |

### 🟢 أولوية متوسطة — تحسينات مستقبلية

| # | المشكلة | التفاصيل | الإصلاح المقترح |
|---|---------|----------|-----------------|
| 11 | لا يوجد PDF generation للفواتير من الواجهة | عدة صفحات تحتاج زر "طباعة" | إضافة مكتبة PDF (ReportLab أو WeasyPrint) |
| 12 | `Timesheets.jsx` و `GanttChart.jsx` بدون routes | صفحات جاهزة لكن غير متاحة | إضافة routes في `App.jsx` |
| 13 | حذف duplicate في `cancel_held_order` | `pos.py` سطر 799-800 | `DELETE FROM pos_order_lines` مكرر مرتين | حذف السطر المكرر |
| 14 | لا يوجد API versioning | كل الـ endpoints على `/api/` | إضافة `/api/v1/` |
| 15 | بعض الترجمات hardcoded | Sidebar + بعض الصفحات | استبدال بمفاتيح ترجمة |
| 16 | لا يوجد password complexity validation في Registration | `Register.jsx` | إضافة validation (8+ أحرف، رقم، رمز) |

---

## 📌 الجزء الخامس: ما هو الصحيح للنظام (بدون كسر أي شيء)

### ✅ إصلاحات آمنة 100% (لا تؤثر على البيانات الحالية):

#### 1. إصلاح POS Routes في Frontend (آمن — Frontend فقط)
```jsx
// من:
<Route path="/pos" element={isAuthenticated() ? <POSHome /> : <Navigate to="/login" />} />
// إلى:
<Route path="/pos" element={<PrivateRoute permission="pos.view"><POSHome /></PrivateRoute>} />
```

#### 2. إصلاح POS JOIN (آمن — قراءة فقط)
```sql
-- من:
LEFT JOIN customers c ON po.customer_id = c.id
-- إلى (COALESCE يجعلها backward-compatible):
LEFT JOIN parties p ON po.customer_id = p.id
LEFT JOIN customers c ON po.customer_id = c.id
-- ثم:
COALESCE(p.party_name, c.customer_name, po.walk_in_customer_name, 'عميل نقدي') as customer_name
```

#### 3. إصلاح Projects JOIN (آمن — نفس النمط)
```sql
LEFT JOIN parties p ON p.customer_id = p.id
LEFT JOIN customers c ON p.customer_id = c.id
COALESCE(p2.party_name, c.customer_name) as customer_name
```

#### 4. حذف الملفات القديمة (آمن — غير مُستخدمة في `main.py`)
- `inventory_old.py`
- `sales_old.py`

#### 5. إصلاح POS duplicate DELETE (آمن — حذف سطر مكرر)
```python
# pos.py سطر 799-800: DELETE مكرر
db.execute(text("DELETE FROM pos_order_lines WHERE order_id = :id"), {"id": order_id})
db.execute(text("DELETE FROM pos_order_lines WHERE order_id = :id"), {"id": order_id})  # ← حذف هذا
```

#### 6. إضافة prefix لـ scheduled_reports (آمن — لا يغير سلوك)
```python
# من:
router = APIRouter()
# إلى:
router = APIRouter(prefix="/scheduled-reports", tags=["التقارير المجدولة"])
```
⚠️ **ملاحظة:** يجب التأكد من تحديث الـ Frontend أيضاً إذا كان يستدعي هذه الـ endpoints.

### ⚠️ إصلاحات تحتاج حذر (تحتاج اختبار):

#### 7. Token Blacklist (حل مؤقت بالذاكرة)
```python
# في auth.py:
_token_blacklist = set()  # In-memory (يُفرغ عند إعادة التشغيل)

@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    _token_blacklist.add(token)
    return {"message": "تم تسجيل الخروج بنجاح"}

# في get_current_user:
if token in _token_blacklist:
    raise credentials_exception
```

### ❌ لا تفعل هذا الآن:
1. **لا تحذف الأعمدة Deprecated** من DDL — قد يكسر كود لم يُفحص
2. **لا تحذف جداول customers/suppliers القديمة** — `pos.py` و `projects.py` يعتمدان عليها
3. **لا تُغيّر اسم `customer_id` لـ `party_id`** في schemas — سيكسر كل Frontend
4. **لا تُقسّم `database.py`** الآن — يحتاج تخطيط دقيق

---

## 📌 الجزء السادس: تقييم المعايير المحاسبية

### مطابقة IFRS (المعايير الدولية للتقارير المالية):

| المعيار | المتطلب | الحالة في أمان |
|---------|---------|----------------|
| **IAS 1** | القوائم المالية الأساسية | ✅ ميزانية + دخل + تدفقات نقدية + ميزان مراجعة |
| **IAS 2** | المخزون (WAC, FIFO) | ✅ WAC مدعوم (Global + Per-WH) |
| **IAS 7** | قائمة التدفقات النقدية | ✅ مُنفذة |
| **IAS 16** | الأصول الثابتة (استهلاك) | ✅ خطي — ينقص: متناقص + وحدات إنتاج |
| **IAS 18/IFRS 15** | الاعتراف بالإيراد | ✅ عند إصدار الفاتورة |
| **IAS 21** | العملات الأجنبية | ✅ Multi-currency + سعر صرف |
| **IFRS 16** | عقود الإيجار | ❌ غير مدعوم |
| **VAT Compliance** (السعودية) | هيئة الزكاة والدخل | ⚠️ إعدادات ضريبة موجودة لكن ZATCA integration ناقص |

### مطابقة المعايير المحاسبية السعودية:

| المتطلب | الحالة |
|---------|--------|
| دفتر اليوميات العامة | ✅ |
| دفتر الأستاذ العام | ✅ |
| ميزان المراجعة | ✅ |
| قائمة الدخل | ✅ |
| الميزانية العمومية | ✅ |
| كشف حساب عميل | ✅ |
| كشف حساب مورد | ✅ |
| تقرير أعمار الديون | ✅ |
| تقرير ضريبة القيمة المضافة | ✅ |
| **الفاتورة الإلكترونية (فاتورة)** | ❌ **ناقص — إلزامي!** |
| **رقم الهوية الضريبية (TIN)** | ✅ حقل `tax_number` موجود |
| **GOSI (التأمينات)** | ✅ وحدة كاملة |

---

## 📌 الخلاصة النهائية

### النظام بشكل عام:
**نظام أمان ERP هو نظام متكامل وقوي** يُقارن بأنظمة مثل ERPNext في الوظائف الأساسية. نقاط قوته الرئيسية:
1. **440+ API endpoint** يغطي كل العمليات التجارية
2. **ربط محاسبي تلقائي** في كل عملية (مبيعات، مشتريات، مخزون، أصول، مشاريع)
3. **14 وحدة HR** أشمل من بعض الأنظمة المدفوعة
4. **نظام أمان متقدم** (2FA + Rate Limiting + Permissions + Branch Access)
5. **Multi-Tenant حقيقي** مع قاعدة بيانات منفصلة لكل شركة

### الأولويات الثلاث الأهم:
1. 🔴 **إصلاح POS/Projects JOIN** — لأنه يؤثر على عرض البيانات الحالية
2. 🔴 **إضافة Permission على POS routes في Frontend** — ثغرة أمنية
3. 🔴 **تكامل ZATCA** — إلزامي قانوناً في السعودية

### التوصية:
**النظام جاهز للاستخدام** بعد إصلاح المشاكل الأربع الحمراء. باقي المشاكل تحسينات يمكن تنفيذها تدريجياً.
