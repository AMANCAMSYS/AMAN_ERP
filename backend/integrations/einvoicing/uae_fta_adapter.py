"""
UAE Federal Tax Authority (FTA) e-invoicing adapter — stub.

The UAE mandate (phase 1 from July 2026) requires:
  * PINT AE (Peppol International UBL) document format.
  * Submission through an Accredited Service Provider (ASP) over the Peppol
    5-corner network rather than direct to FTA.
  * Pre-clearance model: invoices must be accepted by the ASP before being
    legally issued.

This scaffold records a dry-run submission so downstream flows compile; the
real integration requires ASP onboarding per tenant.
"""

from __future__ import annotations

import logging
import os
import uuid as _uuid

from .base import EInvoiceAdapter, SubmissionResult

logger = logging.getLogger(__name__)


class UAEFTAAdapter(EInvoiceAdapter):
    jurisdiction = "AE"

    def __init__(self, asp_endpoint: str | None = None, api_key: str | None = None,
                 dry_run: bool = True):
        self.asp_endpoint = asp_endpoint or os.getenv("UAE_ASP_ENDPOINT", "")
        self.api_key = api_key or os.getenv("UAE_ASP_API_KEY", "")
        self.dry_run = dry_run or not (self.asp_endpoint and self.api_key)

    def submit(self, invoice: dict) -> SubmissionResult:
        if self.dry_run:
            doc_uuid = f"dryrun-ae-{_uuid.uuid4()}"
            logger.info("[UAE-FTA dry_run] recording submission %s for invoice %s",
                        doc_uuid, invoice.get("id"))
            return SubmissionResult(status="submitted", document_uuid=doc_uuid,
                                    response={"dry_run": True})
        return SubmissionResult(status="error", error_message="live UAE ASP submission not implemented")

    def fetch_status(self, document_uuid: str) -> SubmissionResult:
        if self.dry_run:
            return SubmissionResult(status="accepted", document_uuid=document_uuid,
                                    response={"dry_run": True})
        return SubmissionResult(status="error", error_message="live UAE ASP status polling not implemented")
