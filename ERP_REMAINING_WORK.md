# AMAN ERP — المتبقي من العمل

**التاريخ:** 2026-03-30
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
| **الحالة** | ✅ مكتمل (2026-03-30) |
| **المشكلة** | التحقق من توازن المدين/الدائن يتم فقط في Python — لا حماية على مستوى قاعدة البيانات |
| **الخطر** | أي INSERT مباشر أو خطأ برمجي يمكن أن ينتج قيد غير متوازن |
| **الحل** | إنشاء PostgreSQL CONSTRAINT TRIGGER مؤجل (DEFERRABLE INITIALLY DEFERRED) على `journal_lines` يغطي `INSERT/UPDATE/DELETE` لمنع أي قيد غير متوازن |

```sql
CREATE OR REPLACE FUNCTION check_journal_balance() RETURNS TRIGGER AS $$
DECLARE
    target_journal_entry_id INTEGER;
    total_debit NUMERIC;
    total_credit NUMERIC;
BEGIN
    target_journal_entry_id := COALESCE(NEW.journal_entry_id, OLD.journal_entry_id);

    SELECT COALESCE(SUM(debit), 0), COALESCE(SUM(credit), 0)
      INTO total_debit, total_credit
    FROM journal_lines
    WHERE journal_entry_id = target_journal_entry_id;

    IF ABS(total_debit - total_credit) > 0.01 THEN
        RAISE EXCEPTION 'Journal entry % is not balanced (debit %, credit %)',
            target_journal_entry_id, total_debit, total_credit;
    END IF;
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_journal_balance ON journal_lines;

CREATE CONSTRAINT TRIGGER trg_journal_balance
AFTER INSERT OR UPDATE OR DELETE ON journal_lines
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_journal_balance();
```

**التنفيذ الفعلي:**
- تم إنشاء migration رسمي: `alembic/versions/0003_journal_balance_trigger_hardening.py`
- Revision المعتمد: `0003_je_trigger_hard`
- تم تطبيقه على جميع قواعد الشركات النشطة (11/11)
- تم التحقق عمليًا:
    - القيد غير المتوازن يُرفض عند `COMMIT`
    - القيد المتوازن يمر بنجاح

---

### 3. اعتماد Alembic للتهجيرات

| | |
|---|---|
| **الأولوية** | P1 |
| **الجهد** | 2-4 أسابيع |
| **الحالة** | 🚧 قيد التنفيذ المتقدم (تم تفعيل Alembic + ربط provisioning + ORM phase1/phase2/phase3/phase4/phase6/phase7/phase8/phase9/phase10/phase11/phase12/phase13/phase14/phase15/phase16/phase17/phase18/phase19/phase20/phase21/phase22/phase23/phase24/phase25/phase26 + drift-fix إضافي لـ `asset_impairments` و`expense_policies` + bulk drift normalization + revision ثامن: `c1f4e8d9b2a6`) |
| **المشكلة** | Schema يُنشأ بـ `CREATE TABLE IF NOT EXISTS` — لا تتبع للتغييرات، لا rollback |
| **الخطر** | تعديل جدول موجود يتطلب `ALTER TABLE` يدوي — احتمال نسيان تطبيقه على بيئات مختلفة |
| **الحل** | إعداد Alembic مع `autogenerate`، تحويل database.py إلى SQLAlchemy models، إنشاء migration أولي |

**خطوات التنفيذ:**
1. `alembic init migrations`
2. 🚧 إنشاء SQLAlchemy models من الجداول الحالية (phase1 + phase2 + phase3 + phase4 + phase6 + phase7 + phase8 + phase9 + phase10 + phase11 + phase12 + phase13 + phase14 + phase15 + phase16 + phase17 + phase18 + phase19 + phase20 + phase21 + phase22 + phase23 + phase24 + phase25 + phase26 مكتملة حاليًا لـ 156 جدولًا؛ تم توسيع النطاق إلى المخزون/المشتريات/HR + الخزينة/الضرائب/المشاريع + الشيكات/المستندات/الدعم + الموافقات + الأصول الأساسية + الميزانيات الأساسية + مراكز/سياسات التكلفة + الأصول المتقدمة + العملات/استيراد البنوك + الإقفال المالي/الزكاة + العقود/بنود العقود + سياسات المصروفات + CRM advanced scoring/segmentation/forecasting + مفاتيح API/Security/Ops reporting + advanced inventory bins/cycle counting + variants/kits + traceability/quality + customer master/pricing + receivables/delivery + HR compliance/recruitment + MFG/attachments/commissions + reporting/documents/fx/crm contacts + mfg capacity/contracts amendments/crm knowledge/customer groups + dashboard/fiscal/gosi/intercompany/landed costs + landed costs/leasing/leave carryover/security login)
3. ✅ إنشاء ومراجعة revision رابع غير فارغ عبر autogenerate: `908f5baa6f93_phase4_ops_support_autogen_reviewed.py` (إصلاح drift أعمدة مهم في service/docs)
4. ✅ إنشاء Phase 5 targeted migration: `e1c5a8b6d6f2_phase5_targeted_missing_tables.py` لإنشاء جدولَي `service_request_costs` و`document_versions` فقط عند الحاجة وفي شركتين محددتين
5. ✅ تعديل `create_company_tables()` لتشغيل `alembic -x company=<id> upgrade head` تلقائيًا بعد إنشاء الجداول
6. ✅ اختبار على شركة تجريبية + النظام (نجح على المسارين، ثم تمت ترقية جميع القواعد إلى `alembic_version=c1f4e8d9b2a6`)

