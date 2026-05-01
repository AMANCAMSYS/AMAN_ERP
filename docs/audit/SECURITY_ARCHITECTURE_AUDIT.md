# تقرير الفحص الأمني والهيكلي الشامل (Security & Architecture)
# Comprehensive Security & Architecture Audit Report

> **التاريخ**: 2026-04-28
> **النطاق**: SQL Injection, XSS/CSRF, Authorization, Encryption, Error Handling, SOLID/Clean Architecture
> **المراجع**: مراجع كود أولي (Lead Code Auditor)

---

## 1. ثغرات SQL Injection

| # | الملف | السطر | الخطر | التفصيل |
|---|-------|-------|-------|---------|
| **1.1 ثغرة حرجة: اسم الجدول من مدخلات غير موثوقة** ||||
| 1.1.1 | `data_import.py` | 246, 254, 262, 267 | 🔴 CRITICAL | `config['table']` يُمرر مباشرة إلى SQL بدون تحقق. `IMPORT_CONFIGS` معرفة في الكود (مصدر موثوق)، لكن `entity_type` من المستخدم يُستخدم لاختيار config. إذا تسلل config خبيث أو أُضيف عن طريق الخطأ، يمكن حقن اسم جدول |

```python
# الكود الحالي (غير آمن):
existing = db.execute(text(f"""
    SELECT id FROM {config['table']} WHERE {unique_key} = :ukey
"""), {"ukey": params[unique_key]}).fetchone()

# الإصلاح:
from utils.sql_safety import validate_sql_identifier
validate_sql_identifier(config['table'], "table name")  # أضف هذا السطر قبل الاستعلام
```

| 1.1.2 | `data_import.py` | 340 | 🔴 CRITICAL | `SELECT {col_list} FROM {config['table']}` — اسم الجدول غير محقق. الأعمدة تم التحقق منها (سطر 236) لكن الجدول لا |


| **1.2 Dynamic UPDATE SET clauses (~40+ موقعًا)** ||||
| 1.2.1 | `roles.py` | 820 | 🟠 HIGH | `UPDATE roles SET {', '.join(updates)} WHERE id = :id` — أسماء الأعمدة من `data.dict(exclude_unset=True)` (مدخلات المستخدم). لا يوجد `validate_sql_identifier` |
| 1.2.2 | `crm.py` | 264, 499, 763, 1201, 1285, 1471, 1650 | 🟠 HIGH | 7 مواقع في CRM تستخدم `f"UPDATE table SET {set_clause} WHERE id = :id"` — أسماء الأعمدة من مفاتيح dict مدخلات المستخدم |
| 1.2.3 | `projects.py` | 1005, 1175, 1735, 2307, 2731, 2961, 3375 | 🟠 HIGH | 7 مواقع في المشاريع بنفس النمط |
| 1.2.4 | `pos.py` | 1245, 1545, 1645 | 🟠 HIGH | 3 مواقع في POS بنفس النمط |
| 1.2.5 | `advanced.py` (HR) | 88, 174, 596, 694, 762, 826, 907, 989 | 🟠 HIGH | 8 مواقع في HR Advanced بنفس النمط |

**نمط الإصلاح الموحد**:
```python
# قبل كل f"UPDATE table SET {updates}" أضف:
from utils.sql_safety import validate_sql_identifier
for field_name in updates_dict.keys():
    validate_sql_identifier(field_name, "column name")
```

| **1.3 Materialized View names** ||||
| 1.3.1 | `dashboard.py` | 1174-1188 | 🟡 MEDIUM | `f"SELECT ... FROM {mv_name}"` — أسماء MV من مصفوفة ثابتة في الكود (آمنة حاليًا لكن النمط خطر إذا تغير المصدر) |

---

## 2. ثغرات XSS و CSRF في الواجهة الأمامية

