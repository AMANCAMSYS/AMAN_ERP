# AMAN ERP — خطة فحص النظام الشاملة (Module-by-Module Speckit Audit)

> **الهدف**: فحص كل وحدة (Module) في النظام فحصاً كاملاً — Backend + Frontend + Services + Models + Utils — دون ترك أي صفحة أو ملف.
>
> **المنهجية**: كل Speckit يغطي وحدة واحدة كاملة **+ جميع ترابطاتها مع الوحدات الأخرى**. لا يكتفي الفحص بملفات الوحدة فقط، بل يتتبع كل نقطة تماس مع وحدات أخرى ويفحص الكود المقابل فيها. يتم تشغيله بالترتيب التالي (الوحدات الأساسية أولاً، ثم المعتمدة عليها).
>
> **مبدأ الفحص المتقاطع**: عند فحص وحدة X، يتم أيضاً فحص كل كود في وحدات أخرى يتأثر بـ X أو يؤثر فيها. مثلاً: فحص المشتريات يشمل فحص كود استلام المخزون وقيود المحاسبة وسير عمل الموافقات المرتبطة.
>
> **ملاحظة حول الدستور**: speckit يقرأ `.specify/memory/constitution.md` تلقائياً في كل أمر — لا داعي لتكرار المبادئ هنا. نقاط الفحص الرئيسية هي الترجمة العملية للمبادئ بالنسبة لكل وحدة.
>
> **إجمالي**: 18 Speckit Audit — تغطي 305 صفحة Frontend + 70+ Router Backend + 16 Service + 21 Utility

---

## الترتيب المنطقي للفحص

| # | Speckit | الوحدة | أولوية |
|---|---------|--------|--------|
| 1 | `audit-auth-security` | المصادقة والأمان | 🔴 حرجة |
| 2 | `audit-core-admin` | الإدارة والنظام | 🔴 حرجة |
| 3 | `audit-accounting` | المحاسبة والقيود | 🔴 حرجة |
| 4 | `audit-treasury` | الخزينة والبنوك | 🔴 حرجة |
| 5 | `audit-taxes` | الضرائب والزكاة | 🔴 حرجة |
| 6 | `audit-inventory` | المخزون | 🟠 عالية |
| 7 | `audit-purchases` | المشتريات | 🟠 عالية |
| 8 | `audit-sales` | المبيعات | 🟠 عالية |
| 9 | `audit-pos` | نقاط البيع | 🟠 عالية |
| 10 | `audit-hr` | الموارد البشرية | 🟡 متوسطة |
| 11 | `audit-manufacturing` | التصنيع | 🟡 متوسطة |
| 12 | `audit-crm` | إدارة علاقات العملاء | 🟡 متوسطة |
| 13 | `audit-projects` | المشاريع والعقود | 🟡 متوسطة |
| 14 | `audit-assets` | الأصول الثابتة | 🟡 متوسطة |
| 15 | `audit-reports` | التقارير والتحليلات | 🟢 تكميلية |
| 16 | `audit-approvals` | الموافقات وسير العمل | 🟢 تكميلية |
| 17 | `audit-subscriptions-services` | الاشتراكات والخدمات | 🟢 تكميلية |
| 18 | `audit-cross-module` | فحص التكامل بين الوحدات | 🔴 حرجة |

---

## Speckit 1: `audit-auth-security` — المصادقة والأمان

**النطاق**: كل ما يتعلق بتسجيل الدخول، الأدوار، الصلاحيات، SSO، الأمان

### Backend
| نوع | ملف |
|-----|------|
| Router | `routers/auth.py` |
| Router | `routers/security.py` |
| Router | `routers/sso.py` |
| Router | `routers/roles.py` |
| Router | `routers/mobile.py` |
| Service | `services/sso_service.py` |
| Util | `utils/permissions.py` |
| Util | `utils/security_middleware.py` |
| Util | `utils/limiter.py` |
| Model | `models/domains/security_reporting.py` |
| Middleware | `middleware/*` |

### Frontend
| صفحة | ملف |
|-------|------|
| تسجيل الدخول | `pages/Login.jsx` |
| التسجيل | `pages/Register.jsx` |
| نسيت كلمة المرور | `pages/ForgotPassword.jsx` |
| إعادة تعيين كلمة المرور | `pages/ResetPassword.jsx` |
| الملف الشخصي | `pages/UserProfile.jsx` |
| إعداد SSO | `pages/SSO/SsoConfigList.jsx` |
| نموذج SSO | `pages/SSO/SsoConfigForm.jsx` |
| إدارة الأدوار | `pages/Admin/RoleManagement.jsx` |
| أحداث الأمان | `pages/Admin/SecurityEvents.jsx` |
| إعدادات الأمان | `pages/Settings/tabs/SecuritySettings.jsx` |

### ترابطات مع وحدات أخرى (Cross-Module Tracing)
| الوحدة المرتبطة | الملف المطلوب فحصه | نقطة التماس |
|----------------|-------------------|------------|
| كل الوحدات | `database.py` → `get_tenant_db()` | كل endpoint يستخدم tenant isolation |
| كل الوحدات | كل router → `Depends(get_current_user)` | التحقق من أن كل endpoint محمي |
| الموافقات | `routers/approvals.py` → permission checks | صلاحيات الموافقة مبنية على الأدوار |
| الإشعارات | `services/notification_service.py` | إشعارات تسجيل الدخول والتنبيهات الأمنية |

### نقاط الفحص الرئيسية
- [ ] JWT token lifecycle (creation, refresh, revocation)
- [ ] Role-based access control (RBAC) enforcement on every endpoint
- [ ] Tenant isolation in every query
- [ ] Rate limiting configuration
- [ ] SSO integration security
- [ ] Password hashing & validation
- [ ] Session management
- [ ] CORS configuration
- [ ] Input sanitization

---

## Speckit 2: `audit-core-admin` — الإدارة والنظام

**النطاق**: إدارة الشركات، الفروع، الإعدادات، الإشعارات، استيراد البيانات، الإعداد الأولي، سجلات المراجعة

### Backend
| نوع | ملف |
|-----|------|
| Router | `routers/companies.py` |
| Router | `routers/branches.py` |
| Router | `routers/settings.py` |
| Router | `routers/notifications.py` |
| Router | `routers/audit.py` |
| Router | `routers/data_import.py` |
| Router | `routers/system_completion.py` |
| Router | `routers/external.py` |
| Router | `routers/parties.py` |
| Router | `routers/dashboard.py` |
| Service | `services/notification_service.py` |
| Service | `services/email_service.py` |
| Service | `services/scheduler.py` |
| Util | `utils/audit.py` |
| Util | `utils/cache.py` |
| Util | `utils/email.py` |
| Util | `utils/exports.py` |
| Util | `utils/logging_config.py` |
| Util | `utils/webhooks.py` |
| Util | `utils/ws_manager.py` |
| Util | `utils/sql_builder.py` |
| Util | `utils/sql_safety.py` |
| Model | `models/domains/core.py` |
| Config | `config.py` |
| Config | `database.py` |

