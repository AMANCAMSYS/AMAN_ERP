"""
TASK-030 — CSRF middleware (double-submit cookie pattern).

Enforcement modes (config: settings.CSRF_ENFORCEMENT):
  * off         → middleware is a no-op
  * permissive  → logs mismatches but does NOT reject (default during rollout)
  * strict      → rejects mutating requests that fail the check

Checks only run on mutating methods (POST/PUT/PATCH/DELETE) for requests that
look like browser-originated (carry a cookie header). API clients using pure
Bearer auth (mobile app, server-to-server) do not send cookies and are not
subject to the check — they rely on Bearer token secrecy.

Exempt paths: login/refresh/CSRF-bootstrap, so the client can first obtain
the token. SSO callbacks also exempt (they're OAuth/SAML redirect targets
and use their own state/nonce mechanisms).
"""

from __future__ import annotations

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from config import settings

logger = logging.getLogger(__name__)

MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

EXEMPT_PREFIXES = (
    "/api/auth/login",
    "/api/auth/refresh",
    "/api/auth/forgot-password",
    "/api/auth/reset-password",
    "/api/auth/verify-2fa",
    "/api/auth/csrf",
    "/api/auth/register-company",
    "/api/auth/sso",
    "/api/sso",
    "/api/external/",  # external integrations use API keys, not cookies
    "/api/mobile/",    # mobile clients use Bearer only
)


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        mode = (settings.CSRF_ENFORCEMENT or "permissive").lower()
        if mode == "off":
            return await call_next(request)

        if request.method not in MUTATING_METHODS:
            return await call_next(request)

        path = request.url.path or ""
        if any(path.startswith(p) for p in EXEMPT_PREFIXES):
            return await call_next(request)

        # Only enforce on cookie-bearing requests. A pure Bearer client
        # (mobile app, curl with -H Authorization) sends no cookie and is
        # exempt — Bearer tokens are not auto-attached by browsers so the
        # CSRF attack surface doesn't apply.
        cookie_header = request.headers.get("cookie", "")
        if not cookie_header:
            return await call_next(request)

        cookie_token = request.cookies.get(settings.CSRF_COOKIE_NAME)
        header_token = request.headers.get(settings.CSRF_HEADER_NAME)

        mismatch = (
            not cookie_token
            or not header_token
            or not _safe_equal(cookie_token, header_token)
        )

        if mismatch:
            logger.warning(
                "CSRF %s: path=%s cookie=%s header=%s",
                mode,
                path,
                bool(cookie_token),
                bool(header_token),
            )
            if mode == "strict":
                return JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF token missing or invalid"},
                )

        return await call_next(request)


def _safe_equal(a: str, b: str) -> bool:
    """Constant-time comparison."""
    if len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    return result == 0
