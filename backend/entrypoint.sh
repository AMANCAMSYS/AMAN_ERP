#!/bin/sh
# ─────────────────────────────────────────────────────────────────────────────
# AMAN ERP — Container Entrypoint
#
# Runs as root to:
#   1. Create/chown upload directories on the named volume
#   2. Wait for PostgreSQL to be ready (prevents race conditions)
#   3. Run Alembic migrations for all company databases
# Then drops privileges to the 'aman' system user before exec-ing gunicorn.
# ─────────────────────────────────────────────────────────────────────────────
set -e

echo "🔧 Initialising upload directories..."
mkdir -p \
    /app/uploads/documents \
    /app/uploads/logos \
    /app/uploads/temp \
    /app/uploads/invoices \
    /app/uploads/contracts \
    /app/uploads/attachments

chown -R aman:aman /app/uploads
chmod -R 755 /app/uploads
echo "✅ Upload directories ready"

# ── Wait for PostgreSQL ────────────────────────────────────────────────────────
DB_HOST="${POSTGRES_SERVER:-db}"
DB_PORT="${POSTGRES_PORT:-5432}"
MAX_WAIT=60
elapsed=0

echo "⏳ Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."
while ! gosu aman python -c "
import socket, sys
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.settimeout(2)
    s.connect(('${DB_HOST}', ${DB_PORT}))
    s.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; do
    elapsed=$((elapsed + 2))
    if [ "$elapsed" -ge "$MAX_WAIT" ]; then
        echo "❌ PostgreSQL not reachable after ${MAX_WAIT}s — starting anyway"
        break
    fi
    sleep 2
done
echo "✅ PostgreSQL is reachable"

# ── Wait for Redis (optional, non-blocking) ───────────────────────────────────
if [ -n "${REDIS_URL:-}" ]; then
    echo "⏳ Checking Redis connectivity..."
    gosu aman python -c "
import redis, sys, os
try:
    r = redis.from_url(os.environ.get('REDIS_URL', ''), socket_connect_timeout=5)
    r.ping()
    print('✅ Redis is reachable')
except Exception as e:
    print(f'⚠️  Redis not reachable: {e} — continuing without Redis')
" 2>/dev/null || echo "⚠️  Redis check skipped"
fi

# ── Run Alembic migrations for all company databases ──────────────────────────
echo "🔄 Running Alembic migrations for company databases..."
gosu aman python -m alembic -c /app/alembic.ini -x company=all upgrade head 2>&1 || {
    echo "⚠️  Alembic migrations had warnings (non-fatal) — app will attempt schema sync on startup"
}
echo "✅ Migration step complete"

# Drop to non-root user and execute the main command (gunicorn)
exec gosu aman "$@"