### Frontend
| صفحة | ملف |
|-------|------|
| لوحة التحكم | `pages/Dashboard.jsx` |
| قائمة الشركات | `pages/Admin/CompanyList.jsx` |
| سجلات المراجعة | `pages/Admin/AuditLogs.jsx` |
| النسخ الاحتياطي | `pages/Admin/BackupManagement.jsx` |
| استيراد البيانات | `pages/DataImport/DataImportPage.jsx` |
| معالج الإعداد | `pages/Setup/OnboardingWizard.jsx` |
| إعداد القطاع | `pages/Setup/IndustrySetup.jsx` |
| تخصيص الوحدات | `pages/Setup/ModuleCustomization.jsx` |
| غير موجود | `pages/NotFound.jsx` |
| **إعدادات (31 ملف)** | `pages/Settings/CompanySettings.jsx` |
| | `pages/Settings/CompanyProfile.jsx` |
| | `pages/Settings/Branches.jsx` |
| | `pages/Settings/CostingPolicy.jsx` |
| | `pages/Settings/PrintTemplates.jsx` |
| | `pages/Settings/Webhooks.jsx` |
| | `pages/Settings/ApiKeys.jsx` |
| | `pages/Settings/NotificationPreferences.jsx` |
| | `pages/Settings/tabs/GeneralSettings.jsx` |
| | `pages/Settings/tabs/FinancialSettings.jsx` |
| | `pages/Settings/tabs/AccountingMappingSettings.jsx` |
| | `pages/Settings/tabs/SalesSettings.jsx` |
| | `pages/Settings/tabs/PurchasesSettings.jsx` |
| | `pages/Settings/tabs/InventorySettings.jsx` |
| | `pages/Settings/tabs/InvoicingSettings.jsx` |
| | `pages/Settings/tabs/HRSettings.jsx` |
| | `pages/Settings/tabs/POSSettings.jsx` |
| | `pages/Settings/tabs/CRMSettings.jsx` |
| | `pages/Settings/tabs/ProjectsSettings.jsx` |
| | `pages/Settings/tabs/ExpensesSettings.jsx` |
| | `pages/Settings/tabs/ReportingSettings.jsx` |
| | `pages/Settings/tabs/NotificationSettings.jsx` |
| | `pages/Settings/tabs/WorkflowSettings.jsx` |
| | `pages/Settings/tabs/BrandingSettings.jsx` |
| | `pages/Settings/tabs/IntegrationSettings.jsx` |
| | `pages/Settings/tabs/AuditSettings.jsx` |
| | `pages/Settings/tabs/PerformanceSettings.jsx` |
| | `pages/Settings/tabs/ComplianceSettings.jsx` |
| | `pages/Settings/tabs/BranchesSettings.jsx` |
| | `pages/Settings/tabs/ComingSoon.jsx` |

### ترابطات مع وحدات أخرى (Cross-Module Tracing)
| الوحدة المرتبطة | الملف المطلوب فحصه | نقطة التماس |
|----------------|-------------------|------------|
| المحاسبة | `services/gl_service.py` | Dashboard يعرض أرصدة من GL |
| المحاسبة | `services/industry_coa_templates.py` | إعداد القطاع ينشئ دليل حسابات |
| المخزون | `routers/inventory/products.py` | استيراد البيانات يشمل المنتجات |
| الموارد البشرية | `routers/hr/core.py` | استيراد البيانات يشمل الموظفين |
| كل الوحدات | `utils/audit.py` | سجل المراجعة يسجل من كل الوحدات |

### نقاط الفحص الرئيسية
- [ ] Company/Branch CRUD with tenant isolation
- [ ] Settings persistence and validation
- [ ] Notification delivery (email, WebSocket, in-app)
- [ ] Data import validation and error handling
- [ ] Audit trail completeness
- [ ] Dashboard query performance
- [ ] Cache invalidation strategy
- [ ] Webhook security (HMAC signing)

---

## Speckit 3: `audit-accounting` — المحاسبة والقيود

**النطاق**: دليل الحسابات، القيود اليومية، التقارير المالية، الموازنات، العملات، القفل المالي، القيود المتكررة، مراكز التكلفة، المعاملات بين الشركات

### Backend
| نوع | ملف |
|-----|------|
| Router | `routers/finance/accounting.py` |
| Router | `routers/finance/budgets.py` |
| Router | `routers/finance/cost_centers.py` |
| Router | `routers/finance/currencies.py` |
| Router | `routers/finance/intercompany.py` |
| Router | `routers/finance/intercompany_v2.py` |
| Router | `routers/finance/advanced_workflow.py` |
| Router | `routers/finance/costing_policies.py` |
| Service | `services/gl_service.py` |
| Service | `services/intercompany_service.py` |
| Service | `services/industry_coa_templates.py` |
| Service | `services/industry_gl_rules.py` |
| Util | `utils/accounting.py` |
| Util | `utils/fiscal_lock.py` |
| Util | `utils/balance_reconciliation.py` |
| Util | `utils/optimistic_lock.py` |
| Model | `models/domains/finance.py` |
| Model | `models/core_accounting.py` |

### Frontend
| صفحة | ملف |
|-------|------|
| الرئيسية | `pages/Accounting/AccountingHome.jsx` |
| دليل الحسابات | `pages/Accounting/ChartOfAccounts.jsx` |
| الأستاذ العام | `pages/Accounting/GeneralLedger.jsx` |
| نموذج القيد | `pages/Accounting/JournalEntryForm.jsx` |
| قائمة القيود | `pages/Accounting/JournalEntryList.jsx` |
| ميزان المراجعة | `pages/Accounting/TrialBalance.jsx` |
| الميزانية العمومية | `pages/Accounting/BalanceSheet.jsx` |
| قائمة الدخل | `pages/Accounting/IncomeStatement.jsx` |
| التدفق النقدي | `pages/Accounting/CashFlowReport.jsx` |
| تقرير الضريبة | `pages/Accounting/VATReport.jsx` |
| حاسبة الزكاة | `pages/Accounting/ZakatCalculator.jsx` |
| الاعتراف بالإيراد | `pages/Accounting/RevenueRecognition.jsx` |
| الموازنات | `pages/Accounting/Budgets.jsx` |
| بنود الموازنة | `pages/Accounting/BudgetItems.jsx` |
| تقرير الموازنة | `pages/Accounting/BudgetReport.jsx` |
| الموازنة المتقدمة | `pages/Accounting/BudgetAdvanced.jsx` |
| السنوات المالية | `pages/Accounting/FiscalYears.jsx` |
| قفل الفترات | `pages/Accounting/FiscalPeriodLocks.jsx` |
| مقارنة الفترات | `pages/Accounting/PeriodComparison.jsx` |
| القيود المتكررة | `pages/Accounting/RecurringTemplates.jsx` |
| قيود الإقفال | `pages/Accounting/ClosingEntries.jsx` |
| العملات | `pages/Accounting/CurrencyList.jsx` |
| أرصدة افتتاحية | `pages/Accounting/OpeningBalances.jsx` |
| التدقيق الضريبي | `pages/Accounting/TaxAudit.jsx` |
| بين الشركات | `pages/Accounting/IntercompanyTransactions.jsx` |
| مراكز التكلفة | `pages/Accounting/CostCenters/CostCenterList.jsx` |
| بين الشركات (متقدم) | `pages/Intercompany/TransactionList.jsx` |
| | `pages/Intercompany/TransactionForm.jsx` |
| | `pages/Intercompany/AccountMappings.jsx` |
| | `pages/Intercompany/EntityGroupTree.jsx` |
| | `pages/Intercompany/ConsolidationView.jsx` |
| التكاليف | `pages/Costing/CostLayerList.jsx` |
| | `pages/Costing/CostingMethodForm.jsx` |
| | `pages/Costing/ValuationReport.jsx` |

### ترابطات مع وحدات أخرى (Cross-Module Tracing)
| الوحدة المرتبطة | الملف المطلوب فحصه | نقطة التماس |
|----------------|-------------------|------------|
| المبيعات | `routers/sales/invoices.py` → GL posting | فاتورة البيع تنتج قيد محاسبي |
| المشتريات | `routers/purchases.py` → GL posting | فاتورة الشراء تنتج قيد محاسبي |
| المخزون | `routers/inventory/costing.py` | حركة المخزون تنتج قيد تكلفة |
| الموارد البشرية | `routers/hr/core.py` → payroll GL | كشف المرتبات ينتج قيود رواتب |
| الأصول | `routers/finance/assets.py` → depreciation GL | الإهلاك الشهري ينتج قيد |
| الخزينة | `routers/finance/treasury.py` | التحويلات البنكية تنتج قيود |
| الضرائب | `routers/finance/taxes.py` | الضريبة المحصلة/المدفوعة تظهر في GL |
| نقطة البيع | `routers/pos.py` → GL posting | مبيعات POS تنتج قيود |
| التقارير | `routers/reports.py` | التقارير المالية تقرأ من GL |

### نقاط الفحص الرئيسية
- [ ] Double-entry enforcement (debit == credit) on every journal entry
- [ ] Decimal precision (Decimal, never float)
- [ ] Fiscal period locking enforcement
- [ ] Chart of Accounts hierarchy integrity
- [ ] Currency conversion using centralized rates
- [ ] Budget validation (over-budget alerts)
- [ ] Intercompany elimination entries
- [ ] Trial balance always balances
- [ ] GL posting from every sub-ledger
- [ ] Closing entries automation correctness
- [ ] Opening balance carryforward

