"""
AMAN ERP - Webhook Utilities
API-002: Send webhooks with retry logic and logging.
"""

import base64
import hashlib
import hmac
import ipaddress
import json
import logging
import socket
import threading
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

import requests
from cryptography.fernet import Fernet
from sqlalchemy import text

logger = logging.getLogger(__name__)


def _get_fernet() -> Fernet:
    """Derive a Fernet key from SECRET_KEY for webhook secret encryption."""
    from config import settings
    key = base64.urlsafe_b64encode(
        hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    )
    return Fernet(key)


def encrypt_webhook_secret(plaintext: str) -> str:
    """Encrypt a webhook secret for storage."""
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_webhook_secret(ciphertext: str) -> str:
    """Decrypt a stored webhook secret."""
    return _get_fernet().decrypt(ciphertext.encode()).decode()

# ── Private/reserved IP ranges blocked for SSRF protection ───────────────────
_BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]


def validate_webhook_url(url: str) -> None:
    """
    Validate a webhook URL is safe from SSRF attacks.

    Checks:
    - Only http/https schemes allowed
    - Hostname resolves to a public (non-private/reserved) IP
    - Blocks loopback, link-local, and private ranges

    Raises ValueError if the URL is unsafe.
    """
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise ValueError("Only http and https schemes are allowed")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL must include a hostname")

    try:
        addr_infos = socket.getaddrinfo(hostname, parsed.port or 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        raise ValueError("Could not resolve hostname")

    for family, _, _, _, sockaddr in addr_infos:
        ip = ipaddress.ip_address(sockaddr[0])
        for network in _BLOCKED_NETWORKS:
            if ip in network:
                raise ValueError("URL resolves to a blocked IP range")


# Supported events
WEBHOOK_EVENTS = [
    "invoice.created", "invoice.paid", "invoice.cancelled",
    "order.created", "order.confirmed", "order.delivered",
    "payment.received", "payment.refunded",
    "inventory.low_stock", "inventory.adjustment",
    "purchase.created", "purchase.approved",
    "employee.leave_request", "employee.attendance",
    "ticket.created", "ticket.resolved",
    "opportunity.stage_changed", "opportunity.won", "opportunity.lost",
]


def _compute_signature(payload: str, secret: str) -> str:
    """Compute HMAC-SHA256 signature for payload verification."""
    return hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def _send_single_webhook(webhook_id: int, url: str, secret: Optional[str],
                          event: str, payload: dict, timeout: int,
                          retry_count: int, db_factory):
    """Send webhook with retry logic (runs in background thread)."""
    # Defense-in-depth SSRF check before dispatch (DNS rebinding protection)
    try:
        validate_webhook_url(url)
    except ValueError as e:
        logger.warning("Webhook %d blocked by SSRF check: %s - %s", webhook_id, url, e)
        return

    payload_json = json.dumps(payload, default=str, ensure_ascii=False)
    
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "X-Webhook-Event": event,
        "X-Webhook-Timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    if secret:
        try:
            decrypted_secret = decrypt_webhook_secret(secret)
        except Exception:
            logger.warning("Webhook %d: failed to decrypt secret, using raw", webhook_id)
            decrypted_secret = secret
        headers["X-Webhook-Signature"] = _compute_signature(payload_json, decrypted_secret)
    
    for attempt in range(1, retry_count + 1):
        response_status = None
        response_body = None
        error_msg = None
        success = False
        
        try:
            resp = requests.post(url, data=payload_json, headers=headers, timeout=timeout)
            response_status = resp.status_code
            response_body = resp.text[:2000]  # Limit stored body size
            success = 200 <= resp.status_code < 300
        except requests.Timeout:
            error_msg = f"Timeout after {timeout}s"
        except requests.ConnectionError as e:
            error_msg = f"Connection error: {str(e)[:200]}"
        except Exception as e:
            error_msg = f"Error: {str(e)[:200]}"
        
        # Log this attempt
        try:
            db = db_factory()
            db.execute(text("""
                INSERT INTO webhook_logs (webhook_id, event, payload, response_status, response_body, success, attempt, error_message)
                VALUES (:wid, :event, :payload, :status, :body, :success, :attempt, :error)
            """), {
                "wid": webhook_id,
                "event": event,
                "payload": payload_json,
                "status": response_status,
                "body": response_body,
                "success": success,
                "attempt": attempt,
                "error": error_msg
            })
            db.commit()
            db.close()
        except Exception as log_err:
            logger.error(f"Failed to log webhook attempt: {log_err}")
        
        if success:
            logger.info(f"✅ Webhook #{webhook_id} sent: {event} → {url} (attempt {attempt})")
            return
        
        if attempt < retry_count:
            import time
            wait = 2 ** attempt  # Exponential backoff: 2, 4, 8 seconds
            logger.warning(f"⚠️ Webhook #{webhook_id} failed (attempt {attempt}), retrying in {wait}s...")
            time.sleep(wait)
    
    logger.error(f"❌ Webhook #{webhook_id} failed after {retry_count} attempts: {event} → {url}")


def fire_webhook_event(db, event: str, payload: dict, db_factory=None):
    """
    Fire a webhook event to all subscribed active webhooks.
    Runs in background threads so it doesn't block the request.
    
    Usage:
        fire_webhook_event(db, "invoice.created", {"invoice_id": 123, "total": 5000})
    """
    if not db_factory:
        logger.warning("No db_factory provided for webhook logging")
        return
    
    try:
        webhooks = db.execute(text("""
            SELECT id, url, secret, retry_count, timeout_seconds 
            FROM webhooks 
            WHERE is_active = TRUE AND events @> :event::jsonb
        """), {"event": json.dumps([event])}).fetchall()
        
        for wh in webhooks:
            thread = threading.Thread(
                target=_send_single_webhook,
                args=(wh.id, wh.url, wh.secret, event, payload,
                      wh.timeout_seconds or 10, wh.retry_count or 3, db_factory),
                daemon=True
            )
            thread.start()
    except Exception as e:
        logger.error(f"Error firing webhook event {event}: {e}")
