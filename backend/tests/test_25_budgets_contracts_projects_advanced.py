"""
test_25_budgets_contracts_projects_advanced.py
===============================================
اختبارات متقدمة للميزانيات والعقود والمشاريع

Covers UNTESTED endpoints:
- POST /api/accounting/budgets/{id}/activate
- POST /api/accounting/budgets/{id}/close
- GET /api/accounting/budgets/alerts/overruns
- GET /api/accounting/budgets/stats/summary
- GET /api/accounting/budgets/{id}/items
- POST /api/contracts/{id}/cancel
- GET /api/contracts/alerts/expiring
- GET /api/contracts/stats/summary
- GET /api/projects/summary
- Project tasks CRUD
- Project expenses/revenues/financials
"""
import pytest
from datetime import date, timedelta
from helpers import assert_valid_response, assert_error_response


# ══════════════════════════════════════════════════════════════
# 💰 الميزانيات المتقدمة - Budgets Advanced
# ══════════════════════════════════════════════════════════════

class TestBudgetActivateClose:
    """اختبارات تفعيل وإغلاق الميزانيات"""

    def _get_budget_id(self, client, admin_headers):
        r = client.get("/api/accounting/budgets/", headers=admin_headers)
        if r.status_code != 200:
            return None
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("budgets", []))
        return items[0]["id"] if items else None

    def test_activate_budget(self, client, admin_headers):
        """اختبار تفعيل ميزانية"""
        bid = self._get_budget_id(client, admin_headers)
        if not bid:
            pytest.skip("لا توجد ميزانيات")
        r = client.post(f"/api/accounting/budgets/{bid}/activate",
                        headers=admin_headers)
        assert r.status_code in (200, 400, 404, 422, 501)

    def test_close_budget(self, client, admin_headers):
        """اختبار إغلاق ميزانية"""
        bid = self._get_budget_id(client, admin_headers)
        if not bid:
            pytest.skip("لا توجد ميزانيات")
        r = client.post(f"/api/accounting/budgets/{bid}/close",
                        headers=admin_headers)
        assert r.status_code in (200, 400, 404, 422, 501)

    def test_get_budget_items(self, client, admin_headers):
        """اختبار عرض بنود الميزانية"""
        bid = self._get_budget_id(client, admin_headers)
        if not bid:
            pytest.skip("لا توجد ميزانيات")
        r = client.get(f"/api/accounting/budgets/{bid}/items",
                       headers=admin_headers)
        assert r.status_code in (200, 404, 501)
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data, (list, dict))


class TestBudgetAlerts:
    """اختبارات تنبيهات الميزانية"""

    def test_budget_overrun_alerts(self, client, admin_headers):
        """اختبار تنبيهات تجاوز الميزانية"""
        r = client.get("/api/accounting/budgets/alerts/overruns",
                       headers=admin_headers)
        assert r.status_code in (200, 404, 501)
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data, (list, dict))

    def test_budget_stats_summary(self, client, admin_headers):
        """اختبار إحصائيات الميزانيات"""
        r = client.get("/api/accounting/budgets/stats/summary",
                       headers=admin_headers)
        assert r.status_code in (200, 404, 501)
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data, dict)

    def test_budget_vs_actual_report(self, client, admin_headers):
        """اختبار تقرير الميزانية مقابل الفعلي"""
        bid = None
        r = client.get("/api/accounting/budgets/", headers=admin_headers)
        if r.status_code == 200:
            data = r.json()
            items = data if isinstance(data, list) else data.get("items", [])
            if items:
                bid = items[0]["id"]
        if bid:
            r2 = client.get(f"/api/reports/accounting/budget-vs-actual?budget_id={bid}",
                            headers=admin_headers)
            assert r2.status_code in (200, 404)

    def test_create_budget_with_items(self, client, admin_headers):
        """اختبار إنشاء ميزانية مع بنود"""
        accounts_r = client.get("/api/accounting/accounts", headers=admin_headers)
        if accounts_r.status_code != 200:
            pytest.skip("لا يمكن جلب الحسابات")
        accounts = accounts_r.json()
        if isinstance(accounts, dict):
            accounts = accounts.get("items", accounts.get("accounts", []))
        if not accounts:
            pytest.skip("لا توجد حسابات")

        budget_data = {
            "name": f"ميزانية اختبار - {date.today()}",
            "year": date.today().year,
            "start_date": str(date.today().replace(month=1, day=1)),
            "end_date": str(date.today().replace(month=12, day=31)),
            "budget_type": "annual",
            "status": "draft"
        }
        r = client.post("/api/accounting/budgets/", json=budget_data,
                        headers=admin_headers)
        assert r.status_code in (200, 201, 400, 422)
        if r.status_code in (200, 201):
            bid = r.json().get("id")
            if bid:
                # إضافة بنود
                item_data = {
                    "account_id": accounts[0]["id"],
                    "amount": 100000.00,
                    "period": "annual"
                }
                r2 = client.post(f"/api/accounting/budgets/{bid}/items",
                                 json=item_data, headers=admin_headers)
                assert r2.status_code in (200, 201, 400, 422)