---

## Speckit 4: `audit-treasury` — الخزينة والبنوك

**النطاق**: الحسابات البنكية، التسوية، التحويلات، الشيكات، السندات، التدفق النقدي

### Backend
| نوع | ملف |
|-----|------|
| Router | `routers/finance/treasury.py` |
| Router | `routers/finance/checks.py` |
| Router | `routers/finance/notes.py` |
| Router | `routers/finance/reconciliation.py` |
| Router | `routers/finance/cashflow.py` |

### Frontend
| صفحة | ملف |
|-------|------|
| الرئيسية | `pages/Treasury/TreasuryHome.jsx` |
| الحسابات البنكية | `pages/Treasury/TreasuryAccountList.jsx` |
| قائمة التسوية | `pages/Treasury/ReconciliationList.jsx` |
| نموذج التسوية | `pages/Treasury/ReconciliationForm.jsx` |
| نموذج التحويل | `pages/Treasury/TransferForm.jsx` |
| نموذج المصروف | `pages/Treasury/ExpenseForm.jsx` |
| استيراد بنكي | `pages/Treasury/BankImport.jsx` |
| شيكات مستحقة الدفع | `pages/Treasury/ChecksPayable.jsx` |
| شيكات مستحقة القبض | `pages/Treasury/ChecksReceivable.jsx` |
| تقادم الشيكات | `pages/Treasury/ChecksAgingReport.jsx` |
| سندات القبض | `pages/Treasury/NotesReceivable.jsx` |
| سندات الدفع | `pages/Treasury/NotesPayable.jsx` |
| تقرير التدفق النقدي | `pages/Treasury/TreasuryCashflowReport.jsx` |
| تقرير الأرصدة | `pages/Treasury/TreasuryBalancesReport.jsx` |
| توقعات التدفق | `pages/CashFlow/ForecastList.jsx` |
| | `pages/CashFlow/ForecastDetail.jsx` |
| | `pages/CashFlow/ForecastGenerate.jsx` |

### ترابطات مع وحدات أخرى (Cross-Module Tracing)
| الوحدة المرتبطة | الملف المطلوب فحصه | نقطة التماس |
|----------------|-------------------|------------|
| المحاسبة | `services/gl_service.py` → treasury GL entries | كل عملية خزينة تنتج قيد |
| المحاسبة | `routers/finance/accounting.py` → bank accounts in COA | الحسابات البنكية في دليل الحسابات |
| المشتريات | `routers/purchases.py` → supplier payments | دفع الموردين يمر عبر الخزينة |
| المبيعات | `routers/sales/invoices.py` → customer receipts | تحصيل العملاء يمر عبر الخزينة |
| الموارد البشرية | `routers/hr/core.py` → payroll disbursement | صرف الرواتب عبر البنك |

### نقاط الفحص الرئيسية
- [ ] Bank reconciliation matching algorithm
- [ ] Check lifecycle states (issued → cleared/bounced/cancelled)
- [ ] Notes receivable/payable maturity tracking
- [ ] Cash flow forecast accuracy
- [ ] Transfer between accounts creates proper GL entries
- [ ] Bank import parsing and duplicate detection

---

## Speckit 5: `audit-taxes` — الضرائب والزكاة

**النطاق**: الامتثال الضريبي، إقرارات الضريبة، ضريبة الاستقطاع، تقويم الضرائب، ZATCA

### Backend
| نوع | ملف |
|-----|------|
| Router | `routers/finance/taxes.py` |
| Router | `routers/finance/tax_compliance.py` |
| Util | `utils/zatca.py` |

### Frontend
| صفحة | ملف |
|-------|------|
| الرئيسية | `pages/Taxes/TaxHome.jsx` |
| الامتثال | `pages/Taxes/TaxCompliance.jsx` |
| تقويم الضرائب | `pages/Taxes/TaxCalendar.jsx` |
| نموذج الإقرار | `pages/Taxes/TaxReturnForm.jsx` |
| تفاصيل الإقرار | `pages/Taxes/TaxReturnDetails.jsx` |
| ضريبة الاستقطاع | `pages/Taxes/WithholdingTax.jsx` |

### ترابطات مع وحدات أخرى (Cross-Module Tracing)
| الوحدة المرتبطة | الملف المطلوب فحصه | نقطة التماس |
|----------------|-------------------|------------|
| المبيعات | `routers/sales/invoices.py` → VAT on sales | احتساب الضريبة على الفواتير |
| المشتريات | `routers/purchases.py` → VAT on purchases | الضريبة المدخلة على المشتريات |
| المحاسبة | `services/gl_service.py` → tax GL accounts | حسابات الضريبة في الأستاذ العام |
| المحاسبة | `routers/finance/accounting.py` → VAT report data | تقرير الضريبة يقرأ من GL |
| نقطة البيع | `routers/pos.py` → POS VAT | الضريبة على مبيعات POS |
| الموارد البشرية | `routers/hr/core.py` → withholding on payroll | استقطاع من الرواتب |

### نقاط الفحص الرئيسية
- [ ] VAT 15% calculation correctness
- [ ] ZATCA e-invoicing compliance
- [ ] Zakat calculation methodology
- [ ] Withholding tax deduction accuracy
- [ ] Tax return period validation
- [ ] Tax audit trail completeness

---

## Speckit 6: `audit-inventory` — المخزون

**النطاق**: المنتجات، المستودعات، حركات المخزون، التسويات، التحويلات، الشحنات، الدفعات، قوائم الأسعار، التقييم، التنبؤ

### Backend
| نوع | ملف |
|-----|------|
| Router | `routers/inventory/products.py` |
| Router | `routers/inventory/warehouses.py` |
| Router | `routers/inventory/stock_movements.py` |
| Router | `routers/inventory/adjustments.py` |
| Router | `routers/inventory/transfers.py` |
| Router | `routers/inventory/shipments.py` |
| Router | `routers/inventory/batches.py` |
| Router | `routers/inventory/categories.py` |
| Router | `routers/inventory/price_lists.py` |
| Router | `routers/inventory/costing.py` |
| Router | `routers/inventory/forecast.py` |
| Router | `routers/inventory/notifications.py` |
| Router | `routers/inventory/advanced.py` |
| Router | `routers/inventory/reports.py` |
| Router | `routers/inventory/suppliers.py` |
| Router | `routers/inventory/schemas.py` |
| Service | `services/costing_service.py` |
| Service | `services/forecast_service.py` |
| Service | `services/demand_forecast_service.py` |
| Util | `utils/quantity_validation.py` |
| Model | `models/domains/inventory.py` |

### Frontend
| صفحة | ملف |
|-------|------|
| الرئيسية | `pages/Stock/StockHome.jsx` |
| المنتجات | `pages/Stock/ProductList.jsx` |
| نموذج المنتج | `pages/Stock/ProductForm.jsx` |
| الفئات | `pages/Stock/CategoryList.jsx` |
| المستودعات | `pages/Stock/WarehouseList.jsx` |
| تفاصيل المستودع | `pages/Stock/WarehouseDetails.jsx` |
| حركات المخزون | `pages/Stock/StockMovements.jsx` |
| التسويات | `pages/Stock/StockAdjustments.jsx` |
| نموذج التسوية | `pages/Stock/StockAdjustmentForm.jsx` |
| نموذج التحويل | `pages/Stock/StockTransferForm.jsx` |
| نموذج الشحن | `pages/Stock/StockShipmentForm.jsx` |
| تقارير المخزون | `pages/Stock/StockReports.jsx` |
| الدفعات | `pages/Stock/BatchList.jsx` |
| الأرقام التسلسلية | `pages/Stock/SerialList.jsx` |
| قوائم الأسعار | `pages/Stock/PriceLists.jsx` |
| بنود الأسعار | `pages/Stock/PriceListItems.jsx` |
| قائمة الشحنات | `pages/Stock/ShipmentList.jsx` |
| تفاصيل الشحنة | `pages/Stock/ShipmentDetails.jsx` |
| الشحنات الواردة | `pages/Stock/IncomingShipments.jsx` |
| الجرد الدوري | `pages/Stock/CycleCounts.jsx` |
| تقييم المخزون | `pages/Stock/InventoryValuation.jsx` |
| فحص الجودة | `pages/Stock/QualityInspections.jsx` |
| التنبؤ | `pages/Forecast/ForecastList.jsx` |
| | `pages/Forecast/ForecastDetail.jsx` |
| | `pages/Forecast/ForecastGenerate.jsx` |

