"""Common contract for shipping carriers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional


@dataclass
class ShipmentRequest:
    reference: str
    origin: Dict[str, Any]            # {name, phone, line1, city, country, postal}
    destination: Dict[str, Any]
    weight_kg: Decimal
    service_code: Optional[str] = None
    declared_value: Optional[Decimal] = None
    currency: str = "SAR"
    cod_amount: Optional[Decimal] = None
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ShipmentResult:
    status: str                       # created | failed
    tracking_number: Optional[str] = None
    awb_label: Optional[bytes] = None     # PDF/ZPL bytes
    label_url: Optional[str] = None
    carrier_reference: Optional[str] = None
    cost: Optional[Decimal] = None
    currency: Optional[str] = None
    gateway_response: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None


@dataclass
class TrackingEvent:
    code: str
    description: str
    location: Optional[str] = None
    timestamp: Optional[datetime] = None


class ShippingCarrier(ABC):
    carrier: str = ""

    @abstractmethod
    def create_shipment(self, request: ShipmentRequest) -> ShipmentResult:
        """Book a shipment and return tracking + label."""

    @abstractmethod
    def track(self, tracking_number: str) -> List[TrackingEvent]:
        """Return timeline of events for a tracking number."""

    def cancel(self, tracking_number: str) -> bool:
        return False

    def quote(self, request: ShipmentRequest) -> Optional[Decimal]:
        """Optional rate quote; return None if unsupported."""
        return None
