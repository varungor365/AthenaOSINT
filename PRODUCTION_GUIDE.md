# AthenaOSINT Production Deployment Guide

## Quick Production Setup

After you've deployed and tested the development server, set up production:

```bash
# Make the script executable
chmod +x production_setup.sh

# Run the production setup
./production_setup.sh
```

This will automatically:
- Install Gunicorn (production WSGI server)
- Configure Nginx as reverse proxy
- Set up systemd service for auto-restart
- Configure firewall rules
- Start all services

## Manual Configuration

### 1. API Keys Setup

Edit the configuration file:
```bash
nano config/config.py
```

Add your API keys:
- **GROQ_API_KEY** - For Jarvis AI features (get from https://groq.com)
- **HIBP_API_KEY** - Have I Been Pwned (get from https://haveibeenpwned.com/API/Key)
- **DEHASHED_API_KEY** - Advanced leak checking (get from https://dehashed.com)
- **TELEGRAM_BOT_TOKEN** - For Telegram bot (get from @BotFather)

After editing, restart the service:
```bash
sudo systemctl restart athena.service
```

### 2. Domain Name Setup (Optional)

If you have a domain name:

1. Point your domain's A record to: `143.110.254.40`
2. Edit nginx config:
   ```bash
   sudo nano /etc/nginx/sites-available/athena
   ```
3. Change `server_name 143.110.254.40;` to `server_name yourdomain.com;`
4. Restart nginx: `sudo systemctl restart nginx`

### 3. SSL Certificate (HTTPS)

Install Let's Encrypt SSL certificate:

```bash
# Install certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Get SSL certificate (replace with your domain)
sudo certbot --nginx -d yourdomain.com

# Auto-renewal is set up automatically
```

## Service Management Commands

```bash
# View real-time logs
sudo journalctl -u athena.service -f

# Restart the service
sudo systemctl restart athena.service

# Stop the service
sudo systemctl stop athena.service

# Start the service
sudo systemctl start athena.service

# Check service status
sudo systemctl status athena.service

# Restart Nginx
sudo systemctl restart nginx

# Test Nginx configuration
sudo nginx -t
```

## Updating the Application

When you push updates to GitHub:

```bash
cd /root/AthenaOSINT
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart athena.service
```

## Monitoring

### Check if service is running:
```bash
sudo systemctl status athena.service
```

### View application logs:
```bash
# Real-time logs
sudo journalctl -u athena.service -f

# Last 100 lines
sudo journalctl -u athena.service -n 100

# Today's logs
sudo journalctl -u athena.service --since today
```

### Check Nginx logs:
```bash
# Access logs
sudo tail -f /var/log/nginx/access.log

# Error logs
sudo tail -f /var/log/nginx/error.log
```

## Troubleshooting

### Service won't start:
```bash
# Check logs for errors
sudo journalctl -u athena.service -n 50

# Check if port 5000 is in use
sudo lsof -i :5000

# Verify virtual environment
ls -la /root/AthenaOSINT/venv/bin/
```

### Nginx errors:
```bash
# Test configuration
sudo nginx -t

# Check if nginx is running
sudo systemctl status nginx

# Restart nginx
sudo systemctl restart nginx
```

### Application errors:
```bash
# Check Python dependencies
source /root/AthenaOSINT/venv/bin/activate
pip list

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## Security Recommendations

1. **Change default passwords** in config/config.py
2. **Set up firewall**: Only allow ports 80, 443, and 22
3. **Enable SSL/HTTPS** with Let's Encrypt
4. **Regular updates**: 
   ```bash
   sudo apt-get update && sudo apt-get upgrade -y
   ```
5. **Monitor logs** regularly for suspicious activity
6. **Backup configuration** files and data directories

## Performance Optimization

### Increase Gunicorn workers:
Edit `/etc/systemd/system/athena.service`:
```
ExecStart=/root/AthenaOSINT/venv/bin/gunicorn -w 8 -b 127.0.0.1:5000 --timeout 120 run_web:app
```

Reload and restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart athena.service
```

### Enable Nginx caching:
Add to nginx config for better performance with static assets.

## Access URLs

- **Production URL**: http://143.110.254.40 (or your domain)
- **Direct access**: http://127.0.0.1:5000 (localhost only)

---

**Note**: The development server (python run_web.py) should NOT be used in production. Always use the systemd service with Gunicorn.