**مخرجات Phase 2 (مطبقة على 11/11 شركة + النظام):**
- إضافة أعمدة خصومات/Markup الناقصة في `purchase_orders` (`effect_type`, `effect_percentage`, `markup_amount`) عبر هجرة idempotent.
- إضافة أعمدة الرواتب متعددة العملة الناقصة في `payroll_entries` (`currency`, `exchange_rate`, `net_salary_base`).
- توحيد أعمدة ناقصة في بعض الشركات فقط: `invoices` و`invoice_lines` و`party_groups`.
- توحيد نسخة Alembic: كل الشركات والنظام على `2bd1b4bb466a`.

**مخرجات Phase 3 (مطبقة على 11/11 شركة + النظام):**
- إضافة أعمدة المشاريع الناقصة في `projects` (`party_id`, `retainer_amount`, `billing_cycle`, `last_billed_date`, `next_billing_date`) لدعم الفوترة الدورية ومصدر الفوترة الموحد.
- إضافة أعمدة ضرائبية ناقصة في `tax_rates` (`jurisdiction_code`, `updated_at`) لتوحيد إعدادات الضريبة عبر الشركات.
- توحيد نسخة Alembic: كل الشركات والنظام على `786e754b8d34`.

**مخرجات Phase 4 (مطبقة على 11/11 شركة + النظام):**
- إضافة أعمدة تشغيلية ناقصة في `service_requests` (`assigned_at`, `completion_date`, `location`, `notes`, `updated_at`).
- إضافة أعمدة تكلفة ناقصة في `service_request_costs` (`quantity`, `unit_cost`, `total_cost`, `created_at`).
- إضافة أعمدة ربط/إصدار ناقصة في `documents` (`related_module`, `related_id`, `current_version`, `updated_at`).
- إضافة أعمدة تتبّع ناقصة في `document_versions` (`change_notes`, `created_at`).
- توحيد نسخة Alembic: كل الشركات والنظام على `908f5baa6f93`.
- ملاحظة drift (تم إغلاقها): كانت شركتان (`aman_8f3e504b`, `aman_fcfa5fae`) تفتقدان جدولَي `service_request_costs` و`document_versions`، وتمت معالجتها بالكامل في Phase 5 targeted fix.

**مخرجات Phase 5 targeted fix (مطبقة على 11/11 شركة + النظام):**
- إنشاء مشروط لجدول `service_request_costs` فقط إذا كان مفقودًا.
- إنشاء مشروط لجدول `document_versions` فقط إذا كان مفقودًا.
- تفعيل الإنشاء فقط على الشركتين المستهدفتين `aman_8f3e504b` و`aman_fcfa5fae` عبر شرط اسم قاعدة البيانات داخل migration.
- نتيجة التحقق: لا توجد أي شركة مفقود بها هذان الجدولان بعد التطبيق.
- توحيد نسخة Alembic: كل الشركات والنظام على `e1c5a8b6d6f2`.

**مخرجات Phase 6 ORM coverage (مطبقة على 11/11 شركة + النظام):**
- إضافة نماذج ORM لوحدة الموافقات: `approval_workflows`, `approval_requests`, `approval_actions`.
- توسيع `MODELED_TABLES` من 60 إلى 63 جدولًا.
- نتيجة التحقق: لا يوجد drift بنيوي في هذه الجداول عبر جميع الشركات (لا حاجة revision جديدة لهذه الدفعة).

