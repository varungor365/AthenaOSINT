# 🦅 AthenaOSINT Complete Startup Guide

## Quick Start Commands

### For Development/Local Testing

```bash
# Clone and setup
git clone https://github.com/varungor365/AthenaOSINT.git
cd AthenaOSINT

# Run the startup script
chmod +x start_athena.sh
./start_athena.sh
```

### For Production (DigitalOcean/VPS)

```bash
# SSH into your server
ssh varun@143.110.254.40

# Clone repository
git clone https://github.com/varungor365/AthenaOSINT.git
cd AthenaOSINT

# Run production setup
chmod +x production_setup.sh
./production_setup.sh

# Configure .env file
nano .env
# Add your API keys (see below)

# Restart service
sudo systemctl restart athena.service
```

## Configuration

### 1. Create .env File

```bash
cp .env.example .env
nano .env
```

### 2. Add Your API Keys

```env
# Telegram Bot (Required for bot)
TELEGRAM_BOT_TOKEN=8154649770:AAEWtKW4a2srP0T9aWC5-0VBIJNzIAptx2w

# AI/LLM (Required for Jarvis AI features)
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_key_here

# OSINT APIs (Optional but recommended)
HIBP_API_KEY=your_hibp_key
DEHASHED_API_KEY=your_dehashed_key
SHODAN_API_KEY=your_shodan_key
```

## System Components

### 1. Web Dashboard
- **URL**: http://143.110.254.40 (or localhost:5000)
- **Features**:
  - ✅ Module selection with descriptions
  - ✅ Search and filter modules
  - ✅ Select all/deselect all
  - ✅ Live service status checking
  - ✅ Real-time progress updates
  - ✅ Interactive results display

### 2. Telegram Bot
- **Username**: @ANTHENAa_bot
- **Admin**: @hackingmasterr (ID: 796354588)
- **Commands**:
  - `/start` - Welcome message with full menu
  - `/scan <target>` - Standard OSINT scan
  - `/quickscan <target>` - Fast 2-3 min scan
  - `/fullscan <target>` - Comprehensive 5-10 min scan
  - `/deepscan <target> [depth]` - Recursive intelligence scan
  - `/modules` - View all modules with descriptions
  - `/status` - Check scan progress

### 3. Available Modules (18 Total)

#### Social Media & Username
- 👤 **Sherlock** - Find usernames across 400+ social networks
- 📱 **Profile Scraper** - Extract detailed social media profile data

#### Email Intelligence
- 📧 **Holehe** - Check email registration on 120+ websites
- ✉️ **Email Permutator** - Generate and verify email variations

#### Security & Breaches
- 🔓 **Leak Checker** - Search data breaches and password leaks
- 🛡️ **Nuclei** - Scan for vulnerabilities
- 🐦 **Canary Checker** - Detect honeypots

#### Reconnaissance
- 🌐 **TheHarvester** - Gather emails, subdomains, IPs
- 🔍 **Subfinder** - Discover subdomains
- 🌍 **DNSDumpster** - DNS reconnaissance
- 🔎 **Auto Dorker** - Automated Google Dorks

#### Cloud & Blockchain
- ☁️ **Cloud Hunter** - Find exposed cloud storage
- ₿ **Crypto Hunter** - Track crypto addresses

#### Forensics & Analysis
- 📷 **ExifTool** - Extract image metadata
- 📸 **OCR** - Extract text from images
- 💭 **Sentiment** - Analyze online reputation
- ⏰ **Wayback** - Access archived websites

#### Business Intelligence
- 💼 **Job Hunter** - Analyze job postings for tech stack

## Service Management

### Check All Services

```bash
# System check script
./start_athena.sh
# Select option 4 (System Check Only)
```

### Start Services

#### Development Mode
```bash
# Web only
python run_web.py

# Bot only
python run_bot.py

# Both (use tmux or screen)
tmux new -s web "python run_web.py"
tmux new -s bot "python run_bot.py"
```

#### Production Mode
```bash
# Status
sudo systemctl status athena.service

# Start
sudo systemctl start athena.service

# Stop
sudo systemctl stop athena.service

# Restart
sudo systemctl restart athena.service

# View logs
sudo journalctl -u athena.service -f
```

### Update Deployment

```bash
cd /root/AthenaOSINT
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart athena.service
```

## URLs & Access

### Web Dashboard
- **Production**: http://143.110.254.40
- **Local**: http://localhost:5000

### Telegram Bot
- **Username**: @ANTHENAa_bot
- **Link**: https://t.me/ANTHENAa_bot

### GitHub
- **Repository**: https://github.com/varungor365/AthenaOSINT

## Monitoring

### Service Status Dashboard
Click "🔄 Check Services" button in web dashboard to see:
- 🟢 Live services
- 🔴 Down services
- Real-time status updates

### Logs
```bash
# Web service logs
sudo journalctl -u athena.service -n 100

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Application logs
tail -f logs/*.log
```

## Troubleshooting

### Web Dashboard Not Loading
```bash
# Check if service is running
sudo systemctl status athena.service

# Check nginx
sudo systemctl status nginx

# Restart both
sudo systemctl restart athena.service nginx
```

### Telegram Bot Not Responding
```bash
# Check if token is configured
grep TELEGRAM_BOT_TOKEN .env

# Test bot manually
python run_bot.py
```

### Module Not Working
```bash
# Check service status in dashboard
# Click "🔄 Check Services"

# Install missing tools
sudo apt-get install exiftool tesseract-ocr

# For Go tools (subfinder, nuclei)
# See installation guides at their GitHub repos
```

## Security Notes

1. **Never commit .env** - It's in .gitignore
2. **Change SECRET_KEY** in .env for production
3. **Use HTTPS** with Let's Encrypt (see PRODUCTION_GUIDE.md)
4. **Firewall**: Only open ports 80, 443, 22
5. **API Rate Limits**: Respect service rate limits
6. **OPSEC**: Use TOR_ENABLED=True for sensitive scans

## Support

- **Issues**: https://github.com/varungor365/AthenaOSINT/issues
- **Admin**: @hackingmasterr on Telegram
- **Docs**: Check README.md and PRODUCTION_GUIDE.md

---

**🦅 AthenaOSINT - Advanced Open Source Intelligence Framework**

*Use responsibly and ethically. Respect privacy and legal boundaries.*
