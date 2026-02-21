#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# AMAN ERP — PostgreSQL Backup Script
#
# Backs up:
#   • The system/shared postgres database
#   • All aman_<company_id> tenant databases
#
# Retention:
#   • Daily backups: last 7 days kept
#   • Weekly backups (Sunday): last 4 weeks kept
#
# Usage:
#   chmod +x scripts/backup_db.sh
#   ./scripts/backup_db.sh                        # Manual run
#
# Cron (daily at 02:00):
#   0 2 * * * /opt/aman/scripts/backup_db.sh >> /var/log/aman_backup.log 2>&1
#
# Environment vars (or .env):
#   POSTGRES_HOST     default: localhost
#   POSTGRES_PORT     default: 5432
#   POSTGRES_USER     default: aman
#   POSTGRES_PASSWORD required
#   BACKUP_DIR        default: /var/backups/aman
#   S3_BUCKET         optional, e.g. s3://my-bucket/aman-backups/
# ═══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

# ── Load .env if present ──────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../backend/.env"
[[ -f "$ENV_FILE" ]] && set -a && source "$ENV_FILE" && set +a

# ── Configuration ─────────────────────────────────────────────────────────────
PG_HOST="${POSTGRES_SERVER:-${POSTGRES_HOST:-localhost}}"
PG_PORT="${POSTGRES_PORT:-5432}"
PG_USER="${POSTGRES_USER:-aman}"
PGPASSWORD="${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}"
export PGPASSWORD

BACKUP_DIR="${BACKUP_DIR:-/var/backups/aman}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
DAY_OF_WEEK="$(date +%u)"   # 1=Mon … 7=Sun
LOG_PREFIX="[$(date '+%Y-%m-%d %H:%M:%S')]"

KEEP_DAILY=7
KEEP_WEEKLY=4

# ── Helpers ───────────────────────────────────────────────────────────────────
log()  { echo "${LOG_PREFIX} $*"; }
warn() { echo "${LOG_PREFIX} WARN: $*" >&2; }
die()  { echo "${LOG_PREFIX} ERROR: $*" >&2; exit 1; }

# ── Preflight checks ─────────────────────────────────────────────────────────
command -v pg_dump    >/dev/null 2>&1 || die "pg_dump not found"
command -v pg_dumpall >/dev/null 2>&1 || die "pg_dumpall not found"
command -v gzip       >/dev/null 2>&1 || die "gzip not found"

mkdir -p "${BACKUP_DIR}/daily" "${BACKUP_DIR}/weekly"

# ── Determine backup type ─────────────────────────────────────────────────────
if [[ "$DAY_OF_WEEK" == "7" ]]; then
    DEST_DIR="${BACKUP_DIR}/weekly"
    log "Weekly backup starting → ${DEST_DIR}"
else
    DEST_DIR="${BACKUP_DIR}/daily"
    log "Daily backup starting → ${DEST_DIR}"
fi

BACKUP_FILE="${DEST_DIR}/aman_full_${TIMESTAMP}.sql.gz"

# ── List all AMAN tenant databases ───────────────────────────────────────────
DATABASES=$(psql -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d postgres \
    -t -A -c "SELECT datname FROM pg_database WHERE datname LIKE 'aman_%' AND datistemplate = false;" \
    2>/dev/null) || die "Cannot connect to PostgreSQL at ${PG_HOST}:${PG_PORT}"

log "Found tenant databases: $(echo $DATABASES | tr '\n' ' ')"

# ── Global roles & settings dump ─────────────────────────────────────────────
GLOBALS_FILE="${DEST_DIR}/aman_globals_${TIMESTAMP}.sql.gz"
log "Dumping globals (roles/settings) → ${GLOBALS_FILE}"
pg_dumpall -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" --globals-only \
    | gzip -9 > "$GLOBALS_FILE"
log "Globals backup complete ($(du -sh "$GLOBALS_FILE" | cut -f1))"

# ── Per-database dump ─────────────────────────────────────────────────────────
SUCCESS_COUNT=0
FAIL_COUNT=0

for DB in $DATABASES; do
    DB_FILE="${DEST_DIR}/${DB}_${TIMESTAMP}.sql.gz"
    log "Backing up database: ${DB} → ${DB_FILE}"
    if pg_dump -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" \
        --format=plain --no-owner --no-acl "$DB" \
        | gzip -9 > "$DB_FILE"; then
        log "  ✓ ${DB} ($(du -sh "$DB_FILE" | cut -f1))"
        ((SUCCESS_COUNT++))
    else
        warn "  ✗ Failed to dump ${DB}"
        rm -f "$DB_FILE"
        ((FAIL_COUNT++))
    fi
done

# ── Full pg_dumpall (all databases in one file) ───────────────────────────────
log "Creating full dump → ${BACKUP_FILE}"
pg_dumpall -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" \
    | gzip -9 > "$BACKUP_FILE"
log "Full dump complete ($(du -sh "$BACKUP_FILE" | cut -f1))"

# ── Retention: prune old backups ──────────────────────────────────────────────
log "Pruning daily backups older than ${KEEP_DAILY} days..."
find "${BACKUP_DIR}/daily" -name "aman_*" -mtime "+${KEEP_DAILY}" -delete

log "Pruning weekly backups older than $((KEEP_WEEKLY * 7)) days..."
find "${BACKUP_DIR}/weekly" -name "aman_*" -mtime "+$((KEEP_WEEKLY * 7))" -delete

# ── Optional: S3 upload ───────────────────────────────────────────────────────
if [[ -n "${S3_BUCKET:-}" ]]; then
    if command -v aws >/dev/null 2>&1; then
        log "Uploading to S3: ${S3_BUCKET}"
        aws s3 cp "$BACKUP_FILE"  "${S3_BUCKET}/full/"
        aws s3 cp "$GLOBALS_FILE" "${S3_BUCKET}/globals/"
        log "S3 upload complete"
    else
        warn "AWS CLI not found; skipping S3 upload"
    fi
fi

# ── Summary ───────────────────────────────────────────────────────────────────
log "════════════════════════════════════════"
log "Backup complete: ${SUCCESS_COUNT} databases backed up, ${FAIL_COUNT} failed"
log "Backup directory: ${DEST_DIR}"
log "Disk usage: $(du -sh "${BACKUP_DIR}" | cut -f1) total"
log "════════════════════════════════════════"

[[ "$FAIL_COUNT" -gt 0 ]] && exit 1 || exit 0
