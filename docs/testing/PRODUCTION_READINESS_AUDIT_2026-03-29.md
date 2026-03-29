# تقرير جاهزية الإنتاج - AMAN ERP v7.0

**التاريخ:** 29 مارس 2026  
**نوع التقرير:** Production Readiness Audit  
**التقييم الحالي:** 82%

---

## 1) Executive Summary

- **قرار الجاهزية الحالي:** **لا أنصح بالإطلاق الآن**
- **نسبة الجاهزية الواقعية:** **82%**
- **السبب التنفيذي المختصر:** الأساس التقني قوي (أمن أساسي، تكاملات محاسبية واسعة، CI/CD، Monitoring، Backup)، لكن توجد فجوات Must-have قبل الإطلاق تتعلق بالامتثال النهائي، الاعتمادية التشغيلية، وإثباتات تشغيلية نهائية لبعض التدفقات الحرجة في الإنتاج.

### تصنيف RAG العام
- 🟢 قوي: الأمان الأساسي، بنية المحاسبة والتكاملات، دورة التطوير والنشر
- 🟡 يحتاج تحسين: الأداء تحت حمل إنتاجي، استعادة الكوارث، جودة بيانات ما قبل الإطلاق
- 🔴 حرج: متطلبات امتثال/اعتمادية محددة قبل Go-Live

---

## 2) Inventory كامل للوحدات والصفحات

| الوحدة | صفحات الواجهة (تقريب فعلي) | كثافة API | RAG |
|---|---:|---:|---|
| Accounting | 26 | مرتفعة جدًا | 🟡 |
| Sales | 34 | مرتفعة | 🟡 |
| Buying (Purchases) | 27 (+ صفحات Purchases) | مرتفعة | 🟡 |
| Stock (Inventory) | 22 | مرتفعة | 🟡 |
| Treasury | 14 | متوسطة-مرتفعة | 🟡 |
| HR | 26 | مرتفعة | 🟡 |
| POS | 11 | متوسطة | 🟢 |
| Manufacturing | 16 | مرتفعة | 🟡 |
| Projects | 9 | مرتفعة | 🟡 |
| Assets | 7 | متوسطة-مرتفعة | 🟡 |
| CRM | 11 | مرتفعة | 🟢 |
| Expenses | 4 | متوسطة | 🟢 |
| Taxes | 6 | مرتفعة | 🟡 |
| Services | 3 | متوسطة | 🟢 |
| Admin/Settings | 5 + 30 | متوسطة | 🟡 |
| Reports | 10 | مرتفعة جدًا | 🟡 |

### مؤشرات جرد كلية
- API decorators فعلية: **769**
- توزيع الـ API: **392 GET / 244 POST / 80 PUT / 52 DELETE / 1 WebSocket**
- ملفات واجهة JSX/TSX: **312**
- اختبارات Backend: **51** ملف اختبار

---

## 3) تحليل تفصيلي لكل وحدة (مختصر تنفيذي)

> الصياغة التالية تحافظ على القالب الإجباري بشكل مختصر للإدارة التنفيذية.

### Accounting
- الحالة العامة (/100): 88
- الصفحات الموجودة: COA، قيود يومية، ميزانية، قائمة دخل، زكاة، تقارير مالية
- المميزات الموجودة فعليًا: قيود مزدوجة، تحقق توازن، إقفال سنوي، زكاة وحسابات مرتبطة
- السيناريوهات المدعومة: إنشاء/ترحيل/عكس قيود، تقارير مالية، زكاة
- السيناريوهات الحرجة الناقصة: توحيد سياسة التقريب (rounding) عبر كل التقارير
- التكاملات مع الوحدات الأخرى: Sales/Purchases/HR/POS/Assets/Projects/Manufacturing
- الضوابط المحاسبية/الضريبية: تحقق توازن القيد + قفل فترات + قيد زكاة
- مشاكل الصلاحيات المحتملة: حاجة لتغطية أوسع لاختبارات by-id
- مشاكل الأداء المتوقعة: تقارير ثقيلة دون load certification كاف
- المخاطر: انحراف تقارير عند نمو البيانات
- النواقص: Performance + Reconciliation على أحجام بيانات كبيرة
- الأولوية: High
- التصنيف: Must-have
- الاختبارات المطلوبة: Regression مالي + Performance reports + Reconciliation
- الحكم النهائي: جاهزة بشروط

