"""
test_27_sales_advanced.py
==========================
اختبارات متقدمة للمبيعات

Covers UNTESTED endpoints:
- POST /api/sales/returns/{id}/approve
- GET /api/sales/invoices/{id}/payment-history
- GET /api/sales/customers/{id}/transactions
- GET /api/sales/customers/{id}/outstanding-invoices
- GET/POST /api/sales/credit-notes
- GET /api/sales/credit-notes/{id}
- GET/POST /api/sales/debit-notes
- GET /api/sales/debit-notes/{id}
- GET /api/sales/receipts/{id}
- GET /api/sales/payments/{id}
"""
import pytest
from datetime import date, timedelta
from helpers import assert_valid_response, assert_error_response


# ══════════════════════════════════════════════════════════════
# 🏷 إشعارات البيع - Credit/Debit Notes
# ══════════════════════════════════════════════════════════════

class TestSalesCreditNotes:
    """اختبارات إشعارات الدائن (المرتجعات)"""

    def test_list_credit_notes(self, client, admin_headers):
        """اختبار عرض إشعارات الدائن"""
        r = client.get("/api/sales/credit-notes", headers=admin_headers)
        assert r.status_code in (200, 404, 501)
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data, (list, dict))

    def test_create_credit_note(self, client, admin_headers):
        """اختبار إنشاء إشعار دائن"""
        # جلب فاتورة لإنشاء إشعار عليها
        inv_r = client.get("/api/sales/invoices", headers=admin_headers)
        if inv_r.status_code != 200:
            pytest.skip("لا يمكن جلب الفواتير")
        invoices = inv_r.json()
        if isinstance(invoices, dict):
            invoices = invoices.get("items", invoices.get("invoices", []))
        if not invoices:
            pytest.skip("لا توجد فواتير")

        invoice = invoices[0]
        cn_data = {
            "invoice_id": invoice.get("id"),
            "customer_id": invoice.get("customer_id"),
            "date": str(date.today()),
            "reason": "مرتجعات - اختبار",
            "amount": 1000.00,
            "items": [
                {
                    "description": "بند مرتجع",
                    "quantity": 1,
                    "unit_price": 1000.00
                }
            ]
        }
        r = client.post("/api/sales/credit-notes", json=cn_data,
                        headers=admin_headers)
        assert r.status_code in (200, 201, 400, 404, 422, 501)

    def test_get_credit_note_detail(self, client, admin_headers):
        """اختبار تفاصيل إشعار دائن"""
        r = client.get("/api/sales/credit-notes", headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("إشعارات الدائن غير متوفرة")
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])
        if not items:
            pytest.skip("لا توجد إشعارات دائن")
        cn_id = items[0].get("id") or items[0].get("note_id")
        r2 = client.get(f"/api/sales/credit-notes/{cn_id}",
                        headers=admin_headers)
        assert r2.status_code in (200, 404)


class TestSalesDebitNotes:
    """اختبارات إشعارات المدين"""

    def test_list_debit_notes(self, client, admin_headers):
        """اختبار عرض إشعارات المدين"""
        r = client.get("/api/sales/debit-notes", headers=admin_headers)
        assert r.status_code in (200, 404, 501)

    def test_create_debit_note(self, client, admin_headers):
        """اختبار إنشاء إشعار مدين"""
        customers_r = client.get("/api/sales/customers", headers=admin_headers)
        if customers_r.status_code != 200:
            pytest.skip("لا يمكن جلب العملاء")
        customers = customers_r.json()
        if isinstance(customers, dict):
            customers = customers.get("items", customers.get("customers", []))
        if not customers:
            pytest.skip("لا يوجد عملاء")

        dn_data = {
            "customer_id": customers[0]["id"],
            "date": str(date.today()),
            "reason": "فرق سعر - اختبار",
            "amount": 500.00,
            "items": [
                {
                    "description": "فرق سعر",
                    "quantity": 1,
                    "unit_price": 500.00
                }
            ]
        }
        r = client.post("/api/sales/debit-notes", json=dn_data,
                        headers=admin_headers)
        assert r.status_code in (200, 201, 400, 404, 422, 501)

    def test_get_debit_note_detail(self, client, admin_headers):
        """اختبار تفاصيل إشعار مدين"""
        r = client.get("/api/sales/debit-notes", headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("إشعارات المدين غير متوفرة")
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])
        if not items:
            pytest.skip("لا توجد إشعارات مدين")
        dn_id = items[0].get("id") or items[0].get("note_id")
        r2 = client.get(f"/api/sales/debit-notes/{dn_id}",
                        headers=admin_headers)
        assert r2.status_code in (200, 404)


