#!/usr/bin/env python3
"""
TASK-033: CI guard — enforce SQLAlchemy parameterized queries.

Rejects any f-string or `%`/`+` concatenation passed into `text(...)` inside
backend/, because those bypass parameter binding and are the root cause of
SQL injection.

Allowed:  text("SELECT ... WHERE id = :id")  # bind-param
Blocked:  text(f"SELECT ... WHERE id = {user_id}")
          text("SELECT ... WHERE id = " + x)
          text("SELECT ... WHERE id = %s" % x)

A small allowlist is supported (trusted server-generated identifiers such as
table/column names coming from information_schema). Add an explicit comment
`# noqa: sql-lint` on the offending line to whitelist it after review.
"""
from __future__ import annotations

import ast
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = REPO_ROOT / "backend"
BASELINE = REPO_ROOT / "scripts" / "sql_lint_baseline.txt"


def _load_baseline() -> set[str]:
    """Grandfathered pre-existing sites (`path:lineno`). New sites still fail."""
    if not BASELINE.exists():
        return set()
    out: set[str] = set()
    for raw in BASELINE.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        out.add(raw)
    return out


def _is_unsafe_text_call(node: ast.Call, source_lines: list[str]) -> str | None:
    """Return an error message if `text(...)` is called with unsafe args."""
    func = node.func
    if isinstance(func, ast.Name) and func.id == "text":
        pass
    elif isinstance(func, ast.Attribute) and func.attr == "text":
        pass
    else:
        return None

    if not node.args:
        return None

    arg = node.args[0]

    # Per-line opt-out comment.
    try:
        line = source_lines[node.lineno - 1]
        if "noqa: sql-lint" in line:
            return None
    except IndexError:
        pass

    if isinstance(arg, ast.JoinedStr):
        # f-string with at least one interpolation
        has_dynamic = any(isinstance(v, ast.FormattedValue) for v in arg.values)
        if has_dynamic:
            return "text() called with f-string containing interpolated value"

    if isinstance(arg, ast.BinOp):
        # string concatenation or % formatting
        if isinstance(arg.op, (ast.Add, ast.Mod)):
            return "text() called with string concatenation / % formatting"

    if isinstance(arg, ast.Call):
        if isinstance(arg.func, ast.Attribute) and arg.func.attr == "format":
            return "text() called with str.format()"

    return None


def scan_file(path: pathlib.Path) -> list[tuple[int, str]]:
    try:
        src = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    lines = src.splitlines()
    issues: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            msg = _is_unsafe_text_call(node, lines)
            if msg:
                issues.append((node.lineno, msg))
    return issues


def main() -> int:
    if not BACKEND.exists():
        print(f"✗ backend directory not found: {BACKEND}")
        return 2

    baseline = _load_baseline()
    violations: list[tuple[pathlib.Path, int, str]] = []
    grandfathered = 0
    for py in BACKEND.rglob("*.py"):
        # Skip migration files — those are static and vetted, and benign
        # f-string usage on table/column names is unavoidable.
        if "/alembic/" in str(py) or "/migrations/" in str(py):
            continue
        if "/tests/" in str(py):
            continue
        rel = py.relative_to(REPO_ROOT)
        for ln, msg in scan_file(py):
            key = f"{rel}:{ln}"
            if key in baseline:
                grandfathered += 1
                continue
            violations.append((py, ln, msg))

    if violations:
        print("✗ NEW unsafe SQL text() construction detected:\n")
        for path, ln, msg in violations:
            rel = path.relative_to(REPO_ROOT)
            print(f"  {rel}:{ln}  {msg}")
        print(
            "\nFix: use :bind_param placeholders + pass values via "
            ".execute(stmt, {'bind': value}).\n"
            "If the dynamic segment is a trusted identifier vetted at runtime "
            "(e.g. table name fetched from information_schema), add the comment "
            "`# noqa: sql-lint` to the offending line."
        )
        return 1

    print(
        f"OK — no new unsafe text() calls detected in backend/ "
        f"({grandfathered} pre-existing sites grandfathered via "
        f"scripts/sql_lint_baseline.txt)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
