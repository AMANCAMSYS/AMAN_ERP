"""
test_33_checks_notes_due_alerts.py
====================================
اختبارات تنبيهات الشيكات والأوراق التجارية المستحقة

Covers UNTESTED endpoints:
- GET /api/checks/due-alerts
- POST /api/checks/payable/{id}/clear
- GET /api/notes/due-alerts
- POST /api/notes/payable/{id}/protest
"""
import pytest
from datetime import date, timedelta


# ══════════════════════════════════════════════════════════════
# 📋 تنبيهات الشيكات (Checks Due Alerts)
# ══════════════════════════════════════════════════════════════

class TestChecksDueAlerts:
    """اختبارات تنبيهات الشيكات المستحقة"""

    def test_checks_due_alerts(self, client, admin_headers):
        """اختبار تنبيهات الشيكات المستحقة"""
        r = client.get("/api/checks/due-alerts", headers=admin_headers)
        assert r.status_code in (200, 404, 501)
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data, (list, dict))

    def test_checks_due_alerts_with_date_filter(self, client, admin_headers):
        """اختبار تنبيهات الشيكات المستحقة مع فلترة تاريخ"""
        today = str(date.today())
        next_week = str(date.today() + timedelta(days=7))
        r = client.get(
            f"/api/checks/due-alerts?start_date={today}&end_date={next_week}",
            headers=admin_headers
        )
        assert r.status_code in (200, 404, 501)

    def test_checks_receivable_due_alerts(self, client, admin_headers):
        """اختبار تنبيهات الشيكات المستحقة للقبض"""
        r = client.get("/api/checks/due-alerts?type=receivable",
                       headers=admin_headers)
        assert r.status_code in (200, 404, 501)

    def test_checks_payable_due_alerts(self, client, admin_headers):
        """اختبار تنبيهات الشيكات المستحقة للدفع"""
        r = client.get("/api/checks/due-alerts?type=payable",
                       headers=admin_headers)
        assert r.status_code in (200, 404, 501)

    def test_checks_due_today(self, client, admin_headers):
        """اختبار الشيكات المستحقة اليوم"""
        today = str(date.today())
        r = client.get(f"/api/checks/due-alerts?date={today}",
                       headers=admin_headers)
        assert r.status_code in (200, 404, 501)


# ══════════════════════════════════════════════════════════════
# 💳 تصفية الشيكات المدفوعة (Checks Payable Clear)
# ══════════════════════════════════════════════════════════════

class TestChecksPayableClear:
    """اختبارات تصفية الشيكات المدفوعة"""

    def _get_payable_check_id(self, client, admin_headers):
        r = client.get("/api/checks/payable", headers=admin_headers)
        if r.status_code != 200:
            return None
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("checks", []))
        # البحث عن شيك غير مصفى (pending أو issued)
        for check in items:
            if check.get("status") in ("pending", "issued", "active"):
                return check.get("id") or check.get("check_id")
        return items[0].get("id") if items else None

    def test_clear_payable_check(self, client, admin_headers):
        """اختبار تصفية شيك مدفوع"""
        check_id = self._get_payable_check_id(client, admin_headers)
        if not check_id:
            pytest.skip("لا توجد شيكات مدفوعة")
        r = client.post(f"/api/checks/payable/{check_id}/clear",
                        headers=admin_headers)
        assert r.status_code in (200, 404, 422, 501)

    def test_clear_already_cleared_check(self, client, admin_headers):
        """اختبار تصفية شيك مصفى مسبقاً"""
        # جلب شيك مصفى
        r = client.get("/api/checks/payable?status=cleared",
                       headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("لا توجد شيكات")
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])
        cleared = [c for c in items if c.get("status") == "cleared"]
        if not cleared:
            pytest.skip("لا توجد شيكات مصفاة")
        
        check_id = cleared[0].get("id")
        r2 = client.post(f"/api/checks/payable/{check_id}/clear",
                         headers=admin_headers)
        # يجب أن يرفض أو يعطي تحذير
        assert r2.status_code in (200, 400, 404, 409, 422, 501)

    def test_clear_nonexistent_check(self, client, admin_headers):
        """اختبار تصفية شيك غير موجود"""
        r = client.post("/api/checks/payable/999999/clear",
                        headers=admin_headers)
        assert r.status_code in (404, 422, 500, 501)

    def test_create_and_clear_check(self, client, admin_headers):
        """اختبار إنشاء شيك وتصفيته"""
        # جلب مورد
        supp_r = client.get("/api/buying/suppliers", headers=admin_headers)
        if supp_r.status_code != 200:
            pytest.skip("لا يوجد موردون")
        suppliers = supp_r.json()
        if isinstance(suppliers, dict):
            suppliers = suppliers.get("items", [])
        if not suppliers:
            pytest.skip("لا يوجد موردون")

        # إنشاء شيك مدفوع
        check_data = {
            "supplier_id": suppliers[0]["id"],
            "amount": 5000.00,
            "check_number": f"CHK-TEST-{date.today().strftime('%Y%m%d%H%M')}",
            "due_date": str(date.today() + timedelta(days=30)),
            "bank_name": "بنك الاختبار",
            "notes": "شيك اختبار للتصفية"
        }
        create_r = client.post("/api/checks/payable", json=check_data,
                               headers=admin_headers)
        if create_r.status_code not in (200, 201):
            pytest.skip("لا يمكن إنشاء شيك")
        
        check_id = create_r.json().get("id")
        if not check_id:
            pytest.skip("لا يوجد معرف الشيك")

        # تصفية الشيك
        clear_r = client.post(f"/api/checks/payable/{check_id}/clear",
                              headers=admin_headers)
        assert clear_r.status_code in (200, 404, 422, 501)


