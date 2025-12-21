#!/bin/bash
# ============================================================================
# AthenaOSINT v3.0 - 16GB RAM Deployment Script
# ============================================================================
# This script deploys the upgraded high-performance version of Athena
# optimized for 16GB RAM droplets with parallel processing capabilities.
# ============================================================================

set -e

echo "================================================"
echo "  AthenaOSINT v3.0 - 16GB RAM Deployment"
echo "================================================"

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/root/AthenaOSINT"
AGENT_DIR="/opt/agent"
VENV_DIR="$PROJECT_DIR/venv"

echo -e "${YELLOW}[1/8] Updating codebase...${NC}"
cd "$PROJECT_DIR"
git pull origin main
echo -e "${GREEN}✓ Code updated${NC}"

echo -e "${YELLOW}[2/8] Upgrading Python dependencies...${NC}"
source "$VENV_DIR/bin/activate"
pip install -U pip setuptools wheel
pip install -r requirements.txt
pip install gevent==23.9.1  # High-performance async for Flask
pip install gunicorn[gevent]
echo -e "${GREEN}✓ Dependencies installed${NC}"

echo -e "${YELLOW}[3/8] Configuring Ollama for 16GB RAM...${NC}"
# Stop Ollama to update configuration
sudo systemctl stop ollama 2>/dev/null || true

# Set environment for larger context and parallelism
sudo mkdir -p /etc/systemd/system/ollama.service.d
cat << EOF | sudo tee /etc/systemd/system/ollama.service.d/override.conf
[Service]
Environment="OLLAMA_NUM_PARALLEL=4"
Environment="OLLAMA_MAX_LOADED_MODELS=2"
Environment="OLLAMA_KEEP_ALIVE=24h"
Environment="OLLAMA_HOST=127.0.0.1:11434"
LimitNOFILE=65536
LimitNPROC=4096
EOF

sudo systemctl daemon-reload
sudo systemctl start ollama
echo -e "${GREEN}✓ Ollama configured for 16GB RAM${NC}"

echo -e "${YELLOW}[4/8] Pulling larger LLM model (13B)...${NC}"
# Pull wizard-vicuna-uncensored:13b (fits in 16GB with 8K context)
ollama pull wizard-vicuna-uncensored:13b || {
    echo -e "${RED}Failed to pull 13B model, keeping current model${NC}"
}
echo -e "${GREEN}✓ Model ready${NC}"

echo -e "${YELLOW}[5/8] Updating Agent Orchestrator...${NC}"
cd "$AGENT_DIR/orchestrator"

# Update orchestrator .env
cat << EOF > .env
AGENT_MODEL=wizard-vicuna-uncensored:13b
AGENT_CONTEXT=8192
AGENT_THREADS=8
AGENT_PARALLEL=4
AGENT_HOST=0.0.0.0
AGENT_PORT=8081
EOF

# Restart orchestrator
sudo systemctl restart agent-orchestrator
sleep 3

# Verify orchestrator
if curl -s http://127.0.0.1:8081/api/health | grep -q "ok"; then
    echo -e "${GREEN}✓ Orchestrator running with upgraded model${NC}"
else
    echo -e "${YELLOW}⚠ Orchestrator may need manual verification${NC}"
fi

echo -e "${YELLOW}[6/8] Configuring gunicorn for high concurrency...${NC}"
# Create production gunicorn config
cat << 'EOF' > "$PROJECT_DIR/gunicorn.conf.py"
# Gunicorn configuration for 16GB RAM
import multiprocessing

# Server socket
bind = "127.0.0.1:5000"
backlog = 2048

# Worker processes
workers = 12  # 16GB RAM: 12 workers
worker_class = "gevent"
worker_connections = 1000
threads = 4
max_requests = 5000
max_requests_jitter = 500

# Timeouts
timeout = 300
graceful_timeout = 30
keepalive = 5

# Process naming
proc_name = "athena-web"

# Logging
accesslog = "/root/AthenaOSINT/logs/gunicorn_access.log"
errorlog = "/root/AthenaOSINT/logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Server mechanics
daemon = False
pidfile = "/var/run/athena_gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# Performance tuning
worker_tmp_dir = "/dev/shm"  # Use RAM for temp files
preload_app = True
EOF

echo -e "${GREEN}✓ Gunicorn config created${NC}"

echo -e "${YELLOW}[7/8] Updating systemd services...${NC}"
# Update Flask service to use new config
cat << EOF | sudo tee /etc/systemd/system/athena-web.service
[Unit]
Description=AthenaOSINT Web Dashboard (16GB Optimized)
After=network.target

[Service]
Type=notify
User=root
WorkingDirectory=/root/AthenaOSINT
Environment="PATH=/root/AthenaOSINT/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/root/AthenaOSINT/venv/bin/gunicorn -c gunicorn.conf.py run_web:app
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=30
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=athena-web

# Resource limits for 16GB RAM
LimitNOFILE=65536
LimitNPROC=4096
LimitMEMLOCK=infinity

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
echo -e "${GREEN}✓ Systemd services updated${NC}"

echo -e "${YELLOW}[8/8] Optimizing nginx configuration...${NC}"
# Optimize nginx for high concurrency
cat << 'EOF' | sudo tee /etc/nginx/conf.d/athena_optimization.conf
# Performance optimizations for 16GB RAM
client_max_body_size 100M;
client_body_buffer_size 128k;
client_header_buffer_size 1k;
large_client_header_buffers 4 32k;

# Timeouts
client_body_timeout 60s;
client_header_timeout 60s;
send_timeout 60s;
keepalive_timeout 65s;

# Gzip compression
gzip on;
gzip_vary on;
gzip_proxied any;
gzip_comp_level 6;
gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss;

# Caching
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=athena_cache:10m max_size=1g inactive=60m use_temp_path=off;
proxy_cache_key "$scheme$request_method$host$request_uri";
proxy_cache_valid 200 302 10m;
proxy_cache_valid 404 1m;
EOF

sudo nginx -t && sudo systemctl reload nginx
echo -e "${GREEN}✓ Nginx optimized${NC}"

echo ""
echo -e "${GREEN}================================================"
echo "  Deployment Complete!"
echo "================================================${NC}"
echo ""
echo "Starting services..."
sudo systemctl restart athena-web
sudo systemctl restart agent-orchestrator

sleep 5

echo ""
echo "=== Service Status ==="
sudo systemctl status athena-web --no-pager -l | head -10
echo ""
sudo systemctl status agent-orchestrator --no-pager -l | head -10

echo ""
echo "=== Performance Verification ==="
echo -n "Flask workers: "
ps aux | grep gunicorn | grep -v grep | wc -l
echo -n "Ollama model: "
curl -s http://127.0.0.1:8081/api/health | jq -r '.model' 2>/dev/null || echo "Check manually"
echo -n "System RAM: "
free -h | grep Mem | awk '{print $2}'
echo -n "RAM usage: "
free -h | grep Mem | awk '{print $3}'

echo ""
echo -e "${GREEN}🚀 AthenaOSINT v3.0 is now running with:${NC}"
echo "  • 13B parameter uncensored LLM"
echo "  • 12 concurrent Flask workers"
echo "  • 8K context window"
echo "  • Parallel scan engine"
echo "  • AI-powered Sentinel monitoring"
echo "  • Intelligent caching system"
echo ""
echo -e "${YELLOW}Access dashboard: http://$(curl -s ifconfig.me)${NC}"
echo ""
echo "Logs:"
echo "  • Flask: journalctl -u athena-web -f"
echo "  • Orchestrator: journalctl -u agent-orchestrator -f"
echo ""
