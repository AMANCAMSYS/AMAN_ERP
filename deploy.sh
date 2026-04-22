#!/bin/bash
# ═════════════════════════════════════════════════════════════════════════════
# deploy.sh — Manual CD trigger for amanerp.me
#
# Usage:
#   ./deploy.sh               # uses env vars or prompts
#   DEPLOY_PASSWORD=xxx ./deploy.sh
# ═════════════════════════════════════════════════════════════════════════════

set -e

DEPLOY_HOST="${DEPLOY_HOST:-64.225.49.118}"
DEPLOY_USER="${DEPLOY_USER:-root}"
DEPLOY_PASSWORD="${DEPLOY_PASSWORD:-}"

if [ -z "$DEPLOY_PASSWORD" ]; then
  echo "🔐 Enter server root password:"
  read -s DEPLOY_PASSWORD
fi

echo ""
echo "🚀 Deploying to $DEPLOY_USER@$DEPLOY_HOST"
echo ""

sshpass -p "$DEPLOY_PASSWORD" ssh -o StrictHostKeyChecking=accept-new \
  "$DEPLOY_USER@$DEPLOY_HOST" <<'SSH_SCRIPT'
set -e
cd /opt/aman

echo "=== 1. Pull latest code ==="
git fetch origin main
git reset --hard origin/main
echo "✅ Deployed: $(git log --oneline -1)"

echo ""
echo "=== 2. Rebuild Docker images (uses layer cache) ==="
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
  build backend frontend worker 2>&1 | grep -E "^(Step|Successfully built|#)" || true

echo ""
echo "=== 3. Restart services ==="
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
  up -d --no-deps backend frontend worker

echo ""
echo "=== 4. Health check (waiting for backend) ==="
for i in 1 2 3 4 5 6; do
  sleep 10
  if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend healthy after ${i}0s"
    break
  fi
  echo "   Waiting... attempt $i/6"
  if [ "$i" = "6" ]; then
    echo "❌ ERROR: backend not healthy after 60s"
    echo ""
    echo "Docker Logs (last 30 lines):"
    docker logs --tail 30 aman_backend
    exit 1
  fi
done

echo ""
echo "=== 5. Verify health ==="
curl -s http://localhost:8000/health | python3 -m json.tool

echo ""
echo "✅ Deploy complete!"
SSH_SCRIPT

echo ""
echo "✅ All systems deployed and healthy"