| # | الملف | السطر | الخطر | التفصيل |
|---|-------|-------|-------|---------|
| **2.1 XSS عبر document.write** ||||
| 2.1.1 | `ThermalPrintSettings.jsx` | 150 | 🟠 HIGH | `win.document.write(...)` — بيانات من state/react props تمرر عبر template literals. إذا كانت بيانات المنتج/العميل غير موثوقة (يدخلها المستخدم)، فهي قابلة للحقن |
| 2.1.2 | `CustomerDisplay.jsx` | 145 | 🟠 HIGH | نفس النمط — `document.write` مع template literals تحتوي على بيانات من state |
| **2.2 استخدام innerHTML (محمي بـ DOMPurify)** ||||
| 2.2.1 | `Payslips.jsx` | 118 | 🟡 LOW | `innerHTML` مع `DOMPurify.sanitize()` — آمن ✅ |
| 2.2.2 | `WithholdingTax.jsx` | 188 | 🟡 LOW | `innerHTML` مع `DOMPurify.sanitize()` — آمن ✅ |
| 2.2.3 | `InvoicePrintModal.jsx` | 63 | 🟡 LOW | `innerHTML` مع `DOMPurify.sanitize()` — آمن ✅ |
| **2.3 CSRF** ||||
| 2.3.1 | `csrf_middleware.py` | 1-107 | ✅ | Double-submit cookie pattern مع 3 مستويات (off/permissive/strict). يستثني SSO, mobile, API endpoints. مقارنة constant-time ✅ |
| 2.3.2 | `apiClient.js` | 117-126 | ✅ | إرسال `X-CSRF-Token` هيدر مع طلبات POST/PUT/PATCH/DELETE ✅ |
| **2.4 تخزين JWT في localStorage** ||||
| 2.4.1 | `auth.js` | 14 | 🟠 HIGH | `localStorage.getItem('token')` — Access Token مخزن في localStorage (عرضة لـ XSS). Refresh token في HttpOnly cookie ✅، لكن access token لا يزال في localStorage |

```js
// الإصلاح الموصى: تخزين access token في memory فقط
let inMemoryToken = null;
export function setToken(token) { inMemoryToken = token; }
export function getToken() { return inMemoryToken || localStorage.getItem('token'); }
// مع BFF (Backend-for-Frontend) pattern أو Service Worker
```

---

## 3. التحقق من الصلاحيات (Authorization)

| # | الملف | السطر | الخطر | التفصيل |
|---|-------|-------|-------|---------|
| **3.1 صلاحيات ضعيفة جدًا للعمليات التدميرية** ||||
| 3.1.1 | `invoices.py` | 756 | 🔴 CRITICAL | `POST /invoices/{id}/cancel` يستخدم `sales.create` — نفس صلاحية إنشاء الفاتورة. أي كاشير يمكنه إلغاء أي فاتورة |
| 3.1.2 | `returns.py` | 92, 224 | 🔴 CRITICAL | إنشاء + اعتماد المرتجعات بـ `sales.create` — لا فصل بين المسودة والاعتماد |
| 3.1.3 | `credit_notes.py` | 150 | 🔴 CRITICAL | إشعار دائن بـ `sales.create` — يُنشئ قيدًا محاسبيًا ويُعدل رصيد العميل |
| **3.2 صلاحية عرض البيانات المالية واسعة جدًا** ||||
| 3.2.1 | `core.py` (HR) | 214 | 🔴 CRITICAL | `GET /employees/{id}` يعيد salary, bank_account, IBAN لأي مستخدم لديه `hr.view` |
| 3.2.2 | `core.py` (HR) | 1878 | 🟠 HIGH | `GET /payslips` يعرض رواتب جميع الموظفين لأي مستخدم `hr.view` |
| **3.3 نقص الصلاحيات الحساسة** ||||
| 3.3.1 | `permissions.py` | 199-205 | 🟡 MEDIUM | `SENSITIVE_PERMISSIONS` معرفة لكن `require_sensitive_permission` غير مستخدم عمليًا في أي endpoint |
| 3.3.2 | `stock_movements.py` | 29 | 🟠 HIGH | `POST /receipt` يستخدم `stock.manage` (صلاحية عامة) بدل `stock.adjust` |

**الإصلاحات المقترحة**:
```python
# invoices.py:756
@invoices_router.post("/invoices/{invoice_id}/cancel",
    dependencies=[Depends(require_sensitive_permission("sales.delete"))])  # بدل sales.create

# core.py:214 (HR)
if not has_permission(current_user, 'hr.pii'):  # إخفاء salary, IBAN, bank_account
    employee_data.pop('salary', None)
    employee_data.pop('bank_account_number', None)
    employee_data.pop('iban_number', None)
```

---

## 4. تشفير البيانات الحساسة

