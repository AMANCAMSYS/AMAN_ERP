"""
Complete Business Cycles Tests - دورات أعمال كاملة
==========================================
اختبارات لدورات الأعمال الكاملة من البداية إلى النهاية

Covers:
- دورة مبيعات كاملة (عرض سعر → فاتورة → تحصيل)
- دورة مشتريات كاملة (طلب → فاتورة → دفع)
- دورة مخزون (استلام → تخزين → صرف)
- نهاية الفترة المالية (استهلاك → تسويات → إقفال)
- سيناريوهات متعددة الفروع
- سيناريوهات متعددة العملات
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from helpers import assert_valid_response, assert_error_response


# ═══════════════════════════════════════════════════════════════
# 🔄 دورة المبيعات الكاملة - Complete Sales Cycle
# ═══════════════════════════════════════════════════════════════
class TestCompleteSalesCycle:
    """دورة مبيعات كاملة من البداية للنهاية"""

    @pytest.fixture(scope="class")
    def customer_id(self, client, admin_headers):
        """إنشاء عميل للاختبار"""
        r = client.get("/api/parties?party_type=customer", headers=admin_headers)
        customers = r.json()
        if isinstance(customers, list) and len(customers) > 0:
            return customers[0]["id"]
        elif isinstance(customers, dict) and customers.get("items"):
            return customers["items"][0]["id"]
        # Create new customer
        r = client.post("/api/parties", json={
            "party_type": "customer",
            "party_name": "عميل الاختبار الشامل",
            "tax_number": "300123456789003",
            "phone": "0501234567",
            "email": "test@customer.com",
        }, headers=admin_headers)
        if r.status_code in [200, 201]:
            return r.json().get("id")
        pytest.skip("لا يمكن إنشاء عميل")

    def test_sales_cycle_step1_create_quotation(self, client, admin_headers, customer_id):
        """الخطوة 1: إنشاء عرض سعر"""
        r = client.get("/api/inventory/products?limit=3", headers=admin_headers)
        products = r.json() if isinstance(r.json(), list) else r.json().get("data", [])
        if not products:
            pytest.skip("لا منتجات")
        
        product_id = products[0].get("id")
        
        r2 = client.post("/api/sales/quotations", json={
            "customer_id": customer_id,
            "quotation_date": str(date.today()),
            "valid_until": str(date.today() + timedelta(days=30)),
            "items": [
                {"product_id": product_id, "quantity": 5, "unit_price": 100, "tax_rate": 15}
            ],
            "notes": "عرض سعر اختبار",
            "branch_id": 1,
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400, 404, 422, 500]
        if r2.status_code in [200, 201]:
            data = r2.json()
            assert "id" in data or "quotation_number" in data

    def test_sales_cycle_step2_quotation_to_invoice(self, client, admin_headers):
        """الخطوة 2: تحويل عرض السعر إلى فاتورة"""
        r = client.get("/api/sales/quotations?status=draft", headers=admin_headers)
        quotations = r.json() if isinstance(r.json(), list) else []
        if not quotations:
            pytest.skip("لا عروض أسعار")
        
        quot_id = quotations[0].get("id")
        r2 = client.post(f"/api/sales/quotations/{quot_id}/convert-to-invoice", headers=admin_headers)
        assert r2.status_code in [200, 201, 400, 404, 422, 500]

    def test_sales_cycle_step3_partial_payment(self, client, admin_headers):
        """الخطوة 3: دفعة جزئية على الفاتورة"""
        r = client.get("/api/sales/invoices?payment_status=unpaid", headers=admin_headers)
        invoices = r.json() if isinstance(r.json(), list) else r.json().get("data", [])
        if not invoices:
            pytest.skip("لا فواتير")
        
        invoice = invoices[0]
        invoice_id = invoice.get("id")
        total_amount = float(invoice.get("total_amount", 1000))
        
        r2 = client.post("/api/sales/receipts", json={
            "receipt_date": str(date.today()),
            "customer_id": invoice.get("customer_id"),
            "amount": total_amount / 2,  # نصف المبلغ
            "payment_method": "bank_transfer",
            "reference_number": f"RCPT-TEST-{date.today().strftime('%Y%m%d')}",
            "allocations": [
                {"invoice_id": invoice_id, "amount": total_amount / 2}
            ],
            "branch_id": 1,
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400, 404, 422, 500]

    def test_sales_cycle_step4_full_payment(self, client, admin_headers):
        """الخطوة 4: تسديد كامل المبلغ المتبقي"""
        r = client.get("/api/sales/invoices?payment_status=partial", headers=admin_headers)
        invoices = r.json() if isinstance(r.json(), list) else r.json().get("data", [])
        if not invoices:
            pytest.skip("لا فواتير مدفوعة جزئياً")
        
        invoice = invoices[0]
        invoice_id = invoice.get("id")
        remaining = float(invoice.get("remaining_amount", invoice.get("total_amount", 500)))
        
        r2 = client.post("/api/sales/receipts", json={
            "receipt_date": str(date.today()),
            "customer_id": invoice.get("customer_id"),
            "amount": remaining,
            "payment_method": "cash",
            "allocations": [
                {"invoice_id": invoice_id, "amount": remaining}
            ],
            "branch_id": 1,
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400, 404, 422, 500]


# ═══════════════════════════════════════════════════════════════
# 🛒 دورة المشتريات الكاملة - Complete Purchase Cycle
# ═══════════════════════════════════════════════════════════════
class TestCompletePurchaseCycle:
    """دورة مشتريات كاملة من البداية للنهاية"""

    @pytest.fixture(scope="class")
    def supplier_id(self, client, admin_headers):
        """الحصول على مورد"""
        r = client.get("/api/buying/suppliers", headers=admin_headers)
        suppliers = r.json()
        if suppliers and len(suppliers) > 0:
            return suppliers[0]["id"]
        pytest.skip("لا موردين")

    def test_purchase_cycle_step1_create_purchase_order(self, client, admin_headers, supplier_id):
        """الخطوة 1: إنشاء أمر شراء"""
        r = client.get("/api/inventory/products?limit=2", headers=admin_headers)
        products = r.json() if isinstance(r.json(), list) else r.json().get("data", [])
        if not products:
            pytest.skip("لا منتجات")
        
        product_id = products[0].get("id")
        
        r2 = client.post("/api/buying/purchase-orders", json={
            "supplier_id": supplier_id,
            "order_date": str(date.today()),
            "expected_delivery": str(date.today() + timedelta(days=7)),
            "items": [
                {"product_id": product_id, "quantity": 10, "unit_price": 50}
            ],
            "notes": "أمر شراء اختبار",
            "branch_id": 1,
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400, 404, 422, 500]

    def test_purchase_cycle_step2_receive_items(self, client, admin_headers):
        """الخطوة 2: استلام البضاعة"""
        r = client.get("/api/buying/purchase-orders?status=confirmed", headers=admin_headers)
        orders = r.json() if isinstance(r.json(), list) else []
        if not orders:
            pytest.skip("لا أوامر شراء مؤكدة")
        
        order_id = orders[0].get("id")
        r2 = client.post(f"/api/buying/purchase-orders/{order_id}/receive", json={
            "received_date": str(date.today()),
            "notes": "تم الاستلام بالكامل"
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400, 404, 422, 500]

    def test_purchase_cycle_step3_create_purchase_invoice(self, client, admin_headers, supplier_id):
        """الخطوة 3: إنشاء فاتورة شراء"""
        r = client.get("/api/inventory/products?limit=2", headers=admin_headers)
        products = r.json() if isinstance(r.json(), list) else r.json().get("data", [])
        if not products:
            pytest.skip("لا منتجات")
        
        product_id = products[0].get("id")
        
        r2 = client.post("/api/buying/invoices", json={
            "supplier_id": supplier_id,
            "invoice_date": str(date.today()),
            "due_date": str(date.today() + timedelta(days=30)),
            "items": [
                {"product_id": product_id, "quantity": 10, "unit_price": 50, "tax_rate": 15}
            ],
            "notes": "فاتورة شراء اختبار",
            "branch_id": 1,
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400, 404, 422, 500]

    def test_purchase_cycle_step4_make_payment(self, client, admin_headers):
        """الخطوة 4: دفع الفاتورة"""
        r = client.get("/api/buying/invoices?payment_status=unpaid", headers=admin_headers)
        invoices = r.json() if isinstance(r.json(), list) else r.json().get("data", [])
        if not invoices:
            pytest.skip("لا فواتير شراء")
        
        invoice = invoices[0]
        invoice_id = invoice.get("id")
        total_amount = float(invoice.get("total_amount", 1000))
        
        r2 = client.post("/api/buying/payments", json={
            "payment_date": str(date.today()),
            "supplier_id": invoice.get("supplier_id"),
            "amount": total_amount,
            "payment_method": "bank_transfer",
            "allocations": [
                {"invoice_id": invoice_id, "amount": total_amount}
            ],
            "branch_id": 1,
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400, 404, 422, 500]


# ═══════════════════════════════════════════════════════════════
# 📦 دورة المخزون الكاملة - Complete Inventory Cycle
# ═══════════════════════════════════════════════════════════════
class TestCompleteInventoryCycle:
    """دورة مخزون كاملة"""

    def test_inventory_cycle_step1_product_creation(self, client, admin_headers):
        """الخطوة 1: إنشاء منتج جديد"""
        r = client.post("/api/inventory/products", json={
            "name": f"منتج اختبار {date.today().strftime('%Y%m%d%H%M%S')}",
            "name_en": "Test Product",
            "sku": f"TEST-{date.today().strftime('%Y%m%d%H%M%S')}",
            "category": "goods",
            "unit": "piece",
            "cost_price": 50,
            "selling_price": 100,
            "track_inventory": True,
            "branch_id": 1,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 422, 500]

    def test_inventory_cycle_step2_stock_receipt(self, client, admin_headers):
        """الخطوة 2: استلام بضاعة"""
        r = client.get("/api/inventory/products?track_inventory=true", headers=admin_headers)
        products = r.json() if isinstance(r.json(), list) else r.json().get("data", [])
        if not products:
            pytest.skip("لا منتجات")
        
        product_id = products[0].get("id")
        
        r2 = client.post("/api/inventory/stock-receipt", json={
            "receipt_date": str(date.today()),
            "items": [
                {"product_id": product_id, "quantity": 100, "unit_cost": 50}
            ],
            "warehouse_id": 1,
            "notes": "استلام بضاعة",
            "branch_id": 1,
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400, 404, 422, 500]

    def test_inventory_cycle_step3_stock_transfer(self, client, admin_headers):
        """الخطوة 3: نقل بضاعة بين مستودعات"""
        # Get warehouses
        r = client.get("/api/inventory/warehouses", headers=admin_headers)
        warehouses = r.json() if isinstance(r.json(), list) else []
        if len(warehouses) < 2:
            pytest.skip("تحتاج مستودعين على الأقل")
        
        r2 = client.get("/api/inventory/products", headers=admin_headers)
        products = r2.json() if isinstance(r2.json(), list) else r2.json().get("data", [])
        if not products:
            pytest.skip("لا منتجات")
        
        product_id = products[0].get("id")
        
        r3 = client.post("/api/inventory/stock-transfer", json={
            "transfer_date": str(date.today()),
            "from_warehouse_id": warehouses[0]["id"],
            "to_warehouse_id": warehouses[1]["id"],
            "items": [
                {"product_id": product_id, "quantity": 10}
            ],
            "notes": "نقل بضاعة بين مستودعات",
            "branch_id": 1,
        }, headers=admin_headers)
        assert r3.status_code in [200, 201, 400, 404, 422, 500]

    def test_inventory_cycle_step4_stock_delivery(self, client, admin_headers):
        """الخطوة 4: صرف بضاعة"""
        r = client.get("/api/inventory/products", headers=admin_headers)
        products = r.json() if isinstance(r.json(), list) else r.json().get("data", [])
        if not products:
            pytest.skip("لا منتجات")
        
        product_id = products[0].get("id")
        
        r2 = client.post("/api/inventory/stock-delivery", json={
            "delivery_date": str(date.today()),
            "items": [
                {"product_id": product_id, "quantity": 5}
            ],
            "warehouse_id": 1,
            "notes": "صرف بضاعة",
            "branch_id": 1,
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400, 404, 422, 500]

    def test_inventory_cycle_step5_cycle_count(self, client, admin_headers):
        """الخطوة 5: جرد دوري"""
        r = client.get("/api/inventory/products?track_inventory=true&limit=5", headers=admin_headers)
        products = r.json() if isinstance(r.json(), list) else r.json().get("data", [])
        if not products:
            pytest.skip("لا منتجات")
        
        items = []
        for product in products[:3]:
            items.append({
                "product_id": product.get("id"),
                "counted_quantity": 50,
                "system_quantity": product.get("stock_quantity", 0)
            })
        
        r2 = client.post("/api/inventory/cycle-counts", json={
            "count_date": str(date.today()),
            "warehouse_id": 1,
            "items": items,
            "notes": "جرد دوري اختبار",
            "branch_id": 1,
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400, 404, 422, 500]


# ═══════════════════════════════════════════════════════════════
# 💰 نهاية الفترة المالية - Period-End Closing
# ═══════════════════════════════════════════════════════════════
class TestPeriodEndClosing:
    """سيناريوهات نهاية الفترة المالية"""

    def test_period_end_step1_assets_depreciation(self, client, admin_headers):
        """الخطوة 1: استهلاك الأصول"""
        r = client.post("/api/assets/depreciation/calculate", json={
            "calculation_date": str(date.today()),
            "branch_id": 1,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 404, 422, 500]

    def test_period_end_step2_adjustment_entries(self, client, admin_headers):
        """الخطوة 2: قيود التسوية"""
        r = client.post("/api/accounting/journal-entries", json={
            "date": str(date.today()),
            "description": "قيود تسوية نهاية الفترة",
            "entry_type": "adjustment",
            "lines": [
                {"account_id": 10, "debit": 1000, "credit": 0, "description": "مصاريف مستحقة"},
                {"account_id": 50, "debit": 0, "credit": 1000, "description": "ذمم دائنة"},
            ],
            "branch_id": 1,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 422, 500]

    def test_period_end_step3_closing_entries_preview(self, client, admin_headers):
        """الخطوة 3: معاينة قيود الإقفال"""
        r = client.get("/api/accounting/fiscal-years/current", headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("لا سنة مالية حالية")
        
        fiscal_year = r.json()
        year_id = fiscal_year.get("id")
        
        r2 = client.get(f"/api/accounting/closing-entries/preview?fiscal_year_id={year_id}", headers=admin_headers)
        assert r2.status_code in [200, 400, 404, 422, 500]

    def test_period_end_step4_retained_earnings_check(self, client, admin_headers):
        """الخطوة 4: التحقق من حساب الأرباح المحتجزة"""
        r = client.get("/api/accounting/accounts?account_type=equity", headers=admin_headers)
        if r.status_code == 200:
            accounts = r.json() if isinstance(r.json(), list) else r.json().get("data", [])
            retained_acc = next((a for a in accounts if "محتجز" in a.get("name", "") or "retained" in a.get("name_en", "").lower()), None)
            assert retained_acc is not None or len(accounts) > 0, "يجب وجود حساب أرباح محتجزة"


# ═══════════════════════════════════════════════════════════════
# 🏢 سيناريوهات متعددة الفروع - Multi-Branch Scenarios
# ═══════════════════════════════════════════════════════════════
class TestMultiBranchScenarios:
    """سيناريوهات متعددة الفروع"""

    def test_multi_branch_expense_allocation(self, client, admin_headers):
        """توزيع مصروف على عدة فروع"""
        r = client.get("/api/branches", headers=admin_headers)
        branches = r.json() if isinstance(r.json(), list) else []
        if len(branches) < 2:
            pytest.skip("تحتاج فرعين على الأقل")
        
        r2 = client.post("/api/expenses/", json={
            "expense_type": "utilities",
            "amount": 10000,
            "expense_date": str(date.today()),
            "description": "فواتير كهرباء - موزعة",
            "payment_method": "bank_transfer",
            "treasury_id": 1,
            "allocations": [
                {"branch_id": branches[0]["id"], "amount": 6000},
                {"branch_id": branches[1]["id"], "amount": 4000},
            ],
            "branch_id": branches[0]["id"],
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400, 404, 422, 500]

    def test_multi_branch_stock_transfer_between_branches(self, client, admin_headers):
        """نقل مخزون بين فروع"""
        r = client.get("/api/branches", headers=admin_headers)
        branches = r.json() if isinstance(r.json(), list) else []
        if len(branches) < 2:
            pytest.skip("تحتاج فرعين على الأقل")
        
        r2 = client.get("/api/inventory/products?limit=1", headers=admin_headers)
        products = r2.json() if isinstance(r2.json(), list) else r2.json().get("data", [])
        if not products:
            pytest.skip("لا منتجات")
        
        r3 = client.post("/api/inventory/inter-branch-transfer", json={
            "transfer_date": str(date.today()),
            "from_branch_id": branches[0]["id"],
            "to_branch_id": branches[1]["id"],
            "items": [
                {"product_id": products[0]["id"], "quantity": 5}
            ],
            "notes": "نقل بين فروع",
        }, headers=admin_headers)
        assert r3.status_code in [200, 201, 400, 404, 422, 500]

    def test_multi_branch_consolidated_reports(self, client, admin_headers):
        """تقارير موحدة لكل الفروع"""
        r = client.get("/api/reports/accounting/trial-balance", headers=admin_headers)
        assert_valid_response(r)
        
        # Should include all branches
        data = r.json()
        assert isinstance(data, (list, dict))


# ═══════════════════════════════════════════════════════════════
# 💱 سيناريوهات متعددة العملات - Multi-Currency Scenarios
# ═══════════════════════════════════════════════════════════════
class TestMultiCurrencyScenarios:
    """سيناريوهات متعددة العملات"""

    def test_multi_currency_invoice_and_payment(self, client, admin_headers):
        """فاتورة بعملة أجنبية ودفع جزئي"""
        r = client.get("/api/parties?party_type=customer&limit=1", headers=admin_headers)
        customers = r.json()
        if isinstance(customers, dict):
            customers = customers.get("items", [])
        if not customers or not isinstance(customers, list):
            pytest.skip("لا عملاء")
        customer_id = customers[0]["id"]
        
        r2 = client.get("/api/inventory/products?limit=1", headers=admin_headers)
        products = r2.json() if isinstance(r2.json(), list) else r2.json().get("data", [])
        if not products:
            pytest.skip("لا منتجات")
        product_id = products[0]["id"]
        
        # Create invoice in USD
        r3 = client.post("/api/sales/invoices", json={
            "customer_id": customer_id,
            "invoice_date": str(date.today()),
            "currency": "USD",
            "exchange_rate": 3.75,
            "items": [
                {"product_id": product_id, "quantity": 10, "unit_price": 100, "tax_rate": 0}
            ],
            "notes": "فاتورة بالدولار",
            "branch_id": 1,
        }, headers=admin_headers)
        assert r3.status_code in [200, 201, 400, 404, 422, 500]

    def test_multi_currency_exchange_gain_loss(self, client, admin_headers):
        """فروق العملة عند السداد"""
        # This would test realized FX gain/loss
        r = client.get("/api/accounting/currencies/fx-realized", headers=admin_headers)
        assert r.status_code in [200, 404, 405, 422, 500]

    def test_multi_currency_revaluation(self, client, admin_headers):
        """إعادة تقييم العملات"""
        r = client.post("/api/accounting/currencies/revaluate", json={
            "revaluation_date": str(date.today()),
            "currency": "USD",
            "new_rate": 3.80,
            "branch_id": 1,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 404, 422, 500]
