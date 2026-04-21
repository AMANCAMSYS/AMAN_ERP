"""
Sample plugin: GL posting metrics.

Demonstrates the TASK-041/042 plugin + event-bus design by subscribing to
domain events emitted by gl_service and maintaining lightweight in-process
Prometheus counters. Ships by default; can be disabled by setting the env
variable `DISABLE_PLUGINS=1` (disables ALL plugins) or by deleting this
directory.

Counters exposed via `/metrics`:
  - aman_je_posted_total{source,status}
  - aman_sales_invoice_posted_total
  - aman_purchase_invoice_posted_total
  - aman_inventory_movement_posted_total
  - aman_payroll_run_posted_total
  - aman_payment_received_total
  - aman_payment_made_total
"""

from __future__ import annotations

import logging

from fastapi import APIRouter

from utils.event_bus import Events

logger = logging.getLogger(__name__)

# ---- Prometheus counters (fail-open if client is missing) ------------------
try:
    from prometheus_client import Counter

    _je_counter = Counter(
        "aman_je_posted_total",
        "Journal entries posted, labelled by source + status",
        ["source", "status"],
    )
    _sales_invoice_counter = Counter(
        "aman_sales_invoice_posted_total",
        "Sales invoices posted (counted via event bus)",
    )
    _purchase_invoice_counter = Counter(
        "aman_purchase_invoice_posted_total",
        "Purchase invoices posted (counted via event bus)",
    )
    _inventory_movement_counter = Counter(
        "aman_inventory_movement_posted_total",
        "Inventory-impacting JE postings (shipments/deliveries/landed costs)",
    )
    _payroll_counter = Counter(
        "aman_payroll_run_posted_total",
        "Payroll runs posted (counted via event bus)",
    )
    _payment_in_counter = Counter(
        "aman_payment_received_total",
        "Customer payments received (counted via event bus)",
    )
    _payment_out_counter = Counter(
        "aman_payment_made_total",
        "Supplier payments made (counted via event bus)",
    )
    _METRICS_ENABLED = True
except Exception:
    logger.info("prometheus_client unavailable — gl_posting_metrics will no-op")
    _METRICS_ENABLED = False


# ---- Event handlers ---------------------------------------------------------

def _on_je_posted(event):
    if not _METRICS_ENABLED:
        return
    payload = event.payload or {}
    _je_counter.labels(
        source=str(payload.get("source") or "unknown"),
        status=str(payload.get("status") or "unknown"),
    ).inc()


def _on_sales_invoice(event):
    if _METRICS_ENABLED:
        _sales_invoice_counter.inc()


def _on_purchase_invoice(event):
    if _METRICS_ENABLED:
        _purchase_invoice_counter.inc()


def _on_inventory_movement(event):
    if _METRICS_ENABLED:
        _inventory_movement_counter.inc()


def _on_payroll(event):
    if _METRICS_ENABLED:
        _payroll_counter.inc()


def _on_payment_received(event):
    if _METRICS_ENABLED:
        _payment_in_counter.inc()


def _on_payment_made(event):
    if _METRICS_ENABLED:
        _payment_out_counter.inc()


# ---- Optional diagnostic endpoint ------------------------------------------
_router = APIRouter(prefix="/plugins/gl-posting-metrics", tags=["plugin:gl-metrics"])


@_router.get("/health")
def health():
    return {
        "plugin": "gl_posting_metrics",
        "enabled": _METRICS_ENABLED,
        "subscribed_events": [
            Events.JOURNAL_ENTRY_POSTED,
            Events.SALES_INVOICE_POSTED,
            Events.PURCHASE_INVOICE_POSTED,
            Events.INVENTORY_MOVEMENT_POSTED,
            Events.PAYROLL_RUN_POSTED,
            Events.SALES_PAYMENT_RECEIVED,
            Events.PURCHASE_PAYMENT_MADE,
        ],
    }


# ---- Plugin entrypoint ------------------------------------------------------

def register(app, bus):
    bus.subscribe(Events.JOURNAL_ENTRY_POSTED, _on_je_posted)
    bus.subscribe(Events.SALES_INVOICE_POSTED, _on_sales_invoice)
    bus.subscribe(Events.PURCHASE_INVOICE_POSTED, _on_purchase_invoice)
    bus.subscribe(Events.INVENTORY_MOVEMENT_POSTED, _on_inventory_movement)
    bus.subscribe(Events.PAYROLL_RUN_POSTED, _on_payroll)
    bus.subscribe(Events.SALES_PAYMENT_RECEIVED, _on_payment_received)
    bus.subscribe(Events.PURCHASE_PAYMENT_MADE, _on_payment_made)
    app.include_router(_router, prefix="/api")
    logger.info("✅ gl_posting_metrics plugin registered "
                "(7 event subscriptions + /api/plugins/gl-posting-metrics/health)")