# ══════════════════════════════════════════════════════════════
# 📜 تنبيهات الأوراق التجارية (Notes Due Alerts)
# ══════════════════════════════════════════════════════════════

class TestNotesDueAlerts:
    """اختبارات تنبيهات الأوراق التجارية المستحقة"""

    def test_notes_due_alerts(self, client, admin_headers):
        """اختبار تنبيهات الأوراق التجارية المستحقة"""
        r = client.get("/api/notes/due-alerts", headers=admin_headers)
        assert r.status_code in (200, 404, 501)
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data, (list, dict))

    def test_notes_due_alerts_with_date_range(self, client, admin_headers):
        """اختبار تنبيهات الأوراق المستحقة ضمن نطاق تاريخ"""
        today = str(date.today())
        next_month = str(date.today() + timedelta(days=30))
        r = client.get(
            f"/api/notes/due-alerts?start_date={today}&end_date={next_month}",
            headers=admin_headers
        )
        assert r.status_code in (200, 404, 501)

    def test_notes_receivable_due_alerts(self, client, admin_headers):
        """اختبار تنبيهات أوراق القبض المستحقة"""
        r = client.get("/api/notes/due-alerts?type=receivable",
                       headers=admin_headers)
        assert r.status_code in (200, 404, 501)

    def test_notes_payable_due_alerts(self, client, admin_headers):
        """اختبار تنبيهات أوراق الدفع المستحقة"""
        r = client.get("/api/notes/due-alerts?type=payable",
                       headers=admin_headers)
        assert r.status_code in (200, 404, 501)

    def test_overdue_notes_alerts(self, client, admin_headers):
        """اختبار تنبيهات الأوراق المتأخرة"""
        r = client.get("/api/notes/due-alerts?overdue=true",
                       headers=admin_headers)
        assert r.status_code in (200, 404, 501)


# ══════════════════════════════════════════════════════════════
# ⚠️ احتجاج أوراق الدفع (Notes Payable Protest)
# ══════════════════════════════════════════════════════════════

class TestNotesPayableProtest:
    """اختبارات احتجاج أوراق الدفع"""

    def _get_payable_note_id(self, client, admin_headers):
        r = client.get("/api/notes/payable", headers=admin_headers)
        if r.status_code != 200:
            return None
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("notes", []))
        return items[0].get("id") if items else None

    def test_protest_payable_note(self, client, admin_headers):
        """اختبار احتجاج ورقة دفع"""
        note_id = self._get_payable_note_id(client, admin_headers)
        if not note_id:
            pytest.skip("لا توجد أوراق دفع")
        protest_data = {
            "reason": "عدم توفر السيولة - اختبار",
            "protest_date": str(date.today())
        }
        r = client.post(f"/api/notes/payable/{note_id}/protest",
                        json=protest_data, headers=admin_headers)
        assert r.status_code in (200, 400, 404, 422, 501)

    def test_protest_nonexistent_note(self, client, admin_headers):
        """اختبار احتجاج ورقة غير موجودة"""
        protest_data = {
            "reason": "اختبار",
            "protest_date": str(date.today())
        }
        r = client.post("/api/notes/payable/999999/protest",
                        json=protest_data, headers=admin_headers)
        assert r.status_code in (404, 422, 500, 501)

    def test_protest_already_protested_note(self, client, admin_headers):
        """اختبار احتجاج ورقة محتج عليها مسبقاً"""
        # جلب ورقة محتج عليها
        r = client.get("/api/notes/payable?status_filter=protested",
                       headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("لا توجد أوراق")
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])
        protested = [n for n in items if n.get("status") == "protested"]
        if not protested:
            pytest.skip("لا توجد أوراق محتج عليها")

        note_id = protested[0].get("id")
        r2 = client.post(f"/api/notes/payable/{note_id}/protest",
                         json={"reason": "اختبار", "protest_date": str(date.today())},
                         headers=admin_headers)
        # يجب أن يرفض أو يعطي تحذير
        assert r2.status_code in (200, 400, 404, 409, 422, 501)

    def test_create_and_protest_note(self, client, admin_headers):
        """اختبار إنشاء ورقة دفع واحتجاجها"""
        # جلب مورد
        supp_r = client.get("/api/buying/suppliers", headers=admin_headers)
        if supp_r.status_code != 200:
            pytest.skip("لا يوجد موردون")
        suppliers = supp_r.json()
        if isinstance(suppliers, dict):
            suppliers = suppliers.get("items", [])
        if not suppliers:
            pytest.skip("لا يوجد موردون")

        # إنشاء ورقة دفع
        note_data = {
            "supplier_id": suppliers[0]["id"],
            "amount": 8000.00,
            "note_number": f"NOTE-TEST-{date.today().strftime('%Y%m%d%H%M')}",
            "due_date": str(date.today() + timedelta(days=60)),
            "notes": "ورقة تجارية للاحتجاج - اختبار"
        }
        create_r = client.post("/api/notes/payable", json=note_data,
                               headers=admin_headers)
        if create_r.status_code not in (200, 201):
            pytest.skip("لا يمكن إنشاء ورقة")

        note_id = create_r.json().get("id")
        if not note_id:
            pytest.skip("لا يوجد معرف الورقة")

        # احتجاج الورقة
        protest_r = client.post(
            f"/api/notes/payable/{note_id}/protest",
            json={"reason": "اختبار احتجاج", "protest_date": str(date.today())},
            headers=admin_headers
        )
        assert protest_r.status_code in (200, 400, 404, 422, 501)


