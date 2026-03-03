#!/bin/sh
# ─────────────────────────────────────────────────────────────────────────────
# AMAN ERP — Container Entrypoint
#
# Runs as root to initialise upload directories on the named volume,
# then drops privileges to the 'aman' system user before exec-ing gunicorn.
# This solves the race between Dockerfile-created dirs and Docker-mounted
# named volumes that arrive root-owned and override Dockerfile content.
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

# Drop to non-root user and execute the main command (gunicorn)
exec gosu aman "$@"
