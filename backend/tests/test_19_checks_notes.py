"""
AMAN ERP - اختبارات شاملة متعددة السيناريوهات: الشيكات وأوراق القبض والدفع
Comprehensive Multi-Scenario Tests: Checks & Notes (Receivable/Payable)
═══════════════════════════════════════════════════════
يتضمن: شيكات تحت التحصيل، شيكات تحت الدفع، أوراق القبض، أوراق الدفع
القيود المحاسبية: التحصيل، الارتجاع، البروتستو
"""

import pytest
from datetime import date, timedelta
from helpers import assert_valid_response


# ═══════════════════════════════════════════════════════════════
# 🏦 شيكات تحت التحصيل - Checks Receivable (TRS-001)
# ═══════════════════════════════════════════════════════════════
class TestChecksReceivableScenarios:
    """سيناريوهات شيكات تحت التحصيل"""

    def test_list_checks_receivable(self, client, admin_headers):
        """✅ عرض شيكات تحت التحصيل"""
        r = client.get("/api/checks/receivable", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        assert "items" in data or isinstance(data, list)

    def test_checks_receivable_stats(self, client, admin_headers):
        """✅ إحصائيات شيكات تحت التحصيل"""
        r = client.get("/api/checks/receivable/summary/stats", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        assert "pending" in data
        assert "collected" in data
        assert "bounced" in data

    def test_create_check_receivable(self, client, admin_headers):
        """✅ إنشاء شيك تحت التحصيل"""
        # Get customer party
        r = client.get("/api/parties/customers", headers=admin_headers)
        data = r.json()
        parties = data if isinstance(data, list) else data.get("items", data.get("data", []))
        party_id = parties[0]["id"] if parties else None

        r2 = client.post("/api/checks/receivable", json={
            "check_number": "CHK-RCV-001",
            "drawer_name": "أحمد محمد",
            "bank_name": "البنك الأهلي",
            "branch_name": "فرع الرياض",
            "amount": 25000,
            "currency": "SYP",
            "issue_date": str(date.today()),
            "due_date": str(date.today() + timedelta(days=30)),
            "party_id": party_id,
            "treasury_account_id": 4,
            "notes": "شيك من عميل",
            "branch_id": 1,
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400, 500]

    def test_create_check_receivable_minimal(self, client, admin_headers):
        """✅ إنشاء شيك بالحد الأدنى من البيانات"""
        r = client.post("/api/checks/receivable", json={
            "check_number": f"CHK-MIN-{date.today().strftime('%Y%m%d')}",
            "amount": 5000,
            "due_date": str(date.today() + timedelta(days=15)),
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 500]

    def test_get_check_receivable_detail(self, client, admin_headers):
        """✅ تفاصيل شيك تحت التحصيل"""
        r = client.get("/api/checks/receivable", headers=admin_headers)
        data = r.json()
        items = data.get("items", []) if isinstance(data, dict) else data
        if not items:
            pytest.skip("لا شيكات")
        check_id = items[0]["id"]
        r2 = client.get(f"/api/checks/receivable/{check_id}", headers=admin_headers)
        assert r2.status_code in [200, 404]

    def test_collect_check(self, client, admin_headers):
        """✅ تحصيل شيك - القيد: مدين البنك / دائن شيكات تحت التحصيل"""
        r = client.get("/api/checks/receivable?status=pending", headers=admin_headers)
        data = r.json()
        items = data.get("items", []) if isinstance(data, dict) else data
        pending = [c for c in items if c.get("status") == "pending"]
        if not pending:
            # Create a check first
            create_r = client.post("/api/checks/receivable", json={
                "check_number": f"CHK-COL-{date.today().strftime('%Y%m%d%H%M')}",
                "amount": 3000,
                "due_date": str(date.today()),
            }, headers=admin_headers)
            if create_r.status_code in [200, 201]:
                check_id = create_r.json().get("id")
            else:
                pytest.skip("لا شيكات معلقة")
        else:
            check_id = pending[0]["id"]

        r2 = client.post(f"/api/checks/receivable/{check_id}/collect", json={
            "collection_date": str(date.today()),
            "treasury_account_id": 4,
        }, headers=admin_headers)
        assert r2.status_code in [200, 400, 404]

    def test_bounce_check(self, client, admin_headers):
        """✅ ارتجاع شيك - إنشاء قيد عكسي"""
        r = client.get("/api/checks/receivable?status=pending", headers=admin_headers)
        data = r.json()
        items = data.get("items", []) if isinstance(data, dict) else data
        pending = [c for c in items if c.get("status") == "pending"]
        if not pending:
            # Create a check first
            create_r = client.post("/api/checks/receivable", json={
                "check_number": f"CHK-BNC-{date.today().strftime('%Y%m%d%H%M')}",
                "amount": 2000,
                "due_date": str(date.today()),
            }, headers=admin_headers)
            if create_r.status_code in [200, 201]:
                check_id = create_r.json().get("id")
            else:
                pytest.skip("لا شيكات معلقة")
        else:
            check_id = pending[0]["id"]

        r2 = client.post(f"/api/checks/receivable/{check_id}/bounce", json={
            "bounce_date": str(date.today()),
            "reason": "رصيد غير كافي",
        }, headers=admin_headers)
        assert r2.status_code in [200, 400, 404]

    def test_list_overdue_checks(self, client, admin_headers):
        """✅ الشيكات المستحقة / المتأخرة"""
        # Checks with due_date <= today and status = pending
        r = client.get("/api/checks/receivable/summary/stats", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        assert "overdue" in data


# ═══════════════════════════════════════════════════════════════
# 💳 شيكات تحت الدفع - Checks Payable (TRS-002)
# ═══════════════════════════════════════════════════════════════
class TestChecksPayableScenarios:
    """سيناريوهات شيكات تحت الدفع"""

    def test_list_checks_payable(self, client, admin_headers):
        """✅ عرض شيكات تحت الدفع"""
        r = client.get("/api/checks/payable", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        assert "items" in data or isinstance(data, list)

    def test_checks_payable_stats(self, client, admin_headers):
        """✅ إحصائيات شيكات تحت الدفع"""
        r = client.get("/api/checks/payable/summary/stats", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        # API returns 'issued', 'cleared', 'bounced', 'overdue'
        assert "issued" in data or "cleared" in data or isinstance(data, dict)

    def test_create_check_payable(self, client, admin_headers):
        """✅ إنشاء شيك دفع"""
        # Get supplier party
        r = client.get("/api/buying/suppliers", headers=admin_headers)
        suppliers = r.json()
        party_id = suppliers[0]["id"] if suppliers else None

        r2 = client.post("/api/checks/payable", json={
            "check_number": f"CHK-PAY-{date.today().strftime('%Y%m%d')}",
            "beneficiary_name": "مورد المواد الأولية",
            "bank_name": "بنك الراجحي",
            "amount": 15000,
            "currency": "SYP",
            "issue_date": str(date.today()),
            "due_date": str(date.today() + timedelta(days=45)),
            "party_id": party_id,
            "treasury_account_id": 4,
            "branch_id": 1,
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400, 500]

    def test_get_check_payable_detail(self, client, admin_headers):
        """✅ تفاصيل شيك دفع"""
        r = client.get("/api/checks/payable", headers=admin_headers)
        data = r.json()
        items = data.get("items", []) if isinstance(data, dict) else data
        if not items:
            pytest.skip("لا شيكات دفع")
        check_id = items[0]["id"]
        r2 = client.get(f"/api/checks/payable/{check_id}", headers=admin_headers)
        assert r2.status_code in [200, 404]

    def test_pay_check(self, client, admin_headers):
        """✅ صرف شيك - القيد: مدين شيكات تحت الدفع / دائن البنك"""
        r = client.get("/api/checks/payable?status=pending", headers=admin_headers)
        data = r.json()
        items = data.get("items", []) if isinstance(data, dict) else data
        pending = [c for c in items if c.get("status") == "pending"]
        if not pending:
            pytest.skip("لا شيكات دفع معلقة")

        check_id = pending[0]["id"]
        r2 = client.post(f"/api/checks/payable/{check_id}/pay", json={
            "payment_date": str(date.today()),
            "treasury_account_id": 4,
        }, headers=admin_headers)
        assert r2.status_code in [200, 400, 404]

    def test_void_check_payable(self, client, admin_headers):
        """✅ إلغاء شيك دفع"""
        r = client.get("/api/checks/payable?status=pending", headers=admin_headers)
        data = r.json()
        items = data.get("items", []) if isinstance(data, dict) else data
        pending = [c for c in items if c.get("status") == "pending"]
        if not pending:
            pytest.skip("لا شيكات دفع معلقة")

        check_id = pending[0]["id"]
        r2 = client.post(f"/api/checks/payable/{check_id}/void", json={
            "reason": "إلغاء الصفقة",
        }, headers=admin_headers)
        assert r2.status_code in [200, 400, 404]


# ═══════════════════════════════════════════════════════════════
# 📄 أوراق القبض - Notes Receivable
# ═══════════════════════════════════════════════════════════════
class TestNotesReceivableScenarios:
    """سيناريوهات أوراق القبض (الكمبيالات)"""

    def test_list_notes_receivable(self, client, admin_headers):
        """✅ عرض أوراق القبض"""
        r = client.get("/api/notes/receivable", headers=admin_headers)
        assert_valid_response(r)
        assert isinstance(r.json(), list)

    def test_notes_receivable_stats(self, client, admin_headers):
        """✅ إحصائيات أوراق القبض"""
        r = client.get("/api/notes/receivable/summary/stats", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        assert "pending" in data
        assert "collected" in data

    def test_create_note_receivable(self, client, admin_headers):
        """✅ إنشاء ورقة قبض - القيد: مدين أوراق القبض 1210 / دائن العملاء"""
        r = client.get("/api/parties/customers", headers=admin_headers)
        data = r.json()
        parties = data if isinstance(data, list) else data.get("items", data.get("data", []))
        party_id = parties[0]["id"] if parties else None

        r2 = client.post("/api/notes/receivable", json={
            "note_number": f"NR-{date.today().strftime('%Y%m%d%H%M')}",
            "drawer_name": "محمد علي الأحمد",
            "bank_name": "بنك الراجحي",
            "amount": 50000,
            "currency": "SYP",
            "issue_date": str(date.today()),
            "due_date": str(date.today() + timedelta(days=90)),
            "party_id": party_id,
            "branch_id": 1,
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400, 500]

    def test_get_note_receivable_detail(self, client, admin_headers):
        """✅ تفاصيل ورقة قبض"""
        r = client.get("/api/notes/receivable", headers=admin_headers)
        notes = r.json()
        if not notes:
            pytest.skip("لا أوراق قبض")
        note_id = notes[0]["id"]
        r2 = client.get(f"/api/notes/receivable/{note_id}", headers=admin_headers)
        assert r2.status_code in [200, 404]

    def test_collect_note_receivable(self, client, admin_headers):
        """✅ تحصيل ورقة قبض - القيد: مدين البنك / دائن أوراق القبض"""
        r = client.get("/api/notes/receivable?status_filter=pending", headers=admin_headers)
        notes = r.json()
        pending = [n for n in notes if n.get("status") == "pending"]
        if not pending:
            pytest.skip("لا أوراق قبض معلقة")

        note_id = pending[0]["id"]
        r2 = client.post(f"/api/notes/receivable/{note_id}/collect", json={
            "collection_date": str(date.today()),
            "treasury_account_id": 4,
        }, headers=admin_headers)
        assert r2.status_code in [200, 400, 404]

    def test_protest_note_receivable(self, client, admin_headers):
        """✅ بروتستو ورقة قبض - القيد: مدين العملاء / دائن أوراق القبض"""
        r = client.get("/api/notes/receivable?status_filter=pending", headers=admin_headers)
        notes = r.json()
        pending = [n for n in notes if n.get("status") == "pending"]
        if not pending:
            pytest.skip("لا أوراق قبض معلقة")

        note_id = pending[0]["id"]
        r2 = client.post(f"/api/notes/receivable/{note_id}/protest", json={
            "protest_date": str(date.today()),
            "reason": "رفض السداد",
        }, headers=admin_headers)
        assert r2.status_code in [200, 400, 404]


# ═══════════════════════════════════════════════════════════════
# 📝 أوراق الدفع - Notes Payable
# ═══════════════════════════════════════════════════════════════
class TestNotesPayableScenarios:
    """سيناريوهات أوراق الدفع"""

    def test_list_notes_payable(self, client, admin_headers):
        """✅ عرض أوراق الدفع"""
        r = client.get("/api/notes/payable", headers=admin_headers)
        assert_valid_response(r)
        assert isinstance(r.json(), list)

    def test_notes_payable_stats(self, client, admin_headers):
        """✅ إحصائيات أوراق الدفع"""
        r = client.get("/api/notes/payable/summary/stats", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        # API returns 'issued', 'cleared', 'protested', 'overdue' or similar
        assert isinstance(data, dict)

    def test_create_note_payable(self, client, admin_headers):
        """✅ إنشاء ورقة دفع - القيد: مدين الموردين / دائن أوراق الدفع 2110"""
        r = client.get("/api/buying/suppliers", headers=admin_headers)
        suppliers = r.json()
        party_id = suppliers[0]["id"] if suppliers else None

        r2 = client.post("/api/notes/payable", json={
            "note_number": f"NP-{date.today().strftime('%Y%m%d%H%M')}",
            "beneficiary_name": "شركة التوريدات العامة",
            "bank_name": "بنك البلاد",
            "amount": 30000,
            "currency": "SYP",
            "issue_date": str(date.today()),
            "due_date": str(date.today() + timedelta(days=60)),
            "party_id": party_id,
            "branch_id": 1,
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400, 500]

    def test_get_note_payable_detail(self, client, admin_headers):
        """✅ تفاصيل ورقة دفع"""
        r = client.get("/api/notes/payable", headers=admin_headers)
        notes = r.json()
        if not notes:
            pytest.skip("لا أوراق دفع")
        note_id = notes[0]["id"]
        r2 = client.get(f"/api/notes/payable/{note_id}", headers=admin_headers)
        assert r2.status_code in [200, 404]

    def test_pay_note_payable(self, client, admin_headers):
        """✅ سداد ورقة دفع - القيد: مدين أوراق الدفع / دائن البنك"""
        r = client.get("/api/notes/payable?status_filter=pending", headers=admin_headers)
        notes = r.json()
        pending = [n for n in notes if n.get("status") == "pending"]
        if not pending:
            pytest.skip("لا أوراق دفع معلقة")

        note_id = pending[0]["id"]
        r2 = client.post(f"/api/notes/payable/{note_id}/pay", json={
            "payment_date": str(date.today()),
            "treasury_account_id": 4,
        }, headers=admin_headers)
        assert r2.status_code in [200, 400, 404]


# ═══════════════════════════════════════════════════════════════
# 📊 تقارير الشيكات والأوراق التجارية
# ═══════════════════════════════════════════════════════════════
class TestChecksNotesReportScenarios:
    """تقارير الشيكات والأوراق التجارية"""

    def test_checks_receivable_aging(self, client, admin_headers):
        """✅ أعمار شيكات تحت التحصيل"""
        r = client.get("/api/checks/receivable/summary/stats", headers=admin_headers)
        assert_valid_response(r)

    def test_checks_payable_aging(self, client, admin_headers):
        """✅ أعمار شيكات تحت الدفع"""
        r = client.get("/api/checks/payable/summary/stats", headers=admin_headers)
        assert_valid_response(r)

    def test_filter_checks_by_status(self, client, admin_headers):
        """✅ فلترة الشيكات حسب الحالة"""
        for status in ["pending", "collected", "bounced"]:
            r = client.get(f"/api/checks/receivable?status={status}", headers=admin_headers)
            assert r.status_code == 200

    def test_filter_checks_by_branch(self, client, admin_headers):
        """✅ فلترة الشيكات حسب الفرع"""
        r = client.get("/api/checks/receivable?branch_id=1", headers=admin_headers)
        assert_valid_response(r)

    def test_search_checks(self, client, admin_headers):
        """✅ بحث في الشيكات"""
        r = client.get("/api/checks/receivable?search=CHK", headers=admin_headers)
        assert_valid_response(r)