| # | الملف | السطر | الخطر | التفصيل |
|---|-------|-------|-------|---------|
| **4.1 كلمات المرور** ||||
| 4.1.1 | `database.py` | 38, 132-146 | ✅ | bcrypt عبر passlib `CryptContext` ✅ |
| 4.1.2 | `database.py` | 134-138 | ✅ | fallback لـ bcrypt 5.x compatibility ✅ |
| **4.2 مفاتيح API والبيانات الحساسة** ||||
| 4.2.1 | `field_encryption.py` | 1-124 | ✅ | AES-256-GCM مع HKDF لاشتقاق مفاتيح لكل مستأجر. بنية envelope encryption ممتازة |
| 4.2.2 | — | — | 🔴 CRITICAL | **التشفير غير مستخدم فعليًا**: `encrypt`/`decrypt` معرفة لكن لم تُستدعَ في أي endpoint لتخزين/قراءة البيانات الحساسة. جميع الرواتب، IBAN، أرقام الحسابات، ومفاتيح ZATCA مخزنة كنص واضح |
| 4.2.3 | `settings.py` / `company_settings` | — | 🟠 HIGH | ZATCA private key + certificate مخزنان في `company_settings` كنص واضح. SMTP password مخزن كنص واضح |
| 4.2.4 | `webhooks.py` | 35-42 | ✅ | Webhook secrets مشفرة بـ Fernet قبل التخزين ✅ |
| 4.2.5 | `external.py` | 192 | ✅ | API key secrets مجزأة (hashed) قبل التخزين ✅ |
| **4.3 JWT** ||||
| 4.3.1 | `apiClient.js` | 83 | 🟡 MEDIUM | `localStorage.setItem('token', newToken)` — access token في localStorage (عرضة لـ XSS) |
| 4.3.2 | `main.py` (backend) | — | ✅ | JWT مع توقيع وتاريخ انتهاء ✅ |
| **4.4 HTTPS / HSTS** ||||
| 4.4.1 | `security_middleware.py` | — | ✅ | فرض HTTPS في production + HSTS + CSP headers ✅ |

---

## 5. معالجة الاستثناءات (تسرب معلومات)

| # | الملف | السطر | الخطر | التفصيل |
|---|-------|-------|-------|---------|
| **5.1 تسرب تفاصيل internal errors** ||||
| 5.1.1 | `adjustments.py` | 272 | 🟠 HIGH | `detail=f"حدث خطأ أثناء حفظ التسوية: {str(e)}"` — يمرر `str(e)` للمستخدم. استثناءات SQLAlchemy قد تحتوي على أسماء جداول واستعلامات |
| 5.1.2 | `data_import.py` | 280 | 🟠 HIGH | `f"خطأ في السطر {i + 2}"` — لا يمرر `str(e)` لكنه يكشف رقم السطر (معلومات هيكلية عن البيانات) |
| **5.2 أنماط آمنة** ||||
| 5.2.1 | معظم routers | — | ✅ | `logger.exception("Internal error")` + `HTTPException(500, http_error("internal_error"))` — يسجل التفاصيل في السجلات فقط ولا يكشفها للعميل ✅ |
| 5.2.2 | `apiClient.js` | 206-225 | ✅ | أخطاء 5xx: رسالة عامة "A system error occurred" — لا تظهر تفاصيل تقنية ✅ |
| **5.3 استثناءات صامتة (Silent Failures)** ||||
| 5.3.1 | `pos.py` | 756-757 | 🔴 CRITICAL | فشل تحديث رصيد العميل في POS: `except Exception: pass` — العملية تفشل دون إشعار |
| 5.3.2 | `invoices.py` | 667-672 | 🔴 CRITICAL | فشل ZATCA QR: `except Exception as ze: logger.warning(...)` — الفاتورة تُنشأ بدون ZATCA دون إبلاغ |
| 5.3.3 | `core.py` (manufacturing) | 1122-1127 | 🟠 HIGH | `except Exception: trans.rollback() ... raise HTTPException(400)` — لكن `total_material_cost` قد يكون غير معرف في log_activity (سطر 1106) |

---

## 6. الالتزام بمبادئ SOLID و Clean Architecture