### Sales
- الحالة العامة (/100): 80
- الصفحات الموجودة: Quotations/Orders/Invoices/Returns/Credit Notes/Delivery
- المميزات الموجودة فعليًا: دورة مبيعات كاملة، عوائد، إشعارات، VAT
- السيناريوهات المدعومة: Quotation -> SO -> Invoice -> Receipt
- السيناريوهات الحرجة الناقصة: إثبات إنتاجي حديث لسلامة O2C end-to-end
- التكاملات: Inventory + Accounting + Taxes + CRM
- الضوابط المحاسبية/الضريبية: AR/Revenue/VAT/COGS auto JE
- مشاكل الصلاحيات المحتملة: branch scope checks تحتاج توسيع
- مشاكل الأداء المتوقعة: قوائم الفواتير الكبيرة والفلاتر
- المخاطر: توقف الفوترة/التحصيل
- النواقص: Smoke إنتاجي موثق بعد آخر نشر
- الأولوية: High
- التصنيف: Must-have
- الاختبارات المطلوبة: O2C E2E + branch authorization + VAT reconciliation
- الحكم النهائي: جاهزة بشروط

### Buying
- الحالة العامة (/100): 78
- الصفحات الموجودة: RFQ/PO/GRN/Purchase Invoice/Payments/Landed Cost
- المميزات الموجودة فعليًا: دورة شراء كاملة + landed cost
- السيناريوهات المدعومة: RFQ -> PO -> GRN -> PI -> Supplier Payment
- السيناريوهات الحرجة الناقصة: إثبات مانع overpayment في الإنتاج
- التكاملات: Inventory + Accounting + Treasury + Taxes
- الضوابط المحاسبية/الضريبية: AP/VAT Input + قيود الدفع
- مشاكل الصلاحيات المحتملة: صلاحيات اعتماد متعددة المستويات
- مشاكل الأداء المتوقعة: استيراد/معالجة فواتير بكثافة
- المخاطر: تشوه أرصدة الموردين
- النواقص: DB-level safeguards إضافية
- الأولوية: High
- التصنيف: Must-have
- الاختبارات المطلوبة: P2P E2E + DB constraints + supplier reconciliation
- الحكم النهائي: جاهزة بشروط

### Stock
- الحالة العامة (/100): 84
- الصفحات الموجودة: منتجات، تحويلات، تسويات، batch/serial، مستودعات
- المميزات الموجودة فعليًا: تتبع دفعات وسيريال + تحويلات وتسويات
- السيناريوهات المدعومة: transfer/adjustment/cycle counting
- السيناريوهات الحرجة الناقصة: تحقق أثر كل حركة على GL تحت التوازي
- التكاملات: Sales + Buying + Manufacturing + Accounting
- الضوابط المحاسبية/الضريبية: COGS/WIP/Inventory accounts
- مشاكل الصلاحيات المحتملة: صلاحيات مستوى مستودع/فرع
- مشاكل الأداء المتوقعة: تقييم مخزون وتقارير حركة كثيفة
- المخاطر: انحراف تكلفة المخزون
- النواقص: اختبارات تزامن موسعة
- الأولوية: High
- التصنيف: Must-have
- الاختبارات المطلوبة: Concurrency + valuation reconciliation
- الحكم النهائي: جاهزة بشروط

### Treasury
- الحالة العامة (/100): 82
- الصفحات الموجودة: معاملات خزينة، تحويلات، تسوية بنكية، شيكات/سندات
- المميزات الموجودة فعليًا: expense/transfer/reconciliation
- السيناريوهات المدعومة: مصروفات، تحويلات، مطابقة بنكية
- السيناريوهات الحرجة الناقصة: اختبارات مطابقة بنكية على أحجام بيانات كبيرة
- التكاملات: Purchases + HR + Accounting
- الضوابط المحاسبية/الضريبية: قيود خزينة تلقائية
- مشاكل الصلاحيات المحتملة: maker/checker segregation
- مشاكل الأداء المتوقعة: bank statement imports
- المخاطر: أخطاء سيولة ومطابقة
- النواقص: Stress tests لعمليات الاستيراد
- الأولوية: Medium
- التصنيف: Must-have
- الاختبارات المطلوبة: Reconciliation pack + segregation checks
- الحكم النهائي: جاهزة بشروط

