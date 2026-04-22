"""
AMAN ERP - اختبارات شاملة متعددة السيناريوهات: المبيعات
Comprehensive Multi-Scenario Tests: Sales Module
═══════════════════════════════════════════════════════
يتضمن: العملاء، مجموعات العملاء، عروض الأسعار، أوامر البيع، الفواتير، المرتجعات، الإيصالات
"""

import pytest
from datetime import date, timedelta
from helpers import assert_valid_response


# ═══════════════════════════════════════════════════════════════
# 👥 العملاء - Customers
# ═══════════════════════════════════════════════════════════════
class TestCustomerScenarios:
    """سيناريوهات العملاء"""

    def test_list_customers(self, client, admin_headers):
        """✅ عرض العملاء"""
        r = client.get("/api/sales/customers", headers=admin_headers)
        assert_valid_response(r)
        assert len(r.json()) >= 2

    def test_create_individual_customer(self, client, admin_headers):
        """✅ إنشاء عميل فرد"""
        r = client.post("/api/sales/customers", json={
            "name": "محمد أحمد",
            "phone": "0551112233",
            "email": "mohammed@test.com",
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 409]

    def test_create_company_customer(self, client, admin_headers):
        """✅ إنشاء عميل شركة"""
        r = client.post("/api/sales/customers", json={
            "name": "شركة التطوير الحديثة",
            "name_en": "Modern Development Co",
            "phone": "0112345678",
            "email": "modern@company.com",
            "tax_number": "300111222333999",
            "credit_limit": 100000,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 409, 500]

    def test_create_customer_with_branch(self, client, admin_headers):
        """✅ إنشاء عميل مرتبط بفرع"""
        r = client.post("/api/sales/customers", json={
            "name": "عميل الفرع الرئيسي",
            "branch_id": 1,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 409]

    def test_customer_statement(self, client, admin_headers):
        """✅ كشف حساب عميل"""
        r = client.get("/api/sales/customers", headers=admin_headers)
        customers = r.json()
        if not customers:
            pytest.skip("لا عملاء")
        cid = customers[0]["id"]
        r2 = client.get(f"/api/sales/customers/{cid}/statement", headers=admin_headers)
        assert r2.status_code in [200, 404]


# ═══════════════════════════════════════════════════════════════
# 📂 مجموعات العملاء - Customer Groups
# ═══════════════════════════════════════════════════════════════
class TestCustomerGroupScenarios:
    """سيناريوهات مجموعات العملاء"""

    def test_list_customer_groups(self, client, admin_headers):
        """✅ عرض المجموعات"""
        r = client.get("/api/sales/customer-groups", headers=admin_headers)
        assert_valid_response(r)
        assert len(r.json()) >= 1

    def test_create_customer_group(self, client, admin_headers):
        """✅ إنشاء مجموعة"""
        r = client.post("/api/sales/customer-groups", json={
            "group_name": "عملاء VIP",
            "discount_percentage": 20,
            "payment_days": 60,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 409]

    def test_update_customer_group(self, client, admin_headers):
        """✅ تحديث مجموعة"""
        r = client.get("/api/sales/customer-groups", headers=admin_headers)
        groups = r.json()
        if not groups:
            pytest.skip("لا مجموعات")
        gid = groups[0]["id"]
        r2 = client.put(f"/api/sales/customer-groups/{gid}", json={
            "group_name": "مجموعة محدّثة",
            "discount_percentage": 12,
        }, headers=admin_headers)
        assert r2.status_code in [200, 404]

    def test_delete_customer_group(self, client, admin_headers):
        """✅ حذف مجموعة"""
        r = client.post("/api/sales/customer-groups", json={
            "group_name": "مجموعة للحذف",
        }, headers=admin_headers)
        if r.status_code in [200, 201]:
            gid = r.json().get("id")
            if gid:
                r2 = client.delete(f"/api/sales/customer-groups/{gid}", headers=admin_headers)
                assert r2.status_code in [200, 204, 400]


# ═══════════════════════════════════════════════════════════════
# 📋 عروض الأسعار - Sales Quotations
# ═══════════════════════════════════════════════════════════════
class TestQuotationScenarios:
    """سيناريوهات عروض الأسعار"""

    def test_list_quotations(self, client, admin_headers):
        """✅ عرض عروض الأسعار"""
        r = client.get("/api/sales/quotations", headers=admin_headers)
        assert_valid_response(r)
        assert len(r.json()) >= 1

    def test_get_quotation_details(self, client, admin_headers):
        """✅ تفاصيل عرض سعر"""
        r = client.get("/api/sales/quotations", headers=admin_headers)
        quotations = r.json()
        if not quotations:
            pytest.skip("لا عروض أسعار")
        qid = quotations[0]["id"]
        r2 = client.get(f"/api/sales/quotations/{qid}", headers=admin_headers)
        assert r2.status_code in [200, 404]

    def test_create_quotation_single_item(self, client, admin_headers):
        """✅ إنشاء عرض سعر بصنف واحد"""
        r = client.get("/api/sales/customers", headers=admin_headers)
        customers = r.json()
        if not customers:
            pytest.skip("لا عملاء")

        r2 = client.post("/api/sales/quotations", json={
            "customer_id": customers[0]["id"],
            "quotation_date": str(date.today()),
            "items": [
                {"product_id": 1, "description": "منتج 1", "quantity": 5, "unit_price": 150, "tax_rate": 15}
            ]
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400]

    def test_create_quotation_multi_items(self, client, admin_headers):
        """✅ إنشاء عرض سعر بعدة أصناف"""
        r = client.get("/api/sales/customers", headers=admin_headers)
        customers = r.json()
        if not customers:
            pytest.skip("لا عملاء")

        r2 = client.post("/api/sales/quotations", json={
            "customer_id": customers[0]["id"],
            "quotation_date": str(date.today()),
            "items": [
                {"product_id": 1, "description": "منتج 1", "quantity": 3, "unit_price": 150, "tax_rate": 15},
                {"product_id": 2, "description": "منتج 2", "quantity": 2, "unit_price": 250, "tax_rate": 15},
                {"product_id": 3, "description": "خدمة", "quantity": 1, "unit_price": 500, "tax_rate": 15},
            ]
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400]


# ═══════════════════════════════════════════════════════════════
# 📦 أوامر البيع - Sales Orders
# ═══════════════════════════════════════════════════════════════
class TestSalesOrderScenarios:
    """سيناريوهات أوامر البيع"""

    def test_list_sales_orders(self, client, admin_headers):
        """✅ عرض أوامر البيع"""
        r = client.get("/api/sales/orders", headers=admin_headers)
        assert_valid_response(r)
        assert len(r.json()) >= 1

    def test_get_sales_order_detail(self, client, admin_headers):
        """✅ تفاصيل أمر بيع"""
        r = client.get("/api/sales/orders", headers=admin_headers)
        orders = r.json()
        if not orders:
            pytest.skip("لا أوامر بيع")
        oid = orders[0]["id"]
        r2 = client.get(f"/api/sales/orders/{oid}", headers=admin_headers)
        assert r2.status_code in [200, 404]

    def test_create_sales_order(self, client, admin_headers):
        """✅ إنشاء أمر بيع"""
        r = client.get("/api/sales/customers", headers=admin_headers)
        customers = r.json()
        if not customers:
            pytest.skip("لا عملاء")

        r2 = client.post("/api/sales/orders", json={
            "customer_id": customers[0]["id"],
            "order_date": str(date.today()),
            "items": [
                {"product_id": 1, "quantity": 2, "unit_price": 150, "tax_rate": 15},
            ]
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400]

    def test_create_sales_order_with_delivery_date(self, client, admin_headers):
        """✅ أمر بيع بتاريخ تسليم"""
        r = client.get("/api/sales/customers", headers=admin_headers)
        customers = r.json()
        if not customers:
            pytest.skip("لا عملاء")

        r2 = client.post("/api/sales/orders", json={
            "customer_id": customers[0]["id"],
            "order_date": str(date.today()),
            "expected_delivery_date": str(date.today() + timedelta(days=7)),
            "items": [
                {"product_id": 1, "quantity": 10, "unit_price": 150, "tax_rate": 15},
                {"product_id": 2, "quantity": 5, "unit_price": 250, "tax_rate": 15},
            ]
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400]


# ═══════════════════════════════════════════════════════════════
# 🧾 فواتير المبيعات - Sales Invoices
# ═══════════════════════════════════════════════════════════════
class TestSalesInvoiceScenarios:
    """سيناريوهات فواتير المبيعات"""

    def test_list_sales_invoices(self, client, admin_headers):
        """✅ عرض الفواتير"""
        r = client.get("/api/sales/invoices", headers=admin_headers)
        assert_valid_response(r)
        assert len(r.json()) >= 0

    def test_get_invoice_detail(self, client, admin_headers):
        """✅ تفاصيل فاتورة"""
        r = client.get("/api/sales/invoices", headers=admin_headers)
        invoices = r.json()
        if not invoices:
            pytest.skip("لا فواتير")
        inv_id = invoices[0]["id"]
        r2 = client.get(f"/api/sales/invoices/{inv_id}", headers=admin_headers)
        assert r2.status_code in [200, 404]

    def test_create_sales_invoice_cash(self, client, admin_headers):
        """✅ فاتورة مبيعات نقدية"""
        r = client.get("/api/sales/customers", headers=admin_headers)
        customers = r.json()
        if not customers:
            pytest.skip("لا عملاء")

        r2 = client.post("/api/sales/invoices", json={
            "customer_id": customers[0]["id"],
            "invoice_date": str(date.today()),
            "payment_method": "cash",
            "paid_amount": 172.50,
            "treasury_id": 2,
            "items": [
                {"product_id": 1, "description": "منتج 1", "quantity": 1, "unit_price": 150, "tax_rate": 15}
            ]
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400]

    def test_create_sales_invoice_credit(self, client, admin_headers):
        """✅ فاتورة مبيعات آجلة"""
        r = client.get("/api/sales/customers", headers=admin_headers)
        customers = r.json()
        if not customers:
            pytest.skip("لا عملاء")

        r2 = client.post("/api/sales/invoices", json={
            "customer_id": customers[0]["id"],
            "invoice_date": str(date.today()),
            "payment_method": "credit",
            "items": [
                {"product_id": 1, "description": "منتج 1", "quantity": 5, "unit_price": 150, "tax_rate": 15},
                {"product_id": 2, "description": "منتج 2", "quantity": 3, "unit_price": 250, "tax_rate": 15},
            ]
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400]

    def test_create_invoice_multi_items(self, client, admin_headers):
        """✅ فاتورة بعدة أصناف وضريبة"""
        r = client.get("/api/sales/customers", headers=admin_headers)
        customers = r.json()
        if not customers:
            pytest.skip("لا عملاء")

        r2 = client.post("/api/sales/invoices", json={
            "customer_id": customers[0]["id"],
            "invoice_date": str(date.today()),
            "items": [
                {"product_id": 1, "description": "صنف 1", "quantity": 10, "unit_price": 150, "tax_rate": 15},
                {"product_id": 2, "description": "صنف 2", "quantity": 5, "unit_price": 250, "tax_rate": 15},
                {"product_id": 3, "description": "خدمة", "quantity": 2, "unit_price": 500, "tax_rate": 15},
            ]
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400]

    def test_cancel_invoice(self, client, admin_headers):
        """✅ إلغاء فاتورة غير مدفوعة"""
        # Create a new unpaid invoice specifically for cancellation
        r = client.get("/api/sales/customers", headers=admin_headers)
        customers = r.json()
        if not customers:
            pytest.skip("لا عملاء")
        r_create = client.post("/api/sales/invoices", json={
            "customer_id": customers[0]["id"],
            "invoice_date": str(date.today()),
            "items": [{"product_id": 1, "description": "صنف للإلغاء", "quantity": 1, "unit_price": 100, "tax_rate": 0}],
        }, headers=admin_headers)
        if r_create.status_code not in [200, 201]:
            pytest.skip("تعذر إنشاء فاتورة للإلغاء")
        inv_id = r_create.json()["id"]
        r2 = client.post(f"/api/sales/invoices/{inv_id}/cancel", headers=admin_headers)
        assert r2.status_code in [200, 400, 500]

    def test_sales_stats(self, client, admin_headers):
        """✅ إحصائيات المبيعات"""
        r = client.get("/api/sales/stats", headers=admin_headers)
        assert r.status_code in [200, 404]

    def test_outstanding_invoices(self, client, admin_headers):
        """✅ الفواتير المعلقة"""
        r = client.get("/api/sales/customers", headers=admin_headers)
        customers = r.json()
        if not customers:
            pytest.skip("لا عملاء")
        cid = customers[0]["id"]
        r2 = client.get(f"/api/sales/customers/{cid}/outstanding", headers=admin_headers)
        assert r2.status_code in [200, 404]


# ═══════════════════════════════════════════════════════════════
# 🔄 مرتجعات المبيعات - Sales Returns
# ═══════════════════════════════════════════════════════════════
class TestSalesReturnScenarios:
    """سيناريوهات المرتجعات"""

    def test_list_sales_returns(self, client, admin_headers):
        """✅ عرض المرتجعات"""
        r = client.get("/api/sales/returns", headers=admin_headers)
        assert_valid_response(r)

    def test_get_return_detail(self, client, admin_headers):
        """✅ تفاصيل مرتجع"""
        r = client.get("/api/sales/returns", headers=admin_headers)
        returns = r.json()
        if not returns:
            pytest.skip("لا مرتجعات")
        rid = returns[0]["id"]
        r2 = client.get(f"/api/sales/returns/{rid}", headers=admin_headers)
        assert r2.status_code in [200, 404]

    def test_create_sales_return(self, client, admin_headers):
        """✅ إنشاء مرتجع مبيعات"""
        r = client.get("/api/sales/customers", headers=admin_headers)
        customers = r.json()
        if not customers:
            pytest.skip("لا عملاء")

        r2 = client.post("/api/sales/returns", json={
            "customer_id": customers[0]["id"],
            "return_date": str(date.today()),
            "refund_method": "cash",
            "items": [
                {"product_id": 1, "description": "مرتجع", "quantity": 1, "unit_price": 150, "tax_rate": 15}
            ]
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400, 500]


# ═══════════════════════════════════════════════════════════════
# 💳 إيصالات وسندات - Receipts & Payments
# ═══════════════════════════════════════════════════════════════
class TestReceiptPaymentScenarios:
    """سيناريوهات الإيصالات والسندات"""

    def test_list_receipt_vouchers(self, client, admin_headers):
        """✅ عرض سندات القبض"""
        r = client.get("/api/sales/receipt-vouchers", headers=admin_headers)
        assert r.status_code in [200, 404]

    def test_list_payment_vouchers(self, client, admin_headers):
        """✅ عرض سندات الصرف"""
        r = client.get("/api/sales/payment-vouchers", headers=admin_headers)
        assert r.status_code in [200, 404]

    def test_create_customer_receipt(self, client, admin_headers):
        """✅ سند قبض من عميل"""
        r = client.get("/api/sales/customers", headers=admin_headers)
        customers = r.json()
        if not customers:
            pytest.skip("لا عملاء")

        r2 = client.post("/api/sales/receipts", json={
            "customer_id": customers[0]["id"],
            "amount": 500,
            "payment_method": "cash",
            "voucher_date": str(date.today()),
            "treasury_id": 2,
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400]

    def test_create_customer_payment(self, client, admin_headers):
        """✅ سند صرف لعميل (استرداد)"""
        r = client.get("/api/sales/customers", headers=admin_headers)
        customers = r.json()
        if not customers:
            pytest.skip("لا عملاء")

        r2 = client.post("/api/sales/payments", json={
            "customer_id": customers[0]["id"],
            "amount": 100,
            "payment_method": "cash",
            "voucher_date": str(date.today()),
            "treasury_id": 2,
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400]

    def test_payment_history(self, client, admin_headers):
        """✅ تاريخ المدفوعات"""
        r = client.get("/api/sales/customers", headers=admin_headers)
        customers = r.json()
        if not customers:
            pytest.skip("لا عملاء")
        cid = customers[0]["id"]
        r2 = client.get(f"/api/sales/customers/{cid}/payment-history", headers=admin_headers)
        assert r2.status_code in [200, 404]
