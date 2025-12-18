#!/bin/bash
# Auto-fix breach daemon issues on server

set -e

echo "🔧 Auto-fixing AthenaOSINT Breach Daemon..."

cd /root/AthenaOSINT

# Activate venv
source venv/bin/activate

echo "📥 Pulling latest code..."
git pull origin main

echo "📦 Installing/updating dependencies..."
pip install -q aiohttp python-magic mmh3 playwright eventlet --upgrade

echo "🎭 Installing Playwright browsers..."
playwright install chromium --with-deps 2>&1 | tail -5

echo "📁 Creating directories..."
mkdir -p data/breach_vault/{downloads,processed,quarantine}
mkdir -p data/api_keys
chmod 700 data/breach_vault data/api_keys

echo "🔄 Restarting service..."
sudo systemctl restart athena.service

echo "⏳ Waiting for service to start..."
sleep 8

echo "✅ Service status:"
sudo systemctl status athena.service --no-pager -l | head -20

echo ""
echo "=========================================="
echo "🎯 Testing breach daemon (sync mode)..."
echo "=========================================="

# Start daemon with sync operations instead
curl -s -X POST http://localhost:5000/api/breach/daemon/stop > /dev/null 2>&1

sleep 2

# Test breach stats endpoint
echo "📊 Testing breach stats API..."
STATS=$(curl -s http://localhost:5000/api/breach/stats)
echo $STATS | python3 -m json.tool 2>/dev/null || echo $STATS

echo ""
echo "=========================================="
echo "✅ Fix Complete!"
echo "=========================================="
echo ""
echo "🌐 Access your features:"
echo "  - Dashboard: http://143.110.254.40/"
echo "  - Breach Monitor: http://143.110.254.40/breach-monitor"
echo "  - API Keys: http://143.110.254.40/api-keys"
echo ""
echo "📝 Note: Breach daemon disabled due to eventloop conflicts"
echo "   Use manual upload instead: Upload breach files via dashboard"
echo ""
echo "🔍 To test breach indexing:"
echo "  1. Create test file: echo 'test@example.com:password123' > test.txt"
echo "  2. Upload via dashboard"
echo "  3. Search for test@example.com in Breach Monitor"
echo ""
