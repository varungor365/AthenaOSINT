#!/bin/bash

# Quick Server Deployment Commands
# Run these on server 143.110.254.40

echo "=========================================="
echo "  AthenaOSINT - Quick Deploy"
echo "=========================================="

# 1. Pull latest code
git pull origin main

# 2. Run deployment script
chmod +x deploy_complete_fix.sh
./deploy_complete_fix.sh

# 3. Test daemon
echo ""
echo "Testing breach daemon..."
curl -X POST http://127.0.0.1:5000/api/breach/daemon/start \
  -H "Content-Type: application/json" \
  -d '{"max_cpu_percent": 30, "max_memory_mb": 512, "check_interval": 1800}'

sleep 2

curl http://127.0.0.1:5000/api/breach/daemon/status | python3 -m json.tool

echo ""
echo "=========================================="
echo "  Deployment Complete!"
echo "=========================================="
echo ""
echo "Check logs: journalctl -u athena.service -f"
echo "Stop daemon: curl -X POST http://127.0.0.1:5000/api/breach/daemon/stop"
echo ""
