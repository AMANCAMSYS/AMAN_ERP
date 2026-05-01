"""T2.6 — HMAC-signed URLs for time-limited access to private upload paths.

Signs a relative file path (under ``backend/uploads/``) plus an expiry
timestamp with HMAC-SHA256 using the application ``MASTER_SECRET``. The
resulting URL can be embedded in emails or returned in API responses without
requiring the recipient to hold a session — but only validates for the
configured TTL.

Public assets (``/uploads/logos/*``) are excluded from signing entirely:
those are branding images intentionally rendered on login pages and PDF
exports and may be cached by edge proxies.

Usage::

    from utils.signed_urls import sign_upload_path
    url = sign_upload_path("/uploads/projects/spec.pdf", ttl_seconds=600)
    # → "/uploads/projects/spec.pdf?exp=1714588300&sig=AbC..."
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time
from typing import Optional, Tuple
from urllib.parse import quote

# Public path prefixes that do NOT require a signature. Keep this list
# short; everything else must be signed.
PUBLIC_PREFIXES: tuple = ("/uploads/logos/",)

# Default lifetime for emailed / API-issued links.
DEFAULT_TTL_SECONDS = 600  # 10 minutes


def _signing_key() -> bytes:
    secret = os.getenv("MASTER_SECRET") or os.getenv("FIELD_ENCRYPTION_KEY") or ""
    if not secret:
        # Deliberately raise — refusing to mint forgeable URLs.
        raise RuntimeError(
            "MASTER_SECRET (or FIELD_ENCRYPTION_KEY) not set; "
            "cannot generate signed URLs"
        )
    return secret.encode("utf-8")


def is_public_path(file_path: str) -> bool:
    """True if ``file_path`` is allowed without a signature."""
    return any(file_path.startswith(p) for p in PUBLIC_PREFIXES)


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")


def _sign(path: str, exp: int) -> str:
    msg = f"{path}|{exp}".encode("utf-8")
    digest = hmac.new(_signing_key(), msg, hashlib.sha256).digest()
    return _b64(digest)


def sign_upload_path(file_path: str, *, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> str:
    """Return ``file_path`` with ``?exp=…&sig=…`` appended.

    Public paths are returned unchanged (no signature needed).
    """
    if is_public_path(file_path):
        return file_path
    exp = int(time.time()) + max(60, int(ttl_seconds))
    sig = _sign(file_path, exp)
    sep = "&" if "?" in file_path else "?"
    return f"{file_path}{sep}exp={exp}&sig={quote(sig)}"


def verify_signature(file_path: str, exp: Optional[str], sig: Optional[str]) -> Tuple[bool, str]:
    """Return ``(ok, reason)``. ``reason`` is empty when ok."""
    if is_public_path(file_path):
        return True, ""
    if not exp or not sig:
        return False, "missing signature"
    try:
        exp_i = int(exp)
    except (TypeError, ValueError):
        return False, "bad expiry"
    if exp_i < int(time.time()):
        return False, "link expired"
    expected = _sign(file_path, exp_i)
    if not hmac.compare_digest(expected, sig):
        return False, "bad signature"
    return True, ""