### HR
- الحالة العامة (/100): 83
- الصفحات الموجودة: موظفين، حضور، إجازات، رواتب، WPS/GOSI/EOS
- المميزات الموجودة فعليًا: Payroll + WPS export + saudization + EOS
- السيناريوهات المدعومة: Attendance/Leaves/Overtime -> Payroll -> JE
- السيناريوهات الحرجة الناقصة: تحقق تشغيلي نهائي WPS/GOSI لكل فرع
- التكاملات: Treasury + Accounting
- الضوابط المحاسبية/الضريبية: قيد رواتب وGOSI
- مشاكل الصلاحيات المحتملة: خصوصية بيانات الموظفين
- مشاكل الأداء المتوقعة: payroll batch runs
- المخاطر: مخالفة امتثال HR سعودي
- النواقص: UAT امتثال HR قبل الإطلاق
- الأولوية: High
- التصنيف: Must-have
- الاختبارات المطلوبة: Payroll compliance + WPS validation
- الحكم النهائي: جاهزة بشروط

### POS
- الحالة العامة (/100): 86
- الصفحات الموجودة: جلسات، بيع سريع، split payment، loyalty، offline
- المميزات الموجودة فعليًا: sessions + split payment + returns + offline queue
- السيناريوهات المدعومة: Session -> Sale -> Payment -> Return -> Sync
- السيناريوهات الحرجة الناقصة: اختبار sync conflict عند انقطاع/عودة الشبكة
- التكاملات: Sales + Inventory + Accounting + Taxes
- الضوابط المحاسبية/الضريبية: POS JE + VAT logic
- مشاكل الصلاحيات المحتملة: cashier/manager boundaries
- مشاكل الأداء المتوقعة: peak-hour throughput
- المخاطر: فقد أو ازدواجية معاملات
- النواقص: Chaos tests للشبكة
- الأولوية: High
- التصنيف: Must-have
- الاختبارات المطلوبة: Offline sync regression
- الحكم النهائي: جاهزة بشروط

### Manufacturing
- الحالة العامة (/100): 81
- الصفحات الموجودة: BOM/MRP/Orders/Schedule/Costing
- المميزات الموجودة فعليًا: WIP وFG postings
- السيناريوهات المدعومة: BOM -> Order -> WIP -> FG
- السيناريوهات الحرجة الناقصة: تدقيق variance حقيقي على حالات إنتاج
- التكاملات: Inventory + Accounting + Projects
- الضوابط المحاسبية/الضريبية: WIP capitalization
- مشاكل الصلاحيات المحتملة: صلاحيات مراكز العمل
- مشاكل الأداء المتوقعة: MRP runs كثيفة
- المخاطر: تكلفة منتج غير دقيقة
- النواقص: اختبارات MRP على بيانات production-scale
- الأولوية: Medium
- التصنيف: Must-have
- الاختبارات المطلوبة: Manufacturing E2E + variance reconciliation
- الحكم النهائي: جاهزة بشروط

### Projects
- الحالة العامة (/100): 79
- الصفحات الموجودة: مشاريع، مهام، budget، timesheet، profitability
- المميزات الموجودة فعليًا: project costing + invoicing + KPIs
- السيناريوهات المدعومة: Budget -> Timesheet -> Costing -> Invoicing
- السيناريوهات الحرجة الناقصة: تدقيق ربط timesheet بالقيد المالي
- التكاملات: HR + Sales + Accounting
- الضوابط المحاسبية/الضريبية: قيود labor/expense/revenue
- مشاكل الصلاحيات المحتملة: project-level access
- مشاكل الأداء المتوقعة: تقارير ربحية معقدة
- المخاطر: تضخم هامش/تكلفة غير حقيقي
- النواقص: Reconciliation مشروع-ربحية
- الأولوية: Medium
- التصنيف: Must-have
- الاختبارات المطلوبة: Project profitability audit tests
- الحكم النهائي: جاهزة بشروط

