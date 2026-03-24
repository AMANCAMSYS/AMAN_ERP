#!/usr/bin/env bash
set -euo pipefail

# Operational checklist helper for secrets rotation.
# This script does NOT rotate remote secrets automatically.
# It validates local readiness and prints exact next actions.

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
BACKEND_ENV="$ROOT_DIR/backend/.env"
BASE_URL="${AMAN_BASE_URL:-http://localhost:8000}"

echo "== AMAN Secrets Rotation Checklist =="
echo "Project: $ROOT_DIR"
echo "API Base URL: $BASE_URL"

if [[ ! -f "$BACKEND_ENV" ]]; then
  echo "[ERROR] backend/.env not found: $BACKEND_ENV"
  exit 1
fi

echo "[1/5] Checking required keys in backend/.env"
required_keys=(
  "POSTGRES_PASSWORD"
  "SECRET_KEY"
  "REDIS_PASSWORD"
)
for key in "${required_keys[@]}"; do
  if ! grep -qE "^${key}=" "$BACKEND_ENV"; then
    echo "[ERROR] Missing key: $key"
    exit 1
  fi
done

echo "[2/5] Checking for weak/default secret patterns"
if grep -qiE '^SECRET_KEY=(secret|changeme|default|123|test|admin)$' "$BACKEND_ENV"; then
  echo "[ERROR] Weak SECRET_KEY detected in backend/.env"
  exit 1
fi

echo "[3/5] Suggested new values"
echo "- New JWT SECRET_KEY:"
python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(64))
PY

echo "- New strong passwords:"
python3 - <<'PY'
import secrets, string
chars = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
for name in ["POSTGRES_PASSWORD", "REDIS_PASSWORD"]:
    pwd = ''.join(secrets.choice(chars) for _ in range(32))
    print(f"{name}={pwd}")
PY

echo "[4/5] Manual rotation targets (must be updated)"
echo "- GitHub Secrets: DEPLOY_SSH_KEY / PROD_ENV_FILE / any API keys"
echo "- Server env files: /opt/aman/backend/.env and /opt/aman/.env"
echo "- Any external providers (mail/SMS/webhooks)"

echo "[5/5] Post-rotation verification commands"
cat <<'CMD'
# Deploy updated secrets
# (trigger CI deploy or run your approved deployment path)

# Verify backend health
curl -s "$BASE_URL/health"

# Verify auth still works with a fresh token
curl -s -X POST "$BASE_URL/api/auth/login" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=<user>&password=<pass>&company_code=<company_code>'
CMD

echo "Checklist complete. Rotation execution remains a controlled manual operation."
