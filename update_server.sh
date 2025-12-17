#!/bin/bash
# Update server with latest code and restart services

set -e

echo "Pulling latest code..."
git pull origin main

echo "Installing eventlet dependency..."
source venv/bin/activate
pip install eventlet>=0.33.3

echo "Copying service file..."
sudo cp athena.service /etc/systemd/system/

echo "Reloading systemd..."
sudo systemctl daemon-reload

echo "Restarting Athena service..."
sudo systemctl restart athena.service

echo "Checking service status..."
sudo systemctl status athena.service --no-pager

echo ""
echo "Update complete! Check logs with: sudo journalctl -u athena.service -f"