| المبدأ | الامتثال | التفصيل |
|--------|---------|---------|
| **S — Single Responsibility** | 🟠 ضعيف | Routers ضخمة (core.py: 3262 سطر، purchases.py: 3706 سطر، accounting.py: 2772 سطر). كل ملف يحتوي CRUD + business logic + GL posting + notifications + audit |
| **O — Open/Closed** | 🟡 متوسط | نمط Adapter موجود للتكاملات (Payment, SMS, Shipping, E-Invoicing) — يمكن إضافة محولات جديدة بدون تعديل الكود الموجود ✅. لكن الـ routers لا تتبع هذا المبدأ |
| **L — Liskov Substitution** | ✅ جيد | `PaymentGateway`, `SMSGateway`, `ShippingCarrier`, `EInvoiceAdapter` protocols/abstract classes معرفة بشكل صحيح. جميع المحولات تحترم العقود ✅ |
| **I — Interface Segregation** | ✅ جيد | Protocols محددة بدقة: `create_charge()`, `verify_webhook()`, `refund()` — غير مجبرة على تنفيذ ما لا تحتاجه ✅ |
| **D — Dependency Inversion** | 🟡 متوسط | Service layer موجود (`gl_service`, `costing_service`, `notification_service`) لكنه غير مستخدم بشكل شامل. معظم الـ routers تستدعي SQL مباشرة بدل services |

### مشكلات معمارية رئيسية

| # | المشكلة | التأثير |
|---|---------|---------|
| 6.1 | **SQL خام + ORM مختلطان**: `database.py` يعرف الجداول عبر DDL خام وفي نفس الوقت توجد نماذج SQLAlchemy. تعريفان للـ schema في مكانين مختلفين = انجراف schema | صيانة صعبة، أخطاء خفية |
| 6.2 | **منطق الأعمال مبعثر**: نفس العملية (مثلاً إنشاء قيد محاسبي) منفذة في 15+ router مختلف مع duplicate code | عدم اتساق، صعوبة في الإصلاح |
| 6.3 | **لا Repository Pattern**: الوصول للبيانات مباشر في الـ routers عبر `db.execute(text(...))` | صعوبة في اختبار الوحدة، تكرار كود SQL |
| 6.4 | **God Routers**: `purchases.py` (3700+ سطر) يحتوي PO, PI, Returns, Payments, Suppliers, كلها في ملف واحد | صعوبة في المراجعة والصيانة |
| 6.5 | **لا DTOs صريحة**: `dict(row._mapping)` مستخدم في كل مكان بدل كائنات محددة | غياب type safety |
| 6.6 | **تكرار أنماط try/except**: نفس نمط `try/trans.begin()/except/trans.rollback()/finally/conn.close()` مكرر 200+ مرة | تكرار غير ضروري |

### توصيات إعادة الهيكلة

```python
# بدل النمط الحالي (مكرر 200+ مرة):
conn = get_db_connection(company_id)
trans = conn.begin()
try:
    # business logic
    trans.commit()
except HTTPException: raise
except Exception:
    trans.rollback()
    logger.exception(...)
    raise HTTPException(500)
finally:
    conn.close()

# استخدم context manager:
@contextmanager
def transactional(company_id):
    conn = get_db_connection(company_id)
    trans = conn.begin()
    try:
        yield conn
        trans.commit()
    except HTTPException: raise
    except Exception:
        trans.rollback()
        logger.exception("Transaction failed")
        raise HTTPException(500)
    finally:
        conn.close()

# الاستخدام:
with transactional(company_id) as conn:
    # business logic
```

---

## 7. ثغرات أمنية إضافية

| # | الملف | التفصيل | الخطر |
|---|-------|---------|-------|
| 7.1 | `pos.py:1049` | `INSERT INTO inventory ... ON CONFLICT ... DO UPDATE SET quantity = inventory.quantity - :qty` — مرجع جدول غير صالح في سياق ON CONFLICT. سيسبب خطأ على PostgreSQL (قد يُستخدم في DoS) | 🟠 HIGH |
| 7.2 | `main.py:340-342` | Swagger UI + ReDoc متاحان في production بدون حماية. يمكن لأي شخص تصفح جميع الـ endpoints | 🟠 HIGH |
| 7.3 | `sso_service.py` | LDAP bind password يُمرر في body الطلب (ليس مشفرًا أثناء النقل إذا لم يُستخدم HTTPS) | 🟡 MEDIUM |
| 7.4 | `reports.py:3266` | `f"SELECT ... FROM {src['table']}"` — `src['table']` من قاموس ثابت (آمن حاليًا) لكن النمط خطير | 🟡 MEDIUM |
| 7.5 | عدم وجود rate limiting على `/auth/login`: يمكن للمهاجم تجربة كلمات مرور متعددة (brute force). رغم وجود rate limiting عام (120/دقيقة)، لا يوجد حد خاص لمحاولات login الفاشلة | 🟠 HIGH |