### Assets
- الحالة العامة (/100): 84
- الصفحات الموجودة: أصل، إهلاك، disposal، revaluation، leases
- المميزات الموجودة فعليًا: depreciation/disposal/impairment/lease
- السيناريوهات المدعومة: Acquisition -> Depreciation -> Disposal/Revaluation
- السيناريوهات الحرجة الناقصة: مراجعة سياسات العمر الإنتاجي
- التكاملات: Accounting + Reports
- الضوابط المحاسبية/الضريبية: قيود أصل/مجمع إهلاك/خسائر
- مشاكل الصلاحيات المحتملة: تعديل جداول الإهلاك
- مشاكل الأداء المتوقعة: mass depreciation
- المخاطر: تحريف قيمة الأصول
- النواقص: اختبار إهلاك جماعي على dataset كبير
- الأولوية: Medium
- التصنيف: Must-have
- الاختبارات المطلوبة: Assets lifecycle regression
- الحكم النهائي: جاهزة بشروط

### CRM
- الحالة العامة (/100): 85
- الصفحات الموجودة: leads/pipeline/contacts/forecasts/tickets
- المميزات الموجودة فعليًا: scoring/segments/pipeline analytics
- السيناريوهات المدعومة: lead -> opportunity -> forecast
- السيناريوهات الحرجة الناقصة: ربط التحويل النهائي للمبيعات بالتقارير
- التكاملات: Sales + Reports
- الضوابط المحاسبية/الضريبية: غير مباشرة
- مشاكل الصلاحيات المحتملة: بيانات العملاء الحساسة
- مشاكل الأداء المتوقعة: dashboards زمنية
- المخاطر: ضعف دقة التنبؤ
- النواقص: قواعد data quality للـ leads
- الأولوية: Low
- التصنيف: Nice-to-have
- الاختبارات المطلوبة: CRM analytics sanity checks
- الحكم النهائي: جاهزة

### Expenses
- الحالة العامة (/100): 84
- الصفحات الموجودة: إدخال/موافقة/سياسات/مرفقات
- المميزات الموجودة فعليًا: approval workflows + auto JE
- السيناريوهات المدعومة: submit -> approve -> post
- السيناريوهات الحرجة الناقصة: تدقيق fraud controls للمرفقات
- التكاملات: Treasury + Accounting + Approvals
- الضوابط المحاسبية/الضريبية: قيود مصروف تلقائية
- مشاكل الصلاحيات المحتملة: حدود الإنفاق حسب الدور
- مشاكل الأداء المتوقعة: مرفقات كبيرة
- المخاطر: إنفاق غير منضبط
- النواقص: توسيع اختبار policy engine
- الأولوية: Medium
- التصنيف: Must-have
- الاختبارات المطلوبة: Approval + expense policy regression
- الحكم النهائي: جاهزة بشروط

### Taxes
- الحالة العامة (/100): 76
- الصفحات الموجودة: VAT/WHT/Zakat/Compliance
- المميزات الموجودة فعليًا: VAT tracking + WHT rates + Zakat calc/post
- السيناريوهات المدعومة: VAT settlements + zakat posting
- السيناريوهات الحرجة الناقصة: ZATCA live portal + WHT auto GL
- التكاملات: Sales + Buying + Accounting
- الضوابط المحاسبية/الضريبية: VAT/WHT/Zakat
- مشاكل الصلاحيات المحتملة: إعدادات ضريبية حساسة
- مشاكل الأداء المتوقعة: tax reconciliation periods
- المخاطر: مخالفة امتثال قانوني
- النواقص: تكاملات الامتثال النهائية
- الأولوية: High
- التصنيف: Must-have
- الاختبارات المطلوبة: Compliance E2E + filing readiness
- الحكم النهائي: غير جاهزة

