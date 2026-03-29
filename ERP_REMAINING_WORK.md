# AMAN ERP — المتبقي من العمل

**التاريخ:** 2026-03-29
**النتيجة الحالية:** 75 / 100 (خطر منخفض-متوسط)
**إجمالي الإصلاحات المطبقة:** 76 إصلاح عبر 81 ملف

---

## الوضع الحالي — ما تم إنجازه

| الفئة | التفاصيل | النسبة |
|--------|----------|--------|
| الدقة المالية (Decimal) | جميع الحسابات المالية: مبيعات، مشتريات، خزينة، نقاط بيع، رواتب، شيكات، سندات | 100% |
| أمان API | Rate limiting، إخفاء التوكن من اللوج، إزالة التوكن من URL، حذف console.log من الإنتاج | 100% |
| التزامن (Concurrency) | FOR UPDATE على المخزون والحد الائتماني | 100% |
| الامتثال الضريبي (ZATCA) | خصم الرأس على ضريبة القيمة المضافة، قاعدة ضريبية صحيحة في 14 استعلام | 100% |
| تكامل القيود المحاسبية | validate_je_lines في 18 نقطة (خزينة، مصروفات، سندات، شيكات) | 100% |
| قاعدة البيانات | 46 فهرس + 32 قيد FK مضاف | 100% |
| واجهات القوائم (DataTable) | 26 من 26 صفحة قائمة | 100% |
| واجهات النماذج (FormField) | 25 من 25 صفحة نموذج | 100% |
| وحدات القياس (UOM) | التحقق في الفواتير، المرتجعات، نقاط البيع، حركات المخزون | 100% |

---

## المتبقي — الأولوية القصوى (للوصول إلى 80+)

### 1. توحيد خدمة القيود المحاسبية (Centralized GL Service)

| | |
|---|---|
| **الأولوية** | P0 — الأعلى |
| **الجهد** | 1-2 أسبوع |
| **المشكلة** | 75 نسخة مكررة من `INSERT INTO journal_entries` + `INSERT INTO journal_entry_lines` موزعة على 25 ملف |
| **الخطر** | أي تغيير في منطق القيد يحتاج تعديل 25 ملف — احتمال تناقض عالي جداً |
| **الحل** | إنشاء `services/gl_service.py` بدالة `create_journal_entry(db, lines, source, ...)` واستبدال جميع النسخ المكررة |

**الملفات المتأثرة:**

| الملف | عدد النسخ |
|--------|-----------|
| finance/accounting.py | 12 |
| finance/checks.py | 8 |
| purchases.py | 7 |
| projects.py | 6 |
| finance/assets.py | 6 |
| finance/notes.py | 6 |
| pos.py | 3 |
| finance/treasury.py | 3 |
| hr/core.py | 2 |
| 16 ملف آخر | 1-2 لكل ملف |

---

### 2. Trigger قاعدة البيانات للقيد المزدوج

| | |
|---|---|
| **الأولوية** | P0 |
| **الجهد** | 1 أسبوع |
| **المشكلة** | التحقق من توازن المدين/الدائن يتم فقط في Python — لا حماية على مستوى قاعدة البيانات |
| **الخطر** | أي INSERT مباشر أو خطأ برمجي يمكن أن ينتج قيد غير متوازن |
| **الحل** | إنشاء PostgreSQL TRIGGER على `journal_entry_lines` يمنع الحفظ إذا `SUM(debit) != SUM(credit)` |

