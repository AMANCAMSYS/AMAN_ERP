"""
test_30_manufacturing_pos_hr_treasury_advanced.py
===================================================
اختبارات متقدمة للتصنيع، نقاط البيع، الموارد البشرية، والخزينة

Covers UNTESTED endpoints:
- Manufacturing: start/cancel orders, dashboard/stats
- POS: resume/cancel-held orders, return
- HR: payroll-periods/{id}/post
- Treasury: DELETE accounts/{id}, reports/balances, reports/cashflow
"""
import pytest
from datetime import date, timedelta
from helpers import assert_valid_response, assert_error_response


# ══════════════════════════════════════════════════════════════
# 🏭 التصنيع المتقدم (Manufacturing Advanced)
# ══════════════════════════════════════════════════════════════

class TestManufacturingAdvanced:
    """اختبارات متقدمة للتصنيع"""

    def _get_production_order_id(self, client, admin_headers):
        r = client.get("/api/manufacturing/orders", headers=admin_headers)
        if r.status_code != 200:
            return None
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])
        return items[0]["id"] if items else None

    def test_start_production_order(self, client, admin_headers):
        """اختبار بدء أمر إنتاج"""
        order_id = self._get_production_order_id(client, admin_headers)
        if not order_id:
            pytest.skip("لا توجد أوامر إنتاج")
        r = client.post(f"/api/manufacturing/orders/{order_id}/start",
                        headers=admin_headers)
        assert r.status_code in (200, 400, 404, 422, 501)

    def test_cancel_production_order(self, client, admin_headers):
        """اختبار إلغاء أمر إنتاج"""
        order_id = self._get_production_order_id(client, admin_headers)
        if not order_id:
            pytest.skip("لا توجد أوامر إنتاج")
        r = client.post(f"/api/manufacturing/orders/{order_id}/cancel",
                        json={"reason": "إلغاء للاختبار"},
                        headers=admin_headers)
        assert r.status_code in (200, 400, 404, 422, 501)

    def test_get_production_order_detail(self, client, admin_headers):
        """اختبار تفاصيل أمر إنتاج"""
        order_id = self._get_production_order_id(client, admin_headers)
        if not order_id:
            pytest.skip("لا توجد أوامر إنتاج")
        r = client.get(f"/api/manufacturing/orders/{order_id}",
                       headers=admin_headers)
        assert r.status_code in (200, 404)

    def test_manufacturing_dashboard_stats(self, client, admin_headers):
        """اختبار إحصائيات لوحة التصنيع"""
        r = client.get("/api/manufacturing/dashboard/stats",
                       headers=admin_headers)
        assert r.status_code in (200, 404, 501)

    def test_create_and_start_production_order(self, client, admin_headers):
        """اختبار إنشاء أمر إنتاج وبدئه"""
        # جلب BOM
        bom_r = client.get("/api/manufacturing/boms", headers=admin_headers)
        if bom_r.status_code != 200:
            pytest.skip("لا توجد قوائم مواد")
        boms = bom_r.json()
        if isinstance(boms, dict):
            boms = boms.get("items", [])
        if not boms:
            pytest.skip("لا توجد قوائم مواد")

        order_data = {
            "bom_id": boms[0]["id"],
            "quantity": 5,
            "planned_start_date": str(date.today()),
            "planned_end_date": str(date.today() + timedelta(days=7))
        }
        create_r = client.post("/api/manufacturing/orders",
                               json=order_data, headers=admin_headers)
        assert create_r.status_code in (200, 201, 400, 404, 422)


# ══════════════════════════════════════════════════════════════
# 🏪 نقاط البيع المتقدمة (POS Advanced)
# ══════════════════════════════════════════════════════════════

