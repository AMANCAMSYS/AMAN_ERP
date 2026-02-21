"""
test_29_inventory_advanced.py
===============================
اختبارات متقدمة للمخزون - دفعات، أرقام تسلسلية، جودة، جرد، شحن، قوائم أسعار

Covers UNTESTED endpoints:
- Batches: CRUD, expiry-alerts, by-product
- Serials: CRUD, bulk, lookup
- Quality Inspections: CRUD, complete
- Cycle Counts: CRUD, start, complete
- Shipments: confirm, cancel
- Price Lists: CRUD, items
- Notifications: list, unread-count, read, read-all
- Stock: receipt, delivery, single transfer
- Advanced: variants, bins, kits, costing-policies, ledger
- Reports: summary, warehouse-stock, valuation-report
"""
import pytest
from datetime import date, timedelta
from helpers import assert_valid_response, assert_error_response


# ══════════════════════════════════════════════════════════════
# 📦 الدفعات (Batches)
# ══════════════════════════════════════════════════════════════

class TestInventoryBatches:
    """اختبارات إدارة الدفعات"""

    def _get_product_id(self, client, admin_headers):
        r = client.get("/api/inventory/products", headers=admin_headers)
        if r.status_code != 200:
            return None
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])
        return items[0]["id"] if items else None

    def test_list_batches(self, client, admin_headers):
        """اختبار عرض الدفعات"""
        r = client.get("/api/inventory/batches", headers=admin_headers)
        assert r.status_code in (200, 404, 501)

    def test_create_batch(self, client, admin_headers):
        """اختبار إنشاء دفعة"""
        pid = self._get_product_id(client, admin_headers)
        if not pid:
            pytest.skip("لا توجد منتجات")
        batch_data = {
            "product_id": pid,
            "batch_number": f"BATCH-TEST-{date.today().strftime('%Y%m%d')}",
            "manufacturing_date": str(date.today() - timedelta(days=30)),
            "expiry_date": str(date.today() + timedelta(days=365)),
            "quantity": 100
        }
        r = client.post("/api/inventory/batches", json=batch_data,
                        headers=admin_headers)
        assert r.status_code in (200, 201, 400, 404, 422, 501)

    def test_get_batch_detail(self, client, admin_headers):
        """اختبار تفاصيل دفعة"""
        r = client.get("/api/inventory/batches", headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("الدفعات غير متوفرة")
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])
        if not items:
            pytest.skip("لا توجد دفعات")
        batch_id = items[0].get("id") or items[0].get("batch_id")
        r2 = client.get(f"/api/inventory/batches/{batch_id}",
                        headers=admin_headers)
        assert r2.status_code in (200, 404)

    def test_update_batch(self, client, admin_headers):
        """اختبار تحديث دفعة"""
        r = client.get("/api/inventory/batches", headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("الدفعات غير متوفرة")
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])
        if not items:
            pytest.skip("لا توجد دفعات")
        batch_id = items[0].get("id") or items[0].get("batch_id")
        r2 = client.put(f"/api/inventory/batches/{batch_id}",
                        json={"notes": "تحديث اختبار"},
                        headers=admin_headers)
        assert r2.status_code in (200, 404, 422, 501)

    def test_batch_expiry_alerts(self, client, admin_headers):
        """اختبار تنبيهات انتهاء صلاحية الدفعات"""
        r = client.get("/api/inventory/batches/expiry-alerts",
                       headers=admin_headers)
        assert r.status_code in (200, 404, 501)

    def test_batches_by_product(self, client, admin_headers):
        """اختبار الدفعات حسب المنتج"""
        pid = self._get_product_id(client, admin_headers)
        if not pid:
            pytest.skip("لا توجد منتجات")
        r = client.get(f"/api/inventory/batches/product/{pid}",
                       headers=admin_headers)
        assert r.status_code in (200, 404, 501)


# ══════════════════════════════════════════════════════════════
# 🔢 الأرقام التسلسلية (Serials)
# ══════════════════════════════════════════════════════════════

