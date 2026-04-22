# المرحلة 7 · مركز المبيعات (Sales + CRM + POS + CPQ + Contracts + Subscriptions) — نتائج الفحص

**التاريخ:** 22 أبريل 2026 · **البيئة:** `aman_d24b1b1c` · **النطاق:** 13 router + 2 service (~9,771 LoC · 83+ endpoints)

---

## 1 · ملخّص تنفيذي

| المجال | التقييم | ملاحظات |
|---|---|---|
| دورة المبيعات (Quote → SO → DO → Invoice → Payment) | ✅ جيد جداً | GL متكامل · AR/Revenue/VAT متوازن · COGS perpetual |
| Credit Notes / Sales Returns | ✅ ممتاز | GL reversal صحيح · historical cost recovery |
| POS Core + Sessions + GL | ✅ ممتاز | FOR UPDATE locks · cash over/short GL · fiscal lock |
| POS Loyalty + Promotions | ✅ مطبّق | pos_loyalty_programs + pos_promotions endpoints (lines 1299-1400+ / 1162-1226) |
| POS Offline Sync | ⚠️ محدود | PWA manifest فقط — لا conflict resolution flow |
| CPQ | ✅ آمن | Decimal arithmetic · لا eval() · Quote→SO preserves pricing |
| Contracts + Amendments | ✅ مطبّق | `contract_amendments` table immutable + old/new values محفوظة |
| Contract Milestone/Auto-Invoice Billing | ❌ غير مطبّق | لا `contract_milestones` table ولا scheduler |
| Subscriptions Core (enroll/proration/GL) | ✅ ممتاز | Decimal proration · deferred revenue schedule · GL via `create_journal_entry` |
| Subscriptions Dunning/Retry | ❌ غير مطبّق | لا dunning logic لفواتير الاشتراك الفاشلة |
| CRM (leads/opportunities/tickets/campaigns) | ⚠️ ثغرة عزل | `branch_id` مُخزّن لكن **لا يُستخدم للفلترة** |
| Permissions | ✅ ممتاز | 97.6% (81/83) · الباقي intentional (public reports) |

**النتيجة:** المبيعات الأساسية + المحاسبة + POS **ناضجة ومُحكمة**. الفجوات الحقيقية: 3 ميزات workflow غير مكتملة (Dunning · Milestone Billing · POS Offline Sync) + فجوة عزل branch في CRM.

---

## 2 · أرقام مرجعية

### 2.1 Code metrics
| File | LoC | Endpoints |
|---|---|---|
| `routers/sales/invoices.py` | 899 | 4 |
| `routers/sales/credit_notes.py` | 685 | 6 |
| `routers/sales/returns.py` | 496 | 3 |
| `routers/sales/sales_improvements.py` | 520 | 7 |
| `routers/sales/vouchers.py` | 545 | 2 |
| `routers/sales/customers.py` | 446 | 5 |
| `routers/sales/cpq.py` | 364 | 6 |
| `routers/sales/orders.py` | 244 | 3 |
| `routers/sales/quotations.py` | 201 | 3 |
| `routers/crm.py` | 1,966 | 18 |
| `routers/pos.py` | 1,709 | 8 |
| `routers/contracts.py` | 695 | 8 |
| `routers/finance/subscriptions.py` | 406 | 9 |
| `services/subscription_service.py` | 721 | — |
| `services/cpq_service.py` | 268 | — |
| **Total** | **9,771** | **83+** |

### 2.2 DB tables (public schema)
60 جدول في نطاق المبيعات + CRM + POS + CPQ + Contracts + Subscriptions, أبرزها:
`sales_orders`, `sales_order_lines`, `sales_quotations`, `sales_quotation_lines`, `sales_returns`, `sales_return_lines`, `invoices`, `invoice_lines`, `sales_commissions`, `commission_rules`, `sales_targets`, `sales_opportunities`, `delivery_orders`, `delivery_order_lines`, `cpq_quotes`, `cpq_quote_lines`, `cpq_pricing_rules`, `contracts`, `contract_items`, `contract_amendments`, `subscription_plans`, `subscription_enrollments`, `subscription_invoices`, `pos_sessions`, `pos_orders`, `pos_order_lines`, `pos_order_payments`, `pos_payments`, `pos_returns`, `pos_return_items`, `pos_tables`, `pos_table_orders`, `pos_kitchen_orders`, `pos_loyalty_programs`, `pos_loyalty_points`, `pos_loyalty_transactions`, `pos_promotions`, `crm_contacts`, `crm_customer_segments`, `crm_customer_segment_members`, `crm_knowledge_base`, `crm_lead_scores`, `crm_lead_scoring_rules`, `crm_sales_forecasts`, `marketing_campaigns`, `campaign_recipients`, `campaign_lead_attributions`, `support_tickets`, `ticket_comments`, `opportunity_activities`.

---

## 3 · ادعاءات أولية تم دحضها بالتحقّق (False Positives)

