"""
Distributed event-bus bridge — publishes every in-process `DomainEvent` to
Redis Streams so external workers / microservices can consume them.

Enable by setting ``REDIS_EVENT_BUS=1`` and ``REDIS_URL=redis://host:port/db``
in the environment. When disabled (default) this module is a no-op and the
in-process bus behaves exactly as before.

Design
------
* A single "relay" handler is registered for every known event name (and
  subscribed lazily whenever a new event name is seen the first time the
  bridge fans out).
* We XADD to a per-event stream ``erp.events.<name>`` with fields
  ``{payload, occurred_at}`` — JSON-encoded. MAXLEN trims old entries so
  streams stay bounded.
* Delivery failures are logged but **never** raise — domain events must
  not break the triggering DB transaction.
* Consumers use Redis Consumer Groups (XREADGROUP) on their end; the
  bridge itself is publish-only.
"""

from __future__ import annotations

import json
import logging
import os

from .event_bus import DomainEvent, Events, get_bus

logger = logging.getLogger(__name__)

_ENABLED = os.getenv("REDIS_EVENT_BUS", "0").lower() in {"1", "true", "yes", "on"}
_REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
_STREAM_MAXLEN = int(os.getenv("REDIS_EVENT_STREAM_MAXLEN", "10000"))
_STREAM_PREFIX = os.getenv("REDIS_EVENT_STREAM_PREFIX", "erp.events")

_client = None  # lazy singleton
_installed = False


def _get_client():
    global _client
    if _client is not None:
        return _client
    try:
        import redis  # type: ignore
        _client = redis.from_url(_REDIS_URL, socket_connect_timeout=2,
                                 socket_timeout=2, decode_responses=False)
        _client.ping()
        logger.info("redis_event_bus: connected to %s", _REDIS_URL)
    except Exception as e:
        logger.warning("redis_event_bus: disabled (%s)", e)
        _client = False  # sentinel — don't retry every call
    return _client


def _stream_key(event_name: str) -> str:
    return f"{_STREAM_PREFIX}.{event_name}"


def _relay_handler(event: DomainEvent) -> None:
    client = _get_client()
    if not client:
        return
    try:
        client.xadd(
            _stream_key(event.name),
            {
                b"payload": json.dumps(event.payload, default=str).encode("utf-8"),
                b"occurred_at": event.occurred_at.isoformat().encode("utf-8"),
            },
            maxlen=_STREAM_MAXLEN,
            approximate=True,
        )
    except Exception:
        logger.exception("redis_event_bus: XADD failed for %s", event.name)


def _all_known_event_names() -> list[str]:
    """Enumerate every event constant declared on ``Events``."""
    names = []
    for attr in dir(Events):
        if attr.startswith("_"):
            continue
        val = getattr(Events, attr)
        if isinstance(val, str) and "." in val:
            names.append(val)
    return names


def install(force: bool = False) -> bool:
    """
    Install the Redis-Streams relay onto every canonical event.

    Returns True if installed, False if disabled by env or already installed.
    Safe to call multiple times.
    """
    global _installed
    if _installed and not force:
        return False
    if not _ENABLED and not force:
        logger.debug("redis_event_bus: REDIS_EVENT_BUS not enabled; skipping install")
        return False
    bus = get_bus()
    for name in _all_known_event_names():
        bus.subscribe(name, _relay_handler)
    _installed = True
    logger.info("redis_event_bus: relay installed for %d canonical events",
                len(_all_known_event_names()))
    return True


def uninstall() -> None:
    """Remove the relay (primarily for tests)."""
    global _installed
    bus = get_bus()
    for name in _all_known_event_names():
        bus.unsubscribe(name, _relay_handler)
    _installed = False


def is_enabled() -> bool:
    return _ENABLED


def is_installed() -> bool:
    return _installed
