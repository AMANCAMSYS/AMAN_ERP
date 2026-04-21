"""Common contract for SMS gateway adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class SendResult:
    status: str                      # queued | sent | delivered | failed
    message_id: Optional[str] = None
    segments: int = 1                # SMS segments consumed (160-char buckets)
    cost: Optional[float] = None
    gateway_response: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None


class SMSGateway(ABC):
    """Uniform contract every SMS adapter must implement."""

    provider: str = ""

    @abstractmethod
    def send(
        self,
        to: str,
        message: str,
        sender: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SendResult:
        """Send an SMS. ``to`` must be E.164 (e.g. +9665…)."""

    def get_balance(self) -> Optional[float]:
        """Optional: account balance in provider's currency. None if unsupported."""
        return None
