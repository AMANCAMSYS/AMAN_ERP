"""
Payment gateway integrations.

Provides a common `PaymentGateway` protocol and adapters for:
  * Stripe       — global card processing
  * Tap          — Gulf/MENA (KSA, UAE, KW, BH, OM)
  * PayTabs      — Saudi + MENA

Each adapter exposes:
  * create_charge(amount, currency, source, metadata) → ChargeResult
  * verify_webhook(headers, raw_body) → WebhookEvent | None
  * refund(charge_id, amount=None, reason=None) → ChargeResult

Config is passed at instantiation time (per-tenant) so one backend process
can serve multiple companies with different gateway accounts.
"""

from __future__ import annotations

from .base import PaymentGateway, ChargeResult, WebhookEvent
from .registry import get_gateway, register_gateway
from .stripe_adapter import StripeGateway
from .tap_adapter import TapGateway
from .paytabs_adapter import PayTabsGateway

__all__ = [
    "PaymentGateway",
    "ChargeResult",
    "WebhookEvent",
    "get_gateway",
    "register_gateway",
    "StripeGateway",
    "TapGateway",
    "PayTabsGateway",
]
