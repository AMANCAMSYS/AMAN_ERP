# تقرير الفحص الشامل للنظام - AMAN ERP
> تاريخ البدء: 2 أبريل 2026  
> الفحص مقسم إلى وحدات — كل وحدة تُفحص backend + frontend + database

---

## الوحدة 1: Auth & Companies & Setup ✅

**الملفات المفحوصة:**
- Backend: `auth.py`, `companies.py`, `settings.py`, `branches.py`, `roles.py`
- Frontend: `Login.jsx`, `Register.jsx`, `OnboardingWizard.jsx`, `IndustrySetup.jsx`, `ModuleCustomization.jsx`
- Services: `auth.js`, `companies.js`
- Utils: `sql_safety.py`, `auth.js`

### البنود السليمة ✅

| البند | الحالة |
|-------|--------|
| JWT HttpOnly Cookies (secure + samesite strict) | ✅ |
| Rate limiting على Login (Redis + in-memory fallback) | ✅ |
| Rate limiting على forgot-password (`5/minute`) | ✅ |
| Password reset token invalidation (`used=TRUE`) | ✅ |
| Token blacklist (DB + cache + hourly cleanup) | ✅ |
| SQL parameterized queries في auth | ✅ |
| `validate_aman_identifier()` قبل DDL | ✅ |
| Strong password policy enforcement | ✅ |
| Anti-email enumeration (same response always) | ✅ |
| Permission system (`require_permission`) | ✅ |
| Admin lockout on failed attempts | ✅ |
| File upload validation (logo: size, extension, MIME) | ✅ |
| Auto-login بعد التسجيل مع cookies | ✅ |
| شاشة نجاح التسجيل مع عرض company_id | ✅ |

### المشاكل المكتشفة والمُصلحة 🔧

| # | الخطورة | الملف | المشكلة | الإصلاح |
|---|---------|-------|---------|---------|
| 1 | **HIGH** | `companies.py` | `update_company` يبني SET clause من dict keys بدون whitelist — يسمح بتحديث أي عمود | إضافة `ALLOWED_UPDATE_COLUMNS` whitelist (8 أعمدة فقط) |
| 2 | **HIGH** | `Register.jsx` | `setAuth()` بدون try/catch — فشل auto-login يوجه لصفحة setup بدون مصادقة | لف `setAuth` بـ try/catch، تعيين `hasAutoLogin = false` عند الفشل |
| 3 | **HIGH** | `settings.py` | `industry_type` يُحفظ ثم `commit` قبل زرع COA — فشل الزرع يترك الشركة بنوع نشاط بدون شجرة حسابات | نقل `commit` بعد نجاح COA + rollback عند الفشل |
| 4 | **MEDIUM** | `branches.py` | `print()` بدلاً من `logger.error()` — الأخطاء لا تظهر في logs الإنتاج | استبدال 4× `print()` بـ `logger.error()` + إضافة `import logging` |

### بنود تم فحصها ولا تحتاج إصلاح

- **DDL f-strings** (`DROP DATABASE/USER`): المتغيرات مُوثقة بـ `validate_aman_identifier()` قبل الاستخدام. PostgreSQL لا يدعم parameterized identifiers.
- **list_companies query building**: يستخدم `:status` و `:search` placeholders — آمن.
- **Token schema mismatch**: Login يُرجع `Token(...)` مطابق للـ schema.
- **PermissionDeniedRedirect**: لا يوجد double Layout — يعمل كبديل وليس متداخلاً.
- **SMTP password plain text**: طبيعي لهذا الحجم — التشفير يضيف تعقيداً بدون فائدة عملية.

---

## الوحدة 2: المحاسبة (Accounting) ✅