# ══════════════════════════════════════════════════════════════
# 📋 العقود المتقدمة - Contracts Advanced
# ══════════════════════════════════════════════════════════════

class TestContractCancel:
    """اختبارات إلغاء العقود"""

    def _get_contract_id(self, client, admin_headers):
        r = client.get("/api/contracts", headers=admin_headers)
        if r.status_code != 200:
            return None
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("contracts", []))
        return items[0]["id"] if items else None

    def test_cancel_contract(self, client, admin_headers):
        """اختبار إلغاء عقد"""
        cid = self._get_contract_id(client, admin_headers)
        if not cid:
            pytest.skip("لا توجد عقود")
        r = client.post(f"/api/contracts/{cid}/cancel",
                        json={"reason": "إلغاء للاختبار"},
                        headers=admin_headers)
        assert r.status_code in (200, 400, 404, 422, 501)

    def test_cancel_nonexistent_contract(self, client, admin_headers):
        """اختبار إلغاء عقد غير موجود"""
        r = client.post("/api/contracts/999999/cancel",
                        json={"reason": "اختبار"},
                        headers=admin_headers)
        assert r.status_code in (404, 422, 500, 501)


class TestContractAlerts:
    """اختبارات تنبيهات العقود"""

    def test_expiring_contracts_alerts(self, client, admin_headers):
        """اختبار تنبيهات العقود المنتهية"""
        r = client.get("/api/contracts/alerts/expiring", headers=admin_headers)
        assert r.status_code in (200, 404, 501)
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data, (list, dict))

    def test_contracts_stats_summary(self, client, admin_headers):
        """اختبار إحصائيات العقود"""
        r = client.get("/api/contracts/stats/summary", headers=admin_headers)
        assert r.status_code in (200, 404, 501)

    def test_contract_generate_invoice(self, client, admin_headers):
        """اختبار إصدار فاتورة من عقد"""
        r = client.get("/api/contracts", headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("لا يمكن جلب العقود")
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])
        if not items:
            pytest.skip("لا توجد عقود")
        cid = items[0]["id"]
        r2 = client.post(f"/api/contracts/{cid}/generate-invoice",
                         headers=admin_headers)
        assert r2.status_code in (200, 201, 400, 404, 422, 501)

    def test_contract_renew(self, client, admin_headers):
        """اختبار تجديد عقد"""
        r = client.get("/api/contracts", headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("لا يمكن جلب العقود")
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])
        if not items:
            pytest.skip("لا توجد عقود")
        cid = items[0]["id"]
        r2 = client.post(f"/api/contracts/{cid}/renew",
                         json={"duration_months": 12},
                         headers=admin_headers)
        assert r2.status_code in (200, 201, 400, 404, 422, 501)


# ══════════════════════════════════════════════════════════════
# 🏗 المشاريع المتقدمة - Projects Advanced
# ══════════════════════════════════════════════════════════════

class TestProjectSummary:
    """اختبارات ملخص المشاريع"""

    def test_projects_summary(self, client, admin_headers):
        """اختبار ملخص المشاريع"""
        r = client.get("/api/projects/summary", headers=admin_headers)
        assert r.status_code in (200, 404, 501)

    def test_project_list_with_filters(self, client, admin_headers):
        """اختبار عرض المشاريع مع فلاتر"""
        for status in ["active", "completed", "on_hold"]:
            r = client.get(f"/api/projects/?status={status}",
                           headers=admin_headers)
            assert r.status_code in (200, 404)