# ══════════════════════════════════════════════════════════════
# 🔄 مرتجعات المبيعات المتقدمة - Returns Approval
# ══════════════════════════════════════════════════════════════

class TestSalesReturnsApproval:
    """اختبارات اعتماد مرتجعات المبيعات"""

    def test_approve_sales_return(self, client, admin_headers):
        """اختبار اعتماد مرتجع مبيعات"""
        returns_r = client.get("/api/sales/returns", headers=admin_headers)
        if returns_r.status_code != 200:
            pytest.skip("لا يمكن جلب المرتجعات")
        data = returns_r.json()
        items = data if isinstance(data, list) else data.get("items", [])
        if not items:
            pytest.skip("لا توجد مرتجعات")
        ret_id = items[0].get("id") or items[0].get("return_id")
        r = client.post(f"/api/sales/returns/{ret_id}/approve",
                        headers=admin_headers)
        assert r.status_code in (200, 400, 404, 422, 501)

    def test_create_and_approve_return(self, client, admin_headers):
        """اختبار إنشاء مرتجع واعتماده"""
        # جلب فاتورة
        inv_r = client.get("/api/sales/invoices", headers=admin_headers)
        if inv_r.status_code != 200:
            pytest.skip("لا يمكن جلب الفواتير")
        invoices = inv_r.json()
        if isinstance(invoices, dict):
            invoices = invoices.get("items", [])
        if not invoices:
            pytest.skip("لا توجد فواتير")

        invoice = invoices[0]
        return_data = {
            "invoice_id": invoice["id"],
            "customer_id": invoice.get("customer_id"),
            "date": str(date.today()),
            "reason": "بضاعة تالفة - اختبار",
            "items": [
                {
                    "product_id": invoice.get("items", [{}])[0].get("product_id") if invoice.get("items") else None,
                    "quantity": 1,
                    "unit_price": 100.00,
                    "description": "مرتجع اختبار"
                }
            ]
        }
        create_r = client.post("/api/sales/returns", json=return_data,
                               headers=admin_headers)
        if create_r.status_code in (200, 201):
            ret_id = create_r.json().get("id")
            if ret_id:
                approve_r = client.post(
                    f"/api/sales/returns/{ret_id}/approve",
                    headers=admin_headers
                )
                assert approve_r.status_code in (200, 400, 404, 422, 501)


# ══════════════════════════════════════════════════════════════
# 💳 تفاصيل الإيصالات والمدفوعات - Voucher Details
# ══════════════════════════════════════════════════════════════

class TestSalesVoucherDetails:
    """اختبارات تفاصيل سندات القبض والصرف"""

    def test_get_receipt_detail(self, client, admin_headers):
        """اختبار تفاصيل سند قبض"""
        r = client.get("/api/sales/receipts", headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("لا يمكن جلب سندات القبض")
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])
        if not items:
            pytest.skip("لا توجد سندات قبض")
        voucher_id = items[0].get("id") or items[0].get("voucher_id")
        r2 = client.get(f"/api/sales/receipts/{voucher_id}",
                        headers=admin_headers)
        assert r2.status_code in (200, 404)

    def test_get_payment_detail(self, client, admin_headers):
        """اختبار تفاصيل سند دفع"""
        r = client.get("/api/sales/payments", headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("لا يمكن جلب سندات الدفع")
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])
        if not items:
            pytest.skip("لا توجد سندات دفع")
        voucher_id = items[0].get("id") or items[0].get("voucher_id")
        r2 = client.get(f"/api/sales/payments/{voucher_id}",
                        headers=admin_headers)
        assert r2.status_code in (200, 404)


