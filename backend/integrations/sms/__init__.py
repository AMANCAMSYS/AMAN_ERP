"""SMS gateway framework — Twilio / Unifonic / Taqnyat (MENA)."""

from .base import SMSGateway, SendResult
from .registry import get_gateway, register_gateway
from .twilio_adapter import TwilioGateway
from .unifonic_adapter import UnifonicGateway
from .taqnyat_adapter import TaqnyatGateway

__all__ = [
    "SMSGateway", "SendResult",
    "get_gateway", "register_gateway",
    "TwilioGateway", "UnifonicGateway", "TaqnyatGateway",
]
