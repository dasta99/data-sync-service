#!/bin/bash

# Data Sync Service Deployment Script
# Deploys Python sync service via PM2

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_status()  { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

APP_DIR="/opt/data-sync-service"

# ── Pre-flight checks ────────────────────────────────────────────────────────

if [ ! -f .env ]; then
    print_error ".env file not found. Create one based on .env.example"
    exit 1
fi

if ! command -v pm2 &> /dev/null; then
    print_error "PM2 is not installed. Run: npm install -g pm2"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    if [ -x /usr/local/bin/python3.11 ]; then
        print_status "python3 not on PATH but /usr/local/bin/python3.11 found — symlinking..."
        sudo ln -sf /usr/local/bin/python3.11 /usr/bin/python3
        hash -r 2>/dev/null || true
    else
        print_error "python3 is not installed or not on PATH"
        exit 1
    fi
fi

# Verify Python 3.8+
PYTHON_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
PYTHON_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]; }; then
    print_error "Python 3.8+ required (found $(python3 --version))"
    exit 1
fi

hash -r 2>/dev/null || true
print_status "Pre-flight checks passed ✓ ($(python3 --version))"

# ── Python dependencies ──────────────────────────────────────────────────────

PIP=$(command -v pip3 || command -v pip)

if [ -z "$PIP" ]; then
    print_status "pip not found, installing via get-pip.py..."
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3
    PIP=$(command -v pip3 || command -v pip)
fi

print_status "Upgrading pip..."
$PIP install --upgrade pip --quiet

print_status "Installing Python dependencies..."
$PIP install -r requirements.txt --quiet
print_success "Python dependencies installed"

# ── PM2 deployment via ecosystem.config.js ───────────────────────────────────

print_status "Starting/reloading PM2 processes via ecosystem.config.js..."
pm2 reload ecosystem.config.js --update-env || pm2 start ecosystem.config.js
print_success "PM2 processes started"

# ── Save and show status ─────────────────────────────────────────────────────

print_status "Saving PM2 process list..."
pm2 save
print_success "PM2 configuration saved"

print_status "Current PM2 processes:"
pm2 status

print_success "Deployment completed successfully!"
echo ""
echo "Useful commands:"
echo "  - View logs:         pm2 logs data-sync-service"
echo "  - Stop:              pm2 stop data-sync-service"
echo "  - Restart:           pm2 restart data-sync-service"
echo "  - Monitor:           pm2 monit"
echo "  - Health check:      curl http://localhost:8090/health"
echo "  - Sync status:       curl http://localhost:8090/health/sync"
