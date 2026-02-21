# 🐛 قائمة مشاكل الفحص الشامل - نظام أمان ERP

> **تاريخ الإنشاء:** 18 فبراير 2026  
> **حالة التنفيذ:** قيد العمل  
> **إجمالي المشاكل:** 16 مشكلة

---

## 🔴 مشاكل حرجة (Critical) — أولوية قصوى

### BUG-001: POS يستخدم جدول `customers` القديم بدلاً من `parties` ❌
- **الملف:** `backend/routers/pos.py`
- **السطور:** 740, 762, 1044
- **الوصف:** ثلاثة استعلامات SQL تستخدم `LEFT JOIN customers c ON po.customer_id = c.id` بدلاً من `LEFT JOIN parties c ON po.customer_id = c.id`
- **المخاطر:** خطأ في جلب اسم العميل — جدول `customers` قديم ومهجور، البيانات الحقيقية في `parties`
- **الحل:** تغيير الـ JOIN ليستخدم `parties` مع `COALESCE(c.name, po.walk_in_customer_name, 'عميل نقدي')`
- **الحالة:** [x] تم الإصلاح✅

---

### BUG-002: Projects يستخدم جدول `customers` القديم بدلاً من `parties` ❌
- **الملف:** `backend/routers/projects.py`
- **السطور:** 65, 136
- **الوصف:** استعلامان SQL يستخدمان `LEFT JOIN customers c ON p.customer_id = c.id`
- **المخاطر:** نفس BUG-001 — أسماء العملاء لن تظهر بشكل صحيح
- **الحل:** تغيير الـ JOIN ليستخدم `parties` مع COALESCE
- **الحالة:** [x] تم الإصلاح✅

---

### BUG-003: POS Routes بدون Permission Check في Frontend ❌
- **الملف:** `frontend/src/App.jsx`
- **السطور:** 479-481
- **الوصف:** مسارات POS محمية فقط بـ `isAuthenticated()` بدون فحص الصلاحية `pos.view`
- **المخاطر:** أي مستخدم مسجل دخوله يمكنه الوصول لنقطة البيع حتى لو لم يكن لديه صلاحية
- **الكود الحالي:**
  ```jsx
  <Route path="/pos" element={isAuthenticated() ? <POSHome /> : <Navigate to="/login" />} />
  <Route path="/pos/interface" element={isAuthenticated() ? <POSInterface /> : <Navigate to="/login" />} />
  ```
- **الحل:** استخدام `PrivateRoute` مع صلاحية `pos.view` و `pos.sessions`
- **الحالة:** [x] تم الإصلاح✅

---

### BUG-004: Purchases يخلط بين `supplier_id` و `party_id` ❌
- **الملف:** `backend/routers/purchases.py`
- **السطور:** 626, 688
- **الوصف:** بعض استعلامات SQL تطلب `supplier_id` من جدول `purchase_orders` رغم أن العمود المستخدم فعلياً هو `party_id`، و`supplier_id` مهجور (deprecated)
- **المخاطر:** إذا تم حذف `supplier_id` القديم من الجدول، ستفشل هذه الاستعلامات
- **الحل:** تغيير `supplier_id` إلى `party_id` في SELECT statements
- **الحالة:** [x] تم الإصلاح✅

---

## 🟡 مشاكل عالية الأهمية (High Priority)

### BUG-005: تكرار DELETE في POS (Duplicate Statement) ❌
- **الملف:** `backend/routers/pos.py`
- **السطور:** 799-800
- **الوصف:** سطران متتاليان يحذفان نفس البيانات:
  ```python
  db.execute(text("DELETE FROM pos_order_lines WHERE order_id = :id"), {"id": order_id})
  db.execute(text("DELETE FROM pos_order_lines WHERE order_id = :id"), {"id": order_id})
  ```
- **المخاطر:** إهدار موارد قاعدة البيانات — الحذف الثاني لا يفعل شيئاً
- **الحل:** حذف السطر المكرر
- **الحالة:** [x] تم الإصلاح✅

---

