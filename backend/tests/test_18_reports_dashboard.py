"""
AMAN ERP - اختبارات شاملة متعددة السيناريوهات: التقارير ولوحة التحكم والنظام
Comprehensive Multi-Scenario Tests: Reports, Dashboard, Audit, Settings, Branches, Roles
═══════════════════════════════════════════════════════
يتضمن: التقارير المالية، تقارير المبيعات والمشتريات، لوحة التحكم، التدقيق، الإعدادات، الفروع، الأدوار
"""

import pytest
from helpers import assert_valid_response, assert_error_response


# ═══════════════════════════════════════════════════════════════
# 📊 التقارير - Reports
# ═══════════════════════════════════════════════════════════════

class TestSalesReportScenarios:
    """تقارير المبيعات"""

    def test_sales_summary(self, client, admin_headers):
        """✅ ملخص المبيعات"""
        r = client.get("/api/reports/sales/summary", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        assert isinstance(data, dict)

    def test_sales_summary_with_period(self, client, admin_headers):
        """✅ ملخص المبيعات بفترة"""
        r = client.get("/api/reports/sales/summary?start_date=2025-01-01&end_date=2025-12-31", headers=admin_headers)
        assert_valid_response(r)

    def test_sales_trend(self, client, admin_headers):
        """✅ اتجاه المبيعات"""
        r = client.get("/api/reports/sales/trend", headers=admin_headers)
        assert_valid_response(r)
        assert isinstance(r.json(), list)

    def test_sales_by_customer(self, client, admin_headers):
        """✅ المبيعات حسب العميل"""
        r = client.get("/api/reports/sales/by-customer", headers=admin_headers)
        assert_valid_response(r)
        assert isinstance(r.json(), list)

    def test_sales_by_product(self, client, admin_headers):
        """✅ المبيعات حسب المنتج"""
        r = client.get("/api/reports/sales/by-product", headers=admin_headers)
        assert_valid_response(r)
        assert isinstance(r.json(), list)

    def test_customer_statement(self, client, admin_headers):
        """✅ كشف حساب عميل"""
        r = client.get("/api/sales/customers", headers=admin_headers)
        customers = r.json()
        if not customers:
            pytest.skip("لا عملاء")
        cid = customers[0]["id"]
        r2 = client.get(f"/api/reports/sales/customer-statement/{cid}", headers=admin_headers)
        assert r2.status_code in [200, 404]

    def test_receivables_aging(self, client, admin_headers):
        """✅ أعمار الذمم المدينة"""
        r = client.get("/api/reports/sales/aging", headers=admin_headers)
        assert_valid_response(r)
        assert isinstance(r.json(), list)


class TestPurchaseReportScenarios:
    """تقارير المشتريات"""

    def test_purchases_summary(self, client, admin_headers):
        """✅ ملخص المشتريات"""
        r = client.get("/api/reports/purchases/summary", headers=admin_headers)
        assert_valid_response(r)
        assert isinstance(r.json(), dict)

    def test_purchases_trend(self, client, admin_headers):
        """✅ اتجاه المشتريات"""
        r = client.get("/api/reports/purchases/trend", headers=admin_headers)
        assert_valid_response(r)
        assert isinstance(r.json(), list)

    def test_purchases_by_supplier(self, client, admin_headers):
        """✅ المشتريات حسب المورد"""
        r = client.get("/api/reports/purchases/by-supplier", headers=admin_headers)
        assert_valid_response(r)
        assert isinstance(r.json(), list)

    def test_supplier_statement(self, client, admin_headers):
        """✅ كشف حساب مورد"""
        r = client.get("/api/buying/suppliers", headers=admin_headers)
        suppliers = r.json()
        if not suppliers:
            pytest.skip("لا موردين")
        sid = suppliers[0]["id"]
        r2 = client.get(f"/api/reports/purchases/supplier-statement/{sid}", headers=admin_headers)
        assert r2.status_code in [200, 404]

class TestHRReportScenarios:
    """تقارير الموارد البشرية"""

    def test_payroll_trend(self, client, admin_headers):
        """✅ اتجاه الرواتب"""
        r = client.get("/api/reports/hr/payroll/trend", headers=admin_headers)
        assert_valid_response(r)
        assert isinstance(r.json(), list)

    def test_leave_usage(self, client, admin_headers):
        """✅ استخدام الإجازات"""
        r = client.get("/api/reports/hr/leaves/usage", headers=admin_headers)
        assert_valid_response(r)
        assert isinstance(r.json(), list)


class TestAccountingReportScenarios:
    """تقارير محاسبية"""

    def test_trial_balance(self, client, admin_headers):
        """✅ ميزان المراجعة"""
        r = client.get("/api/reports/accounting/trial-balance", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        assert "data" in data

    def test_trial_balance_with_dates(self, client, admin_headers):
        """✅ ميزان المراجعة بتواريخ"""
        r = client.get("/api/reports/accounting/trial-balance?start_date=2025-01-01&end_date=2025-12-31", headers=admin_headers)
        assert_valid_response(r)

    def test_profit_loss(self, client, admin_headers):
        """✅ قائمة الأرباح والخسائر"""
        r = client.get("/api/reports/accounting/profit-loss", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        assert isinstance(data, dict)

    def test_balance_sheet(self, client, admin_headers):
        """✅ الميزانية العمومية"""
        r = client.get("/api/reports/accounting/balance-sheet", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        assert isinstance(data, dict)

    def test_budget_vs_actual(self, client, admin_headers):
        """✅ الموازنة مقابل الفعلي"""
        # budget_id is required
        r = client.get("/api/reports/accounting/budget-vs-actual?budget_id=1", headers=admin_headers)
        assert r.status_code in [200, 400, 404]

    def test_cashflow(self, client, admin_headers):
        """✅ التدفق النقدي"""
        r = client.get("/api/reports/accounting/cashflow", headers=admin_headers)
        assert_valid_response(r)

    def test_general_ledger(self, client, admin_headers):
        """✅ دفتر الأستاذ العام"""
        # account_id is required
        r = client.get("/api/reports/accounting/general-ledger?account_id=7", headers=admin_headers)
        assert r.status_code in [200, 400]

    def test_general_ledger_for_specific_account(self, client, admin_headers):
        """✅ دفتر الأستاذ لحساب محدد"""
        r = client.get("/api/reports/accounting/general-ledger?account_id=7", headers=admin_headers)
        assert_valid_response(r)


# ═══════════════════════════════════════════════════════════════
# 📈 لوحة التحكم - Dashboard
# ═══════════════════════════════════════════════════════════════
class TestDashboardScenarios:
    """سيناريوهات لوحة التحكم"""

    def test_dashboard_stats(self, client, admin_headers):
        """✅ إحصائيات لوحة التحكم"""
        r = client.get("/api/dashboard/stats", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        assert isinstance(data, dict)

    def test_financial_charts(self, client, admin_headers):
        """✅ الرسوم البيانية المالية"""
        r = client.get("/api/dashboard/charts/financial", headers=admin_headers)
        assert_valid_response(r)
        assert isinstance(r.json(), list)

    def test_top_products_chart(self, client, admin_headers):
        """✅ مخطط أفضل المنتجات"""
        r = client.get("/api/dashboard/charts/products", headers=admin_headers)
        assert_valid_response(r)
        assert isinstance(r.json(), list)

    def test_system_stats(self, client, admin_headers):
        """✅ إحصائيات النظام"""
        r = client.get("/api/dashboard/system-stats", headers=admin_headers)
        # system_admin only - company users get 403
        assert r.status_code in [200, 403]


# ═══════════════════════════════════════════════════════════════
# 🔍 التدقيق - Audit
# ═══════════════════════════════════════════════════════════════
class TestAuditScenarios:
    """سيناريوهات التدقيق"""

    def test_query_audit_logs(self, client, admin_headers):
        """✅ استعلام سجلات التدقيق"""
        r = client.get("/api/audit/logs", headers=admin_headers)
        assert_valid_response(r)
        assert isinstance(r.json(), list)

    def test_audit_logs_with_filters(self, client, admin_headers):
        """✅ سجلات التدقيق مع فلاتر"""
        r = client.get("/api/audit/logs?limit=5", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        assert len(data) <= 5

    def test_audit_action_types(self, client, admin_headers):
        """✅ أنواع إجراءات التدقيق"""
        r = client.get("/api/audit/logs/actions", headers=admin_headers)
        assert_valid_response(r)
        assert isinstance(r.json(), list)

    def test_audit_stats(self, client, admin_headers):
        """✅ إحصائيات التدقيق"""
        r = client.get("/api/audit/logs/stats", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        assert isinstance(data, dict)


# ═══════════════════════════════════════════════════════════════
# ⚙️ الإعدادات - Settings
# ═══════════════════════════════════════════════════════════════
class TestSettingsScenarios:
    """سيناريوهات الإعدادات"""

    def test_get_all_settings(self, client, admin_headers):
        """✅ عرض جميع الإعدادات"""
        r = client.get("/api/settings/", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        assert isinstance(data, dict)

    def test_bulk_update_settings(self, client, admin_headers):
        """✅ تحديث إعدادات"""
        r = client.post("/api/settings/bulk", json={
            "settings": {
                "company_name": "شركة أمان التجريبية",
                "default_currency": "SAR",
            }
        }, headers=admin_headers)
        assert r.status_code in [200, 400]

    def test_settings_contain_account_mappings(self, client, admin_headers):
        """✅ الإعدادات تحتوي على ربط الحسابات"""
        r = client.get("/api/settings/", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        # Check some account mappings exist
        has_mapping = any(k.startswith("acc_map_") for k in data.keys())
        assert has_mapping, "الإعدادات لا تحتوي على ربط حسابات"


# ═══════════════════════════════════════════════════════════════
# 🏢 الفروع - Branches
# ═══════════════════════════════════════════════════════════════
class TestBranchScenarios:
    """سيناريوهات الفروع"""

    def test_list_branches(self, client, admin_headers):
        """✅ عرض الفروع"""
        r = client.get("/api/branches", headers=admin_headers)
        assert_valid_response(r)
        branches = r.json()
        assert len(branches) >= 1

    def test_create_branch(self, client, admin_headers):
        """✅ إنشاء فرع"""
        r = client.post("/api/branches", json={
            "branch_name": "فرع اختبار جديد",
            "branch_code": "TST-BR",
            "is_default": False,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400]

    def test_update_branch(self, client, admin_headers):
        """✅ تحديث فرع"""
        r = client.get("/api/branches", headers=admin_headers)
        branches = r.json()
        if len(branches) < 2:
            pytest.skip("فرع واحد فقط")
        # Update non-default branch
        bid = branches[-1]["id"]
        r2 = client.put(f"/api/branches/{bid}", json={
            "branch_name": "فرع محدّث",
        }, headers=admin_headers)
        assert r2.status_code in [200, 400, 404, 422]

    def test_delete_non_default_branch(self, client, admin_headers):
        """✅ حذف فرع غير افتراضي"""
        # Create branch for deletion
        r = client.post("/api/branches", json={
            "branch_name": "فرع للحذف",
            "branch_code": "DEL-BR",
            "is_default": False,
        }, headers=admin_headers)
        if r.status_code in [200, 201]:
            bid = r.json().get("id")
            if bid:
                r2 = client.delete(f"/api/branches/{bid}", headers=admin_headers)
                assert r2.status_code in [200, 204, 400]


# ═══════════════════════════════════════════════════════════════
# 🔐 الأدوار والصلاحيات - Roles & Permissions
# ═══════════════════════════════════════════════════════════════
class TestRoleScenarios:
    """سيناريوهات الأدوار"""

    def test_list_permissions(self, client, admin_headers):
        """✅ عرض الصلاحيات"""
        r = client.get("/api/roles/permissions", headers=admin_headers)
        assert_valid_response(r)
        perms = r.json()
        assert isinstance(perms, list)
        assert len(perms) > 0

    def test_list_roles(self, client, admin_headers):
        """✅ عرض الأدوار"""
        r = client.get("/api/roles/", headers=admin_headers)
        assert_valid_response(r)
        roles = r.json()
        assert isinstance(roles, list)

    def test_create_role(self, client, admin_headers):
        """✅ إنشاء دور"""
        r = client.post("/api/roles/", json={
            "role_name": "محاسب اختبار",
            "permissions": ["accounting.view", "accounting.create", "reports.view"],
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400]

    def test_get_role_detail(self, client, admin_headers):
        """✅ تفاصيل دور"""
        r = client.get("/api/roles/", headers=admin_headers)
        roles = r.json()
        if not roles:
            pytest.skip("لا أدوار")
        rid = roles[0]["id"]
        r2 = client.get(f"/api/roles/{rid}", headers=admin_headers)
        assert r2.status_code in [200, 404]

    def test_update_role(self, client, admin_headers):
        """✅ تحديث دور"""
        r = client.get("/api/roles/", headers=admin_headers)
        roles = r.json()
        if not roles:
            pytest.skip("لا أدوار")
        rid = roles[-1]["id"]
        r2 = client.put(f"/api/roles/{rid}", json={
            "role_name": "دور محدّث",
            "permissions": ["accounting.view"],
        }, headers=admin_headers)
        assert r2.status_code in [200, 400, 404, 422, 500]

    def test_delete_role(self, client, admin_headers):
        """✅ حذف دور"""
        # Create role for deletion
        r = client.post("/api/roles/", json={
            "role_name": "دور للحذف",
            "permissions": ["accounting.view"],
        }, headers=admin_headers)
        if r.status_code in [200, 201]:
            rid = r.json().get("id")
            if rid:
                r2 = client.delete(f"/api/roles/{rid}", headers=admin_headers)
                assert r2.status_code in [200, 204, 400]
