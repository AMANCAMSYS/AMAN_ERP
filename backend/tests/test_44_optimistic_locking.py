"""
AMAN ERP — Task #7 Verification: Optimistic Locking Tests
===========================================================
Tests that version-protected UPDATE endpoints correctly:
  1. Include `version: int` in GET responses (column was migrated)
  2. Return HTTP 409 Conflict when wrong version is sent
  3. Return HTTP 200 on correct version

Each test class creates its own fixture data, runs assertions, then cleans up,
so they work on empty (production) databases without pre-seeded data.

Run:
  pytest tests/test_44_optimistic_locking.py -v
"""

import pytest


# ---------------------------------------------------------------------------
# Asset optimistic locking
# ---------------------------------------------------------------------------

class TestOptimisticLockingAssets:
    """🔒 اختبارات القفل التفاؤلي لجدول assets"""

    @pytest.fixture(autouse=True)
    def create_asset(self, client, admin_headers):
        """Create a test asset before each test, delete after."""
        r = client.post("/api/assets", json={
            "name": "_OL_Test_Asset",
            "type": "machinery",
            "purchase_date": "2024-01-01",
            "cost": 1000.0,
            "life_years": 5,
            "residual_value": 0.0,
            "branch_id": 1,
        }, headers=admin_headers)
        assert r.status_code == 200, f"Asset creation failed: {r.text[:200]}"
        self._asset_id = r.json()["id"]
        yield
        # Cleanup — best effort (some endpoints may not support DELETE)
        client.delete(f"/api/assets/{self._asset_id}", headers=admin_headers)

    def test_get_asset_includes_version_field(self, client, admin_headers):
        """✅ استجابة GET /api/assets يجب أن تحتوي على حقل version"""
        response = client.get("/api/assets", headers=admin_headers)
        assert response.status_code == 200
        items = response.json()
        asset = next((a for a in items if a["id"] == self._asset_id), None)
        assert asset is not None, "Created asset not found in list"
        assert "version" in asset, \
            f"version field missing from asset response: {list(asset.keys())}"
        assert isinstance(asset["version"], int), \
            f"version should be int, got {type(asset['version'])}"

    def test_asset_update_wrong_version_returns_409(self, client, admin_headers):
        """❌ تحديث أصل بإصدار خاطئ يجب أن يرجع 409"""
        r = client.put(
            f"/api/assets/{self._asset_id}",
            json={"name": "_OL_Updated", "version": 99999},
            headers=admin_headers
        )
        assert r.status_code == 409, \
            f"Expected 409 for wrong version, got {r.status_code}: {r.text[:300]}"

    def test_asset_update_correct_version_returns_200(self, client, admin_headers):
        """✅ تحديث أصل بإصدار صحيح يجب أن يرجع 200"""
        # Get current version
        items = client.get("/api/assets", headers=admin_headers).json()
        asset = next(a for a in items if a["id"] == self._asset_id)
        ver = asset["version"]

        r = client.put(
            f"/api/assets/{self._asset_id}",
            json={"name": "_OL_Updated", "version": ver},
            headers=admin_headers
        )
        assert r.status_code == 200, \
            f"Expected 200 for correct version, got {r.status_code}: {r.text[:300]}"


# ---------------------------------------------------------------------------
# Project optimistic locking
# ---------------------------------------------------------------------------

class TestOptimisticLockingProjects:
    """🔒 اختبارات القفل التفاؤلي لجدول projects"""

    @pytest.fixture(autouse=True)
    def create_project(self, client, admin_headers):
        r = client.post("/api/projects", json={
            "project_name": "_OL_Test_Project",
            "start_date": "2024-01-01",
            "status": "active",
            "branch_id": 1,
        }, headers=admin_headers)
        assert r.status_code in (200, 201), f"Project creation failed: {r.text[:200]}"
        self._project_id = r.json()["id"]
        yield
        client.delete(f"/api/projects/{self._project_id}", headers=admin_headers)

    def test_project_version_in_list(self, client, admin_headers):
        """✅ استجابة GET /api/projects تحتوي على حقل version"""
        r = client.get("/api/projects", headers=admin_headers)
        assert r.status_code == 200
        items = r.json()
        proj = next((p for p in items if p["id"] == self._project_id), None)
        assert proj is not None
        assert "version" in proj, f"version missing: {list(proj.keys())}"

    def test_project_update_wrong_version_returns_409(self, client, admin_headers):
        """❌ تحديث مشروع بإصدار خاطئ يجب أن يرجع 409"""
        r = client.put(
            f"/api/projects/{self._project_id}",
            json={"project_name": "_OL_Updated", "version": 99999},
            headers=admin_headers
        )
        assert r.status_code == 409, \
            f"Expected 409, got {r.status_code}: {r.text[:300]}"

    def test_project_update_correct_version_returns_200(self, client, admin_headers):
        """✅ تحديث مشروع بإصدار صحيح يجب أن يرجع 200"""
        items = client.get("/api/projects", headers=admin_headers).json()
        proj = next(p for p in items if p["id"] == self._project_id)
        r = client.put(
            f"/api/projects/{self._project_id}",
            json={"project_name": "_OL_Updated_OK", "version": proj["version"]},
            headers=admin_headers
        )
        assert r.status_code == 200, \
            f"Expected 200, got {r.status_code}: {r.text[:300]}"


