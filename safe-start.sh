#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# AMAN ERP — Safe Start Script
# ═══════════════════════════════════════════════════════════════════════════════
cd /opt/aman
echo '🚀 Starting AMAN ERP...'
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
echo 'Waiting for services to be ready (30s)...'
sleep 30
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
echo ''
curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo 'Health check still starting...'