**مخرجات Phase 7 ORM coverage (مطبقة على 11/11 شركة + النظام):**
- إضافة نماذج ORM للأصول الأساسية: `asset_categories`, `assets`, `asset_transfers`.
- توسيع `MODELED_TABLES` من 63 إلى 66 جدولًا.
- نتيجة التحقق: لا يوجد drift بنيوي في هذه الجداول عبر جميع الشركات (لا حاجة revision جديدة لهذه الدفعة).

**مخرجات Phase 8 ORM coverage (مطبقة على 11/11 شركة + النظام):**
- إضافة نماذج ORM للميزانيات الأساسية: `budgets`, `budget_items`, `budget_lines`.
- توسيع `MODELED_TABLES` من 66 إلى 69 جدولًا.
- نتيجة التحقق: لا يوجد drift بنيوي في هذه الجداول عبر جميع الشركات (لا حاجة revision جديدة لهذه الدفعة).

**مخرجات Phase 9 ORM coverage (مطبقة على 11/11 شركة + النظام):**
- إضافة نماذج ORM لمراكز وسياسات التكلفة: `cost_centers`, `cost_centers_budgets`, `costing_policies`, `costing_policy_details`, `costing_policy_history`, `inventory_cost_snapshots`.
- توسيع `MODELED_TABLES` من 69 إلى 75 جدولًا.
- نتيجة التحقق: لا يوجد drift بنيوي في هذه الجداول عبر جميع الشركات (لا حاجة revision جديدة لهذه الدفعة).

**مخرجات Phase 10 ORM coverage (مطبقة على 11/11 شركة + النظام):**
- إضافة نماذج ORM للأصول المتقدمة: `asset_depreciation_schedule`, `asset_disposals`, `asset_revaluations`, `asset_insurance`, `asset_maintenance`.
- توسيع `MODELED_TABLES` من 75 إلى 80 جدولًا.
- نتيجة التحقق: لا يوجد drift بنيوي في هذه الجداول عبر جميع الشركات (لا حاجة revision جديدة لهذه الدفعة).

**مخرجات Drift-fix (asset_impairments) (مطبقة على 11/11 شركة + النظام):**
- إنشاء migration مخصص: `f3a1d9c42b7e_asset_impairments_created_by_drift_fix.py`.
- إضافة العمود الناقص `created_by` في `asset_impairments` فقط عند غيابه (idempotent).
- نتيجة التحقق: توحيد schema للجدول من `variants=2` إلى `variants=1` عبر جميع الشركات.
- تمت إضافة نموذج ORM لجدول `asset_impairments` بعد توحيده.
- توحيد نسخة Alembic: كل الشركات والنظام على `f3a1d9c42b7e`.

**مخرجات Phase 11 ORM coverage (مطبقة على 11/11 شركة + النظام):**
- إضافة نماذج ORM لوحدة العملات واستيراد البنوك: `currencies`, `exchange_rates`, `bank_import_batches`, `bank_import_lines`.
- توسيع `MODELED_TABLES` من 81 إلى 85 جدولًا.
- نتيجة التحقق: لا يوجد drift بنيوي في هذه الجداول عبر جميع الشركات (لا حاجة revision جديدة لهذه الدفعة).

**مخرجات Phase 12 ORM coverage (مطبقة على 11/11 شركة + النظام):**
- إضافة نماذج ORM لوحدة الإقفال المالي/الزكاة: `fiscal_years`, `fiscal_period_locks`, `zakat_calculations`.
- توسيع `MODELED_TABLES` من 85 إلى 88 جدولًا.
- نتيجة التحقق: لا يوجد drift بنيوي في هذه الجداول عبر جميع الشركات (لا حاجة revision جديدة لهذه الدفعة).

**مخرجات Drift-fix (expense_policies) (مطبقة على 11/11 شركة + النظام):**
- إنشاء migration مخصص: `a4b2c9d8e6f1_expense_policies_created_by_drift_fix.py`.
- إضافة العمود الناقص `created_by` في `expense_policies` فقط عند غيابه (idempotent).
- نتيجة التحقق: توحيد الأعمدة فعليًا عبر جميع الشركات (`set_variants=1`).
- ملاحظة فنية: ما زال `ordered_variants=2` بسبب اختلاف ترتيب العمود (`created_by` قبل/بعد `created_at`) وليس بسبب فقدان أعمدة.
- توحيد نسخة Alembic: كل الشركات والنظام على `a4b2c9d8e6f1`.