```sql
CREATE OR REPLACE FUNCTION check_je_balance() RETURNS TRIGGER AS $$
BEGIN
    IF (SELECT ABS(SUM(debit) - SUM(credit)) FROM journal_entry_lines
        WHERE journal_entry_id = NEW.journal_entry_id) > 0.01 THEN
        RAISE EXCEPTION 'Journal entry is not balanced';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

---

### 3. اعتماد Alembic للتهجيرات

| | |
|---|---|
| **الأولوية** | P1 |
| **الجهد** | 2-4 أسابيع |
| **المشكلة** | Schema يُنشأ بـ `CREATE TABLE IF NOT EXISTS` — لا تتبع للتغييرات، لا rollback |
| **الخطر** | تعديل جدول موجود يتطلب `ALTER TABLE` يدوي — احتمال نسيان تطبيقه على بيئات مختلفة |
| **الحل** | إعداد Alembic مع `autogenerate`، تحويل database.py إلى SQLAlchemy models، إنشاء migration أولي |

**خطوات التنفيذ:**
1. `alembic init migrations`
2. إنشاء SQLAlchemy models من الجداول الحالية
3. إنشاء initial migration من الحالة الحالية
4. تعديل `create_company_database()` لاستخدام `alembic upgrade head`
5. اختبار على شركة جديدة + شركة موجودة

---

### 4. نقل التوكن إلى HttpOnly Cookie

| | |
|---|---|
| **الأولوية** | P1 |
| **الجهد** | 1 أسبوع |
| **المشكلة** | JWT token مخزن في `localStorage` — معرض لسرقة عبر XSS |
| **الخطر** | أي ثغرة XSS تسمح بسرقة التوكن والوصول الكامل للحساب |
| **الحل** | Backend: إرسال التوكن في `Set-Cookie: HttpOnly; Secure; SameSite=Strict` / Frontend: حذف localStorage token، الاعتماد على الكوكيز |

**الملفات المتأثرة:**
- Backend: `routers/auth.py` (login, refresh, logout)
- Frontend: `utils/auth.js`, `services/apiClient.js`, `context/AuthContext.jsx`

---

## المتبقي — أولوية عالية (للوصول إلى 90+)

### 5. Materialized Views للأرصدة

| | |
|---|---|
| **الجهد** | 2-3 أسابيع |
| **المشكلة** | 4 مصادر مختلفة للرصيد: `accounts.balance`، `treasury_accounts.current_balance`، `parties.current_balance`، `party_transactions.balance` — 35+ مسار تحديث مستقل |
| **الحل** | إنشاء materialized view يحسب الرصيد من `journal_entry_lines` كمصدر وحيد للحقيقة |

### 6. Pydantic Models لمسارات API

| | |
|---|---|
| **الجهد** | 2-3 أسابيع |
| **المشكلة** | 98 مسار API يقبل `dict` بدون تحقق — لا validation، لا documentation، لا type safety |
| **الحل** | إنشاء Pydantic models لكل مسار (مثل `AssetTransferCreate`, `RecurringTemplateUpdate`) |

**أكثر الملفات تأثراً:**
- `finance/assets.py` — 6 مسارات بدون schema
- `finance/accounting.py` — 3 مسارات
- `contracts.py`, `delivery_orders.py`, `approvals.py` — 4+ مسارات لكل ملف

### 7. Optimistic Locking

| | |
|---|---|
| **الجهد** | 1 أسبوع |
| **المشكلة** | لا توجد حماية من التعديل المتزامن — مستخدمان يعدلان نفس الفاتورة يفقد أحدهما تعديلاته |
| **الحل** | إضافة `version` column لكل جدول قابل للتعديل + `WHERE version = :expected` في UPDATE |

### 8. اختبارات آلية

| | |
|---|---|
| **الجهد** | 3-4 أسابيع |
| **المشكلة** | لا توجد اختبارات آلية — كل تغيير يحتاج اختبار يدوي |
| **الحل** | pytest + fixtures لقاعدة بيانات اختبار + اختبارات لكل مسار API حرج |

---

## ملخص الجهد الإجمالي

| الفئة | المهام | الجهد |
|--------|--------|-------|
| **P0 — حرج** | GL Service + DB Trigger | 2-3 أسابيع |
| **P1 — عالي** | Alembic + HttpOnly Cookie | 3-5 أسابيع |
| **P2 — متوسط** | Materialized Views + Pydantic + Locking + Tests | 8-11 أسبوع |
| **المجموع** | 8 مهام | 13-19 أسبوع |

---

## ترتيب التنفيذ المقترح

```
الأسبوع 1-2:  GL Service (توحيد 75 نسخة → دالة واحدة)
الأسبوع 3:    DB Trigger (حماية القيد المزدوج)
الأسبوع 4:    HttpOnly Cookie (أمان التوكن)
الأسبوع 5-8:  Alembic (تهجيرات قاعدة البيانات)
الأسبوع 9-11: Pydantic Models (تحقق المدخلات)
الأسبوع 12-14: Materialized Views (توحيد الأرصدة)
الأسبوع 15:   Optimistic Locking
الأسبوع 16-19: Automated Tests
```

**الهدف: الوصول إلى 90+ / 100 خلال 19 أسبوع (~5 أشهر)**

---

*آخر تحديث: 2026-03-29*
