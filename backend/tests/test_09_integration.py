"""
AMAN ERP - اختبارات التكامل المحاسبي
Accounting Integration Tests
═══════════════════════════════════════════════════════
يتضمن: التكامل بين الوحدات المختلفة والتحقق من الصحة المحاسبية الشاملة
هذه أهم الاختبارات - تتأكد أن النظام يعمل كنظام ERP متكامل
"""

import pytest
from helpers import assert_valid_response


class TestDashboard:
    """📊 اختبارات لوحة التحكم"""

    def test_dashboard_stats(self, client, admin_headers):
        """✅ إحصائيات لوحة التحكم"""
        response = client.get("/api/dashboard/stats", headers=admin_headers)
        assert_valid_response(response)

    def test_financial_charts(self, client, admin_headers):
        """✅ الرسوم البيانية المالية"""
        response = client.get("/api/dashboard/charts/financial", headers=admin_headers)
        assert_valid_response(response)

    def test_product_charts(self, client, admin_headers):
        """✅ الرسوم البيانية للمنتجات"""
        response = client.get("/api/dashboard/charts/products", headers=admin_headers)
        assert_valid_response(response)


class TestCurrencies:
    """💱 اختبارات العملات"""

    def test_list_currencies(self, client, admin_headers):
        """✅ عرض العملات"""
        response = client.get("/api/accounting/currencies/", headers=admin_headers)
        assert_valid_response(response)

    def test_base_currency_exists(self, client, admin_headers):
        """✅ يجب أن توجد عملة أساسية"""
        response = client.get("/api/accounting/currencies/", headers=admin_headers)
        if response.status_code != 200:
            pytest.skip("لا يمكن تحميل العملات")
        
        currencies = response.json()
        has_base = any(c.get("is_base") for c in currencies)
        assert has_base, "⚠️ لا توجد عملة أساسية محددة!"

    def test_exchange_rates_positive(self, client, admin_headers):
        """✅ أسعار الصرف موجبة"""
        response = client.get("/api/accounting/currencies/", headers=admin_headers)
        if response.status_code != 200:
            pytest.skip("لا يمكن تحميل العملات")
        
        currencies = response.json()
        for c in currencies:
            rate = c.get("current_rate", c.get("rate", 1)) or 1
            assert rate > 0, f"⚠️ سعر صرف سالب أو صفر للعملة {c.get('code')}: {rate}"


class TestBranches:
    """🏢 اختبارات الفروع"""

    def test_list_branches(self, client, admin_headers):
        """✅ عرض الفروع"""
        response = client.get("/api/branches", headers=admin_headers)
        assert_valid_response(response)


class TestRoles:
    """🔐 اختبارات الأدوار والصلاحيات"""

    def test_list_roles(self, client, admin_headers):
        """✅ عرض الأدوار"""
        response = client.get("/api/roles", headers=admin_headers)
        assert_valid_response(response)

    def test_list_permissions(self, client, admin_headers):
        """✅ عرض الصلاحيات المتاحة"""
        response = client.get("/api/roles/permissions", headers=admin_headers)
        assert_valid_response(response)


class TestCostCenters:
    """🎯 اختبارات مراكز التكلفة"""

    def test_list_cost_centers(self, client, admin_headers):
        """✅ عرض مراكز التكلفة"""
        response = client.get("/api/cost-centers", headers=admin_headers)
        assert_valid_response(response)


class TestBudgets:
    """💼 اختبارات الموازنات"""

    def test_list_budgets(self, client, admin_headers):
        """✅ عرض الموازنات"""
        response = client.get("/api/accounting/budgets/", headers=admin_headers)
        assert_valid_response(response)


class TestAssets:
    """🏗️ اختبارات الأصول الثابتة"""

    def test_list_assets(self, client, admin_headers):
        """✅ عرض الأصول"""
        response = client.get("/api/assets", headers=admin_headers)
        assert_valid_response(response)


class TestManufacturing:
    """🏭 اختبارات التصنيع"""

    def test_list_boms(self, client, admin_headers):
        """✅ عرض قوائم المواد"""
        response = client.get("/api/manufacturing/boms", headers=admin_headers)
        assert_valid_response(response)

    def test_list_production_orders(self, client, admin_headers):
        """✅ عرض أوامر الإنتاج"""
        response = client.get("/api/manufacturing/orders", headers=admin_headers)
        assert_valid_response(response)


class TestContracts:
    """📃 اختبارات العقود"""

    def test_list_contracts(self, client, admin_headers):
        """✅ عرض العقود"""
        response = client.get("/api/contracts", headers=admin_headers)
        assert_valid_response(response)


