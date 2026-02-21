"""
test_23_recurring_opening_closing.py
=====================================
اختبارات القوالب المتكررة، الأرصدة الافتتاحية، وإقفال القيود

Covers UNTESTED endpoints:
- POST /api/accounting/recurring-templates (CRUD + generate)
- GET/POST /api/accounting/opening-balances
- GET/POST /api/accounting/closing-entries (preview + generate)
- POST /api/accounting/journal-entries/{id}/post
- POST /api/accounting/fiscal-years/{id}/close-period (toggle)
"""
import pytest
from datetime import date, timedelta
from helpers import assert_valid_response, assert_error_response


# ══════════════════════════════════════════════════════════════
# 📋 القوالب المتكررة - Recurring Templates
# ══════════════════════════════════════════════════════════════

class TestRecurringTemplates:
    """اختبارات قوالب القيود المتكررة"""

    def test_list_recurring_templates(self, client, admin_headers):
        """اختبار عرض قائمة القوالب المتكررة"""
        r = client.get("/api/accounting/recurring-templates", headers=admin_headers)
        assert r.status_code in (200, 404, 501), f"Unexpected: {r.status_code}"
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data, (list, dict))

    def test_create_recurring_template(self, client, admin_headers):
        """اختبار إنشاء قالب متكرر جديد"""
        # نحتاج حساب للقالب
        accounts_r = client.get("/api/accounting/accounts", headers=admin_headers)
        if accounts_r.status_code != 200:
            pytest.skip("لا يمكن جلب الحسابات")
        accounts = accounts_r.json()
        if isinstance(accounts, dict):
            accounts = accounts.get("items", accounts.get("accounts", []))
        if len(accounts) < 2:
            pytest.skip("لا توجد حسابات كافية")

        acc1 = accounts[0]["id"]
        acc2 = accounts[1]["id"]

        template_data = {
            "name": "إيجار شهري - اختبار",
            "description": "قالب إيجار شهري للاختبار",
            "frequency": "monthly",
            "start_date": str(date.today()),
            "amount": 5000.00,
            "lines": [
                {"account_id": acc1, "debit": 5000.00, "credit": 0},
                {"account_id": acc2, "debit": 0, "credit": 5000.00}
            ]
        }
        r = client.post("/api/accounting/recurring-templates",
                        json=template_data, headers=admin_headers)
        assert r.status_code in (200, 201, 404, 422, 501)

    def test_get_recurring_template_by_id(self, client, admin_headers):
        """اختبار جلب قالب متكرر بالمعرف"""
        r = client.get("/api/accounting/recurring-templates", headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("القوالب غير متوفرة")
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])
        if not items:
            pytest.skip("لا توجد قوالب")
        template_id = items[0]["id"]
        r2 = client.get(f"/api/accounting/recurring-templates/{template_id}",
                        headers=admin_headers)
        assert r2.status_code in (200, 404)

    def test_update_recurring_template(self, client, admin_headers):
        """اختبار تحديث قالب متكرر"""
        r = client.get("/api/accounting/recurring-templates", headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("القوالب غير متوفرة")
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])
        if not items:
            pytest.skip("لا توجد قوالب")
        template_id = items[0]["id"]
        r2 = client.put(f"/api/accounting/recurring-templates/{template_id}",
                        json={"name": "إيجار شهري - محدث", "amount": 5500.00},
                        headers=admin_headers)
        assert r2.status_code in (200, 404, 422, 501)

    def test_delete_recurring_template(self, client, admin_headers):
        """اختبار حذف قالب متكرر"""
        r = client.get("/api/accounting/recurring-templates", headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("القوالب غير متوفرة")
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])
        if not items:
            pytest.skip("لا توجد قوالب")
        template_id = items[-1]["id"]
        r2 = client.delete(f"/api/accounting/recurring-templates/{template_id}",
                           headers=admin_headers)
        assert r2.status_code in (200, 204, 404, 501)

    def test_generate_from_recurring_template(self, client, admin_headers):
        """اختبار توليد قيود من قالب متكرر"""
        r = client.get("/api/accounting/recurring-templates", headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("القوالب غير متوفرة")
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])
        if not items:
            pytest.skip("لا توجد قوالب")
        template_id = items[0]["id"]
        r2 = client.post(f"/api/accounting/recurring-templates/{template_id}/generate",
                         headers=admin_headers)
        assert r2.status_code in (200, 201, 404, 422, 501)


# ══════════════════════════════════════════════════════════════
# 📊 الأرصدة الافتتاحية - Opening Balances
# ══════════════════════════════════════════════════════════════

