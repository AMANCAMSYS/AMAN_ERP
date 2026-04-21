#!/usr/bin/env bash
# OPS-C2 — Automated PostgreSQL backup for AMAN ERP.
# Dumps the system DB and every per-tenant DB (aman_*) into a timestamped
# folder, gzips each, and prunes dumps older than $AMAN_BACKUP_KEEP_DAYS.
#
# Env vars (with defaults):
#   POSTGRES_SERVER   (localhost)
#   POSTGRES_PORT     (5432)
#   POSTGRES_USER     (aman_admin)
#   PGPASSFILE        ($HOME/.pgpass — required; password is never on CLI)
#   AMAN_BACKUP_DIR   (/var/backups/aman)
#   AMAN_BACKUP_KEEP_DAYS (14)
#
# Cron suggestion:
#   0 2 * * *  /opt/aman/scripts/backup_postgres.sh >> /var/log/aman-backup.log 2>&1
#
# Restore a single tenant dump:
#   gunzip -c aman_<company_id>.sql.gz | psql -h host -U user -d aman_<company_id>
#
set -euo pipefail

: "${POSTGRES_SERVER:=localhost}"
: "${POSTGRES_PORT:=5432}"
: "${POSTGRES_USER:=aman_admin}"
: "${AMAN_BACKUP_DIR:=/var/backups/aman}"
: "${AMAN_BACKUP_KEEP_DAYS:=14}"

stamp="$(date -u +%Y%m%dT%H%M%SZ)"
dest="${AMAN_BACKUP_DIR}/${stamp}"
mkdir -p "${dest}"

echo "[aman-backup] start stamp=${stamp} dest=${dest}"

if [[ -z "${PGPASSFILE:-}" && ! -f "${HOME}/.pgpass" ]]; then
    echo "[aman-backup] ERROR: no PGPASSFILE and no ~/.pgpass — aborting" >&2
    exit 2
fi

# List every database that belongs to this ERP installation.
#   aman_system  -> system DB
#   aman_*       -> per-tenant DBs
dbs=$(psql -h "${POSTGRES_SERVER}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" \
    -At -d postgres \
    -c "SELECT datname FROM pg_database WHERE datname = 'aman_system' OR datname LIKE 'aman\\_%' ESCAPE '\\' ORDER BY 1")

if [[ -z "${dbs}" ]]; then
    echo "[aman-backup] WARN: no aman_* databases found — nothing to back up"
    exit 0
fi

# Dump each DB. --clean --if-exists makes the dump self-restorable.
for db in ${dbs}; do
    out="${dest}/${db}.sql.gz"
    echo "[aman-backup] dumping ${db} -> ${out}"
    pg_dump -h "${POSTGRES_SERVER}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" \
        --format=plain --no-owner --no-privileges --clean --if-exists \
        "${db}" | gzip -9 > "${out}"
done

# Write a manifest for restore tooling.
(
    echo "# AMAN ERP backup manifest"
    echo "stamp=${stamp}"
    echo "host=${POSTGRES_SERVER}"
    echo "user=${POSTGRES_USER}"
    echo "databases:"
    for db in ${dbs}; do
        size=$(stat -c%s "${dest}/${db}.sql.gz" 2>/dev/null || echo 0)
        echo "  - { name: ${db}, bytes: ${size} }"
    done
) > "${dest}/MANIFEST.yml"

# Prune old backups.
if [[ "${AMAN_BACKUP_KEEP_DAYS}" -gt 0 ]]; then
    echo "[aman-backup] pruning dumps older than ${AMAN_BACKUP_KEEP_DAYS} days"
    find "${AMAN_BACKUP_DIR}" -mindepth 1 -maxdepth 1 -type d \
        -mtime +"${AMAN_BACKUP_KEEP_DAYS}" -print -exec rm -rf {} +
fi

echo "[aman-backup] done stamp=${stamp}"
