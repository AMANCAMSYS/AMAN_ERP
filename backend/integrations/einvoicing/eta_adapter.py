"""
Egypt Tax Authority (ETA) e-invoicing adapter — stub.

Real implementation must:
  * Acquire an access token via ETA's OAuth endpoint using tenant-specific
    client_id / client_secret.
  * Map the invoice dict into ETA's JSON schema (seller, buyer, lines, taxes,
    totals, signatures block).
  * Sign the document with the tenant's USB token / HSM certificate.
  * POST to https://api.invoicing.eta.gov.eg/api/v1/documentsubmissions.
  * Parse the async submission response and poll documents/{uuid} for status.

This scaffold records a "pending" submission so the rest of the ERP can
proceed; the actual network call is deliberately not implemented.
"""

from __future__ import annotations

import logging
import os
import uuid as _uuid

from .base import EInvoiceAdapter, SubmissionResult

logger = logging.getLogger(__name__)


class EgyptETAAdapter(EInvoiceAdapter):
    jurisdiction = "EG"

    def __init__(self, base_url: str | None = None, client_id: str | None = None,
                 client_secret: str | None = None, dry_run: bool = True):
        self.base_url = base_url or os.getenv("ETA_BASE_URL", "https://api.invoicing.eta.gov.eg")
        self.client_id = client_id or os.getenv("ETA_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("ETA_CLIENT_SECRET", "")
        self.dry_run = dry_run or not (self.client_id and self.client_secret)

    def submit(self, invoice: dict) -> SubmissionResult:
        if self.dry_run:
            doc_uuid = f"dryrun-eta-{_uuid.uuid4()}"
            logger.info("[ETA dry_run] recording submission %s for invoice %s",
                        doc_uuid, invoice.get("id"))
            return SubmissionResult(status="submitted", document_uuid=doc_uuid,
                                    response={"dry_run": True})
        # Real HTTP submission omitted — requires certified signing.
        return SubmissionResult(status="error", error_message="live ETA submission not implemented")

    def fetch_status(self, document_uuid: str) -> SubmissionResult:
        if self.dry_run:
            return SubmissionResult(status="accepted", document_uuid=document_uuid,
                                    response={"dry_run": True})
        return SubmissionResult(status="error", error_message="live ETA status polling not implemented")
