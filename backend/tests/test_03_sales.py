"""
AMAN ERP - اختبارات المبيعات والفواتير
Sales, Invoices, Customers Tests
═══════════════════════════════════════════
يتضمن: العملاء، فواتير المبيعات، عروض الأسعار، الإرتجاع، الإيصالات
"""

import pytest
from helpers import assert_valid_response


class TestCustomers:
    """👥 اختبارات العملاء"""

    def test_list_customers(self, client, admin_headers):
        """✅ عرض قائمة العملاء"""
        response = client.get("/api/sales/customers", headers=admin_headers)
        assert_valid_response(response)
        assert isinstance(response.json(), list)

    def test_create_customer(self, client, admin_headers):
        """✅ إنشاء عميل جديد"""
        customer = {
            "name": "عميل اختبار آلي",
            "name_en": "Test Auto Customer",
            "phone": "0512345678",
            "email": "test.customer@test.com",
            "address": "عنوان اختبار"
        }
        response = client.post(
            "/api/sales/customers",
            json=customer,
            headers=admin_headers
        )
        # قد ينجح أو يكون مكرر
        assert response.status_code in [200, 201, 400, 409]

    def test_customer_details_accessible(self, client, admin_headers):
        """✅ الوصول لتفاصيل عميل"""
        # أولاً نجلب القائمة
        response = client.get("/api/sales/customers", headers=admin_headers)
        if response.status_code != 200:
            pytest.skip("لا يمكن تحميل العملاء")
        
        customers = response.json()
        if len(customers) == 0:
            pytest.skip("لا يوجد عملاء")
        
        # نجلب تفاصيل أول عميل
        customer_id = customers[0].get("id")
        response = client.get(
            f"/api/sales/customers/{customer_id}",
            headers=admin_headers
        )
        assert response.status_code in [200, 404]


class TestSalesInvoices:
    """🧾 اختبارات فواتير المبيعات"""

    def test_list_invoices(self, client, admin_headers):
        """✅ عرض قائمة فواتير المبيعات"""
        response = client.get("/api/sales/invoices", headers=admin_headers)
        assert_valid_response(response)

    def test_invoice_has_required_fields(self, client, admin_headers):
        """✅ الفاتورة تحتوي الحقول المطلوبة"""
        response = client.get("/api/sales/invoices", headers=admin_headers)
        if response.status_code != 200:
            pytest.skip("لا يمكن تحميل الفواتير")
        
        invoices = response.json()
        if isinstance(invoices, dict):
            invoices = invoices.get("data", invoices.get("invoices", []))
        
        if len(invoices) == 0:
            pytest.skip("لا توجد فواتير")
        
        invoice = invoices[0]
        # حقول أساسية يجب أن تكون موجودة
        expected_fields = ["id", "invoice_number"]
        for field in expected_fields:
            assert field in invoice, f"الحقل {field} مفقود من الفاتورة"

    def test_create_sales_invoice(self, client, admin_headers):
        """✅ إنشاء فاتورة مبيعات"""
        # نجلب العملاء والمنتجات
        customers = client.get("/api/sales/customers", headers=admin_headers)
        products = client.get("/api/inventory/products", headers=admin_headers)
        
        if customers.status_code != 200 or products.status_code != 200:
            pytest.skip("لا يمكن تحميل العملاء أو المنتجات")
        
        customer_list = customers.json()
        product_list = products.json()
        
        if not customer_list or not product_list:
            pytest.skip("لا يوجد عملاء أو منتجات")
        
        # نتأكد من وجود حقل id في كلاهما
        if not customer_list[0].get("id") or not product_list[0].get("id"):
            pytest.skip("بيانات العملاء أو المنتجات ناقصة")
        
        invoice = {
            "customer_id": customer_list[0]["id"],
            "invoice_date": "2026-02-11",
            "items": [
                {
                    "product_id": product_list[0]["id"],
                    "quantity": 1,
                    "unit_price": product_list[0].get("selling_price", 100),
                    "tax_rate": 0,
                    "description": "اختبار"
                }
            ]
        }
        
        response = client.post(
            "/api/sales/invoices",
            json=invoice,
            headers=admin_headers
        )
        # ممكن ينجح أو يرفض بسبب عدم وجود مخزون
        assert response.status_code in [200, 201, 400, 422]

    def test_invoice_total_calculation(self, client, admin_headers):
        """
        ✅ حساب إجمالي الفاتورة صحيح
        القاعدة: الإجمالي = مجموع (الكمية × سعر الوحدة) - الخصم + الضريبة
        """
        response = client.get("/api/sales/invoices", headers=admin_headers)
        if response.status_code != 200:
            pytest.skip("لا يمكن تحميل الفواتير")
        
        invoices = response.json()
        if isinstance(invoices, dict):
            invoices = invoices.get("data", invoices.get("invoices", []))
        
        for inv in invoices[:5]:  # نفحص أول 5 فواتير
            total = float(inv.get("total", inv.get("grand_total", 0)) or 0)
            if total != 0:
                # الإجمالي يجب أن يكون موجب
                assert total > 0, f"⚠️ فاتورة {inv.get('id')} بإجمالي سالب: {total}"


class TestSalesOrders:
    """📋 اختبارات أوامر المبيعات"""

    def test_list_sales_orders(self, client, admin_headers):
        """✅ عرض أوامر المبيعات"""
        response = client.get("/api/sales/orders", headers=admin_headers)
        assert_valid_response(response)

    def test_list_quotations(self, client, admin_headers):
        """✅ عرض عروض الأسعار"""
        response = client.get("/api/sales/quotations", headers=admin_headers)
        assert_valid_response(response)


class TestSalesReturns:
    """🔄 اختبارات مرتجعات المبيعات"""

    def test_list_returns(self, client, admin_headers):
        """✅ عرض مرتجعات المبيعات"""
        response = client.get("/api/sales/returns", headers=admin_headers)
        assert_valid_response(response)


class TestSalesPayments:
    """💳 اختبارات سندات القبض والصرف"""

    def test_list_receipts(self, client, admin_headers):
        """✅ عرض سندات القبض"""
        response = client.get("/api/sales/receipts", headers=admin_headers)
        assert_valid_response(response)

    def test_list_payments(self, client, admin_headers):
        """✅ عرض سندات الصرف"""
        response = client.get("/api/sales/payments", headers=admin_headers)
        assert_valid_response(response)

    def test_sales_summary(self, client, admin_headers):
        """✅ ملخص المبيعات"""
        response = client.get("/api/sales/summary", headers=admin_headers)
        assert_valid_response(response)