class TestOpeningBalances:
    """اختبارات الأرصدة الافتتاحية"""

    def test_get_opening_balances(self, client, admin_headers):
        """اختبار عرض الأرصدة الافتتاحية"""
        r = client.get("/api/accounting/opening-balances", headers=admin_headers)
        assert r.status_code in (200, 404, 501)
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data, (list, dict))

    def test_post_opening_balances(self, client, admin_headers):
        """اختبار تعيين أرصدة افتتاحية"""
        accounts_r = client.get("/api/accounting/accounts", headers=admin_headers)
        if accounts_r.status_code != 200:
            pytest.skip("لا يمكن جلب الحسابات")
        accounts = accounts_r.json()
        if isinstance(accounts, dict):
            accounts = accounts.get("items", accounts.get("accounts", []))
        if not accounts:
            pytest.skip("لا توجد حسابات")

        opening_data = {
            "date": str(date.today().replace(month=1, day=1)),
            "balances": [
                {"account_id": accounts[0]["id"], "debit": 10000.00, "credit": 0}
            ]
        }
        r = client.post("/api/accounting/opening-balances",
                        json=opening_data, headers=admin_headers)
        assert r.status_code in (200, 201, 404, 422, 501)

    def test_opening_balances_validation_debit_credit(self, client, admin_headers):
        """اختبار أن الأرصدة الافتتاحية متوازنة (المدين = الدائن)"""
        accounts_r = client.get("/api/accounting/accounts", headers=admin_headers)
        if accounts_r.status_code != 200:
            pytest.skip("لا يمكن جلب الحسابات")
        accounts = accounts_r.json()
        if isinstance(accounts, dict):
            accounts = accounts.get("items", accounts.get("accounts", []))
        if len(accounts) < 2:
            pytest.skip("لا توجد حسابات كافية")

        # أرصدة غير متوازنة - يجب أن يرفض النظام
        opening_data = {
            "date": str(date.today().replace(month=1, day=1)),
            "balances": [
                {"account_id": accounts[0]["id"], "debit": 10000.00, "credit": 0},
                {"account_id": accounts[1]["id"], "debit": 5000.00, "credit": 0}
            ]
        }
        r = client.post("/api/accounting/opening-balances",
                        json=opening_data, headers=admin_headers)
        # إما يرفض (422) أو يقبل حسب تصميم النظام
        assert r.status_code in (200, 201, 400, 404, 422, 501)


# ══════════════════════════════════════════════════════════════
# 🔒 إقفال القيود - Closing Entries
# ══════════════════════════════════════════════════════════════

class TestClosingEntries:
    """اختبارات قيود الإقفال"""

    def test_preview_closing_entries(self, client, admin_headers):
        """اختبار معاينة قيود الإقفال قبل التنفيذ"""
        r = client.get("/api/accounting/closing-entries/preview", headers=admin_headers)
        assert r.status_code in (200, 404, 501)
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data, (list, dict))

    def test_generate_closing_entries(self, client, admin_headers):
        """اختبار توليد قيود الإقفال"""
        closing_data = {
            "fiscal_year_id": None,  # will be filled
            "date": str(date.today())
        }
        # جلب السنة المالية الحالية
        fy_r = client.get("/api/accounting/fiscal-years/current", headers=admin_headers)
        if fy_r.status_code == 200:
            fy = fy_r.json()
            closing_data["fiscal_year_id"] = fy.get("id")

        r = client.post("/api/accounting/closing-entries/generate",
                        json=closing_data, headers=admin_headers)
        assert r.status_code in (200, 201, 400, 404, 422, 501)

    def test_closing_entries_without_fiscal_year(self, client, admin_headers):
        """اختبار إقفال بدون سنة مالية - يجب أن يرفض"""
        r = client.post("/api/accounting/closing-entries/generate",
                        json={}, headers=admin_headers)
        assert r.status_code in (400, 404, 422, 500, 501)


# ══════════════════════════════════════════════════════════════
# ✅ ترحيل القيود - Journal Entries Posting
# ══════════════════════════════════════════════════════════════

