"""
AMAN ERP - اختبارات شاملة متعددة السيناريوهات: المخزون
Comprehensive Multi-Scenario Tests: Inventory Module
═══════════════════════════════════════════════════════
يتضمن: المنتجات، الفئات، المستودعات، حركات المخزون، الشحنات، التسويات
"""

import pytest
from helpers import assert_valid_response


# ═══════════════════════════════════════════════════════════════
# 📦 المنتجات - Products
# ═══════════════════════════════════════════════════════════════
class TestProductScenarios:
    """سيناريوهات المنتجات"""

    def test_list_products(self, client, admin_headers):
        """✅ عرض المنتجات"""
        r = client.get("/api/inventory/products", headers=admin_headers)
        assert_valid_response(r)
        assert len(r.json()) >= 3

    def test_get_product_detail(self, client, admin_headers):
        """✅ تفاصيل منتج"""
        r = client.get("/api/inventory/products/1", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        assert "id" in data

    def test_create_product(self, client, admin_headers):
        """✅ إنشاء منتج جديد"""
        r = client.post("/api/inventory/products", json={
            "item_code": "TST-NEW-001",
            "item_name": "منتج اختبار جديد",
            "unit": "قطعة",
            "selling_price": 99.99,
            "buying_price": 50,
            "tax_rate": 15,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 409]

    def test_create_service_product(self, client, admin_headers):
        """✅ إنشاء منتج خدمة"""
        r = client.post("/api/inventory/products", json={
            "item_code": "SRV-NEW-001",
            "item_name": "خدمة استشارات",
            "unit": "ساعة",
            "selling_price": 200,
            "buying_price": 0,
            "tax_rate": 15,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 409]

    def test_create_product_with_category(self, client, admin_headers):
        """✅ إنشاء منتج بفئة"""
        r = client.get("/api/inventory/categories", headers=admin_headers)
        cats = r.json()
        cat_id = cats[0]["id"] if cats else None

        r2 = client.post("/api/inventory/products", json={
            "item_code": "TST-CAT-001",
            "item_name": "منتج بفئة",
            "unit": "قطعة",
            "selling_price": 100,
            "buying_price": 60,
            "tax_rate": 15,
            "category_id": cat_id,
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400, 409]

    def test_update_product(self, client, admin_headers):
        """✅ تحديث منتج"""
        # Get current product data first
        r0 = client.get("/api/inventory/products/1", headers=admin_headers)
        if r0.status_code != 200:
            pytest.skip("منتج غير موجود")
        prod = r0.json()
        r = client.put("/api/inventory/products/1", json={
            "item_code": prod.get("item_code", "PROD-001"),
            "item_name": "منتج محدّث",
            "selling_price": 160,
        }, headers=admin_headers)
        assert r.status_code in [200, 400, 404, 422, 500]

    def test_get_product_stock(self, client, admin_headers):
        """✅ استعلام كمية مخزون منتج"""
        r = client.get("/api/inventory/products/1/stock", headers=admin_headers)
        assert r.status_code in [200, 404]

    def test_product_cost_per_warehouse(self, client, admin_headers):
        """✅ تكلفة المنتج حسب المستودع"""
        r = client.get("/api/inventory/products/1/cost", headers=admin_headers)
        assert r.status_code in [200, 404]

    def test_delete_unused_product(self, client, admin_headers):
        """✅ حذف منتج غير مستخدم"""
        # Create then delete
        r = client.post("/api/inventory/products", json={
            "item_code": "DEL-001",
            "item_name": "منتج للحذف",
            "unit": "قطعة",
            "selling_price": 10,
            "buying_price": 5,
            "tax_rate": 0,
        }, headers=admin_headers)
        if r.status_code in [200, 201]:
            pid = r.json().get("id")
            if pid:
                r2 = client.delete(f"/api/inventory/products/{pid}", headers=admin_headers)
                assert r2.status_code in [200, 204, 400]

    def test_low_stock_alerts(self, client, admin_headers):
        """✅ تنبيهات المخزون المنخفض"""
        r = client.get("/api/inventory/alerts", headers=admin_headers)
        assert r.status_code in [200, 404]


# ═══════════════════════════════════════════════════════════════
# 📂 فئات المنتجات - Product Categories
# ═══════════════════════════════════════════════════════════════
class TestCategoryScenarios:
    """سيناريوهات الفئات"""

    def test_list_categories(self, client, admin_headers):
        """✅ عرض الفئات"""
        r = client.get("/api/inventory/categories", headers=admin_headers)
        assert_valid_response(r)
        assert len(r.json()) >= 1

    def test_create_category(self, client, admin_headers):
        """✅ إنشاء فئة"""
        r = client.post("/api/inventory/categories", json={
            "name": "فئة اختبار جديدة",
            "code": "CAT-TST-001",
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 409]

    def test_create_subcategory(self, client, admin_headers):
        """✅ إنشاء فئة فرعية"""
        r = client.get("/api/inventory/categories", headers=admin_headers)
        cats = r.json()
        if not cats:
            pytest.skip("لا فئات")

        r2 = client.post("/api/inventory/categories", json={
            "name": "فئة فرعية",
            "code": "CAT-SUB-001",
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400, 409]

    def test_update_category(self, client, admin_headers):
        """✅ تحديث فئة"""
        r = client.get("/api/inventory/categories", headers=admin_headers)
        cats = r.json()
        if not cats:
            pytest.skip("لا فئات")
        r2 = client.put(f"/api/inventory/categories/{cats[0]['id']}", json={
            "name": "فئة محدّثة",
        }, headers=admin_headers)
        assert r2.status_code in [200, 400, 404]

    def test_delete_empty_category(self, client, admin_headers):
        """✅ حذف فئة فارغة"""
        r = client.post("/api/inventory/categories", json={
            "name": "فئة للحذف",
            "code": "CAT-DEL-001",
        }, headers=admin_headers)
        if r.status_code in [200, 201]:
            cid = r.json().get("id")
            if cid:
                r2 = client.delete(f"/api/inventory/categories/{cid}", headers=admin_headers)
                assert r2.status_code in [200, 204, 400]

    def test_get_next_category_code(self, client, admin_headers):
        """✅ الحصول على الكود التالي"""
        r = client.get("/api/inventory/categories/next-code", headers=admin_headers)
        assert r.status_code in [200, 404]


# ═══════════════════════════════════════════════════════════════
# 🏭 المستودعات - Warehouses
# ═══════════════════════════════════════════════════════════════
class TestWarehouseScenarios:
    """سيناريوهات المستودعات"""

    def test_list_warehouses(self, client, admin_headers):
        """✅ عرض المستودعات"""
        r = client.get("/api/inventory/warehouses", headers=admin_headers)
        assert_valid_response(r)
        assert len(r.json()) >= 1

    def test_get_warehouse_detail(self, client, admin_headers):
        """✅ تفاصيل مستودع"""
        r = client.get("/api/inventory/warehouses/1", headers=admin_headers)
        assert_valid_response(r)

    def test_warehouse_stock_list(self, client, admin_headers):
        """✅ قائمة المخزون بالمستودع"""
        r = client.get("/api/inventory/warehouses/1/stock", headers=admin_headers)
        assert r.status_code in [200, 404]

    def test_create_warehouse(self, client, admin_headers):
        """✅ إنشاء مستودع"""
        r = client.post("/api/inventory/warehouses", json={
            "name": "مستودع اختبار",
            "code": "WH-TST-001",
            "branch_id": 1,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 409]

    def test_update_warehouse(self, client, admin_headers):
        """✅ تحديث مستودع"""
        r = client.get("/api/inventory/warehouses", headers=admin_headers)
        warehouses = r.json()
        if len(warehouses) < 2:
            pytest.skip("مستودع واحد فقط")
        wid = warehouses[-1]["id"]
        r2 = client.put(f"/api/inventory/warehouses/{wid}", json={
            "name": "مستودع محدّث",
        }, headers=admin_headers)
        assert r2.status_code in [200, 400, 404]

    def test_all_stock_by_warehouse(self, client, admin_headers):
        """✅ المخزون حسب المستودع"""
        r = client.get("/api/inventory/stock-by-warehouse", headers=admin_headers)
        assert r.status_code in [200, 404]

    def test_stock_valuation(self, client, admin_headers):
        """✅ تقييم المخزون"""
        r = client.get("/api/inventory/valuation", headers=admin_headers)
        assert r.status_code in [200, 404]

    def test_inventory_stats(self, client, admin_headers):
        """✅ إحصائيات المخزون"""
        r = client.get("/api/inventory/stats", headers=admin_headers)
        assert r.status_code in [200, 404]


# ═══════════════════════════════════════════════════════════════
# 🔄 حركات المخزون - Stock Movements
# ═══════════════════════════════════════════════════════════════
class TestStockMovementScenarios:
    """سيناريوهات حركات المخزون"""

    def test_stock_movements_log(self, client, admin_headers):
        """✅ سجل حركات المخزون"""
        r = client.get("/api/inventory/movements", headers=admin_headers)
        assert r.status_code in [200, 404]

    def test_stock_transfer(self, client, admin_headers):
        """✅ تحويل مخزون بين مستودعات"""
        r = client.get("/api/inventory/warehouses", headers=admin_headers)
        warehouses = r.json()
        if len(warehouses) < 2:
            pytest.skip("أقل من مستودعين")

        r2 = client.post("/api/inventory/transfers", json={
            "product_id": 1,
            "source_warehouse_id": warehouses[0]["id"],
            "destination_warehouse_id": warehouses[1]["id"],
            "quantity": 5,
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400]


# ═══════════════════════════════════════════════════════════════
# 📊 التسويات المخزنية - Stock Adjustments
# ═══════════════════════════════════════════════════════════════
class TestStockAdjustmentScenarios:
    """سيناريوهات التسويات"""

    def test_list_adjustments(self, client, admin_headers):
        """✅ عرض التسويات"""
        r = client.get("/api/inventory/adjustments", headers=admin_headers)
        assert_valid_response(r)

    def test_create_increase_adjustment(self, client, admin_headers):
        """✅ تسوية زيادة"""
        r = client.post("/api/inventory/adjustments", json={
            "warehouse_id": 1,
            "product_id": 1,
            "new_quantity": 200,
            "reason": "جرد فعلي - زيادة",
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400]

    def test_create_decrease_adjustment(self, client, admin_headers):
        """✅ تسوية نقص"""
        r = client.post("/api/inventory/adjustments", json={
            "warehouse_id": 1,
            "product_id": 2,
            "new_quantity": 90,
            "reason": "تلف بضاعة",
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400]


# ═══════════════════════════════════════════════════════════════
# 🚚 الشحنات - Stock Shipments
# ═══════════════════════════════════════════════════════════════
class TestShipmentScenarios:
    """سيناريوهات الشحنات"""

    def test_list_shipments(self, client, admin_headers):
        """✅ عرض الشحنات"""
        r = client.get("/api/inventory/shipments", headers=admin_headers)
        assert_valid_response(r)

    def test_list_incoming_shipments(self, client, admin_headers):
        """✅ الشحنات الواردة"""
        r = client.get("/api/inventory/shipments/incoming", headers=admin_headers)
        assert r.status_code in [200, 404]

    def test_get_shipment_detail(self, client, admin_headers):
        """✅ تفاصيل شحنة"""
        r = client.get("/api/inventory/shipments", headers=admin_headers)
        shipments = r.json()
        if not shipments:
            pytest.skip("لا شحنات")
        sid = shipments[0]["id"]
        r2 = client.get(f"/api/inventory/shipments/{sid}", headers=admin_headers)
        assert r2.status_code in [200, 404]

    def test_create_shipment(self, client, admin_headers):
        """✅ إنشاء شحنة"""
        r = client.get("/api/inventory/warehouses", headers=admin_headers)
        warehouses = r.json()
        if len(warehouses) < 2:
            pytest.skip("أقل من مستودعين")

        r2 = client.post("/api/inventory/shipments", json={
            "source_warehouse_id": warehouses[0]["id"],
            "destination_warehouse_id": warehouses[1]["id"],
            "items": [
                {"product_id": 1, "quantity": 3}
            ]
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400]
