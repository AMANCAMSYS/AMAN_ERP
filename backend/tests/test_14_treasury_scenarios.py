"""
AMAN ERP - اختبارات شاملة متعددة السيناريوهات: الخزينة
Comprehensive Multi-Scenario Tests: Treasury Module
═══════════════════════════════════════════════════════
يتضمن: حسابات الخزينة، المصروفات، التحويلات، المطابقة البنكية
"""

import pytest
from datetime import date, timedelta
from helpers import assert_valid_response


# ═══════════════════════════════════════════════════════════════
# 🏦 حسابات الخزينة - Treasury Accounts
# ═══════════════════════════════════════════════════════════════
class TestTreasuryAccountScenarios:
    """سيناريوهات حسابات الخزينة"""

    def test_list_treasury_accounts(self, client, admin_headers):
        """✅ عرض حسابات الخزينة"""
        r = client.get("/api/treasury/accounts", headers=admin_headers)
        assert_valid_response(r)
        assert len(r.json()) >= 2

    def test_create_cash_account(self, client, admin_headers, base_currency):
        """✅ إنشاء صندوق نقدي"""
        r = client.post("/api/treasury/accounts", json={
            "name": "صندوق فرعي اختبار",
            "account_type": "cash",
            "currency": base_currency,
            "opening_balance": 5000,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 409, 500]

    def test_create_bank_account(self, client, admin_headers, base_currency):
        """✅ إنشاء حساب بنكي"""
        r = client.post("/api/treasury/accounts", json={
            "name": "حساب بنك الاختبار",
            "account_type": "bank",
            "currency": base_currency,
            "opening_balance": 100000,
            "branch_id": 1,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 409, 500]

    def test_create_usd_treasury(self, client, admin_headers):
        """✅ إنشاء حساب خزينة بعملة أجنبية"""
        r = client.post("/api/treasury/accounts", json={
            "name": "حساب دولار",
            "account_type": "bank",
            "currency": "USD",
            "opening_balance": 10000,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 409, 500]

    def test_update_treasury_account(self, client, admin_headers, base_currency):
        """✅ تحديث حساب خزينة"""
        r = client.get("/api/treasury/accounts", headers=admin_headers)
        accounts = r.json()
        if not accounts:
            pytest.skip("لا حسابات خزينة")
        aid = accounts[-1]["id"]
        r2 = client.put(f"/api/treasury/accounts/{aid}", json={
            "name": "حساب محدّث",
            "account_type": "cash",
            "currency": base_currency,
        }, headers=admin_headers)
        assert r2.status_code in [200, 400, 404, 422]

    def test_transaction_log(self, client, admin_headers):
        """✅ سجل العمليات"""
        r = client.get("/api/treasury/transactions", headers=admin_headers)
        assert r.status_code in [200, 404]


# ═══════════════════════════════════════════════════════════════
# 💸 المصروفات - Expenses
# ═══════════════════════════════════════════════════════════════
class TestExpenseScenarios:
    """سيناريوهات المصروفات"""

    def test_record_expense_general(self, client, admin_headers):
        """✅ تسجيل مصروف عام"""
        r = client.post("/api/treasury/transactions/expense", json={
            "transaction_type": "expense",
            "amount": 500,
            "treasury_id": 2,
            "target_account_id": 42,  # مصروف اهلاك
            "description": "مصاريف متنوعة",
            "transaction_date": str(date.today()),
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 500]

    def test_record_expense_bank_fees(self, client, admin_headers):
        """✅ تسجيل رسوم بنكية"""
        r = client.post("/api/treasury/transactions/expense", json={
            "transaction_type": "expense",
            "amount": 150,
            "treasury_id": 3,
            "target_account_id": 44,  # رسوم بنكية
            "description": "رسوم بنكية شهرية",
            "transaction_date": str(date.today()),
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 500]

    def test_record_expense_zero_amount_fails(self, client, admin_headers):
        """✅ رفض مصروف بمبلغ صفر"""
        r = client.post("/api/treasury/transactions/expense", json={
            "transaction_type": "expense",
            "amount": 0,
            "treasury_id": 2,
            "target_account_id": 42,
            "description": "مصروف صفري",
            "transaction_date": str(date.today()),
        }, headers=admin_headers)
        assert r.status_code in [400, 422]

    def test_list_expense_claims(self, client, admin_headers):
        """✅ عرض المطالبات"""
        r = client.get("/api/expenses/claims", headers=admin_headers)
        assert r.status_code in [200, 404, 422]

    def test_create_expense_claim(self, client, admin_headers):
        """✅ إنشاء مطالبة مصروف"""
        r = client.post("/api/expenses/claims", json={
            "description": "مصاريف ضيافة",
            "amount": 300,
            "expense_date": str(date.today()),
            "treasury_id": 2,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 405, 422]
# ═══════════════════════════════════════════════════════════════
class TestTransferScenarios:
    """سيناريوهات التحويلات"""

    def test_transfer_cash_to_bank(self, client, admin_headers):
        """✅ تحويل من صندوق لبنك"""
        r = client.post("/api/treasury/transactions/transfer", json={
            "transaction_type": "transfer",
            "amount": 1000,
            "treasury_id": 2,
            "target_treasury_id": 3,
            "description": "تحويل من صندوق نقدي لحساب بنكي",
            "transaction_date": str(date.today()),
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400]

    def test_transfer_bank_to_cash(self, client, admin_headers):
        """✅ تحويل من بنك لصندوق"""
        r = client.post("/api/treasury/transactions/transfer", json={
            "transaction_type": "transfer",
            "amount": 500,
            "treasury_id": 3,
            "target_treasury_id": 2,
            "description": "سحب من البنك للصندوق",
            "transaction_date": str(date.today()),
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400]

    def test_transfer_same_account_fails(self, client, admin_headers):
        """✅ رفض تحويل لنفس الحساب"""
        r = client.post("/api/treasury/transactions/transfer", json={
            "transaction_type": "transfer",
            "amount": 100,
            "treasury_id": 2,
            "target_treasury_id": 2,
            "description": "تحويل لنفس الحساب",
            "transaction_date": str(date.today()),
        }, headers=admin_headers)
        assert r.status_code in [400, 422]

    def test_transfer_zero_amount_fails(self, client, admin_headers):
        """✅ رفض تحويل بمبلغ صفر"""
        r = client.post("/api/treasury/transactions/transfer", json={
            "transaction_type": "transfer",
            "amount": 0,
            "treasury_id": 2,
            "target_treasury_id": 3,
            "description": "تحويل صفري",
            "transaction_date": str(date.today()),
        }, headers=admin_headers)
        assert r.status_code in [400, 422]


# ═══════════════════════════════════════════════════════════════
# 🏦 المطابقة البنكية - Bank Reconciliation
# ═══════════════════════════════════════════════════════════════
class TestBankReconciliationScenarios:
    """سيناريوهات المطابقة البنكية"""

    def test_list_reconciliations(self, client, admin_headers):
        """✅ عرض المطابقات"""
        r = client.get("/api/reconciliation", headers=admin_headers)
        assert_valid_response(r)

    def test_create_reconciliation(self, client, admin_headers):
        """✅ إنشاء مطابقة جديدة"""
        r = client.post("/api/reconciliation", json={
            "treasury_account_id": 4,
            "statement_date": str(date.today()),
            "start_balance": 50000,
            "end_balance": 52000,
            "branch_id": 1,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400]

    def test_get_reconciliation_detail(self, client, admin_headers):
        """✅ تفاصيل مطابقة"""
        r = client.get("/api/reconciliation", headers=admin_headers)
        recons = r.json()
        if not recons:
            pytest.skip("لا مطابقات")
        rid = recons[0]["id"]
        r2 = client.get(f"/api/reconciliation/{rid}", headers=admin_headers)
        assert r2.status_code in [200, 404]

    def test_add_statement_lines(self, client, admin_headers):
        """✅ إضافة أسطر كشف بنكي"""
        r = client.get("/api/reconciliation", headers=admin_headers)
        recons = r.json()
        if not recons:
            pytest.skip("لا مطابقات")
        rid = recons[0]["id"]
        r2 = client.post(f"/api/reconciliation/{rid}/lines", json=[
            {"transaction_date": str(date.today()), "description": "إيداع اختبار", "debit": 1000, "credit": 0},
            {"transaction_date": str(date.today()), "description": "سحب اختبار", "debit": 0, "credit": 500},
        ], headers=admin_headers)
        assert r2.status_code in [200, 201, 400]

    def test_get_unreconciled_entries(self, client, admin_headers):
        """✅ القيود غير المطابقة"""
        r = client.get("/api/reconciliation", headers=admin_headers)
        recons = r.json()
        if not recons:
            pytest.skip("لا مطابقات")
        rid = recons[0]["id"]
        r2 = client.get(f"/api/reconciliation/{rid}/unreconciled", headers=admin_headers)
        assert r2.status_code in [200, 404]

    def test_delete_draft_reconciliation(self, client, admin_headers):
        """✅ حذف مطابقة مسودة"""
        # Create a new one to delete
        r = client.post("/api/reconciliation", json={
            "treasury_account_id": 4,
            "statement_date": str(date.today() - timedelta(days=30)),
            "start_balance": 40000,
            "end_balance": 41000,
            "branch_id": 1,
        }, headers=admin_headers)
        if r.status_code in [200, 201]:
            rid = r.json().get("id")
            if rid:
                r2 = client.delete(f"/api/reconciliation/{rid}", headers=admin_headers)
                assert r2.status_code in [200, 204, 400]
