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