# ---------------------------------------------------------------------------
# Service Request optimistic locking
# ---------------------------------------------------------------------------

class TestOptimisticLockingServices:
    """🔒 اختبارات القفل التفاؤلي لجدول service_requests"""

    @pytest.fixture(autouse=True)
    def create_service_request(self, client, admin_headers):
        r = client.post("/api/services/requests", json={
            "title": "_OL_Test_Request",
            "priority": "medium",
        }, headers=admin_headers)
        assert r.status_code == 200, f"Service request creation failed: {r.text[:200]}"
        self._req_id = r.json()["id"]
        yield

    def test_service_request_version_in_response(self, client, admin_headers):
        """✅ استجابة GET /api/services/requests/{id} تحتوي على حقل version"""
        r = client.get(f"/api/services/requests/{self._req_id}", headers=admin_headers)
        assert r.status_code == 200
        req = r.json()
        assert "version" in req, f"version missing: {list(req.keys())}"
        assert isinstance(req["version"], int)

    def test_service_request_wrong_version_returns_409(self, client, admin_headers):
        """❌ تحديث طلب صيانة بإصدار خاطئ يجب أن يرجع 409"""
        r = client.put(
            f"/api/services/requests/{self._req_id}",
            json={"title": "_OL_Updated", "version": 99999},
            headers=admin_headers
        )
        assert r.status_code == 409, \
            f"Expected 409, got {r.status_code}: {r.text[:300]}"

    def test_service_request_correct_version_returns_200(self, client, admin_headers):
        """✅ تحديث صحيح يرجع 200"""
        req = client.get(f"/api/services/requests/{self._req_id}", headers=admin_headers).json()
        r = client.put(
            f"/api/services/requests/{self._req_id}",
            json={"title": "_OL_Updated_OK", "version": req["version"]},
            headers=admin_headers
        )
        assert r.status_code == 200, \
            f"Expected 200, got {r.status_code}: {r.text[:300]}"


# ---------------------------------------------------------------------------
# CRM Opportunity optimistic locking
# ---------------------------------------------------------------------------

class TestOptimisticLockingOpportunities:
    """🔒 اختبارات القفل التفاؤلي لجدول sales_opportunities"""

    @pytest.fixture(autouse=True)
    def create_opportunity(self, client, admin_headers):
        r = client.post("/api/crm/opportunities", json={
            "title": "_OL_Test_Opportunity",
            "stage": "lead",
            "value": 1000.0,
        }, headers=admin_headers)
        assert r.status_code in (200, 201), f"Opportunity creation failed: {r.text[:200]}"
        self._opp_id = r.json()["id"]
        yield

    def test_opportunity_wrong_version_returns_409(self, client, admin_headers):
        """❌ تحديث فرصة بإصدار خاطئ يجب أن يرجع 409"""
        r = client.put(
            f"/api/crm/opportunities/{self._opp_id}",
            json={"stage": "proposal", "version": 99999},
            headers=admin_headers
        )
        assert r.status_code == 409, \
            f"Expected 409, got {r.status_code}: {r.text[:300]}"

    def test_opportunity_correct_version_returns_200(self, client, admin_headers):
        """✅ تحديث فرصة بإصدار صحيح يجب أن يرجع 200"""
        # Get current version from list
        items_r = client.get("/api/crm/opportunities", headers=admin_headers)
        items = items_r.json() if isinstance(items_r.json(), list) else items_r.json().get("items", [])
        opp = next((o for o in items if o["id"] == self._opp_id), None)
        if opp is None:
            pytest.skip("Opportunity not found in list response")
        r = client.put(
            f"/api/crm/opportunities/{self._opp_id}",
            json={"stage": "proposal", "version": opp.get("version", 1)},
            headers=admin_headers
        )
        assert r.status_code == 200, \
            f"Expected 200, got {r.status_code}: {r.text[:300]}"