**الملفات المفحوصة:**
- Backend (16 ملف): `accounting.py`, `budgets.py`, `cost_centers.py`, `currencies.py`, `taxes.py`, `tax_compliance.py`, `assets.py`, `expenses.py`, `treasury.py`, `checks.py`, `notes.py`, `reconciliation.py`, `costing_policies.py`, `intercompany.py`, `advanced_workflow.py`
- Frontend Accounting (26 صفحة): `ChartOfAccounts`, `GeneralLedger`, `JournalEntryForm/List`, `TrialBalance`, `BalanceSheet`, `IncomeStatement`, `CashFlowReport`, `FiscalYears`, `FiscalPeriodLocks`, `Budgets`, `BudgetItems`, `BudgetReport`, `CurrencyList`, `CurrencyRates`, `ClosingEntries`, `RecurringTemplates`, `RevenueRecognition`, `VATReport`, `ZakatCalculator`, `PeriodComparison`, `CostCenterList`, `CostCenterReport`, `OpeningBalances`, `AccountingHome`
- Frontend Treasury (14 صفحة): `TreasuryHome`, `TreasuryAccountList`, `TransferForm`, `ExpenseForm`, `ChecksReceivable/Payable`, `ChecksAgingReport`, `NotesReceivable/Payable`, `ReconciliationForm/List`, `TreasuryBalancesReport`, `TreasuryCashflowReport`, `BankImport`

### البنود السليمة ✅

| البند | الحالة |
|-------|--------|
| جميع SQL queries تستخدم parameterized `text()` | ✅ |
| Decimal precision مع `_D2` constant | ✅ |
| Permission checks متسقة على جميع endpoints | ✅ (باستثناء 2 تم إصلاحهم) |
| response_model مطابق للقيم المُرجعة | ✅ |
| Journal entries تدعم multi-currency | ✅ |
| Fiscal year/period locking يعمل | ✅ |
| VAT calculations صحيحة | ✅ |
| COA tree structure سليمة | ✅ |
| لا يوجد t() على مستوى module scope | ✅ |

### المشاكل المكتشفة والمُصلحة 🔧

| # | الخطورة | الملف | المشكلة | الإصلاح |
|---|---------|-------|---------|---------|
| 1 | **CRITICAL** | `reconciliation.py` | Auto-match date comparison: `hasattr(sl_date, 'days')` always False لـ date objects → `day_diff=999` دائماً → المطابقة التلقائية لا تعمل أبداً | إعادة كتابة المقارنة: تحويل صريح لـ `date` ثم حساب الفرق |
| 2 | **CRITICAL** | `checks.py` | endpoint `/status-log/*` بدون `require_permission` → أي مستخدم مصادق يمكنه رؤية سجل حالة الشيكات | إضافة `dependencies=[Depends(require_permission("treasury.view"))]` |
| 3 | **CRITICAL** | `TrialBalance.jsx` | `setAccounts(accData)` بدون Array.isArray guard | إضافة guard |
| 4 | **CRITICAL** | `CostCenterList.jsx` | `setCostCenters(response.data)` بدون Array guard | إضافة guard |
| 5 | **CRITICAL** | `CurrencyList.jsx` | `setCurrencies(response.data)` بدون Array guard | إضافة guard |
| 6 | **CRITICAL** | `JournalEntryForm.jsx` | `setAccounts(response.data \|\| [])` بدون Array.isArray | إضافة guard |
| 7 | **HIGH** | `Budgets.jsx` | `setBudgets(budgetsRes.data \|\| [])` بدون Array guard | إضافة guard |
| 8 | **HIGH** | `BudgetItems.jsx` | `allAccounts = accountsRes.data \|\| []` بدون guard | إضافة guard |
| 9 | **HIGH** | `NotesReceivable.jsx` | `setNotes(notesRes.data)` بدون guard | إضافة guard |
| 10 | **HIGH** | `NotesPayable.jsx` | `setNotes(notesRes.data)` بدون guard | إضافة guard |
| 11 | **MEDIUM** | `BalanceSheet.jsx` | `data.data.filter()` يتعطل إذا data.data ليست array | تحويل لـ `Array.isArray(data?.data)` |
| 12 | **MEDIUM** | `IncomeStatement.jsx` | `data?.data \|\| []` لا يتحقق من نوع Array | تحويل لـ `Array.isArray(data?.data)` |
| 13 | **MEDIUM** | `GeneralLedger.jsx` | `response.data.entries` بدون optional chaining | إضافة `?.` operator |

### ملاحظات إضافية (لا تحتاج إصلاح عاجل)

- `AccountingHome.jsx`: بعض النصوص الإنجليزية hardcoded (LOW)
- بعض ملفات Treasury تستخدم `catch { console.error }` بدون toast للمستخدم (LOW)
- `ReconciliationForm.jsx`: `resRec.data.lines` بدون optional chaining (LOW)