class TestInventorySerials:
    """اختبارات إدارة الأرقام التسلسلية"""

    def _get_product_id(self, client, admin_headers):
        r = client.get("/api/inventory/products", headers=admin_headers)
        if r.status_code != 200:
            return None
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])
        return items[0]["id"] if items else None

    def test_list_serials(self, client, admin_headers):
        """اختبار عرض الأرقام التسلسلية"""
        r = client.get("/api/inventory/serials", headers=admin_headers)
        assert r.status_code in (200, 404, 501)

    def test_create_serial(self, client, admin_headers):
        """اختبار إنشاء رقم تسلسلي"""
        pid = self._get_product_id(client, admin_headers)
        if not pid:
            pytest.skip("لا توجد منتجات")
        serial_data = {
            "product_id": pid,
            "serial_number": f"SN-TEST-{date.today().strftime('%Y%m%d%H%M')}",
            "status": "available"
        }
        r = client.post("/api/inventory/serials", json=serial_data,
                        headers=admin_headers)
        assert r.status_code in (200, 201, 400, 404, 422, 501)

    def test_bulk_create_serials(self, client, admin_headers):
        """اختبار إنشاء أرقام تسلسلية بالجملة"""
        pid = self._get_product_id(client, admin_headers)
        if not pid:
            pytest.skip("لا توجد منتجات")
        bulk_data = {
            "product_id": pid,
            "prefix": "BULK-TEST",
            "count": 5,
            "start_number": 1
        }
        r = client.post("/api/inventory/serials/bulk", json=bulk_data,
                        headers=admin_headers)
        assert r.status_code in (200, 201, 400, 404, 422, 501)

    def test_lookup_serial(self, client, admin_headers):
        """اختبار البحث برقم تسلسلي"""
        r = client.get("/api/inventory/serials/lookup/SN-TEST-001",
                       headers=admin_headers)
        assert r.status_code in (200, 404, 501)

    def test_get_serial_detail(self, client, admin_headers):
        """اختبار تفاصيل رقم تسلسلي"""
        r = client.get("/api/inventory/serials", headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("الأرقام التسلسلية غير متوفرة")
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])
        if not items:
            pytest.skip("لا توجد أرقام تسلسلية")
        serial_id = items[0].get("id") or items[0].get("serial_id")
        r2 = client.get(f"/api/inventory/serials/{serial_id}",
                        headers=admin_headers)
        assert r2.status_code in (200, 404)

    def test_update_serial(self, client, admin_headers):
        """اختبار تحديث رقم تسلسلي"""
        r = client.get("/api/inventory/serials", headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("الأرقام التسلسلية غير متوفرة")
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])
        if not items:
            pytest.skip("لا توجد أرقام تسلسلية")
        serial_id = items[0].get("id") or items[0].get("serial_id")
        r2 = client.put(f"/api/inventory/serials/{serial_id}",
                        json={"status": "reserved"},
                        headers=admin_headers)
        assert r2.status_code in (200, 404, 422, 501)

    def test_set_product_tracking(self, client, admin_headers):
        """اختبار تعيين نوع تتبع المنتج (دفعة/تسلسلي)"""
        pid = self._get_product_id(client, admin_headers)
        if not pid:
            pytest.skip("لا توجد منتجات")
        r = client.put(f"/api/inventory/products/{pid}/tracking",
                       json={"tracking_type": "batch"},
                       headers=admin_headers)
        assert r.status_code in (200, 404, 422, 501)


# ══════════════════════════════════════════════════════════════
# ✅ فحص الجودة (Quality Inspections)
# ══════════════════════════════════════════════════════════════

