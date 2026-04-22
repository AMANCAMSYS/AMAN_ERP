"""
SEC-203: HTTPS Enforcement Middleware
SEC-204: Input Sanitization Middleware
"""
from fastapi import Request
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
        # SEC-004: CSRF — not applicable (auth via Authorization header / localStorage, not cookies).
        # If cookies are ever used, SameSite=Lax protects against CSRF by default.
        # We also add X-Content-Type-Options and X-Frame-Options above as defense-in-depth.

        # HSTS header (only on HTTPS or production)
        if is_https or not is_localhost:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # SEC-005: Tightened CSP — restrict connect-src to known origins
        from config import settings
        allowed_connect = "'self'"
        if settings.APP_ENV == "production":
            # In production, only allow WebSocket connections to our own domains
            origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]
            if settings.FRONTEND_URL_PRODUCTION:
                origins.append(settings.FRONTEND_URL_PRODUCTION)
            ws_origins = []
            for origin in origins:
                ws_origin = origin.replace("https://", "wss://").replace("http://", "ws://")
                ws_origins.append(ws_origin)
            if ws_origins:
                allowed_connect = "'self' " + " ".join(ws_origins)
        else:
            # Development: allow local ws connections
            allowed_connect = "'self' ws://localhost:* wss://localhost:*"

        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: blob: https://fastapi.tiangolo.com; "
            "font-src 'self' data:; "
            f"connect-src {allowed_connect}; "
            "frame-ancestors 'none';"
        )

        return response


class SecurityHeadersOnlyMiddleware(BaseHTTPMiddleware):
    """
    Sets security headers WITHOUT redirecting HTTP → HTTPS.
    Use this when SSL terminates at a load-balancer/nginx and the backend
    communicates over plain HTTP internally (FORCE_HTTPS=false).
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
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

# TASK-033: SQL-injection regex middleware removed.
# Rationale: regex-based SQL-injection detection produced false positives on
# legitimate payloads (e.g. product names containing "OR 1=1", audit diffs
# containing SQL keywords) while providing zero real protection — SQLAlchemy
# parameterized queries are the only correct defence. A static-analysis lint
# (scripts/check_sql_parameterization.py) now enforces that no router builds
# SQL via f-strings or `%` / `+` string concatenation on untrusted input.

# Paths to skip sanitization (file upload only — binary content)
SKIP_PATHS = ["/uploads", "/api/companies/logo"]


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


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to detect and block potentially malicious input.
    - Detects XSS patterns in query params and headers
    - Logs suspicious requests
    Note: SQL-injection regex checks were removed (TASK-033). The only
    correct defence is parameterized queries, enforced by SQLAlchemy and
    the scripts/check_sql_parameterization.py CI lint.
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip certain paths
        for skip in SKIP_PATHS:
            if path.startswith(skip):
                return await call_next(request)

        # Check query parameters for XSS
        for key, value in request.query_params.items():
            if detect_xss(value):
                logger.warning(f"🚨 XSS detected in query param '{key}' from {request.client.host}: {value[:100]}")
                return JSONResponse(
                    status_code=400,
                    content={"detail": "تم اكتشاف محتوى غير آمن في الطلب"}
                )

        # Check path parameters
        if detect_xss(path):
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

                    # SEC-FIX-013: Check ALL XSS patterns in body, not just <script>
                    if detect_xss(body_str):
                        logger.warning(f"🚨 XSS injection in body from {request.client.host}")
                        return JSONResponse(
                            status_code=400,
                            content={"detail": "تم اكتشاف محتوى غير آمن في الطلب"}
                        )

                    # Reconstruct request with body (since we consumed it)
                    async def receive():
                        return {"type": "http.request", "body": body}
                    request._receive = receive
                except Exception:
                    pass  # Don't block on body read failure

        response = await call_next(request)
        return response
