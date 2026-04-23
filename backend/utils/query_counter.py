"""Per-request SQL query counter (opt-in, observability).

Counts the number of executed statements per HTTP request and exposes the
total in the ``X-DB-Query-Count`` response header plus the structured log
line. When the count exceeds ``QUERY_COUNT_WARN_THRESHOLD`` (default 50) a
WARNING is emitted so suspect endpoints can be hunted with a simple
``grep "n+1 suspect"`` over the access log.

Disabled by default; enable with ``ENABLE_QUERY_COUNTER=1``.

The middleware uses ``contextvars`` so worker threads / async contexts get
their own counter, and a SQLAlchemy event hook on ``before_cursor_execute``
to do the actual counting. It does **not** log SQL bodies, only counts.
"""
from __future__ import annotations

import logging
import os
import time
from contextvars import ContextVar

from sqlalchemy import event

logger = logging.getLogger(__name__)

QUERY_COUNT_WARN_THRESHOLD = int(os.environ.get("QUERY_COUNT_WARN_THRESHOLD", "50"))

_query_count: ContextVar[int] = ContextVar("aman_query_count", default=0)


def _bump(*_args, **_kwargs) -> None:
    try:
        _query_count.set(_query_count.get() + 1)
    except Exception:
        # Never let observability break a request.
        pass


def install_engine_listener(engine) -> None:
    """Attach the counter to a SQLAlchemy engine. Idempotent."""
    if getattr(engine, "_aman_query_counter_attached", False):
        return
    event.listen(engine, "before_cursor_execute", _bump)
    engine._aman_query_counter_attached = True


class QueryCounterMiddleware:
    """ASGI middleware that resets the counter per request and logs the result."""

    def __init__(self, app):
        self.app = app
        self.enabled = os.environ.get("ENABLE_QUERY_COUNTER", "0") == "1"

    async def __call__(self, scope, receive, send):
        if not self.enabled or scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        token = _query_count.set(0)
        start = time.perf_counter()
        path = scope.get("path", "")

        async def _send(message):
            if message["type"] == "http.response.start":
                count = _query_count.get()
                duration_ms = int((time.perf_counter() - start) * 1000)
                headers = list(message.get("headers", []))
                headers.append((b"x-db-query-count", str(count).encode()))
                message["headers"] = headers
                if count >= QUERY_COUNT_WARN_THRESHOLD:
                    logger.warning(
                        "n+1 suspect: %d queries on %s in %d ms",
                        count, path, duration_ms,
                    )
            await send(message)

        try:
            await self.app(scope, receive, _send)
        finally:
            _query_count.reset(token)