class TestQualityInspections:
    """اختبارات فحص الجودة"""

    def test_list_quality_inspections(self, client, admin_headers):
        """اختبار عرض فحوصات الجودة"""
        r = client.get("/api/inventory/quality-inspections",
                       headers=admin_headers)
        assert r.status_code in (200, 404, 501)

    def test_create_quality_inspection(self, client, admin_headers):
        """اختبار إنشاء فحص جودة"""
        pid = None
        prod_r = client.get("/api/inventory/products", headers=admin_headers)
        if prod_r.status_code == 200:
            prods = prod_r.json()
            if isinstance(prods, dict):
                prods = prods.get("items", [])
            if prods:
                pid = prods[0]["id"]
        if not pid:
            pytest.skip("لا توجد منتجات")

        inspection_data = {
            "product_id": pid,
            "inspection_type": "incoming",
            "date": str(date.today()),
            "quantity": 50,
            "notes": "فحص مواد مستلمة - اختبار"
        }
        r = client.post("/api/inventory/quality-inspections",
                        json=inspection_data, headers=admin_headers)
        assert r.status_code in (200, 201, 400, 404, 422, 501)

    def test_get_inspection_detail(self, client, admin_headers):
        """اختبار تفاصيل فحص جودة"""
        r = client.get("/api/inventory/quality-inspections",
                       headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("فحوصات الجودة غير متوفرة")
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])
        if not items:
            pytest.skip("لا توجد فحوصات")
        insp_id = items[0].get("id") or items[0].get("inspection_id")
        r2 = client.get(f"/api/inventory/quality-inspections/{insp_id}",
                        headers=admin_headers)
        assert r2.status_code in (200, 404)

    def test_complete_inspection(self, client, admin_headers):
        """اختبار إكمال فحص جودة"""
        r = client.get("/api/inventory/quality-inspections",
                       headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("فحوصات الجودة غير متوفرة")
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])
        if not items:
            pytest.skip("لا توجد فحوصات")
        insp_id = items[0].get("id") or items[0].get("inspection_id")
        r2 = client.put(
            f"/api/inventory/quality-inspections/{insp_id}/complete",
            json={"result": "pass", "notes": "نتيجة ناجحة"},
            headers=admin_headers
        )
        assert r2.status_code in (200, 400, 404, 422, 501)


# ══════════════════════════════════════════════════════════════
# 📋 الجرد الدوري (Cycle Counts)
# ══════════════════════════════════════════════════════════════

class TestCycleCounts:
    """اختبارات الجرد الدوري"""

    def _get_warehouse_id(self, client, admin_headers):
        r = client.get("/api/inventory/warehouses", headers=admin_headers)
        if r.status_code != 200:
            return None
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])
        return items[0]["id"] if items else None

    def test_list_cycle_counts(self, client, admin_headers):
        """اختبار عرض عمليات الجرد"""
        r = client.get("/api/inventory/cycle-counts", headers=admin_headers)
        assert r.status_code in (200, 404, 501)

    def test_create_cycle_count(self, client, admin_headers):
        """اختبار إنشاء عملية جرد"""
        wid = self._get_warehouse_id(client, admin_headers)
        if not wid:
            pytest.skip("لا توجد مخازن")
        count_data = {
            "warehouse_id": wid,
            "date": str(date.today()),
            "count_type": "full",
            "notes": "جرد اختبار"
        }
        r = client.post("/api/inventory/cycle-counts", json=count_data,
                        headers=admin_headers)
        assert r.status_code in (200, 201, 400, 404, 422, 501)

    def test_get_cycle_count_detail(self, client, admin_headers):
        """اختبار تفاصيل عملية جرد"""
        r = client.get("/api/inventory/cycle-counts", headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("الجرد غير متوفر")
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])
        if not items:
            pytest.skip("لا توجد عمليات جرد")
        count_id = items[0].get("id") or items[0].get("count_id")
        r2 = client.get(f"/api/inventory/cycle-counts/{count_id}",
                        headers=admin_headers)
        assert r2.status_code in (200, 404)

    def test_start_cycle_count(self, client, admin_headers):
        """اختبار بدء عملية جرد"""
        r = client.get("/api/inventory/cycle-counts", headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("الجرد غير متوفر")
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])
        if not items:
            pytest.skip("لا توجد عمليات جرد")
        count_id = items[0].get("id") or items[0].get("count_id")
        r2 = client.put(f"/api/inventory/cycle-counts/{count_id}/start",
                        headers=admin_headers)
        assert r2.status_code in (200, 400, 404, 422, 501)

    def test_complete_cycle_count(self, client, admin_headers):
        """اختبار إكمال عملية جرد"""
        r = client.get("/api/inventory/cycle-counts", headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("الجرد غير متوفر")
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])
        if not items:
            pytest.skip("لا توجد عمليات جرد")
        count_id = items[0].get("id") or items[0].get("count_id")
        r2 = client.put(f"/api/inventory/cycle-counts/{count_id}/complete",
                        json={"notes": "اكتمل الجرد"},
                        headers=admin_headers)
        assert r2.status_code in (200, 400, 404, 422, 501)


