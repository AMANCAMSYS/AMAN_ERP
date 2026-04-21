"""
PayTabs adapter (Saudi Arabia + MENA).

PayTabs PayPage v2 — `POST https://secure.paytabs.sa/payment/request` to
create a hosted-checkout redirect. Webhooks (IPN) arrive as form-encoded
POSTs with a `signature` field equal to HMAC-SHA256 of the body fields.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from decimal import Decimal
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

from .base import ChargeResult, PaymentGateway, WebhookEvent

logger = logging.getLogger(__name__)


class PayTabsGateway(PaymentGateway):
    provider = "paytabs"

    def __init__(self, profile_id: str, server_key: str,
                 webhook_secret: Optional[str] = None,
                 api_base: str = "https://secure.paytabs.sa",
                 timeout: int = 30):
        self.profile_id = profile_id
        self.server_key = server_key
        self.webhook_secret = webhook_secret
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout

    def create_charge(self, amount, currency, source, metadata=None) -> ChargeResult:
        payload: Dict[str, Any] = {
            "profile_id": self.profile_id,
            "tran_type": "sale",
            "tran_class": "ecom",
            "cart_id": (metadata or {}).get("cart_id") or source.get("cart_id") or "CART",
            "cart_description": (metadata or {}).get("description") or "Aman ERP payment",
            "cart_currency": (currency or "SAR").upper(),
            "cart_amount": float(Decimal(str(amount))),
            "customer_details": source.get("customer") or {},
            "return": source.get("redirect_url") or "",
            "callback": source.get("callback_url") or "",
        }
        try:
            r = requests.post(self.api_base + "/payment/request",
                              json=payload,
                              headers={"Authorization": self.server_key,
                                       "Content-Type": "application/json"},
                              timeout=self.timeout)
            body = r.json()
        except requests.RequestException as e:
            return ChargeResult(status="failed", error_message=str(e))
        if r.status_code >= 400 or not body.get("tran_ref"):
            return ChargeResult(status="failed", gateway_response=body,
                                error_message=body.get("message") or "paytabs_error")
        return ChargeResult(
            status="pending",   # user must complete the hosted page first
            charge_id=body.get("tran_ref"),
            amount=Decimal(str(amount)),
            currency=(currency or "SAR").upper(),
            gateway_response=body,
        )

    def verify_webhook(self, headers, raw_body) -> Optional[WebhookEvent]:
        if not self.webhook_secret:
            return None
        try:
            payload = json.loads(raw_body)
        except Exception:
            return None
        received = payload.get("signature") or headers.get("signature") or ""
        # Build the signed string from the body minus the signature itself,
        # sorted by key (PayTabs IPN convention).
        items = [(k, v) for k, v in payload.items() if k != "signature"]
        items.sort(key=lambda kv: kv[0])
        message = urlencode(items, doseq=True).encode("utf-8")
        expected = hmac.new(self.webhook_secret.encode("utf-8"),
                            message, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, received):
            return None
        status = (payload.get("payment_result") or {}).get("response_status") or payload.get("response_status")
        status_map = {"A": "charge.succeeded", "H": "charge.authorised",
                      "P": "charge.pending", "D": "charge.failed",
                      "V": "charge.cancelled", "E": "charge.failed"}
        return WebhookEvent(
            event_type=status_map.get(status, "charge.updated"),
            charge_id=payload.get("tran_ref"),
            amount=Decimal(str(payload.get("cart_amount") or "0")),
            currency=(payload.get("cart_currency") or "").upper() or None,
            payload=payload,
        )

    def refund(self, charge_id, amount=None, reason=None) -> ChargeResult:
        payload = {
            "profile_id": self.profile_id,
            "tran_type": "refund",
            "tran_class": "ecom",
            "cart_id": charge_id,
            "cart_currency": "SAR",
            "cart_amount": float(Decimal(amount)) if amount is not None else 0,
            "tran_ref": charge_id,
            "cart_description": reason or "refund",
        }
        try:
            r = requests.post(self.api_base + "/payment/request",
                              json=payload,
                              headers={"Authorization": self.server_key,
                                       "Content-Type": "application/json"},
                              timeout=self.timeout)
            body = r.json()
        except requests.RequestException as e:
            return ChargeResult(status="failed", error_message=str(e))
        if r.status_code >= 400:
            return ChargeResult(status="failed", gateway_response=body,
                                error_message=body.get("message"))
        return ChargeResult(status="refunded", charge_id=body.get("tran_ref"),
                            gateway_response=body)
