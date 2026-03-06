#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$ROOT_DIR/logs"

info() { echo "[INFO] $1"; }
warn() { echo "[WARN] $1"; }

stop_pid_file() {
    local pid_file="$1"
    local name="$2"

    if [[ -f "$pid_file" ]]; then
        local pid
        pid="$(cat "$pid_file" 2>/dev/null || true)"
        if [[ -n "${pid:-}" ]] && kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
            sleep 1
            if kill -0 "$pid" 2>/dev/null; then
                kill -9 "$pid" 2>/dev/null || true
            fi
            info "$name stopped (PID: $pid)"
        else
            warn "$name PID file exists but process is not running"
        fi
        rm -f "$pid_file"
    else
        warn "$name PID file not found"
    fi
}

info "Stopping AMAN ERP local services..."

# Stop frontend/backend by PID files first
stop_pid_file "$LOG_DIR/frontend.pid" "Frontend"
stop_pid_file "$LOG_DIR/backend.pid" "Backend"

# Fallback kill in case PID files are missing/outdated
pkill -f "uvicorn main:app" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
pkill -f "npm run dev" 2>/dev/null || true

# Stop Redis only if we started it from start-local.sh
if [[ -f "$LOG_DIR/redis.started_by_script" ]]; then
    if command -v redis-cli >/dev/null 2>&1; then
        redis-cli shutdown >/dev/null 2>&1 || true
    fi
    if [[ -f "$LOG_DIR/redis-local.pid" ]]; then
        pid="$(cat "$LOG_DIR/redis-local.pid" 2>/dev/null || true)"
        [[ -n "${pid:-}" ]] && kill "$pid" 2>/dev/null || true
        rm -f "$LOG_DIR/redis-local.pid"
    fi
    rm -f "$LOG_DIR/redis.started_by_script"
    info "Redis stopped (started-by-script instance)"
else
    info "Redis left running (not started by this script)"
fi

info "Local system stop completed."

if ss -ltn | grep -q ':8000 '; then
    warn "Backend still listening on :8000"
fi

if ss -ltn | grep -q ':5173 '; then
    warn "Frontend still listening on :5173"
fi
