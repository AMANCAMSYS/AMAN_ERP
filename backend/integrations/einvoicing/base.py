"""Common contract for e-invoicing adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class SubmissionResult:
    status: str                 # submitted | accepted | rejected | error
    document_uuid: Optional[str] = None
    response: Optional[dict] = None
    error_message: Optional[str] = None


class EInvoiceAdapter(ABC):
    """Every jurisdictional adapter implements this protocol."""

    jurisdiction: str = ""

    @abstractmethod
    def submit(self, invoice: dict) -> SubmissionResult:
        """Send an invoice document to the tax authority."""

    @abstractmethod
    def fetch_status(self, document_uuid: str) -> SubmissionResult:
        """Poll current status for a previously-submitted document."""

    def cancel(self, document_uuid: str, reason: str) -> SubmissionResult:
        """Optional cancellation flow; default not supported."""
        return SubmissionResult(status="error", error_message="cancel not supported by adapter")