**مخرجات Phase 13 ORM coverage (مطبقة على 11/11 شركة + النظام):**
- إضافة نماذج ORM لوحدة العقود/المصروفات: `contracts`, `contract_items`, `expense_policies`.
- توسيع `MODELED_TABLES` من 88 إلى 91 جدولًا.
- نتيجة التحقق: لا يوجد missing modeled tables عبر جميع الشركات، والجداول الثلاثة مستقرة بنيويًا.

**مخرجات Phase 14 ORM coverage (مطبقة على 11/11 شركة + النظام):**
- إضافة نماذج ORM لوحدة CRM المتقدمة: `crm_lead_scoring_rules`, `crm_lead_scores`, `crm_customer_segments`, `crm_customer_segment_members`, `crm_sales_forecasts`.
- توسيع `MODELED_TABLES` من 91 إلى 96 جدولًا.
- نتيجة التحقق: الجداول الخمسة مستقرة عبر جميع الشركات (`present=11/11`, `ordered_variants=1`, `set_variants=1`) ولا يوجد missing modeled tables.

**مخرجات Phase 15 ORM coverage (مطبقة على 11/11 شركة + النظام):**
- إضافة نماذج ORM لوحدة Security/Ops/Reporting: `api_keys`, `audit_logs`, `backup_history`, `custom_reports`, `email_templates`.
- توسيع `MODELED_TABLES` من 96 إلى 101 جدولًا.
- نتيجة التحقق: الجداول الخمسة مستقرة عبر جميع الشركات (`present=11/11`, `ordered_variants=1`, `set_variants=1`) ولا يوجد missing modeled tables.

**مخرجات Phase 16 ORM coverage (مطبقة على 11/11 شركة + النظام):**
- إضافة نماذج ORM لوحدة المخزون المتقدم (bins/cycle): `batch_serial_movements`, `cycle_counts`, `cycle_count_items`, `bin_locations`, `bin_inventory`.
- توسيع `MODELED_TABLES` من 101 إلى 106 جدولًا.
- نتيجة التحقق: الجداول الخمسة مستقرة عبر جميع الشركات (`present=11/11`, `ordered_variants=1`, `set_variants=1`) ولا يوجد missing modeled tables.

**مخرجات Phase 17 ORM coverage (مطبقة على 11/11 شركة + النظام):**
- إضافة نماذج ORM لوحدة variants/kits: `product_attributes`, `product_attribute_values`, `product_variants`, `product_variant_attributes`, `product_kits`.
- توسيع `MODELED_TABLES` من 106 إلى 111 جدولًا.
- نتيجة التحقق: الجداول الخمسة مستقرة عبر جميع الشركات (`present=11/11`, `ordered_variants=1`, `set_variants=1`) ولا يوجد missing modeled tables.

**مخرجات Phase 18 ORM coverage (مطبقة على 11/11 شركة + النظام):**
- إضافة نماذج ORM لوحدة traceability/quality: `product_batches`, `product_serials`, `quality_inspections`, `quality_inspection_criteria`, `product_kit_items`.
- توسيع `MODELED_TABLES` من 111 إلى 116 جدولًا.
- نتيجة التحقق: الجداول الخمسة مستقرة عبر جميع الشركات (`present=11/11`, `ordered_variants=1`, `set_variants=1`) ولا يوجد missing modeled tables.

**مخرجات Phase 19 ORM coverage (مطبقة على 11/11 شركة + النظام):**
- إضافة نماذج ORM لوحدة customer master/pricing: `customers`, `customer_contacts`, `customer_bank_accounts`, `customer_price_lists`, `customer_price_list_items`.
- توسيع `MODELED_TABLES` من 116 إلى 121 جدولًا.
- نتيجة التحقق: الجداول الخمسة مستقرة عبر جميع الشركات (`present=11/11`, `ordered_variants=1`, `set_variants=1`) ولا يوجد missing modeled tables.

**مخرجات Phase 20 ORM coverage (مطبقة على 11/11 شركة + النظام):**
- إضافة نماذج ORM لوحدة receivables/delivery: `customer_transactions`, `customer_receipts`, `customer_balances`, `delivery_orders`, `delivery_order_lines`.
- توسيع `MODELED_TABLES` من 121 إلى 126 جدولًا.
- نتيجة التحقق: الجداول الخمسة مستقرة عبر جميع الشركات (`present=11/11`, `ordered_variants=1`, `set_variants=1`) ولا يوجد missing modeled tables.

