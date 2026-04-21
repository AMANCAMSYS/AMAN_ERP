#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# AMAN ERP — Safe Start Script (Production Docker)
# ═══════════════════════════════════════════════════════════════════════════════
set -euo pipefail
cd /opt/aman

COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

echo '🚀 Starting AMAN ERP...'

# 1. Ensure .env files exist
if [[ ! -f .env ]]; then
    echo '❌ Missing .env at /opt/aman/.env — copy from .env.example and fill in values'
    exit 1
fi
if [[ ! -f backend/.env ]]; then
    echo '❌ Missing backend/.env — copy from backend/.env.example and fill in values'
    exit 1
fi

# 2. Start infrastructure first (db + redis)
echo '🗄️  Starting database and Redis...'
$COMPOSE up -d db redis
echo 'Waiting for database to be healthy...'
$COMPOSE exec -T db sh -c 'until pg_isready -U ${POSTGRES_USER:-aman}; do sleep 2; done' 2>/dev/null
echo '✅ Database is ready'

# 3. Start all application services
echo '🔧 Starting backend + frontend + monitoring...'
$COMPOSE up -d

# 4. Wait for backend health
echo 'Waiting for backend to be healthy (up to 120s)...'
MAX_WAIT=120
elapsed=0
while (( elapsed < MAX_WAIT )); do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is healthy (${elapsed}s)"
        break
    fi
    sleep 3
    elapsed=$((elapsed + 3))
done
if (( elapsed >= MAX_WAIT )); then
    echo "⚠️  Backend health check timed out after ${MAX_WAIT}s — check logs:"
    echo "   $COMPOSE logs --tail=50 backend"
fi

# 5. Show status
echo ''
echo '═══════════════════════════════════════════'
$COMPOSE ps
echo '═══════════════════════════════════════════'
echo ''
curl -s http://localhost:8000/health 2>/dev/null | python3 -m json.tool 2>/dev/null || echo 'Health endpoint not yet responding'
echo ''
echo '✅ AMAN ERP started. Logs: docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f'