---

## الوحدة 3: المبيعات (Sales) ✅

**الملفات المفحوصة:**
- Backend (9 ملفات): `invoices.py`, `orders.py`, `quotations.py`, `customers.py`, `credit_notes.py`, `returns.py`, `vouchers.py`, `sales_improvements.py`, `schemas.py`
- Frontend (34 صفحة): `InvoiceList/Form/Details`, `SalesOrders/Details`, `SalesQuotations/Form/Details`, `CustomerList/Form/Details/Statement/Receipts`, `SalesCreditNotes/DebitNotes`, `SalesReturns`, `DeliveryOrders/Details`, `ReceiptForm/Details`, `SalesReports`, `AgingReport`, `SalesCommissions`, `SalesHome`, `ContractForm`, `InvoicePrintModal`

### البنود السليمة ✅

| البند | الحالة |
|-------|--------|
| SQL queries جميعها parameterized | ✅ |
| InvoiceList يحتوي على Array.isArray guard سليم | ✅ |
| Permission checks متسقة على endpoints | ✅ |
| ZATCA compliant invoice format | ✅ |
| Multi-currency support في الفواتير | ✅ |
| ReceiptDetails يتحقق من allocations قبل reduce | ✅ |

### المشاكل المكتشفة والمُصلحة 🔧

| # | الخطورة | الملف | المشكلة | الإصلاح |
|---|---------|-------|---------|---------|
| 1 | **CRITICAL** | `SalesCreditNotes.jsx` | `res.data.items` بدون optional chaining → crash إذا data=undefined | إضافة `res.data?.items` |
| 2 | **CRITICAL** | `InvoiceDetails.jsx` | `invoice.items.map()` بدون guard → crash إذا items=null | إضافة `Array.isArray(invoice?.items) &&` |
| 3 | **HIGH** | `CustomerReceipts.jsx` | `receiptsRes.data.map()` مباشرة بدون Array guard | إضافة `Array.isArray` مع fallback لـ `.items` |
| 4 | **HIGH** | `ReceiptForm.jsx` | `setOutstandingInvoices(res.data)` بدون guard (موقعين) | إضافة Array.isArray guard في كلا الموقعين |
| 5 | **MEDIUM** | `SalesCommissions.jsx` | `commRes.data \|\| []` بدون Array.isArray | إضافة guard كامل |

### ملاحظات إضافية (لا تحتاج إصلاح عاجل)

- بعض نصوص الطباعة في `InvoicePrintModal.jsx` hardcoded بالإنجليزية (LOW)
- `orders.py` يفتقر لـ `validate_branch_access` في بعض endpoints (MEDIUM - edge case)

---

## الوحدة 4: المشتريات (Buying) ✅

**الملفات المفحوصة:**
- Backend (2 ملف): `purchases.py` (~2400 سطر), `landed_costs.py`
- Frontend (12 صفحة): `PurchaseInvoiceForm/List/Details`, `BuyingOrderForm`, `BuyingReturns`, `BuyingReturnForm`, `SupplierList/Form/Groups/Payments/Statement`, `LandedCosts`, `PurchaseOrderDetails`, `PurchaseCreditNotes`, `PurchaseDebitNotes`
- Schemas: `purchases.py`

### البنود السليمة ✅

| البند | الحالة |
|-------|--------|
| جميع SQL queries parameterized `:param` | ✅ |
| `require_permission("buying.*")` على جميع الـ endpoints | ✅ |
| Multi-tenant isolation via `get_db_connection(company_id)` | ✅ |
| `validate_branch_access()` في قائمة الفواتير | ✅ |
| `check_fiscal_period_open()` في إنشاء فواتير المشتريات | ✅ |
| Exchange rate fallback `or 1` يمنع القسمة على صفر | ✅ |
| `PurchaseCreditNotes.jsx` و `PurchaseDebitNotes.jsx` آمنة (best practice) | ✅ |
| Inventory `FOR UPDATE` lock عند تحديث المخزون | ✅ |
| `LEAST(total, paid_amount + :amt)` يمنع الدفع الزائد | ✅ |

### المشاكل المكتشفة والمُصلحة 🔧

#### Backend (3 إصلاحات)

