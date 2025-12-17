#!/bin/bash
# AthenaOSINT Production Setup Script
# Run this after initial deployment to set up production environment

set -e

echo "🦅 AthenaOSINT Production Setup"
echo "================================"

# 1. Install production dependencies
echo "[+] Installing Gunicorn and production tools..."
source venv/bin/activate
pip install gunicorn eventlet

# 2. Install and configure Nginx
echo "[+] Installing Nginx..."
sudo apt-get install -y nginx

# 3. Copy nginx configuration
echo "[+] Configuring Nginx..."
sudo cp nginx-athena.conf /etc/nginx/sites-available/athena
sudo ln -sf /etc/nginx/sites-available/athena /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t

# 4. Set up systemd service
echo "[+] Setting up systemd service..."
sudo cp athena.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable athena.service
sudo systemctl start athena.service

# 5. Start/Restart Nginx
echo "[+] Starting Nginx..."
sudo systemctl restart nginx
sudo systemctl enable nginx

# 6. Set up firewall (if ufw is installed)
if command -v ufw &> /dev/null; then
    echo "[+] Configuring firewall..."
    sudo ufw allow 'Nginx Full'
    sudo ufw allow OpenSSH
    sudo ufw --force enable
fi

# 7. Check service status
echo ""
echo "✅ Production setup complete!"
echo ""
echo "Service Status:"
sudo systemctl status athena.service --no-pager
echo ""
echo "Nginx Status:"
sudo systemctl status nginx --no-pager
echo ""
echo "🌐 AthenaOSINT is now running at: http://143.110.254.40"
echo ""
echo "Useful commands:"
echo "  - View logs: sudo journalctl -u athena.service -f"
echo "  - Restart service: sudo systemctl restart athena.service"
echo "  - Stop service: sudo systemctl stop athena.service"
echo "  - Restart Nginx: sudo systemctl restart nginx"
echo ""
echo "To configure API keys, edit: /root/AthenaOSINT/config/config.py"
echo "Then restart: sudo systemctl restart athena.service"
