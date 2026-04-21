"""Provider-name → SMS-gateway-class registry."""

from __future__ import annotations

from typing import Dict, Type

from .base import SMSGateway

_REGISTRY: Dict[str, Type[SMSGateway]] = {}


def register_gateway(provider: str, cls: Type[SMSGateway]) -> None:
    _REGISTRY[(provider or "").lower()] = cls


def get_gateway(provider: str, **config) -> SMSGateway:
    key = (provider or "").lower()
    if key not in _REGISTRY:
        raise ValueError(f"no SMS gateway registered for provider {provider!r}")
    return _REGISTRY[key](**config)


def _bootstrap() -> None:
    from .twilio_adapter import TwilioGateway
    from .unifonic_adapter import UnifonicGateway
    from .taqnyat_adapter import TaqnyatGateway
    register_gateway("twilio", TwilioGateway)
    register_gateway("unifonic", UnifonicGateway)
    register_gateway("taqnyat", TaqnyatGateway)


_bootstrap()