> **منهجية:** الفحص الآلي الأولي أشار إلى 3 P0 + 3 P1. بعد القراءة الكاملة للكود، **4 منها كانت false positives** من قراءات subagent ناقصة.

| ادعاء أولي | الحالة | الدليل |
|---|---|---|
| POS loyalty غير مُطبّق | ❌ **FALSE POSITIVE** | `pos.py:1299-1400+` — enroll, earn, redeem endpoints موجودة + جداول `pos_loyalty_*` populated |
| POS promotions غير مطبّقة | ❌ **FALSE POSITIVE** | `pos.py:1162-1226` — CRUD كامل على `pos_promotions` |
| Contract amendments بدون version history | ❌ **FALSE POSITIVE** | `contracts.py:594-636` — `list_amendments` + `create_amendment` يستخدمان `contract_amendments` table مع `old_value`/`new_value` محفوظة immutably |
| Partial invoice بدون fiscal lock (P0) | ❌ **FALSE POSITIVE** | `sales_improvements.py:409` يُنشئ فاتورة بحالة `draft` **بدون GL posting** — الـ fiscal lock يُطبّق لاحقاً في `invoices.py:160` عند الترحيل الفعلي |

---

## 4 · الـ Findings المؤكّدة (بعد التحقّق)

### 4.1 P1 — High Priority

| ID | Title | Evidence | Status |
|---|---|---|---|
| **SUB-F1** | Dunning / Retry Logic مفقود في الاشتراكات | `services/subscription_service.py` + `routers/finance/subscriptions.py`: لا يوجد أي reference لـ `dunning`/`retry`/`past_due`/`next_retry`/`failed_at`. الفواتير الفاشلة تبقى معلّقة بلا workflow استرداد | 🟡 OPEN |
| **CRM-F1** | Branch isolation في CRM لا يُطبّق على الاستعلامات | `routers/crm.py`: الـ `branch_id` يُخزّن على leads/opportunities/tickets/campaigns (lines 209, 425, 548, 677) لكن **لا يوجد أي `WHERE branch_id=` أو `AND branch_id=`** في list endpoints. مستخدم من branch A قد يرى سجلات branch B | 🟡 OPEN |

### 4.2 P2 — Medium

| ID | Title | Evidence | Status |
|---|---|---|---|
| **CON-F1** | Contract Milestone Billing / Auto-Invoice Scheduler غير مطبّق | لا `contract_milestones` table في schema. `contracts.py` لا يحتوي endpoints لـ milestone billing. Auto-invoice من العقد يعتمد فقط على subscription module، غير متاح للعقود التقليدية | 🟡 OPEN |
| **POS-F1** | POS Offline Sync محدود على PWA cache فقط | `pos.py:1665` و `:1687` — PWA manifest + cached products/settings. لا يوجد endpoint لـ bulk sync للطلبات المُنشأة offline مع conflict resolution (مثل `client_uuid` + `idempotency_key` + reconciliation flow). الـ AUDIT_PLAN يتطلّب "Offline Mode + Sync + Conflict Resolution" | 🟡 OPEN |

### 4.3 P3 — Enhancements

| ID | Title | Evidence | Status |
|---|---|---|---|
| **SALES-F1** | `create_partial_invoice` يَستخدم `NOW()` hardcoded | `sales_improvements.py:409` — `invoice_date` يُثبّت كـ `NOW()` دون accepting client date، مُقبول لكنه غير مرن للـ backdated partial billing | 🟡 OPEN |
| **CRM-F2** | Campaign execution idempotency ضعيفة | `crm.py:750-830` — second execution يتخطّى (line 767) لكن بدون rollback للـ partial state عند فشل منتصف الـ loop | 🟡 OPEN |

---

## 5 · ما يعمل بشكل صحيح (يُوثّق)

### 5.1 GL Integrity — Sales Invoice 🏆
`sales/invoices.py:588-695`:
- `acc_map_ar` (DR) + `acc_map_sales_rev` (CR) + `acc_map_vat_out` (CR) — متوازن
- Perpetual inventory: COGS (DR) + Inventory (CR) at cost layer
- `check_fiscal_period_open(db, invoice.invoice_date)` قبل أي JE
- Credit limit check مع `FOR UPDATE` على `parties` (line 281) — TOCTOU-safe
- Inventory deduction مع `FOR UPDATE` (line 356)

### 5.2 Credit Notes GL Reversal 🏆
`sales/credit_notes.py:277-324`:
- Sales Revenue (DR) + VAT Output (DR) + AR (CR) — reversal صحيح
- `related_invoice_id` محفوظ + تحديث `paid_amount` على الفاتورة الأصل
- `current_balance -= amount` على الـ party — متّسق

### 5.3 Sales Returns 🏆
`sales/returns.py:340-395`:
- Historical `unit_cost` يُسترجع من `inventory_transactions` (line 340-355)
- Inventory quantity adds back (line 350)
- Refund GL: Cash/Bank (CR) + AR (DR) — balanced
- Treasury balance synced

