"""
TASK-042 — In-process domain event bus.

A lightweight synchronous pub/sub for decoupling cross-module side effects
(e.g. "a sales invoice was posted" → notifications, analytics refresh,
plugin hooks) from the posting flow itself.

Design decisions:
  * In-process only — no Redis/Kafka. Lives inside the FastAPI worker so
    handlers have the same DB session context available.
  * Synchronous by default. Handlers that need async work should schedule
    it themselves (APScheduler/worker).
  * Handler errors are logged but NEVER propagated — domain events must not
    break the triggering transaction. If you need a handler whose failure
    must abort the transaction, do NOT use the event bus; call it directly.
  * Event names are dotted lowercase strings: `{domain}.{entity}.{verb}`,
    e.g. `sales.invoice.posted`, `gl.journal_entry.posted`, `ar.payment.received`.

Plugin system (TASK-041) is a thin layer on top: plugins register handlers
via the same API.

Example:
    from utils.event_bus import subscribe, publish

    @subscribe("sales.invoice.posted")
    def on_invoice_posted(event):
        ...  # event.payload is a dict

    publish("sales.invoice.posted", {"invoice_id": 42, "company_id": "C001"})
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DomainEvent:
    name: str
    payload: Dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


EventHandler = Callable[[DomainEvent], None]


class EventBus:
    def __init__(self) -> None:
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._lock = RLock()

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        with self._lock:
            self._handlers.setdefault(event_name, []).append(handler)
        logger.debug("event_bus: subscribed %s -> %s", event_name, getattr(handler, "__qualname__", handler))

    def unsubscribe(self, event_name: str, handler: EventHandler) -> bool:
        with self._lock:
            handlers = self._handlers.get(event_name)
            if not handlers or handler not in handlers:
                return False
            handlers.remove(handler)
            return True

    def publish(self, event_name: str, payload: Dict[str, Any] | None = None) -> None:
        event = DomainEvent(name=event_name, payload=dict(payload or {}))
        with self._lock:
            handlers = list(self._handlers.get(event_name, ()))
        if not handlers:
            return
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                # Domain events must NEVER break the triggering transaction.
                logger.exception(
                    "event_bus: handler %s failed for event %s",
                    getattr(handler, "__qualname__", handler),
                    event_name,
                )

    def handlers_for(self, event_name: str) -> List[EventHandler]:
        with self._lock:
            return list(self._handlers.get(event_name, ()))

    def clear(self) -> None:  # primarily for tests
        with self._lock:
            self._handlers.clear()


# Module-level singleton. Import from here everywhere.
_bus = EventBus()


def subscribe(event_name: str):
    """Decorator form: @subscribe("sales.invoice.posted") def handler(event): ..."""
    def _decorator(fn: EventHandler) -> EventHandler:
        _bus.subscribe(event_name, fn)
        return fn
    return _decorator


def publish(event_name: str, payload: Dict[str, Any] | None = None) -> None:
    _bus.publish(event_name, payload)


def get_bus() -> EventBus:
    return _bus


# ═══════════════════════════════════════════════════════════════════════════════
# Canonical event names — single source of truth for producers and plugins.
# Add new events here; do NOT inline string literals in call sites.
# ═══════════════════════════════════════════════════════════════════════════════

class Events:
    # GL
    JOURNAL_ENTRY_POSTED = "gl.journal_entry.posted"
    JOURNAL_ENTRY_REVERSED = "gl.journal_entry.reversed"
    # Sales
    SALES_INVOICE_POSTED = "sales.invoice.posted"
    SALES_INVOICE_CANCELLED = "sales.invoice.cancelled"
    SALES_PAYMENT_RECEIVED = "sales.payment.received"
    # Purchases
    PURCHASE_INVOICE_POSTED = "purchases.invoice.posted"
    PURCHASE_PAYMENT_MADE = "purchases.payment.made"
    # Inventory
    INVENTORY_MOVEMENT_POSTED = "inventory.movement.posted"
    # HR
    PAYROLL_RUN_POSTED = "hr.payroll_run.posted"
