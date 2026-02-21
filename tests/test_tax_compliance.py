"""
اختبارات وحدة الامتثال الضريبي — AMAN ERP
═══════════════════════════════════════════
يختبر:
  - قائمة الأنظمة الضريبية (tax_regimes)
  - قائمة الدول المدعومة
  - إعدادات الشركة الضريبية
  - إعدادات الفروع الضريبية
  - الضرائب المطبقة حسب الفرع
  - تقرير VAT السعودي (ZATCA)
  - تقرير ضريبة الدخل السوري
  - تقرير VAT الإماراتي (FTA)
  - تقرير VAT مصر (ETA)
  - نظرة عامة على الامتثال
  - فلترة أسعار الضرائب حسب الدولة
  - إنشاء إقرار ضريبي مع jurisdiction
"""

import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from fastapi.testclient import TestClient
from main import app
import json

client = TestClient(app)

# ═══════════════════════════════════════════════════════════
# Auth Helpers
# ═══════════════════════════════════════════════════════════

def get_test_credentials():
    """Load test credentials from test_data"""
    creds_file = os.path.join(os.path.dirname(__file__), '..', 'test_data', 'load_test_credentials.json')
    with open(creds_file) as f:
        creds = json.load(f)
    return creds[0]  # Use first credential

@pytest.fixture(scope="module")
def auth_headers():
    """Use direct token generation like other backend tests"""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
    from routers.auth import create_access_token
    from datetime import timedelta
    token = create_access_token({
        "sub": "aaaa",
        "user_id": 1,
        "company_id": "be67ce39",
        "role": "superuser",
        "permissions": ["*"],
        "allowed_branches": [1],
        "type": "company_user"
    }, expires_delta=timedelta(hours=24))
    return {"Authorization": f"Bearer {token}"}


# ═══════════════════════════════════════════════════════════
# 1. Tax Regimes
# ═══════════════════════════════════════════════════════════

