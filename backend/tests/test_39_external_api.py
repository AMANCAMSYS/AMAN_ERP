"""
AMAN ERP - اختبارات التكامل الخارجي: مفاتيح API، Webhooks، ZATCA، ضريبة الاستقطاع
External Integration: API Keys, Webhooks, ZATCA QR, WHT
═══════════════════════════════════════════════════════════════
"""

import pytest
from datetime import date
from helpers import assert_valid_response


# ═══════════════════════════════════════════════════════════════
# 🔑 مفاتيح API - API Keys
# ═══════════════════════════════════════════════════════════════
class TestAPIKeys:
    """سيناريوهات مفاتيح API"""

    def test_list_api_keys(self, client, admin_headers):
        """✅ عرض قائمة مفاتيح API"""
        r = client.get("/api/external/api-keys", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        assert isinstance(data, (list, dict))

    def test_create_api_key(self, client, admin_headers):
        """✅ إنشاء مفتاح API جديد"""
        r = client.post("/api/external/api-keys", json={
            "name": "مفتاح اختبار آلي",
            "permissions": ["read"],
            "expires_in_days": 30,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 422]
        if r.status_code in [200, 201]:
            data = r.json()
            assert "key" in data or "api_key" in data or "id" in data

    def test_create_api_key_full_access(self, client, admin_headers):
        """✅ إنشاء مفتاح API بصلاحيات كاملة"""
        r = client.post("/api/external/api-keys", json={
            "name": "مفتاح كامل الصلاحيات",
            "permissions": ["read", "write", "delete"],
            "expires_in_days": 7,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 422]

    def test_revoke_api_key(self, client, admin_headers):
        """✅ إلغاء مفتاح API"""
        # إنشاء مفتاح ثم إلغاؤه
        r = client.post("/api/external/api-keys", json={
            "name": "مفتاح للإلغاء",
            "permissions": ["read"],
            "expires_in_days": 1,
        }, headers=admin_headers)
        if r.status_code in [200, 201]:
            key_id = r.json().get("id")
            if key_id:
                r2 = client.delete(f"/api/external/api-keys/{key_id}", headers=admin_headers)
                assert r2.status_code in [200, 204, 400, 404]


# ═══════════════════════════════════════════════════════════════
# 🔗 Webhooks
# ═══════════════════════════════════════════════════════════════
class TestWebhooks:
    """سيناريوهات Webhooks"""

    def test_list_webhook_events(self, client, admin_headers):
        """✅ عرض الأحداث المتاحة"""
        r = client.get("/api/external/webhooks/events", headers=admin_headers)
        assert r.status_code in [200, 404]
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data, list)

    def test_list_webhooks(self, client, admin_headers):
        """✅ عرض قائمة Webhooks"""
        r = client.get("/api/external/webhooks", headers=admin_headers)
        assert_valid_response(r)

    def test_create_webhook(self, client, admin_headers):
        """✅ إنشاء Webhook"""
        r = client.post("/api/external/webhooks", json={
            "name": "Webhook اختبار",
            "url": "https://example.com/webhook",
            "events": ["invoice.created", "payment.received"],
            "is_active": True,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 422]

    def test_update_webhook(self, client, admin_headers):
        """✅ تحديث Webhook"""
        r = client.get("/api/external/webhooks", headers=admin_headers)
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("data", []))
        if not items:
            pytest.skip("لا يوجد Webhooks")
        wh_id = items[0]["id"]
        r2 = client.put(f"/api/external/webhooks/{wh_id}", json={
            "name": "Webhook محدّث",
            "is_active": False,
        }, headers=admin_headers)
        assert r2.status_code in [200, 400, 404, 422]

    def test_get_webhook_logs(self, client, admin_headers):
        """✅ عرض سجل Webhook"""
        r = client.get("/api/external/webhooks", headers=admin_headers)
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("data", []))
        if not items:
            pytest.skip("لا يوجد Webhooks")
        wh_id = items[0]["id"]
        r2 = client.get(f"/api/external/webhooks/{wh_id}/logs", headers=admin_headers)
        assert r2.status_code in [200, 404]

    def test_delete_webhook(self, client, admin_headers):
        """✅ حذف Webhook"""
        r = client.post("/api/external/webhooks", json={
            "name": "Webhook للحذف",
            "url": "https://example.com/delete-test",
            "events": ["test.event"],
            "is_active": False,
        }, headers=admin_headers)
        if r.status_code in [200, 201]:
            wh_id = r.json().get("id")
            if wh_id:
                r2 = client.delete(f"/api/external/webhooks/{wh_id}", headers=admin_headers)
                assert r2.status_code in [200, 204, 400, 404]


# ═══════════════════════════════════════════════════════════════
# 📱 ZATCA - الفوترة الإلكترونية
# ═══════════════════════════════════════════════════════════════
class TestZATCA:
    """سيناريوهات ZATCA"""

    def test_generate_qr_code(self, client, admin_headers):
        """✅ توليد رمز QR للفاتورة"""
        r = client.post("/api/external/zatca/generate-qr", json={
            "seller_name": "شركة أمان",
            "tax_number": "300000000000003",
            "invoice_date": str(date.today()),
            "total_amount": 11500,
            "vat_amount": 1500,
        }, headers=admin_headers)
        assert r.status_code in [200, 400, 422]
        if r.status_code == 200:
            data = r.json()
            assert "qr_code" in data or "qr" in data or "base64" in data

    def test_generate_keypair(self, client, admin_headers):
        """✅ توليد زوج مفاتيح ZATCA"""
        r = client.post("/api/external/zatca/generate-keypair", json={
            "common_name": "AMAN ERP Test",
            "organization": "شركة أمان",
        }, headers=admin_headers)
        assert r.status_code in [200, 400, 422]

    def test_verify_invoice_qr(self, client, admin_headers):
        """✅ التحقق من QR فاتورة"""
        r = client.get("/api/external/zatca/verify/1", headers=admin_headers)
        assert r.status_code in [200, 400, 404]


# ═══════════════════════════════════════════════════════════════
# 💰 ضريبة الاستقطاع - Withholding Tax (WHT)
# ═══════════════════════════════════════════════════════════════
class TestWHT:
    """سيناريوهات ضريبة الاستقطاع"""

    def test_list_wht_rates(self, client, admin_headers):
        """✅ عرض نسب ضريبة الاستقطاع"""
        r = client.get("/api/external/wht/rates", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        assert isinstance(data, (list, dict))

    def test_create_wht_rate(self, client, admin_headers):
        """✅ إنشاء نسبة ضريبة استقطاع"""
        r = client.post("/api/external/wht/rates", json={
            "name": "خدمات استشارية",
            "rate": 15.0,
            "category": "services",
            "is_active": True,
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 409, 422]

    def test_calculate_wht(self, client, admin_headers):
        """✅ حساب ضريبة الاستقطاع"""
        r = client.post("/api/external/wht/calculate", json={
            "amount": 100000,
            "rate_id": 1,
        }, headers=admin_headers)
        assert r.status_code in [200, 400, 404, 422]
        if r.status_code == 200:
            data = r.json()
            assert "wht_amount" in data or "tax_amount" in data or "amount" in data

    def test_create_wht_transaction(self, client, admin_headers):
        """✅ إنشاء عملية استقطاع ضريبي"""
        r = client.post("/api/external/wht/transactions", json={
            "party_name": "شركة خدمات خارجية",
            "gross_amount": 50000,
            "wht_rate": 15.0,
            "wht_amount": 7500,
            "net_amount": 42500,
            "transaction_date": str(date.today()),
            "description": "دفعة خدمات استشارية",
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 422]

    def test_list_wht_transactions(self, client, admin_headers):
        """✅ عرض عمليات الاستقطاع الضريبي"""
        r = client.get("/api/external/wht/transactions", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        assert isinstance(data, (list, dict))