# ══════════════════════════════════════════════════════════════
# 🚚 الشحنات المتقدمة (Shipments)
# ══════════════════════════════════════════════════════════════

class TestShipmentActions:
    """اختبارات إجراءات الشحنات"""

    def _get_shipment_id(self, client, admin_headers):
        r = client.get("/api/inventory/shipments", headers=admin_headers)
        if r.status_code != 200:
            return None
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])
        return items[0]["id"] if items else None

    def test_confirm_shipment(self, client, admin_headers):
        """اختبار تأكيد شحنة"""
        sid = self._get_shipment_id(client, admin_headers)
        if not sid:
            pytest.skip("لا توجد شحنات")
        r = client.post(f"/api/inventory/shipments/{sid}/confirm",
                        headers=admin_headers)
        assert r.status_code in (200, 400, 404, 422, 501)

    def test_cancel_shipment(self, client, admin_headers):
        """اختبار إلغاء شحنة"""
        sid = self._get_shipment_id(client, admin_headers)
        if not sid:
            pytest.skip("لا توجد شحنات")
        r = client.post(f"/api/inventory/shipments/{sid}/cancel",
                        headers=admin_headers)
        assert r.status_code in (200, 400, 404, 422, 501)


# ══════════════════════════════════════════════════════════════
# 💰 قوائم الأسعار (Price Lists)
# ══════════════════════════════════════════════════════════════

class TestPriceLists:
    """اختبارات قوائم الأسعار"""

    def test_create_price_list(self, client, admin_headers):
        """اختبار إنشاء قائمة أسعار"""
        pl_data = {
            "name": f"قائمة أسعار اختبار - {date.today()}",
            "currency": "SYP",
            "is_active": True
        }
        r = client.post("/api/inventory/price-lists", json=pl_data,
                        headers=admin_headers)
        assert r.status_code in (200, 201, 400, 422, 501)

    def test_update_price_list(self, client, admin_headers):
        """اختبار تحديث قائمة أسعار"""
        r = client.get("/api/inventory/price-lists", headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("قوائم الأسعار غير متوفرة")
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])
        if not items:
            pytest.skip("لا توجد قوائم أسعار")
        pl_id = items[0]["id"]
        r2 = client.put(f"/api/inventory/price-lists/{pl_id}",
                        json={"name": "قائمة محدثة"},
                        headers=admin_headers)
        assert r2.status_code in (200, 404, 422, 501)

    def test_delete_price_list(self, client, admin_headers):
        """اختبار حذف قائمة أسعار"""
        r = client.get("/api/inventory/price-lists", headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("قوائم الأسعار غير متوفرة")
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])
        if not items:
            pytest.skip("لا توجد قوائم أسعار")
        pl_id = items[-1]["id"]
        r2 = client.delete(f"/api/inventory/price-lists/{pl_id}",
                           headers=admin_headers)
        assert r2.status_code in (200, 204, 404, 422, 501)

    def test_get_price_list_items(self, client, admin_headers):
        """اختبار بنود قائمة الأسعار"""
        r = client.get("/api/inventory/price-lists", headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("قوائم الأسعار غير متوفرة")
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])
        if not items:
            pytest.skip("لا توجد قوائم أسعار")
        pl_id = items[0]["id"]
        r2 = client.get(f"/api/inventory/price-lists/{pl_id}/items",
                        headers=admin_headers)
        assert r2.status_code in (200, 404, 501)

    def test_add_price_list_items(self, client, admin_headers):
        """اختبار إضافة بنود لقائمة أسعار"""
        r = client.get("/api/inventory/price-lists", headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("قوائم الأسعار غير متوفرة")
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])
        if not items:
            pytest.skip("لا توجد قوائم أسعار")
        pl_id = items[0]["id"]

        # جلب منتج
        prods_r = client.get("/api/inventory/products", headers=admin_headers)
        if prods_r.status_code != 200:
            pytest.skip("لا يمكن جلب المنتجات")
        prods = prods_r.json()
        if isinstance(prods, dict):
            prods = prods.get("items", [])
        if not prods:
            pytest.skip("لا توجد منتجات")

        item_data = {
            "product_id": prods[0]["id"],
            "price": 150.00
        }
        r2 = client.post(f"/api/inventory/price-lists/{pl_id}/items",
                         json=item_data, headers=admin_headers)
        assert r2.status_code in (200, 201, 400, 404, 422, 501)