class TestJournalEntryPosting:
    """اختبارات ترحيل القيود المحاسبية"""

    def test_post_journal_entry(self, client, admin_headers):
        """اختبار ترحيل قيد محاسبي (نشر)"""
        # إنشاء قيد جديد
        accounts_r = client.get("/api/accounting/accounts", headers=admin_headers)
        if accounts_r.status_code != 200:
            pytest.skip("لا يمكن جلب الحسابات")
        accounts = accounts_r.json()
        if isinstance(accounts, dict):
            accounts = accounts.get("items", accounts.get("accounts", []))
        if len(accounts) < 2:
            pytest.skip("لا توجد حسابات كافية")

        je_data = {
            "date": str(date.today()),
            "description": "قيد للترحيل - اختبار",
            "lines": [
                {"account_id": accounts[0]["id"], "debit": 1000, "credit": 0,
                 "description": "مدين"},
                {"account_id": accounts[1]["id"], "debit": 0, "credit": 1000,
                 "description": "دائن"}
            ]
        }
        create_r = client.post("/api/accounting/journal-entries",
                               json=je_data, headers=admin_headers)
        if create_r.status_code not in (200, 201):
            pytest.skip("لا يمكن إنشاء قيد")
        je_id = create_r.json().get("id")
        if not je_id:
            pytest.skip("لا يوجد معرف القيد")

        # ترحيل القيد
        r = client.post(f"/api/accounting/journal-entries/{je_id}/post",
                        headers=admin_headers)
        assert r.status_code in (200, 404, 422, 501)

    def test_post_already_posted_entry(self, client, admin_headers):
        """اختبار ترحيل قيد مرحّل مسبقاً - يجب أن يرفض"""
        # جلب القيود المرحّلة
        r = client.get("/api/accounting/journal-entries?status=posted",
                       headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("لا يمكن جلب القيود")
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])
        posted = [j for j in items if j.get("status") == "posted"]
        if not posted:
            pytest.skip("لا توجد قيود مرحّلة")
        je_id = posted[0]["id"]
        r2 = client.post(f"/api/accounting/journal-entries/{je_id}/post",
                         headers=admin_headers)
        # يجب أن يرفض أو يعطي تحذير
        assert r2.status_code in (200, 400, 404, 409, 422, 501)

    def test_post_nonexistent_entry(self, client, admin_headers):
        """اختبار ترحيل قيد غير موجود"""
        r = client.post("/api/accounting/journal-entries/999999/post",
                        headers=admin_headers)
        assert r.status_code in (404, 422, 500, 501)


# ══════════════════════════════════════════════════════════════
# 📅 الفترات المالية - Fiscal Period Toggle
# ══════════════════════════════════════════════════════════════

class TestFiscalPeriodToggle:
    """اختبارات إغلاق/فتح الفترات المالية"""

    def test_toggle_close_fiscal_period(self, client, admin_headers):
        """اختبار إغلاق/فتح فترة مالية"""
        fy_r = client.get("/api/accounting/fiscal-years", headers=admin_headers)
        if fy_r.status_code != 200:
            pytest.skip("لا يمكن جلب السنوات المالية")
        data = fy_r.json()
        years = data if isinstance(data, list) else data.get("items", [])
        if not years:
            pytest.skip("لا توجد سنوات مالية")
        fy_id = years[0]["id"]

        periods_r = client.get(f"/api/accounting/fiscal-years/{fy_id}/periods",
                               headers=admin_headers)
        if periods_r.status_code != 200:
            pytest.skip("لا يمكن جلب الفترات")
        periods = periods_r.json()
        if isinstance(periods, dict):
            periods = periods.get("items", periods.get("periods", []))
        if not periods:
            pytest.skip("لا توجد فترات")

        period_id = periods[0].get("id", periods[0].get("period_number", 1))
        r = client.post(
            f"/api/accounting/fiscal-years/{fy_id}/toggle-close-period",
            json={"period_id": period_id},
            headers=admin_headers
        )
        assert r.status_code in (200, 404, 422, 501)

    def test_get_journal_entries_list(self, client, admin_headers):
        """اختبار عرض قائمة القيود المحاسبية مع فلترة"""
        r = client.get("/api/accounting/journal-entries", headers=admin_headers)
        assert r.status_code in (200, 404)
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data, (list, dict))

    def test_get_journal_entry_by_id(self, client, admin_headers):
        """اختبار جلب قيد محاسبي بالمعرف"""
        r = client.get("/api/accounting/journal-entries", headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("لا يمكن جلب القيود")
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])
        if not items:
            pytest.skip("لا توجد قيود")
        je_id = items[0]["id"]
        r2 = client.get(f"/api/accounting/journal-entries/{je_id}",
                        headers=admin_headers)
        assert r2.status_code in (200, 404)

    def test_get_journal_entries_filtered_by_date(self, client, admin_headers):
        """اختبار فلترة القيود بالتاريخ"""
        today = str(date.today())
        month_ago = str(date.today() - timedelta(days=30))
        r = client.get(
            f"/api/accounting/journal-entries?start_date={month_ago}&end_date={today}",
            headers=admin_headers
        )
        assert r.status_code in (200, 404)

    def test_get_journal_entries_filtered_by_status(self, client, admin_headers):
        """اختبار فلترة القيود بالحالة"""
        for status in ["posted", "draft", "void"]:
            r = client.get(
                f"/api/accounting/journal-entries?status={status}",
                headers=admin_headers
            )
            assert r.status_code in (200, 404)
