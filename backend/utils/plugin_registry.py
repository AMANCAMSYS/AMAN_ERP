"""
TASK-041 — Plugin / Hook registry.

A thin layer on top of the event bus (TASK-042). Plugins are discovered on
startup from the `backend/plugins/` directory and/or from an entry-point
group `aman_erp.plugins`. Each plugin module exposes a `register(app, bus)`
callable that wires its event handlers + optional routes + settings panels.

This is intentionally small — the goal is to make it POSSIBLE to extend the
ERP without forking, not to ship a marketplace. Deeper features (sandboxing,
per-tenant enable/disable UI, signed packages) are deliberately out of scope
for this scaffold.

Usage inside a plugin package (e.g. backend/plugins/my_plugin/__init__.py):

    from utils.event_bus import Events

    def register(app, bus):
        @bus.subscribe = ...  # or use the decorator
        bus.subscribe(Events.JOURNAL_ENTRY_POSTED, _on_je_posted)

        from fastapi import APIRouter
        r = APIRouter(prefix="/plugins/my-plugin", tags=["plugin:my-plugin"])
        @r.get("/ping")
        def ping(): return {"ok": True}
        app.include_router(r, prefix="/api")

    def _on_je_posted(event):
        ...

Call `load_plugins(app)` once during FastAPI startup after all core routers
are registered.
"""

from __future__ import annotations

import importlib
import logging
import os
import pkgutil
from typing import Any, List

from utils.event_bus import get_bus

logger = logging.getLogger(__name__)

_LOADED: List[str] = []


def _iter_local_plugins(plugins_pkg: str = "plugins"):
    """Yield (name, module) for every immediate sub-package of `backend/plugins/`."""
    try:
        pkg = importlib.import_module(plugins_pkg)
    except ModuleNotFoundError:
        return
    pkg_path = getattr(pkg, "__path__", None)
    if not pkg_path:
        return
    for mod in pkgutil.iter_modules(pkg_path):
        if mod.name.startswith("_"):
            continue
        full_name = f"{plugins_pkg}.{mod.name}"
        try:
            yield mod.name, importlib.import_module(full_name)
        except Exception as e:
            logger.warning("plugin import failed %s: %s", full_name, e)


def _iter_entry_point_plugins():
    """Yield (name, module) for every plugin declared via entry points."""
    try:
        from importlib.metadata import entry_points
    except ImportError:
        return
    try:
        eps = entry_points().select(group="aman_erp.plugins")  # py3.10+
    except Exception:
        try:
            eps = entry_points().get("aman_erp.plugins", [])
        except Exception:
            eps = []
    for ep in eps:
        try:
            yield ep.name, ep.load()
        except Exception as e:
            logger.warning("entry-point plugin failed %s: %s", ep.name, e)


def load_plugins(app: Any) -> List[str]:
    """Discover and register all plugins. Safe to call at most once per process."""
    if os.getenv("DISABLE_PLUGINS", "").lower() in ("1", "true", "yes"):
        logger.info("Plugins disabled via DISABLE_PLUGINS")
        return []

    if _LOADED:
        logger.debug("Plugins already loaded: %s", _LOADED)
        return list(_LOADED)

    bus = get_bus()
    loaded: List[str] = []

    for source in (_iter_local_plugins, _iter_entry_point_plugins):
        for name, module in source():
            register = getattr(module, "register", None)
            if not callable(register):
                logger.debug("plugin %s has no register(app, bus) — skipped", name)
                continue
            try:
                register(app, bus)
                loaded.append(name)
                logger.info("✅ plugin loaded: %s", name)
            except Exception:
                logger.exception("plugin %s register() raised — skipping", name)

    _LOADED.extend(loaded)
    if not loaded:
        logger.info("No plugins found (plugins/ dir empty and no entry-points).")
    return loaded


def loaded_plugins() -> List[str]:
    return list(_LOADED)