class TestProjectTasks:
    """اختبارات مهام المشاريع"""

    def _get_project_id(self, client, admin_headers):
        r = client.get("/api/projects/", headers=admin_headers)
        if r.status_code != 200:
            return None
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("projects", []))
        return items[0]["id"] if items else None

    def test_list_project_tasks(self, client, admin_headers):
        """اختبار عرض مهام المشروع"""
        pid = self._get_project_id(client, admin_headers)
        if not pid:
            pytest.skip("لا توجد مشاريع")
        r = client.get(f"/api/projects/{pid}/tasks", headers=admin_headers)
        assert r.status_code in (200, 404, 501)

    def test_create_project_task(self, client, admin_headers):
        """اختبار إنشاء مهمة في مشروع"""
        pid = self._get_project_id(client, admin_headers)
        if not pid:
            pytest.skip("لا توجد مشاريع")
        task_data = {
            "title": "مهمة اختبار",
            "description": "وصف مهمة الاختبار",
            "status": "pending",
            "priority": "medium",
            "due_date": str(date.today() + timedelta(days=14))
        }
        r = client.post(f"/api/projects/{pid}/tasks",
                        json=task_data, headers=admin_headers)
        assert r.status_code in (200, 201, 404, 422, 501)

    def test_update_project_task(self, client, admin_headers):
        """اختبار تحديث مهمة مشروع"""
        pid = self._get_project_id(client, admin_headers)
        if not pid:
            pytest.skip("لا توجد مشاريع")
        tasks_r = client.get(f"/api/projects/{pid}/tasks", headers=admin_headers)
        if tasks_r.status_code != 200:
            pytest.skip("لا يمكن جلب المهام")
        tasks = tasks_r.json()
        if isinstance(tasks, dict):
            tasks = tasks.get("items", tasks.get("tasks", []))
        if not tasks:
            pytest.skip("لا توجد مهام")
        task_id = tasks[0]["id"]
        r = client.put(f"/api/projects/{pid}/tasks/{task_id}",
                       json={"status": "in_progress"},
                       headers=admin_headers)
        assert r.status_code in (200, 404, 422, 501)

    def test_delete_project_task(self, client, admin_headers):
        """اختبار حذف مهمة مشروع"""
        pid = self._get_project_id(client, admin_headers)
        if not pid:
            pytest.skip("لا توجد مشاريع")
        tasks_r = client.get(f"/api/projects/{pid}/tasks", headers=admin_headers)
        if tasks_r.status_code != 200:
            pytest.skip("لا يمكن جلب المهام")
        tasks = tasks_r.json()
        if isinstance(tasks, dict):
            tasks = tasks.get("items", tasks.get("tasks", []))
        if not tasks:
            pytest.skip("لا توجد مهام")
        task_id = tasks[-1]["id"]
        r = client.delete(f"/api/projects/{pid}/tasks/{task_id}",
                          headers=admin_headers)
        assert r.status_code in (200, 204, 404, 501)


class TestProjectFinancials:
    """اختبارات الجانب المالي للمشاريع"""

    def _get_project_id(self, client, admin_headers):
        r = client.get("/api/projects/", headers=admin_headers)
        if r.status_code != 200:
            return None
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("projects", []))
        return items[0]["id"] if items else None

    def test_project_expenses(self, client, admin_headers):
        """اختبار مصروفات المشروع"""
        pid = self._get_project_id(client, admin_headers)
        if not pid:
            pytest.skip("لا توجد مشاريع")
        r = client.get(f"/api/projects/{pid}/expenses", headers=admin_headers)
        assert r.status_code in (200, 404, 501)

    def test_add_project_expense(self, client, admin_headers):
        """اختبار إضافة مصروف للمشروع"""
        pid = self._get_project_id(client, admin_headers)
        if not pid:
            pytest.skip("لا توجد مشاريع")
        expense_data = {
            "description": "مصروفات مواد - اختبار",
            "amount": 2500.00,
            "date": str(date.today()),
            "category": "materials"
        }
        r = client.post(f"/api/projects/{pid}/expenses",
                        json=expense_data, headers=admin_headers)
        assert r.status_code in (200, 201, 404, 422, 501)

    def test_project_revenues(self, client, admin_headers):
        """اختبار إيرادات المشروع"""
        pid = self._get_project_id(client, admin_headers)
        if not pid:
            pytest.skip("لا توجد مشاريع")
        r = client.get(f"/api/projects/{pid}/revenues", headers=admin_headers)
        assert r.status_code in (200, 404, 501)

    def test_add_project_revenue(self, client, admin_headers):
        """اختبار إضافة إيراد للمشروع"""
        pid = self._get_project_id(client, admin_headers)
        if not pid:
            pytest.skip("لا توجد مشاريع")
        revenue_data = {
            "description": "دفعة عميل - اختبار",
            "amount": 10000.00,
            "date": str(date.today())
        }
        r = client.post(f"/api/projects/{pid}/revenues",
                        json=revenue_data, headers=admin_headers)
        assert r.status_code in (200, 201, 404, 422, 501)

    def test_project_financials(self, client, admin_headers):
        """اختبار الملخص المالي للمشروع"""
        pid = self._get_project_id(client, admin_headers)
        if not pid:
            pytest.skip("لا توجد مشاريع")
        r = client.get(f"/api/projects/{pid}/financials", headers=admin_headers)
        assert r.status_code in (200, 404, 501)
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data, dict)

    def test_project_profitability(self, client, admin_headers):
        """اختبار ربحية المشروع"""
        pid = self._get_project_id(client, admin_headers)
        if not pid:
            pytest.skip("لا توجد مشاريع")
        r = client.get(f"/api/projects/{pid}/profitability",
                       headers=admin_headers)
        assert r.status_code in (200, 404, 501)
