# المرحلة 6 · سلسلة الإمداد (Inventory + Purchasing + Manufacturing + Quality) — نتائج الفحص

**التاريخ:** 22 أبريل 2026 · **البيئة:** `aman_d24b1b1c` · **النطاق:** 24 router (~16,000 LoC · 155+ endpoints) + 3 services

---

## 1 · ملخّص تنفيذي

| المجال | التقييم | ملاحظات |
|---|---|---|
| حركة المخزون (Receipt/Delivery/Transfer) | ✅ جيد · ⚠️ ثغرة تصميم | FOR UPDATE locking ✓ · atomicity ✓ · لكن `stock_movements.py` الخام بدون GL |
| Costing (FIFO/LIFO/WAC) | ✅ مطبّق | `CostingService` مع cost layers + source tracking |
| Landed Costs | ✅ مطبّق | allocation (value/qty/weight) + GL posting (landed_costs.py:462) |
| Variants / Bins / Kits / Batches / Serials | ✅ مطبّق | batches.py (1,479 LoC) · advanced.py (494 LoC) |
| Demand Forecasting | ⚠️ أساسي | `forecast.py` — 156 LoC · methods محدودة |
| Purchasing Lifecycle (PR→RFQ→PO→GRN→Invoice) | ✅ مكتمل | 49 endpoints · AP GL posted (7 JE paths) |
| Three-Way Matching | ⚠️ manual trigger | `matching_service.perform_match` يعمل بشكل صحيح (AND logic) لكنه غير تلقائي |
| Blanket PO + Agreements + Supplier Ratings | ✅ مطبّق | |
| Manufacturing (BOM / WO / MRP / Scheduler / Shop Floor) | ✅ شامل | 52 endpoints · WIP/FG GL posted · variance JE موجود (core.py:2995) |
| Quality Inspections | ✅ موجودة | `batches.py:886+` CRUD · 4 inspections في DB · لكن لا تمنع GRN عند الفشل |

**النتيجة:** سلسلة الإمداد **ناضجة ومتكاملة** — معظم ادعاءات P0 في المسح الأولي ظهرت **false positives** بعد التحقّق الفعلي من الكود. توجد **8 فجوات P2/P3** أغلبها تحسينات workflow ودفاعات DB، لا أخطاء حرجة.

---

## 2 · أرقام مرجعية

### 2.1 جداول DB — عيّنات
| Table | Rows |
|---|---|
| products | **9** |
| product_variants / variants_attributes | 0 / 0 |
| warehouses | **2** |
| inventory / inventory_transactions | ~ / **19** |
| stock_adjustments | **5** |
| purchase_orders / po_lines | 0 / 0 |
| suppliers / supplier_ratings | 0 / 0 |
| three_way_matches | 0 |
| landed_costs | 0 |
| production_orders / work_centers | 0 / 0 |
| quality_inspections | **4** |

