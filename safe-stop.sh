#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# AMAN ERP — Safe Stop Script
# ⚠️  استخدم هذا دائماً عند إيقاف السيرفر - لا تستخدم 'docker compose down -v'
# ═══════════════════════════════════════════════════════════════════════════════
set -euo pipefail
cd /opt/aman

COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

echo '💾 Taking backup before stopping...'
bash /opt/aman/scripts/backup.sh || echo '⚠️  Backup failed — continuing with stop'

echo ''
echo '⏹️  Stopping all services (data preserved)...'
$COMPOSE stop

echo ''
echo '✅ All services stopped safely. Data is preserved in Docker volumes.'
echo '   To restart: cd /opt/aman && bash safe-start.sh'
