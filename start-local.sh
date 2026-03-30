#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
VENV_DIR="$ROOT_DIR/.venv"
LOG_DIR="$ROOT_DIR/logs"

mkdir -p "$LOG_DIR"

info() { echo "[INFO] $1"; }
warn() { echo "[WARN] $1"; }
err()  { echo "[ERROR] $1"; }

is_port_listening() {
    local port="$1"
    ss -ltn | grep -q ":${port} "
}

wait_for_port() {
    local port="$1"
    local name="$2"
    local timeout_seconds="${3:-30}"
    local elapsed=0

    while (( elapsed < timeout_seconds )); do
        if is_port_listening "$port"; then
            return 0
        fi
        sleep 1
        elapsed=$((elapsed + 1))
    done

    err "$name did not open port $port within ${timeout_seconds}s"
    return 1
}

start_postgres_if_needed() {
    if command -v pg_isready >/dev/null 2>&1 && pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
        info "PostgreSQL is already running on localhost:5432"
        return
    fi

    warn "PostgreSQL is not running. Trying to start it..."
    if command -v systemctl >/dev/null 2>&1; then
        sudo systemctl start postgresql 2>/dev/null || systemctl start postgresql 2>/dev/null || true
    fi
    if command -v service >/dev/null 2>&1; then
        sudo service postgresql start 2>/dev/null || service postgresql start 2>/dev/null || true
    fi

    if command -v pg_isready >/dev/null 2>&1 && pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
        info "PostgreSQL started successfully"
    else
        err "PostgreSQL is still not reachable on localhost:5432"
        err "Start PostgreSQL manually, then run this script again."
        exit 1
    fi
}

start_redis_if_available() {
    if command -v redis-cli >/dev/null 2>&1 && redis-cli ping >/dev/null 2>&1; then
        info "Redis is already running"
        return
    fi

    # If redis-cli is unavailable, a listening 6379 usually means Redis is already up.
    if is_port_listening 6379; then
        info "Port 6379 is already in use; assuming Redis is available"
        return
    fi

    if command -v redis-server >/dev/null 2>&1; then
        info "Starting local Redis..."
        redis-server --daemonize yes \
            --bind 127.0.0.1 \
            --port 6379 \
            --pidfile "$LOG_DIR/redis-local.pid" \
            --logfile "$LOG_DIR/redis.log" >/dev/null 2>&1 || true

        sleep 1
        if is_port_listening 6379; then
            info "Redis started successfully"
            echo "daemon" > "$LOG_DIR/redis.started_by_script"
        else
            warn "Could not start Redis daemon. Backend will continue using fallback mode if supported."
        fi
        return
    fi

    if command -v docker >/dev/null 2>&1; then
        info "redis-server not installed. Starting Redis using Docker fallback..."

        if docker ps -a --format '{{.Names}}' | grep -qx "aman_local_redis"; then
            docker start aman_local_redis >/dev/null 2>&1 || true
        else
            docker run -d --name aman_local_redis -p 6379:6379 redis:7-alpine >/dev/null 2>&1 || true
        fi

        sleep 1
        if is_port_listening 6379; then
            info "Redis started successfully (Docker fallback)"
            echo "docker" > "$LOG_DIR/redis.started_by_script"
        else
            warn "Could not start Redis with Docker fallback. Backend will continue using fallback mode if supported."
        fi
        return
    fi

    warn "redis-server not installed and Docker unavailable. System will run with in-memory fallback."
}

start_backend() {
    if is_port_listening 8000; then
        info "Backend already running on :8000"
        return
    fi

    if [[ ! -f "$BACKEND_DIR/.env" ]]; then
        err "Missing backend/.env file"
        err "Create it first (you can copy from backend/.env.example)."
        exit 1
    fi

    local -a backend_cmd
    if [[ -x "$VENV_DIR/bin/python" ]] && "$VENV_DIR/bin/python" -c "import uvicorn" >/dev/null 2>&1; then
        backend_cmd=("$VENV_DIR/bin/python" "-m" "uvicorn")
        info "Using virtual environment Python for backend"
    elif /usr/bin/python3 -c "import uvicorn" >/dev/null 2>&1; then
        backend_cmd=("/usr/bin/python3" "-m" "uvicorn")
        warn "Virtual environment not required; using system Python for backend"
    elif command -v uvicorn >/dev/null 2>&1; then
        backend_cmd=("uvicorn")
        warn "Using uvicorn from PATH"
    else
        err "Uvicorn is not available in .venv, system Python, or PATH"
        err "Install backend requirements and retry."
        exit 1
    fi

    info "Starting backend (FastAPI/Uvicorn)..."
    (
        cd "$BACKEND_DIR"
        nohup "${backend_cmd[@]}" main:app --host 0.0.0.0 --port 8000 --reload > "$LOG_DIR/backend.log" 2>&1 &
        echo $! > "$LOG_DIR/backend.pid"
    )

    if wait_for_port 8000 "Backend" 30; then
        info "Backend started on http://localhost:8000"
    else
        err "Backend failed to start. Check: $LOG_DIR/backend.log"
        tail -n 40 "$LOG_DIR/backend.log" || true
        exit 1
    fi
}

start_frontend() {
    if is_port_listening 5173; then
        info "Frontend already running on :5173"
        return
    fi

    if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
        info "Installing frontend dependencies..."
        (cd "$FRONTEND_DIR" && npm install)
    fi

    info "Starting frontend (Vite)..."
    (
        cd "$FRONTEND_DIR"
        nohup npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
        echo $! > "$LOG_DIR/frontend.pid"
    )

    if wait_for_port 5173 "Frontend" 30; then
        info "Frontend started on http://localhost:5173"
    else
        err "Frontend failed to start. Check: $LOG_DIR/frontend.log"
        tail -n 40 "$LOG_DIR/frontend.log" || true
        exit 1
    fi
}

info "Starting AMAN ERP locally (data + backend + frontend)..."

for cmd in ss python3 npm; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        err "Required command not found: $cmd"
        exit 1
    fi
done

start_postgres_if_needed
start_redis_if_available
start_backend
start_frontend

echo ""
info "System is running:"
echo "  Frontend: http://localhost:5173"
echo "  Backend : http://localhost:8000"
echo "  Health  : http://localhost:8000/health"
echo ""
echo "Logs:"
echo "  $LOG_DIR/backend.log"
echo "  $LOG_DIR/frontend.log"
echo "  $LOG_DIR/redis.log"
