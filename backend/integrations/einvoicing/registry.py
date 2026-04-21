"""Jurisdiction → adapter lookup."""

from __future__ import annotations

from typing import Dict, Type

from .base import EInvoiceAdapter
from .eta_adapter import EgyptETAAdapter
from .uae_fta_adapter import UAEFTAAdapter

_REGISTRY: Dict[str, Type[EInvoiceAdapter]] = {
    "EG": EgyptETAAdapter,
    "AE": UAEFTAAdapter,
}


def get_adapter(jurisdiction: str, **kwargs) -> EInvoiceAdapter:
    key = (jurisdiction or "").upper()
    if key not in _REGISTRY:
        raise ValueError(f"no e-invoicing adapter registered for jurisdiction {jurisdiction!r}")
    return _REGISTRY[key](**kwargs)
