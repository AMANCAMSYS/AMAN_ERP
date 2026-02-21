# 📖 دليل API — AMAN ERP

> **Base URL:** `http://localhost:8000/api`  
> **Auth:** JWT Bearer Token in `Authorization` header  
> **Swagger UI:** http://localhost:8000/api/docs  
> **ReDoc:** http://localhost:8000/api/redoc

---

## المصادقة (Authentication)

### تسجيل الدخول
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "role": "superuser",
    "permissions": ["*"]
  },
  "company_id": "80b0ada0"
}
```

### استخدام التوكن
```http
GET /api/accounting/accounts
Authorization: Bearer eyJhbGci...
```

### Rate Limiting
| نقطة النهاية | الحد |
|-------------|------|
| `POST /api/auth/login` | 10 طلبات / دقيقة |
| جميع الطلبات الأخرى | 120 طلب / دقيقة |

---

## 📊 المحاسبة (Accounting)

### دليل الحسابات
```http
GET    /api/accounting/accounts              # قائمة الحسابات (شجرة)
POST   /api/accounting/accounts              # إنشاء حساب
PUT    /api/accounting/accounts/{id}         # تعديل حساب
DELETE /api/accounting/accounts/{id}         # حذف حساب
```

### القيود اليومية
```http
GET    /api/accounting/journal-entries       # قائمة القيود
POST   /api/accounting/journal-entries       # إنشاء قيد
GET    /api/accounting/journal-entries/{id}  # تفاصيل قيد
PUT    /api/accounting/journal-entries/{id}  # تعديل قيد
POST   /api/accounting/journal-entries/{id}/post  # ترحيل قيد
```

**إنشاء قيد يومي:**
```json
{
  "entry_date": "2026-02-21",
  "description": "فاتورة مبيعات #1001",
  "lines": [
    {"account_id": 101, "debit": 1150, "credit": 0, "description": "العملاء"},
    {"account_id": 401, "debit": 0, "credit": 1000, "description": "المبيعات"},
    {"account_id": 221, "debit": 0, "credit": 150, "description": "ضريبة القيمة المضافة"}
  ]
}
```

### التقارير المالية
```http
GET /api/accounting/trial-balance?from_date=2026-01-01&to_date=2026-12-31
GET /api/accounting/income-statement?from_date=2026-01-01&to_date=2026-12-31
GET /api/accounting/balance-sheet?as_of=2026-12-31
GET /api/accounting/general-ledger?account_id=101&from_date=2026-01-01
```

---

## 💰 المبيعات (Sales)

### العملاء
```http
GET    /api/sales/customers                  # قائمة العملاء
POST   /api/sales/customers                  # إنشاء عميل
GET    /api/sales/customers/{id}             # تفاصيل عميل
PUT    /api/sales/customers/{id}             # تعديل عميل
GET    /api/sales/customers/{id}/statement   # كشف حساب
```

### الفواتير
```http
GET    /api/sales/invoices                   # قائمة الفواتير
POST   /api/sales/invoices                   # إنشاء فاتورة
GET    /api/sales/invoices/{id}              # تفاصيل فاتورة
POST   /api/sales/invoices/{id}/post         # ترحيل فاتورة
```

### أوامر البيع
```http
GET    /api/sales/orders                     # قائمة الأوامر
POST   /api/sales/orders                     # إنشاء أمر بيع
GET    /api/sales/orders/{id}                # تفاصيل
POST   /api/sales/orders/{id}/confirm        # تأكيد
POST   /api/sales/orders/{id}/invoice        # تحويل لفاتورة
```

### عروض الأسعار
```http
GET    /api/sales/quotations
POST   /api/sales/quotations
POST   /api/sales/quotations/{id}/approve    # اعتماد
POST   /api/sales/quotations/{id}/convert    # تحويل لأمر بيع
```

---

## 🛒 المشتريات (Purchases)

```http
GET    /api/buying/suppliers                 # قائمة الموردين
POST   /api/buying/suppliers                 # إنشاء مورد
GET    /api/buying/orders                    # أوامر الشراء
POST   /api/buying/orders                    # إنشاء أمر شراء
POST   /api/buying/orders/{id}/receive       # استلام بضاعة
GET    /api/buying/invoices                  # فواتير المشتريات
POST   /api/buying/invoices                  # إنشاء فاتورة
GET    /api/buying/rfq                       # طلبات عروض أسعار
POST   /api/buying/rfq                       # إنشاء RFQ
```

---

## 📦 المخزون (Inventory)

### المنتجات
```http
GET    /api/inventory/products               # قائمة المنتجات
POST   /api/inventory/products               # إنشاء منتج
PUT    /api/inventory/products/{id}          # تعديل منتج
```

**إنشاء منتج:**
```json
{
  "name": "لابتوب HP",
  "sku": "HP-LAP-001",
  "product_type": "product",
  "category_id": 1,
  "cost_price": 2500,
  "selling_price": 3200,
  "unit": "piece",
  "track_inventory": true
}
```

### المستودعات والمخزون
```http
GET    /api/inventory/warehouses             # المستودعات
POST   /api/inventory/warehouses             # إنشاء مستودع
GET    /api/inventory/warehouses/{id}        # مخزون المستودع
POST   /api/inventory/transfers              # تحويل بين مستودعات
POST   /api/inventory/adjustments            # تسوية مخزون
GET    /api/inventory/stock-movements        # حركات المخزون
```

### التتبع المتقدم
```http
GET    /api/inventory/advanced/batches       # الدفعات
GET    /api/inventory/advanced/serials       # الأرقام التسلسلية
POST   /api/inventory/advanced/quality       # فحص جودة
GET    /api/inventory/advanced/cycle-counts  # جرد دوري
```

---

## 🏦 الخزينة (Treasury)

```http
GET    /api/treasury/accounts                # حسابات الخزينة
POST   /api/treasury/expense                 # تسجيل مصروف
POST   /api/treasury/transfer                # تحويل بين حسابات
GET    /api/treasury/balances                # أرصدة الحسابات
GET    /api/treasury/cashflow                # تقرير التدفقات النقدية