### Services
- الحالة العامة (/100): 82
- الصفحات الموجودة: طلبات خدمة، تعيين، أرشفة
- المميزات الموجودة فعليًا: service requests + logs
- السيناريوهات المدعومة: request -> assign -> complete
- السيناريوهات الحرجة الناقصة: ربط محكم بالفوترة/العقود
- التكاملات: Contracts + Sales + Reports
- الضوابط المحاسبية/الضريبية: غير مباشرة
- مشاكل الصلاحيات المحتملة: رؤية مستندات الخدمة
- مشاكل الأداء المتوقعة: أرشفة ملفات
- المخاطر: فقد traceability
- النواقص: SLA/aging analytics
- الأولوية: Low
- التصنيف: Nice-to-have
- الاختبارات المطلوبة: Service workflow regression
- الحكم النهائي: جاهزة بشروط

### Admin/Settings
- الحالة العامة (/100): 80
- الصفحات الموجودة: users/roles/security/settings/workflows
- المميزات الموجودة فعليًا: RBAC + 2FA + auditing
- السيناريوهات المدعومة: lifecycle للمستخدم والدور
- السيناريوهات الحرجة الناقصة: إثبات فصل الصلاحيات الحساسة بالكامل
- التكاملات: كل الوحدات
- الضوابط المحاسبية/الضريبية: غير مباشرة
- مشاكل الصلاحيات المحتملة: privilege escalation
- مشاكل الأداء المتوقعة: صفحات إعدادات كثيفة
- المخاطر: اختراق صلاحيات شامل
- النواقص: PenTest صلاحيات قبل go-live
- الأولوية: High
- التصنيف: Must-have
- الاختبارات المطلوبة: RBAC matrix + session revocation
- الحكم النهائي: جاهزة بشروط

### Reports
- الحالة العامة (/100): 83
- الصفحات الموجودة: financial/kpi/custom/scheduled/shared
- المميزات الموجودة فعليًا: تصدير، جدولة، تقارير مالية
- السيناريوهات المدعومة: تقارير تشغيلية ومالية متعددة
- السيناريوهات الحرجة الناقصة: baseline أداء تقارير ثقيلة
- التكاملات: كل الوحدات
- الضوابط المحاسبية/الضريبية: reconciliation outputs
- مشاكل الصلاحيات المحتملة: shared report leakage
- مشاكل الأداء المتوقعة: ضغط DB وقت الذروة
- المخاطر: قرارات إدارية على بيانات غير متطابقة
- النواقص: performance + consistency certification
- الأولوية: High
- التصنيف: Must-have
- الاختبارات المطلوبة: Report reconciliation + load test
- الحكم النهائي: جاهزة بشروط

---

## 4) Gap Analysis (As-Is vs To-Be)

| المجال | As-Is | To-Be قبل Go-Live | الفجوة | الأثر التجاري/التشغيلي | أولوية | تصنيف |
|---|---|---|---|---|---|---|
| الامتثال الضريبي السعودي | ZATCA phase 1 حاضر | تكامل live portal + filing readiness | تكامل ناقص | خطر امتثال وغرامات | High | Must-have |
| WHT | إدارة rates موجودة | Auto GL posting متكامل | قيد تلقائي غير مكتمل | أخطاء إقفال ضريبي | High | Must-have |
| O2C/P2P production proof | أدلة سابقة متباينة | Smoke/Regression حديث ومؤكد | دليل تشغيلي غير كافٍ | تعطيل إيراد/مدفوعات | High | Must-have |
| RLS/RBAC by-id | آليات موجودة | تغطية شاملة لكل الوحدات الحساسة | تغطية غير مكتملة | كشف بيانات بين الفروع | High | Must-have |
| Performance تحت حمل | اختبارات أساسية متوفرة | Load certification واقعي | فجوة تحقق | بطء/انقطاع | High | Must-have |
| PgBouncer | غير مفعل | pooling فعلي | مفقود | اتصال DB غير مستقر عند التوسع | Medium | Must-have |
| DR drill | Runbook + backup موجود | اختبار DR موثق برقم RTO/RPO | تنفيذ غير موثق دوريًا | تعافي بطيء عند الحوادث | High | Must-have |
| Restore automation | موجود جزئيًا | playbook آلي متكرر | شبه يدوي | خطأ بشري | Medium | Must-have |
| Monitoring depth | Prometheus/Grafana أساسي | Exporters + SLO alerts | مراقبة ناقصة | ضعف الإنذار المبكر | Medium | Nice-to-have |
| Security assurance | 2FA/RBAC/audit موجودة | PenTest نهائي + secret rotation cadence | إثبات نهائي ناقص | مخاطر اختراق/امتثال | High | Must-have |