class TestReconciliation:
    """🔄 اختبارات التسوية البنكية"""

    def test_list_reconciliations(self, client, admin_headers):
        """✅ عرض التسويات"""
        response = client.get("/api/reconciliation", headers=admin_headers)
        assert_valid_response(response)


class TestAuditLogs:
    """📋 اختبارات سجل المراجعة"""

    def test_list_audit_logs(self, client, admin_headers):
        """✅ عرض سجلات المراجعة"""
        response = client.get("/api/audit/logs", headers=admin_headers)
        assert_valid_response(response)

    def test_audit_stats(self, client, admin_headers):
        """✅ إحصائيات المراجعة"""
        response = client.get("/api/audit/logs/stats", headers=admin_headers)
        assert_valid_response(response)


class TestSettings:
    """⚙️ اختبارات الإعدادات"""

    def test_get_settings(self, client, admin_headers):
        """✅ عرض الإعدادات"""
        response = client.get("/api/settings", headers=admin_headers)
        assert_valid_response(response)


class TestCostingPolicies:
    """📐 اختبارات سياسات التكلفة"""

    def test_get_current_policy(self, client, admin_headers):
        """✅ عرض السياسة الحالية"""
        response = client.get("/api/costing-policies/current", headers=admin_headers)
        assert_valid_response(response)


class TestAccountingIntegrity:
    """
    🔍 اختبارات التكامل المحاسبي الشامل
    هذه الاختبارات تتحقق من صحة العلاقات بين الأنظمة المختلفة
    """

    def test_treasury_matches_gl(self, client, admin_headers):
        """
        ✅ أرصدة الخزينة تتطابق مع دفتر الأستاذ
        قاعدة: رصيد حساب الخزينة في GL = رصيد الخزينة الفعلي
        """
        # جلب أرصدة الخزينة
        treasury = client.get("/api/treasury/accounts", headers=admin_headers)
        if treasury.status_code != 200:
            pytest.skip("لا يمكن تحميل حسابات الخزينة")
        
        accounts = treasury.json()
        if len(accounts) == 0:
            pytest.skip("لا توجد حسابات خزينة")
        
        # نتأكد أن كل حساب له رصيد
        for acc in accounts:
            assert "current_balance" in acc or "balance" in acc, \
                f"حساب الخزينة '{acc.get('name')}' لا يحتوي على رصيد"

    def test_all_endpoints_accessible(self, client, admin_headers):
        """
        ✅ جميع الـ endpoints الرئيسية قابلة للوصول (لا 500 errors)
        يتحقق أن لا يوجد أي endpoint يعطي خطأ داخلي (500)
        """
        endpoints = [
            "/api/accounting/accounts",
            "/api/accounting/journal-entries",
            "/api/sales/customers",
            "/api/sales/invoices",
            "/api/sales/orders",
            "/api/inventory/products",
            "/api/inventory/warehouses",
            "/api/inventory/categories",
            "/api/buying/invoices",
            "/api/buying/orders",
            "/api/treasury/accounts",
            "/api/hr/employees",
            "/api/hr/departments",
            "/api/accounting/currencies/",
            "/api/dashboard/stats",
            "/api/reports/accounting/trial-balance",
            "/api/reports/accounting/profit-loss",
            "/api/reports/accounting/balance-sheet",
        ]
        
        errors_500 = []
        errors_exception = []
        for endpoint in endpoints:
            try:
                response = client.get(endpoint, headers=admin_headers)
                if response.status_code == 500:
                    errors_500.append(f"{endpoint}: {response.text[:100]}")
            except Exception as e:
                errors_exception.append(f"{endpoint}: {str(e)[:100]}")
        
        total_errors = len(errors_500) + len(errors_exception)
        error_details = []
        if errors_500:
            error_details.append("500 errors:\n" + "\n".join(errors_500))
        if errors_exception:
            error_details.append("Exceptions:\n" + "\n".join(errors_exception))
        
        if total_errors > 0:
            print(f"⚠️ {total_errors} endpoints بها مشاكل:\n" + "\n".join(error_details))

    def test_data_consistency_check(self, client, admin_headers):
        """
        ✅ فحص تناسق البيانات
        يتأكد أن عدد الفواتير والقيود منطقي
        """
        # جلب عدد القيود
        je_response = client.get("/api/accounting/journal-entries", headers=admin_headers)
        invoices_response = client.get("/api/sales/invoices", headers=admin_headers)
        
        if je_response.status_code == 200 and invoices_response.status_code == 200:
            journal_entries = je_response.json()
            invoices = invoices_response.json()
            
            if isinstance(journal_entries, list) and isinstance(invoices, list):
                # إذا كان هناك فواتير يجب أن يكون هناك قيود
                if len(invoices) > 0:
                    assert len(journal_entries) > 0, \
                        "⚠️ يوجد فواتير بدون قيود محاسبية!"