# الشيكات
GET    /api/checks/                          # قائمة الشيكات
POST   /api/checks/                          # إنشاء شيك
PATCH  /api/checks/{id}/collect              # تحصيل
PATCH  /api/checks/{id}/bounce               # ارتداد

# السندات
GET    /api/notes/                            # قائمة السندات
POST   /api/notes/                            # إنشاء سند
```

---

## 👥 الموارد البشرية (HR)

```http
# الموظفون
GET    /api/hr/employees                     # قائمة
POST   /api/hr/employees                     # إنشاء
PUT    /api/hr/employees/{id}                # تعديل

# الرواتب
GET    /api/hr/payroll                        # فترات الرواتب
POST   /api/hr/payroll                        # بدء فترة جديدة
POST   /api/hr/payroll/{id}/process           # معالجة الرواتب

# الحضور والإجازات
POST   /api/hr/attendance                     # تسجيل حضور
GET    /api/hr/leaves                         # طلبات الإجازات
POST   /api/hr/leaves                         # طلب إجازة

# HR متقدم
GET    /api/hr-advanced/performance-reviews    # مراجعات الأداء
GET    /api/hr-advanced/training               # البرامج التدريبية
GET    /api/hr-advanced/violations             # المخالفات
GET    /api/hr-advanced/recruitment            # التوظيف
```

---

## 🏭 التصنيع (Manufacturing)

```http
GET    /api/manufacturing/work-centers        # مراكز العمل
POST   /api/manufacturing/work-centers        # إنشاء مركز عمل
GET    /api/manufacturing/boms                 # قوائم المواد (BOM)
POST   /api/manufacturing/boms                 # إنشاء BOM
GET    /api/manufacturing/orders               # أوامر الإنتاج
POST   /api/manufacturing/orders               # إنشاء أمر إنتاج
POST   /api/manufacturing/orders/{id}/start    # بدء الإنتاج
POST   /api/manufacturing/orders/{id}/complete # إتمام
GET    /api/manufacturing/job-cards            # بطاقات العمل
GET    /api/manufacturing/mrp                  # تخطيط MRP
```

---

## 🏪 نقاط البيع (POS)

```http
POST   /api/pos/sessions/open                 # فتح جلسة
POST   /api/pos/sessions/{id}/close            # إغلاق جلسة
POST   /api/pos/orders                         # إنشاء طلب
GET    /api/pos/orders?session_id=1            # طلبات الجلسة
GET    /api/pos/promotions                     # العروض الترويجية
GET    /api/pos/loyalty                        # برامج الولاء
```

---

## 📐 المشاريع (Projects)

```http
GET    /api/projects/                          # قائمة المشاريع
POST   /api/projects/                          # إنشاء مشروع
GET    /api/projects/{id}                      # تفاصيل مشروع
POST   /api/projects/{id}/tasks                # إضافة مهمة
POST   /api/projects/{id}/resources            # إضافة مورد
GET    /api/projects/{id}/progress             # تقرير تقدم
```

---

## 🔔 الإشعارات (Notifications)

### HTTP
```http
GET    /api/notifications                      # قائمة الإشعارات
GET    /api/notifications/unread-count          # عدد غير المقروءة
PATCH  /api/notifications/{id}/read             # تعليم كمقروء
```

### WebSocket (Real-time)
```javascript
const ws = new WebSocket('ws://localhost:8000/api/notifications/ws?token=JWT_TOKEN')
ws.onmessage = (event) => {
  const { event: type, data } = JSON.parse(event.data)
  // type: "new_notification"
  // data: { id, title, message, type, link, is_read, created_at }
}
```

---

## 🔐 الأمان (Security)

```http
# مفاتيح API
GET    /api/security/api-keys                  # قائمة المفاتيح
POST   /api/security/api-keys                  # إنشاء مفتاح

