"""
Field-level encryption utility for sensitive PII columns (salaries,
government IDs, bank account numbers, …).

Uses AES-256-GCM via ``cryptography`` (already in requirements) with a
tenant-derived key and envelope-encryption layout::

    | 1-byte version | 12-byte nonce | ciphertext+tag |

All output is base64-encoded (URL-safe) so it can be stored in TEXT
columns without further escaping.

Key resolution (priority order):
  1. Explicit ``key`` argument.
  2. ``FIELD_ENCRYPTION_KEY`` environment variable (base64, 32 bytes).
  3. Derived from ``MASTER_SECRET`` + tenant id via HKDF-SHA256.

If no key can be resolved, ``encrypt`` raises — we refuse to silently
store plaintext when encryption was requested.
"""

from __future__ import annotations

import base64
import os
from typing import Optional

from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

_VERSION = b"\x01"
_NONCE_LEN = 12
_KEY_LEN = 32


class FieldEncryptionError(RuntimeError):
    pass


def _b64e(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode("ascii")


def _b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s.encode("ascii"))


def _master_key() -> Optional[bytes]:
    raw = os.getenv("FIELD_ENCRYPTION_KEY")
    if raw:
        try:
            k = base64.urlsafe_b64decode(raw)
            if len(k) == _KEY_LEN:
                return k
        except Exception:
            pass
    ms = os.getenv("MASTER_SECRET")
    if ms:
        return ms.encode("utf-8").ljust(_KEY_LEN, b"\0")[:_KEY_LEN]
    return None


def _derive_tenant_key(tenant_id: Optional[str]) -> bytes:
    master = _master_key()
    if master is None:
        raise FieldEncryptionError(
            "no encryption key configured — set FIELD_ENCRYPTION_KEY or MASTER_SECRET"
        )
    salt = (tenant_id or "default").encode("utf-8").ljust(16, b"\0")[:16]
    hkdf = HKDF(algorithm=hashes.SHA256(), length=_KEY_LEN,
                salt=salt, info=b"aman-erp-field-enc")
    return hkdf.derive(master)


def encrypt(plaintext: str, *, tenant_id: Optional[str] = None,
            key: Optional[bytes] = None) -> str:
    """Encrypt a UTF-8 string. Returns a base64url token."""
    if plaintext is None:
        return ""
    k = key or _derive_tenant_key(tenant_id)
    aead = AESGCM(k)
    nonce = os.urandom(_NONCE_LEN)
    ct = aead.encrypt(nonce, plaintext.encode("utf-8"), associated_data=None)
    return _b64e(_VERSION + nonce + ct)


def decrypt(token: str, *, tenant_id: Optional[str] = None,
            key: Optional[bytes] = None) -> str:
    """Decrypt a token produced by :func:`encrypt`."""
    if not token:
        return ""
    blob = _b64d(token)
    if not blob or blob[:1] != _VERSION:
        raise FieldEncryptionError("unknown ciphertext version")
    nonce = blob[1:1 + _NONCE_LEN]
    ct = blob[1 + _NONCE_LEN:]
    k = key or _derive_tenant_key(tenant_id)
    try:
        return AESGCM(k).decrypt(nonce, ct, associated_data=None).decode("utf-8")
    except Exception as e:
        raise FieldEncryptionError(f"decryption failed: {e}") from e


def is_encrypted(value: str) -> bool:
    """Heuristic: value looks like a token produced by :func:`encrypt`."""
    if not value or len(value) < 20:
        return False
    try:
        blob = _b64d(value)
        return blob[:1] == _VERSION and len(blob) >= 1 + _NONCE_LEN + 16
    except Exception:
        return False


def fingerprint(value: str, *, tenant_id: Optional[str] = None) -> str:
    """
    Deterministic HMAC-SHA256 of a value — for indexable lookups
    (e.g. finding a row by encrypted SSN without decrypting every row).
    """
    k = _derive_tenant_key(tenant_id)
    h = hmac.HMAC(k, hashes.SHA256())
    h.update(value.encode("utf-8"))
    return _b64e(h.finalize())[:22]  # 16 bytes → 22 b64 chars