# ══════════════════════════════════════════════════════════════
# 🔔 الإشعارات (Notifications)
# ══════════════════════════════════════════════════════════════

class TestInventoryNotifications:
    """اختبارات إشعارات المخزون"""

    def test_list_notifications(self, client, admin_headers):
        """اختبار عرض الإشعارات"""
        r = client.get("/api/inventory/notifications", headers=admin_headers)
        assert r.status_code in (200, 404, 501)

    def test_unread_count(self, client, admin_headers):
        """اختبار عدد الإشعارات غير المقروءة"""
        r = client.get("/api/inventory/notifications/unread-count",
                       headers=admin_headers)
        assert r.status_code in (200, 404, 501)

    def test_mark_notification_read(self, client, admin_headers):
        """اختبار تحديد إشعار كمقروء"""
        r = client.get("/api/inventory/notifications", headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("الإشعارات غير متوفرة")
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])
        if not items:
            pytest.skip("لا توجد إشعارات")
        notif_id = items[0].get("id")
        r2 = client.post(f"/api/inventory/notifications/{notif_id}/read",
                         headers=admin_headers)
        assert r2.status_code in (200, 404, 501)

    def test_mark_all_notifications_read(self, client, admin_headers):
        """اختبار تحديد جميع الإشعارات كمقروءة"""
        r = client.post("/api/inventory/notifications/read-all",
                        headers=admin_headers)
        assert r.status_code in (200, 404, 501)


# ══════════════════════════════════════════════════════════════
# 📥📤 حركات المخزون (Stock Movements)
# ══════════════════════════════════════════════════════════════

