#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# AMAN ERP — Server Initial Setup Script
# Run on DigitalOcean Ubuntu 22.04 droplet as root:
#   curl -sSL https://raw.githubusercontent.com/AMANCAMSYS/AMAN_ERP/main/scripts/setup_server.sh | bash
# ═══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

GITHUB_REPO="https://github.com/AMANCAMSYS/AMAN_ERP.git"
APP_DIR="/opt/aman"
DEPLOY_USER="deploy"

echo ""
echo "═══════════════════════════════════════════════"
echo "  AMAN ERP — Server Setup"
echo "  $(date)"
echo "═══════════════════════════════════════════════"
echo ""

# ── 1. System Updates ─────────────────────────────────────────────────────────
echo "[1/8] Updating system packages..."
apt-get update -qq
apt-get upgrade -y -qq
apt-get install -y -qq \
    curl wget git vim ufw fail2ban \
    ca-certificates gnupg lsb-release \
    postgresql-client python3-pip

echo "✅ System packages updated"

# ── 2. Install Docker ─────────────────────────────────────────────────────────
echo "[2/8] Installing Docker..."
if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    echo "✅ Docker installed: $(docker --version)"
else
    echo "✅ Docker already installed: $(docker --version)"
fi

# ── 3. Create deploy user ─────────────────────────────────────────────────────
echo "[3/8] Creating deploy user..."
if ! id "$DEPLOY_USER" &>/dev/null; then
    useradd -m -s /bin/bash "$DEPLOY_USER"
    usermod -aG docker "$DEPLOY_USER"
    mkdir -p /home/$DEPLOY_USER/.ssh
    chmod 700 /home/$DEPLOY_USER/.ssh
    echo "✅ User '$DEPLOY_USER' created"
else
    usermod -aG docker "$DEPLOY_USER"
    echo "✅ User '$DEPLOY_USER' already exists"
fi

# ── 4. Setup SSH for deploy user ──────────────────────────────────────────────
echo "[4/8] Setting up SSH keys..."
echo ""
echo "══════════════════════════════════════════════════════════"
echo "  ACTION REQUIRED: Add deploy user SSH public key"
echo "  Paste the public key for GitHub Actions below"
echo "  (press Enter twice when done):"
echo "══════════════════════════════════════════════════════════"
read -r PUBKEY
if [[ -n "$PUBKEY" ]]; then
    echo "$PUBKEY" >> /home/$DEPLOY_USER/.ssh/authorized_keys
    chmod 600 /home/$DEPLOY_USER/.ssh/authorized_keys
    chown -R $DEPLOY_USER:$DEPLOY_USER /home/$DEPLOY_USER/.ssh
    echo "✅ SSH key added"
else
    echo "⚠️  No key provided — add manually later:"
    echo "   echo 'YOUR_PUBLIC_KEY' >> /home/$DEPLOY_USER/.ssh/authorized_keys"
fi

# ── 5. Clone repository ───────────────────────────────────────────────────────
echo "[5/8] Cloning AMAN ERP repository..."
mkdir -p "$APP_DIR"
if [ ! -d "$APP_DIR/.git" ]; then
    git clone "$GITHUB_REPO" "$APP_DIR"
    echo "✅ Repository cloned to $APP_DIR"
else
    cd "$APP_DIR" && git pull origin main
    echo "✅ Repository already exists — pulled latest"
fi
chown -R $DEPLOY_USER:$DEPLOY_USER "$APP_DIR"

# ── 6. Create .env file ───────────────────────────────────────────────────────
echo "[6/8] Creating .env file..."
if [ ! -f "$APP_DIR/backend/.env" ]; then
    cat > "$APP_DIR/backend/.env" << 'EOF'
# ═══════════════════════════════════════════════════════
# AMAN ERP — Production Environment Variables
# IMPORTANT: Change ALL values below before starting!
# ═══════════════════════════════════════════════════════

# Database
POSTGRES_SERVER=db
POSTGRES_PORT=5432
POSTGRES_USER=aman
POSTGRES_PASSWORD=CHANGE_THIS_STRONG_PASSWORD
POSTGRES_DB=postgres

# Redis
REDIS_URL=redis://:CHANGE_THIS_REDIS_PASSWORD@redis:6379/0
REDIS_PASSWORD=CHANGE_THIS_REDIS_PASSWORD

# Security — generate with: python3 -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=CHANGE_THIS_TO_64_CHAR_RANDOM_STRING

# App
APP_ENV=production
ALLOWED_ORIGINS=https://yourdomain.com

# Email (optional)
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=noreply@yourdomain.com

# Frontend URL
FRONTEND_URL=https://yourdomain.com
FRONTEND_URL_PRODUCTION=https://yourdomain.com

# Grafana
GRAFANA_USER=admin
GRAFANA_PASSWORD=CHANGE_THIS_GRAFANA_PASSWORD
GRAFANA_ROOT_URL=https://yourdomain.com:3000
EOF
    chmod 600 "$APP_DIR/backend/.env"
    chown $DEPLOY_USER:$DEPLOY_USER "$APP_DIR/backend/.env"
    echo "✅ .env file created at $APP_DIR/backend/.env"
    echo "⚠️  EDIT THIS FILE NOW: nano $APP_DIR/backend/.env"
else
    echo "✅ .env already exists — not overwritten"
fi

# ── 7. Firewall setup ─────────────────────────────────────────────────────────
echo "[7/8] Configuring firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp    comment 'SSH'
ufw allow 80/tcp    comment 'HTTP'
ufw allow 443/tcp   comment 'HTTPS'
# Internal only (monitoring) - remove if not needed
# ufw allow 9090/tcp comment 'Prometheus'
# ufw allow 3000/tcp comment 'Grafana'
ufw --force enable
echo "✅ Firewall configured (22, 80, 443)"

# ── 8. Setup fail2ban ──────────────────────────────────────────────────────────
echo "[8/8] Configuring fail2ban..."
systemctl enable fail2ban
systemctl start fail2ban
echo "✅ fail2ban enabled"

# ── Summary ──────────────────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  ✅ Server setup complete!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "  1. Edit the .env file:"
echo "     nano $APP_DIR/backend/.env"
echo ""
echo "  2. Start the application:"
echo "     cd $APP_DIR"
echo "     docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d"
echo ""
echo "  3. Check status:"
echo "     docker compose ps"
echo "     curl http://localhost:8000/health"
echo ""
echo "  Server IP: $(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')"
echo ""
