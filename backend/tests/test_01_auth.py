"""
AMAN ERP - اختبارات المصادقة والتسجيل
Authentication & Authorization Tests
═══════════════════════════════════════
"""

import pytest
from helpers import assert_valid_response


class TestAuth:
    """🔐 اختبارات تسجيل الدخول والمصادقة"""

    def test_login_success(self, client):
        """✅ تسجيل دخول ناجح"""
        import os
        password = os.environ.get("AMAN_ADMIN_PASSWORD", "admin")
        response = client.post(
            "/api/auth/login",
            data={
                "username": "admin",
                "password": password,
                "grant_type": "password"
            }
        )
        assert_valid_response(response)
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        """❌ تسجيل دخول بكلمة مرور خاطئة"""
        response = client.post(
            "/api/auth/login",
            data={
                "username": "admin",
                "password": "wrong_password_12345",
                "grant_type": "password"
            }
        )
        assert response.status_code in [401, 404], \
            f"Expected 401/404 but got {response.status_code}"

    def test_login_nonexistent_user(self, client):
        """❌ تسجيل دخول بمستخدم غير موجود"""
        response = client.post(
            "/api/auth/login",
            data={
                "username": "nonexistent_user_xyz",
                "password": "any_password",
                "grant_type": "password"
            }
        )
        assert response.status_code in [401, 404]

    def test_access_protected_without_token(self, client):
        """❌ الوصول لصفحة محمية بدون توكن"""
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_access_with_invalid_token(self, client):
        """❌ الوصول بتوكن مزيف"""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer fake_token_12345"}
        )
        assert response.status_code == 401

    def test_get_current_user(self, client, admin_headers):
        """✅ الحصول على بيانات المستخدم الحالي"""
        response = client.get("/api/auth/me", headers=admin_headers)
        assert_valid_response(response)
        data = response.json()
        assert "username" in data
        assert "role" in data
        assert "permissions" in data

    def test_user_has_currency_and_country(self, client, admin_headers):
        """✅ بيانات المستخدم تحتوي على العملة والدولة"""
        response = client.get("/api/auth/me", headers=admin_headers)
        if response.status_code != 200:
            pytest.skip("لا يمكن جلب بيانات المستخدم")
        data = response.json()
        if data.get("role") == "system_admin":
            pytest.skip("مدير النظام ليس لديه شركة")
        assert "currency" in data, "حقل العملة مفقود من بيانات المستخدم"
        assert "country" in data, "حقل الدولة مفقود من بيانات المستخدم"
        assert data["currency"] is not None, "العملة فارغة"
        assert data["country"] is not None, "الدولة فارغة"
        assert len(data["country"]) == 2, f"كود الدولة يجب أن يكون حرفين: {data['country']}"

    def test_user_has_allowed_branches(self, client, admin_headers):
        """✅ بيانات المستخدم تحتوي على الفروع المسموحة"""
        response = client.get("/api/auth/me", headers=admin_headers)
        if response.status_code != 200:
            pytest.skip("لا يمكن جلب بيانات المستخدم")
        data = response.json()
        if data.get("role") == "system_admin":
            pytest.skip("مدير النظام ليس لديه فروع")
        assert "allowed_branches" in data, "حقل الفروع المسموحة مفقود"

    def test_token_has_required_fields(self, client):
        """✅ التوكن يحتوي على جميع الحقول المطلوبة"""
        import os
        password = os.environ.get("AMAN_ADMIN_PASSWORD", "admin")
        response = client.post(
            "/api/auth/login",
            data={
                "username": "admin",
                "password": password,
                "grant_type": "password"
            }
        )
        if response.status_code != 200:
            pytest.skip("لا يمكن تسجيل الدخول")
        
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert len(data["access_token"]) > 50  # JWT عادة أطول من 50 حرف


class TestHealthEndpoints:
    """🏥 اختبارات نقاط الصحة"""

    def test_root_endpoint(self, client):
        """✅ الصفحة الرئيسية تعمل"""
        response = client.get("/")
        assert_valid_response(response)
        data = response.json()
        assert data["system"] == "AMAN ERP"
        assert data["status"] == "running"

    def test_health_check(self, client):
        """✅ فحص صحة النظام"""
        response = client.get("/health")
        assert_valid_response(response)
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"

    def test_api_docs_available(self, client):
        """✅ وثائق API متاحة"""
        response = client.get("/api/docs")
        assert response.status_code == 200


class TestPermissions:
    """🔒 اختبارات الصلاحيات"""

    def test_admin_has_full_permissions(self, client, admin_headers):
        """✅ المدير لديه كل الصلاحيات"""
        response = client.get("/api/auth/me", headers=admin_headers)
        if response.status_code != 200:
            pytest.skip("لا يمكن التحقق")
        data = response.json()
        permissions = data.get("permissions", [])
        assert "*" in permissions or len(permissions) > 5
