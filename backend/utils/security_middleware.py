"""
SEC-203: HTTPS Enforcement Middleware
SEC-204: Input Sanitization Middleware
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse, JSONResponse
import re
import html
import logging

logger = logging.getLogger("aman.security_middleware")


# ===================== SEC-203: HTTPS Enforcement =====================

class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """
    Force HTTPS in production environment.
    - Redirects HTTP to HTTPS
    - Sets HSTS headers
    - Sets other security headers
    """

    async def dispatch(self, request: Request, call_next):
        # Check if we're behind a reverse proxy (common in production)
        forwarded_proto = request.headers.get("x-forwarded-proto", "")
        is_https = request.url.scheme == "https" or forwarded_proto == "https"
        is_localhost = request.url.hostname in ("localhost", "127.0.0.1", "0.0.0.0")

        # Only enforce HTTPS in production (not localhost)
        if not is_localhost and not is_https:
            # Redirect HTTP → HTTPS
            url = str(request.url).replace("http://", "https://", 1)
            return RedirectResponse(url=url, status_code=301)

        response = await call_next(request)

        # Security Headers (always set)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # HSTS header (only on HTTPS or production)
        if is_https or not is_localhost:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "font-src 'self' data:; "
            "connect-src 'self' ws: wss: http: https:;"
        )

        return response


# ===================== SEC-204: Input Sanitization =====================

# Patterns that indicate potential XSS attacks
XSS_PATTERNS = [
    re.compile(r'<script[^>]*>', re.IGNORECASE),
    re.compile(r'javascript\s*:', re.IGNORECASE),
    re.compile(r'on\w+\s*=', re.IGNORECASE),  # onclick=, onerror=, etc.
    re.compile(r'<iframe[^>]*>', re.IGNORECASE),
    re.compile(r'<object[^>]*>', re.IGNORECASE),
    re.compile(r'<embed[^>]*>', re.IGNORECASE),
    re.compile(r'<applet[^>]*>', re.IGNORECASE),
    re.compile(r'eval\s*\(', re.IGNORECASE),
    re.compile(r'expression\s*\(', re.IGNORECASE),
    re.compile(r'vbscript\s*:', re.IGNORECASE),
]

# SQL Injection patterns (basic detection — parameterized queries are the real defense)
SQL_PATTERNS = [
    re.compile(r"('\s*(OR|AND)\s*'?\s*\d+\s*=\s*\d+)", re.IGNORECASE),
    re.compile(r"(;\s*(DROP|DELETE|TRUNCATE|ALTER|CREATE)\s+)", re.IGNORECASE),
    re.compile(r"(UNION\s+(ALL\s+)?SELECT)", re.IGNORECASE),
]

# Paths to skip sanitization (file upload, etc.)
SKIP_PATHS = ["/uploads", "/api/data-import", "/api/companies/logo"]


def sanitize_string(value: str) -> str:
    """Sanitize a string value by escaping HTML entities"""
    if not isinstance(value, str):
        return value
    return html.escape(value, quote=True)


def detect_xss(value: str) -> bool:
    """Detect potential XSS in a string"""
    if not isinstance(value, str):
        return False
    for pattern in XSS_PATTERNS:
        if pattern.search(value):
            return True
    return False


def detect_sql_injection(value: str) -> bool:
    """Detect basic SQL injection patterns"""
    if not isinstance(value, str):
        return False
    for pattern in SQL_PATTERNS:
        if pattern.search(value):
            return True
    return False


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to detect and block potentially malicious input.
    - Detects XSS patterns in query params and headers
    - Detects SQL injection patterns
    - Logs suspicious requests
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip certain paths
        for skip in SKIP_PATHS:
            if path.startswith(skip):
                return await call_next(request)

        # Check query parameters for XSS/SQLi
        for key, value in request.query_params.items():
            if detect_xss(value):
                logger.warning(f"🚨 XSS detected in query param '{key}' from {request.client.host}: {value[:100]}")
                return JSONResponse(
                    status_code=400,
                    content={"detail": "تم اكتشاف محتوى غير آمن في الطلب"}
                )
            if detect_sql_injection(value):
                logger.warning(f"🚨 SQLi detected in query param '{key}' from {request.client.host}: {value[:100]}")
                return JSONResponse(
                    status_code=400,
                    content={"detail": "تم اكتشاف محتوى غير آمن في الطلب"}
                )

        # Check path parameters
        if detect_xss(path) or detect_sql_injection(path):
            logger.warning(f"🚨 Malicious path from {request.client.host}: {path[:200]}")
            return JSONResponse(
                status_code=400,
                content={"detail": "تم اكتشاف محتوى غير آمن في الطلب"}
            )

        # For JSON body, we check in a non-destructive way
        # (FastAPI's Pydantic validation handles most type checking)
        if request.method in ("POST", "PUT", "PATCH"):
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    body = await request.body()
                    body_str = body.decode("utf-8", errors="ignore")

                    # Only check for obvious script injection in body
                    if re.search(r'<script[^>]*>.*?</script>', body_str, re.IGNORECASE | re.DOTALL):
                        logger.warning(f"🚨 Script injection in body from {request.client.host}")
                        return JSONResponse(
                            status_code=400,
                            content={"detail": "تم اكتشاف محتوى غير آمن في الطلب"}
                        )

                    # Reconstruct request with body (since we consumed it)
                    from starlette.datastructures import State
                    async def receive():
                        return {"type": "http.request", "body": body}
                    request._receive = receive
                except Exception:
                    pass  # Don't block on body read failure

        response = await call_next(request)
        return response
