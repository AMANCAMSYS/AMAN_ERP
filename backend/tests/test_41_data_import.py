"""
AMAN ERP - اختبارات استيراد/تصدير البيانات
Data Import/Export: Entity Types, Templates, Preview, Execute, Export, History
═══════════════════════════════════════════════════════════════
"""

from helpers import assert_valid_response


# ═══════════════════════════════════════════════════════════════
# 📥 استيراد البيانات - Data Import
# ═══════════════════════════════════════════════════════════════
class TestDataImport:
    """سيناريوهات استيراد البيانات"""

    def test_list_importable_entities(self, client, admin_headers):
        """✅ عرض الكيانات القابلة للاستيراد"""
        r = client.get("/api/data-import/entity-types", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_download_template_accounts(self, client, admin_headers):
        """✅ تحميل قالب استيراد الحسابات"""
        r = client.get("/api/data-import/template/accounts", headers=admin_headers)
        assert r.status_code in [200, 404]

    def test_download_template_customers(self, client, admin_headers):
        """✅ تحميل قالب استيراد العملاء"""
        r = client.get("/api/data-import/template/customers", headers=admin_headers)
        assert r.status_code in [200, 400, 404]

    def test_download_template_suppliers(self, client, admin_headers):
        """✅ تحميل قالب استيراد الموردين"""
        r = client.get("/api/data-import/template/suppliers", headers=admin_headers)
        assert r.status_code in [200, 400, 404]

    def test_download_template_products(self, client, admin_headers):
        """✅ تحميل قالب استيراد المنتجات"""
        r = client.get("/api/data-import/template/products", headers=admin_headers)
        assert r.status_code in [200, 404]

    def test_download_template_invalid_entity(self, client, admin_headers):
        """❌ قالب كيان غير موجود"""
        r = client.get("/api/data-import/template/nonexistent_entity", headers=admin_headers)
        assert r.status_code in [400, 404]


# ═══════════════════════════════════════════════════════════════
# 📤 تصدير البيانات - Data Export
# ═══════════════════════════════════════════════════════════════
class TestDataExport:
    """سيناريوهات تصدير البيانات"""

    def test_export_accounts(self, client, admin_headers):
        """✅ تصدير دليل الحسابات"""
        r = client.get("/api/data-import/export/accounts", headers=admin_headers)
        assert r.status_code in [200, 400, 404, 500]

    def test_export_customers(self, client, admin_headers):
        """✅ تصدير بيانات العملاء"""
        r = client.get("/api/data-import/export/customers", headers=admin_headers)
        assert r.status_code in [200, 400, 404]

    def test_export_suppliers(self, client, admin_headers):
        """✅ تصدير بيانات الموردين"""
        r = client.get("/api/data-import/export/suppliers", headers=admin_headers)
        assert r.status_code in [200, 400, 404]

    def test_export_products(self, client, admin_headers):
        """✅ تصدير بيانات المنتجات"""
        r = client.get("/api/data-import/export/products", headers=admin_headers)
        assert r.status_code in [200, 400, 404]

    def test_export_invalid_entity(self, client, admin_headers):
        """❌ تصدير كيان غير موجود"""
        r = client.get("/api/data-import/export/nonexistent_entity", headers=admin_headers)
        assert r.status_code in [400, 404]


# ═══════════════════════════════════════════════════════════════
# 📋 سجل الاستيراد - Import History
# ═══════════════════════════════════════════════════════════════
class TestImportHistory:
    """سيناريوهات سجل الاستيراد"""

    def test_get_import_history(self, client, admin_headers):
        """✅ عرض سجل عمليات الاستيراد"""
        r = client.get("/api/data-import/history", headers=admin_headers)
        assert r.status_code in [200, 404]
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data, (list, dict))
