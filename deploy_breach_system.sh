
#!/bin/bash
# Deploy Breach Monitoring System

set -e

echo "🚀 Deploying Breach Monitoring System..."

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# Install new dependencies
echo "📦 Installing dependencies..."
pip install python-magic mmh3 playwright

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install chromium

# Create breach vault directory
echo "📁 Creating breach vault directory..."
mkdir -p data/breach_vault/{downloads,processed,quarantine}

# Set permissions
chmod 700 data/breach_vault
chmod 755 data/breach_vault/downloads
chmod 755 data/breach_vault/processed
chmod 700 data/breach_vault/quarantine

# Restart service
echo "🔄 Restarting Athena service..."
sudo systemctl restart athena.service

# Check status
echo "✅ Checking service status..."
sleep 3
sudo systemctl status athena.service --no-pager

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Breach Monitor UI: http://143.110.254.40/breach-monitor"
echo ""
echo "To start autonomous monitoring:"
echo "  Visit the Breach Monitor page and click 'Start Monitoring'"
echo ""
echo "To monitor logs:"
echo "  sudo journalctl -u athena.service -f"
echo ""