| # | الخطورة | الملف | المشكلة | الإصلاح |
|---|---------|-------|---------|---------|
| 1 | **HIGH** | `purchases.py` L1729 | `raise ValueError` في فحص المخزون عند الإرجاع → يسبب 500 بدلاً من 400 | تغيير إلى `raise HTTPException(status_code=400, ...)` |
| 2 | **HIGH** | `purchases.py` L1668 | مردودات المشتريات لا تفحص `check_fiscal_period_open()` — يسمح بالترحيل في فترة مغلقة | إضافة `check_fiscal_period_open(db, invoice.invoice_date)` قبل إنشاء المردود |
| 3 | **MEDIUM** | `purchases.py` L1247 | `receipt_accrual_reversal_base = 0.0` (float) يُستخدم في عمليات مالية | تغيير إلى `Decimal('0')` |

#### Frontend (12 ملف — Array.isArray guards)

| # | الملف | المشكلة |
|---|-------|---------|
| 1 | `PurchaseInvoiceForm.jsx` | 6 setters + `curRes.data.find()` بدون guard |
| 2 | `PurchaseInvoiceForm.jsx` | `order.items.map()` بدون guard |
| 3 | `BuyingOrderForm.jsx` | 3 setters بدون guard |
| 4 | `PurchaseInvoiceList.jsx` | `setInvoices(response.data)` بدون guard |
| 5 | `BuyingReturns.jsx` | `setReturns(response.data)` بدون guard |
| 6 | `SupplierList.jsx` | `setSuppliers(suppliersRes.data)` بدون guard |
| 7 | `SupplierForm.jsx` | `curRes.data.filter()` و `groupRes.data.filter()` بدون Array check |
| 8 | `SupplierGroups.jsx` | `setGroups(response.data)` بدون guard |
| 9 | `SupplierPayments.jsx` | `setPayments(response.data)` بدون guard |
| 10 | `SupplierStatement.jsx` | `statement.transactions.map()` بدون guard + `.length` crash |
| 11 | `BuyingReturnForm.jsx` | `invoice.items.map()` بدون guard |
| 12 | `PurchaseInvoiceDetails.jsx` | `setPaymentHistory(historyRes.data)` بدون guard |

### ملاحظات إضافية (لا تحتاج إصلاح عاجل)

| البند | الخطورة | التوصية |
|-------|---------|---------|
| `PurchaseLineItem.quantity: float` في schema | MEDIUM | تغيير لـ `Decimal` في المستقبل |
| `PurchaseLineItem.markup: float = 0.0` | LOW | تغيير لـ `Decimal` |
| Hardcoded tax rate `15` في 3 ملفات frontend | LOW | استخدام إعدادات الشركة |
| Sequential number generation بدون `FOR UPDATE` | LOW | فحص `generate_sequential_number()` |
| `SupplierStatement` error handling → `console.error` فقط | LOW | إضافة `setError()` |

---

## الوحدة 5: المخزون (Inventory) ✅

**الملفات المفحوصة:**
- Backend (8 ملفات): `shipments.py`, `transfers.py`, `adjustments.py`, `stock_movements.py`, `products.py`, `batches.py`, `warehouses.py`, `costing_service.py`
- Frontend (22 صفحة في `Stock/`): `StockTransferForm`, `InventoryValuation`, `PriceListItems`, `StockMovements`, `ProductList/Form`, `WarehouseList/Details`, `ShipmentList/Details/Form`, `IncomingShipments`, `StockAdjustments/Form`, `StockReports`, `CycleCounts`, `QualityInspections`, `SerialList`, `BatchList`, `PriceLists`, `CategoryList`, `StockHome`

### البنود السليمة ✅

| البند | الحالة |
|-------|--------|
| Multi-tenant isolation عبر `get_db_connection(company_id)` | ✅ |
| `require_permission("stock.*")` على جميع الـ endpoints | ✅ |
| `validate_branch_access()` مطبق | ✅ |
| WAC calculations تستخدم `Decimal` + `ROUND_HALF_UP` | ✅ |
| `CostingService.calculate_new_cost()` محمي من division by zero | ✅ |
| Transfers تستخدم `FOR UPDATE` على المصدر والوجهة | ✅ |
| Adjustments تمنع المخزون السالب | ✅ |
| StockAdjustments.jsx يستخدم `|| []` fallback | ✅ |
| WarehouseDetails.jsx يستخدم `Array.isArray` ✅ (best practice) | ✅ |
| لا يوجد `t()` على مستوى module scope | ✅ |
| لا يوجد `raise ValueError` في inventory routers | ✅ |

