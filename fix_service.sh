#!/bin/bash
# Fix service configuration on server

set -e

echo "Installing eventlet..."
source venv/bin/activate
pip install eventlet>=0.33.3

echo "Copying updated service file..."
sudo cp athena.service /etc/systemd/system/athena.service

echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "Restarting service..."
sudo systemctl restart athena.service

sleep 2

echo "Checking service status..."
sudo systemctl status athena.service --no-pager -l

echo ""
echo "Verifying worker type..."
sudo journalctl -u athena.service -n 20 --no-pager | grep -i "worker"
