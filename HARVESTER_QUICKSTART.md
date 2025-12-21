# 🚀 24/7 Harvester Quick Start

## Deployment on Droplet

```bash
# SSH to droplet
ssh root@143.110.254.40

# Pull latest code
cd /root/AthenaOSINT
git pull origin main

# Run deployment (includes harvester setup)
chmod +x scripts/deploy_16gb.sh
./scripts/deploy_16gb.sh

# Enable and start harvester
systemctl enable athena-harvester
systemctl start athena-harvester

# Check status
systemctl status athena-harvester
```

## Dashboard Access

Visit: `http://143.110.254.40/harvester`

## Quick Configuration

### Add Targets via Dashboard
1. Go to http://143.110.254.40/harvester
2. Select target type (domain/email/username/keyword)
3. Enter target value
4. Click "Add"

### Add Targets via API
```bash
# Add your company domain
curl -X POST http://localhost:5000/api/harvester/add-target \
  -H "Content-Type: application/json" \
  -d '{"type":"domain","target":"yourcompany.com"}'

# Add CEO email
curl -X POST http://localhost:5000/api/harvester/add-target \
  -H "Content-Type: application/json" \
  -d '{"type":"email","target":"ceo@yourcompany.com"}'

# Add sensitive keyword
curl -X POST http://localhost:5000/api/harvester/add-target \
  -H "Content-Type: application/json" \
  -d '{"type":"keyword","target":"yourcompany api_key"}'

# Add competitor username
curl -X POST http://localhost:5000/api/harvester/add-target \
  -H "Content-Type: application/json" \
  -d '{"type":"username","target":"competitor_ceo"}'
```

## What It Does Automatically

Every 30 minutes (configurable), the harvester will:

✅ **Check all emails** for new breaches (holehe, leak_checker)
✅ **Scan all domains** for new subdomains (subfinder, amass)
✅ **Search GitHub** for exposed secrets matching keywords
✅ **Monitor Pastebin** for leaks containing keywords
✅ **Check SSL certificates** for expiration
✅ **Run Nuclei scans** for vulnerabilities
✅ **Scrape social media** for username changes
✅ **Alert you** when threats are detected

## Monitor Logs

```bash
# Real-time harvester logs
journalctl -u athena-harvester -f

# Last 100 lines
journalctl -u athena-harvester -n 100

# Today's logs
journalctl -u athena-harvester --since today
```

## Check Statistics

```bash
# Via API
curl http://localhost:5000/api/harvester/status | jq

# Example output:
{
  "success": true,
  "stats": {
    "tasks_completed": 247,
    "targets_monitored": 15,
    "threats_found": 8,
    "data_harvested_mb": 45.2,
    "uptime_hours": 72.5,
    "queue_size": 3,
    "running": true
  }
}
```

## View Alerts

```bash
# Get recent alerts
curl http://localhost:5000/api/harvester/alerts | jq

# Check alert files directly
ls -lah /root/AthenaOSINT/data/harvester_results/alert_*

# Read latest alert
cat $(ls -t /root/AthenaOSINT/data/harvester_results/alert_* | head -1) | jq
```

## Configuration File

Edit: `/root/AthenaOSINT/data/harvester_config.json`

```json
{
  "enabled": true,
  "interval_minutes": 30,
  "max_concurrent": 4,
  
  "watchlist_domains": ["yourcompany.com"],
  "watchlist_emails": ["ceo@company.com"],
  "watchlist_usernames": ["company_official"],
  "watchlist_keywords": ["company confidential"],
  
  "tasks": {
    "breach_monitoring": true,
    "subdomain_discovery": true,
    "leak_scanning": true,
    "ssl_monitoring": true,
    "dns_monitoring": true,
    "phishing_detection": true,
    "social_scraping": true,
    "vulnerability_scanning": true,
    "github_secrets": true,
    "pastebin_monitoring": true
  }
}
```

## Troubleshooting

### Harvester not starting
```bash
# Check service status
systemctl status athena-harvester

# View errors
journalctl -u athena-harvester -n 50

# Restart
systemctl restart athena-harvester
```

### High resource usage
```bash
# Check CPU/RAM
htop

# Reduce workers in config
nano /root/AthenaOSINT/data/harvester_config.json
# Change: "max_concurrent": 2

# Increase interval
# Change: "interval_minutes": 60

# Restart
systemctl restart athena-harvester
```

### No alerts appearing
```bash
# Make sure you've added targets
curl http://localhost:5000/api/harvester/config | jq '.config.watchlist_domains'

# Check if tasks are running
journalctl -u athena-harvester -f
# Should see: "Executing breach_check for..."

# Check results directory
ls -lah /root/AthenaOSINT/data/harvester_results/
```

## Stop/Disable Harvester

```bash
# Stop temporarily
systemctl stop athena-harvester

# Disable auto-start on boot
systemctl disable athena-harvester

# Check status
systemctl status athena-harvester
```

## Example: Enterprise Setup

```bash
# Add multiple company domains
for domain in main.com subsidiary1.com subsidiary2.com; do
  curl -X POST http://localhost:5000/api/harvester/add-target \
    -H "Content-Type: application/json" \
    -d "{\"type\":\"domain\",\"target\":\"$domain\"}"
done

# Add executive emails
for email in ceo@company.com cto@company.com ciso@company.com; do
  curl -X POST http://localhost:5000/api/harvester/add-target \
    -H "Content-Type: application/json" \
    -d "{\"type\":\"email\",\"target\":\"$email\"}"
done

# Add leak monitoring keywords
for keyword in "company confidential" "company api" "company password"; do
  curl -X POST http://localhost:5000/api/harvester/add-target \
    -H "Content-Type: application/json" \
    -d "{\"type\":\"keyword\",\"target\":\"$keyword\"}"
done

# Start harvester
systemctl start athena-harvester

# Monitor for 1 hour
journalctl -u athena-harvester -f
```

## Performance Tips

- **Interval:** 30min = balanced, 15min = aggressive, 60min = conservative
- **Workers:** 4 = optimal for 16GB RAM, reduce to 2 if CPU/RAM constrained
- **Tasks:** Disable tasks you don't need to save resources
- **Rate Limits:** Some APIs limit requests (e.g., VirusTotal). Increase interval if hitting limits.

## Integration with Other Systems

### Slack Webhooks (modify code)
```python
# In background_harvester.py _alert() function, add:
import requests
webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
requests.post(webhook_url, json={"text": f"🚨 {title}: {details}"})
```

### Email Notifications
```python
# Add to _alert() function:
import smtplib
from email.message import EmailMessage

msg = EmailMessage()
msg['Subject'] = title
msg['From'] = 'athena@company.com'
msg['To'] = 'security@company.com'
msg.set_content(details)

with smtplib.SMTP('localhost') as s:
    s.send_message(msg)
```

---

**Your computer is now working 24/7 collecting OSINT intelligence! 🎯**

View live dashboard: `http://143.110.254.40/harvester`
