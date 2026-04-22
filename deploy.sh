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

OLD_COMMIT="$(git rev-parse HEAD)"

echo "=== 1. Pull latest code ==="
git fetch origin main
git reset --hard origin/main
NEW_COMMIT="$(git rev-parse HEAD)"
echo "✅ Deployed: $(git log --oneline -1)"

echo ""
echo "=== 1.1 Detect changed files ==="
CHANGED_FILES="$(git diff --name-only "$OLD_COMMIT" "$NEW_COMMIT" || true)"
if [ -z "$CHANGED_FILES" ]; then
  echo "No file changes between $OLD_COMMIT and $NEW_COMMIT"
fi

NEED_BACKEND=0
NEED_FRONTEND=0

# Backend/worker image is affected by backend code, migrations, or compose wiring.
if echo "$CHANGED_FILES" | grep -Eq '^(backend/|alembic/|migrations/|docker-compose\.yml|docker-compose\.prod\.yml|deploy\.sh)'; then
  NEED_BACKEND=1
fi

# Frontend image is affected by frontend code or compose wiring.
if echo "$CHANGED_FILES" | grep -Eq '^(frontend/|docker-compose\.yml|docker-compose\.prod\.yml)'; then
  NEED_FRONTEND=1
fi

echo "Plan: backend=$NEED_BACKEND frontend=$NEED_FRONTEND"

echo ""
echo "=== 2. Rebuild Docker images (affected services only) ==="
BUILD_SERVICES=""
if [ "$NEED_BACKEND" -eq 1 ]; then
  BUILD_SERVICES="$BUILD_SERVICES backend worker"
fi
if [ "$NEED_FRONTEND" -eq 1 ]; then
  BUILD_SERVICES="$BUILD_SERVICES frontend"
fi

if [ -n "$BUILD_SERVICES" ]; then
  docker compose -f docker-compose.yml -f docker-compose.prod.yml \
    build $BUILD_SERVICES 2>&1 | grep -E "^(Step|Successfully built|#)" || true
else
  echo "No runtime service changes detected — skipping image build/restart."
fi

echo ""
if [ "$NEED_BACKEND" -eq 1 ]; then
  echo "=== 3. Restart backend + worker first (keep frontend serving) ==="
  docker compose -f docker-compose.yml -f docker-compose.prod.yml \
    up -d --no-deps backend worker

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
else
  echo "=== 3/4. Backend unchanged — skip backend restart ==="
fi

echo ""
if [ "$NEED_FRONTEND" -eq 1 ]; then
  echo "=== 5. Restart frontend after backend is healthy ==="
  docker compose -f docker-compose.yml -f docker-compose.prod.yml \
    up -d --no-deps frontend

  echo "Waiting for frontend to be reachable..."
  for i in 1 2 3 4 5 6; do
    sleep 5
    if curl -sf http://localhost/ > /dev/null 2>&1; then
      echo "✅ Frontend reachable after ${i}x5s"
      break
    fi
    echo "   Waiting frontend... attempt $i/6"
    if [ "$i" = "6" ]; then
      echo "❌ ERROR: frontend not reachable after 30s"
      docker logs --tail 40 aman_frontend || true
      exit 1
    fi
  done
else
  echo "=== 5. Frontend unchanged — skip frontend restart ==="
fi

echo ""
echo "=== 6. Verify health ==="
curl -s http://localhost:8000/health | python3 -m json.tool

echo ""
echo "✅ Deploy complete!"
SSH_SCRIPT

echo ""
echo "✅ All systems deployed and healthy"
