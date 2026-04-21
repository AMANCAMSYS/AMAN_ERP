#!/usr/bin/env python3
"""
CI guard — prevents new raw INSERTs into GL tables outside the approved
gateway (`backend/services/gl_service.py`). Routers and services MUST
call `gl_service.create_journal_entry(...)` so every posting flows through
idempotency, balance, period-lock, and immutability checks.

Exit code 0: clean. Exit code 1: violation detected.

Allow-list: the gateway itself, Alembic migrations, seed scripts, and
this checker.
"""
from __future__ import annotations
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"

ALLOWED = {
    "backend/services/gl_service.py",
    "backend/scripts/seed_data.py",
    "scripts/check_gl_posting_discipline.py",
}

RAW_INSERT_RE = re.compile(
    r"INSERT\s+INTO\s+journal_(?:entries|lines)\b",
    re.IGNORECASE,
)

violations: list[tuple[pathlib.Path, int, str]] = []

for path in BACKEND.rglob("*.py"):
    rel = path.relative_to(ROOT).as_posix()
    if rel in ALLOWED:
        continue
    if "/alembic/versions/" in rel or rel.startswith("backend/migrations/"):
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        continue
    for lineno, line in enumerate(text.splitlines(), start=1):
        if RAW_INSERT_RE.search(line):
            violations.append((path, lineno, line.strip()))

if violations:
    print("GL posting discipline violations (route through services/gl_service.py):")
    for path, lineno, line in violations:
        print(f"  {path.relative_to(ROOT)}:{lineno}: {line[:160]}")
    print(f"\nTotal: {len(violations)} violation(s).")
    sys.exit(1)

print("OK — no raw INSERTs into journal_entries/journal_lines outside gl_service.")
sys.exit(0)
