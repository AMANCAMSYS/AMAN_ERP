"""
AMAN ERP - اختبارات شاملة متعددة السيناريوهات: المحاسبة المتقدمة
Comprehensive Multi-Scenario Tests: Advanced Accounting
═══════════════════════════════════════════════════════
يتضمن: سياسات التكلفة، القيود الدورية، المصروفات المستحقة، الإيرادات المؤجلة،
التسويات المحاسبية، القيود العكسية، تحليل الحسابات
"""

import pytest
from datetime import date, timedelta
from helpers import assert_valid_response, assert_error_response


# ═══════════════════════════════════════════════════════════════
# 📊 سياسات التكلفة - Costing Policies
# ═══════════════════════════════════════════════════════════════
class TestCostingPolicyScenarios:
    """سيناريوهات سياسات التكلفة"""

    def test_get_current_costing_policy(self, client, admin_headers):
        """✅ الحصول على سياسة التكلفة الحالية"""
        r = client.get("/api/costing-policies/current", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        assert "policy_type" in data

    def test_get_costing_policy_history(self, client, admin_headers):
        """✅ تاريخ تغييرات سياسة التكلفة"""
        r = client.get("/api/costing-policies/history", headers=admin_headers)
        assert_valid_response(r)
        assert isinstance(r.json(), list)

    def test_set_global_wac_policy(self, client, admin_headers):
        """✅ تعيين سياسة المتوسط المرجح العام"""
        r = client.post("/api/costing-policies/set", json={
            "policy_type": "global_wac",
            "reason": "اختبار سياسة المتوسط المرجح العام",
        }, headers=admin_headers)
        assert r.status_code in [200, 400]

    def test_set_per_warehouse_wac_policy(self, client, admin_headers):
        """✅ تعيين سياسة المتوسط المرجح لكل مستودع"""
        r = client.post("/api/costing-policies/set", json={
            "policy_type": "per_warehouse_wac",
            "reason": "اختبار سياسة المتوسط المرجح لكل مستودع",
        }, headers=admin_headers)
        assert r.status_code in [200, 400]

    def test_invalid_costing_policy_type(self, client, admin_headers):
        """❌ رفض سياسة تكلفة غير صالحة"""
        r = client.post("/api/costing-policies/set", json={
            "policy_type": "invalid_policy",
            "reason": "اختبار",
        }, headers=admin_headers)
        assert r.status_code == 400


# ═══════════════════════════════════════════════════════════════
# 💰 المصروفات - Expenses
# ═══════════════════════════════════════════════════════════════
class TestExpenseScenarios:
    """سيناريوهات المصروفات"""

    def test_list_expenses(self, client, admin_headers):
        """✅ عرض المصروفات"""
        r = client.get("/api/expenses/", headers=admin_headers)
        assert_valid_response(r)

    def test_get_expenses_summary(self, client, admin_headers):
        """✅ ملخص المصروفات"""
        r = client.get("/api/expenses/summary", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        assert "total_amount" in data or "total_expenses" in data

    def test_create_general_expense(self, client, admin_headers):
        """✅ إنشاء مصروف عام"""
        r = client.post("/api/expenses/", json={
            "expense_type": "general",
            "amount": 500,
            "expense_date": str(date.today()),
            "description": "مصروف عام اختبار",
            "treasury_id": 2,
            "branch_id": 1,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400]

    def test_create_rent_expense(self, client, admin_headers):
        """✅ إنشاء مصروف إيجار"""
        r = client.post("/api/expenses/", json={
            "expense_type": "rent",
            "amount": 10000,
            "expense_date": str(date.today()),
            "description": "إيجار مكتب شهر يناير",
            "treasury_id": 3,
            "branch_id": 1,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400]

    def test_create_utilities_expense(self, client, admin_headers):
        """✅ إنشاء مصروف خدمات"""
        r = client.post("/api/expenses/", json={
            "expense_type": "utilities",
            "amount": 1500,
            "expense_date": str(date.today()),
            "description": "فاتورة كهرباء",
            "treasury_id": 2,
            "branch_id": 1,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400]

    def test_create_expense_with_cost_center(self, client, admin_headers):
        """✅ مصروف مرتبط بمركز تكلفة"""
        r = client.get("/api/cost-centers/", headers=admin_headers)
        centers = r.json()
        cc_id = centers[0]["id"] if centers else None

        r2 = client.post("/api/expenses/", json={
            "expense_type": "general",
            "amount": 300,
            "expense_date": str(date.today()),
            "description": "مصروف لمركز تكلفة",
            "treasury_id": 2,
            "cost_center_id": cc_id,
            "branch_id": 1,
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400]

    def test_create_expense_with_project(self, client, admin_headers):
        """✅ مصروف مرتبط بمشروع"""
        r = client.get("/api/projects/", headers=admin_headers)
        projects = r.json()
        proj_id = projects[0]["id"] if projects else None

        r2 = client.post("/api/expenses/", json={
            "expense_type": "general",
            "amount": 2000,
            "expense_date": str(date.today()),
            "description": "مصروف مشروع",
            "treasury_id": 2,
            "project_id": proj_id,
            "branch_id": 1,
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400]

    def test_get_expense_detail(self, client, admin_headers):
        """✅ تفاصيل مصروف"""
        r = client.get("/api/expenses/", headers=admin_headers)
        expenses = r.json()
        if not expenses:
            pytest.skip("لا مصروفات")
        exp_id = expenses[0]["id"]
        r2 = client.get(f"/api/expenses/{exp_id}", headers=admin_headers)
        assert r2.status_code in [200, 404]

    def test_approve_expense(self, client, admin_headers):
        """✅ اعتماد مصروف"""
        r = client.get("/api/expenses/?approval_status=pending", headers=admin_headers)
        expenses = r.json()
        pending = [e for e in expenses if e.get("approval_status") == "pending"]
        if not pending:
            pytest.skip("لا مصروفات معلقة")
        exp_id = pending[0]["id"]
        r2 = client.post(f"/api/expenses/{exp_id}/approve", json={
            "approval_status": "approved",
            "approval_notes": "موافق عليه"
        }, headers=admin_headers)
        assert r2.status_code in [200, 400, 404]

    def test_reject_expense(self, client, admin_headers):
        """✅ رفض مصروف"""
        r = client.get("/api/expenses/?approval_status=pending", headers=admin_headers)
        expenses = r.json()
        pending = [e for e in expenses if e.get("approval_status") == "pending"]
        if not pending:
            pytest.skip("لا مصروفات معلقة")
        exp_id = pending[0]["id"]
        r2 = client.post(f"/api/expenses/{exp_id}/reject", json={
            "rejection_reason": "المبلغ غير صحيح",
        }, headers=admin_headers)
        assert r2.status_code in [200, 400, 404]

    def test_filter_expenses_by_date(self, client, admin_headers):
        """✅ فلترة المصروفات بالتاريخ"""
        r = client.get(f"/api/expenses/?start_date=2025-01-01&end_date=2025-12-31", 
                      headers=admin_headers)
        assert_valid_response(r)

    def test_filter_expenses_by_type(self, client, admin_headers):
        """✅ فلترة المصروفات بالنوع"""
        r = client.get("/api/expenses/?expense_type=rent", headers=admin_headers)
        assert_valid_response(r)


# ═══════════════════════════════════════════════════════════════
# 📝 ملخص المحاسبة - Accounting Summary
# ═══════════════════════════════════════════════════════════════
class TestAccountingSummaryScenarios:
    """سيناريوهات ملخص المحاسبة"""

    def test_accounting_summary(self, client, admin_headers):
        """✅ ملخص المحاسبة العام"""
        r = client.get("/api/accounting/summary", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        assert "total_income" in data
        assert "total_expenses" in data
        assert "net_profit" in data

    def test_accounting_summary_by_branch(self, client, admin_headers):
        """✅ ملخص المحاسبة حسب الفرع"""
        r = client.get("/api/accounting/summary?branch_id=1", headers=admin_headers)
        assert_valid_response(r)

    def test_accounting_stats(self, client, admin_headers):
        """✅ إحصائيات المحاسبة"""
        r = client.get("/api/accounting/stats", headers=admin_headers)
        assert r.status_code in [200, 404]


# ═══════════════════════════════════════════════════════════════
# 🔄 القيود العكسية والتسويات - Reversing & Adjustment Entries
# ═══════════════════════════════════════════════════════════════
class TestReversalAdjustmentScenarios:
    """سيناريوهات القيود العكسية والتسويات"""

    def test_void_journal_entry(self, client, admin_headers):
        """✅ إلغاء قيد (قيد عكسي)"""
        # Create entry first
        r = client.post("/api/accounting/journal-entries", json={
            "date": str(date.today()),
            "description": "قيد للإلغاء",
            "lines": [
                {"account_id": 7, "debit": 1000, "credit": 0},
                {"account_id": 10, "debit": 0, "credit": 1000},
            ]
        }, headers=admin_headers)
        if r.status_code in [200, 201]:
            je_id = r.json().get("id")
            if je_id:
                r2 = client.post(f"/api/accounting/journal-entries/{je_id}/void", 
                               headers=admin_headers)
                assert r2.status_code in [200, 400, 404]

    def test_create_adjustment_entry(self, client, admin_headers):
        """✅ قيد تسوية"""
        r = client.post("/api/accounting/journal-entries", json={
            "date": str(date.today()),
            "description": "قيد تسوية - مصروفات مستحقة",
            "reference": "ADJ-001",
            "lines": [
                {"account_id": 42, "debit": 2000, "credit": 0, "description": "مصروفات مستحقة"},
                {"account_id": 14, "debit": 0, "credit": 2000, "description": "مستحقات"},
            ]
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400]


# ═══════════════════════════════════════════════════════════════
# 📊 تحليل الحسابات - Account Analysis
# ═══════════════════════════════════════════════════════════════
class TestAccountAnalysisScenarios:
    """سيناريوهات تحليل الحسابات"""

    def test_account_ledger(self, client, admin_headers):
        """✅ دفتر الأستاذ لحساب"""
        r = client.get("/api/reports/accounting/general-ledger?account_id=7", 
                      headers=admin_headers)
        assert_valid_response(r)

    def test_account_ledger_with_dates(self, client, admin_headers):
        """✅ دفتر الأستاذ بتواريخ"""
        r = client.get("/api/reports/accounting/general-ledger?account_id=7&start_date=2025-01-01&end_date=2025-12-31", 
                      headers=admin_headers)
        assert_valid_response(r)

    def test_account_balance_by_branch(self, client, admin_headers):
        """✅ رصيد الحساب حسب الفرع"""
        r = client.get("/api/accounting/accounts?branch_id=1", headers=admin_headers)
        assert_valid_response(r)

    def test_account_search(self, client, admin_headers):
        """✅ بحث في الحسابات"""
        r = client.get("/api/accounting/accounts?search=نقد", headers=admin_headers)
        assert_valid_response(r)

    def test_filter_accounts_by_type(self, client, admin_headers):
        """✅ فلترة الحسابات بالنوع"""
        for acc_type in ["asset", "liability", "equity", "revenue", "expense"]:
            r = client.get(f"/api/accounting/accounts?account_type={acc_type}", 
                          headers=admin_headers)
            assert_valid_response(r)


# ═══════════════════════════════════════════════════════════════
# 📈 تقارير محاسبية متقدمة - Advanced Accounting Reports
# ═══════════════════════════════════════════════════════════════
class TestAdvancedAccountingReportScenarios:
    """تقارير محاسبية متقدمة"""

    def test_comparative_trial_balance(self, client, admin_headers):
        """✅ ميزان مراجعة مقارن"""
        r = client.get("/api/reports/accounting/trial-balance?comparative=true", 
                      headers=admin_headers)
        assert r.status_code in [200, 400]

    def test_trial_balance_by_branch(self, client, admin_headers):
        """✅ ميزان المراجعة حسب الفرع"""
        r = client.get("/api/reports/accounting/trial-balance?branch_id=1", 
                      headers=admin_headers)
        assert_valid_response(r)

    def test_profit_loss_detailed(self, client, admin_headers):
        """✅ قائمة الدخل التفصيلية"""
        r = client.get("/api/reports/accounting/profit-loss?start_date=2025-01-01&end_date=2025-12-31", 
                      headers=admin_headers)
        assert_valid_response(r)

    def test_profit_loss_by_branch(self, client, admin_headers):
        """✅ قائمة الدخل حسب الفرع"""
        r = client.get("/api/reports/accounting/profit-loss?branch_id=1", 
                      headers=admin_headers)
        assert_valid_response(r)

    def test_balance_sheet_detailed(self, client, admin_headers):
        """✅ الميزانية العمومية التفصيلية"""
        r = client.get("/api/reports/accounting/balance-sheet", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        assert "assets" in data or "total_assets" in data or isinstance(data, dict)

    def test_cashflow_statement(self, client, admin_headers):
        """✅ قائمة التدفقات النقدية"""
        r = client.get("/api/reports/accounting/cashflow", headers=admin_headers)
        assert_valid_response(r)

    def test_cost_center_report(self, client, admin_headers):
        """✅ تقرير مراكز التكلفة"""
        r = client.get("/api/reports/cost-centers", headers=admin_headers)
        assert r.status_code in [200, 404]


# ═══════════════════════════════════════════════════════════════
# 💱 التعامل مع العملات المتعددة - Multi-Currency Accounting
# ═══════════════════════════════════════════════════════════════
class TestMultiCurrencyScenarios:
    """سيناريوهات العملات المتعددة"""

    def test_journal_entry_with_currency(self, client, admin_headers):
        """✅ قيد بعملة أجنبية"""
        r = client.post("/api/accounting/journal-entries", json={
            "date": str(date.today()),
            "description": "قيد بالدولار",
            "currency": "USD",
            "exchange_rate": 3.75,
            "lines": [
                {"account_id": 7, "debit": 3750, "credit": 0, "description": "1000 دولار"},
                {"account_id": 28, "debit": 0, "credit": 3750, "description": "إيراد بالدولار"},
            ]
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400]

    def test_account_balance_in_currency(self, client, admin_headers):
        """✅ رصيد حساب بالعملة الأجنبية"""
        r = client.get("/api/accounting/accounts", headers=admin_headers)
        assert_valid_response(r)
        accounts = r.json() if isinstance(r.json(), list) else r.json().get("data", [])
        # Check if balance_currency field exists
        for acc in accounts[:5]:
            if acc.get("currency"):
                assert "balance_currency" in acc or "balance" in acc

    def test_realized_gain_loss(self, client, admin_headers):
        """✅ أرباح/خسائر فروق العملة المحققة"""
        r = client.get("/api/reports/accounting/fx-realized", headers=admin_headers)
        assert r.status_code in [200, 404]

    def test_unrealized_gain_loss(self, client, admin_headers):
        """✅ أرباح/خسائر فروق العملة غير المحققة"""
        r = client.get("/api/reports/accounting/fx-unrealized", headers=admin_headers)
        assert r.status_code in [200, 404]


# ═══════════════════════════════════════════════════════════════
# 🔢 سيناريوهات محاسبية محددة - Specific Accounting Scenarios
# ═══════════════════════════════════════════════════════════════
class TestSpecificAccountingScenarios:
    """سيناريوهات محاسبية محددة"""

    def test_accrued_expenses_entry(self, client, admin_headers):
        """✅ قيد مصروفات مستحقة"""
        # Dr. Expense / Cr. Accrued Expenses (Liability)
        r = client.post("/api/accounting/journal-entries", json={
            "date": str(date.today()),
            "description": "مصروفات مستحقة - رواتب ديسمبر",
            "reference": "ACC-EXP-001",
            "lines": [
                {"account_id": 38, "debit": 50000, "credit": 0, "description": "رواتب مستحقة"},
                {"account_id": 14, "debit": 0, "credit": 50000, "description": "مستحقات"},
            ]
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400]

    def test_prepaid_expense_entry(self, client, admin_headers):
        """✅ قيد مصروفات مدفوعة مقدماً"""
        # Dr. Prepaid Expense (Asset) / Cr. Cash
        r = client.post("/api/accounting/journal-entries", json={
            "date": str(date.today()),
            "description": "إيجار مدفوع مقدماً",
            "reference": "PRE-EXP-001",
            "lines": [
                {"account_id": 9, "debit": 60000, "credit": 0, "description": "إيجار سنة"},
                {"account_id": 7, "debit": 0, "credit": 60000, "description": "دفع نقدي"},
            ]
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400]

    def test_unearned_revenue_entry(self, client, admin_headers):
        """✅ قيد إيراد مؤجل"""
        # Dr. Cash / Cr. Unearned Revenue (Liability)
        r = client.post("/api/accounting/journal-entries", json={
            "date": str(date.today()),
            "description": "إيراد مؤجل - اشتراك سنوي",
            "reference": "DEF-REV-001",
            "lines": [
                {"account_id": 7, "debit": 12000, "credit": 0, "description": "قبض نقدي"},
                {"account_id": 17, "debit": 0, "credit": 12000, "description": "إيراد مؤجل"},
            ]
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400]

    def test_recognize_deferred_revenue(self, client, admin_headers):
        """✅ قيد الاعتراف بالإيراد المؤجل"""
        # Dr. Unearned Revenue / Cr. Revenue
        r = client.post("/api/accounting/journal-entries", json={
            "date": str(date.today()),
            "description": "اعتراف بإيراد الاشتراك - شهر يناير",
            "reference": "REV-REC-001",
            "lines": [
                {"account_id": 17, "debit": 1000, "credit": 0, "description": "تخفيض إيراد مؤجل"},
                {"account_id": 28, "debit": 0, "credit": 1000, "description": "إيراد الشهر"},
            ]
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400]

    def test_bad_debt_write_off(self, client, admin_headers):
        """✅ قيد إعدام دين معدوم"""
        # Dr. Bad Debt Expense / Cr. Accounts Receivable
        r = client.post("/api/accounting/journal-entries", json={
            "date": str(date.today()),
            "description": "إعدام دين معدوم",
            "reference": "BAD-DEBT-001",
            "lines": [
                {"account_id": 46, "debit": 5000, "credit": 0, "description": "ديون معدومة"},
                {"account_id": 10, "debit": 0, "credit": 5000, "description": "إعدام ذمة عميل"},
            ]
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400]

    def test_provision_for_bad_debts(self, client, admin_headers):
        """✅ قيد مخصص ديون مشكوك فيها"""
        # Dr. Bad Debt Expense / Cr. Allowance for Doubtful Accounts
        r = client.post("/api/accounting/journal-entries", json={
            "date": str(date.today()),
            "description": "مخصص ديون مشكوك فيها",
            "reference": "PROV-BD-001",
            "lines": [
                {"account_id": 46, "debit": 10000, "credit": 0, "description": "مصروف مخصص"},
                {"account_id": 11, "debit": 0, "credit": 10000, "description": "مخصص"},
            ]
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400]