### ترابطات مع وحدات أخرى (Cross-Module Tracing)
| الوحدة المرتبطة | الملف المطلوب فحصه | نقطة التماس |
|----------------|-------------------|------------|
| المشتريات | `routers/purchases.py` → goods receipt | استلام أمر الشراء يزيد المخزون |
| المبيعات | `routers/sales/orders.py` → stock reservation | أمر البيع يحجز مخزون |
| المبيعات | `routers/delivery_orders.py` → stock deduction | أمر التسليم ينقص المخزون |
| المحاسبة | `services/gl_service.py` → inventory GL | تسوية المخزون تنتج قيد |
| التصنيع | `routers/manufacturing/core.py` → raw material consumption | أمر الإنتاج يستهلك مواد |
| التصنيع | `routers/manufacturing/core.py` → finished goods | إنتاج تام يزيد المخزون |
| نقطة البيع | `routers/pos.py` → POS stock deduction | بيع POS ينقص المخزون |
| المرتجعات | `routers/sales/returns.py` | مرتجع يعيد المخزون |

### نقاط الفحص الرئيسية
- [ ] Stock level never goes negative (unless configured)
- [ ] Costing method consistency (FIFO/LIFO/Weighted Average/Standard)
- [ ] Batch/serial tracking enforcement
- [ ] Warehouse transfer creates proper stock movements
- [ ] Adjustment posts correct GL entries
- [ ] Reorder point alerts
- [ ] Inventory valuation accuracy vs. GL balance
- [ ] Shipment status lifecycle

---

## Speckit 7: `audit-purchases` — المشتريات

**النطاق**: أوامر الشراء، المرتجعات، فواتير الشراء، الموردين، التكاليف المضافة، المطابقة، عروض الأسعار، الاتفاقيات الإطارية

### Backend
| نوع | ملف |
|-----|------|
| Router | `routers/purchases.py` |
| Router | `routers/landed_costs.py` |
| Router | `routers/matching.py` |
| Service | `services/matching_service.py` |
| Model | `models/domains/procurement.py` |

### Frontend
| صفحة | ملف |
|-------|------|
| الرئيسية | `pages/Buying/BuyingHome.jsx` |
| أوامر الشراء | `pages/Buying/BuyingOrders.jsx` |
| نموذج أمر الشراء | `pages/Buying/BuyingOrderForm.jsx` |
| تفاصيل أمر الشراء | `pages/Buying/BuyingOrderDetails.jsx` |
| المرتجعات | `pages/Buying/BuyingReturns.jsx` |
| نموذج المرتجع | `pages/Buying/BuyingReturnForm.jsx` |
| تفاصيل المرتجع | `pages/Buying/BuyingReturnDetails.jsx` |
| التقارير | `pages/Buying/BuyingReports.jsx` |
| الموردين | `pages/Buying/SupplierList.jsx` |
| نموذج المورد | `pages/Buying/SupplierForm.jsx` |
| تفاصيل المورد | `pages/Buying/SupplierDetails.jsx` |
| مجموعات الموردين | `pages/Buying/SupplierGroups.jsx` |
| كشف حساب المورد | `pages/Buying/SupplierStatement.jsx` |
| مدفوعات الموردين | `pages/Buying/SupplierPayments.jsx` |
| تقييم الموردين | `pages/Buying/SupplierRatings.jsx` |
| فواتير الشراء | `pages/Buying/PurchaseInvoiceList.jsx` |
| نموذج الفاتورة | `pages/Buying/PurchaseInvoiceForm.jsx` |
| تفاصيل الفاتورة | `pages/Buying/PurchaseInvoiceDetails.jsx` |
| تفاصيل أمر الشراء | `pages/Buying/PurchaseOrderDetails.jsx` |
| استلام أمر الشراء | `pages/Buying/PurchaseOrderReceive.jsx` |
| إشعارات دائنة | `pages/Buying/PurchaseCreditNotes.jsx` |
| إشعارات مدينة | `pages/Buying/PurchaseDebitNotes.jsx` |
| اتفاقيات الشراء | `pages/Buying/PurchaseAgreements.jsx` |
| تقادم المشتريات | `pages/Buying/PurchasesAgingReport.jsx` |
| التكاليف المضافة | `pages/Buying/LandedCosts.jsx` |
| تفاصيل التكلفة المضافة | `pages/Buying/LandedCostDetails.jsx` |
| طلب عرض أسعار | `pages/Buying/RFQList.jsx` |
| مدفوعات (Purchases) | `pages/Purchases/SupplierPayments.jsx` |
| نموذج الدفع | `pages/Purchases/PaymentForm.jsx` |
| تفاصيل الدفع | `pages/Purchases/PaymentDetails.jsx` |
| المطابقة | `pages/Matching/MatchList.jsx` |
| تفاصيل المطابقة | `pages/Matching/MatchDetail.jsx` |
| إعداد التفاوت | `pages/Matching/ToleranceConfig.jsx` |
| الاتفاقيات الإطارية | `pages/BlanketPO/BlanketPOList.jsx` |
| | `pages/BlanketPO/BlanketPOForm.jsx` |
| | `pages/BlanketPO/BlanketPODetail.jsx` |

### ترابطات مع وحدات أخرى (Cross-Module Tracing)
| الوحدة المرتبطة | الملف المطلوب فحصه | نقطة التماس |
|----------------|-------------------|------------|
| المخزون | `routers/inventory/stock_movements.py` → GRN | استلام البضاعة يزيد المخزون |
| المخزون | `routers/inventory/costing.py` | التكلفة المضافة تؤثر على تكلفة المخزون |
| المخزون | `services/costing_service.py` | طريقة التكلفة تؤثر على قيمة المشتريات |
| المحاسبة | `services/gl_service.py` → purchase GL | فاتورة الشراء → قيد محاسبي |
| المحاسبة | `utils/accounting.py` → AP posting | الذمم الدائنة |
| الخزينة | `routers/finance/treasury.py` → supplier payment | دفع المورد via الخزينة |
| الخزينة | `routers/finance/checks.py` → supplier checks | شيكات الموردين |
| الضرائب | `routers/finance/taxes.py` → input VAT | ضريبة المدخلات على المشتريات |
| الموافقات | `routers/approvals.py` → PO approval | اعتماد أمر الشراء |
| الموازنات | `routers/finance/budgets.py` → budget check | فحص تجاوز الموازنة |

### نقاط الفحص الرئيسية
- [ ] 3-way matching (PO → GRN → Invoice)
- [ ] Landed cost allocation accuracy
- [ ] Supplier aging report correctness
- [ ] Purchase return restores stock
- [ ] Credit/debit notes affect GL correctly
- [ ] Blanket PO release tracking
- [ ] RFQ → PO conversion flow
- [ ] Duplicate invoice prevention

---

## Speckit 8: `audit-sales` — المبيعات

**النطاق**: العملاء، عروض الأسعار، أوامر البيع، الفواتير، المرتجعات، أوامر التسليم، الإشعارات الدائنة/المدينة، العمولات، CPQ

### Backend
| نوع | ملف |
|-----|------|
| Router | `routers/sales/customers.py` |
| Router | `routers/sales/quotations.py` |
| Router | `routers/sales/orders.py` |
| Router | `routers/sales/invoices.py` |
| Router | `routers/sales/returns.py` |
| Router | `routers/sales/credit_notes.py` |
| Router | `routers/sales/vouchers.py` |
| Router | `routers/sales/cpq.py` |
| Router | `routers/sales/sales_improvements.py` |
| Router | `routers/sales/schemas.py` |
| Router | `routers/delivery_orders.py` |
| Service | `services/cpq_service.py` |
| Model | `models/domains/sales.py` |