---

## 5) Risk Register

| Risk | Probability | Impact | Severity | Mitigation | Owner | Due Date |
|---|---|---|---|---|---|---|
| عدم اكتمال ZATCA live | متوسط | عالٍ جدًا | 🔴 | إنهاء التكامل + UAT ضريبي | Tax Lead + Backend Lead | 15-04-2026 |
| خلل O2C بالإنتاج | متوسط | عالٍ جدًا | 🔴 | smoke O2C آلي بعد كل نشر | QA + DevOps | 07-04-2026 |
| خلل P2P/overpayment | متوسط | عالٍ جدًا | 🔴 | DB constraints + integration tests | Backend + QA | 07-04-2026 |
| تسريب صلاحيات بين الفروع | متوسط | عالٍ | 🔴 | RBAC/RLS matrix tests | Security Lead | 12-04-2026 |
| اختناق DB connections | متوسط | عالٍ | 🟡 | PgBouncer + tuning | DevOps Lead | 20-04-2026 |
| فشل الاستعادة في حادث | منخفض-متوسط | عالٍ جدًا | 🔴 | DR drill + توثيق RTO/RPO | DevOps + DBA | 25-04-2026 |
| بطء التقارير الثقيلة | متوسط | عالٍ | 🟡 | indexing + caching + load test | Backend + DBA | 30-04-2026 |
| غياب exporters تفصيلية | متوسط | متوسط | 🟡 | نشر DB/Redis exporters | SRE | 18-04-2026 |
| جودة بيانات افتتاحية منخفضة | متوسط | عالٍ | 🟡 | reconciliation + duplicate checks | Finance + Data | 10-04-2026 |
| تدوير أسرار غير منتظم | منخفض-متوسط | عالٍ جدًا | 🔴 | سياسة rotation ربع سنوية | Security + DevOps | 08-04-2026 |

---

## 6) Top 10 Critical Gaps قبل الإطلاق

1. 🔴 ZATCA live portal readiness غير مكتمل
2. 🔴 WHT auto GL posting غير مكتمل
3. 🔴 إثبات تشغيل O2C إنتاجي حديث غير كافٍ
4. 🔴 إثبات تشغيل P2P إنتاجي حديث غير كافٍ
5. 🔴 تغطية RBAC/RLS by-id غير مكتملة لكل الوحدات الحساسة
6. 🔴 DR drill فعلي غير موثق بنتائج RTO/RPO
7. 🟡 PgBouncer غير مفعل
8. 🟡 اختبار حمل إنتاجي شامل غير معتمد
9. 🟡 Restore automation غير مكتمل
10. 🟡 Exporters لقواعد البيانات/Redis غير مكتملة

---

## 7) Top 10 Quick Wins (30 يوم)

1. بوابة CI تمنع النشر إذا فشل smoke O2C/P2P
2. تشغيل RBAC matrix tests تلقائيًا يوميًا
3. تفعيل PostgreSQL/Redis exporters
4. إضافة DB constraints مالية حرجة
5. توحيد rounding policy على الضرائب والتقارير
6. حزمة reconciliation قبل الإقفال الشهري
7. اختبار Offline POS fault-injection أسبوعي
8. تحسين فهارس التقارير الثقيلة
9. تمرين استعادة شهري
10. لوحة تنفيذية يومية لحالة RAG

---

## 8) Go-Live Decision

- **جاهز للإطلاق؟** لا
- **نسبة الجاهزية:** 82%

### شروط الإطلاق الإلزامية
1. إغلاق فجوات الامتثال الضريبي الحرجة (ZATCA live + WHT auto GL).
2. تمرير smoke/regression موثق لتدفقات O2C وP2P على البيئة المستهدفة.
3. تنفيذ DR drill فعلي وتوثيق RTO/RPO.
4. إكمال مصفوفة صلاحيات RBAC/RLS واختبارات by-id للوحدات الحساسة.
5. تفعيل تحسينات الاعتمادية (Pooling + مراقبة أعمق) قبل التوسع.

