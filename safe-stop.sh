#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# AMAN ERP — Safe Stop Script
# ⚠️  استخدم هذا دائماً عند إيقاف السيرفر - لا تستخدم 'docker compose down -v'
# ═══════════════════════════════════════════════════════════════════════════════
cd /opt/aman

echo '💾 Taking backup before stopping...'
bash /opt/aman/scripts/backup.sh

echo ''
echo '⏹️  Stopping all services (data preserved)...'
docker compose -f docker-compose.yml -f docker-compose.prod.yml stop

echo ''
echo '✅ All services stopped safely. Data is preserved in Docker volumes.'
echo '   To restart: cd /opt/aman && bash safe-start.sh'
