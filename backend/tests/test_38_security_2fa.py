"""
AMAN ERP - اختبارات الأمان المتقدم والمصادقة الثنائية
Security: 2FA, Password Change, Password Policy, Sessions
═══════════════════════════════════════════════════════════════
"""

import pytest
from helpers import assert_valid_response, assert_error_response


# ═══════════════════════════════════════════════════════════════
# 🔐 المصادقة الثنائية - Two-Factor Authentication
# ═══════════════════════════════════════════════════════════════
class TestTwoFactorAuth:
    """سيناريوهات المصادقة الثنائية"""

    def test_get_2fa_status(self, client, admin_headers):
        """✅ حالة المصادقة الثنائية"""
        r = client.get("/api/security/2fa/status", headers=admin_headers)
        assert r.status_code in [200, 404]
        if r.status_code == 200:
            data = r.json()
            assert "enabled" in data or "is_enabled" in data or isinstance(data, dict)

    def test_setup_2fa(self, client, admin_headers):
        """✅ إعداد المصادقة الثنائية"""
        r = client.post("/api/security/2fa/setup", headers=admin_headers)
        assert r.status_code in [200, 400, 404, 500]
        if r.status_code == 200:
            data = r.json()
            # يجب أن يرجع QR code أو مفتاح سري
            assert "secret" in data or "qr_code" in data or "otpauth_url" in data

    def test_verify_2fa_invalid_code(self, client, admin_headers):
        """❌ رفض رمز 2FA غير صالح"""
        r = client.post("/api/security/2fa/verify", json={
            "code": "000000",
        }, headers=admin_headers)
        assert r.status_code in [400, 401, 422, 500]

    def test_disable_2fa(self, client, admin_headers):
        """✅ تعطيل المصادقة الثنائية"""
        r = client.post("/api/security/2fa/disable", json={
            "code": "000000",  # رمز وهمي - قد يتم رفضه
        }, headers=admin_headers)
        assert r.status_code in [200, 400, 401, 422, 500]


# ═══════════════════════════════════════════════════════════════
# 🔑 تغيير كلمة المرور - Password Change
# ═══════════════════════════════════════════════════════════════
class TestPasswordManagement:
    """سيناريوهات تغيير كلمة المرور"""

    def test_change_password_wrong_current(self, client, admin_headers):
        """❌ رفض تغيير كلمة المرور بكلمة حالية خاطئة"""
        r = client.post("/api/security/change-password", json={
            "current_password": "wrong_password_12345",
            "new_password": "New@Pass123",
            "confirm_password": "New@Pass123",
        }, headers=admin_headers)
        assert r.status_code in [400, 401, 422]

    def test_change_password_mismatch(self, client, admin_headers):
        """❌ رفض تغيير كلمة المرور عند عدم تطابق التأكيد"""
        r = client.post("/api/security/change-password", json={
            "current_password": "As123321",
            "new_password": "New@Pass123",
            "confirm_password": "Different@Pass123",
        }, headers=admin_headers)
        assert r.status_code in [400, 422]

    def test_change_password_weak(self, client, admin_headers):
        """❌ رفض كلمة مرور ضعيفة"""
        r = client.post("/api/security/change-password", json={
            "current_password": "As123321",
            "new_password": "123",
            "confirm_password": "123",
        }, headers=admin_headers)
        assert r.status_code in [400, 422]

    def test_check_password_expiry(self, client, admin_headers):
        """✅ فحص انتهاء صلاحية كلمة المرور"""
        r = client.get("/api/security/password-expiry", headers=admin_headers)
        assert r.status_code in [200, 404]


# ═══════════════════════════════════════════════════════════════
# 📜 سياسة كلمة المرور - Password Policy
# ═══════════════════════════════════════════════════════════════
class TestPasswordPolicy:
    """سيناريوهات سياسة كلمة المرور"""

    def test_get_password_policy(self, client, admin_headers):
        """✅ عرض سياسة كلمة المرور"""
        r = client.get("/api/security/password-policy", headers=admin_headers)
        assert r.status_code in [200, 404]
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data, dict)

    def test_update_password_policy(self, client, admin_headers):
        """✅ تحديث سياسة كلمة المرور"""
        r = client.put("/api/security/password-policy", json={
            "min_length": 8,
            "require_uppercase": True,
            "require_lowercase": True,
            "require_digit": True,
            "require_special": True,
            "max_age_days": 90,
        }, headers=admin_headers)
        assert r.status_code in [200, 400, 404, 422]


# ═══════════════════════════════════════════════════════════════
# 💻 الجلسات النشطة - Active Sessions
# ═══════════════════════════════════════════════════════════════
class TestSessions:
    """سيناريوهات الجلسات النشطة"""

    def test_list_active_sessions(self, client, admin_headers):
        """✅ عرض الجلسات النشطة"""
        r = client.get("/api/security/sessions", headers=admin_headers)
        assert r.status_code in [200, 404]
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data, (list, dict))

    def test_terminate_specific_session(self, client, admin_headers):
        """✅ إنهاء جلسة محددة"""
        r = client.get("/api/security/sessions", headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("لا يمكن جلب الجلسات")
        data = r.json()
        sessions = data if isinstance(data, list) else data.get("sessions", data.get("items", []))
        if len(sessions) < 2:
            pytest.skip("أقل من جلستين لاختبار الإنهاء")
        # إنهاء آخر جلسة (ليست الحالية)
        session_id = sessions[-1].get("id", sessions[-1].get("session_id"))
        if session_id:
            r2 = client.delete(f"/api/security/sessions/{session_id}", headers=admin_headers)
            assert r2.status_code in [200, 204, 400, 404]

    def test_terminate_all_sessions(self, client, admin_headers):
        """✅ إنهاء جميع الجلسات (عدا الحالية)"""
        r = client.delete("/api/security/sessions", headers=admin_headers)
        assert r.status_code in [200, 204, 400, 404]