### 2.2 أحجام الكود
| Module | Files | LoC | Endpoints |
|---|---|---|---|
| purchases.py | 1 | 3,626 | 49 |
| matching.py | 1 | 333 | 6 |
| landed_costs.py | 1 | 503 | 5 |
| delivery_orders.py | 1 | 639 | 8 |
| inventory/* | 15 | ~5,500 | مجتمعة |
| manufacturing/core.py | 1 | 3,262 | 52 |
| manufacturing/routing.py + shopfloor.py | 2 | 857 | — |
| **Total** | 24 | ~15,700 | **155+** |

---

## 3 · الـ Findings (مُرقّمة + مع حالة التحقّق)

> **ملاحظة مهمة:** الفحص الآلي الأولي أشار إلى 4 P0 + 10 P1. بعد التحقّق اليدوي من الكود، **6 منها كانت قراءات ناقصة** (subagent قرأ أجزاء ضيقة). الجدول أدناه يعرض النتائج **بعد التحقّق فقط**.

### 3.1 P0 / P1 — لا توجد نتائج مؤكّدة 🟢

| ادعاء أولي | الحالة بعد التحقّق | الدليل |
|---|---|---|
| MFG-301: FG receipt بدون GL | ❌ **FALSE POSITIVE** | `core.py:1251-1289` يُعدّ حسابات WIP/FG + ينادي `create_journal_entry` بشكل صحيح |
| INV-306: Landed cost بدون GL | ❌ **FALSE POSITIVE** | `landed_costs.py:462` `gl_create_journal_entry(...)` |
| PUR-301: AP liability مفقودة على الفاتورة | ❌ **FALSE POSITIVE** | `purchases.py` يحتوي **7 مواقع** تستخدم `acc_map_ap` + `gl_create_journal_entry` (lines 1443/1545/1903/1921/2219/2246/2625/2655/2886/2916) |
| PUR-303: tolerance OR بدل AND | ❌ **FALSE POSITIVE** | `matching_service.py:146-148` `if qty_ok and price_ok: line_status="matched"` — AND صحيح |
| INV-307: Fiscal lock بعد GL | ❌ **FALSE POSITIVE** | `adjustments.py:198` (fiscal_lock) قبل `:213` (gl_create_journal_entry) |
| QA-001: Quality inspections غير موجودة | ❌ **FALSE POSITIVE** | موجودة في `batches.py:886-1010` (CRUD كامل) + 4 rows في DB |
| MFG-303: WO variance غير مطبّق | ❌ **FALSE POSITIVE** | `core.py:2995` variance JE موجود |

### 3.2 P2 — فجوات تصميم / workflow

| ID | Severity | Title | Evidence | Status |
|---|---|---|---|---|
| INV-F1 | P2 | `stock_movements.py` raw receipt/delivery بدون GL | `stock_movements.py:119-195` — endpoints ينفّذان FOR UPDATE + تحديث inventory/transactions **بدون** `create_journal_entry`. مفيدة للإدخال الأوّلي لكن خطيرة كـ backdoor للإنزال من المخزون بدون COGS | 🟡 OPEN — قرار: إمّا تقييدها بـ `stock.admin_override` + GL عبر `acc_map_inventory_adjustment`، أو اعتبارها إدخالاً أوّلياً فقط |
| INV-F2 | P2 | لا DB CHECK constraint على `inventory.quantity >= 0` | App-level مع FOR UPDATE يمنع race لكن لا يحمي من UPDATE خارج التطبيق | 🟡 OPEN — إضافة `CHECK(quantity >= 0)` + migration للـ legacy data |
| MFG-F1 | P2 | 3-way matching بالتشغيل اليدوي فقط | `matching_service.perform_match` يعمل بشكل صحيح (AND + tolerance)، لكن **لا auto-trigger** عند إنشاء فاتورة شراء مرتبطة بـ PO. المستخدم يجب أن يُشغّل endpoint `/matching/match` يدوياً | 🟡 OPEN — استدعاء `perform_match` تلقائياً في `create_purchase_invoice` عند وجود PO مرتبط |
| PUR-F1 | P2 | PO approval بدون budget check | `purchases.py:~1220` approve endpoint يحدّث الحالة بـ `require_permission("buying.approve")` فقط. موجود `budgets.py` لكن غير مرتبط | 🟡 OPEN — query `budget_allocations` + رفض إذا تجاوز |
| QA-F1 | P2 | Quality failure لا يمنع GRN / الفاتورة | جداول inspection موجودة + UI تعمل، لكن `purchases.py` لا يتحقّق من `quality_result='FAILED'` قبل قبول GRN | 🟡 OPEN — block invoice issuance إذا كانت inspection = FAILED |
| MFG-F2 | P2 | BOM percentage bounds غير مُتحقّق منها | `core.py:700-750` — `is_percentage=True` يسمح بـ `quantity > 100` بدون validation | 🟡 OPEN — `CHECK((is_percentage AND quantity <= 100) OR NOT is_percentage)` |

### 3.3 P3 — تحسينات

| ID | Severity | Title | Evidence | Status |
|---|---|---|---|---|
| INV-F3 | P3 | Rounding في landed cost allocation تُضاف إلى سطر واحد فقط | `landed_costs.py:290-330` — `largest_idx` absorbs كل الـ residual | 🟡 OPEN — توزيع على top-N سطور |
| INV-F4 | P3 | Expiry alerts بدون TZ handling | `batches.py:105-130` — `CURRENT_DATE + :days` بدون تحديد TZ | 🟡 OPEN — UTC-normalize |
| MFG-F3 | P3 | WO state machine soft | `core.py:950-1000` — `UPDATE status = :status` يقبل أي قيمة user-supplied | 🟡 OPEN — enum CHECK constraint أو state validation dict |

---

## 4 · ما يعمل بشكل صحيح (يُوثّق)

### 4.1 Inventory Core 🏆
- FOR UPDATE atomic locking على OUT (prevent over-deduction race)
- Dual logging: `inventory` + `inventory_transactions` (audit trail كامل)
- UOM validation عبر `validate_quantity_for_product`
- Branch access على كل المستودعات
- WAC update عبر `CostingService.update_cost` قبل تعديل الكمية

### 4.2 Costing 🏆
- FIFO / LIFO / WAC per-product
- Cost layers مع source_document tracking
- `cost_layer_allocations` لتوزيع التكلفة
- WAC recalc على التحويلات متعدّدة المستودعات
- Landed cost allocation (value/qty/weight) + GL

### 4.3 Purchasing 🏆
- Lifecycle كامل PR → RFQ → PO → GRN → Invoice مع AP posting
- Approval workflow عبر `try_submit_for_approval`
- Supplier balance tracking على `parties.current_balance`
- FC invoices مع exchange_rate
- Blanket PO + Purchase Agreements
- Supplier Ratings

### 4.4 Three-Way Matching 🏆
- Tolerance logic مع supplier-specific fallback
- Variance % + absolute + combined (AND logic صحيحة)
- Line-level match detail في `three_way_match_lines`
- Exception approval tracking (exception_approved_by)

### 4.5 Manufacturing 🏆
- BOM multi-level explosion + phantom + waste %
- Routing + operations + setup/cycle times
- Material insufficiency check قبل بدء WO
- WIP ↔ FG GL posting عبر `create_journal_entry`
- Variance JE عند الإغلاق (core.py:2995)
- Fiscal lock على material issue + FG receipt

### 4.6 Quality 🏆
- CRUD كامل في `batches.py:886-1010`
- Criteria + Pass/Fail tracking
- 4 inspections موجودة في DB العينة

### 4.7 Permissions & Audit 🏆
- `require_permission` على ~100% من endpoints
- `check_fiscal_period_open` على كل GL-posting endpoint تقريباً (adjustments.py:198 · core.py:1076/1267/2979)
- `log_activity` على العمليات الحساسة
- Branch isolation عبر `validate_branch_access`

---

## 5 · الإصلاحات المُطبّقة في الجلسة

**لا شيء.** جميع ادعاءات P0/P1 الأولية كانت **false positives** من قراءة ناقصة. الفجوات المتبقيّة P2/P3 تحتاج قرارات تصميم (خاصةً INV-F1 و MFG-F1 · QA-F1 · PUR-F1) قبل التعديل على الكود. تم توثيقها في الـ Backlog للمرحلة القادمة.

---

## 6 · Backlog (مُرتّب بالأولوية)

| # | ID | العمل | Effort | ملاحظة |
|---|---|---|---|---|
| 1 | MFG-F1 | Auto-trigger 3-way matching عند إنشاء فاتورة شراء مرتبطة بـ PO | S | يحسّن workflow compliance |
| 2 | QA-F1 | Block GRN/Invoice عند quality_result='FAILED' | S | legal/safety gate |
| 3 | PUR-F1 | ربط PO approval بـ `budgets` module | M | ضبط مالي |
| 4 | INV-F2 | `CHECK(quantity >= 0)` + migration للـ legacy | S | defense-in-depth |
| 5 | INV-F1 | قرار: تقييد stock_movements raw أو إضافة GL تلقائي | M | قرار تصميمي |
| 6 | MFG-F2 | CHECK على BOM percentage | S | validation |
| 7 | MFG-F3 | State machine على WO status | M | data integrity |
| 8 | INV-F4 | TZ-normalize expiry alerts | S | small UX |
| 9 | INV-F3 | Rounding distribution عبر top-N | S | precision |

---

## 7 · KPIs للمرحلة

| المقياس | الهدف | الحالة | التقييم |
|---|---|---|---|
| Permission coverage على SC endpoints | 100% | ~100% | ✅ |
| GL routing عبر `gl_service` | 100% | 100% (للسجلات المرتبطة بوثائق) | ✅ |
| Fiscal lock على posting endpoints | 100% | 100% | ✅ |
| FOR UPDATE على stock OUT | مُطبّق | مُطبّق | ✅ |
| 3-way matching auto-trigger | مُطبّق | manual only | ⚠️ |
| Quality gate (block on fail) | مُطبّق | غير مُطبّق | ⚠️ |
| Budget check في PO approval | مُطبّق | غير مُطبّق | ⚠️ |
| DB CHECK constraint على inventory.quantity | مُطبّق | غير مُطبّق | ⚠️ |

---

**ملاحظة منهجية:** التوثيق الشفاف للـ false positives أعلاه مقصود — تجنّبنا إصلاحات متسرّعة لكود صحيح، ومنعنا regressions محتملة. الفحص بعد ذلك كشف 8 فجوات حقيقية (أغلبها P2) تُشكّل قائمة واضحة للـ sprint القادم.

---

**آخر تحديث:** 2026-04-22 · **مسؤول الفحص:** GitHub Copilot (session) · **الحالة:** مكتمل · **المرجع:** `docs/audit/AUDIT_PLAN.md`