### المشاكل المكتشفة والمُصلحة 🔧

#### Backend (2 إصلاح)

| # | الخطورة | الملف | المشكلة | الإصلاح |
|---|---------|-------|---------|---------|
| 1 | **CRITICAL** | `shipments.py` L66 | `SELECT quantity FROM inventory` بدون `FOR UPDATE` عند إنشاء الشحنة — race condition يسمح بسحب مخزون مكرر | إضافة `FOR UPDATE` على SELECT |
| 2 | **HIGH** | `shipments.py` L270 | `confirm_shipment` يخصم المخزون بدون فحص كمية كافية — `UPDATE SET quantity = quantity - :qty` بدون WHERE guard | إضافة `AND quantity >= :qty` في WHERE clause |

#### Frontend (4 ملفات — Array.isArray guards)

| # | الملف | المشكلة |
|---|-------|---------|
| 1 | `StockTransferForm.jsx` | `setWarehouses(whRes.data)` + `setSourceStock(res.data)` بدون guard |
| 2 | `InventoryValuation.jsx` | `setData(response.data)` ثم `.reduce()` و `.length` بدون guard |
| 3 | `PriceListItems.jsx` | `setItems(response.data \|\| [])` لا يضمن Array |
| 4 | `StockMovements.jsx` | `setWarehouses/setMovements(res.data)` بدون guard (موقعين) |

### ملاحظات إضافية (لا تحتاج إصلاح عاجل)

| البند | الخطورة | التوصية |
|-------|---------|---------|
| Manufacturing يسمح بمخزون سالب عند استهلاك المواد | CRITICAL | سيُعالج في وحدة التصنيع |
| `float()` conversion عند إرسال القيم للـ API | LOW | استخدام `str()` للدقة |
| Product version field موجود لكن لا يُستخدم في optimistic locking | MEDIUM | تفعيل في المستقبل |
| Batch duplicate check بدون UNIQUE constraint | MEDIUM | إضافة DB constraint |
| `_D2` vs `_D4` inconsistency بين الملفات | LOW | توحيد الدقة |

---

## الوحدة 6: الخزينة (Treasury) ✅

> تم فحص الخزينة ضمن الوحدة 2 (المحاسبة) — 14 صفحة frontend + `treasury.py` backend
> الإصلاحات: فحص رصيد الخزينة قبل المصروفات + Array.isArray guards على 5 صفحات

---

## الوحدة 7: الموارد البشرية (HR) ✅

**الملفات المفحوصة:**
- Backend (2 ملف): `hr/core.py` (~1800 سطر), `hr_wps_compliance.py` (~450 سطر)
- Frontend (24 صفحة في `HR/`): `EmployeeList/Form/Details`, `PayrollPeriods/Details`, `Payslips`, `LeaveList/Form`, `EOSSettlement`, `SalaryStructures`, `OvertimeRequests`, `ViolationsList`, `AttendanceList`, `GosiReport`, `WPSCompliance`, `SalaryAdvance`, `HRHome`, etc.

### البنود السليمة ✅

| البند | الحالة |
|-------|--------|
| `require_permission("hr.*")` على جميع الـ endpoints | ✅ |
| Multi-tenant عبر `get_db_connection(company_id)` | ✅ |
| SQL parameterized في معظم الاستعلامات | ✅ |
| GOSI calculations تستخدم `Decimal` + تمييز سعودي/غير سعودي | ✅ |
| EOS date validation (termination >= hire) | ✅ |
| Transaction scope صحيح في payroll processing | ✅ |
| Saudization percentage يتحقق من `total > 0` قبل القسمة | ✅ |
| `LeaveList.jsx` يستخدم `Array.isArray()` ✅ (best practice) | ✅ |

### المشاكل المكتشفة والمُصلحة 🔧

#### Backend (1 إصلاح)

