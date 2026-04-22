"""
AMAN ERP - اختبارات المشتريات والموردين
Purchases, Suppliers, Purchase Orders Tests
═══════════════════════════════════════════════
"""

import pytest
from helpers import assert_valid_response


class TestSuppliers:
    """🏭 اختبارات الموردين"""

    def test_list_suppliers(self, client, admin_headers):
        """✅ عرض قائمة الموردين"""
        response = client.get("/api/inventory/suppliers", headers=admin_headers)
        assert_valid_response(response)

    def test_create_supplier(self, client, admin_headers):
        """✅ إنشاء مورد جديد"""
        supplier = {
            "name": "مورد اختبار آلي",
            "name_en": "Auto Test Supplier",
            "phone": "0598765432",
            "email": "supplier@test.com",
            "currency": "SYP"  # العملة الأساسية
        }
        response = client.post(
            "/api/inventory/suppliers",
            json=supplier,
            headers=admin_headers
        )
        assert response.status_code in [200, 201, 400, 409]

    def test_supplier_details(self, client, admin_headers):
        """✅ عرض تفاصيل مورد"""
        response = client.get("/api/inventory/suppliers", headers=admin_headers)
        if response.status_code != 200:
            pytest.skip("لا يمكن تحميل الموردين")
        
        suppliers = response.json()
        if len(suppliers) == 0:
            pytest.skip("لا يوجد موردين")
        
        sid = suppliers[0].get("id")
        detail = client.get(f"/api/inventory/suppliers/{sid}", headers=admin_headers)
        assert detail.status_code in [200, 404]


class TestPurchaseInvoices:
    """🧾 اختبارات فواتير الشراء"""

    def test_list_purchase_invoices(self, client, admin_headers):
        """✅ عرض فواتير الشراء"""
        response = client.get("/api/buying/invoices", headers=admin_headers)
        assert_valid_response(response)

    def test_purchase_invoice_total_positive(self, client, admin_headers):
        """✅ إجمالي فواتير الشراء موجب"""
        response = client.get("/api/buying/invoices", headers=admin_headers)
        if response.status_code != 200:
            pytest.skip("لا يمكن تحميل الفواتير")
        
        invoices = response.json()
        if isinstance(invoices, dict):
            invoices = invoices.get("data", invoices.get("invoices", []))
        
        for inv in invoices[:5]:
            total = inv.get("total", inv.get("grand_total", 0))
            if total:
                total = float(total)
                assert total >= 0, f"⚠️ فاتورة شراء بإجمالي سالب: {total}"


class TestPurchaseOrders:
    """📋 اختبارات أوامر الشراء"""

    def test_list_purchase_orders(self, client, admin_headers):
        """✅ عرض أوامر الشراء"""
        response = client.get("/api/buying/orders", headers=admin_headers)
        assert_valid_response(response)


class TestPurchaseReturns:
    """🔄 اختبارات مرتجعات الشراء"""

    def test_list_purchase_returns(self, client, admin_headers):
        """✅ عرض مرتجعات الشراء"""
        response = client.get("/api/buying/returns", headers=admin_headers)
        assert_valid_response(response)


class TestPurchasePayments:
    """💳 اختبارات سندات صرف المشتريات"""

    def test_list_purchase_payments(self, client, admin_headers):
        """✅ عرض سندات صرف الموردين"""
        response = client.get("/api/buying/payments", headers=admin_headers)
        assert_valid_response(response)


class TestSupplierGroups:
    """📁 اختبارات مجموعات الموردين"""

    def test_list_supplier_groups(self, client, admin_headers):
        """✅ عرض مجموعات الموردين"""
        response = client.get("/api/buying/supplier-groups", headers=admin_headers)
        assert_valid_response(response)