### Frontend
| صفحة | ملف |
|-------|------|
| الرئيسية | `pages/Sales/SalesHome.jsx` |
| التقارير | `pages/Sales/SalesReports.jsx` |
| العملاء | `pages/Sales/CustomerList.jsx` |
| نموذج العميل | `pages/Sales/CustomerForm.jsx` |
| تفاصيل العميل | `pages/Sales/CustomerDetails.jsx` |
| مجموعات العملاء | `pages/Sales/CustomerGroups.jsx` |
| كشف حساب العميل | `pages/Sales/CustomerStatement.jsx` |
| إيصالات العملاء | `pages/Sales/CustomerReceipts.jsx` |
| عروض الأسعار | `pages/Sales/SalesQuotations.jsx` |
| نموذج عرض السعر | `pages/Sales/SalesQuotationForm.jsx` |
| تفاصيل عرض السعر | `pages/Sales/SalesQuotationDetails.jsx` |
| أوامر البيع | `pages/Sales/SalesOrders.jsx` |
| نموذج أمر البيع | `pages/Sales/SalesOrderForm.jsx` |
| تفاصيل أمر البيع | `pages/Sales/SalesOrderDetails.jsx` |
| الفواتير | `pages/Sales/InvoiceList.jsx` |
| نموذج الفاتورة | `pages/Sales/InvoiceForm.jsx` |
| تفاصيل الفاتورة | `pages/Sales/InvoiceDetails.jsx` |
| طباعة الفاتورة | `pages/Sales/InvoicePrintModal.jsx` |
| المرتجعات | `pages/Sales/SalesReturns.jsx` |
| نموذج المرتجع | `pages/Sales/SalesReturnForm.jsx` |
| تفاصيل المرتجع | `pages/Sales/SalesReturnDetails.jsx` |
| إشعارات دائنة | `pages/Sales/SalesCreditNotes.jsx` |
| إشعارات مدينة | `pages/Sales/SalesDebitNotes.jsx` |
| العمولات | `pages/Sales/SalesCommissions.jsx` |
| أوامر التسليم | `pages/Sales/DeliveryOrders.jsx` |
| نموذج التسليم | `pages/Sales/DeliveryOrderForm.jsx` |
| تفاصيل التسليم | `pages/Sales/DeliveryOrderDetails.jsx` |
| الإيصالات | `pages/Sales/ReceiptForm.jsx` |
| تفاصيل الإيصال | `pages/Sales/ReceiptDetails.jsx` |
| تقادم العملاء | `pages/Sales/AgingReport.jsx` |
| العقود | `pages/Sales/ContractList.jsx` |
| نموذج العقد | `pages/Sales/ContractForm.jsx` |
| تفاصيل العقد | `pages/Sales/ContractDetails.jsx` |
| تعديلات العقد | `pages/Sales/ContractAmendments.jsx` |
| CPQ | `pages/CPQ/QuoteList.jsx` |
| | `pages/CPQ/QuoteDetail.jsx` |
| | `pages/CPQ/ConfigurableProducts.jsx` |
| | `pages/CPQ/Configurator.jsx` |

### ترابطات مع وحدات أخرى (Cross-Module Tracing)
| الوحدة المرتبطة | الملف المطلوب فحصه | نقطة التماس |
|----------------|-------------------|------------|
| المخزون | `routers/inventory/stock_movements.py` | أمر التسليم ينقص المخزون، المرتجع يعيده |
| المخزون | `routers/inventory/shipments.py` | شحن البضاعة للعميل |
| المحاسبة | `services/gl_service.py` → sales GL | فاتورة البيع → قيد إيراد + ذمم مدينة |
| المحاسبة | `utils/accounting.py` → AR posting | الذمم المدينة |
| الخزينة | `routers/finance/treasury.py` → customer receipt | تحصيل العميل via الخزينة |
| الخزينة | `routers/finance/checks.py` → customer checks | شيكات العملاء |
| الضرائب | `routers/finance/taxes.py` → output VAT | ضريبة المخرجات على المبيعات |
| الضرائب | `utils/zatca.py` → e-invoicing | الفوترة الإلكترونية ZATCA |
| الموافقات | `routers/approvals.py` | اعتماد عروض الأسعار والفواتير |
| CRM | `routers/crm.py` → lead to customer | تحويل العميل المحتمل إلى عميل |

### نقاط الفحص الرئيسية
- [ ] Quote → Order → Invoice → Delivery flow integrity
- [ ] Return restores stock and reverses GL
- [ ] Credit/debit note GL impact
- [ ] Customer aging accuracy
- [ ] Commission calculation correctness
- [ ] Revenue recognition timing
- [ ] Delivery order stock reservation
- [ ] CPQ pricing engine accuracy
- [ ] Invoice printing / ZATCA compliance

---

## Speckit 9: `audit-pos` — نقاط البيع

**النطاق**: واجهة نقطة البيع، الطلبات المعلقة، المرتجعات، إدارة الطاولات، المطبخ، الولاء، العروض، الوضع غير المتصل

### Backend
| نوع | ملف |
|-----|------|
| Router | `routers/pos.py` |
| Model | `models/domains/operations.py` (POS section) |

### Frontend
| صفحة | ملف |
|-------|------|
| الرئيسية | `pages/POS/POSHome.jsx` |
| واجهة البيع | `pages/POS/POSInterface.jsx` |
| الوضع غير المتصل | `pages/POS/POSOfflineManager.jsx` |
| إدارة الطاولات | `pages/POS/TableManagement.jsx` |
| شاشة المطبخ | `pages/POS/KitchenDisplay.jsx` |
| شاشة العميل | `pages/POS/CustomerDisplay.jsx` |
| إعدادات الطابعة | `pages/POS/ThermalPrintSettings.jsx` |
| برامج الولاء | `pages/POS/LoyaltyPrograms.jsx` |
| العروض | `pages/POS/Promotions.jsx` |
| المرتجعات | `pages/POS/components/POSReturns.jsx` |
| الطلبات المعلقة | `pages/POS/components/HeldOrders.jsx` |

### ترابطات مع وحدات أخرى (Cross-Module Tracing)
| الوحدة المرتبطة | الملف المطلوب فحصه | نقطة التماس |
|----------------|-------------------|------------|
| المخزون | `routers/inventory/stock_movements.py` | بيع POS ينقص المخزون فوراً |
| المبيعات | `routers/sales/invoices.py` | بيع POS ينشئ فاتورة مبيعات |
| المحاسبة | `services/gl_service.py` → POS GL | بيع POS → قيد نقدي/إيراد |
| الخزينة | `routers/finance/treasury.py` | إغلاق الجلسة → تسوية النقدية |
| الضرائب | `routers/finance/taxes.py` | الضريبة على مبيعات POS |
| العملاء | `routers/sales/customers.py` | ربط عميل POS ببيانات العملاء |

### نقاط الفحص الرئيسية
- [ ] Offline mode data sync and conflict resolution
- [ ] POS session open/close with cash reconciliation
- [ ] Receipt printing accuracy
- [ ] Loyalty points calculation
- [ ] Promotion discount stacking rules
- [ ] POS return creates proper GL reversal
- [ ] Kitchen display real-time updates
- [ ] Held order recovery

---

## Speckit 10: `audit-hr` — الموارد البشرية

**النطاق**: الموظفين، الأقسام، الحضور، الإجازات، المرتبات، القروض، نهاية الخدمة، التأمينات، WPS، السعودة، التدريب، الأداء، الخدمة الذاتية

### Backend
| نوع | ملف |
|-----|------|
| Router | `routers/hr/core.py` |
| Router | `routers/hr/advanced.py` |
| Router | `routers/hr/performance.py` |
| Router | `routers/hr/self_service.py` |
| Router | `routers/hr_wps_compliance.py` |
| Util | `utils/hr_helpers.py` |
| Model | `models/domains/hr.py` |

