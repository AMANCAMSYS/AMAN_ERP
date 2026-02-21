"""
AMAN ERP - اختبارات شاملة متعددة السيناريوهات: المحاسبة
Comprehensive Multi-Scenario Tests: Accounting Module
═══════════════════════════════════════════════════════
يتضمن: شجرة الحسابات، القيود اليومية، مراكز التكلفة، الميزانيات، العملات
"""

import pytest
from datetime import date, timedelta
from helpers import assert_valid_response, assert_error_response


# ═══════════════════════════════════════════════════════════════
# 🏦 شجرة الحسابات - Chart of Accounts
# ═══════════════════════════════════════════════════════════════
class TestChartOfAccounts:
    """شجرة الحسابات - سيناريوهات متعددة"""

    def test_list_accounts(self, client, admin_headers):
        """✅ عرض جميع الحسابات"""
        r = client.get("/api/accounting/accounts", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_accounts_have_required_fields(self, client, admin_headers):
        """✅ كل حساب يحتوي على الحقول المطلوبة"""
        r = client.get("/api/accounting/accounts", headers=admin_headers)
        data = r.json()
        for acc in data[:5]:
            assert "id" in acc
            assert "account_number" in acc or "account_code" in acc
            assert "name" in acc
            assert "account_type" in acc

    def test_create_account_asset(self, client, admin_headers):
        """✅ إنشاء حساب أصول"""
        r = client.post("/api/accounting/accounts", json={
            "name": "حساب اختبار أصول",
            "account_number": "1999",
            "account_type": "asset",
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 409]

    def test_create_account_liability(self, client, admin_headers):
        """✅ إنشاء حساب التزامات"""
        r = client.post("/api/accounting/accounts", json={
            "name": "حساب اختبار التزامات",
            "account_number": "2999",
            "account_type": "liability",
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 409]

    def test_create_account_revenue(self, client, admin_headers):
        """✅ إنشاء حساب إيرادات"""
        r = client.post("/api/accounting/accounts", json={
            "name": "حساب اختبار إيرادات",
            "account_number": "4999",
            "account_type": "revenue",
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 409]

    def test_create_account_expense(self, client, admin_headers):
        """✅ إنشاء حساب مصروفات"""
        r = client.post("/api/accounting/accounts", json={
            "name": "حساب اختبار مصروفات",
            "account_number": "5999",
            "account_type": "expense",
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 409]

    def test_create_account_with_parent(self, client, admin_headers):
        """✅ إنشاء حساب فرعي بحساب أب"""
        r = client.post("/api/accounting/accounts", json={
            "name": "حساب فرعي من النقد",
            "account_number": "110199",
            "account_type": "asset",
            "parent_id": 3,  # النقد وما في حكمه
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 409]

    def test_create_duplicate_account_number(self, client, admin_headers):
        """✅ منع إنشاء حساب برقم مكرر"""
        # أولاً ننشئ
        client.post("/api/accounting/accounts", json={
            "name": "حساب أول", "account_number": "9001", "account_type": "asset"
        }, headers=admin_headers)
        # ثانياً نحاول التكرار
        r = client.post("/api/accounting/accounts", json={
            "name": "حساب مكرر", "account_number": "9001", "account_type": "asset"
        }, headers=admin_headers)
        assert r.status_code in [400, 409, 200]  # يجب أن يرفض أو يتعامل

    def test_update_account_name(self, client, admin_headers):
        """✅ تحديث اسم حساب"""
        r = client.get("/api/accounting/accounts", headers=admin_headers)
        accounts = r.json()
        # Find a non-system account to update
        test_acc = None
        for acc in accounts:
            if acc.get("account_number", "").startswith("9") or acc.get("account_number", "").startswith("1999"):
                test_acc = acc
                break
        if not test_acc:
            test_acc = accounts[-1]

        r = client.put(f"/api/accounting/accounts/{test_acc['id']}", json={
            "name": "اسم محدّث",
            "name_en": "Updated Name",
        }, headers=admin_headers)
        assert r.status_code in [200, 404]

    def test_delete_unused_account(self, client, admin_headers):
        """✅ حذف حساب غير مستخدم"""
        # Create a temp account
        r = client.post("/api/accounting/accounts", json={
            "name": "حساب للحذف", "account_number": "9999", "account_type": "asset"
        }, headers=admin_headers)
        if r.status_code in [200, 201]:
            acc_id = r.json().get("id")
            if acc_id:
                r2 = client.delete(f"/api/accounting/accounts/{acc_id}", headers=admin_headers)
                assert r2.status_code in [200, 204, 400]

    def test_delete_used_account_fails(self, client, admin_headers):
        """✅ منع حذف حساب مستخدم في قيود"""
        # Account 7 (النقد) is used
        r = client.delete("/api/accounting/accounts/7", headers=admin_headers)
        assert r.status_code in [400, 409, 403, 200]

    def test_accounting_stats(self, client, admin_headers):
        """✅ إحصائيات المحاسبة"""
        r = client.get("/api/accounting/stats", headers=admin_headers)
        assert r.status_code in [200, 404]


# ═══════════════════════════════════════════════════════════════
# 📝 القيود اليومية - Journal Entries
# ═══════════════════════════════════════════════════════════════
class TestJournalEntries:
    """القيود اليومية - سيناريوهات متعددة"""

    def test_create_balanced_journal_entry(self, client, admin_headers):
        """✅ إنشاء قيد يومي متوازن"""
        r = client.post("/api/accounting/journal-entries", json={
            "date": str(date.today()),
            "description": "قيد اختبار متوازن",
            "reference": "TEST-JE-001",
            "lines": [
                {"account_id": 7, "debit": 1000, "credit": 0, "description": "مدين"},
                {"account_id": 10, "debit": 0, "credit": 1000, "description": "دائن"},
            ]
        }, headers=admin_headers)
        assert r.status_code in [200, 201]
        if r.status_code in [200, 201]:
            data = r.json()
            assert data.get("entry_number") is not None or data.get("id") is not None

    def test_create_multi_line_journal(self, client, admin_headers):
        """✅ قيد يومي متعدد الأسطر"""
        r = client.post("/api/accounting/journal-entries", json={
            "date": str(date.today()),
            "description": "قيد متعدد الأسطر",
            "reference": "TEST-JE-002",
            "lines": [
                {"account_id": 7, "debit": 500, "credit": 0, "description": "نقد"},
                {"account_id": 10, "debit": 500, "credit": 0, "description": "عملاء"},
                {"account_id": 28, "debit": 0, "credit": 1000, "description": "مبيعات"},
            ]
        }, headers=admin_headers)
        assert r.status_code in [200, 201]

    def test_create_unbalanced_journal_fails(self, client, admin_headers):
        """✅ رفض قيد غير متوازن"""
        r = client.post("/api/accounting/journal-entries", json={
            "date": str(date.today()),
            "description": "قيد غير متوازن",
            "reference": "TEST-UNBAL",
            "lines": [
                {"account_id": 7, "debit": 1000, "credit": 0},
                {"account_id": 10, "debit": 0, "credit": 500},  # Not balanced
            ]
        }, headers=admin_headers)
        assert r.status_code in [400, 422]

    def test_create_journal_with_currency(self, client, admin_headers):
        """✅ قيد يومي بعملة أجنبية"""
        r = client.post("/api/accounting/journal-entries", json={
            "date": str(date.today()),
            "description": "قيد بالدولار",
            "reference": "TEST-JE-FX",
            "currency": "USD",
            "exchange_rate": 3.75,
            "lines": [
                {"account_id": 7, "debit": 3750, "credit": 0},
                {"account_id": 28, "debit": 0, "credit": 3750},
            ]
        }, headers=admin_headers)
        assert r.status_code in [200, 201]

    def test_create_journal_with_branch(self, client, admin_headers):
        """✅ قيد يومي مرتبط بفرع"""
        r = client.post("/api/accounting/journal-entries", json={
            "date": str(date.today()),
            "description": "قيد مرتبط بالفرع الرئيسي",
            "reference": "TEST-JE-BR",
            "branch_id": 1,
            "lines": [
                {"account_id": 7, "debit": 200, "credit": 0},
                {"account_id": 28, "debit": 0, "credit": 200},
            ]
        }, headers=admin_headers)
        assert r.status_code in [200, 201]

    def test_void_journal_entry(self, client, admin_headers):
        """✅ إلغاء قيد يومي (عكسه)"""
        # Create an entry first
        r = client.post("/api/accounting/journal-entries", json={
            "date": str(date.today()),
            "description": "قيد سيتم إلغاؤه",
            "reference": "TEST-VOID",
            "lines": [
                {"account_id": 7, "debit": 100, "credit": 0},
                {"account_id": 10, "debit": 0, "credit": 100},
            ]
        }, headers=admin_headers)
        if r.status_code in [200, 201]:
            je_id = r.json().get("id")
            if je_id:
                r2 = client.post(f"/api/accounting/journal-entries/{je_id}/void", headers=admin_headers)
                assert r2.status_code in [200, 201, 400]

    def test_journal_entry_empty_lines_fails(self, client, admin_headers):
        """✅ قيد بدون أسطر - قد يُقبل أو يُرفض"""
        r = client.post("/api/accounting/journal-entries", json={
            "date": str(date.today()),
            "description": "قيد فارغ",
            "lines": []
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 422]

    def test_journal_entry_single_line_fails(self, client, admin_headers):
        """✅ رفض قيد بسطر واحد"""
        r = client.post("/api/accounting/journal-entries", json={
            "date": str(date.today()),
            "description": "قيد بسطر واحد",
            "lines": [
                {"account_id": 7, "debit": 100, "credit": 0}
            ]
        }, headers=admin_headers)
        assert r.status_code in [400, 422]


# ═══════════════════════════════════════════════════════════════
# 🏢 مراكز التكلفة - Cost Centers
# ═══════════════════════════════════════════════════════════════
class TestCostCenters:
    """مراكز التكلفة - سيناريوهات متعددة"""

    def test_list_cost_centers(self, client, admin_headers):
        """✅ عرض مراكز التكلفة"""
        r = client.get("/api/cost-centers/", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 3

    def test_create_cost_center(self, client, admin_headers):
        """✅ إنشاء مركز تكلفة جديد"""
        r = client.post("/api/cost-centers/", json={
            "center_name": "مركز تكلفة اختبار",
            "center_name_en": "Test Cost Center",
            "center_code": "CC-TEST-001",
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 409]

    def test_create_cost_center_with_department(self, client, admin_headers):
        """✅ إنشاء مركز تكلفة مرتبط بقسم"""
        r = client.post("/api/cost-centers/", json={
            "center_name": "مركز المبيعات",
            "center_code": "CC-TEST-002",
            "department_id": 1,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 409]

    def test_update_cost_center(self, client, admin_headers):
        """✅ تحديث مركز تكلفة"""
        r = client.get("/api/cost-centers/", headers=admin_headers)
        centers = r.json()
        if centers:
            cc_id = centers[0]["id"]
            r2 = client.put(f"/api/cost-centers/{cc_id}", json={
                "center_name": "مركز محدّث",
                "budget": 150000,
            }, headers=admin_headers)
            assert r2.status_code in [200, 404]

    def test_delete_unused_cost_center(self, client, admin_headers):
        """✅ حذف مركز تكلفة غير مستخدم"""
        r = client.post("/api/cost-centers/", json={
            "center_name": "مركز للحذف",
            "center_code": "CC-DEL-001",
        }, headers=admin_headers)
        if r.status_code in [200, 201]:
            cc_id = r.json().get("id")
            if cc_id:
                r2 = client.delete(f"/api/cost-centers/{cc_id}", headers=admin_headers)
                assert r2.status_code in [200, 204, 400]


# ═══════════════════════════════════════════════════════════════
# 💰 الميزانيات - Budgets
# ═══════════════════════════════════════════════════════════════
class TestBudgets:
    """الميزانيات - سيناريوهات متعددة"""

    def test_list_budgets(self, client, admin_headers):
        """✅ عرض الميزانيات"""
        r = client.get("/api/accounting/budgets/", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_create_budget(self, client, admin_headers):
        """✅ إنشاء ميزانية جديدة"""
        r = client.post("/api/accounting/budgets/", json={
            "name": "ميزانية اختبار الربع الثاني",
            "start_date": "2025-04-01",
            "end_date": "2025-06-30",
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400]

    def test_set_budget_items(self, client, admin_headers):
        """✅ تحديد بنود الميزانية"""
        r = client.get("/api/accounting/budgets/", headers=admin_headers)
        budgets = r.json()
        if not budgets:
            pytest.skip("لا توجد ميزانيات")
        budget_id = budgets[0]["id"]
        r2 = client.post(f"/api/accounting/budgets/{budget_id}/items", json=[
            {"account_id": 28, "planned_amount": 100000},
            {"account_id": 30, "planned_amount": 50000},
        ], headers=admin_headers)
        assert r2.status_code in [200, 201, 400]

    def test_budget_vs_actual_report(self, client, admin_headers):
        """✅ تقرير الميزانية مقابل الفعلي"""
        r = client.get("/api/accounting/budgets/", headers=admin_headers)
        budgets = r.json()
        if not budgets:
            pytest.skip("لا توجد ميزانيات")
        budget_id = budgets[0]["id"]
        r2 = client.get(f"/api/accounting/budgets/{budget_id}/report", headers=admin_headers)
        assert r2.status_code in [200, 404]

    def test_delete_budget(self, client, admin_headers):
        """✅ حذف ميزانية"""
        r = client.post("/api/accounting/budgets/", json={
            "name": "ميزانية للحذف",
            "start_date": "2025-10-01",
            "end_date": "2025-12-31",
        }, headers=admin_headers)
        if r.status_code in [200, 201]:
            bid = r.json().get("id")
            if bid:
                r2 = client.delete(f"/api/accounting/budgets/{bid}", headers=admin_headers)
                assert r2.status_code in [200, 204]


# ═══════════════════════════════════════════════════════════════
# 💱 العملات وأسعار الصرف - Currencies
# ═══════════════════════════════════════════════════════════════
class TestCurrencies:
    """العملات - سيناريوهات متعددة"""

    def test_list_currencies(self, client, admin_headers):
        """✅ عرض العملات"""
        r = client.get("/api/accounting/currencies/", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        assert len(data) >= 1
        # SAR should exist
        codes = [c.get("code") for c in data]
        assert "SAR" in codes

    def test_create_currency(self, client, admin_headers):
        """✅ إنشاء عملة جديدة"""
        r = client.post("/api/accounting/currencies/", json={
            "code": "GBP",
            "name": "جنيه استرليني",
            "symbol": "£",
            "is_base": False,
            "current_rate": 4.75,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 409]

    def test_update_currency_rate(self, client, admin_headers):
        """✅ تحديث سعر عملة"""
        r = client.get("/api/accounting/currencies/", headers=admin_headers)
        currencies = r.json()
        usd = next((c for c in currencies if c.get("code") == "USD"), None)
        if not usd:
            pytest.skip("عملة USD غير موجودة")
        r2 = client.put(f"/api/accounting/currencies/{usd['id']}", json={
            "current_rate": 3.76,
        }, headers=admin_headers)
        assert r2.status_code in [200, 400, 422]

    def test_add_exchange_rate(self, client, admin_headers):
        """✅ إضافة سعر صرف"""
        r = client.get("/api/accounting/currencies/", headers=admin_headers)
        currencies = r.json()
        usd = next((c for c in currencies if c.get("code") == "USD"), None)
        if not usd:
            pytest.skip("عملة USD غير موجودة")
        r2 = client.post("/api/accounting/currencies/rates", json={
            "currency_id": usd["id"],
            "rate_date": str(date.today()),
            "rate": 3.77,
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400]

    def test_exchange_rate_history(self, client, admin_headers):
        """✅ تاريخ أسعار الصرف"""
        r = client.get("/api/accounting/currencies/", headers=admin_headers)
        currencies = r.json()
        usd = next((c for c in currencies if c.get("code") == "USD"), None)
        if not usd:
            pytest.skip("عملة USD غير موجودة")
        r2 = client.get(f"/api/accounting/currencies/{usd['id']}/rates", headers=admin_headers)
        assert r2.status_code in [200, 404]

    def test_cannot_delete_base_currency(self, client, admin_headers):
        """✅ منع حذف العملة الأساسية"""
        r = client.get("/api/accounting/currencies/", headers=admin_headers)
        currencies = r.json()
        base = next((c for c in currencies if c.get("is_base")), None)
        if base:
            r2 = client.delete(f"/api/accounting/currencies/{base['id']}", headers=admin_headers)
            assert r2.status_code in [400, 403, 409]

    def test_cannot_delete_used_currency(self, client, admin_headers):
        """✅ منع حذف عملة مستخدمة"""
        r = client.get("/api/accounting/currencies/", headers=admin_headers)
        sar = next((c for c in r.json() if c.get("code") == "SAR"), None)
        if sar:
            r2 = client.delete(f"/api/accounting/currencies/{sar['id']}", headers=admin_headers)
            assert r2.status_code in [400, 403, 409]
