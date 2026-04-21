"""Provider-name → gateway-class registry."""

from __future__ import annotations

from typing import Dict, Type

from .base import PaymentGateway

_REGISTRY: Dict[str, Type[PaymentGateway]] = {}


def register_gateway(provider: str, cls: Type[PaymentGateway]) -> None:
    _REGISTRY[(provider or "").lower()] = cls


def get_gateway(provider: str, **config) -> PaymentGateway:
    key = (provider or "").lower()
    if key not in _REGISTRY:
        raise ValueError(f"no payment gateway registered for provider {provider!r}")
    return _REGISTRY[key](**config)


# Register built-in adapters lazily to avoid import cycles.
def _bootstrap() -> None:
    from .stripe_adapter import StripeGateway
    from .tap_adapter import TapGateway
    from .paytabs_adapter import PayTabsGateway
    register_gateway("stripe", StripeGateway)
    register_gateway("tap", TapGateway)
    register_gateway("paytabs", PayTabsGateway)


_bootstrap()
