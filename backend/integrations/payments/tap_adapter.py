"""
Tap Payments adapter (Gulf/MENA).

Tap exposes a REST API at https://api.tap.company/v2. Charges are created via
`POST /charges`. Webhooks arrive as signed JSON (HMAC-SHA256 in the
`HMAC-SIG` header computed over a set of pipe-joined fields).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from decimal import Decimal
from typing import Any, Dict, Optional

import requests

from .base import ChargeResult, PaymentGateway, WebhookEvent

logger = logging.getLogger(__name__)


class TapGateway(PaymentGateway):
    provider = "tap"

    def __init__(self, secret_key: str, webhook_secret: Optional[str] = None,
                 api_base: str = "https://api.tap.company/v2", timeout: int = 30):
        self.secret_key = secret_key
        self.webhook_secret = webhook_secret
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout

    def create_charge(self, amount, currency, source, metadata=None) -> ChargeResult:
        payload: Dict[str, Any] = {
            "amount": float(Decimal(str(amount))),
            "currency": (currency or "SAR").upper(),
            "threeDSecure": bool(source.get("threeDSecure", True)),
            "save_card": bool(source.get("save_card", False)),
            "source": {"id": source.get("token") or source.get("source_id")},
            "redirect": {"url": source.get("redirect_url", "")} if source.get("redirect_url") else {"url": ""},
            "customer": source.get("customer") or {},
            "metadata": metadata or {},
        }
        try:
            r = requests.post(self.api_base + "/charges", json=payload,
                              headers={"Authorization": f"Bearer {self.secret_key}"},
                              timeout=self.timeout)
            body = r.json()
        except requests.RequestException as e:
            return ChargeResult(status="failed", error_message=str(e))
        if r.status_code >= 400:
            return ChargeResult(status="failed", gateway_response=body,
                                error_message=(body.get("errors") or [{}])[0].get("description"))
        status_map = {
            "INITIATED": "pending", "IN_PROGRESS": "pending", "PENDING": "pending",
            "AUTHORIZED": "authorised", "CAPTURED": "captured",
            "DECLINED": "failed", "VOID": "cancelled", "FAILED": "failed",
        }
        tap_status = (body.get("status") or "").upper()
        return ChargeResult(
            status=status_map.get(tap_status, tap_status.lower() or "pending"),
            charge_id=body.get("id"),
            amount=Decimal(str(body.get("amount", amount))),
            currency=(body.get("currency") or currency).upper(),
            gateway_response=body,
        )

    def verify_webhook(self, headers, raw_body) -> Optional[WebhookEvent]:
        if not self.webhook_secret:
            return None
        received = headers.get("HMAC-SIG") or headers.get("hmac-sig") or ""
        try:
            payload = json.loads(raw_body)
        except Exception:
            return None
        # Tap docs: message = pipe-joined critical fields; signature = HMAC-SHA256(key, message) hex.
        fields = [str(payload.get(k, "")) for k in
                  ("id", "amount", "currency", "gateway_reference", "payment_reference",
                   "status", "created")]
        message = "|".join(fields)
        expected = hmac.new(self.webhook_secret.encode("utf-8"),
                            message.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, received):
            return None
        status_map = {"CAPTURED": "charge.succeeded", "AUTHORIZED": "charge.authorised",
                      "DECLINED": "charge.failed", "FAILED": "charge.failed",
                      "VOID": "charge.cancelled", "REFUNDED": "refund.processed"}
        return WebhookEvent(
            event_type=status_map.get((payload.get("status") or "").upper(),
                                      "charge.updated"),
            charge_id=payload.get("id"),
            amount=Decimal(str(payload.get("amount") or "0")),
            currency=(payload.get("currency") or "").upper() or None,
            payload=payload,
        )

    def refund(self, charge_id, amount=None, reason=None) -> ChargeResult:
        payload: Dict[str, Any] = {"charge_id": charge_id}
        if amount is not None:
            payload["amount"] = float(Decimal(amount))
        if reason:
            payload["reason"] = reason
        try:
            r = requests.post(self.api_base + "/refunds", json=payload,
                              headers={"Authorization": f"Bearer {self.secret_key}"},
                              timeout=self.timeout)
            body = r.json()
        except requests.RequestException as e:
            return ChargeResult(status="failed", error_message=str(e))
        if r.status_code >= 400:
            return ChargeResult(status="failed", gateway_response=body,
                                error_message=(body.get("errors") or [{}])[0].get("description"))
        return ChargeResult(status="refunded", charge_id=body.get("id"),
                            gateway_response=body)