### 5.4 POS Session + Cash Over/Short 🏆
`pos.py:39-270`:
- Session open: `FOR UPDATE SKIP LOCKED` منع سباق duplicate session
- Session close: `difference = cash_register - expected` مع GL entry متوازن على الفرق
- Fiscal lock في close_session (line 255)

### 5.5 POS Order Posting 🏆
`pos.py:454-550`:
- Cash/Bank (DR) + Revenue (CR) + VAT (CR) + COGS/Inventory (DR/CR)
- `FOR UPDATE` على inventory قبل الخصم (line 420)

### 5.6 Subscription Billing 🏆
`services/subscription_service.py`:
- Proration daily (lines 303-309): `remaining_days / total_days * old_amount` — Decimal
- Deferred revenue schedule (lines 226-254): monthly straight-line = IFRS 15 compliant
- GL posting عبر `create_journal_entry` (line 316) — AR / Revenue / VAT

### 5.7 CPQ Price Engine 🏆
`services/cpq_service.py:53-115`:
- Decimal arithmetic فقط — **لا eval() ولا exec() ولا user-expression evaluation**
- Rules = SQL-based constraints (requires/excludes), ليست runtime code

### 5.8 Vouchers (Customer Receipts) 🏆
`sales/vouchers.py:78-151`:
- `FOR UPDATE` على invoice row قبل تخصيص الدفع — anti-over-allocation
- GL Receipt balanced (Cash/Bank DR + AR CR)
- Fiscal lock (line 52)

---

## 6 · الإصلاحات المُطبّقة في الجلسة

**لا شيء.** جميع الـ findings الـ P0 الأولية ظهرت **false positives**. الـ findings الحقيقية (SUB-F1 · CRM-F1 · CON-F1 · POS-F1) تتطلّب:
- **SUB-F1**: جدول جديد `subscription_payment_failures` + job scheduler + dunning templates — عمل متوسط يحتاج موافقة تصميم
- **CRM-F1**: تعديل ~18 endpoint لإضافة `AND branch_id IN (...allowed)` + قرار سياسة (هل ALL branches مسموح للـ CRM admins؟) — يحتاج قرار منتج
- **CON-F1**: جدول `contract_milestones` جديد + scheduler — ميزة كاملة
- **POS-F1**: endpoint bulk sync + idempotency_key + conflict resolution — ميزة كاملة

كل هذه مُوثّقة في الـ Backlog للـ Sprint القادم.

---

## 7 · Backlog (مُرتّب بالأولوية)

| # | ID | العمل | Effort | Severity |
|---|---|---|---|---|
| 1 | CRM-F1 | Branch isolation على CRM list endpoints | M | P1 |
| 2 | SUB-F1 | Dunning/retry pipeline للاشتراكات | L | P1 |
| 3 | CON-F1 | `contract_milestones` + billing scheduler | L | P2 |
| 4 | POS-F1 | POS offline sync flow + conflict resolution | L | P2 |
| 5 | CRM-F2 | Campaign execution idempotency (DB transaction + resume) | S | P3 |
| 6 | SALES-F1 | Partial invoice يقبل `invoice_date` من payload مع fiscal lock | XS | P3 |

---

## 8 · KPIs للمرحلة

| المقياس | الهدف | الحالة | التقييم |
|---|---|---|---|
| Permission coverage | 100% | 97.6% (81/83) | ✅ acceptable |
| GL posting على الفواتير | 100% | 100% | ✅ |
| Fiscal lock على GL endpoints | 100% | 100% (على الترحيل الفعلي) | ✅ |
| FOR UPDATE على stock OUT / balance / invoices | 100% | 100% | ✅ |
| CPQ بدون runtime eval | ✓ | ✓ | ✅ |
| POS session lifecycle + GL | ✓ | ✓ | ✅ |
| POS Loyalty + Promotions | ✓ | ✓ | ✅ |
| Subscription proration دقيقة | ✓ | ✓ (Decimal) | ✅ |
| Subscription deferred revenue (IFRS 15) | ✓ | ✓ | ✅ |
| Subscription dunning | ✓ | ✗ | ⚠️ (P1) |
| Contract amendments immutable | ✓ | ✓ | ✅ |
| Contract milestone billing | ✓ | ✗ | ⚠️ (P2) |
| POS offline sync | ✓ | PWA cache فقط | ⚠️ (P2) |
| CRM branch isolation | ✓ | branch_id مخزّن لا مُستخدم | ⚠️ (P1) |

---

**ملاحظة منهجية:** 4 من 6 ادعاءات P0/P1 الأولية كانت قراءات ناقصة (Loyalty, Promotions, Contract Amendments, Partial Invoice Fiscal Lock). التحقّق الصارم منع regressions محتملة. الـ 4 فجوات الحقيقية المتبقّية جميعها ميزات workflow تتطلّب تصميم + لا bugs حرجة تهدّد البيانات الحالية.

---

**آخر تحديث:** 2026-04-22 · **مسؤول الفحص:** GitHub Copilot (session) · **الحالة:** مكتمل · **المرجع:** `docs/audit/AUDIT_PLAN.md`
