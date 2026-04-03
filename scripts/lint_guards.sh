#!/usr/bin/env bash
# Lint guard: detect float() wrapping monetary variables and f-string SQL in backend code.
# Usage: bash scripts/lint_guards.sh   (exit 0 = clean, exit 1 = violations found)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
EXIT=0

echo "=== Lint Guard: float() on monetary values ==="
# Match float(<var>) near common monetary variable names in Python response dicts
# Excludes test files and the lint script itself
FLOAT_HITS=$(grep -rn --include='*.py' \
    -e 'float(.*balance' \
    -e 'float(.*amount' \
    -e 'float(.*total' \
    -e 'float(.*debit' \
    -e 'float(.*credit' \
    -e 'float(.*salary' \
    -e 'float(.*price' \
    -e 'float(.*cost' \
    -e 'float(.*revenue' \
    -e 'float(.*share' \
    -e 'float(.*gross' \
    -e 'float(.*net_' \
    -e 'float(.*wht' \
    -e 'float(.*housing' \
    -e 'float(.*contributable' \
    -e 'float(.*hazard' \
    "$BACKEND/routers/" "$BACKEND/services/" "$BACKEND/utils/" \
    2>/dev/null || true)

if [ -n "$FLOAT_HITS" ]; then
    echo "VIOLATIONS FOUND:"
    echo "$FLOAT_HITS"
    EXIT=1
else
    echo "  OK — no float() on monetary values detected"
fi

echo ""
echo "=== Lint Guard: f-string SQL statements ==="
# Match f"UPDATE/INSERT/DELETE/SELECT in router files (high SQL injection risk)
FSQL_HITS=$(grep -rn --include='*.py' \
    -e 'f"UPDATE ' -e "f'UPDATE " \
    -e 'f"INSERT ' -e "f'INSERT " \
    -e 'f"DELETE ' -e "f'DELETE " \
    -e 'f"SELECT ' -e "f'SELECT " \
    -e 'f"""UPDATE ' -e "f'''UPDATE " \
    -e 'f"""INSERT ' -e "f'''INSERT " \
    -e 'f"""DELETE ' -e "f'''DELETE " \
    -e 'f"""SELECT ' -e "f'''SELECT " \
    "$BACKEND/routers/" \
    2>/dev/null | grep -v '#.*noqa' | grep -v '# safe:' || true)

if [ -n "$FSQL_HITS" ]; then
    echo "VIOLATIONS FOUND:"
    echo "$FSQL_HITS"
    EXIT=1
else
    echo "  OK — no f-string SQL detected in routers"
fi

echo ""
if [ $EXIT -eq 0 ]; then
    echo "All lint guards passed."
else
    echo "Lint guard violations found. Please fix before committing."
fi

exit $EXIT
