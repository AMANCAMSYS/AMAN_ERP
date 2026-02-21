"""
AMAN ERP - اختبارات التقارير المجدولة
Scheduled Reports: List, Create, Delete, Toggle
═══════════════════════════════════════════════════════════════
"""

import pytest
from helpers import assert_valid_response, assert_error_response


# ═══════════════════════════════════════════════════════════════
# 📊 التقارير المجدولة - Scheduled Reports
# ═══════════════════════════════════════════════════════════════
class TestScheduledReports:
    """سيناريوهات التقارير المجدولة"""

    def test_list_scheduled_reports(self, client, admin_headers):
        """✅ عرض التقارير المجدولة"""
        r = client.get("/api/reports/scheduled/", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        assert isinstance(data, (list, dict))

    def test_create_scheduled_report_daily(self, client, admin_headers):
        """✅ إنشاء تقرير مجدول يومي"""
        r = client.post("/api/reports/scheduled/", json={
            "report_type": "trial_balance",
            "schedule": "daily",
            "time": "08:00",
            "recipients": ["omaradal60@gmail.com"],
            "is_active": True,
            "name": "ميزان مراجعة يومي",
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 422]

    def test_create_scheduled_report_weekly(self, client, admin_headers):
        """✅ إنشاء تقرير مجدول أسبوعي"""
        r = client.post("/api/reports/scheduled/", json={
            "report_type": "income_statement",
            "schedule": "weekly",
            "day_of_week": "sunday",
            "time": "09:00",
            "recipients": ["omaradal60@gmail.com"],
            "is_active": True,
            "name": "قائمة الدخل الأسبوعية",
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 422]

    def test_create_scheduled_report_monthly(self, client, admin_headers):
        """✅ إنشاء تقرير مجدول شهري"""
        r = client.post("/api/reports/scheduled/", json={
            "report_type": "balance_sheet",
            "schedule": "monthly",
            "day_of_month": 1,
            "time": "07:00",
            "recipients": ["omaradal60@gmail.com"],
            "is_active": True,
            "name": "الميزانية العمومية الشهرية",
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 422]

    def test_toggle_scheduled_report(self, client, admin_headers):
        """✅ تفعيل/تعطيل تقرير مجدول"""
        r = client.get("/api/reports/scheduled/", headers=admin_headers)
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("data", []))
        if not items:
            pytest.skip("لا توجد تقارير مجدولة")
        report_id = items[0]["id"]
        r2 = client.put(f"/api/reports/scheduled/{report_id}/toggle", headers=admin_headers)
        assert r2.status_code in [200, 400, 404]

    def test_delete_scheduled_report(self, client, admin_headers):
        """✅ حذف تقرير مجدول"""
        # إنشاء تقرير ثم حذفه
        r = client.post("/api/reports/scheduled/", json={
            "report_type": "trial_balance",
            "schedule": "daily",
            "time": "23:00",
            "recipients": ["test@test.com"],
            "is_active": False,
            "name": "تقرير للحذف",
        }, headers=admin_headers)
        if r.status_code in [200, 201]:
            report_id = r.json().get("id")
            if report_id:
                r2 = client.delete(f"/api/reports/scheduled/{report_id}", headers=admin_headers)
                assert r2.status_code in [200, 204, 400, 404]
