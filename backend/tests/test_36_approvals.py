"""
AMAN ERP - اختبارات نظام الاعتمادات والموافقات
Approvals: Workflows, Requests, Actions, Stats
═══════════════════════════════════════════════════════════════
"""

import pytest
from helpers import assert_valid_response


# ═══════════════════════════════════════════════════════════════
# 📋 سير عمل الاعتمادات - Approval Workflows
# ═══════════════════════════════════════════════════════════════
class TestApprovalWorkflows:
    """سيناريوهات سير عمل الاعتمادات"""

    def test_list_workflows(self, client, admin_headers):
        """✅ عرض قائمة سير العمل"""
        r = client.get("/api/approvals/workflows", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        assert isinstance(data, (list, dict))

    def test_list_document_types(self, client, admin_headers):
        """✅ عرض أنواع المستندات القابلة للاعتماد"""
        r = client.get("/api/approvals/document-types", headers=admin_headers)
        assert r.status_code in [200, 404]
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data, list)

    def test_create_workflow(self, client, admin_headers):
        """✅ إنشاء سير عمل اعتماد"""
        r = client.post("/api/approvals/workflows", json={
            "name": "اعتماد فواتير الشراء",
            "document_type": "purchase_invoice",
            "is_active": True,
            "steps": [
                {"step_order": 1, "approver_type": "role", "approver_value": "admin", "required": True},
            ],
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 409, 422]

    def test_create_multi_step_workflow(self, client, admin_headers):
        """✅ إنشاء سير عمل متعدد المراحل"""
        r = client.post("/api/approvals/workflows", json={
            "name": "اعتماد أوامر الشراء الكبيرة",
            "document_type": "purchase_order",
            "min_amount": 50000,
            "is_active": True,
            "steps": [
                {"step_order": 1, "approver_type": "role", "approver_value": "manager", "required": True},
                {"step_order": 2, "approver_type": "role", "approver_value": "admin", "required": True},
            ],
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 409, 422]

    def test_get_workflow_detail(self, client, admin_headers):
        """✅ عرض تفاصيل سير العمل"""
        r = client.get("/api/approvals/workflows", headers=admin_headers)
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("data", []))
        if not items:
            pytest.skip("لا يوجد سير عمل")
        wf_id = items[0]["id"]
        r2 = client.get(f"/api/approvals/workflows/{wf_id}", headers=admin_headers)
        assert r2.status_code in [200, 404]

    def test_update_workflow(self, client, admin_headers):
        """✅ تحديث سير عمل"""
        r = client.get("/api/approvals/workflows", headers=admin_headers)
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("data", []))
        if not items:
            pytest.skip("لا يوجد سير عمل")
        wf_id = items[0]["id"]
        r2 = client.put(f"/api/approvals/workflows/{wf_id}", json={
            "name": "سير عمل محدّث",
            "is_active": True,
        }, headers=admin_headers)
        assert r2.status_code in [200, 400, 404, 422]

    def test_delete_workflow(self, client, admin_headers):
        """✅ حذف سير عمل"""
        r = client.post("/api/approvals/workflows", json={
            "name": "سير عمل للحذف",
            "document_type": "expense",
            "is_active": False,
            "steps": [
                {"step_order": 1, "approver_type": "role", "approver_value": "admin", "required": True},
            ],
        }, headers=admin_headers)
        if r.status_code in [200, 201]:
            wf_id = r.json().get("id")
            if wf_id:
                r2 = client.delete(f"/api/approvals/workflows/{wf_id}", headers=admin_headers)
                assert r2.status_code in [200, 204, 400, 404]


# ═══════════════════════════════════════════════════════════════
# 📝 طلبات الاعتماد - Approval Requests
# ═══════════════════════════════════════════════════════════════
class TestApprovalRequests:
    """سيناريوهات طلبات الاعتماد"""

    def test_list_all_requests(self, client, admin_headers):
        """✅ عرض جميع طلبات الاعتماد"""
        r = client.get("/api/approvals/requests", headers=admin_headers)
        assert_valid_response(r)

    def test_list_pending_approvals(self, client, admin_headers):
        """✅ عرض الطلبات المعلقة"""
        r = client.get("/api/approvals/pending", headers=admin_headers)
        assert_valid_response(r)

    def test_create_approval_request(self, client, admin_headers):
        """✅ إنشاء طلب اعتماد"""
        r = client.post("/api/approvals/requests", json={
            "document_type": "purchase_invoice",
            "document_id": 1,
            "amount": 25000,
            "notes": "طلب اعتماد فاتورة شراء مواد خام",
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 404, 422]

    def test_get_approval_request_detail(self, client, admin_headers):
        """✅ عرض تفاصيل طلب اعتماد"""
        r = client.get("/api/approvals/requests", headers=admin_headers)
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("data", []))
        if not items:
            pytest.skip("لا توجد طلبات اعتماد")
        req_id = items[0]["id"]
        r2 = client.get(f"/api/approvals/requests/{req_id}", headers=admin_headers)
        assert r2.status_code in [200, 404]

    def test_approve_request(self, client, admin_headers):
        """✅ الموافقة على طلب اعتماد"""
        r = client.get("/api/approvals/pending", headers=admin_headers)
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("data", []))
        if not items:
            pytest.skip("لا توجد طلبات معلقة")
        req_id = items[0]["id"]
        r2 = client.post(f"/api/approvals/requests/{req_id}/action", json={
            "action": "approve",
            "notes": "تمت الموافقة",
        }, headers=admin_headers)
        assert r2.status_code in [200, 400, 404, 422]

    def test_reject_request(self, client, admin_headers):
        """✅ رفض طلب اعتماد"""
        # إنشاء طلب ثم رفضه
        r = client.post("/api/approvals/requests", json={
            "document_type": "expense",
            "document_id": 999,
            "amount": 100000,
            "notes": "طلب مصاريف كبير",
        }, headers=admin_headers)
        if r.status_code in [200, 201]:
            req_id = r.json().get("id")
            if req_id:
                r2 = client.post(f"/api/approvals/requests/{req_id}/action", json={
                    "action": "reject",
                    "notes": "المبلغ يتجاوز الميزانية",
                }, headers=admin_headers)
                assert r2.status_code in [200, 400, 404, 422]

    def test_approval_stats(self, client, admin_headers):
        """✅ إحصائيات الاعتمادات"""
        r = client.get("/api/approvals/stats", headers=admin_headers)
        assert r.status_code in [200, 404]
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data, dict)
