# Deployment Instructions

Run these commands on your Droplet to upgrade AthenaOSINT to **v2.0 (Research Edition)**.

## 1. Upgrade Codebase and Dependencies
```bash
# Navigate to project directory (adjust path if different)
cd /opt/athena-osint || cd ~/osint-website

# Pull latest changes
git pull origin main

# Install new dependencies (WeasyPrint, Graph libs, GoogleSearch)
pip3 install -r requirements.txt

# Install system dependencies for WeasyPrint (PDF Generation)
# For Ubuntu/Debian:
sudo apt-get update && sudo apt-get install -y build-essential python3-dev python3-pip python3-setuptools python3-wheel python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
```

## 2. Upgrade Go Tools (Advanced Arsenal)
Ensure Go is installed. If not: `sudo apt install golang -y`
The python wrappers will try to auto-install tools, but you can pre-install for speed:
```bash
go install -v github.com/projectdiscovery/chaos-client/cmd/chaos@latest
go install -v github.com/projectdiscovery/katana/cmd/katana@latest
go install -v github.com/projectdiscovery/gau/v2/cmd/gau@latest
go install -v github.com/projectdiscovery/hakrawler@latest
```

## 3. Restart Service
Restart the application to apply changes.
```bash
# If running via systemd:
sudo systemctl restart athena

# OR if running via Docker:
docker-compose restart

# OR if running manually:
# Ctrl+C to stop, then:
python3 run_web.py
```

## 4. Verification
1. Open your browser to the dashboard.
2. Go to **Research Mode**.
3. Verify "Interactive Graph" and "Export PDF" buttons appear on scan results.
