"""Shipping carrier framework — Aramex / DHL / FedEx."""

from .base import ShippingCarrier, ShipmentRequest, ShipmentResult, TrackingEvent
from .registry import get_carrier, register_carrier
from .aramex_adapter import AramexCarrier
from .dhl_adapter import DHLCarrier

__all__ = [
    "ShippingCarrier", "ShipmentRequest", "ShipmentResult", "TrackingEvent",
    "get_carrier", "register_carrier",
    "AramexCarrier", "DHLCarrier",
]