### Frontend
| صفحة | ملف |
|-------|------|
| الرئيسية | `pages/HR/HRHome.jsx` |
| الموظفين | `pages/HR/Employees.jsx` |
| وثائق الموظف | `pages/HR/EmployeeDocuments.jsx` |
| الأقسام | `pages/HR/DepartmentList.jsx` |
| المناصب | `pages/HR/PositionList.jsx` |
| الحضور | `pages/HR/Attendance.jsx` |
| الإجازات | `pages/HR/LeaveList.jsx` |
| ترحيل الإجازات | `pages/HR/LeaveCarryover.jsx` |
| كشف المرتبات | `pages/HR/PayrollList.jsx` |
| تفاصيل المرتب | `pages/HR/PayrollDetails.jsx` |
| قسائم الراتب | `pages/HR/Payslips.jsx` |
| هياكل الرواتب | `pages/HR/SalaryStructures.jsx` |
| القروض | `pages/HR/LoanList.jsx` |
| الإضافي | `pages/HR/OvertimeRequests.jsx` |
| المخالفات | `pages/HR/Violations.jsx` |
| نهاية الخدمة | `pages/HR/EOSSettlement.jsx` |
| التأمينات | `pages/HR/GOSISettings.jsx` |
| تصدير WPS | `pages/HR/WPSExport.jsx` |
| لوحة السعودة | `pages/HR/SaudizationDashboard.jsx` |
| التدريب | `pages/HR/TrainingPrograms.jsx` |
| تقييم الأداء | `pages/HR/PerformanceReviews.jsx` |
| العهد | `pages/HR/CustodyManagement.jsx` |
| التوظيف | `pages/HR/Recruitment.jsx` |
| تقارير الموارد البشرية | `pages/HR/Reports/HRReports.jsx` |
| تقرير الإجازات | `pages/HR/Reports/LeaveReport.jsx` |
| تقرير المرتبات | `pages/HR/Reports/PayrollReport.jsx` |
| الأداء - الدورات | `pages/Performance/CycleList.jsx` |
| | `pages/Performance/CycleForm.jsx` |
| | `pages/Performance/TeamReviews.jsx` |
| | `pages/Performance/ManagerReview.jsx` |
| | `pages/Performance/MyReviews.jsx` |
| | `pages/Performance/SelfAssessment.jsx` |
| | `pages/Performance/ReviewResult.jsx` |
| الخدمة الذاتية | `pages/SelfService/EmployeeDashboard.jsx` |
| | `pages/SelfService/PayslipList.jsx` |
| | `pages/SelfService/PayslipDetail.jsx` |
| | `pages/SelfService/ProfileEdit.jsx` |
| | `pages/SelfService/LeaveRequestForm.jsx` |
| | `pages/SelfService/TeamRequests.jsx` |
| تتبع الوقت | `pages/TimeTracking/TimesheetWeek.jsx` |
| | `pages/TimeTracking/TeamTimesheets.jsx` |
| | `pages/TimeTracking/ProjectProfitability.jsx` |

### ترابطات مع وحدات أخرى (Cross-Module Tracing)
| الوحدة المرتبطة | الملف المطلوب فحصه | نقطة التماس |
|----------------|-------------------|------------|
| المحاسبة | `services/gl_service.py` → payroll GL | كشف المرتبات ينتج قيود رواتب |
| الخزينة | `routers/finance/treasury.py` → salary disbursement | صرف الرواتب عبر البنك |
| الضرائب | `routers/finance/taxes.py` → GOSI/withholding | استقطاعات التأمينات والضرائب |
| الموافقات | `routers/approvals.py` → leave/overtime approval | اعتماد الإجازات والإضافي |
| المشاريع | `routers/projects.py` → timesheet integration | الجداول الزمنية → تكلفة المشروع |
| الإشعارات | `services/notification_service.py` | إشعار الموظف بالإجازة/الراتب |

### نقاط الفحص الرئيسية
- [ ] Payroll calculation accuracy (basic + allowances - deductions)
- [ ] GOSI contribution calculation
- [ ] WPS file format compliance
- [ ] End-of-service calculation per Saudi labor law
- [ ] Leave balance accuracy
- [ ] Attendance integration
- [ ] Saudization ratio calculation
- [ ] Loan installment deduction from payroll
- [ ] Overtime calculation rules
- [ ] Self-service permission boundaries

---

## Speckit 11: `audit-manufacturing` — التصنيع

**النطاق**: أوامر الإنتاج، قائمة المواد، التوجيه، مراكز العمل، بطاقات العمل، تخطيط الطاقة، MRP، الصيانة، تكلفة التصنيع

### Backend
| نوع | ملف |
|-----|------|
| Router | `routers/manufacturing/core.py` |
| Router | `routers/manufacturing/routing.py` |
| Router | `routers/manufacturing/shopfloor.py` |
| Model | `models/domains/manufacturing.py` |

### Frontend
| صفحة | ملف |
|-------|------|
| الرئيسية | `pages/Manufacturing/ManufacturingHome.jsx` |
| أوامر الإنتاج | `pages/Manufacturing/ProductionOrders.jsx` |
| تفاصيل أمر الإنتاج | `pages/Manufacturing/ProductionOrderDetails.jsx` |
| جدول الإنتاج | `pages/Manufacturing/ProductionSchedule.jsx` |
| تحليلات الإنتاج | `pages/Manufacturing/ProductionAnalytics.jsx` |
| قائمة المواد | `pages/Manufacturing/BOMs.jsx` |
| التوجيه | `pages/Manufacturing/Routings.jsx` |
| مراكز العمل | `pages/Manufacturing/WorkCenters.jsx` |
| بطاقات العمل | `pages/Manufacturing/JobCards.jsx` |
| تخطيط الطاقة | `pages/Manufacturing/CapacityPlanning.jsx` |
| صيانة المعدات | `pages/Manufacturing/EquipmentMaintenance.jsx` |
| تخطيط MRP | `pages/Manufacturing/MRPPlanning.jsx` |
| عرض MRP | `pages/Manufacturing/MRPView.jsx` |
| تكلفة التصنيع | `pages/Manufacturing/ManufacturingCosting.jsx` |
| تقرير العمالة | `pages/Manufacturing/DirectLaborReport.jsx` |
| تقرير حالة الأوامر | `pages/Manufacturing/WorkOrderStatusReport.jsx` |
| التوجيه (مستقل) | `pages/Routing/RoutingList.jsx` |
| | `pages/Routing/RoutingForm.jsx` |
| أرضية المصنع | `pages/ShopFloor/ShopFloorDashboard.jsx` |
| | `pages/ShopFloor/OperationEntry.jsx` |
| تخطيط الموارد | `pages/ResourcePlanning/ProjectResources.jsx` |
| | `pages/ResourcePlanning/AllocationForm.jsx` |
| | `pages/ResourcePlanning/AvailabilityCalendar.jsx` |

### ترابطات مع وحدات أخرى (Cross-Module Tracing)
| الوحدة المرتبطة | الملف المطلوب فحصه | نقطة التماس |
|----------------|-------------------|------------|
| المخزون | `routers/inventory/stock_movements.py` | استهلاك مواد أولية + إضافة منتجات تامة |
| المخزون | `routers/inventory/products.py` | BOM يربط بمنتجات المخزون |
| المحاسبة | `services/gl_service.py` → WIP GL | الإنتاج تحت التشغيل → قيد |
| المحاسبة | `services/costing_service.py` | تكلفة التصنيع والانحرافات |
| المشتريات | `routers/purchases.py` | MRP ينتج طلبات شراء |
| الموارد البشرية | `routers/hr/core.py` → labor cost | تكلفة العمالة المباشرة |

### نقاط الفحص الرئيسية
- [ ] BOM explosion accuracy
- [ ] Production order consumes raw materials correctly
- [ ] Finished goods added to inventory on completion
- [ ] WIP accounting entries
- [ ] MRP demand calculation
- [ ] Routing time calculations
- [ ] Shop floor data capture
- [ ] Manufacturing cost variance analysis

---

## Speckit 12: `audit-crm` — إدارة علاقات العملاء

**النطاق**: جهات الاتصال، الفرص، تقييم العملاء المحتملين، شرائح العملاء، الحملات، تحليلات المبيعات، تذاكر الدعم

### Backend
| نوع | ملف |
|-----|------|
| Router | `routers/crm.py` |
| Model | `models/domains/projects_crm.py` (CRM section) |

