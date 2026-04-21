#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# Ops-20: Render nginx/production.conf.template -> nginx/production.conf
#
# Usage:
#   AMAN_SERVER_NAME=erp.example.com ./scripts/render_nginx_conf.sh
#
# Requires envsubst (from gettext-base / gettext on most distros).
# ═══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

: "${AMAN_SERVER_NAME:?AMAN_SERVER_NAME must be set (e.g. erp.example.com)}"

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT_DIR/nginx/production.conf.template"
DST="$ROOT_DIR/nginx/production.conf"

if [[ ! -f "$SRC" ]]; then
    echo "template not found: $SRC" >&2
    exit 1
fi

if ! command -v envsubst >/dev/null 2>&1; then
    echo "envsubst not installed. apt-get install gettext-base" >&2
    exit 1
fi

# Only substitute our variable; leave all other $... (like nginx $host) alone.
envsubst '${AMAN_SERVER_NAME}' < "$SRC" > "$DST"
echo "rendered: $DST (AMAN_SERVER_NAME=$AMAN_SERVER_NAME)"
