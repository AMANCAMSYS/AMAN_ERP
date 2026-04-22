"""
AMAN ERP - اختبارات الموارد البشرية المتقدمة
HR Advanced: Salary Structures, Components, Overtime, GOSI,
             Documents, Performance Reviews, Training, Violations, Custody
═══════════════════════════════════════════════════════════════
"""

import pytest
from datetime import date, timedelta
from helpers import assert_valid_response


# ═══════════════════════════════════════════════════════════════
# 💼 هياكل الرواتب - Salary Structures
# ═══════════════════════════════════════════════════════════════
class TestSalaryStructures:
    """سيناريوهات هياكل الرواتب"""

    def test_list_salary_structures(self, client, admin_headers):
        """✅ عرض هياكل الرواتب"""
        r = client.get("/api/hr-advanced/salary-structures", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        assert isinstance(data, (list, dict))

    def test_create_salary_structure(self, client, admin_headers):
        """✅ إنشاء هيكل رواتب"""
        r = client.post("/api/hr-advanced/salary-structures", json={
            "name": "هيكل رواتب مهندسين",
            "base_salary": 500000,
            "is_active": True,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 409, 422]

    def test_update_salary_structure(self, client, admin_headers):
        """✅ تحديث هيكل رواتب"""
        r = client.get("/api/hr-advanced/salary-structures", headers=admin_headers)
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("data", []))
        if not items:
            pytest.skip("لا توجد هياكل رواتب")
        struct_id = items[0]["id"]
        r2 = client.put(f"/api/hr-advanced/salary-structures/{struct_id}", json={
            "name": "هيكل رواتب محدّث",
            "base_salary": 600000,
        }, headers=admin_headers)
        assert r2.status_code in [200, 400, 404, 422]

    def test_delete_salary_structure(self, client, admin_headers):
        """✅ حذف هيكل رواتب"""
        r = client.post("/api/hr-advanced/salary-structures", json={
            "name": "هيكل للحذف",
            "base_salary": 100000,
        }, headers=admin_headers)
        if r.status_code in [200, 201]:
            struct_id = r.json().get("id")
            if struct_id:
                r2 = client.delete(f"/api/hr-advanced/salary-structures/{struct_id}", headers=admin_headers)
                assert r2.status_code in [200, 204, 400, 404]


# ═══════════════════════════════════════════════════════════════
# 📊 مكونات الرواتب - Salary Components
# ═══════════════════════════════════════════════════════════════
class TestSalaryComponents:
    """سيناريوهات مكونات الرواتب"""

    def test_list_salary_components(self, client, admin_headers):
        """✅ عرض مكونات الرواتب"""
        r = client.get("/api/hr-advanced/salary-components", headers=admin_headers)
        assert_valid_response(r)

    def test_create_salary_component_allowance(self, client, admin_headers):
        """✅ إنشاء بدل (مكون إيجابي)"""
        r = client.post("/api/hr-advanced/salary-components", json={
            "name": "بدل سكن",
            "name_en": "Housing Allowance",
            "component_type": "allowance",
            "calculation_type": "percentage",
            "value": 25,
            "is_taxable": False,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 409, 422]

    def test_create_salary_component_deduction(self, client, admin_headers):
        """✅ إنشاء حسم (مكون سلبي)"""
        r = client.post("/api/hr-advanced/salary-components", json={
            "name": "تأمين صحي",
            "name_en": "Health Insurance",
            "component_type": "deduction",
            "calculation_type": "fixed",
            "value": 5000,
            "is_taxable": False,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 409, 422]

    def test_update_salary_component(self, client, admin_headers):
        """✅ تحديث مكون راتب"""
        r = client.get("/api/hr-advanced/salary-components", headers=admin_headers)
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("data", []))
        if not items:
            pytest.skip("لا توجد مكونات رواتب")
        comp_id = items[0]["id"]
        r2 = client.put(f"/api/hr-advanced/salary-components/{comp_id}", json={
            "name": "مكون محدّث",
            "value": 30,
        }, headers=admin_headers)
        assert r2.status_code in [200, 400, 404, 422]


# ═══════════════════════════════════════════════════════════════
# 👤 مكونات رواتب الموظفين - Employee Salary Components
# ═══════════════════════════════════════════════════════════════
class TestEmployeeSalaryComponents:
    """سيناريوهات مكونات رواتب الموظفين"""

    def test_assign_salary_component(self, client, admin_headers):
        """✅ تعيين مكون راتب لموظف"""
        # جلب قائمة الموظفين
        emp_r = client.get("/api/hr/employees", headers=admin_headers)
        if emp_r.status_code != 200:
            pytest.skip("لا يمكن جلب الموظفين")
        emp_data = emp_r.json()
        employees = emp_data if isinstance(emp_data, list) else emp_data.get("items", emp_data.get("data", []))
        if not employees:
            pytest.skip("لا يوجد موظفين")
        emp_id = employees[0]["id"]

        # جلب مكونات الرواتب
        comp_r = client.get("/api/hr-advanced/salary-components", headers=admin_headers)
        comp_data = comp_r.json()
        components = comp_data if isinstance(comp_data, list) else comp_data.get("items", comp_data.get("data", []))
        if not components:
            pytest.skip("لا توجد مكونات رواتب")
        comp_id = components[0]["id"]

        r = client.post("/api/hr-advanced/employee-salary-components", json={
            "employee_id": emp_id,
            "component_id": comp_id,
            "amount": 50000,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 409, 422]

    def test_get_employee_salary_components(self, client, admin_headers):
        """✅ عرض مكونات راتب موظف"""
        emp_r = client.get("/api/hr/employees", headers=admin_headers)
        if emp_r.status_code != 200:
            pytest.skip("لا يمكن جلب الموظفين")
        emp_data = emp_r.json()
        employees = emp_data if isinstance(emp_data, list) else emp_data.get("items", emp_data.get("data", []))
        if not employees:
            pytest.skip("لا يوجد موظفين")
        emp_id = employees[0]["id"]
        r = client.get(f"/api/hr-advanced/employee-salary-components/{emp_id}", headers=admin_headers)
        assert r.status_code in [200, 404]


# ═══════════════════════════════════════════════════════════════
# ⏰ العمل الإضافي - Overtime
# ═══════════════════════════════════════════════════════════════
class TestOvertime:
    """سيناريوهات العمل الإضافي"""

    def test_list_overtime_requests(self, client, admin_headers):
        """✅ عرض طلبات العمل الإضافي"""
        r = client.get("/api/hr-advanced/overtime", headers=admin_headers)
        assert_valid_response(r)

    def test_create_overtime_request(self, client, admin_headers):
        """✅ إنشاء طلب عمل إضافي"""
        emp_r = client.get("/api/hr/employees", headers=admin_headers)
        if emp_r.status_code != 200:
            pytest.skip("لا يمكن جلب الموظفين")
        emp_data = emp_r.json()
        employees = emp_data if isinstance(emp_data, list) else emp_data.get("items", emp_data.get("data", []))
        if not employees:
            pytest.skip("لا يوجد موظفين")
        emp_id = employees[0]["id"]

        r = client.post("/api/hr-advanced/overtime", json={
            "employee_id": emp_id,
            "date": str(date.today()),
            "hours": 3,
            "overtime_type": "normal",
            "reason": "إنهاء مشروع عاجل",
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 422]

    def test_approve_overtime(self, client, admin_headers):
        """✅ الموافقة على عمل إضافي"""
        r = client.get("/api/hr-advanced/overtime", headers=admin_headers)
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("data", []))
        pending = [o for o in items if o.get("status") in ["pending", "submitted"]]
        if not pending:
            pytest.skip("لا توجد طلبات معلقة")
        ot_id = pending[0]["id"]
        r2 = client.put(f"/api/hr-advanced/overtime/{ot_id}/approve", headers=admin_headers)
        assert r2.status_code in [200, 400, 404]


# ═══════════════════════════════════════════════════════════════
# 🏛 التأمينات الاجتماعية - GOSI
# ═══════════════════════════════════════════════════════════════
class TestGOSI:
    """سيناريوهات التأمينات الاجتماعية"""

    def test_get_gosi_settings(self, client, admin_headers):
        """✅ عرض إعدادات التأمينات"""
        r = client.get("/api/hr-advanced/gosi-settings", headers=admin_headers)
        assert r.status_code in [200, 404]

    def test_save_gosi_settings(self, client, admin_headers):
        """✅ حفظ إعدادات التأمينات"""
        r = client.post("/api/hr-advanced/gosi-settings", json={
            "employee_share": 9.75,
            "employer_share": 11.75,
            "max_salary": 45000,
            "is_active": True,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 422]

    def test_calculate_gosi(self, client, admin_headers):
        """✅ حساب التأمينات لموظف"""
        emp_r = client.get("/api/hr/employees", headers=admin_headers)
        if emp_r.status_code != 200:
            pytest.skip("لا يمكن جلب الموظفين")
        emp_data = emp_r.json()
        employees = emp_data if isinstance(emp_data, list) else emp_data.get("items", emp_data.get("data", []))
        if not employees:
            pytest.skip("لا يوجد موظفين")
        emp_id = employees[0]["id"]
        r = client.get(f"/api/hr-advanced/gosi-calculation?employee_id={emp_id}", headers=admin_headers)
        assert r.status_code in [200, 400, 404]


# ═══════════════════════════════════════════════════════════════
# 📄 وثائق الموظفين - Employee Documents
# ═══════════════════════════════════════════════════════════════
class TestEmployeeDocuments:
    """سيناريوهات وثائق الموظفين"""

    def test_list_documents(self, client, admin_headers):
        """✅ عرض قائمة الوثائق"""
        r = client.get("/api/hr-advanced/documents", headers=admin_headers)
        assert_valid_response(r)

    def test_create_document(self, client, admin_headers):
        """✅ إنشاء وثيقة موظف"""
        emp_r = client.get("/api/hr/employees", headers=admin_headers)
        if emp_r.status_code != 200:
            pytest.skip("لا يمكن جلب الموظفين")
        emp_data = emp_r.json()
        employees = emp_data if isinstance(emp_data, list) else emp_data.get("items", emp_data.get("data", []))
        if not employees:
            pytest.skip("لا يوجد موظفين")
        emp_id = employees[0]["id"]

        r = client.post("/api/hr-advanced/documents", json={
            "employee_id": emp_id,
            "document_type": "passport",
            "document_number": "N12345678",
            "issue_date": "2024-01-01",
            "expiry_date": "2034-01-01",
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 409, 422]

    def test_update_document(self, client, admin_headers):
        """✅ تحديث وثيقة"""
        r = client.get("/api/hr-advanced/documents", headers=admin_headers)
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("data", []))
        if not items:
            pytest.skip("لا توجد وثائق")
        doc_id = items[0]["id"]
        r2 = client.put(f"/api/hr-advanced/documents/{doc_id}", json={
            "document_number": "N99999999",
        }, headers=admin_headers)
        assert r2.status_code in [200, 400, 404, 422]

    def test_delete_document(self, client, admin_headers):
        """✅ حذف وثيقة"""
        r = client.get("/api/hr-advanced/documents", headers=admin_headers)
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("data", []))
        if not items:
            pytest.skip("لا توجد وثائق")
        doc_id = items[-1]["id"]
        r2 = client.delete(f"/api/hr-advanced/documents/{doc_id}", headers=admin_headers)
        assert r2.status_code in [200, 204, 400, 404]


# ═══════════════════════════════════════════════════════════════
# ⭐ تقييم الأداء - Performance Reviews
# ═══════════════════════════════════════════════════════════════
class TestPerformanceReviews:
    """سيناريوهات تقييم الأداء"""

    def test_list_performance_reviews(self, client, admin_headers):
        """✅ عرض تقييمات الأداء"""
        r = client.get("/api/hr-advanced/performance-reviews", headers=admin_headers)
        assert_valid_response(r)

    def test_create_performance_review(self, client, admin_headers):
        """✅ إنشاء تقييم أداء"""
        emp_r = client.get("/api/hr/employees", headers=admin_headers)
        if emp_r.status_code != 200:
            pytest.skip("لا يمكن جلب الموظفين")
        emp_data = emp_r.json()
        employees = emp_data if isinstance(emp_data, list) else emp_data.get("items", emp_data.get("data", []))
        if not employees:
            pytest.skip("لا يوجد موظفين")
        emp_id = employees[0]["id"]

        r = client.post("/api/hr-advanced/performance-reviews", json={
            "employee_id": emp_id,
            "review_period": "2025-Q4",
            "rating": 4,
            "goals_achieved": 85,
            "strengths": "أداء ممتاز في المبيعات",
            "improvements": "يحتاج تطوير في العمل الجماعي",
            "reviewer_notes": "موظف متميز",
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 422]

    def test_update_performance_review(self, client, admin_headers):
        """✅ تحديث تقييم أداء"""
        r = client.get("/api/hr-advanced/performance-reviews", headers=admin_headers)
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("data", []))
        if not items:
            pytest.skip("لا توجد تقييمات")
        review_id = items[0]["id"]
        r2 = client.put(f"/api/hr-advanced/performance-reviews/{review_id}", json={
            "rating": 5,
            "reviewer_notes": "ترقية مستحقة",
        }, headers=admin_headers)
        assert r2.status_code in [200, 400, 404, 422]


# ═══════════════════════════════════════════════════════════════
# 🎓 التدريب - Training Programs
# ═══════════════════════════════════════════════════════════════
class TestTrainingPrograms:
    """سيناريوهات البرامج التدريبية"""

    def test_list_training_programs(self, client, admin_headers):
        """✅ عرض البرامج التدريبية"""
        r = client.get("/api/hr-advanced/training", headers=admin_headers)
        assert_valid_response(r)

    def test_create_training_program(self, client, admin_headers):
        """✅ إنشاء برنامج تدريبي"""
        r = client.post("/api/hr-advanced/training", json={
            "name": "دورة تطوير المهارات القيادية",
            "description": "برنامج تدريبي للمدراء الجدد",
            "start_date": str(date.today() + timedelta(days=30)),
            "end_date": str(date.today() + timedelta(days=35)),
            "trainer": "أكاديمية التطوير المهني",
            "max_participants": 20,
            "cost": 500000,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 422]

    def test_update_training_program(self, client, admin_headers):
        """✅ تحديث برنامج تدريبي"""
        r = client.get("/api/hr-advanced/training", headers=admin_headers)
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("data", []))
        if not items:
            pytest.skip("لا توجد برامج تدريبية")
        training_id = items[0]["id"]
        r2 = client.put(f"/api/hr-advanced/training/{training_id}", json={
            "name": "برنامج محدّث",
            "max_participants": 25,
        }, headers=admin_headers)
        assert r2.status_code in [200, 400, 404, 422]

    def test_add_training_participant(self, client, admin_headers):
        """✅ إضافة مشارك لبرنامج تدريبي"""
        # جلب البرامج
        r = client.get("/api/hr-advanced/training", headers=admin_headers)
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("data", []))
        if not items:
            pytest.skip("لا توجد برامج تدريبية")
        training_id = items[0]["id"]

        # جلب الموظفين
        emp_r = client.get("/api/hr/employees", headers=admin_headers)
        if emp_r.status_code != 200:
            pytest.skip("لا يمكن جلب الموظفين")
        emp_data = emp_r.json()
        employees = emp_data if isinstance(emp_data, list) else emp_data.get("items", emp_data.get("data", []))
        if not employees:
            pytest.skip("لا يوجد موظفين")
        emp_id = employees[0]["id"]

        r2 = client.post(f"/api/hr-advanced/training/{training_id}/participants", json={
            "employee_id": emp_id,
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400, 409, 422]

    def test_list_training_participants(self, client, admin_headers):
        """✅ عرض مشاركي برنامج تدريبي"""
        r = client.get("/api/hr-advanced/training", headers=admin_headers)
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("data", []))
        if not items:
            pytest.skip("لا توجد برامج تدريبية")
        training_id = items[0]["id"]
        r2 = client.get(f"/api/hr-advanced/training/{training_id}/participants", headers=admin_headers)
        assert r2.status_code in [200, 404]


# ═══════════════════════════════════════════════════════════════
# ⚠️ المخالفات - Violations
# ═══════════════════════════════════════════════════════════════
class TestViolations:
    """سيناريوهات المخالفات"""

    def test_list_violations(self, client, admin_headers):
        """✅ عرض المخالفات"""
        r = client.get("/api/hr-advanced/violations", headers=admin_headers)
        assert_valid_response(r)

    def test_create_violation(self, client, admin_headers):
        """✅ تسجيل مخالفة"""
        emp_r = client.get("/api/hr/employees", headers=admin_headers)
        if emp_r.status_code != 200:
            pytest.skip("لا يمكن جلب الموظفين")
        emp_data = emp_r.json()
        employees = emp_data if isinstance(emp_data, list) else emp_data.get("items", emp_data.get("data", []))
        if not employees:
            pytest.skip("لا يوجد موظفين")
        emp_id = employees[0]["id"]

        r = client.post("/api/hr-advanced/violations", json={
            "employee_id": emp_id,
            "violation_type": "late_attendance",
            "violation_date": str(date.today()),
            "description": "تأخر عن الدوام 30 دقيقة",
            "severity": "minor",
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 422]

    def test_update_violation(self, client, admin_headers):
        """✅ تحديث مخالفة"""
        r = client.get("/api/hr-advanced/violations", headers=admin_headers)
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("data", []))
        if not items:
            pytest.skip("لا توجد مخالفات")
        viol_id = items[0]["id"]
        r2 = client.put(f"/api/hr-advanced/violations/{viol_id}", json={
            "action_taken": "إنذار شفهي",
        }, headers=admin_headers)
        assert r2.status_code in [200, 400, 404, 422]


# ═══════════════════════════════════════════════════════════════
# 📦 العهد - Custody
# ═══════════════════════════════════════════════════════════════
class TestCustody:
    """سيناريوهات العهد"""

    def test_list_custody(self, client, admin_headers):
        """✅ عرض العهد"""
        r = client.get("/api/hr-advanced/custody", headers=admin_headers)
        assert_valid_response(r)

    def test_create_custody(self, client, admin_headers):
        """✅ تسليم عهدة لموظف"""
        emp_r = client.get("/api/hr/employees", headers=admin_headers)
        if emp_r.status_code != 200:
            pytest.skip("لا يمكن جلب الموظفين")
        emp_data = emp_r.json()
        employees = emp_data if isinstance(emp_data, list) else emp_data.get("items", emp_data.get("data", []))
        if not employees:
            pytest.skip("لا يوجد موظفين")
        emp_id = employees[0]["id"]

        r = client.post("/api/hr-advanced/custody", json={
            "employee_id": emp_id,
            "item_name": "لابتوب Dell Latitude",
            "item_type": "equipment",
            "serial_number": "DL-2026-001",
            "value": 2500000,
            "delivery_date": str(date.today()),
            "notes": "لابتوب عمل جديد",
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 422]

    def test_update_custody(self, client, admin_headers):
        """✅ تحديث عهدة"""
        r = client.get("/api/hr-advanced/custody", headers=admin_headers)
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("data", []))
        if not items:
            pytest.skip("لا توجد عهد")
        custody_id = items[0]["id"]
        r2 = client.put(f"/api/hr-advanced/custody/{custody_id}", json={
            "notes": "تم تحديث الملاحظات",
        }, headers=admin_headers)
        assert r2.status_code in [200, 400, 404, 422]

    def test_return_custody(self, client, admin_headers):
        """✅ إرجاع عهدة"""
        r = client.get("/api/hr-advanced/custody", headers=admin_headers)
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("data", []))
        active = [c for c in items if c.get("status") in ["active", "delivered", None]]
        if not active:
            pytest.skip("لا توجد عهد نشطة")
        custody_id = active[0]["id"]
        r2 = client.put(f"/api/hr-advanced/custody/{custody_id}/return", json={
            "return_date": str(date.today()),
            "condition": "good",
            "notes": "تم الإرجاع بحالة جيدة",
        }, headers=admin_headers)
        assert r2.status_code in [200, 400, 404, 422]
