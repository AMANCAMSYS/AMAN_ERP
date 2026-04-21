"""Taqnyat SMS adapter (Saudi Arabia)."""

from __future__ import annotations

import logging
from typing import Optional

import requests

from .base import SendResult, SMSGateway
from .twilio_adapter import _segments

logger = logging.getLogger(__name__)


class TaqnyatGateway(SMSGateway):
    provider = "taqnyat"

    def __init__(self, bearer_token: str, sender: Optional[str] = None,
                 api_base: str = "https://api.taqnyat.sa",
                 timeout: int = 20):
        self.bearer_token = bearer_token
        self.sender = sender
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout

    def send(self, to, message, sender=None, metadata=None) -> SendResult:
        recipient = to.lstrip("+")
        payload = {
            "recipients": [recipient],
            "body": message,
            "sender": sender or self.sender or "Aman",
        }
        try:
            r = requests.post(
                f"{self.api_base}/v1/messages",
                json=payload,
                headers={"Authorization": f"Bearer {self.bearer_token}",
                         "Content-Type": "application/json"},
                timeout=self.timeout,
            )
            body = r.json() if r.content else {}
        except requests.RequestException as e:
            return SendResult(status="failed", error_message=str(e))
        if r.status_code >= 400 or body.get("statusCode", 200) >= 400:
            return SendResult(status="failed", gateway_response=body,
                              error_message=body.get("message"))
        return SendResult(
            status="queued",
            message_id=str(body.get("messageId") or body.get("id") or ""),
            segments=_segments(message),
            gateway_response=body,
        )

    def get_balance(self) -> Optional[float]:
        try:
            r = requests.get(
                f"{self.api_base}/v1/account/balance",
                headers={"Authorization": f"Bearer {self.bearer_token}"},
                timeout=self.timeout,
            )
            if r.status_code < 400:
                return float((r.json() or {}).get("balance") or 0)
        except Exception:
            pass
        return None
