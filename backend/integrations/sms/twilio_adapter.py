"""Twilio SMS adapter (global)."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import requests

from .base import SendResult, SMSGateway

logger = logging.getLogger(__name__)


def _segments(text: str) -> int:
    """Approximate SMS segment count (GSM-7 vs UCS-2)."""
    is_unicode = any(ord(c) > 127 for c in text)
    if is_unicode:
        per = 70 if len(text) <= 70 else 67
    else:
        per = 160 if len(text) <= 160 else 153
    return max(1, -(-len(text) // per))


class TwilioGateway(SMSGateway):
    provider = "twilio"

    def __init__(self, account_sid: str, auth_token: str,
                 from_number: Optional[str] = None,
                 messaging_service_sid: Optional[str] = None,
                 api_base: str = "https://api.twilio.com",
                 timeout: int = 20):
        if not (from_number or messaging_service_sid):
            raise ValueError("Twilio requires either from_number or messaging_service_sid")
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self.messaging_service_sid = messaging_service_sid
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout

    def send(self, to, message, sender=None, metadata=None) -> SendResult:
        data: Dict[str, Any] = {"To": to, "Body": message}
        if sender:
            data["From"] = sender
        elif self.from_number:
            data["From"] = self.from_number
        elif self.messaging_service_sid:
            data["MessagingServiceSid"] = self.messaging_service_sid
        try:
            r = requests.post(
                f"{self.api_base}/2010-04-01/Accounts/{self.account_sid}/Messages.json",
                data=data, auth=(self.account_sid, self.auth_token),
                timeout=self.timeout,
            )
            body = r.json()
        except requests.RequestException as e:
            return SendResult(status="failed", error_message=str(e))
        if r.status_code >= 400:
            return SendResult(status="failed", gateway_response=body,
                              error_message=body.get("message"))
        status_map = {"queued": "queued", "accepted": "queued", "sending": "queued",
                      "sent": "sent", "delivered": "delivered",
                      "failed": "failed", "undelivered": "failed"}
        return SendResult(
            status=status_map.get(body.get("status", ""), "queued"),
            message_id=body.get("sid"),
            segments=_segments(message),
            gateway_response=body,
        )
