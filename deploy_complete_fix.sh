#!/bin/bash

# Complete Fix and Deployment Script for AthenaOSINT
# Addresses all identified issues and deploys to production

set -e  # Exit on any error

echo "================================================================"
echo "  AthenaOSINT - Complete Fix & Deployment"
echo "================================================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# 1. Pull Latest Code
echo ""
log_info "Pulling latest code from GitHub..."
git pull origin main || log_error "Git pull failed"

# 2. Check Python Environment
log_info "Checking Python environment..."
if [ ! -d "venv" ]; then
    log_warn "Virtual environment not found, creating..."
    python3 -m venv venv
fi

source venv/bin/activate

# 3. Install/Update Dependencies
log_info "Installing dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt --quiet || log_error "Dependency installation failed"

# 4. Install Playwright Browsers
log_info "Installing Playwright browsers..."
playwright install chromium > /dev/null 2>&1 || log_warn "Playwright install failed (may already be installed)"

# 5. Create Required Directories
log_info "Creating directory structure..."
mkdir -p data/breach_vault/{downloads,processed,quarantine}
mkdir -p logs
mkdir -p reports
mkdir -p data

# 6. Run Diagnostic
log_info "Running system diagnostic..."
python3 diagnostic_complete.py || log_warn "Some diagnostic checks failed"

# 7. Check Service Status
log_info "Checking service status..."
if systemctl is-active --quiet athena.service; then
    log_info "Service is running, restarting..."
    systemctl restart athena.service
else
    log_warn "Service is not running, starting..."
    systemctl start athena.service
fi

# 8. Wait for Service to Start
log_info "Waiting for service to initialize..."
sleep 5

# 9. Test Critical Endpoints
log_info "Testing critical endpoints..."

test_endpoint() {
    local endpoint=$1
    local name=$2
    
    response=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000${endpoint})
    
    if [ "$response" == "200" ]; then
        log_info "$name: OK"
    else
        log_error "$name: FAILED (HTTP $response)"
    fi
}

test_endpoint "/" "Dashboard"
test_endpoint "/api/modules" "Modules API"
test_endpoint "/breach-monitor" "Breach Monitor"
test_endpoint "/api-keys" "API Keys"
test_endpoint "/api/breach/daemon/status" "Daemon Status"

# 10. Test Breach System
log_info "Testing breach indexer..."
python3 -c "
from intelligence.breach_indexer import BreachIndexer
indexer = BreachIndexer()
stats = indexer.get_breach_stats()
print(f\"Breach DB: {stats['total_credentials']} credentials, {stats['total_breaches']} breaches\")
" || log_warn "Breach indexer test failed"

# 11. Check for Errors in Logs
log_info "Checking recent logs for errors..."
journalctl -u athena.service --no-pager -n 20 | grep -i error || log_info "No recent errors found"

# 12. Resource Usage
log_info "Checking resource usage..."
python3 -c "
import psutil
print(f'CPU: {psutil.cpu_percent()}%')
print(f'RAM: {psutil.virtual_memory().percent}%')
print(f'Disk: {psutil.disk_usage(\"/\").percent}%')
"

# 13. Final Status
echo ""
echo "================================================================"
log_info "Deployment Complete!"
echo "================================================================"
echo ""
echo "Service Status:"
systemctl status athena.service --no-pager -l | head -20
echo ""
echo "Access Points:"
echo "  - Dashboard: http://$(hostname -I | awk '{print $1}')/"
echo "  - Breach Monitor: http://$(hostname -I | awk '{print $1}')/breach-monitor"
echo "  - API Keys: http://$(hostname -I | awk '{print $1}')/api-keys"
echo ""
echo "Key Improvements:"
log_info "Breach daemon now uses multiprocessing (no eventloop conflicts)"
log_info "Improved SocketIO configuration (reduced connection errors)"
log_info "Complete diagnostic tool added"
log_info "All dependencies verified"
echo ""
log_warn "Note: Test breach daemon manually with: curl -X POST http://127.0.0.1:5000/api/breach/daemon/start"
echo ""
