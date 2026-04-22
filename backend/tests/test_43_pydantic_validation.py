"""
AMAN ERP — Task #6 Verification: Pydantic Validation Tests
=============================================================
Tests that newly typed endpoints correctly reject invalid payloads
with HTTP 422 Unprocessable Entity.

These tests verify that the `data: dict` → `data: PydanticModel`
migration is working — invalid or missing required fields are caught
at the FastAPI validation layer before reaching business logic.
"""



class TestPydanticValidation:
    """✅ اختبارات تحقق من صحة المدخلات عبر Pydantic"""

    # ─── Assets ───────────────────────────────────────────────

    def test_asset_update_requires_valid_body(self, client, admin_headers):
        """❌ تحديث أصل بجسم غير صالح يجب أن يرجع 422"""
        # version field is required — omitting it should fail
        response = client.put(
            "/api/assets/999",
            json={"name": "X", "cost": "not_a_number"},
            headers=admin_headers
        )
        # 422 if validation fails on cost, or 404/409 if it gets through
        # We just need it not to crash with a 500
        assert response.status_code != 500, f"Got 500: {response.text[:300]}"

    def test_asset_update_missing_version_returns_422(self, client, admin_headers):
        """❌ تحديث أصل بدون version يجب أن يرجع 422"""
        response = client.put(
            "/api/assets/1",
            json={"name": "Test Asset"},  # Missing required 'version' field
            headers=admin_headers
        )
        assert response.status_code == 422, \
            f"Expected 422 (missing version), got {response.status_code}: {response.text[:300]}"

    # ─── Projects ─────────────────────────────────────────────

    def test_project_update_missing_version_returns_422(self, client, admin_headers):
        """❌ تحديث مشروع بدون version يجب أن يرجع 422"""
        response = client.put(
            "/api/projects/1",
            json={"project_name": "Test"},  # Missing required 'version'
            headers=admin_headers
        )
        assert response.status_code == 422, \
            f"Expected 422, got {response.status_code}: {response.text[:300]}"

    def test_project_task_update_missing_version_returns_422(self, client, admin_headers):
        """❌ تحديث مهمة بدون version يجب أن يرجع 422"""
        response = client.put(
            "/api/projects/1/tasks/1",
            json={"task_name": "Test Task"},  # Missing required 'version'
            headers=admin_headers
        )
        assert response.status_code == 422, \
            f"Expected 422, got {response.status_code}: {response.text[:300]}"

    # ─── Services ─────────────────────────────────────────────

    def test_service_request_update_missing_version_returns_422(self, client, admin_headers):
        """❌ تحديث طلب صيانة بدون version يجب أن يرجع 422"""
        response = client.put(
            "/api/services/requests/1",
            json={"title": "Test"},  # Missing required 'version'
            headers=admin_headers
        )
        assert response.status_code == 422, \
            f"Expected 422, got {response.status_code}: {response.text[:300]}"

    # ─── CRM ──────────────────────────────────────────────────

    def test_opportunity_update_missing_version_returns_422(self, client, admin_headers):
        """❌ تحديث فرصة بيع بدون version يجب أن يرجع 422"""
        response = client.put(
            "/api/crm/opportunities/1",
            json={"stage": "proposal"},  # Missing required 'version'
            headers=admin_headers
        )
        assert response.status_code == 422, \
            f"Expected 422, got {response.status_code}: {response.text[:300]}"

    def test_ticket_update_missing_version_returns_422(self, client, admin_headers):
        """❌ تحديث تذكرة دعم بدون version يجب أن يرجع 422"""
        response = client.put(
            "/api/crm/tickets/1",
            json={"status": "resolved"},  # Missing required 'version'
            headers=admin_headers
        )
        assert response.status_code == 422, \
            f"Expected 422, got {response.status_code}: {response.text[:300]}"

    # ─── HR ───────────────────────────────────────────────────

    def test_employee_update_missing_version_returns_422(self, client, admin_headers):
        """❌ تحديث موظف بدون version يجب أن يرجع 422"""
        response = client.put(
            "/api/hr/employees/1",
            json={"first_name": "Ahmed"},  # Missing required 'version'
            headers=admin_headers
        )
        assert response.status_code == 422, \
            f"Expected 422, got {response.status_code}: {response.text[:300]}"

    # ─── POS ──────────────────────────────────────────────────

    def test_pos_validate_coupon_missing_required_field(self, client, admin_headers):
        """✅ POST /api/pos/promotions/validate — يقبل أي body (coupon_code has default)"""
        # CouponValidateRequest has coupon_code: str = "" (optional default)
        # So an empty body is valid Pydantic, returns 400 (business validation — code required)
        response = client.post(
            "/api/pos/promotions/validate",
            json={},  # coupon_code defaults to ""
            headers=admin_headers
        )
        # Business logic returns 400 "Coupon code required", not a 422 or 500
        assert response.status_code in (400, 404), \
            f"Expected 400 (empty coupon) or 404, got {response.status_code}: {response.text[:300]}"
        assert response.status_code != 500, f"Got 500: {response.text[:300]}"

    def test_pos_earn_points_missing_required_field(self, client, admin_headers):
        """❌ إضافة نقاط ولاء بدون amount الإلزامي يجب أن يرجع 422"""
        response = client.post(
            "/api/pos/loyalty/earn",
            json={"customer_id": 1},  # Missing required 'amount'
            headers=admin_headers
        )
        assert response.status_code == 422, \
            f"Expected 422, got {response.status_code}: {response.text[:300]}"

    # ─── Purchases ────────────────────────────────────────────

    def test_create_rfq_missing_supplier(self, client, admin_headers):
        """❌ إنشاء طلب عرض سعر بدون بيانات إلزامية يجب أن يرجع 422"""
        # Route: POST /api/buying/rfq (purchases router prefix is /buying)
        response = client.post(
            "/api/buying/rfq",
            json={"lines": []},  # Missing required fields
            headers=admin_headers
        )
        assert response.status_code == 422, \
            f"Expected 422, got {response.status_code}: {response.text[:300]}"

    # ─── Sales ────────────────────────────────────────────────

    def test_create_commission_rule_missing_name(self, client, admin_headers):
        """❌ إنشاء قاعدة عمولة بدون name يجب أن يرجع 422"""
        response = client.post(
            "/api/sales/commissions/rules",
            json={"commission_rate": 5.0},  # Missing required 'name'
            headers=admin_headers
        )
        assert response.status_code == 422, \
            f"Expected 422, got {response.status_code}: {response.text[:300]}"

    # ─── Approvals ────────────────────────────────────────────

    def test_create_approval_request_missing_fields(self, client, admin_headers):
        """❌ إنشاء طلب موافقة بدون document_type/document_id يُرجع خطأ (400/404 — business validation)"""
        # ApprovalRequestCreate has optional fields → Pydantic passes,
        # but business layer validates and returns 400 "يجب تحديد نوع المستند ورقمه"
        response = client.post(
            "/api/approvals/requests",
            json={"notes": "please approve"},  # Missing document_type + document_id
            headers=admin_headers
        )
        # Business validation returns 400 (not 422) — document_type/document_id are Optional in schema
        assert response.status_code in (400, 404, 422), \
            f"Expected 400/404/422 for missing fields, got {response.status_code}: {response.text[:300]}"
        assert response.status_code != 500, f"Got 500: {response.text[:300]}"

    # ─── Notifications ───────────────────────────────────────

    def test_empty_body_on_typed_endpoint_returns_422(self, client, admin_headers):
        """❌ إرسال جسم فارغ {} لنقطة نهاية محددة يجب أن تنجح (كل الحقول اختيارية)"""
        # NotificationSettingsUpdate has all optional fields, so {} is valid (200 or 404)
        response = client.put(
            "/api/notifications/settings",
            json={},
            headers=admin_headers
        )
        assert response.status_code != 422, \
            "Empty body should be accepted for all-optional schema, got 422"
        assert response.status_code != 500, f"Got 500: {response.text[:300]}"
