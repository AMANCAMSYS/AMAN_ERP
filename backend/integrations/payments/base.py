"""Common contract for payment gateway adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, Mapping, Optional


@dataclass
class ChargeResult:
    status: str                     # pending | authorised | captured | failed | refunded | cancelled
    charge_id: Optional[str] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    gateway_response: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None


@dataclass
class WebhookEvent:
    event_type: str                 # charge.succeeded | charge.failed | refund.processed | …
    charge_id: Optional[str] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)


class PaymentGateway(ABC):
    """Uniform contract every payment adapter must implement."""

    provider: str = ""

    @abstractmethod
    def create_charge(
        self,
        amount: Decimal,
        currency: str,
        source: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ChargeResult:
        """Create (and optionally capture) a charge.

        `source` semantics are gateway-specific (token, card, saved-card
        id, 3DS redirect result, etc.) — adapters document the exact keys.
        """

    @abstractmethod
    def verify_webhook(
        self, headers: Mapping[str, str], raw_body: bytes
    ) -> Optional[WebhookEvent]:
        """Validate signature and return a normalised event, or None if invalid."""

    def refund(
        self,
        charge_id: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None,
    ) -> ChargeResult:
        """Optional refund flow; default unsupported."""
        return ChargeResult(status="failed", error_message="refund not supported by adapter")
