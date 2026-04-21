"""TASK-042 — unit tests for the in-process event bus."""
from __future__ import annotations

import os
import sys

_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from utils.event_bus import EventBus, DomainEvent, Events  # noqa: E402


def test_publish_delivers_to_subscribers():
    bus = EventBus()
    received = []
    bus.subscribe("x.y.z", lambda e: received.append(e))
    bus.publish("x.y.z", {"a": 1})
    assert len(received) == 1
    assert received[0].name == "x.y.z"
    assert received[0].payload == {"a": 1}


def test_multiple_subscribers_all_called():
    bus = EventBus()
    hits = []
    bus.subscribe("ev", lambda e: hits.append("a"))
    bus.subscribe("ev", lambda e: hits.append("b"))
    bus.publish("ev")
    assert hits == ["a", "b"]


def test_handler_exception_does_not_abort_other_handlers():
    bus = EventBus()
    called = []
    def bad(e): raise RuntimeError("boom")
    def good(e): called.append("ok")
    bus.subscribe("ev", bad)
    bus.subscribe("ev", good)
    bus.publish("ev")  # must NOT raise
    assert called == ["ok"]


def test_unsubscribe_removes_handler():
    bus = EventBus()
    hits = []
    def h(e): hits.append(1)
    bus.subscribe("ev", h)
    assert bus.unsubscribe("ev", h) is True
    bus.publish("ev")
    assert hits == []


def test_no_handlers_is_noop():
    bus = EventBus()
    bus.publish("nobody.listens")  # must not raise


def test_canonical_event_names_exist():
    assert Events.JOURNAL_ENTRY_POSTED == "gl.journal_entry.posted"
    assert Events.SALES_INVOICE_POSTED.startswith("sales.")


def test_source_to_domain_event_map_covers_core_flows():
    """gl_service must fan out the right domain event based on JE `source`."""
    from services.gl_service import _SOURCE_EVENT_MAP
    # Spot-check representatives from each domain.
    assert _SOURCE_EVENT_MAP["sales-invoice"] == Events.SALES_INVOICE_POSTED
    assert _SOURCE_EVENT_MAP["purchase_invoice"] == Events.PURCHASE_INVOICE_POSTED
    assert _SOURCE_EVENT_MAP["shipment_dispatch"] == Events.INVENTORY_MOVEMENT_POSTED
    assert _SOURCE_EVENT_MAP["payroll"] == Events.PAYROLL_RUN_POSTED
    assert _SOURCE_EVENT_MAP["customerreceipt"] == Events.SALES_PAYMENT_RECEIVED
    assert _SOURCE_EVENT_MAP["payment_voucher"] == Events.PURCHASE_PAYMENT_MADE


def test_sample_plugin_registers_subscriptions():
    """plugins/gl_posting_metrics must subscribe to the 7 canonical events."""
    bus = EventBus()

    class _FakeApp:
        def __init__(self): self.routers = []
        def include_router(self, r, **kw): self.routers.append(r)

    import plugins.gl_posting_metrics as plugin
    app = _FakeApp()
    plugin.register(app, bus)

    # At least JE + 6 domain events subscribed, and a router included.
    assert Events.JOURNAL_ENTRY_POSTED in bus._handlers
    assert Events.SALES_INVOICE_POSTED in bus._handlers
    assert Events.PURCHASE_INVOICE_POSTED in bus._handlers
    assert Events.INVENTORY_MOVEMENT_POSTED in bus._handlers
    assert Events.PAYROLL_RUN_POSTED in bus._handlers
    assert len(app.routers) == 1