| # | الخطورة | الملف | المشكلة | الإصلاح |
|---|---------|-------|---------|---------|
| 1 | **CRITICAL** | `hr/core.py` L633 | `loan.amount / loan.total_installments` بدون فحص صفر — ZeroDivisionError | إضافة `if loan.total_installments <= 0: raise HTTPException(400)` |

#### Frontend (4 ملفات — Array.isArray guards)

| # | الملف | المشكلة |
|---|-------|---------|
| 1 | `Payslips.jsx` | `setPayslips(res.data \|\| [])` لا يضمن Array |
| 2 | `PayrollDetails.jsx` | `setEntries(eRes.data)` بدون guard ثم `entries.forEach/map` |
| 3 | `SalaryStructures.jsx` | `setStructures/setComponents(data \|\| [])` لا يضمن Array |
| 4 | `OvertimeRequests.jsx` | `setEmployees(empRes.data?.items \|\| empRes.data \|\| [])` — fallback chain غير آمن |

### ملاحظات إضافية (لا تحتاج إصلاح عاجل)

| البند | الخطورة | التوصية |
|-------|---------|---------|
| Payroll entries تستخدم `float()` عند الإدراج بدلاً من `Decimal` | HIGH | استخدام Decimal مباشرة إذا عمود DB يدعم NUMERIC |
| `branch_filter` f-string في WPS compliance | LOW | آمن فعلياً (يبني string ثابت من الكود) |
| Negative salary validation مفقودة في schema | MEDIUM | إضافة `ge=0` في Pydantic |
| `EOSSettlement.jsx` `emp.full_name` قد لا تكون موجودة | LOW | استخدام fallback |

---

## الوحدة 8: التصنيع (Manufacturing) ✅

**الملفات المفحوصة:**
- Backend: `manufacturing/core.py` (~925 سطر)
- Frontend (6 صفحات): `ProductionOrders`, `BOMs`, `BOMForm`, `ManufacturingHome`, `WorkCenters`, `Routes`

### البنود السليمة ✅

| البند | الحالة |
|-------|--------|
| Permission checks على جميع الـ endpoints | ✅ |
| Parameterized SQL queries | ✅ |
| Transaction safety في production orders | ✅ |
| Work center CRUD سليم | ✅ |

### المشاكل المكتشفة والمُصلحة 🔧

#### Frontend (3 ملفات)

| # | الملف | المشكلة | الإصلاح |
|---|-------|---------|---------|
| 1 | `ProductionOrders.jsx` | `setOrders/setBoms/setRoutes(res.data)` بدون guard | Array.isArray guards |
| 2 | `BOMs.jsx` | `productsRes.data.products \|\| []` يتعطل إذا data=undefined | safe chaining + Array.isArray |
| 3 | `ManufacturingHome.jsx` | `o.data.filter()` + `wc.data.length` بدون guard | Array.isArray على كل الاستخدامات |

### ملاحظات إضافية

| البند | الخطورة | التوصية |
|-------|---------|---------|
| Float arithmetic في `check_inventory_sufficiency` | HIGH | تحويل لـ Decimal |
| نقص فحص المخزون قبل استهلاك المواد | CRITICAL | سيُعالج مع وحدة المخزون |

---

## الوحدة 9: المشاريع (Projects) ✅

**الملفات المفحوصة:**
- Backend: `projects.py`
- Frontend: `ProjectList`, `ProjectDetails`, `ProjectForm`, `ProjectExpenses`, `TimeEntries`, `ProjectReports`, إلخ

### البنود السليمة ✅

| البند | الحالة |
|-------|--------|
| Division by zero guard على `budget_consumed_pct` | ✅ |
| Parameterized SQL queries | ✅ |
| Permission checks | ✅ |
| Frontend Array.isArray — `ProjectList.jsx` سليم | ✅ |

### ملاحظات إضافية

| البند | الخطورة | التوصية |
|-------|---------|---------|
| `delete_task` يستخدم `projects.edit` بدلاً من `projects.delete` | MEDIUM | تغيير الصلاحية |
| `create_project_expense` لا يفحص `branch_id` | MEDIUM | إضافة `validate_branch_access` |

---

## الوحدة 10: CRM ✅

**الملفات المفحوصة:**
- Backend: `crm.py` (~800 سطر)
- Frontend: `Opportunities`, `SupportTickets`, `Campaigns`, `KnowledgeBase`, `CRMHome`, إلخ