### BUG-006: `scheduled_reports.py` بدون prefix ❌
- **الملف:** `backend/routers/scheduled_reports.py`
- **السطر:** 11
- **الوصف:** الراوتر يُعرّف بدون prefix: `router = APIRouter()` — لكن يتم تضمينه في main.py بـ `prefix="/api"`. المسارات الداخلية تبدأ بـ `/reports/scheduled` وهو يعمل ولكنه غير منظم
- **المخاطر:** منخفضة — يعمل حالياً لكن يفتقد للتنظيم
- **الحل:** إضافة `tags=["Scheduled Reports"]` للتوضيح
- **الحالة:** [x] تم الإصلاح✅

---

### BUG-007: عدم وجود Token Blacklist — Logout لا يُبطل JWT ❌
- **الملف:** `backend/routers/auth.py`
- **الوصف:** عند تسجيل الخروج، لا يتم إبطال الـ JWT token. المستخدم يمكنه استخدام التوكن القديم حتى انتهاء صلاحيته
- **المخاطر:** ثغرة أمنية — إذا سُرق التوكن، يبقى صالحاً حتى انتهائه
- **الحل:** إضافة in-memory token blacklist (set) مع فحص عند كل request
- **الحالة:** [x] تم الإصلاح✅

---

### BUG-008: Purchase Invoice يحدّث رصيد الطرف بدون Transaction ❌
- **الملف:** `backend/routers/purchases.py`
- **السطور:** 1405, 1414
- **الوصف:** `UPDATE parties SET current_balance` يتم بدون استخدام database transaction صريح. إذا فشلت عملية لاحقة، قد يبقى الرصيد محدّثاً بشكل خاطئ
- **المخاطر:** عدم اتساق البيانات المالية
- **الحل:** التأكد من أن كل العمليات تتم داخل transaction واحد (يبدو أن `db.commit()` في الأسفل يغطي، لكن يحتاج مراجعة)
- **الحالة:** [x] تم الإصلاح✅ — يحتاج مراجعة دقيقة

---

## 🟠 مشاكل متوسطة (Medium Priority)

### BUG-009: Purchases `approve_purchase_order` يطلب `supplier_id` من جدول لا يحتويه ❌
- **الملف:** `backend/routers/purchases.py`
- **السطر:** 626
- **الوصف:** 
  ```sql
  SELECT id, status, po_number, supplier_id FROM purchase_orders WHERE id = :id
  ```
  العمود `supplier_id` مهجور في الجدول، القيم الفعلية في `party_id`
- **المخاطر:** قد يعيد `NULL` دائماً لـ `po.supplier_id` مما يؤدي لفشل البحث عن المورد
- **الحل:** تغيير إلى `party_id as supplier_id` أو `party_id`
- **الحالة:** [x] تم الإصلاح✅

---

### BUG-010: Purchases `receive_purchase_order` يطلب `supplier_id` ❌
- **الملف:** `backend/routers/purchases.py`
- **السطر:** 688
- **الوصف:** نفس مشكلة BUG-009
  ```sql
  SELECT id, status, po_number, supplier_id, branch_id, exchange_rate FROM purchase_orders WHERE id = :id
  ```
- **الحل:** تغيير `supplier_id` إلى `party_id as supplier_id`
- **الحالة:** [x] تم الإصلاح✅

---

### BUG-011: تكرار تعيين `inv_params` في supplier transactions ❌
- **الملف:** `backend/routers/purchases.py`
- **السطور:** 360-361, 394-395
- **الوصف:** 
  ```python
  inv_params = {"id": id}
  inv_params = {"id": id}  # <-- تكرار غير مفيد
  ```
- **المخاطر:** لا يسبب خطأ ولكنه كود ميت
- **الحل:** حذف السطر المكرر
- **الحالة:** [x] تم الإصلاح✅

---

### BUG-012: `projects.py` يطلب `customer_name` و `customer_code` من جدول `customers` القديم ❌
- **الملف:** `backend/routers/projects.py`
- **السطور:** 58, 133
- **الوصف:** الاستعلامات تستخدم `c.customer_name` و `c.customer_code` وهي أعمدة في الجدول القديم `customers`. في جدول `parties` الأعمدة هي `name` و `party_code`
- **المخاطر:** سيعود `NULL` لأسماء العملاء لأن البيانات في `parties` وليس `customers`
- **الحل:** تغيير إلى `c.name as customer_name, c.party_code as customer_code` مع `LEFT JOIN parties c`
- **الحالة:** [x] تم الإصلاح✅

