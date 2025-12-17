#!/bin/bash
# AthenaOSINT Deployment Script for Ubuntu/Debian
# Run this on your DigitalOcean Droplet

set -e

echo "🦅 AthenaOSINT Deployment initiated..."

# 1. System Updates
echo "[+] Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y python3 python3-pip python3-venv git

# 2. Project Setup
echo "[+] Setting up project environment..."
# Check if we are in the repo directory
if [ ! -f "requirements.txt" ]; then
    echo "[!] requirements.txt not found. Please clone the repo first."
    exit 1
fi

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install Dependencies
echo "[+] Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install CLI tools for OSINT modules (Subfinder, Nuclei, etc.) if needed
# Note: Many go-based tools might need manual install or snap
# basic update for apt-based tools
sudo apt-get install -y exiftool

echo "[+] Installation Complete!"
echo ""
echo "To run AthenaOSINT:"
echo "  1. source venv/bin/activate"
echo "  2. python run_web.py"
echo ""
echo "Creating systemd value for daemon is recommended for 24/7 uptime."
