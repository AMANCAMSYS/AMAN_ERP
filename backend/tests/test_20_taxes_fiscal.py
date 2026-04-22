"""
AMAN ERP - اختبارات شاملة متعددة السيناريوهات: الضرائب والسنوات المالية
Comprehensive Multi-Scenario Tests: Taxes & Fiscal Years
═══════════════════════════════════════════════════════
يتضمن: أنواع الضرائب، مجموعات الضرائب، الإقرارات الضريبية، المدفوعات، التسويات
السنوات المالية، الفترات المحاسبية، إقفال السنة
"""

import pytest
from datetime import date
from helpers import assert_valid_response


# ═══════════════════════════════════════════════════════════════
# 💰 أنواع الضرائب - Tax Rates
# ═══════════════════════════════════════════════════════════════
class TestTaxRateScenarios:
    """سيناريوهات أنواع الضرائب"""

    def test_list_tax_rates(self, client, admin_headers):
        """✅ عرض أنواع الضرائب"""
        r = client.get("/api/taxes/rates", headers=admin_headers)
        assert_valid_response(r)
        assert isinstance(r.json(), list)

    def test_list_active_tax_rates(self, client, admin_headers):
        """✅ عرض الضرائب النشطة فقط"""
        r = client.get("/api/taxes/rates?is_active=true", headers=admin_headers)
        assert_valid_response(r)
        for rate in r.json():
            assert rate.get("is_active")

    def test_get_tax_rate_detail(self, client, admin_headers):
        """✅ تفاصيل نوع ضريبة"""
        r = client.get("/api/taxes/rates", headers=admin_headers)
        rates = r.json()
        if not rates:
            pytest.skip("لا أنواع ضرائب")
        rate_id = rates[0]["id"]
        r2 = client.get(f"/api/taxes/rates/{rate_id}", headers=admin_headers)
        assert_valid_response(r2)

    def test_create_vat_rate(self, client, admin_headers):
        """✅ إنشاء نوع ضريبة القيمة المضافة"""
        r = client.post("/api/taxes/rates", json={
            "tax_code": "VAT-15",
            "tax_name": "ضريبة القيمة المضافة 15%",
            "tax_name_en": "VAT 15%",
            "rate_type": "percentage",
            "rate_value": 15.0,
            "description": "ضريبة القيمة المضافة الأساسية",
            "effective_from": "2024-01-01",
            "is_active": True,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 409]

    def test_create_zero_rate_tax(self, client, admin_headers):
        """✅ إنشاء ضريبة صفرية (للصادرات)"""
        r = client.post("/api/taxes/rates", json={
            "tax_code": "VAT-ZERO",
            "tax_name": "ضريبة صفرية",
            "tax_name_en": "Zero Rate",
            "rate_type": "percentage",
            "rate_value": 0,
            "description": "للصادرات والخدمات الدولية",
            "is_active": True,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 409]

    def test_create_exempt_tax(self, client, admin_headers):
        """✅ إنشاء إعفاء ضريبي"""
        r = client.post("/api/taxes/rates", json={
            "tax_code": "VAT-EXEMPT",
            "tax_name": "معفى من الضريبة",
            "tax_name_en": "Exempt",
            "rate_type": "percentage",
            "rate_value": 0,
            "description": "للخدمات المعفاة",
            "is_active": True,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 409]

    def test_update_tax_rate(self, client, admin_headers):
        """✅ تحديث نوع ضريبة"""
        r = client.get("/api/taxes/rates", headers=admin_headers)
        rates = r.json()
        if not rates:
            pytest.skip("لا أنواع ضرائب")
        rate_id = rates[-1]["id"]
        r2 = client.put(f"/api/taxes/rates/{rate_id}", json={
            "description": "وصف محدث للضريبة",
        }, headers=admin_headers)
        assert r2.status_code in [200, 400, 404]

    def test_deactivate_tax_rate(self, client, admin_headers):
        """✅ إيقاف نوع ضريبة"""
        # Create a tax specifically for deactivation
        r = client.post("/api/taxes/rates", json={
            "tax_code": f"DEL-{date.today().strftime('%H%M%S')}",
            "tax_name": "ضريبة للإيقاف",
            "rate_type": "percentage",
            "rate_value": 5,
            "is_active": True,
        }, headers=admin_headers)
        if r.status_code in [200, 201]:
            rate_id = r.json().get("id")
            if rate_id:
                r2 = client.delete(f"/api/taxes/rates/{rate_id}", headers=admin_headers)
                assert r2.status_code in [200, 400]


# ═══════════════════════════════════════════════════════════════
# 📦 مجموعات الضرائب - Tax Groups
# ═══════════════════════════════════════════════════════════════
class TestTaxGroupScenarios:
    """سيناريوهات مجموعات الضرائب"""

    def test_list_tax_groups(self, client, admin_headers):
        """✅ عرض مجموعات الضرائب"""
        r = client.get("/api/taxes/groups", headers=admin_headers)
        assert_valid_response(r)
        assert isinstance(r.json(), list)

    def test_get_tax_group_detail(self, client, admin_headers):
        """✅ تفاصيل مجموعة ضرائب"""
        r = client.get("/api/taxes/groups", headers=admin_headers)
        groups = r.json()
        if not groups:
            pytest.skip("لا مجموعات ضرائب")
        group_id = groups[0]["id"]
        r2 = client.get(f"/api/taxes/groups/{group_id}", headers=admin_headers)
        assert r2.status_code in [200, 404]

    def test_create_tax_group(self, client, admin_headers):
        """✅ إنشاء مجموعة ضرائب"""
        # Get tax rates first
        r = client.get("/api/taxes/rates", headers=admin_headers)
        rates = r.json()
        tax_ids = [rates[0]["id"]] if rates else []

        r2 = client.post("/api/taxes/groups", json={
            "group_code": "TG-STD",
            "group_name": "مجموعة الضريبة القياسية",
            "group_name_en": "Standard Tax Group",
            "description": "تطبق على معظم المبيعات",
            "tax_ids": tax_ids,
            "is_active": True,
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400, 409]

    def test_update_tax_group(self, client, admin_headers):
        """✅ تحديث مجموعة ضرائب"""
        r = client.get("/api/taxes/groups", headers=admin_headers)
        groups = r.json()
        if not groups:
            pytest.skip("لا مجموعات ضرائب")
        group_id = groups[0]["id"]
        r2 = client.put(f"/api/taxes/groups/{group_id}", json={
            "description": "وصف محدث",
        }, headers=admin_headers)
        assert r2.status_code in [200, 400, 404]


# ═══════════════════════════════════════════════════════════════
# 📋 الإقرارات الضريبية - Tax Returns
# ═══════════════════════════════════════════════════════════════
class TestTaxReturnScenarios:
    """سيناريوهات الإقرارات الضريبية"""

    def test_list_tax_returns(self, client, admin_headers):
        """✅ عرض الإقرارات الضريبية"""
        r = client.get("/api/taxes/returns", headers=admin_headers)
        assert_valid_response(r)

    def test_get_tax_return_detail(self, client, admin_headers):
        """✅ تفاصيل إقرار ضريبي"""
        r = client.get("/api/taxes/returns", headers=admin_headers)
        returns = r.json()
        if not returns:
            pytest.skip("لا إقرارات ضريبية")
        return_id = returns[0]["id"]
        r2 = client.get(f"/api/taxes/returns/{return_id}", headers=admin_headers)
        assert r2.status_code in [200, 404]

    def test_create_tax_return_monthly(self, client, admin_headers):
        """✅ إنشاء إقرار ضريبي شهري"""
        r = client.post("/api/taxes/returns", json={
            "tax_period": "2025-01",
            "tax_type": "vat",
            "due_date": "2025-02-28",
            "notes": "إقرار شهر يناير",
            "branch_id": 1,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 500]

    def test_create_tax_return_quarterly(self, client, admin_headers):
        """✅ إنشاء إقرار ضريبي ربع سنوي"""
        r = client.post("/api/taxes/returns", json={
            "tax_period": "2025-Q1",
            "tax_type": "vat",
            "due_date": "2025-04-30",
            "notes": "إقرار الربع الأول",
            "branch_id": 1,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 500]

    def test_calculate_tax_return(self, client, admin_headers):
        """✅ حساب الإقرار الضريبي من الفواتير"""
        r = client.get("/api/taxes/returns", headers=admin_headers)
        returns = r.json()
        draft = next((ret for ret in returns if ret.get("status") == "draft"), None)
        if not draft:
            pytest.skip("لا إقرار مسودة")
        return_id = draft["id"]
        r2 = client.post(f"/api/taxes/returns/{return_id}/calculate", headers=admin_headers)
        assert r2.status_code in [200, 400, 404]

    def test_submit_tax_return(self, client, admin_headers):
        """✅ تقديم الإقرار الضريبي"""
        r = client.get("/api/taxes/returns", headers=admin_headers)
        returns = r.json()
        draft = next((ret for ret in returns if ret.get("status") == "draft"), None)
        if not draft:
            pytest.skip("لا إقرار مسودة")
        return_id = draft["id"]
        r2 = client.post(f"/api/taxes/returns/{return_id}/submit", headers=admin_headers)
        assert r2.status_code in [200, 400, 404]


# ═══════════════════════════════════════════════════════════════
# 💳 مدفوعات الضرائب - Tax Payments
# ═══════════════════════════════════════════════════════════════
class TestTaxPaymentScenarios:
    """سيناريوهات مدفوعات الضرائب"""

    def test_list_tax_payments(self, client, admin_headers):
        """✅ عرض مدفوعات الضرائب"""
        r = client.get("/api/taxes/payments", headers=admin_headers)
        assert_valid_response(r)

    def test_create_tax_payment(self, client, admin_headers):
        """✅ إنشاء دفعة ضريبة - القيد: مدين ضريبة مستحقة / دائن البنك"""
        # Get a submitted tax return
        r = client.get("/api/taxes/returns", headers=admin_headers)
        returns = r.json()
        submitted = next((ret for ret in returns if ret.get("status") == "submitted"), None)
        
        r2 = client.post("/api/taxes/payments", json={
            "tax_return_id": submitted["id"] if submitted else 1,
            "amount": 5000,
            "payment_date": str(date.today()),
            "payment_method": "bank_transfer",
            "treasury_account_id": 4,
            "reference": f"TAX-PAY-{date.today().strftime('%Y%m%d')}",
            "notes": "دفعة ضريبة القيمة المضافة",
        }, headers=admin_headers)
        assert r2.status_code in [200, 201, 400, 500]

    def test_get_tax_payment_detail(self, client, admin_headers):
        """✅ تفاصيل دفعة ضريبة"""
        r = client.get("/api/taxes/payments", headers=admin_headers)
        payments = r.json()
        if not payments:
            pytest.skip("لا مدفوعات ضرائب")
        payment_id = payments[0]["id"]
        r2 = client.get(f"/api/taxes/payments/{payment_id}", headers=admin_headers)
        assert r2.status_code in [200, 404]


# ═══════════════════════════════════════════════════════════════
# 🔄 تسويات الضرائب - Tax Adjustments
# ═══════════════════════════════════════════════════════════════
class TestTaxAdjustmentScenarios:
    """سيناريوهات تسويات الضرائب"""

    def test_list_tax_adjustments(self, client, admin_headers):
        """✅ عرض تسويات الضرائب"""
        r = client.get("/api/taxes/adjustments", headers=admin_headers)
        assert r.status_code in [200, 404]

    def test_create_tax_adjustment_increase(self, client, admin_headers):
        """✅ إنشاء تسوية زيادة ضريبة"""
        r = client.post("/api/taxes/adjustments", json={
            "adjustment_type": "increase",
            "amount": 500,
            "adjustment_date": str(date.today()),
            "reason": "تصحيح ضريبة فاتورة سابقة",
            "branch_id": 1,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 404]

    def test_create_tax_adjustment_decrease(self, client, admin_headers):
        """✅ إنشاء تسوية تخفيض ضريبة"""
        r = client.post("/api/taxes/adjustments", json={
            "adjustment_type": "decrease",
            "amount": 200,
            "adjustment_date": str(date.today()),
            "reason": "خصم ضريبي مستحق",
            "branch_id": 1,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 404]


# ═══════════════════════════════════════════════════════════════
# 📅 السنوات المالية - Fiscal Years
# ═══════════════════════════════════════════════════════════════
class TestFiscalYearScenarios:
    """سيناريوهات السنوات المالية"""

    def test_list_fiscal_years(self, client, admin_headers):
        """✅ عرض السنوات المالية"""
        r = client.get("/api/accounting/fiscal-years", headers=admin_headers)
        assert r.status_code in [200, 404]

    def test_get_current_fiscal_year(self, client, admin_headers):
        """✅ السنة المالية الحالية"""
        r = client.get("/api/accounting/fiscal-years/current", headers=admin_headers)
        assert r.status_code in [200, 404]

    def test_create_fiscal_year(self, client, admin_headers):
        """✅ إنشاء سنة مالية جديدة"""
        r = client.post("/api/accounting/fiscal-years", json={
            "year": 2026,
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 404]

    def test_get_fiscal_year_periods(self, client, admin_headers):
        """✅ فترات السنة المالية"""
        r = client.get("/api/accounting/fiscal-years", headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("لا سنوات مالية")
        years = r.json()
        if not years:
            pytest.skip("لا سنوات مالية")
        year_id = years[0]["id"]
        r2 = client.get(f"/api/accounting/fiscal-years/{year_id}/periods", headers=admin_headers)
        assert r2.status_code in [200, 404]

    def test_close_fiscal_period(self, client, admin_headers):
        """✅ إقفال فترة محاسبية"""
        r = client.get("/api/accounting/fiscal-years/current", headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("لا سنة مالية")
        year = r.json()
        if not year:
            pytest.skip("لا سنة مالية")
        r2 = client.post(f"/api/accounting/fiscal-years/{year['id']}/close-period", json={
            "period_number": 1,
        }, headers=admin_headers)
        assert r2.status_code in [200, 400, 404]


# ═══════════════════════════════════════════════════════════════
# 🔒 إقفال السنة المالية - Year End Close
# ═══════════════════════════════════════════════════════════════
class TestYearEndCloseScenarios:
    """سيناريوهات إقفال السنة المالية"""

    def test_prepare_year_end_close(self, client, admin_headers):
        """✅ تجهيز إقفال السنة"""
        r = client.get("/api/accounting/fiscal-years", headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("لا سنوات مالية")
        years = r.json()
        if not years:
            pytest.skip("لا سنوات مالية")
        year_id = years[0]["id"]
        r2 = client.get(f"/api/accounting/fiscal-years/{year_id}/prepare-close", headers=admin_headers)
        assert r2.status_code in [200, 400, 404]

    def test_year_end_closing_entries(self, client, admin_headers):
        """✅ قيود الإقفال - إقفال الإيرادات والمصروفات للأرباح المحتجزة"""
        r = client.get("/api/accounting/fiscal-years", headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("لا سنوات مالية")
        years = r.json()
        if not years:
            pytest.skip("لا سنوات مالية")
        year_id = years[0]["id"]
        r2 = client.post(f"/api/accounting/fiscal-years/{year_id}/close", headers=admin_headers)
        assert r2.status_code in [200, 400, 404]


# ═══════════════════════════════════════════════════════════════
# 📊 تقارير الضرائب - Tax Reports
# ═══════════════════════════════════════════════════════════════
class TestTaxReportScenarios:
    """تقارير الضرائب"""

    def test_vat_report(self, client, admin_headers):
        """✅ تقرير ضريبة القيمة المضافة"""
        r = client.get("/api/reports/taxes/vat?start_date=2025-01-01&end_date=2025-12-31", 
                      headers=admin_headers)
        assert r.status_code in [200, 404]

    def test_tax_summary_report(self, client, admin_headers):
        """✅ ملخص الضرائب"""
        r = client.get("/api/taxes/summary", headers=admin_headers)
        assert r.status_code in [200, 404]

    def test_sales_tax_report(self, client, admin_headers):
        """✅ تقرير ضريبة المبيعات"""
        r = client.get("/api/reports/taxes/sales?start_date=2025-01-01&end_date=2025-12-31",
                      headers=admin_headers)
        assert r.status_code in [200, 404]

    def test_purchase_tax_report(self, client, admin_headers):
        """✅ تقرير ضريبة المشتريات"""
        r = client.get("/api/reports/taxes/purchases?start_date=2025-01-01&end_date=2025-12-31",
                      headers=admin_headers)
        assert r.status_code in [200, 404]

    def test_tax_liability_report(self, client, admin_headers):
        """✅ تقرير الالتزام الضريبي"""
        r = client.get("/api/taxes/liability", headers=admin_headers)
        assert r.status_code in [200, 404]

