#!/usr/bin/env python3
"""
CI guard — prevents new raw INSERTs into GL tables outside the approved
gateway (`backend/services/gl_service.py`). Routers and services MUST
call `gl_service.create_journal_entry(...)` so every posting flows through
idempotency, balance, period-lock, and immutability checks.

Also enforces that every call site of ``create_journal_entry`` /
``gl_create_journal_entry`` in router/service modules is preceded by a
``check_fiscal_period_open(...)`` call in the same enclosing function.
This prevents new GL postings from bypassing the fiscal-period lock.

Exit code 0: clean. Exit code 1: violation detected.

Allow-list: the gateway itself, Alembic migrations, seed scripts, and
this checker.
"""
from __future__ import annotations
import ast
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


# ---------------------------------------------------------------------------
# Fiscal-lock pairing check
# ---------------------------------------------------------------------------
# Every call to ``create_journal_entry`` (or the conventional local alias
# ``gl_create_journal_entry``) inside a router/service function must be
# preceded by a call to ``check_fiscal_period_open`` earlier in the same
# enclosing function body. Endpoints that legitimately cross the fiscal
# lock (fiscal-year close/reopen, closing-entry generation) are allow-
# listed below.

JE_CALL_NAMES = {"create_journal_entry", "gl_create_journal_entry"}
FISCAL_CHECK_NAME = "check_fiscal_period_open"

# Keyed by (posix path relative to repo root, qualified function name).
# Qualified name includes the outermost class if present (e.g.
# ``Class.method``) or just the function name otherwise.
FISCAL_LOCK_ALLOWLIST: set[tuple[str, str]] = {
    # Gateway definition itself.
    ("backend/services/gl_service.py", "create_journal_entry"),
    # Fiscal-year close/reopen and closing entries legitimately cross
    # the lock boundary (gated by ``accounting.manage`` permission).
    ("backend/routers/finance/accounting.py", "close_fiscal_year"),
    ("backend/routers/finance/accounting.py", "reopen_fiscal_year"),
    ("backend/routers/finance/accounting.py", "generate_closing_entries"),
    # Helper invoked only from ``create_expense`` which already guards the
    # fiscal period at the router entry point.
    ("backend/routers/finance/expenses.py", "create_expense_journal_entry"),
}


def _qualname(stack: list[ast.AST]) -> str:
    parts: list[str] = []
    for node in stack:
        if isinstance(node, ast.ClassDef):
            parts.append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            parts.append(node.name)
    return ".".join(parts)


def _call_name(call: ast.Call) -> str | None:
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _scan_function(
    func: ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[bool, list[ast.Call]]:
    """Return (has_fiscal_check, je_calls) for a function body.

    ``has_fiscal_check`` reflects whether any ``check_fiscal_period_open``
    call appears anywhere in the function (including nested conditionals).
    The pairing rule requires the fiscal check to appear *before* each JE
    call lexically, which we approximate by line number ordering within
    the same function.
    """
    je_calls: list[ast.Call] = []
    fiscal_calls: list[ast.Call] = []
    for node in ast.walk(func):
        # Do not descend into nested function definitions — they form
        # their own scope and are scanned separately.
        if node is func:
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if isinstance(node, ast.Call):
            name = _call_name(node)
            if name in JE_CALL_NAMES:
                je_calls.append(node)
            elif name == FISCAL_CHECK_NAME:
                fiscal_calls.append(node)
    return fiscal_calls, je_calls


def _iter_functions(tree: ast.AST, stack: list[ast.AST] | None = None):
    if stack is None:
        stack = []
    for child in ast.iter_child_nodes(tree):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield stack + [child], child
            yield from _iter_functions(child, stack + [child])
        elif isinstance(child, ast.ClassDef):
            yield from _iter_functions(child, stack + [child])
        else:
            yield from _iter_functions(child, stack)


fiscal_violations: list[tuple[str, int, str]] = []

# Scope: routers + services (where endpoints/service methods post GL).
SCAN_DIRS = [
    BACKEND / "routers",
    BACKEND / "services",
]

for scan_dir in SCAN_DIRS:
    if not scan_dir.exists():
        continue
    for path in scan_dir.rglob("*.py"):
        rel = path.relative_to(ROOT).as_posix()
        try:
            source = path.read_text(encoding="utf-8")
        except Exception:
            continue
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError:
            continue

        # Quick skip: no JE call by name anywhere in the file.
        if not any(
            name in source for name in JE_CALL_NAMES
        ):
            continue

        for stack, func in _iter_functions(tree):
            fiscal_calls, je_calls = _scan_function(func)
            if not je_calls:
                continue
            qname = _qualname(stack)
            if (rel, qname) in FISCAL_LOCK_ALLOWLIST:
                continue
            # Also allow simple function name match (in case of nested
            # helpers where qualified name includes the outer class).
            if (rel, func.name) in FISCAL_LOCK_ALLOWLIST:
                continue
            for je_call in je_calls:
                # Require at least one fiscal check at an earlier line.
                if not any(
                    fc.lineno < je_call.lineno for fc in fiscal_calls
                ):
                    fiscal_violations.append((rel, je_call.lineno, qname))

if fiscal_violations:
    print()
    print(
        "Fiscal-lock pairing violations "
        "(each JE call must be preceded by check_fiscal_period_open):"
    )
    for rel, lineno, qname in fiscal_violations:
        print(f"  {rel}:{lineno}  in  {qname}()")
    print(f"\nTotal: {len(fiscal_violations)} violation(s).")
    sys.exit(1)

print("OK — every GL posting is preceded by check_fiscal_period_open.")
sys.exit(0)