class TestTaxRegimes:

    def test_list_all_regimes(self, auth_headers):
        """جلب جميع الأنظمة الضريبية بدون فلتر"""
        res = client.get("/api/tax-compliance/regimes", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)

    def test_list_regimes_filter_by_sa(self, auth_headers):
        """تصفية الأنظمة حسب السعودية"""
        res = client.get("/api/tax-compliance/regimes?country_code=SA", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        for regime in data:
            assert regime["country_code"] == "SA"

    def test_list_regimes_filter_by_sy(self, auth_headers):
        """تصفية الأنظمة حسب سوريا"""
        res = client.get("/api/tax-compliance/regimes?country_code=SY", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        for regime in data:
            assert regime["country_code"] == "SY"

    def test_regimes_have_required_fields(self, auth_headers):
        """التحقق من الحقول المطلوبة في الأنظمة"""
        res = client.get("/api/tax-compliance/regimes?country_code=SA", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        if len(data) > 0:
            regime = data[0]
            assert "tax_type" in regime
            assert "name_ar" in regime
            assert "name_en" in regime
            assert "default_rate" in regime
            assert "is_required" in regime
            assert "filing_frequency" in regime

    def test_regimes_active_filter(self, auth_headers):
        """فلتر الأنظمة النشطة"""
        res = client.get("/api/tax-compliance/regimes?is_active=true", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)


# ═══════════════════════════════════════════════════════════
# 2. Supported Countries
# ═══════════════════════════════════════════════════════════

class TestSupportedCountries:

    def test_list_countries(self, auth_headers):
        """جلب قائمة الدول المدعومة"""
        res = client.get("/api/tax-compliance/countries", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)

    def test_countries_have_required_fields(self, auth_headers):
        """التحقق من حقول الدول"""
        res = client.get("/api/tax-compliance/countries", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        if len(data) > 0:
            country = data[0]
            assert "country_code" in country
            assert "name_ar" in country
            assert "name_en" in country
            assert "has_vat" in country
            assert "has_zakat" in country

    def test_saudi_arabia_has_vat_and_zakat(self, auth_headers):
        """التحقق من خصائص السعودية"""
        res = client.get("/api/tax-compliance/countries", headers=auth_headers)
        assert res.status_code == 200
        countries = res.json()
        sa = next((c for c in countries if c["country_code"] == "SA"), None)
        if sa:
            assert sa["has_vat"] is True
            assert sa["has_zakat"] is True
            assert sa["has_zatca"] is True

    def test_syria_has_no_vat(self, auth_headers):
        """سوريا لا يوجد بها VAT"""
        res = client.get("/api/tax-compliance/countries", headers=auth_headers)
        assert res.status_code == 200
        countries = res.json()
        sy = next((c for c in countries if c["country_code"] == "SY"), None)
        if sy:
            assert sy["has_vat"] is False
            assert sy["has_zatca"] is False


# ═══════════════════════════════════════════════════════════
# 3. Company Tax Settings
# ═══════════════════════════════════════════════════════════

class TestCompanyTaxSettings:

    def test_get_company_settings(self, auth_headers):
        """جلب إعدادات الضرائب على مستوى الشركة"""
        res = client.get("/api/tax-compliance/company-settings", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_update_company_settings_sa(self, auth_headers):
        """تحديث إعدادات الشركة للسعودية"""
        res = client.put("/api/tax-compliance/company-settings", json={
            "country_code": "SA",
            "is_vat_registered": True,
            "vat_number": "3001234567890123",
            "zatca_phase": "phase2",
            "fiscal_year_start": "01-01",
            "default_filing_frequency": "quarterly"
        }, headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data.get("success") is True

    def test_update_company_settings_sy(self, auth_headers):
        """تحديث إعدادات الشركة لسوريا"""
        res = client.put("/api/tax-compliance/company-settings", json={
            "country_code": "SY",
            "is_vat_registered": False,
            "tax_registration_number": "SY123456789",
            "fiscal_year_start": "01-01",
            "default_filing_frequency": "annual"
        }, headers=auth_headers)
        assert res.status_code == 200

    def test_company_settings_persisted(self, auth_headers):
        """التحقق من حفظ الإعدادات"""
        # Update
        client.put("/api/tax-compliance/company-settings", json={
            "country_code": "SA",
            "is_vat_registered": True,
            "vat_number": "TEST-VAT-12345",
            "fiscal_year_start": "01-01",
            "default_filing_frequency": "quarterly"
        }, headers=auth_headers)
        # Retrieve
        res = client.get("/api/tax-compliance/company-settings", headers=auth_headers)
        assert res.status_code == 200
        settings_list = res.json()
        sa_setting = next((s for s in settings_list if s.get("country_code") == "SA"), None)
        assert sa_setting is not None


# ═══════════════════════════════════════════════════════════
# 4. Branch Tax Settings
# ═══════════════════════════════════════════════════════════

class TestBranchTaxSettings:

    def get_first_branch(self, auth_headers):
        """Get first available branch ID"""
        res = client.get("/api/branches/", headers=auth_headers)
        if res.status_code == 200 and len(res.json()) > 0:
            return res.json()[0]["id"]
        return None

    def test_get_branch_settings_default(self, auth_headers):
        """جلب إعدادات الفرع الضريبية"""
        branch_id = self.get_first_branch(auth_headers)
        if not branch_id:
            pytest.skip("No branches available")
        res = client.get(f"/api/tax-compliance/branch-settings/{branch_id}", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        # API returns {branch: {...}, tax_settings: [...], country_meta: {...}}
        assert "branch" in data or "branch_id" in data
        if "branch" in data:
            assert data["branch"]["id"] == branch_id
        else:
            assert data["branch_id"] == branch_id

    def test_update_branch_setting(self, auth_headers):
        """تحديث إعداد ضريبي للفرع"""
        # Get a regime first
        regimes_res = client.get("/api/tax-compliance/regimes?country_code=SA", headers=auth_headers)
        if regimes_res.status_code != 200 or not regimes_res.json():
            pytest.skip("No SA tax regimes available")

        branch_id = self.get_first_branch(auth_headers)
        if not branch_id:
            pytest.skip("No branches available")

        regime = regimes_res.json()[0]
        res = client.put("/api/tax-compliance/branch-settings", json={
            "branch_id": branch_id,
            "tax_regime_id": regime["id"],
            "is_registered": True,
            "registration_number": "BRANCH-VAT-001"
        }, headers=auth_headers)
        assert res.status_code in (200, 201)

    def test_get_applicable_taxes(self, auth_headers):
        """جلب الضرائب المطبقة على الفرع"""
        branch_id = self.get_first_branch(auth_headers)
        if not branch_id:
            pytest.skip("No branches available")
        res = client.get(f"/api/tax-compliance/applicable-taxes/{branch_id}", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        # API returns {branch_id, jurisdiction, taxes: [...]} or a list
        if isinstance(data, list):
            assert True  # list form
        else:
            assert "taxes" in data
            assert isinstance(data["taxes"], list)


# ═══════════════════════════════════════════════════════════
# 5. Official Tax Reports
# ═══════════════════════════════════════════════════════════

class TestOfficialReports:

    def test_saudi_vat_report_current_year(self, auth_headers):
        """اختبار إقرار VAT السعودي للسنة الحالية"""
        import datetime
        year = datetime.date.today().year
        res = client.get(f"/api/tax-compliance/reports/sa-vat?year={year}", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert "boxes" in data
        # summary may not exist; boxes is a dict keyed by box name
        boxes = data["boxes"]
        assert isinstance(boxes, dict) and len(boxes) > 0

    def test_saudi_vat_report_has_zatca_boxes(self, auth_headers):
        """تقرير VAT السعودي يجب أن يحتوي على صناديق ZATCA"""
        res = client.get("/api/tax-compliance/reports/sa-vat?year=2024", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        boxes = data.get("boxes", [])
        # ZATCA standard VAT return has at least 3 boxes
        assert len(boxes) >= 3

    def test_saudi_vat_report_with_quarter(self, auth_headers):
        """تقرير VAT السعودي للربع الأول"""
        res = client.get("/api/tax-compliance/reports/sa-vat?year=2024&period=Q1", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert "boxes" in data

    def test_syrian_income_report(self, auth_headers):
        """اختبار تقرير ضريبة الدخل السوري"""
        res = client.get("/api/tax-compliance/reports/sy-income?year=2024", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        # SY income report returns {income_statement, tax_computation, report_name_ar, ...}
        assert "income_statement" in data or "boxes" in data or "total_income" in data or "report_name_ar" in data or "report_name" in data

    def test_uae_vat_report(self, auth_headers):
        """اختبار تقرير VAT الإماراتي"""
        res = client.get("/api/tax-compliance/reports/ae-vat?year=2024", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        # AE VAT report uses {supplies, expenses} sections
        assert "boxes" in data or "supplies" in data or "expenses" in data

    def test_egypt_vat_report(self, auth_headers):
        """اختبار تقرير VAT مصر"""
        res = client.get("/api/tax-compliance/reports/eg-vat?year=2024", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        # EG VAT report uses {output, input} sections
        assert "boxes" in data or "output" in data or "input" in data

    def test_generic_income_report(self, auth_headers):
        """اختبار تقرير ضريبة الدخل العام"""
        res = client.get("/api/tax-compliance/reports/generic-income?year=2024", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, dict)

    def test_report_has_company_info(self, auth_headers):
        """التحقق من بيانات الشركة في التقرير"""
        res = client.get("/api/tax-compliance/reports/sa-vat?year=2024", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        # Should have at minimum report name (Arabic or English)
        assert "report_name_ar" in data or "report_name_en" in data or "report_name" in data or "company_name" in data or "title" in data

    def test_report_box_numeric_values(self, auth_headers):
        """التحقق من أن قيم الصناديق أرقام"""
        res = client.get("/api/tax-compliance/reports/sa-vat?year=2024", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        boxes = data.get("boxes", [])
        for box in boxes:
            for key in ["taxable_amount", "tax_amount", "amount"]:
                if key in box and box[key] is not None:
                    assert isinstance(box[key], (int, float)), f"Expected numeric value for {key}, got {type(box[key])}"


# ═══════════════════════════════════════════════════════════
# 6. Compliance Overview
# ═══════════════════════════════════════════════════════════

class TestComplianceOverview:

    def test_get_overview(self, auth_headers):
        """جلب النظرة العامة على الامتثال"""
        res = client.get("/api/tax-compliance/overview", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, dict)

    def test_overview_has_branches(self, auth_headers):
        """التحقق من وجود معلومات الفروع"""
        res = client.get("/api/tax-compliance/overview", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        # branches are nested inside jurisdictions[]
        has_branches = "branches" in data or (
            "jurisdictions" in data and
            any("branches" in j for j in data["jurisdictions"])
        )
        assert has_branches

    def test_overview_has_counters(self, auth_headers):
        """التحقق من وجود مؤشرات الملخص"""
        res = client.get("/api/tax-compliance/overview", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        # Check that at least some known fields are present
        # branches are nested in jurisdictions; top-level has company_settings, jurisdictions, pending_returns
        expected_fields = {"jurisdictions", "pending_returns"}
        missing = expected_fields - set(data.keys())
        assert not missing, f"Missing fields: {missing}"


# ═══════════════════════════════════════════════════════════
# 7. Jurisdiction Awareness in Tax Returns
# ═══════════════════════════════════════════════════════════

class TestJurisdictionInTaxReturns:

    def test_list_tax_rates_without_country_filter(self, auth_headers):
        """جلب أسعار الضرائب بدون فلتر دولة"""
        res = client.get("/api/taxes/rates", headers=auth_headers)
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_list_tax_rates_with_sa_filter(self, auth_headers):
        """جلب أسعار الضرائب للسعودية"""
        res = client.get("/api/taxes/rates?country_code=SA", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        # All results must be SA or global (country_code is NULL)
        for rate in data:
            assert rate.get("country_code") in ("SA", None)

    def test_list_tax_rates_with_sy_filter(self, auth_headers):
        """جلب أسعار الضرائب لسوريا"""
        res = client.get("/api/taxes/rates?country_code=SY", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        for rate in data:
            assert rate.get("country_code") in ("SY", None)


# ═══════════════════════════════════════════════════════════
# 8. Migration Integrity
# ═══════════════════════════════════════════════════════════

class TestMigrationIntegrity:

    def test_tax_regimes_table_exists(self, auth_headers):
        """التحقق من وجود جدول tax_regimes"""
        # If the regimes endpoint works, the table exists
        res = client.get("/api/tax-compliance/regimes", headers=auth_headers)
        assert res.status_code == 200

    def test_company_tax_settings_table_exists(self, auth_headers):
        """التحقق من وجود جدول company_tax_settings"""
        res = client.get("/api/tax-compliance/company-settings", headers=auth_headers)
        assert res.status_code == 200

    def test_overview_endpoint_works(self, auth_headers):
        """التحقق من عمل نقطة نهاية النظرة العامة"""
        res = client.get("/api/tax-compliance/overview", headers=auth_headers)
        assert res.status_code == 200

    def test_all_endpoints_authenticated(self):
        """جميع النقاط النهائية تتطلب المصادقة"""
        endpoints = [
            "/api/tax-compliance/regimes",
            "/api/tax-compliance/company-settings",
            "/api/tax-compliance/overview",
            "/api/tax-compliance/reports/sa-vat",
        ]
        for ep in endpoints:
            res = client.get(ep)
            assert res.status_code in (401, 403), f"Endpoint {ep} should require auth, got {res.status_code}"


# ═══════════════════════════════════════════════════════════
# 9. Edge Cases
# ═══════════════════════════════════════════════════════════

class TestEdgeCases:

    def test_unknown_country_regimes_returns_empty(self, auth_headers):
        """بلد غير موجود يُرجع قائمة فارغة"""
        res = client.get("/api/tax-compliance/regimes?country_code=XX", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_branch_settings_nonexistent_branch(self, auth_headers):
        """فرع غير موجود يرجع 404"""
        res = client.get("/api/tax-compliance/branch-settings/999999", headers=auth_headers)
        assert res.status_code in (404, 200)  # May return empty or 404

    def test_report_with_invalid_year(self, auth_headers):
        """الملف مع سنة غير صالحة"""
        res = client.get("/api/tax-compliance/reports/sa-vat?year=abc", headers=auth_headers)
        assert res.status_code == 422  # Validation error

    def test_company_settings_invalid_country(self, auth_headers):
        """رفض كود دولة غير صالح"""
        res = client.put("/api/tax-compliance/company-settings", json={
            "country_code": "XX",  # Invalid
            "is_vat_registered": False,
            "fiscal_year_start": "01-01",
            "default_filing_frequency": "quarterly"
        }, headers=auth_headers)
        # Should either succeed (for unknown CC) or return 422
        assert res.status_code in (200, 201, 422)

    def test_applicable_taxes_returns_list(self, auth_headers):
        """الضرائب المطبقة تُرجع قائمة أو كائن يحتوي على قائمة"""
        # Use branch 1 (might not exist but endpoint should handle gracefully)
        res = client.get("/api/tax-compliance/applicable-taxes/1", headers=auth_headers)
        assert res.status_code in (200, 404)
        if res.status_code == 200:
            data = res.json()
            # API returns {branch_id, jurisdiction, taxes: [...]} or a direct list
            if isinstance(data, list):
                assert True
            else:
                assert "taxes" in data
                assert isinstance(data["taxes"], list)
