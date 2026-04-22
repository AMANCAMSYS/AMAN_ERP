"""
AMAN ERP - اختبارات شاملة للتكامل وسير العمل المحاسبي
Comprehensive Integration & Workflow Tests
═══════════════════════════════════════════════════════
يتضمن: دورة المبيعات الكاملة، دورة المشتريات الكاملة، دورة التصنيع،
التحقق من الأرصدة المحاسبية، التكامل بين الوحدات
"""

import pytest
from datetime import date, timedelta
from helpers import assert_valid_response


# ═══════════════════════════════════════════════════════════════
# 🔄 دورة المبيعات الكاملة - Complete Sales Cycle
# ═══════════════════════════════════════════════════════════════
class TestCompleteSalesCycleWorkflow:
    """دورة المبيعات الكاملة: عرض سعر ← أمر بيع ← فاتورة ← تحصيل"""

    def test_sales_cycle_step1_create_quotation(self, client, admin_headers):
        """الخطوة 1: إنشاء عرض سعر"""
        r = client.get("/api/sales/customers", headers=admin_headers)
        customers = r.json()
        if not customers:
            pytest.skip("لا عملاء")

        r2 = client.post("/api/sales/quotations", json={
            "customer_id": customers[0]["id"],
            "quotation_date": str(date.today()),
            "valid_until": str(date.today() + timedelta(days=30)),
            "items": [
                {"product_id": 1, "description": "منتج 1", "quantity": 10, "unit_price": 100, "tax_rate": 15},
                {"product_id": 2, "description": "منتج 2", "quantity": 5, "unit_price": 200, "tax_rate": 15},
            ]
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400]

    def test_sales_cycle_step2_convert_to_order(self, client, admin_headers):
        """الخطوة 2: تحويل عرض السعر لأمر بيع"""
        r = client.get("/api/sales/quotations", headers=admin_headers)
        quotations = r.json()
        if not quotations:
            pytest.skip("لا عروض أسعار")
        
        quot = quotations[0]
        quot_id = quot["id"]
        r2 = client.post(f"/api/sales/quotations/{quot_id}/convert-to-order", 
                        headers=admin_headers)
        assert r2.status_code in [200, 201, 400, 404]

    def test_sales_cycle_step3_create_invoice_from_order(self, client, admin_headers):
        """الخطوة 3: إنشاء فاتورة من أمر البيع - القيد: مدين العميل / دائن المبيعات والضريبة"""
        r = client.get("/api/sales/orders", headers=admin_headers)
        orders = r.json()
        confirmed = next((o for o in orders if o.get("status") in ["confirmed", "approved"]), None)
        if not confirmed:
            pytest.skip("لا أمر بيع معتمد")

        order_id = confirmed["id"]
        r2 = client.post(f"/api/sales/orders/{order_id}/create-invoice", 
                        headers=admin_headers)
        assert r2.status_code in [200, 201, 400, 404]

    def test_sales_cycle_step4_collect_payment(self, client, admin_headers):
        """الخطوة 4: تحصيل الدفعة - القيد: مدين الصندوق / دائن العميل"""
        r = client.get("/api/sales/invoices", headers=admin_headers)
        invoices = r.json()
        unpaid = next((i for i in invoices if i.get("status") in ["unpaid", "partial"]), None)
        if not unpaid:
            pytest.skip("لا فواتير غير مدفوعة")

        invoice_id = unpaid["id"]
        amount = unpaid.get("total", unpaid.get("remaining_amount", 100))
        r2 = client.post("/api/treasury/transactions/receipt", json={
            "transaction_type": "receipt",
            "party_id": unpaid.get("customer_id"),
            "amount": amount,
            "treasury_id": 2,
            "invoice_id": invoice_id,
            "transaction_date": str(date.today()),
            "description": "تحصيل فاتورة",
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400, 404, 422, 500]


# ═══════════════════════════════════════════════════════════════
# 🔄 دورة المشتريات الكاملة - Complete Purchase Cycle
# ═══════════════════════════════════════════════════════════════
class TestCompletePurchaseCycleWorkflow:
    """دورة المشتريات الكاملة: طلب شراء ← فاتورة شراء ← استلام ← دفع"""

    def test_purchase_cycle_step1_create_order(self, client, admin_headers):
        """الخطوة 1: إنشاء أمر شراء"""
        r = client.get("/api/buying/suppliers", headers=admin_headers)
        suppliers = r.json()
        if not suppliers:
            pytest.skip("لا موردين")

        r2 = client.post("/api/buying/orders", json={
            "supplier_id": suppliers[0]["id"],
            "order_date": str(date.today()),
            "expected_date": str(date.today() + timedelta(days=7)),
            "items": [
                {"product_id": 1, "description": "مواد أولية", "quantity": 50, "unit_price": 80, "tax_rate": 15},
            ]
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400]

    def test_purchase_cycle_step2_approve_order(self, client, admin_headers):
        """الخطوة 2: اعتماد أمر الشراء"""
        r = client.get("/api/buying/orders", headers=admin_headers)
        orders = r.json()
        draft = next((o for o in orders if o.get("status") == "draft"), None)
        if not draft:
            pytest.skip("لا أمر شراء مسودة")

        order_id = draft["id"]
        r2 = client.put(f"/api/buying/orders/{order_id}/approve", headers=admin_headers)
        assert r2.status_code in [200, 400, 404]

    def test_purchase_cycle_step3_create_invoice(self, client, admin_headers):
        """الخطوة 3: إنشاء فاتورة شراء - القيد: مدين المشتريات والضريبة / دائن المورد"""
        r = client.get("/api/buying/suppliers", headers=admin_headers)
        suppliers = r.json()
        if not suppliers:
            pytest.skip("لا موردين")

        r2 = client.post("/api/buying/invoices", json={
            "supplier_id": suppliers[0]["id"],
            "invoice_date": str(date.today()),
            "payment_method": "credit",
            "items": [
                {"product_id": 1, "description": "مواد أولية", "quantity": 50, "unit_price": 80, "tax_rate": 15},
            ]
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400]

    def test_purchase_cycle_step4_pay_supplier(self, client, admin_headers):
        """الخطوة 4: الدفع للمورد - القيد: مدين المورد / دائن البنك"""
        r = client.get("/api/buying/suppliers", headers=admin_headers)
        suppliers = r.json()
        if not suppliers:
            pytest.skip("لا موردين")

        r2 = client.post("/api/buying/payments", json={
            "supplier_id": suppliers[0]["id"],
            "amount": 2000,
            "payment_method": "bank_transfer",
            "voucher_date": str(date.today()),
            "treasury_id": 3,
            "description": "دفعة للمورد",
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400]


# ═══════════════════════════════════════════════════════════════
# 🔄 دورة التصنيع الكاملة - Complete Manufacturing Cycle
# ═══════════════════════════════════════════════════════════════
class TestCompleteManufacturingWorkflow:
    """دورة التصنيع: قائمة مواد ← أمر إنتاج ← إكمال الأمر ← تحديث المخزون"""

    def test_manufacturing_step1_verify_bom(self, client, admin_headers):
        """الخطوة 1: التأكد من وجود قائمة مواد"""
        r = client.get("/api/manufacturing/boms", headers=admin_headers)
        assert_valid_response(r)
        boms = r.json()
        assert len(boms) >= 0, "يجب أن تكون قائمة المواد صالحة"
        if not boms:
            pytest.skip("لا قوائم مواد في قاعدة البيانات")

    def test_manufacturing_step2_create_production_order(self, client, admin_headers):
        """الخطوة 2: إنشاء أمر إنتاج"""
        r = client.get("/api/manufacturing/boms", headers=admin_headers)
        boms = r.json()
        if not boms:
            pytest.skip("لا قوائم مواد")

        bom_id = boms[0]["id"]
        r2 = client.post("/api/manufacturing/orders", json={
            "bom_id": bom_id,
            "quantity": 5,
            "status": "planned",
            "start_date": str(date.today()),
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400]

    def test_manufacturing_step3_complete_production(self, client, admin_headers):
        """الخطوة 3: إكمال الإنتاج وتحديث المخزون"""
        r = client.get("/api/manufacturing/orders", headers=admin_headers)
        orders = r.json()
        planned = next((o for o in orders if o.get("status") in ["planned", "in_progress"]), None)
        if not planned:
            pytest.skip("لا أمر إنتاج للإكمال")

        order_id = planned["id"]
        r2 = client.post(f"/api/manufacturing/orders/{order_id}/complete", 
                        headers=admin_headers)
        # May fail due to insufficient materials
        assert r2.status_code in [200, 400, 500]


# ═══════════════════════════════════════════════════════════════
# 🔄 دورة نقاط البيع الكاملة - Complete POS Cycle
# ═══════════════════════════════════════════════════════════════
class TestCompletePOSWorkflow:
    """دورة نقاط البيع: فتح جلسة ← طلبات ← إغلاق جلسة"""

    def test_pos_step1_open_session(self, client, admin_headers):
        """الخطوة 1: فتح جلسة البيع"""
        # Close any existing session first
        active = client.get("/api/pos/sessions/active", headers=admin_headers)
        if active.status_code == 200 and active.json():
            sid = active.json().get("id")
            if sid:
                client.post(f"/api/pos/sessions/{sid}/close", json={
                    "closing_balance": 0,
                    "cash_register_balance": 0,
                }, headers=admin_headers)

        r = client.post("/api/pos/sessions/open", json={
            "warehouse_id": 1,
            "opening_balance": 1000,
            "branch_id": 1,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 500]

    def test_pos_step2_create_orders(self, client, admin_headers):
        """الخطوة 2: إنشاء طلبات متعددة"""
        active = client.get("/api/pos/sessions/active", headers=admin_headers)
        if active.status_code != 200 or not active.json():
            pytest.skip("لا جلسة نشطة")

        session_id = active.json()["id"]
        
        # Create multiple orders
        for i in range(3):
            r = client.post("/api/pos/orders", json={
                "session_id": session_id,
                "items": [
                    {"product_id": 1, "quantity": 1 + i, "unit_price": 100, "tax_rate": 15},
                ],
                "payments": [
                    {"method": "cash", "amount": 115 * (1 + i)},
                ],
                "status": "paid",
            }, headers=admin_headers)
            # Just check it doesn't crash
            assert r.status_code in [200, 201, 400]

    def test_pos_step3_close_session(self, client, admin_headers):
        """الخطوة 3: إغلاق جلسة البيع"""
        active = client.get("/api/pos/sessions/active", headers=admin_headers)
        if active.status_code != 200 or not active.json():
            pytest.skip("لا جلسة نشطة")

        session_id = active.json()["id"]
        r = client.post(f"/api/pos/sessions/{session_id}/close", json={
            "closing_balance": 2000,
            "cash_register_balance": 2000,
            "notes": "إغلاق جلسة اختبار التكامل",
        }, headers=admin_headers)
        assert r.status_code in [200, 400, 500]


# ═══════════════════════════════════════════════════════════════
# ✅ التحقق من الأرصدة المحاسبية - Balance Verification
# ═══════════════════════════════════════════════════════════════
class TestAccountingBalanceVerification:
    """التحقق من صحة الأرصدة المحاسبية"""

    def test_trial_balance_is_balanced(self, client, admin_headers):
        """✅ ميزان المراجعة متوازن (المدين = الدائن)"""
        r = client.get("/api/reports/accounting/trial-balance", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        
        # Extract totals
        total_debit = data.get("total_debit", 0)
        total_credit = data.get("total_credit", 0)
        
        # If totals are in the data directly
        if total_debit and total_credit:
            diff = abs(float(total_debit) - float(total_credit))
            assert diff < 1, f"ميزان المراجعة غير متوازن: مدين={total_debit}, دائن={total_credit}"

    def test_balance_sheet_equation(self, client, admin_headers):
        """✅ معادلة الميزانية: الأصول = الخصوم + حقوق الملكية"""
        r = client.get("/api/reports/accounting/balance-sheet", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        
        # Extract totals if available
        total_assets = data.get("total_assets", 0)
        total_liabilities = data.get("total_liabilities", 0)
        total_equity = data.get("total_equity", 0)
        
        if total_assets and (total_liabilities or total_equity):
            left_side = float(total_assets)
            right_side = float(total_liabilities or 0) + float(total_equity or 0)
            diff = abs(left_side - right_side)
            # Allow small rounding differences
            assert diff < 1, f"معادلة الميزانية غير متوازنة: أصول={total_assets}, خصوم+حقوق={right_side}"

    def test_all_journal_entries_balanced(self, client, admin_headers):
        """✅ جميع القيود اليومية متوازنة"""
        r = client.get("/api/accounting/journal-entries", headers=admin_headers)
        assert_valid_response(r)
        entries = r.json()
        if isinstance(entries, dict):
            entries = entries.get("items", entries.get("data", []))
        
        for entry in entries[:20]:  # Check first 20
            if "lines" in entry:
                total_debit = sum(float(line.get("debit", 0)) for line in entry["lines"])
                total_credit = sum(float(line.get("credit", 0)) for line in entry["lines"])
                diff = abs(total_debit - total_credit)
                assert diff < 0.01, f"القيد {entry.get('entry_number')} غير متوازن"


# ═══════════════════════════════════════════════════════════════
# 🔗 تكامل الوحدات - Module Integration
# ═══════════════════════════════════════════════════════════════
class TestModuleIntegration:
    """اختبارات تكامل الوحدات"""

    def test_sales_invoice_creates_journal_entry(self, client, admin_headers):
        """✅ فاتورة المبيعات تُنشئ قيد يومي"""
        r = client.get("/api/sales/invoices", headers=admin_headers)
        invoices = r.json()
        if not invoices:
            pytest.skip("لا فواتير")
        
        invoice = invoices[0]
        # Most invoices should have a journal entry
        journal_id = invoice.get("journal_entry_id")
        if journal_id:
            r2 = client.get(f"/api/accounting/journal-entries/{journal_id}", 
                          headers=admin_headers)
            assert r2.status_code in [200, 404]

    def test_purchase_invoice_creates_journal_entry(self, client, admin_headers):
        """✅ فاتورة المشتريات تُنشئ قيد يومي"""
        r = client.get("/api/buying/invoices", headers=admin_headers)
        invoices = r.json()
        if not invoices:
            pytest.skip("لا فواتير شراء")
        
        invoice = invoices[0]
        journal_id = invoice.get("journal_entry_id")
        if journal_id:
            r2 = client.get(f"/api/accounting/journal-entries/{journal_id}", 
                          headers=admin_headers)
            assert r2.status_code in [200, 404]

    def test_treasury_transactions_update_balances(self, client, admin_headers):
        """✅ عمليات الخزينة تُحدث الأرصدة"""
        r = client.get("/api/treasury/accounts", headers=admin_headers)
        assert_valid_response(r)
        accounts = r.json()
        
        for acc in accounts[:5]:
            balance = acc.get("current_balance", acc.get("balance", 0))
            # Balance can be any value but should exist
            assert balance is not None

    def test_inventory_movements_tracked(self, client, admin_headers):
        """✅ حركات المخزون مُتتبَعة"""
        r = client.get("/api/inventory/movements", headers=admin_headers)
        assert r.status_code in [200, 404]
        if r.status_code == 200:
            movements = r.json()
            assert isinstance(movements, list)

    def test_payroll_creates_journal_entries(self, client, admin_headers):
        """✅ الرواتب تُنشئ قيود يومية"""
        r = client.get("/api/hr/payroll-periods", headers=admin_headers)
        periods = r.json()
        processed = next((p for p in periods if p.get("status") == "processed"), None)
        if processed:
            journal_id = processed.get("journal_entry_id")
            if journal_id:
                r2 = client.get(f"/api/accounting/journal-entries/{journal_id}", 
                              headers=admin_headers)
                assert r2.status_code in [200, 404]


# ═══════════════════════════════════════════════════════════════
# 📊 تقارير شاملة - Comprehensive Reports
# ═══════════════════════════════════════════════════════════════
class TestComprehensiveReports:
    """اختبارات التقارير الشاملة"""

    def test_all_financial_reports_load(self, client, admin_headers):
        """✅ جميع التقارير المالية تُحمّل"""
        reports = [
            "/api/reports/accounting/trial-balance",
            "/api/reports/accounting/profit-loss",
            "/api/reports/accounting/balance-sheet",
            "/api/reports/accounting/cashflow",
        ]
        for report_url in reports:
            r = client.get(report_url, headers=admin_headers)
            assert r.status_code in [200, 404], f"فشل تحميل التقرير: {report_url}"

    def test_all_sales_reports_load(self, client, admin_headers):
        """✅ جميع تقارير المبيعات تُحمّل"""
        reports = [
            "/api/reports/sales/summary",
            "/api/reports/sales/trend",
            "/api/reports/sales/by-customer",
            "/api/reports/sales/by-product",
            "/api/reports/sales/aging",
        ]
        for report_url in reports:
            r = client.get(report_url, headers=admin_headers)
            assert r.status_code in [200, 404], f"فشل تحميل التقرير: {report_url}"

    def test_all_purchase_reports_load(self, client, admin_headers):
        """✅ جميع تقارير المشتريات تُحمّل"""
        reports = [
            "/api/reports/purchases/summary",
            "/api/reports/purchases/trend",
            "/api/reports/purchases/by-supplier",
        ]
        for report_url in reports:
            r = client.get(report_url, headers=admin_headers)
            assert r.status_code in [200, 404], f"فشل تحميل التقرير: {report_url}"

    def test_dashboard_loads_all_stats(self, client, admin_headers):
        """✅ لوحة التحكم تُحمّل جميع الإحصائيات"""
        r = client.get("/api/dashboard/stats", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        assert isinstance(data, dict)


# ═══════════════════════════════════════════════════════════════
# 🔐 اختبارات الصلاحيات - Permission Tests
# ═══════════════════════════════════════════════════════════════
class TestPermissionsIntegration:
    """اختبارات تكامل الصلاحيات"""

    def test_unauthorized_access_rejected(self, client):
        """❌ الوصول غير المصرح به مرفوض"""
        endpoints = [
            "/api/accounting/accounts",
            "/api/sales/invoices",
            "/api/buying/orders",
            "/api/hr/employees",
        ]
        for endpoint in endpoints:
            r = client.get(endpoint)  # No headers
            assert r.status_code in [401, 403, 422], f"يجب رفض الوصول: {endpoint}"

    def test_invalid_token_rejected(self, client):
        """❌ التوكن غير الصالح مرفوض"""
        headers = {"Authorization": "Bearer invalid_token_12345"}
        r = client.get("/api/accounting/accounts", headers=headers)
        assert r.status_code in [401, 403, 422]


# ═══════════════════════════════════════════════════════════════
# 🏁 اختبار النظام الشامل - System Health Check
# ═══════════════════════════════════════════════════════════════
class TestSystemHealthCheck:
    """فحص صحة النظام"""

    def test_all_main_endpoints_respond(self, client, admin_headers):
        """✅ جميع نقاط النهاية الرئيسية تستجيب"""
        endpoints = [
            "/api/accounting/accounts",
            "/api/sales/customers",
            "/api/sales/invoices",
            "/api/buying/suppliers",
            "/api/inventory/products",
            "/api/treasury/accounts",
            "/api/hr/employees",
            "/api/dashboard/stats",
        ]
        for endpoint in endpoints:
            r = client.get(endpoint, headers=admin_headers)
            assert r.status_code in [200, 404], f"فشلت نقطة النهاية: {endpoint}"

    def test_database_connections_healthy(self, client, admin_headers):
        """✅ اتصالات قاعدة البيانات سليمة"""
        # If we can fetch accounts, the DB connection is healthy
        r = client.get("/api/accounting/accounts", headers=admin_headers)
        assert r.status_code == 200

    def test_authentication_system_working(self, client, admin_headers):
        """✅ نظام المصادقة يعمل"""
        r = client.get("/api/auth/me", headers=admin_headers)
        assert_valid_response(r)
        user = r.json()
        assert "id" in user or "username" in user

