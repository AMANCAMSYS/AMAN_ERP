"""
TASK-030 — Auth cookie helpers (HttpOnly refresh + readable CSRF token).

Design:
  * refresh_token → HttpOnly, Secure (when request came via HTTPS), SameSite=Lax,
    path=/api/auth. Never accessible to JS → mitigates XSS token theft.
  * csrf_token    → NOT HttpOnly (JS must read it to echo in a header),
    Secure (when request came via HTTPS), SameSite=Lax, path=/. Double-submit
    pattern: attacker on a different origin cannot read the cookie nor
    set the custom header, so CSRF is blocked.

Cookies are set IN ADDITION to returning tokens in the JSON body to keep
older clients (mobile app) working until they migrate. The `/auth/refresh`
route already prefers the cookie when present (see routers/auth.py).

FIX: The `Secure` flag is now determined from the actual request protocol
(checking X-Forwarded-Proto set by Nginx/reverse proxy) instead of only
relying on APP_ENV. This prevents cookies from being silently discarded
when a production server is accessed over HTTP or behind a proxy that
terminates HTTPS externally (e.g., Cloudflare Flexible SSL).
"""

from __future__ import annotations

import secrets
from typing import Optional

from fastapi import Request, Response

from config import settings


def _is_secure_request(request: Optional[Request] = None) -> bool:
    """Determine if the Secure flag should be set on cookies.

    Priority:
    1. X-Forwarded-Proto header (set by Nginx / load balancers)
    2. Request URL scheme
    3. Fallback: APP_ENV-based check (staging/production → True)

    This ensures cookies work correctly whether the server is:
    - Behind HTTPS-terminating proxy (X-Forwarded-Proto: https)
    - Directly serving HTTPS
    - Serving HTTP in production (Secure=False so cookies are not discarded)
    """
    if request:
        forwarded_proto = (request.headers.get("x-forwarded-proto") or "").lower()
        if forwarded_proto == "https":
            return True
        if hasattr(request, "url") and request.url.scheme == "https":
            return True
        # We have a real request and it's clearly HTTP — don't set Secure.
        return False
    # No request available — conservative fallback based on APP_ENV.
    return (settings.APP_ENV or "development").lower() in ("staging", "production")


def generate_csrf_token() -> str:
    # 32-byte URL-safe string. Not a JWT — just an opaque random value echoed
    # from cookie → header (double-submit).
    return secrets.token_urlsafe(32)


def set_refresh_cookie(
    response: Response,
    refresh_token: str,
    request: Optional[Request] = None,
) -> None:
    max_age = getattr(settings, "REFRESH_TOKEN_EXPIRE_DAYS", 7) * 86400
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=max_age,
        httponly=True,
        secure=_is_secure_request(request),
        samesite=settings.COOKIE_SAMESITE,
        path="/api/auth",
    )


def set_csrf_cookie(
    response: Response,
    csrf_token: Optional[str] = None,
    request: Optional[Request] = None,
) -> str:
    """Set (or rotate) the CSRF cookie. Returns the token value."""
    token = csrf_token or generate_csrf_token()
    # Match refresh-cookie lifetime so they rotate together on refresh.
    max_age = getattr(settings, "REFRESH_TOKEN_EXPIRE_DAYS", 7) * 86400
    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,
        value=token,
        max_age=max_age,
        httponly=False,  # JS must read this
        secure=_is_secure_request(request),
        samesite=settings.COOKIE_SAMESITE,
        path="/",
    )
    return token


def set_auth_cookies(
    response: Response,
    refresh_token: str,
    request: Optional[Request] = None,
) -> str:
    """Convenience wrapper — sets both cookies, returns the CSRF token value."""
    set_refresh_cookie(response, refresh_token, request)
    return set_csrf_cookie(response, request=request)


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(settings.REFRESH_COOKIE_NAME, path="/api/auth")
    response.delete_cookie(settings.CSRF_COOKIE_NAME, path="/")
