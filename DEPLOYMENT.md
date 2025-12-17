# AthenaOSINT Deployment Guide

## 📦 Push to GitHub

### Step 1: Initialize Git Repository
```bash
git init
git add .
git commit -m "Initial commit - AthenaOSINT Framework"
```

### Step 2: Create GitHub Repository
1. Go to https://github.com/new
2. Create a new repository named `athena-osint`
3. **DO NOT** initialize with README (we already have one)

### Step 3: Push to GitHub
```bash
git remote add origin https://github.com/YOUR_USERNAME/athena-osint.git
git branch -M main
git push -u origin main
```

**Replace `YOUR_USERNAME` with your GitHub username**

---

## 🚀 Deploy to DigitalOcean Droplet

### Step 1: Create Droplet
1. Login to DigitalOcean
2. Create a new Droplet:
   - **Image**: Ubuntu 22.04 LTS
   - **Plan**: Basic ($6/month minimum recommended)
   - **Size**: 2GB RAM / 1 CPU (for basic use)
   - **Datacenter**: Choose nearest to your location
   - **Authentication**: SSH Key (recommended) or Password
   - **Hostname**: athena-osint

### Step 2: Connect to Droplet
```bash
ssh root@YOUR_DROPLET_IP
```

### Step 3: Clone and Deploy
```bash
# Clone from GitHub
git clone https://github.com/YOUR_USERNAME/athena-osint.git
cd athena-osint

# Make deployment script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

### Step 4: Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit with your API keys
nano .env
```

Add your API keys:
```
HIBP_API_KEY=your_key_here
DEHASHED_API_KEY=your_key_here
INTELX_API_KEY=your_key_here
TELEGRAM_BOT_TOKEN=your_token_here
```

Save: `Ctrl+O` → `Enter` → `Ctrl+X`

### Step 5: Run the Application

#### Option A: Run Web Interface
```bash
source venv/bin/activate
python run_web.py
```
Access at: `http://YOUR_DROPLET_IP:5000`

#### Option B: Run as Background Service (Recommended)
```bash
# Create systemd service
sudo nano /etc/systemd/system/athena-web.service
```

Paste this configuration:
```ini
[Unit]
Description=AthenaOSINT Web Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/athena-osint
Environment="PATH=/root/athena-osint/venv/bin"
ExecStart=/root/athena-osint/venv/bin/python run_web.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable athena-web
sudo systemctl start athena-web
sudo systemctl status athena-web
```

### Step 6: Configure Firewall
```bash
# Allow SSH
sudo ufw allow 22

# Allow Web Interface
sudo ufw allow 5000

# Enable firewall
sudo ufw enable
```

### Step 7: Setup Nginx Reverse Proxy (Optional but Recommended)
```bash
# Install Nginx
sudo apt-get install -y nginx

# Create configuration
sudo nano /etc/nginx/sites-available/athena
```

Paste:
```nginx
server {
    listen 80;
    server_name YOUR_DROPLET_IP;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/athena /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Allow Nginx through firewall
sudo ufw allow 'Nginx Full'
```

Now access at: `http://YOUR_DROPLET_IP` (port 80)

---

## 🔧 Maintenance Commands

### Check Service Status
```bash
sudo systemctl status athena-web
```

### View Logs
```bash
sudo journalctl -u athena-web -f
```

### Restart Service
```bash
sudo systemctl restart athena-web
```

### Update Code from GitHub
```bash
cd /root/athena-osint
git pull origin main
sudo systemctl restart athena-web
```

### Run CLI Commands
```bash
cd /root/athena-osint
source venv/bin/activate
python athena.py --help
```

---

## 🔒 Security Recommendations

1. **Change SSH Port**
   ```bash
   sudo nano /etc/ssh/sshd_config
   # Change Port 22 to Port 2222
   sudo systemctl restart sshd
   sudo ufw allow 2222
   ```

2. **Setup SSL with Let's Encrypt** (if using domain)
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```

3. **Regular Updates**
   ```bash
   sudo apt-get update && sudo apt-get upgrade -y
   ```

4. **Backup Data Directory**
   ```bash
   tar -czf athena-backup-$(date +%Y%m%d).tar.gz /root/athena-osint/data
   ```

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
sudo lsof -i :5000
sudo kill -9 PID
```

### Module Not Found Errors
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Permission Denied
```bash
chmod +x deploy.sh
chmod -R 755 /root/athena-osint
```

### Check Python Version
```bash
python3 --version  # Should be 3.9+
```

---

## 📞 Support

For issues, check:
- `logs/` directory for application logs
- `sudo journalctl -u athena-web` for service logs
- GitHub Issues page

**Your AthenaOSINT instance is now live! 🦅**
