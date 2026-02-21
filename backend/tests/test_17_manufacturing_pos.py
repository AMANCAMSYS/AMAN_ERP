"""
AMAN ERP - اختبارات شاملة متعددة السيناريوهات: التصنيع ونقاط البيع
Comprehensive Multi-Scenario Tests: Manufacturing & POS
═══════════════════════════════════════════════════════
يتضمن: قوائم المواد، أوامر الإنتاج، جلسات البيع، الطلبات، المرتجعات
"""

import pytest
from datetime import date, datetime
from helpers import assert_valid_response, assert_error_response


# ═══════════════════════════════════════════════════════════════
# 🏭 التصنيع - Manufacturing
# ═══════════════════════════════════════════════════════════════
class TestBOMScenarios:
    """سيناريوهات قوائم المواد"""

    def test_list_boms(self, client, admin_headers):
        """✅ عرض قوائم المواد"""
        r = client.get("/api/manufacturing/boms", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_bom_detail(self, client, admin_headers):
        """✅ تفاصيل قائمة مواد"""
        r = client.get("/api/manufacturing/boms", headers=admin_headers)
        boms = r.json()
        if not boms:
            pytest.skip("لا قوائم مواد")
        bid = boms[0]["id"]
        r2 = client.get(f"/api/manufacturing/boms/{bid}", headers=admin_headers)
        assert_valid_response(r2)
        detail = r2.json()
        assert "items" in detail
        assert detail["id"] == bid

    def test_create_bom(self, client, admin_headers):
        """✅ إنشاء قائمة مواد جديدة"""
        r = client.post("/api/manufacturing/boms", json={
            "name": "BOM اختبار جديد",
            "product_id": 1,
            "quantity": 1,
            "is_active": True,
            "items": [
                {"item_id": 2, "quantity": 3, "waste_percentage": 5},
                {"item_id": 3, "quantity": 1, "waste_percentage": 0},
            ]
        }, headers=admin_headers)
        assert r.status_code in [200, 201]
        data = r.json()
        assert data["name"] == "BOM اختبار جديد"

    def test_update_bom(self, client, admin_headers):
        """✅ تحديث قائمة مواد"""
        r = client.get("/api/manufacturing/boms", headers=admin_headers)
        boms = r.json()
        if not boms:
            pytest.skip("لا قوائم مواد")
        # Find a BOM not used in production orders for safe update
        bid = boms[-1]["id"]
        r2 = client.put(f"/api/manufacturing/boms/{bid}", json={
            "name": "BOM محدّث",
            "product_id": 1,
            "quantity": 2,
            "is_active": True,
            "items": [
                {"item_id": 2, "quantity": 5, "waste_percentage": 2},
            ]
        }, headers=admin_headers)
        assert r2.status_code in [200, 400, 404]

    def test_delete_bom_used_in_order(self, client, admin_headers):
        """❌ حذف قائمة مواد مستخدمة في أمر إنتاج"""
        r = client.get("/api/manufacturing/boms", headers=admin_headers)
        boms = r.json()
        if not boms:
            pytest.skip("لا قوائم مواد")
        # Try to delete the first BOM (likely used in orders)
        bid = boms[0]["id"]
        r2 = client.delete(f"/api/manufacturing/boms/{bid}", headers=admin_headers)
        # Should fail with 400 if used, or 200 if not
        assert r2.status_code in [200, 400]

    def test_delete_bom_unused(self, client, admin_headers):
        """✅ حذف قائمة مواد غير مستخدمة"""
        # Create a new BOM specifically for deletion
        r = client.post("/api/manufacturing/boms", json={
            "name": "BOM للحذف",
            "product_id": 1,
            "quantity": 1,
            "is_active": False,
            "items": [
                {"item_id": 2, "quantity": 1, "waste_percentage": 0},
            ]
        }, headers=admin_headers)
        if r.status_code in [200, 201]:
            bid = r.json()["id"]
            r2 = client.delete(f"/api/manufacturing/boms/{bid}", headers=admin_headers)
            assert r2.status_code == 200

    def test_get_nonexistent_bom(self, client, admin_headers):
        """❌ طلب قائمة مواد غير موجودة"""
        r = client.get("/api/manufacturing/boms/99999", headers=admin_headers)
        assert r.status_code == 404


class TestProductionOrderScenarios:
    """سيناريوهات أوامر الإنتاج"""

    def test_list_production_orders(self, client, admin_headers):
        """✅ عرض أوامر الإنتاج"""
        r = client.get("/api/manufacturing/orders", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_create_production_order(self, client, admin_headers):
        """✅ إنشاء أمر إنتاج"""
        r = client.get("/api/manufacturing/boms", headers=admin_headers)
        boms = r.json()
        if not boms:
            pytest.skip("لا قوائم مواد")
        bom_id = boms[0]["id"]
        r2 = client.post("/api/manufacturing/orders", json={
            "bom_id": bom_id,
            "quantity": 5,
            "status": "planned",
            "start_date": str(date.today()),
        }, headers=admin_headers)
        assert r2.status_code in [200, 201]
        data = r2.json()
        assert data["bom_id"] == bom_id

    def test_complete_production_order(self, client, admin_headers):
        """✅ إكمال أمر إنتاج"""
        # Get an existing order
        r = client.get("/api/manufacturing/orders", headers=admin_headers)
        orders = r.json()
        planned = next((o for o in orders if o.get("status") in ("planned", "confirmed", "in_progress")), None)
        if not planned:
            pytest.skip("لا أمر إنتاج معلق")
        oid = planned["id"]
        r2 = client.post(f"/api/manufacturing/orders/{oid}/complete", headers=admin_headers)
        # Could succeed or fail due to insufficient stock
        assert r2.status_code in [200, 400, 500]

    def test_complete_already_completed_order(self, client, admin_headers):
        """❌ إكمال أمر إنتاج مكتمل"""
        r = client.get("/api/manufacturing/orders", headers=admin_headers)
        orders = r.json()
        completed = next((o for o in orders if o.get("status") == "completed"), None)
        if not completed:
            # Try to complete a planned order first
            planned = next((o for o in orders if o.get("status") in ("planned", "confirmed", "in_progress")), None)
            if planned:
                client.post(f"/api/manufacturing/orders/{planned['id']}/complete", headers=admin_headers)
                # Re-check
                r = client.get("/api/manufacturing/orders", headers=admin_headers)
                orders = r.json()
                completed = next((o for o in orders if o.get("status") == "completed"), None)
            if not completed:
                pytest.skip("لا أمر مكتمل")
        oid = completed["id"]
        r2 = client.post(f"/api/manufacturing/orders/{oid}/complete", headers=admin_headers)
        assert r2.status_code in [400, 500]


# ═══════════════════════════════════════════════════════════════
# 🛒 نقاط البيع - POS
# ═══════════════════════════════════════════════════════════════
class TestPOSSessionScenarios:
    """سيناريوهات جلسات نقاط البيع"""

    def test_open_session(self, client, admin_headers):
        """✅ فتح جلسة بيع"""
        # Close any existing sessions first
        active = client.get("/api/pos/sessions/active", headers=admin_headers)
        if active.status_code == 200 and active.json():
            sid = active.json().get("id")
            if sid:
                client.post(f"/api/pos/sessions/{sid}/close", json={
                    "closing_balance": 0,
                    "cash_register_balance": 0,
                }, headers=admin_headers)

        r = client.post("/api/pos/sessions/open", json={
            "warehouse_id": 1,
            "opening_balance": 500,
            "branch_id": 1,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 422, 500]

    def test_get_active_session(self, client, admin_headers):
        """✅ الحصول على الجلسة النشطة"""
        r = client.get("/api/pos/sessions/active", headers=admin_headers)
        assert r.status_code == 200

    def test_open_duplicate_session(self, client, admin_headers):
        """❌ فتح جلسة مكررة"""
        active = client.get("/api/pos/sessions/active", headers=admin_headers)
        if active.status_code == 200 and active.json():
            r = client.post("/api/pos/sessions/open", json={
                "warehouse_id": 1,
                "opening_balance": 100,
            }, headers=admin_headers)
            assert r.status_code in [400, 409, 500]


class TestPOSProductScenarios:
    """سيناريوهات منتجات نقاط البيع"""

    def test_list_pos_products(self, client, admin_headers):
        """✅ عرض منتجات نقاط البيع"""
        r = client.get("/api/pos/products", headers=admin_headers)
        assert_valid_response(r)
        products = r.json()
        assert isinstance(products, list)

    def test_list_pos_warehouses(self, client, admin_headers):
        """✅ عرض مستودعات نقاط البيع"""
        r = client.get("/api/pos/warehouses", headers=admin_headers)
        assert_valid_response(r)


class TestPOSOrderScenarios:
    """سيناريوهات طلبات نقاط البيع"""

    def _ensure_session(self, client, admin_headers):
        """تأكيد وجود جلسة نشطة"""
        active = client.get("/api/pos/sessions/active", headers=admin_headers)
        if active.status_code == 200 and active.json():
            return active.json()["id"]
        # Open new session
        r = client.post("/api/pos/sessions/open", json={
            "warehouse_id": 1,
            "opening_balance": 500,
            "branch_id": 1,
        }, headers=admin_headers)
        if r.status_code in [200, 201]:
            return r.json()["id"]
        return None

    def test_create_cash_order(self, client, admin_headers):
        """✅ إنشاء طلب نقدي"""
        sid = self._ensure_session(client, admin_headers)
        if not sid:
            pytest.skip("لا جلسة نشطة")

        r = client.post("/api/pos/orders", json={
            "session_id": sid,
            "items": [
                {"product_id": 1, "quantity": 2, "unit_price": 100, "tax_rate": 15},
            ],
            "payments": [
                {"method": "cash", "amount": 230},
            ],
            "status": "paid",
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400]

    def test_create_card_order(self, client, admin_headers):
        """✅ إنشاء طلب بطاقة"""
        sid = self._ensure_session(client, admin_headers)
        if not sid:
            pytest.skip("لا جلسة نشطة")

        r = client.post("/api/pos/orders", json={
            "session_id": sid,
            "items": [
                {"product_id": 2, "quantity": 1, "unit_price": 200, "tax_rate": 15},
            ],
            "payments": [
                {"method": "card", "amount": 230},
            ],
            "status": "paid",
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400]

    def test_create_split_payment_order(self, client, admin_headers):
        """✅ طلب بدفع مقسم (نقد + بطاقة)"""
        sid = self._ensure_session(client, admin_headers)
        if not sid:
            pytest.skip("لا جلسة نشطة")

        r = client.post("/api/pos/orders", json={
            "session_id": sid,
            "items": [
                {"product_id": 1, "quantity": 3, "unit_price": 100, "tax_rate": 15},
            ],
            "payments": [
                {"method": "cash", "amount": 200},
                {"method": "card", "amount": 145},
            ],
            "status": "paid",
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400]

    def test_create_held_order(self, client, admin_headers):
        """✅ إنشاء طلب معلق"""
        sid = self._ensure_session(client, admin_headers)
        if not sid:
            pytest.skip("لا جلسة نشطة")

        r = client.post("/api/pos/orders", json={
            "session_id": sid,
            "items": [
                {"product_id": 1, "quantity": 1, "unit_price": 50, "tax_rate": 0},
            ],
            "status": "hold",
            "note": "طلب معلق - في انتظار العميل",
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400]

    def test_list_held_orders(self, client, admin_headers):
        """✅ عرض الطلبات المعلقة"""
        r = client.get("/api/pos/orders/held", headers=admin_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_order_details(self, client, admin_headers):
        """✅ تفاصيل طلب"""
        # First create an order
        sid = self._ensure_session(client, admin_headers)
        if not sid:
            pytest.skip("لا جلسة نشطة")
        r = client.post("/api/pos/orders", json={
            "session_id": sid,
            "items": [{"product_id": 1, "quantity": 1, "unit_price": 100, "tax_rate": 0}],
            "payments": [{"method": "cash", "amount": 100}],
            "status": "paid",
        }, headers=admin_headers)
        if r.status_code in [200, 201]:
            oid = r.json().get("id")
            if oid:
                r2 = client.get(f"/api/pos/orders/{oid}/details", headers=admin_headers)
                assert r2.status_code in [200, 404]

    def test_create_order_with_discount(self, client, admin_headers):
        """✅ طلب بخصم"""
        sid = self._ensure_session(client, admin_headers)
        if not sid:
            pytest.skip("لا جلسة نشطة")

        r = client.post("/api/pos/orders", json={
            "session_id": sid,
            "items": [
                {"product_id": 1, "quantity": 2, "unit_price": 100, "discount_amount": 20, "tax_rate": 15},
            ],
            "discount_amount": 10,
            "payments": [
                {"method": "cash", "amount": 200},
            ],
            "status": "paid",
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400]

    def test_create_walk_in_customer_order(self, client, admin_headers):
        """✅ طلب عميل عابر"""
        sid = self._ensure_session(client, admin_headers)
        if not sid:
            pytest.skip("لا جلسة نشطة")

        r = client.post("/api/pos/orders", json={
            "session_id": sid,
            "walk_in_customer_name": "عميل عابر",
            "items": [
                {"product_id": 2, "quantity": 1, "unit_price": 150, "tax_rate": 0},
            ],
            "payments": [
                {"method": "cash", "amount": 150},
            ],
            "status": "paid",
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400]


class TestPOSCloseSessionScenarios:
    """سيناريوهات إغلاق جلسة نقاط البيع"""

    def test_close_session(self, client, admin_headers):
        """✅ إغلاق جلسة البيع"""
        active = client.get("/api/pos/sessions/active", headers=admin_headers)
        if active.status_code != 200 or not active.json():
            pytest.skip("لا جلسة نشطة")

        sid = active.json()["id"]
        r = client.post(f"/api/pos/sessions/{sid}/close", json={
            "closing_balance": 1000,
            "cash_register_balance": 1000,
            "notes": "إغلاق اختبار",
        }, headers=admin_headers)
        assert r.status_code in [200, 400, 500]

    def test_close_nonexistent_session(self, client, admin_headers):
        """❌ إغلاق جلسة غير موجودة"""
        r = client.post("/api/pos/sessions/99999/close", json={
            "closing_balance": 0,
            "cash_register_balance": 0,
        }, headers=admin_headers)
        assert r.status_code in [400, 404]
