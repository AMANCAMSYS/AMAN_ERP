#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# AMAN ERP — Automated Database Backup Script
# OPS-003: pg_dump all system + company databases, compress, rotate
#
# Usage:
#   ./scripts/backup.sh                         # backup to ./backups/
#   BACKUP_DIR=/mnt/nfs/backups ./scripts/backup.sh
#   RETENTION_DAYS=7 ./scripts/backup.sh        # keep last 7 days
#   S3_BUCKET=s3://my-bucket/aman ./scripts/backup.sh
#
# Cron example (daily at 02:00):
#   0 2 * * * /opt/aman/scripts/backup.sh >> /var/log/aman-backup.log 2>&1
# ═══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
BACKUP_DIR="${BACKUP_DIR:-$(dirname "$0")/../backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
S3_BUCKET="${S3_BUCKET:-}"                          # Empty = no S3 upload
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_PREFIX="[AMAN-BACKUP]"

# Database connection (reads from .pgpass or env)
PGHOST="${POSTGRES_SERVER:-localhost}"
PGPORT="${POSTGRES_PORT:-5432}"
PGUSER="${POSTGRES_USER:-aman}"
DB_MAIN="${POSTGRES_DB:-postgres}"

# ── Helpers ───────────────────────────────────────────────────────────────────
info()  { echo "$LOG_PREFIX $(date '+%Y-%m-%d %H:%M:%S') INFO  $*"; }
warn()  { echo "$LOG_PREFIX $(date '+%Y-%m-%d %H:%M:%S') WARN  $*" >&2; }
error() { echo "$LOG_PREFIX $(date '+%Y-%m-%d %H:%M:%S') ERROR $*" >&2; }

cleanup_on_error() {
    error "Backup failed! Cleaning partial files..."
    rm -f "${BACKUP_DIR}/${TIMESTAMP}"_*.sql.gz 2>/dev/null || true
    exit 1
}
trap cleanup_on_error ERR

# ── Verify tools ──────────────────────────────────────────────────────────────
for cmd in pg_dump psql gzip; do
    if ! command -v "$cmd" &>/dev/null; then
        error "Required command '$cmd' not found. Install PostgreSQL client tools."
        exit 1
    fi
done

# ── Create backup directory ──────────────────────────────────────────────────
mkdir -p "$BACKUP_DIR"
info "Backup directory: $BACKUP_DIR"

# ── 1. Backup system database ────────────────────────────────────────────────
SYSTEM_DUMP="${BACKUP_DIR}/${TIMESTAMP}_system.sql.gz"
info "Backing up system database: $DB_MAIN → $SYSTEM_DUMP"
pg_dump -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" \
    --no-owner --no-privileges --if-exists --clean \
    "$DB_MAIN" | gzip -9 > "$SYSTEM_DUMP"
SIZE_SYS=$(du -sh "$SYSTEM_DUMP" | cut -f1)
info "  ✅ System DB backup complete ($SIZE_SYS)"

# ── 2. Discover and backup all company databases ─────────────────────────────
COMPANY_DBS=$(psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$DB_MAIN" \
    -t -A -c "SELECT database_name FROM system_companies WHERE status = 'active'" 2>/dev/null || true)

if [[ -z "$COMPANY_DBS" ]]; then
    # Fallback: discover by naming convention
    COMPANY_DBS=$(psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$DB_MAIN" \
        -t -A -c "SELECT datname FROM pg_database WHERE datname LIKE 'aman_%' AND datistemplate = false" 2>/dev/null || true)
fi

COMPANY_COUNT=0
COMPANY_ERRORS=0

for db_name in $COMPANY_DBS; do
    DUMP_FILE="${BACKUP_DIR}/${TIMESTAMP}_${db_name}.sql.gz"
    info "Backing up company database: $db_name"
    if pg_dump -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" \
        --no-owner --no-privileges --if-exists --clean \
        "$db_name" 2>/dev/null | gzip -9 > "$DUMP_FILE"; then
        SIZE=$(du -sh "$DUMP_FILE" | cut -f1)
        info "  ✅ $db_name ($SIZE)"
        COMPANY_COUNT=$((COMPANY_COUNT + 1))
    else
        warn "  ⚠️ Failed to backup $db_name — skipping"
        rm -f "$DUMP_FILE"
        COMPANY_ERRORS=$((COMPANY_ERRORS + 1))
    fi
done

info "Company databases backed up: $COMPANY_COUNT (errors: $COMPANY_ERRORS)"

# ── 3. Create combined manifest ──────────────────────────────────────────────
MANIFEST="${BACKUP_DIR}/${TIMESTAMP}_manifest.txt"
{
    echo "AMAN ERP Backup Manifest"
    echo "========================"
    echo "Timestamp:  $TIMESTAMP"
    echo "Host:       $PGHOST:$PGPORT"
    echo "System DB:  $DB_MAIN"
    echo "Companies:  $COMPANY_COUNT"
    echo "Errors:     $COMPANY_ERRORS"
    echo ""
    echo "Files:"
    ls -lh "${BACKUP_DIR}/${TIMESTAMP}"_*.sql.gz 2>/dev/null
} > "$MANIFEST"

# ── 4. Upload to S3 (optional) ───────────────────────────────────────────────
if [[ -n "$S3_BUCKET" ]]; then
    if command -v aws &>/dev/null; then
        info "Uploading to S3: $S3_BUCKET"
        aws s3 cp "${BACKUP_DIR}/" "$S3_BUCKET/${TIMESTAMP}/" \
            --recursive \
            --include "${TIMESTAMP}_*" \
            --storage-class STANDARD_IA \
            --quiet
        info "  ✅ S3 upload complete"
    else
        warn "aws CLI not found — skipping S3 upload"
    fi
fi

# ── 5. Rotate old backups ────────────────────────────────────────────────────
info "Rotating backups older than $RETENTION_DAYS days..."
DELETED=$(find "$BACKUP_DIR" -name "*.sql.gz" -mtime +"$RETENTION_DAYS" -delete -print | wc -l)
find "$BACKUP_DIR" -name "*_manifest.txt" -mtime +"$RETENTION_DAYS" -delete 2>/dev/null || true
info "  Deleted $DELETED old backup files"

# ── Summary ──────────────────────────────────────────────────────────────────
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
info "═══════════════════════════════════════════════════"
info "Backup complete!"
info "  Files:     $(ls "${BACKUP_DIR}/${TIMESTAMP}"_*.sql.gz 2>/dev/null | wc -l) dumps + manifest"
info "  Total dir: $TOTAL_SIZE"
info "  Retention: $RETENTION_DAYS days"
info "═══════════════════════════════════════════════════"