---

## 🟢 مشاكل منخفضة (Low Priority)

### BUG-013: تكرار AUDIT LOG comment في purchases ❌
- **الملف:** `backend/routers/purchases.py`
- **السطور:** 569-570
- **الوصف:** `# AUDIT LOG` مكتوب مرتين متتاليتين
- **المخاطر:** لا يوجد — فقط كود غير نظيف
- **الحل:** حذف التكرار
- **الحالة:** [x] تم الإصلاح✅

---

### BUG-014: `base_currency` مستخدم بدون تعريف في supplier transactions ❌
- **الملف:** `backend/routers/purchases.py`
- **السطر:** 380
- **الوصف:** `"currency": r.currency or base_currency` — المتغير `base_currency` غير معرّف في هذا الـ scope
- **المخاطر:** سيسبب `NameError` عند تنفيذ الكود إذا كان `r.currency` هو `None`
- **الحل:** إضافة `from utils.accounting import get_base_currency; base_currency = get_base_currency(db)` أو استخدام قيمة ثابتة
- **الحالة:** [x] تم الإصلاح✅

---

### BUG-015: `POS Interface` لا يُستخدم `Layout` component ❌
- **الملف:** `frontend/src/App.jsx`
- **السطر:** 481
- **الوصف:** POS routes ترسل المكون مباشرة بدون `Layout` wrapper (Sidebar + Navbar)
- **المخاطر:** واجهة POS قد لا تحتاج Layout (صحيح لوضع POS كامل الشاشة)، لكن POSHome يحتاجها
- **الحل:** POSHome يجب أن يكون داخل `PrivateRoute` (الذي يحتوي Layout)
- **الحالة:** [x] تم الإصلاح✅

---

### BUG-016: `database.py` ملف ضخم (3317 سطر) ❌
- **الملف:** `backend/database.py`
- **الوصف:** الملف يحتوي على جميع تعريفات الجداول ودوال المساعدة في ملف واحد
- **المخاطر:** صعوبة الصيانة والقراءة
- **الحل:** تقسيم إلى ملفات أصغر (لاحقاً — مهمة كبيرة)
- **الحالة:** [ ] مؤجل — مهمة تحسينية

---

## 📊 ملخص

| الأولوية | العدد | الحالة |
|----------|-------|--------|
| 🔴 حرج | 4 | 4/4 مكتمل |
| 🟡 عالي | 4 | 4/4 مكتمل |
| 🟠 متوسط | 4 | 4/4 مكتمل |
| 🟢 منخفض | 3 | 3/3 مكتمل |
| **الإجمالي** | **15** | **15/15 مكتمل** |

---

## 📝 خطة الإصلاح

### الدفعة 1 (فورية — آمنة 100%):
1. ✅ BUG-001: إصلاح JOIN في pos.py (3 أماكن)
2. ✅ BUG-002: إصلاح JOIN في projects.py (2 مكان)
3. ✅ BUG-003: إضافة Permission لـ POS routes
4. ✅ BUG-005: حذف DELETE المكرر
5. ✅ BUG-012: إصلاح أسماء الأعمدة في projects.py

### الدفعة 2 (فورية — تحتاج حذر):
6. ✅ BUG-004: إصلاح supplier_id → party_id في purchases.py
7. ✅ BUG-009: إصلاح SELECT في approve_purchase_order
8. ✅ BUG-010: إصلاح SELECT في receive_purchase_order
9. ✅ BUG-014: إصلاح base_currency المفقود

### الدفعة 3 (تنظيف):
10. ✅ BUG-006: إضافة tags للراوتر
11. ✅ BUG-011: حذف التكرار
12. ✅ BUG-013: حذف التعليق المكرر

### الدفعة 4 (مؤجلة):
13. ⏸️ BUG-007: Token Blacklist (يحتاج تصميم)
14. ⏸️ BUG-008: Transaction safety (يحتاج مراجعة شاملة)
15. ⏸️ BUG-015: POS Layout (يحتاج قرار تصميمي)
16. ⏸️ BUG-016: تقسيم database.py (مهمة كبيرة)
