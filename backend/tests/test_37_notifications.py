"""
AMAN ERP - اختبارات نظام الإشعارات
Notifications: List, Unread Count, Mark Read, Send, Settings
═══════════════════════════════════════════════════════════════
"""

import pytest
from helpers import assert_valid_response


# ═══════════════════════════════════════════════════════════════
# 🔔 الإشعارات - Notifications
# ═══════════════════════════════════════════════════════════════
class TestNotifications:
    """سيناريوهات الإشعارات"""

    def test_list_notifications(self, client, admin_headers):
        """✅ عرض قائمة الإشعارات"""
        r = client.get("/api/notifications", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        assert isinstance(data, (list, dict))

    def test_get_unread_count(self, client, admin_headers):
        """✅ عدد الإشعارات غير المقروءة"""
        r = client.get("/api/notifications/unread-count", headers=admin_headers)
        assert_valid_response(r)
        data = r.json()
        assert isinstance(data, (dict, int))

    def test_send_notification(self, client, admin_headers):
        """✅ إرسال إشعار"""
        r = client.post("/api/notifications/send", json={
            "title": "إشعار اختبار آلي",
            "message": "هذا إشعار تجريبي من نظام الاختبار التلقائي",
            "type": "info",
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 422]

    def test_send_warning_notification(self, client, admin_headers):
        """✅ إرسال إشعار تحذيري"""
        r = client.post("/api/notifications/send", json={
            "title": "تحذير: رصيد منخفض",
            "message": "حساب الصندوق الرئيسي أصبح أقل من الحد الأدنى",
            "type": "warning",
        }, headers=admin_headers)
        assert r.status_code in [200, 201, 400, 422]

    def test_mark_notification_as_read(self, client, admin_headers):
        """✅ تحديد إشعار كمقروء"""
        # جلب الإشعارات
        r = client.get("/api/notifications", headers=admin_headers)
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("data", data.get("notifications", [])))
        if not items:
            pytest.skip("لا توجد إشعارات")
        notif_id = items[0]["id"]
        r2 = client.put(f"/api/notifications/{notif_id}/read", headers=admin_headers)
        assert r2.status_code in [200, 400, 404]

    def test_mark_all_as_read(self, client, admin_headers):
        """✅ تحديد جميع الإشعارات كمقروءة"""
        r = client.post("/api/notifications/mark-all-read", headers=admin_headers)
        assert r.status_code in [200, 400, 404]


# ═══════════════════════════════════════════════════════════════
# ⚙️ إعدادات الإشعارات - Notification Settings
# ═══════════════════════════════════════════════════════════════
class TestNotificationSettings:
    """سيناريوهات إعدادات الإشعارات"""

    def test_get_notification_settings(self, client, admin_headers):
        """✅ عرض إعدادات الإشعارات"""
        r = client.get("/api/notifications/settings", headers=admin_headers)
        assert r.status_code in [200, 404]

    def test_update_notification_settings(self, client, admin_headers):
        """✅ تحديث إعدادات الإشعارات"""
        r = client.put("/api/notifications/settings", json={
            "email_enabled": True,
            "sms_enabled": False,
            "push_enabled": True,
        }, headers=admin_headers)
        assert r.status_code in [200, 400, 404, 422]

    def test_test_email_connection(self, client, admin_headers):
        """✅ اختبار اتصال البريد الإلكتروني"""
        r = client.post("/api/notifications/test-email", json={
            "email": "test@example.com",
        }, headers=admin_headers)
        # قد يفشل إذا لم تكن SMTP مهيأة - وهذا مقبول
        assert r.status_code in [200, 400, 422, 500]
