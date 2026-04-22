#!/usr/bin/env python3
"""
SEC-07: CI guard — reject log statements that embed raw secret/PII values.

Blocked patterns (f-strings inside logger.* or print):
    logger.info(f"token: {token}")         # actual secret in log
    logger.info(f"password: {password}")   # actual secret in log
    logger.info(f"api_key = {api_key}")    # actual secret in log

Allowed patterns:
    logger.info("Generate with: python -c '...'")   # constant message
    logger.info(f"Password reset for {email}")      # email (non-secret PII is ok)
    logger.info(f"token prefix: {token[:8]}...")    # truncated — safe hint
    logger.info("Password policy updated")          # no interpolation of secret

Exit codes:
    0 → clean
    1 → violations found
"""
from __future__ import annotations

import ast
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = REPO_ROOT / "backend"

# Variable names that MUST NOT be interpolated (bare) into log strings.
FORBIDDEN_NAMES = {
    "password", "new_password", "old_password", "raw_password", "plain_password",
    "secret", "secret_key", "api_key", "apikey", "client_secret",
    "token", "access_token", "refresh_token", "reset_token", "temp_token",
    "bearer", "authorization",
    "cvv", "card_number", "pan",
    "ssn", "iban", "sort_code",
    "private_key", "priv_key",
}

LOGGER_METHODS = {"info", "warning", "warn", "error", "exception", "critical", "debug"}


def _is_log_call(node: ast.Call) -> bool:
    func = node.func
    if isinstance(func, ast.Attribute) and func.attr in LOGGER_METHODS:
        return True
    if isinstance(func, ast.Name) and func.id == "print":
        return True
    return False


def _fstring_has_bare_secret(fstr: ast.JoinedStr) -> str | None:
    """Return the offending name if the f-string interpolates a forbidden
    variable WITHOUT slicing/hashing/masking it."""
    for part in fstr.values:
        if not isinstance(part, ast.FormattedValue):
            continue
        expr = part.value
        # Bare Name: f"... {password} ..."
        if isinstance(expr, ast.Name) and expr.id.lower() in FORBIDDEN_NAMES:
            return expr.id
        # Bare attribute: f"... {obj.password} ..."
        if isinstance(expr, ast.Attribute) and expr.attr.lower() in FORBIDDEN_NAMES:
            return expr.attr
        # Subscript like token[:8] is safe (truncated) — skip.
        # Call like mask(token) / hash(token) is safe — skip.
    return None


def _scan(path: pathlib.Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return []
    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not _is_log_call(node):
            continue
        for arg in node.args:
            if isinstance(arg, ast.JoinedStr):
                name = _fstring_has_bare_secret(arg)
                if name:
                    violations.append(
                        f"{path.relative_to(REPO_ROOT)}:{node.lineno}: "
                        f"log interpolates bare secret '{name}'. "
                        f"Use mask_pii() or truncate (e.g. {{{name}[:8]}}...)."
                    )
    return violations


def main() -> int:
    violations: list[str] = []
    for py in BACKEND.rglob("*.py"):
        # Skip tests (may legitimately log test fixtures).
        if "/tests/" in str(py) or py.name.startswith("test_"):
            continue
        violations.extend(_scan(py))
    if violations:
        print("❌ PII/secret logging violations:\n", file=sys.stderr)
        for v in violations:
            print("  " + v, file=sys.stderr)
        print(
            f"\n{len(violations)} violation(s). Mask or truncate sensitive values "
            f"before logging (see backend/utils/masking.py).",
            file=sys.stderr,
        )
        return 1
    print("OK — no raw secret interpolation in logger/print calls.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
