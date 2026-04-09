#!/usr/bin/env bash
# ============================================================
#  start-mobile.sh  —  Aman Mobile App Launcher
#  Starts Metro bundler + backend, sets up ADB reverse tunnel
# ============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$ROOT_DIR/backend"
METRO_PORT=8081
BACKEND_PORT=8000
METRO_LOG="$SCRIPT_DIR/../logs/metro.log"
METRO_PID_FILE="$SCRIPT_DIR/../logs/metro.pid"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
RESET='\033[0m'

ok()   { echo -e "${GREEN}✔  $*${RESET}"; }
info() { echo -e "${CYAN}→  $*${RESET}"; }
warn() { echo -e "${YELLOW}⚠  $*${RESET}"; }
err()  { echo -e "${RED}✗  $*${RESET}"; }

echo ""
echo -e "${CYAN}╔══════════════════════════════════════╗${RESET}"
echo -e "${CYAN}║     Aman Mobile — App Launcher       ║${RESET}"
echo -e "${CYAN}╚══════════════════════════════════════╝${RESET}"
echo ""

# ── 1. Check backend ────────────────────────────────────────
info "Checking backend (port $BACKEND_PORT)..."

if curl -sf "http://localhost:$BACKEND_PORT/health" > /dev/null 2>&1 || \
   curl -sf "http://localhost:$BACKEND_PORT/api/health" > /dev/null 2>&1; then
  ok "Backend is already running"
else
  warn "Backend not running — attempting to start it..."
  if [ -f "$BACKEND_DIR/start.sh" ]; then
    bash "$BACKEND_DIR/start.sh" &
    sleep 3
    if curl -sf "http://localhost:$BACKEND_PORT/health" > /dev/null 2>&1 || \
       curl -sf "http://localhost:$BACKEND_PORT/api/health" > /dev/null 2>&1; then
      ok "Backend started successfully"
    else
      warn "Backend may still be starting. Continuing..."
    fi
  else
    warn "No start.sh found in backend/. Start the backend manually if needed."
  fi
fi

# ── 2. Kill any existing Metro process ──────────────────────
info "Stopping any existing Metro bundler..."

# Kill by PID file
if [ -f "$METRO_PID_FILE" ]; then
  OLD_PID=$(cat "$METRO_PID_FILE" 2>/dev/null || true)
  if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
    kill "$OLD_PID" 2>/dev/null || true
    ok "Stopped Metro (PID $OLD_PID)"
  fi
  rm -f "$METRO_PID_FILE"
fi

# Kill by port
if lsof -ti:$METRO_PORT > /dev/null 2>&1; then
  lsof -ti:$METRO_PORT | xargs kill -9 2>/dev/null || true
  ok "Released port $METRO_PORT"
fi

sleep 1

# ── 3. Start Metro bundler ───────────────────────────────────
info "Starting Metro bundler on 0.0.0.0:$METRO_PORT..."
mkdir -p "$(dirname "$METRO_LOG")"

cd "$SCRIPT_DIR"
npx react-native start \
  --host 0.0.0.0 \
  --port "$METRO_PORT" \
  --reset-cache > "$METRO_LOG" 2>&1 &

METRO_PID=$!
echo "$METRO_PID" > "$METRO_PID_FILE"
ok "Metro started (PID $METRO_PID) — log: $METRO_LOG"

# Wait briefly for Metro to initialize
info "Waiting for Metro to initialize..."
for i in $(seq 1 15); do
  if curl -sf "http://localhost:$METRO_PORT/status" > /dev/null 2>&1; then
    ok "Metro is ready"
    break
  fi
  sleep 1
  printf "."
done
echo ""

# ── 4. ADB device check ──────────────────────────────────────
info "Checking ADB device connection..."

if ! command -v adb &>/dev/null; then
  warn "ADB not found in PATH. Skipping ADB setup."
else
  DEVICES=$(adb devices | tail -n +2 | grep -v '^$' | grep -v 'offline' || true)

  if [ -z "$DEVICES" ]; then
    warn "No ADB devices found."
    echo "  USB debugging:     Settings → Developer options → USB debugging"
    echo "  Wireless (TCP/IP): adb connect <phone-ip>:5555"
  else
    ok "ADB devices:"
    echo "$DEVICES" | while read -r line; do
      echo "     $line"
    done

    # ── 5. Set up ADB reverse tunnel ────────────────────────
    info "Setting up ADB reverse tunnels..."
    if adb reverse tcp:$METRO_PORT tcp:$METRO_PORT 2>/dev/null && \
       adb reverse tcp:$BACKEND_PORT tcp:$BACKEND_PORT 2>/dev/null; then
      ok "ADB reverse tunnels set: Metro :$METRO_PORT  Backend :$BACKEND_PORT"
    else
      warn "ADB reverse failed (may be wireless). App will use network IP."
      HOST_IP=$(ip route get 1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src") {print $(i+1); exit}}' || hostname -I 2>/dev/null | awk '{print $1}')
      if [ -n "$HOST_IP" ]; then
        info "Detected laptop IP: $HOST_IP"
        echo "  Make sure the app's API_BASE points to http://$HOST_IP:$BACKEND_PORT"
        echo "  Metro will be at: http://$HOST_IP:$METRO_PORT"
      fi
    fi
  fi
fi

# ── Summary ──────────────────────────────────────────────────
echo ""
echo -e "${GREEN}══════════════════════════════════════${RESET}"
ok "Setup complete!"
echo ""
echo "  Metro bundler : http://localhost:$METRO_PORT"
echo "  Backend API   : http://localhost:$BACKEND_PORT"
echo "  Metro log     : $METRO_LOG"
echo ""
echo "To run on device (in another terminal):"
echo "  cd mobile && npx react-native run-android"
echo ""
echo "To stop Metro:"
echo "  kill \$(cat $METRO_PID_FILE)"
echo -e "${GREEN}══════════════════════════════════════${RESET}"
