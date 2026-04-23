#!/usr/bin/env python3
"""Permission audit utility.

Walks the backend tree and builds two sets:

* ``declared``  - permissions referenced by ``require_permission("...")``
                   decorators / dependencies (the canonical "in-use" set).
* ``seeded``    - permissions found in role-seed JSON / SQL fixtures (the
                   set actually granted to any role).

The script then reports:

* declared-but-never-seeded  (orphan checks - dead in production)
* seeded-but-never-declared  (dead permissions still being granted)

Run:
    python scripts/audit_permissions.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"

REQUIRE_RE = re.compile(r"""require_permission\(\s*['"]([\w.\*-]+)['"]""")
PERM_LIST_KEY = re.compile(r'"permissions"\s*:\s*\[([^\]]*)\]')
QUOTED = re.compile(r"['\"]([\w.\*-]+)['\"]")


def scan_declared() -> set[str]:
    found: set[str] = set()
    for path in BACKEND.rglob("*.py"):
        if "/tests/" in str(path):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for match in REQUIRE_RE.finditer(text):
            found.add(match.group(1))
    return found


def scan_seeded() -> set[str]:
    """Collect permissions from JSON role seeds and Python seed scripts."""
    found: set[str] = set()
    candidates = list(BACKEND.rglob("*role*seed*"))
    candidates += list(BACKEND.rglob("*permission*seed*"))
    candidates += list(ROOT.glob("backend/scripts/*seed*"))
    candidates += list(BACKEND.rglob("seed_*.py"))
    for path in candidates:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for block in PERM_LIST_KEY.findall(text):
            for match in QUOTED.finditer(block):
                found.add(match.group(1))
    return found


def main() -> int:
    declared = scan_declared()
    seeded = scan_seeded()

    orphan_declared = sorted(declared - seeded - {"*"})
    orphan_seeded = sorted(seeded - declared - {"*"})

    report = {
        "declared_count": len(declared),
        "seeded_count": len(seeded),
        "declared_not_seeded": orphan_declared,
        "seeded_not_declared": orphan_seeded,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))

    # Always exit 0 — advisory tool, not a CI gate (yet).
    return 0


if __name__ == "__main__":
    sys.exit(main())
