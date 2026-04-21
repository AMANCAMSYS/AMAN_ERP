"""Carrier registry."""

from __future__ import annotations

from typing import Dict, Type

from .base import ShippingCarrier

_REGISTRY: Dict[str, Type[ShippingCarrier]] = {}


def register_carrier(carrier: str, cls: Type[ShippingCarrier]) -> None:
    _REGISTRY[(carrier or "").lower()] = cls


def get_carrier(carrier: str, **config) -> ShippingCarrier:
    key = (carrier or "").lower()
    if key not in _REGISTRY:
        raise ValueError(f"no shipping carrier registered for {carrier!r}")
    return _REGISTRY[key](**config)


def _bootstrap() -> None:
    from .aramex_adapter import AramexCarrier
    from .dhl_adapter import DHLCarrier
    register_carrier("aramex", AramexCarrier)
    register_carrier("dhl", DHLCarrier)


_bootstrap()