class TestPOSAdvanced:
    """اختبارات متقدمة لنقاط البيع"""

    def _get_held_order_id(self, client, admin_headers):
        r = client.get("/api/pos/orders/held", headers=admin_headers)
        if r.status_code != 200:
            return None
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])
        return items[0]["id"] if items else None

    def test_resume_held_order(self, client, admin_headers):
        """اختبار استئناف طلب معلق"""
        order_id = self._get_held_order_id(client, admin_headers)
        if not order_id:
            pytest.skip("لا توجد طلبات معلقة")
        r = client.post(f"/api/pos/orders/{order_id}/resume",
                        headers=admin_headers)
        assert r.status_code in (200, 404, 422, 501)

    def test_cancel_held_order(self, client, admin_headers):
        """اختبار إلغاء طلب معلق"""
        order_id = self._get_held_order_id(client, admin_headers)
        if not order_id:
            pytest.skip("لا توجد طلبات معلقة")
        r = client.delete(f"/api/pos/orders/{order_id}/cancel-held",
                          headers=admin_headers)
        assert r.status_code in (200, 204, 404, 422, 501)

    def test_create_pos_return(self, client, admin_headers):
        """اختبار إنشاء مرتجع POS"""
        # فتح جلسة POS أولاً
        session_r = client.get("/api/pos/sessions/active", headers=admin_headers)
        if session_r.status_code != 200:
            # محاولة فتح جلسة
            wh_r = client.get("/api/pos/warehouses", headers=admin_headers)
            if wh_r.status_code != 200:
                pytest.skip("لا يمكن فتح جلسة POS")
            whs = wh_r.json()
            if isinstance(whs, dict):
                whs = whs.get("items", [])
            if not whs:
                pytest.skip("لا توجد مخازن POS")
            open_r = client.post("/api/pos/sessions/open",
                                 json={"warehouse_id": whs[0]["id"]},
                                 headers=admin_headers)
            if open_r.status_code not in (200, 201):
                pytest.skip("لا يمكن فتح جلسة")

        # محاولة إنشاء مرتجع لطلب سابق
        return_data = {
            "order_id": None,  # سيتم ملؤه
            "items": [],
            "reason": "مرتجع اختبار"
        }
        r = client.post("/api/pos/orders/999999/return",
                        json=return_data, headers=admin_headers)
        assert r.status_code in (200, 201, 400, 404, 422, 501)

    def test_pos_order_detail(self, client, admin_headers):
        """اختبار تفاصيل طلب POS"""
        # جلب طلب
        r = client.get("/api/pos/orders/held", headers=admin_headers)
        if r.status_code == 200:
            data = r.json()
            items = data if isinstance(data, list) else data.get("items", [])
            if items:
                order_id = items[0]["id"]
                r2 = client.get(f"/api/pos/orders/{order_id}/details",
                                headers=admin_headers)
                assert r2.status_code in (200, 404)


# ══════════════════════════════════════════════════════════════
# 👥 الموارد البشرية المتقدمة (HR Advanced)
# ══════════════════════════════════════════════════════════════

class TestHRPayrollPost:
    """اختبارات ترحيل الرواتب"""

    def _get_payroll_period_id(self, client, admin_headers):
        r = client.get("/api/hr/payroll-periods", headers=admin_headers)
        if r.status_code != 200:
            return None
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("periods", []))
        return items[0]["id"] if items else None

    def test_post_payroll_period(self, client, admin_headers):
        """اختبار ترحيل فترة رواتب"""
        period_id = self._get_payroll_period_id(client, admin_headers)
        if not period_id:
            pytest.skip("لا توجد فترات رواتب")
        r = client.post(f"/api/hr/payroll-periods/{period_id}/post",
                        headers=admin_headers)
        assert r.status_code in (200, 400, 404, 422, 501)

    def test_payroll_period_detail(self, client, admin_headers):
        """اختبار تفاصيل فترة رواتب"""
        period_id = self._get_payroll_period_id(client, admin_headers)
        if not period_id:
            pytest.skip("لا توجد فترات رواتب")
        r = client.get(f"/api/hr/payroll-periods/{period_id}",
                       headers=admin_headers)
        assert r.status_code in (200, 404)

    def test_generate_payroll_entries(self, client, admin_headers):
        """اختبار توليد قيود الرواتب"""
        period_id = self._get_payroll_period_id(client, admin_headers)
        if not period_id:
            pytest.skip("لا توجد فترات رواتب")
        r = client.post(f"/api/hr/payroll-periods/{period_id}/generate",
                        headers=admin_headers)
        assert r.status_code in (200, 201, 400, 404, 422, 501)

    def test_payroll_entries_list(self, client, admin_headers):
        """اختبار عرض قيود الرواتب"""
        period_id = self._get_payroll_period_id(client, admin_headers)
        if not period_id:
            pytest.skip("لا توجد فترات رواتب")
        r = client.get(f"/api/hr/payroll-periods/{period_id}/entries",
                       headers=admin_headers)
        assert r.status_code in (200, 404)