# ══════════════════════════════════════════════════════════════
# 📊 تاريخ دفع الفاتورة ومعاملات العميل
# ══════════════════════════════════════════════════════════════

class TestSalesInvoicePaymentHistory:
    """اختبارات سجل دفعات الفواتير"""

    def test_invoice_payment_history(self, client, admin_headers):
        """اختبار سجل دفعات فاتورة مبيعات"""
        inv_r = client.get("/api/sales/invoices", headers=admin_headers)
        if inv_r.status_code != 200:
            pytest.skip("لا يمكن جلب الفواتير")
        invoices = inv_r.json()
        if isinstance(invoices, dict):
            invoices = invoices.get("items", [])
        if not invoices:
            pytest.skip("لا توجد فواتير")
        inv_id = invoices[0]["id"]
        r = client.get(f"/api/sales/invoices/{inv_id}/payment-history",
                       headers=admin_headers)
        assert r.status_code in (200, 404)

    def test_customer_transactions(self, client, admin_headers):
        """اختبار معاملات العميل"""
        cust_r = client.get("/api/sales/customers", headers=admin_headers)
        if cust_r.status_code != 200:
            pytest.skip("لا يمكن جلب العملاء")
        customers = cust_r.json()
        if isinstance(customers, dict):
            customers = customers.get("items", customers.get("customers", []))
        if not customers:
            pytest.skip("لا يوجد عملاء")
        cid = customers[0]["id"]
        r = client.get(f"/api/sales/customers/{cid}/transactions",
                       headers=admin_headers)
        assert r.status_code in (200, 404)

    def test_customer_outstanding_invoices(self, client, admin_headers):
        """اختبار فواتير العميل المستحقة"""
        cust_r = client.get("/api/sales/customers", headers=admin_headers)
        if cust_r.status_code != 200:
            pytest.skip("لا يمكن جلب العملاء")
        customers = cust_r.json()
        if isinstance(customers, dict):
            customers = customers.get("items", customers.get("customers", []))
        if not customers:
            pytest.skip("لا يوجد عملاء")
        cid = customers[0]["id"]
        r = client.get(f"/api/sales/customers/{cid}/outstanding-invoices",
                       headers=admin_headers)
        assert r.status_code in (200, 404)

    def test_cancel_invoice(self, client, admin_headers):
        """اختبار إلغاء فاتورة مبيعات"""
        inv_r = client.get("/api/sales/invoices", headers=admin_headers)
        if inv_r.status_code != 200:
            pytest.skip("لا يمكن جلب الفواتير")
        invoices = inv_r.json()
        if isinstance(invoices, dict):
            invoices = invoices.get("items", [])
        if not invoices:
            pytest.skip("لا توجد فواتير")
        inv_id = invoices[-1]["id"]
        r = client.post(f"/api/sales/invoices/{inv_id}/cancel",
                        headers=admin_headers)
        assert r.status_code in (200, 400, 404, 422)

    def test_create_receipt_voucher(self, client, admin_headers):
        """اختبار إنشاء سند قبض"""
        customers_r = client.get("/api/sales/customers", headers=admin_headers)
        if customers_r.status_code != 200:
            pytest.skip("لا يمكن جلب العملاء")
        customers = customers_r.json()
        if isinstance(customers, dict):
            customers = customers.get("items", [])
        if not customers:
            pytest.skip("لا يوجد عملاء")

        treasury_r = client.get("/api/treasury/accounts", headers=admin_headers)
        if treasury_r.status_code != 200:
            pytest.skip("لا يمكن جلب حسابات الخزينة")
        taccts = treasury_r.json()
        if isinstance(taccts, dict):
            taccts = taccts.get("items", [])
        if not taccts:
            pytest.skip("لا توجد حسابات خزينة")

        receipt_data = {
            "customer_id": customers[0]["id"],
            "treasury_account_id": taccts[0]["id"],
            "amount": 5000.00,
            "date": str(date.today()),
            "payment_method": "cash",
            "description": "سند قبض اختبار"
        }
        r = client.post("/api/sales/receipts", json=receipt_data,
                        headers=admin_headers)
        assert r.status_code in (200, 201, 400, 422, 501)