### Frontend
| صفحة | ملف |
|-------|------|
| الرئيسية | `pages/CRM/CRMHome.jsx` |
| لوحة التحكم | `pages/CRM/CRMDashboard.jsx` |
| جهات الاتصال | `pages/CRM/CRMContacts.jsx` |
| الفرص | `pages/CRM/Opportunities.jsx` |
| تقييم العملاء | `pages/CRM/LeadScoring.jsx` |
| شرائح العملاء | `pages/CRM/CustomerSegments.jsx` |
| الحملات التسويقية | `pages/CRM/MarketingCampaigns.jsx` |
| تحليلات المبيعات | `pages/CRM/PipelineAnalytics.jsx` |
| توقعات المبيعات | `pages/CRM/SalesForecasts.jsx` |
| تذاكر الدعم | `pages/CRM/SupportTickets.jsx` |
| قاعدة المعرفة | `pages/CRM/KnowledgeBase.jsx` |
| الحملات (مستقل) | `pages/Campaign/CampaignList.jsx` |
| | `pages/Campaign/CampaignForm.jsx` |
| | `pages/Campaign/CampaignReport.jsx` |

### ترابطات مع وحدات أخرى (Cross-Module Tracing)
| الوحدة المرتبطة | الملف المطلوب فحصه | نقطة التماس |
|----------------|-------------------|------------|
| المبيعات | `routers/sales/customers.py` | تحويل Lead إلى Customer |
| المبيعات | `routers/sales/quotations.py` | الفرصة تنتج عرض سعر |
| الإشعارات | `services/notification_service.py` | إشعارات الحملات والتذاكر |
| التقارير | `routers/reports.py` | تقارير المبيعات تستخدم بيانات CRM |

### نقاط الفحص الرئيسية
- [ ] Lead → Opportunity → Customer conversion flow
- [ ] Lead scoring algorithm
- [ ] Pipeline stage transitions
- [ ] Campaign ROI calculation
- [ ] Support ticket SLA tracking
- [ ] Customer segmentation criteria

---

## Speckit 13: `audit-projects` — المشاريع والعقود

**النطاق**: المشاريع، المهام، الجداول الزمنية، الموارد، المخاطر، الماليات، العقود

### Backend
| نوع | ملف |
|-----|------|
| Router | `routers/projects.py` |
| Router | `routers/contracts.py` |
| Model | `models/domains/projects_crm.py` (Projects section) |

### Frontend
| صفحة | ملف |
|-------|------|
| قائمة المشاريع | `pages/Projects/ProjectList.jsx` |
| نموذج المشروع | `pages/Projects/ProjectForm.jsx` |
| تفاصيل المشروع | `pages/Projects/ProjectDetails.jsx` |
| المخاطر | `pages/Projects/ProjectRisks.jsx` |
| الجداول الزمنية | `pages/Projects/Timesheets.jsx` |
| مخطط جانت | `pages/Projects/GanttChart.jsx` |
| إدارة الموارد | `pages/Projects/ResourceManagement.jsx` |
| استغلال الموارد | `pages/Projects/ResourceUtilizationReport.jsx` |
| الماليات | `pages/Projects/ProjectFinancialsReport.jsx` |

### ترابطات مع وحدات أخرى (Cross-Module Tracing)
| الوحدة المرتبطة | الملف المطلوب فحصه | نقطة التماس |
|----------------|-------------------|------------|
| المحاسبة | `services/gl_service.py` → project GL | تكلفة المشروع → قيود محاسبية |
| الموارد البشرية | `routers/hr/core.py` → timesheets | جداول العمل → تكلفة العمالة |
| الموارد البشرية | `routers/hr/core.py` → employee allocation | تخصيص الموظفين للمشاريع |
| المبيعات | `routers/sales/invoices.py` | فوترة مراحل العقد |
| الموازنات | `routers/finance/budgets.py` | موازنة المشروع |
| الموافقات | `routers/approvals.py` | اعتماد مصروفات المشروع |

### نقاط الفحص الرئيسية
- [ ] Project budget vs. actual tracking
- [ ] Timesheet → payroll integration
- [ ] Resource allocation conflicts
- [ ] Contract billing milestones
- [ ] Project profitability calculation
- [ ] Gantt chart data consistency

---

## Speckit 14: `audit-assets` — الأصول الثابتة

**النطاق**: الأصول، الإهلاك، اختبار التدني، عقود الإيجار

### Backend
| نوع | ملف |
|-----|------|
| Router | `routers/finance/assets.py` |
| Model | `models/domains/finance.py` (Assets section) |

### Frontend
| صفحة | ملف |
|-------|------|
| قائمة الأصول | `pages/Assets/AssetList.jsx` |
| نموذج الأصل | `pages/Assets/AssetForm.jsx` |
| تفاصيل الأصل | `pages/Assets/AssetDetails.jsx` |
| إدارة الأصول | `pages/Assets/AssetManagement.jsx` |
| تقارير الأصول | `pages/Assets/AssetReports.jsx` |
| اختبار التدني | `pages/Assets/ImpairmentTest.jsx` |
| عقود الإيجار | `pages/Assets/LeaseContracts.jsx` |

### ترابطات مع وحدات أخرى (Cross-Module Tracing)
| الوحدة المرتبطة | الملف المطلوب فحصه | نقطة التماس |
|----------------|-------------------|------------|
| المحاسبة | `services/gl_service.py` → depreciation GL | الإهلاك الشهري → قيد محاسبي |
| المحاسبة | `routers/finance/accounting.py` | استبعاد الأصل → قيد ربح/خسارة |
| المشتريات | `routers/purchases.py` | شراء أصل من فاتورة مشتريات |
| المخزون | `routers/inventory/products.py` | الأصل كمنتج غير مخزني |
| الضرائب | `routers/finance/taxes.py` | الضريبة على شراء/بيع الأصل |

### نقاط الفحص الرئيسية
- [ ] Depreciation calculation (straight-line, declining balance)
- [ ] Monthly depreciation GL posting
- [ ] Asset disposal accounting
- [ ] Impairment test methodology
- [ ] IFRS 16 lease accounting
- [ ] Asset category → GL account mapping

---

## Speckit 15: `audit-reports` — التقارير والتحليلات

**النطاق**: مركز التقارير، التقارير المجدولة، مؤشرات الأداء، لوحات التحكم المخصصة، الأرباح والخسائر التفصيلية، التجميع

### Backend
| نوع | ملف |
|-----|------|
| Router | `routers/reports.py` |
| Router | `routers/scheduled_reports.py` |
| Router | `routers/role_dashboards.py` |
| Service | `services/kpi_service.py` |
| Service | `services/industry_kpi_service.py` |

### Frontend
| صفحة | ملف |
|-------|------|
| مركز التقارير | `pages/Reports/ReportCenter.jsx` |
| منشئ التقارير | `pages/Reports/ReportBuilder.jsx` |
| أرباح وخسائر تفصيلية | `pages/Reports/DetailedProfitLoss.jsx` |
| التدفق النقدي IAS7 | `pages/Reports/CashFlowIAS7.jsx` |
| أرباح/خسائر العملة | `pages/Reports/FXGainLossReport.jsx` |
| تقارير التجميع | `pages/Reports/ConsolidationReports.jsx` |
| تقرير القطاع | `pages/Reports/IndustryReport.jsx` |
| لوحة المؤشرات | `pages/Reports/KPIDashboard.jsx` |
| التقارير المشتركة | `pages/Reports/SharedReports.jsx` |
| التقارير المجدولة | `pages/Reports/ScheduledReports.jsx` |
| لوحة المؤشرات | `pages/KPI/KPIHub.jsx` |
| لوحة الأدوار | `pages/KPI/RoleDashboard.jsx` |
| التحليلات | `pages/Analytics/DashboardList.jsx` |
| عرض اللوحة | `pages/Analytics/DashboardView.jsx` |
| محرر اللوحة | `pages/Analytics/DashboardEditor.jsx` |

### ترابطات مع وحدات أخرى (Cross-Module Tracing)
| الوحدة المرتبطة | الملف المطلوب فحصه | نقطة التماس |
|----------------|-------------------|------------|
| المحاسبة | `services/gl_service.py` | كل التقارير المالية تقرأ من GL |
| المحاسبة | `routers/finance/accounting.py` | ميزان المراجعة، الميزانية، الدخل |
| الخزينة | `routers/finance/treasury.py` | تقرير التدفق النقدي |
| المبيعات | `routers/sales/invoices.py` | تقارير المبيعات |
| المشتريات | `routers/purchases.py` | تقارير المشتريات |
| المخزون | `routers/inventory/reports.py` | تقارير المخزون |
| الموارد البشرية | `routers/hr/core.py` | تقارير المرتبات |
| الضرائب | `routers/finance/taxes.py` | تقارير الضريبة |
| بين الشركات | `services/intercompany_service.py` | تقارير التجميع |