---

## ملخص الخلل حسب الخطورة

### 🔴 CRITICAL — 7 مشكلات
| # | المشكلة | الملف |
|---|---------|-------|
| C1 | `config['table']` غير محقق في `data_import.py` | `data_import.py:246-267` |
| C2 | صلاحية `sales.create` للإلغاء والاعتماد والمرتجعات | `invoices.py:756`, `returns.py:92,224`, `credit_notes.py:150` |
| C3 | بيانات مالية حساسة (salary, IBAN) مرئية لـ `hr.view` | `core.py (HR):214` |
| C4 | التشفير غير مفعل فعليًا للبيانات الحساسة | `field_encryption.py` + جميع routers |
| C5 | Silent exception swallowing في POS + ZATCA | `pos.py:756`, `invoices.py:667` |
| C6 | فشل تحديث رصيد العميل دون إشعار | `pos.py:756-757` |
| C7 | `ON CONFLICT` بمرجع غير صالح — فشل قاعدة بيانات | `pos.py:1049`, `manufacturing/core.py:1053` |

### 🟠 HIGH — 15 مشكلة
| # | المشكلة | المواقع |
|---|---------|---------|
| H1 | Dynamic UPDATE بدون validate_sql_identifier | 40+ موقع (CRM, Projects, POS, HR Advanced, Roles) |
| H2 | document.write مع بيانات غير موثوقة | `ThermalPrintSettings.jsx:150`, `CustomerDisplay.jsx:145` |
| H3 | JWT access token في localStorage | `auth.js:14` |
| H4 | صلاحية stock.manage واسعة جدًا | `stock_movements.py:29` |
| H5 | ZATCA private key + SMTP password نص واضح | `settings.py`, `company_settings` |
| H6 | تفاصيل استثناء في رسائل الخطأ | `adjustments.py:272`, `data_import.py:280` |
| H7 | Swagger في production بدون حماية | `main.py:340` |
| H8 | لا rate limiting خاص بـ login | `auth.py` |
| H9 | Silent failure في manufacturing core | `manufacturing/core.py:1106` |
| H10 | Payslips مرئية لجميع مستخدمي hr.view | `core.py (HR):1878` |

---

## توصيات الإصلاح حسب الأولوية

### 🔴 عاجل جدًا (اليوم)

1. **إضافة `validate_sql_identifier` لأسماء الجداول** في `data_import.py:246-267` — إصلاح بحر سطر واحد
2. **تغيير صلاحية إلغاء الفواتير والمرتجعات** إلى `sales.delete` + `require_sensitive_permission`
3. **إخفاء البيانات المالية الحساسة** عن `hr.view` — إضافة شرط `hr.pii`
4. **إصلاح أخطاء `ON CONFLICT`** في `pos.py:1049` و `manufacturing/core.py:1053`
5. **حماية Swagger UI في production** — تعطيل أو إضافة HTTP Basic Auth

### 🟠 عاجل (هذا الأسبوع)

6. **إضافة `validate_sql_identifier` لجميع Dynamic UPDATE** — ~40 موقعًا
7. **استبدال `document.write` بـ `window.open` + blob** في الواجهة الأمامية
8. **تفعيل التشفير** على حقول salary, IBAN, bank_account, ZATCA keys
9. **إضافة rate limiting مخصص لـ login** (5 محاولات/دقيقة لكل IP)
10. **إزالة `str(e)` من رسائل HTTPException** — استخدام رسائل عامة

### 🟡 هذا الشهر

11. **إنشاء `transactional` context manager** لتوحيد معالجة المعاملات
12. **تقسيم routers الضخمة** (>2000 سطر) إلى ملفات أصغر
13. **نقل الـ access token إلى memory فقط** (HttpOnly cookie للـ refresh)
14. **توحيد `validate_sql_identifier`** في دالة واحدة تُستدعى تلقائيًا