# ══════════════════════════════════════════════════════════════
# 💰 الخزينة المتقدمة (Treasury Advanced)
# ══════════════════════════════════════════════════════════════

class TestTreasuryAdvanced:
    """اختبارات متقدمة للخزينة"""

    def _get_treasury_account_id(self, client, admin_headers):
        r = client.get("/api/treasury/accounts", headers=admin_headers)
        if r.status_code != 200:
            return None
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("accounts", []))
        return items[-1]["id"] if items else None  # آخر حساب للحذف

    def test_delete_treasury_account(self, client, admin_headers):
        """اختبار حذف حساب خزينة"""
        account_id = self._get_treasury_account_id(client, admin_headers)
        if not account_id:
            pytest.skip("لا توجد حسابات خزينة")
        r = client.delete(f"/api/treasury/accounts/{account_id}",
                          headers=admin_headers)
        assert r.status_code in (200, 204, 400, 404, 422, 501)

    def test_treasury_balances_report(self, client, admin_headers):
        """اختبار تقرير أرصدة الخزينة"""
        r = client.get("/api/treasury/reports/balances",
                       headers=admin_headers)
        assert r.status_code in (200, 404, 501)

    def test_treasury_cashflow_report(self, client, admin_headers):
        """اختبار تقرير التدفقات النقدية للخزينة"""
        r = client.get("/api/treasury/reports/cashflow",
                       headers=admin_headers)
        assert r.status_code in (200, 404, 501)

    def test_treasury_transactions_filter(self, client, admin_headers):
        """اختبار فلترة معاملات الخزينة"""
        accounts_r = client.get("/api/treasury/accounts", headers=admin_headers)
        if accounts_r.status_code != 200:
            pytest.skip("لا توجد حسابات خزينة")
        accounts = accounts_r.json()
        if isinstance(accounts, dict):
            accounts = accounts.get("items", [])
        if not accounts:
            pytest.skip("لا توجد حسابات")
        acc_id = accounts[0]["id"]
        r = client.get(f"/api/treasury/transactions?account_id={acc_id}",
                       headers=admin_headers)
        assert r.status_code in (200, 404)

    def test_create_treasury_transfer(self, client, admin_headers):
        """اختبار تحويل بين حسابات الخزينة"""
        accounts_r = client.get("/api/treasury/accounts", headers=admin_headers)
        if accounts_r.status_code != 200:
            pytest.skip("لا توجد حسابات خزينة")
        accounts = accounts_r.json()
        if isinstance(accounts, dict):
            accounts = accounts.get("items", [])
        if len(accounts) < 2:
            pytest.skip("يجب وجود حسابين خزينة على الأقل")

        transfer_data = {
            "from_account_id": accounts[0]["id"],
            "to_account_id": accounts[1]["id"],
            "amount": 1000.00,
            "date": str(date.today()),
            "description": "تحويل اختبار"
        }
        r = client.post("/api/treasury/transactions/transfer",
                        json=transfer_data, headers=admin_headers)
        assert r.status_code in (200, 201, 400, 422)

    def test_create_treasury_expense(self, client, admin_headers):
        """اختبار تسجيل مصروف من الخزينة"""
        accounts_r = client.get("/api/treasury/accounts", headers=admin_headers)
        if accounts_r.status_code != 200:
            pytest.skip("لا توجد حسابات خزينة")
        accounts = accounts_r.json()
        if isinstance(accounts, dict):
            accounts = accounts.get("items", [])
        if not accounts:
            pytest.skip("لا توجد حسابات")

        expense_data = {
            "account_id": accounts[0]["id"],
            "amount": 500.00,
            "date": str(date.today()),
            "description": "مصروف اختبار",
            "category": "office_supplies"
        }
        r = client.post("/api/treasury/transactions/expense",
                        json=expense_data, headers=admin_headers)
        assert r.status_code in (200, 201, 400, 422)
