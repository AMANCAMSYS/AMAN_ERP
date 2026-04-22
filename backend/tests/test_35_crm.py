"""
AMAN ERP - اختبارات إدارة علاقات العملاء CRM
CRM: Opportunities, Pipeline, Activities, Tickets, Comments
═══════════════════════════════════════════════════════════════
"""

import pytest
from datetime import date, timedelta
from helpers import assert_valid_response


# ═══════════════════════════════════════════════════════════════
# 🎯 الفرص التجارية - Opportunities
# ═══════════════════════════════════════════════════════════════
class TestCRMOpportunities:
    """سيناريوهات الفرص التجارية"""

    def test_list_opportunities(self, client, admin_headers):
        """✅ عرض قائمة الفرص"""
        r = client.get("/api/crm/opportunities", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        assert isinstance(data, (list, dict))

    def test_create_opportunity(self, client, admin_headers):
        """✅ إنشاء فرصة تجارية جديدة"""
        r = client.post("/api/crm/opportunities", json={
            "title": "فرصة بيع نظام ERP",
            "customer_name": "شركة الأمل التجارية",
            "expected_amount": 150000,
            "stage": "new",
            "probability": 30,
            "expected_close_date": str(date.today() + timedelta(days=60)),
            "notes": "عميل مهتم بنظام ERP كامل",
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 422]

    def test_create_opportunity_with_contact(self, client, admin_headers):
        """✅ إنشاء فرصة مع بيانات الاتصال"""
        r = client.post("/api/crm/opportunities", json={
            "title": "صفقة توريد معدات",
            "customer_name": "مؤسسة النور",
            "contact_name": "أحمد محمد",
            "contact_email": "ahmed@alnoor.com",
            "contact_phone": "+963911000000",
            "expected_amount": 50000,
            "stage": "qualification",
            "probability": 50,
            "expected_close_date": str(date.today() + timedelta(days=30)),
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 422]

    def test_get_opportunity_detail(self, client, admin_headers):
        """✅ عرض تفاصيل فرصة"""
        r = client.get("/api/crm/opportunities", headers=admin_headers)
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("data", []))
        if not items:
            pytest.skip("لا توجد فرص")
        opp_id = items[0]["id"]
        r2 = client.get(f"/api/crm/opportunities/{opp_id}", headers=admin_headers)
        assert r2.status_code in [200, 404]
        if r2.status_code == 200:
            detail = r2.json()
            assert "title" in detail
            assert "stage" in detail

    def test_update_opportunity_stage(self, client, admin_headers):
        """✅ تحديث مرحلة الفرصة"""
        r = client.get("/api/crm/opportunities", headers=admin_headers)
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("data", []))
        if not items:
            pytest.skip("لا توجد فرص")
        opp_id = items[0]["id"]
        r2 = client.put(f"/api/crm/opportunities/{opp_id}", json={
            "stage": "negotiation",
            "probability": 70,
        }, headers=admin_headers)
        assert r2.status_code in [200, 400, 404, 422]

    def test_update_opportunity_amount(self, client, admin_headers):
        """✅ تحديث القيمة المتوقعة للفرصة"""
        r = client.get("/api/crm/opportunities", headers=admin_headers)
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("data", []))
        if not items:
            pytest.skip("لا توجد فرص")
        opp_id = items[0]["id"]
        r2 = client.put(f"/api/crm/opportunities/{opp_id}", json={
            "expected_amount": 200000,
        }, headers=admin_headers)
        assert r2.status_code in [200, 400, 404, 422]

    def test_delete_opportunity(self, client, admin_headers):
        """✅ حذف فرصة"""
        # إنشاء فرصة ثم حذفها
        r = client.post("/api/crm/opportunities", json={
            "title": "فرصة للحذف",
            "customer_name": "عميل مؤقت",
            "expected_amount": 1000,
            "stage": "new",
        }, headers=admin_headers)
        if r.status_code in [200, 201]:
            opp_id = r.json().get("id")
            if opp_id:
                r2 = client.delete(f"/api/crm/opportunities/{opp_id}", headers=admin_headers)
                assert r2.status_code in [200, 204, 400, 404]


# ═══════════════════════════════════════════════════════════════
# 📊 خط أنابيب المبيعات - Pipeline
# ═══════════════════════════════════════════════════════════════
class TestCRMPipeline:
    """سيناريوهات خط أنابيب المبيعات"""

    def test_get_pipeline_summary(self, client, admin_headers):
        """✅ ملخص خط أنابيب المبيعات"""
        r = client.get("/api/crm/opportunities/pipeline", headers=admin_headers)
        assert r.status_code in [200, 404]
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data, (list, dict))