**مخرجات Phase 21 ORM coverage (مطبقة على 11/11 شركة + النظام):**
- إضافة نماذج ORM لوحدة HR compliance/recruitment: `employee_documents`, `employee_violations`, `employee_custody`, `job_openings`, `job_applications`.
- توسيع `MODELED_TABLES` من 126 إلى 131 جدولًا.
- نتيجة التحقق: الجداول الخمسة مستقرة عبر جميع الشركات (`present=11/11`, `ordered_variants=1`, `set_variants=1`) ولا يوجد missing modeled tables.

**مخرجات Phase 22 ORM coverage (مطبقة على 11/11 شركة + النظام):**
- إضافة نماذج ORM لوحدة MFG/attachments/commissions: `attachments`, `bill_of_materials`, `bom_outputs`, `check_status_log`, `commission_rules`.
- توسيع `MODELED_TABLES` من 131 إلى 136 جدولًا.
- نتيجة التحقق: الجداول الخمسة مستقرة عبر جميع الشركات (`present=11/11`, `ordered_variants=1`, `set_variants=1`) ولا يوجد missing modeled tables.

**مخرجات Phase 23 ORM coverage (مطبقة على 11/11 شركة + النظام):**
- إضافة نماذج ORM لوحدة reporting/documents/fx/crm contacts: `financial_reports`, `document_types`, `document_templates`, `currency_transactions`, `crm_contacts`.
- توسيع `MODELED_TABLES` من 136 إلى 141 جدولًا.
- نتيجة التحقق: الجداول الخمسة مستقرة عبر جميع الشركات (`present=11/11`, `ordered_variants=1`, `set_variants=1`) ولا يوجد missing modeled tables.

**مخرجات Phase 24 ORM coverage (مطبقة على الشركات الحالية + النظام):**
- إضافة نماذج ORM لوحدة mfg/capacity/contracts/crm/customer groups: `bom_components`, `capacity_plans`, `contract_amendments`, `crm_knowledge_base`, `customer_groups`.
- توسيع `MODELED_TABLES` من 141 إلى 146 جدولًا.
- نتيجة التحقق: الجداول الخمسة مستقرة عبر جميع الشركات الحالية (`present=2/2`, `ordered_variants=1`, `set_variants=1`) ولا يوجد missing modeled tables.

**مخرجات Phase 25 ORM coverage (مطبقة على الشركات الحالية + النظام):**
- إضافة نماذج ORM لوحدة dashboard/fiscal/gosi/intercompany/landed costs: `dashboard_layouts`, `fiscal_periods`, `gosi_settings`, `intercompany_transactions`, `landed_cost_allocations`.
- توسيع `MODELED_TABLES` من 146 إلى 151 جدولًا.
- نتيجة التحقق: الجداول الخمسة مستقرة عبر جميع الشركات الحالية (`present=2/2`, `ordered_variants=1`, `set_variants=1`) ولا يوجد missing modeled tables.

**مخرجات Phase 26 ORM coverage (مطبقة على الشركات الحالية + النظام):**
- إضافة نماذج ORM لوحدة landed costs/leasing/leave carryover/security login: `landed_costs`, `landed_cost_items`, `lease_contracts`, `leave_carryover`, `login_attempts`.
- توسيع `MODELED_TABLES` من 151 إلى 156 جدولًا.
- نتيجة التحقق: الجداول الخمسة مستقرة عبر جميع الشركات الحالية (`present=2/2`, `ordered_variants=1`, `set_variants=1`) ولا يوجد missing modeled tables.

**مخرجات Drift-fix bulk normalization (مطبقة على 11/11 شركة + النظام):**
- إنشاء migration شامل idempotent: `alembic/versions/c1f4e8d9b2a6_bulk_drift_normalization.py`.
- تغطية 27 جدولًا و90 عمودًا (إضافة أعمدة ناقصة + توحيد النوع + توحيد nullable) على الجداول غير الممثلة ORM.
- نتيجة التحقق بعد التطبيق: `REMAINING_DRIFT_SET=0` (لا يوجد drift بنيوي متبقٍ في الجداول الكاملة الحضور).
- ملاحظة فنية: تبقى `REMAINING_DRIFT_ORDER_ONLY=20` كاختلاف ترتيب أعمدة فقط (`set_variants=1`) بدون اختلاف بنيوي.
- توحيد نسخة Alembic: كل الشركات والنظام على `c1f4e8d9b2a6`.

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

*آخر تحديث: 2026-03-30*
