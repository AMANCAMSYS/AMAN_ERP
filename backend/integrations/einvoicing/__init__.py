"""
TASK-040 — E-invoicing adapters (Egypt ETA + UAE FTA 2026).

This package defines a common `EInvoiceAdapter` protocol and per-jurisdiction
adapter stubs. Each adapter is responsible for:

  * Serialising a domain invoice into the authority's XML/JSON schema.
  * Signing (where required) and submitting to the authority's endpoint.
  * Recording the submission in `e_invoice_submissions`.
  * Polling / handling status updates.

The stubs here expose the API surface so downstream services can depend on
the contract without waiting for full integrations, which require per-tenant
credentials, sandbox testing, and certified signing keys.
"""

from .base import EInvoiceAdapter, SubmissionResult
from .eta_adapter import EgyptETAAdapter
from .uae_fta_adapter import UAEFTAAdapter
from .zatca_adapter import ZATCAAdapter, ZATCAConfig, build_qr_payload, build_ubl_xml, invoice_hash
from .registry import get_adapter

__all__ = [
    "EInvoiceAdapter",
    "SubmissionResult",
    "EgyptETAAdapter",
    "UAEFTAAdapter",
    "ZATCAAdapter",
    "ZATCAConfig",
    "build_qr_payload",
    "build_ubl_xml",
    "invoice_hash",
    "get_adapter",
]