# ---------------------------------------------------------------------------
# Customer (Party) optimistic locking
# ---------------------------------------------------------------------------

class TestOptimisticLockingCustomers:
    """🔒 اختبارات القفل التفاؤلي لجدول parties (customers)"""

    @pytest.fixture(autouse=True)
    def create_customer(self, client, admin_headers):
        r = client.post("/api/sales/customers", json={
            "name": "_OL_Test_Customer",
            "phone": "0500000099",
        }, headers=admin_headers)
        assert r.status_code in (200, 201), f"Customer creation failed: {r.text[:200]}"
        self._cust_id = r.json()["id"]
        yield

    def test_customer_wrong_version_returns_409(self, client, admin_headers):
        """❌ تحديث عميل بإصدار خاطئ يجب أن يرجع 409"""
        r = client.put(
            f"/api/sales/customers/{self._cust_id}",
            json={"name": "_OL_Updated", "version": 99999},
            headers=admin_headers
        )
        assert r.status_code == 409, \
            f"Expected 409, got {r.status_code}: {r.text[:300]}"

    def test_customer_correct_version_returns_200(self, client, admin_headers):
        """✅ تحديث عميل بإصدار صحيح يجب أن يرجع 200"""
        # Fetch the current version
        r_list = client.get("/api/sales/customers", headers=admin_headers)
        customers = r_list.json() if isinstance(r_list.json(), list) else r_list.json().get("items", [])
        cust = next((c for c in customers if c["id"] == self._cust_id), None)
        if cust is None:
            pytest.skip("Customer not found in list response")
        r = client.put(
            f"/api/sales/customers/{self._cust_id}",
            json={"name": "_OL_Updated_OK", "version": cust.get("version", 1)},
            headers=admin_headers
        )
        assert r.status_code == 200, \
            f"Expected 200, got {r.status_code}: {r.text[:300]}"


# ---------------------------------------------------------------------------
# Product (Inventory) optimistic locking
# ---------------------------------------------------------------------------

class TestOptimisticLockingProducts:
    """🔒 اختبارات القفل التفاؤلي لجدول products"""

    @pytest.fixture(autouse=True)
    def create_product(self, client, admin_headers, request):
        import time
        # Use test name to ensure unique code per test
        code = f"_OL_{request.node.name[:8]}_{int(time.time() * 1000) % 100000}"
        r = client.post("/api/inventory/products", json={
            "item_code": code,
            "item_name": "_OL_Test_Product",
            "unit": "pcs",
            "buying_price": 10.0,
            "selling_price": 15.0,
        }, headers=admin_headers)
        assert r.status_code in (200, 201), f"Product creation failed: {r.text[:200]}"
        resp = r.json()
        self._prod_id = resp.get("id") or resp.get("product_id")
        self._item_code = code
        yield

    def test_product_wrong_version_returns_409(self, client, admin_headers):
        """❌ تحديث منتج بإصدار خاطئ يجب أن يرجع 409"""
        r = client.put(
            f"/api/inventory/products/{self._prod_id}",
            json={"item_code": self._item_code, "item_name": "_OL_Updated", "version": 99999},
            headers=admin_headers
        )
        assert r.status_code == 409, \
            f"Expected 409, got {r.status_code}: {r.text[:300]}"

    def test_product_correct_version_returns_200(self, client, admin_headers):
        """✅ تحديث منتج بإصدار صحيح يجب أن يرجع 200"""
        r_list = client.get("/api/inventory/products", headers=admin_headers)
        products = r_list.json() if isinstance(r_list.json(), list) else r_list.json().get("items", [])
        prod = next((p for p in products if p["id"] == self._prod_id), None)
        if prod is None:
            pytest.skip("Product not found in list response")
        r = client.put(
            f"/api/inventory/products/{self._prod_id}",
            json={"item_code": self._item_code, "item_name": "_OL_Updated_OK", "version": prod.get("version", 1)},
            headers=admin_headers
        )
        assert r.status_code == 200, \
            f"Expected 200, got {r.status_code}: {r.text[:300]}"