# Webhooks
GET    /api/security/webhooks                  # قائمة Webhooks
POST   /api/security/webhooks                  # إنشاء Webhook

# المصادقة الثنائية
POST   /api/auth/2fa/setup                     # إعداد 2FA
POST   /api/auth/2fa/verify                    # التحقق من كود OTP
```

---

## 📊 لوحة التحكم (Dashboard)

```http
GET /api/dashboard/stats                       # إحصائيات عامة
GET /api/dashboard/charts/financial            # رسوم بيانية مالية
GET /api/dashboard/charts/products             # أكثر المنتجات مبيعاً
GET /api/dashboard/recent-activity             # آخر النشاطات
```

---

## 🔍 أنماط الاستعلام الشائعة

### التصفح (Pagination)
```http
GET /api/sales/invoices?page=1&per_page=20
```

### البحث
```http
GET /api/inventory/products?search=لابتوب
GET /api/sales/customers?search=أحمد
```

### الفلترة
```http
GET /api/sales/invoices?status=posted&from_date=2026-01-01&to_date=2026-12-31
GET /api/hr/employees?department_id=3&status=active
```

---

## ❌ أكواد الخطأ

| الكود | الوصف |
|-------|-------|
| 400 | طلب غير صالح — بيانات ناقصة أو غير صحيحة |
| 401 | غير مصادق — توكن مفقود أو منتهي الصلاحية |
| 403 | غير مصرح — لا تملك صلاحية لهذه العملية |
| 404 | غير موجود — المورد المطلوب غير موجود |
| 422 | خطأ في بنية البيانات — Pydantic validation error |
| 429 | تجاوز الحد المسموح — Rate limit exceeded |
| 500 | خطأ داخلي في الخادم |

**شكل رسالة الخطأ:**
```json
{
  "detail": "رسالة الخطأ بالعربية أو الإنجليزية"
}
```
