"""T2.5 — Encrypted reads/writes for sensitive ``company_settings`` rows.

Wraps :mod:`utils.field_encryption` (AES-256-GCM, tenant-derived key) to give
routers a single, pluggable surface for storing/retrieving secrets that must
never sit in the database as plaintext:

* ZATCA signing private key (``zatca_private_key``)
* SMTP password (``smtp_password``)
* SMS gateway API key (``sms_api_key``)

The companion CLI ``scripts/encrypt_existing_secrets.py`` walks each tenant
database once and rewrites legacy plaintext rows in-place.

Design notes:
  * Reads tolerate **legacy plaintext** values (decoded via
    :func:`field_encryption.is_encrypted`). This guarantees zero-downtime
    rollout: encrypt-on-write goes live first, the migration script runs
    at any later point, and existing values keep working until then.
  * Writes always emit ciphertext. There is no "off" switch — if no key is
    configured the underlying ``encrypt`` call raises and the route fails
    loudly rather than silently storing plaintext.
  * Tenant-id used for HKDF salt is the ``company_id`` string the caller
    already passes to :func:`database.get_db_connection`; this binds each
    secret to its tenant and means a leaked DB dump cannot be decrypted
    by another tenant's key derivation.

Key rotation playbook (operator):
  1. Generate a new ``FIELD_ENCRYPTION_KEY`` and set it as the **secondary**
     env var (``FIELD_ENCRYPTION_KEY_NEXT`` — future work).
  2. Run ``scripts/encrypt_existing_secrets.py --rekey`` (future work) to
     decrypt with the old key and re-encrypt with the new one.
  3. Promote ``FIELD_ENCRYPTION_KEY_NEXT`` → ``FIELD_ENCRYPTION_KEY`` and
     restart workers.

Only step (1) and the basic migration are wired today; rekey is tracked in
the audit TODO under T2.5 follow-ups.
"""

from __future__ import annotations

from typing import Iterable, Optional, Set

from sqlalchemy import text

from utils.field_encryption import (
    FieldEncryptionError,
    decrypt as _decrypt,
    encrypt as _encrypt,
    is_encrypted,
)

# Keys that must never be stored as plaintext.
ENCRYPTED_SETTING_KEYS: Set[str] = {
    "zatca_private_key",
    "smtp_password",
    "sms_api_key",
}


def is_secret_key(setting_key: str) -> bool:
    return setting_key in ENCRYPTED_SETTING_KEYS


def encrypt_value(value: str, *, tenant_id: str) -> str:
    """Encrypt ``value`` (raises if no key configured)."""
    if value is None or value == "":
        return value
    return _encrypt(value, tenant_id=tenant_id)


def decrypt_value(value: Optional[str], *, tenant_id: str) -> Optional[str]:
    """Decrypt ``value`` if it looks like ciphertext, else return as-is.

    Tolerates legacy plaintext rows during the migration window.
    """
    if value is None or value == "":
        return value
    if not is_encrypted(value):
        # Legacy plaintext — return unchanged. Migration script will fix it.
        return value
    try:
        return _decrypt(value, tenant_id=tenant_id)
    except FieldEncryptionError:
        # Corrupt or wrong-key ciphertext — surface as None rather than
        # leaking a base64 token to the caller.
        return None


def get_secret_setting(db, setting_key: str, *, tenant_id: str) -> Optional[str]:
    """Read a single sensitive setting and decrypt if needed."""
    row = db.execute(
        text("SELECT setting_value FROM company_settings WHERE setting_key = :k"),
        {"k": setting_key},
    ).fetchone()
    if not row:
        return None
    return decrypt_value(row[0], tenant_id=tenant_id)


def set_secret_setting(db, setting_key: str, value: Optional[str], *, tenant_id: str) -> None:
    """Upsert a single sensitive setting, encrypting on the way in."""
    enc = encrypt_value(value, tenant_id=tenant_id) if value else value
    db.execute(
        text(
            """
            INSERT INTO company_settings (setting_key, setting_value)
            VALUES (:k, :v)
            ON CONFLICT (setting_key) DO UPDATE SET setting_value = :v
            """
        ),
        {"k": setting_key, "v": enc},
    )


def decrypt_settings_map(
    settings: dict, *, tenant_id: str, only_keys: Optional[Iterable[str]] = None
) -> dict:
    """Return a copy of ``settings`` with sensitive values decrypted."""
    out = dict(settings)
    target = set(only_keys) if only_keys else ENCRYPTED_SETTING_KEYS
    for k in target:
        if k in out and out[k]:
            out[k] = decrypt_value(out[k], tenant_id=tenant_id)
    return out


def encrypt_existing_secrets(db, *, tenant_id: str) -> dict:
    """One-shot migration: encrypt any plaintext rows for the encrypted keys.

    Returns a per-key summary ``{key: action}`` where action is one of
    ``"encrypted" | "already_encrypted" | "missing" | "empty"``.
    """
    summary: dict = {}
    for k in ENCRYPTED_SETTING_KEYS:
        row = db.execute(
            text("SELECT setting_value FROM company_settings WHERE setting_key = :k"),
            {"k": k},
        ).fetchone()
        if not row:
            summary[k] = "missing"
            continue
        v = row[0]
        if v is None or v == "":
            summary[k] = "empty"
            continue
        if is_encrypted(v):
            summary[k] = "already_encrypted"
            continue
        enc = _encrypt(v, tenant_id=tenant_id)
        db.execute(
            text("UPDATE company_settings SET setting_value = :v WHERE setting_key = :k"),
            {"k": k, "v": enc},
        )
        summary[k] = "encrypted"
    return summary