---

## 9) خطة 30/60/90 يوم

### 30 يوم (Stabilize & Gate)
- إغلاق البنود الحرجة.
- ربط بوابات النشر بـ smoke + RBAC tests.
- تنفيذ DR drill أول وتقرير تنفيذي.
- الهدف: رفع الجاهزية إلى 90%.

### 60 يوم (Scale & Hardening)
- تفعيل pooling + DB tuning.
- Load testing شامل API/Reports/POS.
- تحسين الفهارس والاستعلامات الثقيلة.
- الهدف: رفع الجاهزية إلى 94%.

### 90 يوم (Compliance Maturity)
- استقرار دورة امتثال ضريبي شهرية end-to-end.
- PenTest دوري + معالجة findings.
- أتمتة restore playbook.
- الهدف: 96%+ مع استدامة تشغيلية.

---

## 10) أسئلة استيضاحية (أولوية)

1. هل تم إغلاق ZATCA live portal فعليًا في الإنتاج أم ما زال Phase 1 فقط؟
2. هل توجد نتائج smoke/regression موثقة بعد آخر نشر لـ O2C/P2P؟
3. هل RTO/RPO معتمدين رسميًا وتم اختبارهما فعليًا؟
4. هل PgBouncer شرط Go-Live إلزامي أم شرط تحسين خلال 30 يوم؟
5. هل تم اعتماد مصفوفة صلاحيات نهائية على مستوى الفرع/المستودع/المشروع؟

---

## ملخص تدفقات الأعمال الإلزامية (Cross-Module)

| التدفق | الحالة | الملاحظة | التصنيف |
|---|---|---|---|
| Sales Flow | 🟡 | الربط المالي موجود ويلزم إثبات تشغيل إنتاجي حديث | Must-have |
| Purchase Flow | 🟡 | الدورة موجودة ويلزم إثبات مانع overpayment إنتاجيًا | Must-have |
| Inventory Flow | 🟡 | الأثر المالي موجود ويلزم اختبارات تزامن أوسع | Must-have |
| HR Payroll Flow | 🟡 | WPS/GOSI/JE موجودة ويلزم UAT امتثال نهائي | Must-have |
| POS Flow | 🟡 | Offline/split/returns موجودة ويلزم sync conflict testing | Must-have |
| Manufacturing Flow | 🟡 | WIP/FG موجودان ويلزم variance validation | Must-have |
| Projects Flow | 🟡 | Budget/costing/invoicing موجودة ويلزم ربط profitability | Must-have |
| Fixed Assets Flow | 🟢 | Lifecycle مالي متكامل بدرجة جيدة | Must-have |
| Tax Flow | 🔴 | ZATCA live + WHT auto GL فجوة حرجة | Must-have |
| Admin/Security Flow | 🟡 | lifecycle/audit موجودان ويلزم RBAC matrix كاملة | Must-have |

---

## Go-Live Checklist (Final)

| البند | الحالة | RAG |
|---|---|---|
| Security (Auth/RBAC/2FA/Session/Rate limits/Audit) | شبه مكتمل | 🟡 |
| Compliance (ZATCA/WPS/GOSI/Tax filing) | مكتمل جزئيًا | 🔴 |
| Performance (API/reports/concurrency/POS) | مكتمل جزئيًا | 🟡 |
| Reliability (Backup/Restore/DR/RTO-RPO/Failover) | متوسط | 🟡 |
| Infrastructure (Pooling/Provisioning/Observability) | متوسط | 🟡 |
| Quality (Unit/Integration/UAT/Regression/PenTest) | جيد جزئيًا | 🟡 |
| Operations (CI/CD/Rollback/Incident/Runbook) | جيد | 🟢 |
| Data (opening/reconciliation/duplicates/migration) | متوسط | 🟡 |

---

## التوصية النهائية

**لا أنصح بالإطلاق الآن** حتى إغلاق شروط Must-have المذكورة، ثم إعادة التقييم باختبار تشغيلي موثق.
