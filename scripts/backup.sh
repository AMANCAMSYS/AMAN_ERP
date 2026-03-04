#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# AMAN ERP — Automated Database Backup Script (Docker-aware)
# OPS-003: pg_dump all system + company databases, compress, rotate
#
# Usage:
#   ./scripts/backup.sh                         # backup to /opt/aman/backups/
#   BACKUP_DIR=/mnt/nfs/backups ./scripts/backup.sh
#   RETENTION_DAYS=7 ./scripts/backup.sh        # keep last 7 days
#
# Cron example (daily at 02:00):
#   0 2 * * * /opt/aman/scripts/backup.sh >> /var/log/aman-backup.log 2>&1
# ═══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
BACKUP_DIR="${BACKUP_DIR:-/opt/aman/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_PREFIX="[AMAN-BACKUP]"
PGUSER="${POSTGRES_USER:-aman}"

info()  { echo "$LOG_PREFIX $(date '+%Y-%m-%d %H:%M:%S') INFO  $*"; }
warn()  { echo "$LOG_PREFIX $(date '+%Y-%m-%d %H:%M:%S') WARN  $*" >&2; }
error() { echo "$LOG_PREFIX $(date '+%Y-%m-%d %H:%M:%S') ERROR $*" >&2; }

cleanup_on_error() {
    error "Backup failed! Cleaning partial files..."
    rm -f "${BACKUP_DIR}/${TIMESTAMP}"_*.sql.gz 2>/dev/null || true
    exit 1
}
trap cleanup_on_error ERR

# ── Verify database container is running ─────────────────────────────────────
if ! docker inspect -f '{{.State.Running}}' aman_db 2>/dev/null | grep -q true; then
    error "Database container 'aman_db' is not running! Cannot backup."
    exit 1
fi

mkdir -p "$BACKUP_DIR"
info "=== Starting AMAN ERP Backup === Timestamp: $TIMESTAMP"
info "Backup directory: $BACKUP_DIR"

# ── 1. Backup system database ────────────────────────────────────────────────
SYSTEM_DUMP="${BACKUP_DIR}/${TIMESTAMP}_system.sql.gz"
info "Backing up system database (postgres)..."
docker exec aman_db pg_dump -U "$PGUSER" --no-owner --no-privileges --clean --if-exists postgres \
    | gzip -9 > "$SYSTEM_DUMP"
info "  System DB: $(du -sh $SYSTEM_DUMP | cut -f1)"

# ── 2. Backup all active company databases ───────────────────────────────────
info "Fetching active company databases..."
COMPANY_DBS=$(docker exec aman_db psql -U "$PGUSER" -d postgres -t -A \
    -c "SELECT database_name FROM system_companies WHERE status='active';" 2>/dev/null || echo "")

if [ -z "$COMPANY_DBS" ]; then
    warn "No active company databases found."
else
    COMPANY_COUNT=0
    for DB_NAME in $COMPANY_DBS; do
        DB_NAME=$(echo "$DB_NAME" | tr -d '[:space:]')
        [ -z "$DB_NAME" ] && continue
        COMPANY_DUMP="${BACKUP_DIR}/${TIMESTAMP}_${DB_NAME}.sql.gz"
        info "Backing up company DB: $DB_NAME..."
        docker exec aman_db pg_dump -U "$PGUSER" --no-owner --no-privileges --clean --if-exists "$DB_NAME" \
            | gzip -9 > "$COMPANY_DUMP"
        info "  $DB_NAME: $(du -sh $COMPANY_DUMP | cut -f1)"
        COMPANY_COUNT=$((COMPANY_COUNT + 1))
    done
    info "Company databases backed up: $COMPANY_COUNT"
fi

# ── 3. Rotate old backups ────────────────────────────────────────────────────
info "Removing backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name '*.sql.gz' -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
BACKUP_COUNT=$(ls "$BACKUP_DIR"/*.sql.gz 2>/dev/null | wc -l || echo 0)
info "Total backup files kept: $BACKUP_COUNT"

# ── 4. Summary ───────────────────────────────────────────────────────────────
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1 || echo 'unknown')
info "=== Backup Complete === Total size: $TOTAL_SIZE ==="
