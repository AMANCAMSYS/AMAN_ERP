#!/usr/bin/env bash
# OPS-C2 — Restore a single AMAN ERP database from a backup dump.
# Usage:
#   scripts/restore_postgres.sh <dump.sql.gz> [target_db_name]
# If target_db_name is omitted, the DB name is inferred from the filename.
#
# Safety:
#   * Refuses to restore into a DB that does not exist yet unless
#     AMAN_RESTORE_CREATE=1 is set.
#   * Does NOT drop the existing DB — use `dropdb` manually first if you
#     want a truly clean restore.
#
set -euo pipefail

: "${POSTGRES_SERVER:=localhost}"
: "${POSTGRES_PORT:=5432}"
: "${POSTGRES_USER:=aman_admin}"

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <dump.sql.gz> [target_db_name]" >&2
    exit 1
fi

dump="$1"
target="${2:-$(basename "${dump}" .sql.gz)}"

if [[ ! -f "${dump}" ]]; then
    echo "[restore] ERROR: dump not found: ${dump}" >&2
    exit 2
fi

exists=$(psql -h "${POSTGRES_SERVER}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" \
    -At -d postgres -c "SELECT 1 FROM pg_database WHERE datname = '${target}'")

if [[ -z "${exists}" ]]; then
    if [[ "${AMAN_RESTORE_CREATE:-0}" = "1" ]]; then
        echo "[restore] creating database ${target}"
        createdb -h "${POSTGRES_SERVER}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" "${target}"
    else
        echo "[restore] ERROR: database ${target} does not exist." >&2
        echo "         Set AMAN_RESTORE_CREATE=1 to auto-create it." >&2
        exit 3
    fi
fi

echo "[restore] restoring ${dump} -> ${target}"
gunzip -c "${dump}" | psql -h "${POSTGRES_SERVER}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${target}" --set ON_ERROR_STOP=1 --quiet

echo "[restore] done: ${target}"