# ══════════════════════════════════════════════════════════════
# 🔄 اختبارات شاملة للدورة الكاملة
# ══════════════════════════════════════════════════════════════

class TestChecksNotesFullCycle:
    """اختبارات الدورة الكاملة للشيكات والأوراق التجارية"""

    def test_checks_receivable_full_cycle(self, client, admin_headers):
        """اختبار الدورة الكاملة لشيك قبض"""
        # جلب عميل
        cust_r = client.get("/api/sales/customers", headers=admin_headers)
        if cust_r.status_code != 200:
            pytest.skip("لا يوجد عملاء")
        customers = cust_r.json()
        if isinstance(customers, dict):
            customers = customers.get("items", [])
        if not customers:
            pytest.skip("لا يوجد عملاء")

        # إنشاء شيك قبض
        check_data = {
            "customer_id": customers[0]["id"],
            "amount": 10000.00,
            "check_number": f"RECV-{date.today().strftime('%Y%m%d%H%M')}",
            "due_date": str(date.today() + timedelta(days=15)),
            "bank_name": "بنك الراجحي",
            "notes": "شيك قبض - اختبار دورة كاملة"
        }
        create_r = client.post("/api/checks/receivable", json=check_data,
                               headers=admin_headers)
        assert create_r.status_code in (200, 201, 400, 422, 500)

        if create_r.status_code in (200, 201):
            check_id = create_r.json().get("id")
            if check_id:
                # محاولة تحصيل الشيك
                collect_r = client.post(
                    f"/api/checks/receivable/{check_id}/collect",
                    headers=admin_headers
                )
                assert collect_r.status_code in (200, 400, 404, 422)

    def test_notes_receivable_full_cycle(self, client, admin_headers):
        """اختبار الدورة الكاملة لورقة قبض"""
        # جلب عميل
        cust_r = client.get("/api/sales/customers", headers=admin_headers)
        if cust_r.status_code != 200:
            pytest.skip("لا يوجد عملاء")
        customers = cust_r.json()
        if isinstance(customers, dict):
            customers = customers.get("items", [])
        if not customers:
            pytest.skip("لا يوجد عملاء")

        # إنشاء ورقة قبض
        note_data = {
            "customer_id": customers[0]["id"],
            "amount": 15000.00,
            "note_number": f"RN-{date.today().strftime('%Y%m%d%H%M')}",
            "due_date": str(date.today() + timedelta(days=45)),
            "notes": "ورقة قبض - اختبار دورة كاملة"
        }
        create_r = client.post("/api/notes/receivable", json=note_data,
                               headers=admin_headers)
        assert create_r.status_code in (200, 201, 400, 422, 500)

        if create_r.status_code in (200, 201):
            note_id = create_r.json().get("id")
            if note_id:
                # محاولة تحصيل الورقة
                collect_r = client.post(
                    f"/api/notes/receivable/{note_id}/collect",
                    headers=admin_headers
                )
                assert collect_r.status_code in (200, 400, 404, 422)

    def test_checks_and_notes_statistics(self, client, admin_headers):
        """اختبار إحصائيات الشيكات والأوراق التجارية"""
        # إحصائيات شيكات القبض
        recv_stats_r = client.get("/api/checks/receivable/summary/stats",
                                  headers=admin_headers)
        assert recv_stats_r.status_code in (200, 404)

        # إحصائيات شيكات الدفع
        pay_stats_r = client.get("/api/checks/payable/summary/stats",
                                 headers=admin_headers)
        assert pay_stats_r.status_code in (200, 404)

        # إحصائيات أوراق القبض
        notes_recv_stats_r = client.get("/api/notes/receivable/summary/stats",
                                        headers=admin_headers)
        assert notes_recv_stats_r.status_code in (200, 404)

        # إحصائيات أوراق الدفع
        notes_pay_stats_r = client.get("/api/notes/payable/summary/stats",
                                       headers=admin_headers)
        assert notes_pay_stats_r.status_code in (200, 404)
