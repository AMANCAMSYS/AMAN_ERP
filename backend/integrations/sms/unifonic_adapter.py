"""Unifonic SMS adapter (MENA)."""

from __future__ import annotations

import logging
from typing import Optional

import requests

from .base import SendResult, SMSGateway
from .twilio_adapter import _segments  # reuse segment calc

logger = logging.getLogger(__name__)


class UnifonicGateway(SMSGateway):
    provider = "unifonic"

    def __init__(self, app_sid: str, sender_id: Optional[str] = None,
                 api_base: str = "https://api.unifonic.com",
                 timeout: int = 20):
        self.app_sid = app_sid
        self.sender_id = sender_id
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout

    def send(self, to, message, sender=None, metadata=None) -> SendResult:
        # Unifonic expects local form without '+'.
        recipient = to.lstrip("+")
        payload = {
            "AppSid": self.app_sid,
            "Recipient": recipient,
            "Body": message,
            "SenderID": sender or self.sender_id or "Aman",
            "async": "true",
        }
        try:
            r = requests.post(f"{self.api_base}/rest/SMS/messages",
                              data=payload, timeout=self.timeout)
            body = r.json()
        except requests.RequestException as e:
            return SendResult(status="failed", error_message=str(e))
        if r.status_code >= 400 or not body.get("success"):
            return SendResult(status="failed", gateway_response=body,
                              error_message=body.get("errorCode") or body.get("message"))
        data = body.get("data") or {}
        return SendResult(
            status="queued",
            message_id=str(data.get("MessageID") or ""),
            segments=_segments(message),
            gateway_response=body,
        )

    def get_balance(self) -> Optional[float]:
        try:
            r = requests.post(f"{self.api_base}/rest/Accounts/getBalance",
                              data={"AppSid": self.app_sid}, timeout=self.timeout)
            body = r.json()
            if body.get("success"):
                return float((body.get("data") or {}).get("Balance") or 0)
        except Exception:
            pass
        return None