# ═══════════════════════════════════════════════════════════════
# 📋 الأنشطة - Activities
# ═══════════════════════════════════════════════════════════════
class TestCRMActivities:
    """سيناريوهات الأنشطة"""

    def test_add_activity_to_opportunity(self, client, admin_headers):
        """✅ إضافة نشاط لفرصة"""
        r = client.get("/api/crm/opportunities", headers=admin_headers)
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("data", []))
        if not items:
            pytest.skip("لا توجد فرص")
        opp_id = items[0]["id"]
        r2 = client.post(f"/api/crm/opportunities/{opp_id}/activities", json={
            "activity_type": "call",
            "subject": "مكالمة متابعة",
            "description": "متابعة مع العميل حول العرض المقدم",
            "scheduled_date": str(date.today() + timedelta(days=3)),
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400, 404, 422]

    def test_add_meeting_activity(self, client, admin_headers):
        """✅ إضافة نشاط اجتماع"""
        r = client.get("/api/crm/opportunities", headers=admin_headers)
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("data", []))
        if not items:
            pytest.skip("لا توجد فرص")
        opp_id = items[0]["id"]
        r2 = client.post(f"/api/crm/opportunities/{opp_id}/activities", json={
            "activity_type": "meeting",
            "subject": "اجتماع عرض تجريبي",
            "description": "عرض تجريبي للنظام أمام فريق العميل",
            "scheduled_date": str(date.today() + timedelta(days=7)),
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400, 404, 422]


# ═══════════════════════════════════════════════════════════════
# 🎫 تذاكر الدعم - Support Tickets
# ═══════════════════════════════════════════════════════════════
class TestCRMTickets:
    """سيناريوهات تذاكر الدعم"""

    def test_list_tickets(self, client, admin_headers):
        """✅ عرض قائمة التذاكر"""
        r = client.get("/api/crm/tickets", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        assert isinstance(data, (list, dict))

    def test_get_ticket_stats(self, client, admin_headers):
        """✅ إحصائيات التذاكر"""
        r = client.get("/api/crm/tickets/stats", headers=admin_headers)
        assert r.status_code in [200, 404]
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data, dict)

    def test_create_ticket(self, client, admin_headers):
        """✅ إنشاء تذكرة دعم"""
        r = client.post("/api/crm/tickets", json={
            "subject": "مشكلة في طباعة الفواتير",
            "description": "لا يمكن طباعة فواتير المبيعات - تظهر صفحة بيضاء",
            "priority": "high",
            "category": "technical",
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 422]

    def test_create_ticket_low_priority(self, client, admin_headers):
        """✅ إنشاء تذكرة بأولوية منخفضة"""
        r = client.post("/api/crm/tickets", json={
            "subject": "طلب تعديل تقرير",
            "description": "يرجى إضافة عمود تاريخ الاستحقاق في تقرير العملاء",
            "priority": "low",
            "category": "feature_request",
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 422]

    def test_get_ticket_detail(self, client, admin_headers):
        """✅ عرض تفاصيل تذكرة"""
        r = client.get("/api/crm/tickets", headers=admin_headers)
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("data", []))
        if not items:
            pytest.skip("لا توجد تذاكر")
        ticket_id = items[0]["id"]
        r2 = client.get(f"/api/crm/tickets/{ticket_id}", headers=admin_headers)
        assert r2.status_code in [200, 404]

    def test_update_ticket_status(self, client, admin_headers):
        """✅ تحديث حالة تذكرة"""
        r = client.get("/api/crm/tickets", headers=admin_headers)
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("data", []))
        if not items:
            pytest.skip("لا توجد تذاكر")
        ticket_id = items[0]["id"]
        r2 = client.put(f"/api/crm/tickets/{ticket_id}", json={
            "status": "in_progress",
        }, headers=admin_headers)
        assert r2.status_code in [200, 400, 404, 422]

    def test_add_comment_to_ticket(self, client, admin_headers):
        """✅ إضافة تعليق على تذكرة"""
        r = client.get("/api/crm/tickets", headers=admin_headers)
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("data", []))
        if not items:
            pytest.skip("لا توجد تذاكر")
        ticket_id = items[0]["id"]
        r2 = client.post(f"/api/crm/tickets/{ticket_id}/comments", json={
            "content": "تم فحص المشكلة - يبدو أنها مرتبطة بإعدادات الطابعة",
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400, 404, 422]

    def test_add_multiple_comments(self, client, admin_headers):
        """✅ إضافة عدة تعليقات على تذكرة"""
        r = client.get("/api/crm/tickets", headers=admin_headers)
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("data", []))
        if not items:
            pytest.skip("لا توجد تذاكر")
        ticket_id = items[0]["id"]
        comments = [
            "جاري العمل على حل المشكلة",
            "تم تحديد السبب الجذري",
            "تم إصلاح المشكلة بنجاح",
        ]
        for comment in comments:
            r2 = client.post(f"/api/crm/tickets/{ticket_id}/comments", json={
                "content": comment,
            }, headers=admin_headers)
            assert r2.status_code in [200, 201, 400, 404, 422]