### نقاط الفحص الرئيسية
- [ ] Report data matches GL balances
- [ ] Scheduled reports delivery
- [ ] KPI calculation accuracy
- [ ] Dashboard query performance
- [ ] Consolidation elimination entries
- [ ] IAS 7 cash flow statement compliance
- [ ] Report export formats (PDF, Excel)

---

## Speckit 16: `audit-approvals` — الموافقات وسير العمل

**النطاق**: سير عمل الموافقات، محرر سير العمل

### Backend
| نوع | ملف |
|-----|------|
| Router | `routers/approvals.py` |
| Util | `utils/approval_utils.py` |
| Util | `utils/duplicate_detection.py` |

### Frontend
| صفحة | ملف |
|-------|------|
| صفحة الموافقات | `pages/Approvals/ApprovalsPage.jsx` |
| محرر سير العمل | `pages/Approvals/WorkflowEditor.jsx` |

### ترابطات مع وحدات أخرى (Cross-Module Tracing)
| الوحدة المرتبطة | الملف المطلوب فحصه | نقطة التماس |
|----------------|-------------------|------------|
| المشتريات | `routers/purchases.py` → PO approval | اعتماد أوامر الشراء |
| المبيعات | `routers/sales/quotations.py` → quote approval | اعتماد عروض الأسعار |
| الموارد البشرية | `routers/hr/core.py` → leave approval | اعتماد الإجازات |
| المصروفات | `routers/finance/expenses.py` | اعتماد المصروفات |
| الخزينة | `routers/finance/treasury.py` → payment approval | اعتماد المدفوعات |
| الموازنات | `routers/finance/budgets.py` | تجاوز الموازنة يطلب موافقة |

### نقاط الفحص الرئيسية
- [ ] Multi-level approval chain
- [ ] Delegation and escalation
- [ ] Approval timeout handling
- [ ] Approval affects document status correctly
- [ ] Audit trail for approvals
- [ ] Duplicate submission prevention

---

## Speckit 17: `audit-subscriptions-services` — الاشتراكات والخدمات والمصروفات

**النطاق**: الاشتراكات، الخدمات، المصروفات

### Backend
| نوع | ملف |
|-----|------|
| Router | `routers/finance/subscriptions.py` |
| Router | `routers/finance/expenses.py` |
| Router | `routers/services.py` |
| Service | `services/subscription_service.py` |

### Frontend
| صفحة | ملف |
|-------|------|
| الاشتراكات | `pages/Subscription/SubscriptionHome.jsx` |
| قائمة الخطط | `pages/Subscription/PlanList.jsx` |
| نموذج الخطة | `pages/Subscription/PlanForm.jsx` |
| التسجيلات | `pages/Subscription/EnrollmentList.jsx` |
| نموذج التسجيل | `pages/Subscription/EnrollmentForm.jsx` |
| تفاصيل التسجيل | `pages/Subscription/EnrollmentDetail.jsx` |
| الخدمات | `pages/Services/ServicesHome.jsx` |
| طلبات الخدمة | `pages/Services/ServiceRequests.jsx` |
| إدارة المستندات | `pages/Services/DocumentManagement.jsx` |
| المصروفات | `pages/Expenses/ExpenseList.jsx` |
| نموذج المصروف | `pages/Expenses/ExpenseForm.jsx` |
| تفاصيل المصروف | `pages/Expenses/ExpenseDetails.jsx` |
| سياسات المصروفات | `pages/Expenses/ExpensePolicies.jsx` |

### ترابطات مع وحدات أخرى (Cross-Module Tracing)
| الوحدة المرتبطة | الملف المطلوب فحصه | نقطة التماس |
|----------------|-------------------|------------|
| المحاسبة | `services/gl_service.py` → expense/subscription GL | المصروف → قيد محاسبي |
| المحاسبة | `routers/finance/accounting.py` | الاشتراك → إيراد مؤجل |
| الموافقات | `routers/approvals.py` | اعتماد المصروفات |
| المبيعات | `routers/sales/invoices.py` | فاتورة الاشتراك المتكررة |
| الإشعارات | `services/notification_service.py` | تذكير تجديد الاشتراك |

### نقاط الفحص الرئيسية
- [ ] Subscription billing cycle accuracy
- [ ] Expense approval and GL posting
- [ ] Expense policy enforcement
- [ ] Service request lifecycle
- [ ] Document management security
- [ ] Recurring subscription invoicing

---

## Speckit 18: `audit-cross-module` — فحص التكامل بين الوحدات

**النطاق**: هذا الفحص لا يغطي وحدة بعينها — بل يتحقق من التكامل والاتساق بين جميع الوحدات

### الملفات المحورية
| نوع | ملف |
|-----|------|
| Service | `services/gl_service.py` — GL posting from ALL modules |
| Service | `services/matching_service.py` — 3-way matching |
| Service | `services/intercompany_service.py` — cross-entity |
| Util | `utils/balance_reconciliation.py` |
| Util | `utils/accounting.py` |
| Model | `models/base.py` |
| Model | `models/__init__.py` |
| Model | `models/business_core.py` |
| Model | `models/core_accounting.py` |

### نقاط الفحص الرئيسية
- [ ] **Sales Invoice → GL**: كل فاتورة بيع تنتج قيد محاسبي صحيح
- [ ] **Purchase Invoice → GL**: كل فاتورة شراء تنتج قيد محاسبي صحيح
- [ ] **Inventory → GL**: كل حركة مخزون تنتج قيد تكلفة
- [ ] **Payroll → GL**: كشف المرتبات ينتج قيود رواتب
- [ ] **Asset Depreciation → GL**: الإهلاك الشهري ينتج قيد
- [ ] **POS → Sales + Inventory**: نقطة البيع تؤثر على المبيعات والمخزون
- [ ] **Manufacturing → Inventory**: أمر الإنتاج يستهلك مواد أولية وينتج منتجات تامة
- [ ] **Tax → GL**: الضريبة المحصلة/المدفوعة تظهر في الميزانية
- [ ] **Intercompany → Elimination**: المعاملات بين الشركات تُلغى في التجميع
- [ ] **Budget → Approval**: تجاوز الموازنة يمنع الاعتماد (إن مفعّل)
- [ ] **Trial Balance = 0**: ميزان المراجعة يجب أن يتوازن دائماً
- [ ] **Subledger → GL Reconciliation**: أرصدة الدفاتر الفرعية = أرصدة الأستاذ العام

---

## ملاحظات التنفيذ

### كيفية تشغيل كل Speckit
```
speckit.specify → speckit.plan → speckit.tasks → speckit.implement
```

لكل وحدة يتم:
1. **specify**: وصف الوحدة ونطاقها وكل ملفاتها (من هذه الخطة)
2. **plan**: تحديد نقاط الفحص والمعايير والأدوات
3. **tasks**: تحويل نقاط الفحص إلى مهام قابلة للتنفيذ
4. **implement**: تنفيذ الفحص وتسجيل النتائج

### ترتيب التبعيات
```
auth-security (1)
    ↓
core-admin (2)
    ↓
accounting (3) → treasury (4) → taxes (5)
    ↓
inventory (6)
    ↓
purchases (7) ←→ sales (8) → pos (9)
    ↓
hr (10) → manufacturing (11) → crm (12) → projects (13)
    ↓
assets (14) → reports (15) → approvals (16) → subscriptions (17)
    ↓
cross-module (18) — MUST BE LAST
```

### إحصائيات الخطة
| المقياس | العدد |
|---------|-------|
| إجمالي Speckit | 18 |
| إجمالي ملفات Backend (Routers) | 70+ |
| إجمالي ملفات Frontend (Pages) | 305 |
| إجمالي Services | 16 |
| إجمالي Utils | 21 |
| إجمالي Domain Models | 9 |
| نقاط الفحص الرئيسية | 120+ |