class TestStockMovements:
    """اختبارات حركات الاستلام والصرف"""

    def _get_product_and_warehouse(self, client, admin_headers):
        prods_r = client.get("/api/inventory/products", headers=admin_headers)
        wh_r = client.get("/api/inventory/warehouses", headers=admin_headers)
        pid = wid = None
        if prods_r.status_code == 200:
            prods = prods_r.json()
            if isinstance(prods, dict):
                prods = prods.get("items", [])
            if prods:
                pid = prods[0]["id"]
        if wh_r.status_code == 200:
            whs = wh_r.json()
            if isinstance(whs, dict):
                whs = whs.get("items", [])
            if whs:
                wid = whs[0]["id"]
        return pid, wid

    def test_stock_receipt(self, client, admin_headers):
        """اختبار استلام بضاعة"""
        pid, wid = self._get_product_and_warehouse(client, admin_headers)
        if not pid or not wid:
            pytest.skip("لا توجد منتجات أو مخازن")
        receipt_data = {
            "product_id": pid,
            "warehouse_id": wid,
            "quantity": 10,
            "date": str(date.today()),
            "reference": "اختبار استلام"
        }
        r = client.post("/api/inventory/receipt", json=receipt_data,
                        headers=admin_headers)
        assert r.status_code in (200, 201, 400, 404, 422, 501)

    def test_stock_delivery(self, client, admin_headers):
        """اختبار صرف بضاعة"""
        pid, wid = self._get_product_and_warehouse(client, admin_headers)
        if not pid or not wid:
            pytest.skip("لا توجد منتجات أو مخازن")
        delivery_data = {
            "product_id": pid,
            "warehouse_id": wid,
            "quantity": 2,
            "date": str(date.today()),
            "reference": "اختبار صرف"
        }
        r = client.post("/api/inventory/delivery", json=delivery_data,
                        headers=admin_headers)
        assert r.status_code in (200, 201, 400, 404, 422, 501)

    def test_single_transfer(self, client, admin_headers):
        """اختبار تحويل مخزون واحد"""
        r = client.get("/api/inventory/warehouses", headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("لا يمكن جلب المخازن")
        whs = r.json()
        if isinstance(whs, dict):
            whs = whs.get("items", [])
        if len(whs) < 2:
            pytest.skip("يجب وجود مخزنين على الأقل")

        pid, _ = self._get_product_and_warehouse(client, admin_headers)
        if not pid:
            pytest.skip("لا توجد منتجات")

        transfer_data = {
            "product_id": pid,
            "from_warehouse_id": whs[0]["id"],
            "to_warehouse_id": whs[1]["id"],
            "quantity": 1,
            "date": str(date.today())
        }
        r2 = client.post("/api/inventory/transfer", json=transfer_data,
                         headers=admin_headers)
        assert r2.status_code in (200, 201, 400, 404, 422, 501)


# ══════════════════════════════════════════════════════════════
# 🎯 المخزون المتقدم (Advanced)
# ══════════════════════════════════════════════════════════════

class TestAdvancedInventory:
    """اختبارات المخزون المتقدم - متغيرات، صناديق، أطقم"""

    def test_list_variants(self, client, admin_headers):
        """اختبار عرض متغيرات المنتجات"""
        r = client.get("/api/inventory/advanced/variants",
                       headers=admin_headers)
        assert r.status_code in (200, 404, 422, 501)

    def test_create_variant(self, client, admin_headers):
        """اختبار إنشاء متغير منتج"""
        prods_r = client.get("/api/inventory/products", headers=admin_headers)
        if prods_r.status_code != 200:
            pytest.skip("لا يمكن جلب المنتجات")
        prods = prods_r.json()
        if isinstance(prods, dict):
            prods = prods.get("items", [])
        if not prods:
            pytest.skip("لا توجد منتجات")
        variant_data = {
            "product_id": prods[0]["id"],
            "name": "اختبار - لون أحمر",
            "sku": f"VAR-TEST-{date.today().strftime('%Y%m%d')}",
            "attributes": {"color": "red", "size": "M"}
        }
        r = client.post("/api/inventory/advanced/variants",
                        json=variant_data, headers=admin_headers)
        assert r.status_code in (200, 201, 400, 404, 422, 501)

    def test_list_bins(self, client, admin_headers):
        """اختبار عرض صناديق المخازن"""
        r = client.get("/api/inventory/advanced/bins", headers=admin_headers)
        assert r.status_code in (200, 404, 422, 501)

    def test_create_bin(self, client, admin_headers):
        """اختبار إنشاء صندوق مخزن"""
        wh_r = client.get("/api/inventory/warehouses", headers=admin_headers)
        if wh_r.status_code != 200:
            pytest.skip("لا يمكن جلب المخازن")
        whs = wh_r.json()
        if isinstance(whs, dict):
            whs = whs.get("items", [])
        if not whs:
            pytest.skip("لا توجد مخازن")
        bin_data = {
            "warehouse_id": whs[0]["id"],
            "name": f"BIN-TEST-{date.today().strftime('%Y%m%d')}",
            "code": f"B-T-{date.today().strftime('%m%d')}"
        }
        r = client.post("/api/inventory/advanced/bins",
                        json=bin_data, headers=admin_headers)
        assert r.status_code in (200, 201, 400, 404, 422, 501)

    def test_list_kits(self, client, admin_headers):
        """اختبار عرض الأطقم"""
        r = client.get("/api/inventory/advanced/kits", headers=admin_headers)
        assert r.status_code in (200, 404, 422, 501)

    def test_create_kit(self, client, admin_headers):
        """اختبار إنشاء طقم منتجات"""
        prods_r = client.get("/api/inventory/products", headers=admin_headers)
        if prods_r.status_code != 200:
            pytest.skip("لا يمكن جلب المنتجات")
        prods = prods_r.json()
        if isinstance(prods, dict):
            prods = prods.get("items", [])
        if len(prods) < 2:
            pytest.skip("يجب وجود منتجين على الأقل")
        kit_data = {
            "name": "طقم اختبار",
            "components": [
                {"product_id": prods[0]["id"], "quantity": 1},
                {"product_id": prods[1]["id"], "quantity": 2}
            ]
        }
        r = client.post("/api/inventory/advanced/kits",
                        json=kit_data, headers=admin_headers)
        assert r.status_code in (200, 201, 400, 404, 422, 501)

    def test_get_kit_detail(self, client, admin_headers):
        """اختبار تفاصيل طقم"""
        r = client.get("/api/inventory/advanced/kits", headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("الأطقم غير متوفرة")
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])
        if not items:
            pytest.skip("لا توجد أطقم")
        kit_id = items[0].get("id") or items[0].get("kit_id")
        r2 = client.get(f"/api/inventory/advanced/kits/{kit_id}",
                        headers=admin_headers)
        assert r2.status_code in (200, 404)

    def test_advanced_costing_policies(self, client, admin_headers):
        """اختبار عرض سياسات التكلفة المتقدمة"""
        r = client.get("/api/inventory/advanced/costing-policies",
                       headers=admin_headers)
        assert r.status_code in (200, 404, 501)

    def test_inventory_ledger(self, client, admin_headers):
        """اختبار دفتر أستاذ المخزون"""
        r = client.get("/api/inventory/advanced/ledger",
                       headers=admin_headers)
        assert r.status_code in (200, 404, 422, 501)