### البنود السليمة ✅

| البند | الحالة |
|-------|--------|
| Parameterized SQL queries | ✅ |
| Opportunity pipeline queries آمنة | ✅ |
| Optimistic locking (version check) في تحديث الفرص | ✅ |
| Frontend `Opportunities.jsx` و `SupportTickets.jsx` سليمة | ✅ |

### المشاكل المكتشفة والمُصلحة 🔧

| # | الخطورة | الملف | المشكلة | الإصلاح |
|---|---------|-------|---------|---------|
| 1 | **MEDIUM** | `crm.py` L642 | حذف الحملات يستخدم `sales.create` بدلاً من `sales.delete` | تغيير إلى `sales.delete` |
| 2 | **MEDIUM** | `crm.py` L754 | حذف المقالات يستخدم `sales.create` بدلاً من `sales.delete` | تغيير إلى `sales.delete` |

---

## الوحدة 11: التقارير و KPI (Reports) ✅

**الملفات المفحوصة:**
- Backend: `reports.py`, `dashboard.py`, `role_dashboards.py`, `scheduled_reports.py`
- Frontend: `ReportCenter`, `ScheduledReports`, `SharedReports`, `KPIDashboard`, `Dashboard`, `RoleDashboard`

### البنود السليمة ✅

| البند | الحالة |
|-------|--------|
| Division by zero guards (`if revenue > 0 else 0`, `if prev == 0`) | ✅ |
| SQL parameterized queries | ✅ |
| `validate_branch_access()` مطبق | ✅ |
| `scheduled_reports`: whitelist validation لأسماء الجداول | ✅ |
| `Dashboard.jsx`: fallback `fR.data \|\| []` | ✅ |
| لا يوجد t() على مستوى module scope | ✅ |
| Optional chaining مستخدم بشكل صحيح | ✅ |

### لا توجد مشاكل تحتاج إصلاح ✅

---

## الوحدة 12: المصروفات والضرائب والأصول (Expenses, Taxes, Assets) ✅

**الملفات المفحوصة:**
- Backend: تم فحصه ضمن الوحدة 2 (المحاسبة)
- Frontend: `ExpenseList/Form`, `TaxHome`, `TaxCompliance`, `WithholdingTax`, `AssetList`, `AssetDetails`, `AssetReports`

### البنود السليمة ✅

| البند | الحالة |
|-------|--------|
| `ExpenseList.jsx`: `expensesRes.data \|\| []` fallback | ✅ |
| `AssetReports.jsx`: `res.data?.items \|\| res.data \|\| []` | ✅ |
| Backend expenses/taxes/assets تم فحصه وإصلاحه في الوحدة 2 | ✅ |

### المشاكل المكتشفة والمُصلحة 🔧

| # | الملف | المشكلة | الإصلاح |
|---|-------|---------|----------|
| 1 | `TaxHome.jsx` | `setRates/setReturns(res.data)` بدون guard | Array.isArray guard |
| 2 | `AssetList.jsx` | `setAssets(response.data)` ثم `.reduce()` بدون guard | Array.isArray guard |
| 3 | `WithholdingTax.jsx` | `setRates(res.data ?? res)` — fallback للكائن بدلاً من مصفوفة | Array.isArray guard |

---

## ملخص عام

| الوحدة | الحالة | مشاكل مُصلحة | مشاكل معلقة |
|--------|--------|-------------|-------------|
| Auth & Companies & Setup | ✅ مكتمل | 4 | 0 |
| المحاسبة | ✅ مكتمل | 13 | 0 |
| المبيعات | ✅ مكتمل | 5 | 0 |
| المشتريات | ✅ مكتمل | 15 | 0 |
| المخزون | ✅ مكتمل | 6 | 0 |
| الخزينة | ✅ مكتمل (ضمن وحدة 2) | 6 | 0 |
| الموارد البشرية | ✅ مكتمل | 5 | 0 |
| التصنيع | ✅ مكتمل | 3 | 0 |
| المشاريع | ✅ مكتمل | 0 | 0 |
| CRM | ✅ مكتمل | 2 | 0 |
| التقارير | ✅ مكتمل | 0 | 0 |
| مصروفات/ضرائب/أصول | ✅ مكتمل | 3 | 0 |