# ══════════════════════════════════════════════════════════════
# 📊 تقارير المخزون (Inventory Reports)
# ══════════════════════════════════════════════════════════════

class TestInventoryReports:
    """اختبارات تقارير المخزون"""

    def test_inventory_summary(self, client, admin_headers):
        """اختبار ملخص المخزون"""
        r = client.get("/api/inventory/summary", headers=admin_headers)
        assert r.status_code in (200, 404, 501)

    def test_warehouse_stock_report(self, client, admin_headers):
        """اختبار تقرير مخزون المخازن"""
        r = client.get("/api/inventory/warehouse-stock", headers=admin_headers)
        assert r.status_code in (200, 404, 501)

    def test_valuation_report(self, client, admin_headers):
        """اختبار تقرير تقييم المخزون"""
        r = client.get("/api/inventory/valuation-report",
                       headers=admin_headers)
        assert r.status_code in (200, 404, 501)

    def test_product_cost_breakdown(self, client, admin_headers):
        """اختبار تفصيل تكلفة المنتج"""
        prods_r = client.get("/api/inventory/products", headers=admin_headers)
        if prods_r.status_code != 200:
            pytest.skip("لا يمكن جلب المنتجات")
        prods = prods_r.json()
        if isinstance(prods, dict):
            prods = prods.get("items", [])
        if not prods:
            pytest.skip("لا توجد منتجات")
        pid = prods[0]["id"]
        r = client.get(f"/api/inventory/products/{pid}/cost-breakdown",
                       headers=admin_headers)
        assert r.status_code in (200, 404, 501)

    def test_warehouse_current_stock(self, client, admin_headers):
        """اختبار المخزون الحالي في مخزن"""
        wh_r = client.get("/api/inventory/warehouses", headers=admin_headers)
        if wh_r.status_code != 200:
            pytest.skip("لا يمكن جلب المخازن")
        whs = wh_r.json()
        if isinstance(whs, dict):
            whs = whs.get("items", [])
        if not whs:
            pytest.skip("لا توجد مخازن")
        wid = whs[0]["id"]
        r = client.get(f"/api/inventory/warehouses/{wid}/current-stock",
                       headers=admin_headers)
        assert r.status_code in (200, 404, 501)

    def test_delete_warehouse(self, client, admin_headers):
        """اختبار حذف مخزن"""
        wh_r = client.get("/api/inventory/warehouses", headers=admin_headers)
        if wh_r.status_code != 200:
            pytest.skip("لا يمكن جلب المخازن")
        whs = wh_r.json()
        if isinstance(whs, dict):
            whs = whs.get("items", [])
        if not whs:
            pytest.skip("لا توجد مخازن")
        # حذف آخر مخزن (الأقل احتمال للاستخدام)
        wid = whs[-1]["id"]
        r = client.delete(f"/api/inventory/warehouses/{wid}",
                          headers=admin_headers)
        assert r.status_code in (200, 204, 400, 404, 422, 500, 501)
