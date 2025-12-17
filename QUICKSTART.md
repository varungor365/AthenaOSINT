# 🎯 AthenaOSINT - Quick Start Guide

## ⚡ 5-Minute Setup

### 1. Install Dependencies

```powershell
# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install packages
pip install -r requirements.txt
```

### 2. Configure (Minimal)

```powershell
# Copy environment template
copy .env.example .env

# Edit .env (optional - tool works without API keys for basic functionality)
notepad .env
```

### 3. Run Your First Scan

```powershell
# Test the CLI
python athena.py modules

# Simple scan (works without API keys)
python athena.py run johndoe --modules sherlock,holehe

# With leak checking (requires HIBP API key)
python athena.py run test@example.com --modules leak_checker
```

## 📊 Usage Examples

### Command Line

```bash
# Basic email scan
python athena.py run john.doe@example.com

# Username scan with specific modules
python athena.py run johndoe --modules sherlock,holehe

# Domain scan with HTML report
python athena.py run example.com --format html

# Deep recursive scan
python athena.py deepscan johndoe --depth 2

# Check configuration
python athena.py config-check

# List modules
python athena.py modules

# Extract file metadata
python athena.py extract-metadata photo.jpg
```

### Web Interface

```bash
# Start web server
python run_web.py

# Open browser to http://localhost:5000
```

**Web Features:**
- Real-time progress updates
- Interactive module selection
- Visual results dashboard
- Download reports (JSON, HTML)
- Mobile-friendly interface

### Telegram Bot

```bash
# Configure bot token in .env first
# TELEGRAM_BOT_TOKEN=your_token_here

# Start bot
python run_bot.py

# Talk to your bot on Telegram
```

**Bot Commands:**
- `/start` - Welcome message
- `/scan <target>` - Standard scan
- `/quickscan <target>` - Fast scan
- `/fullscan <target>` - Complete scan
- `/deepscan <target> <depth>` - Recursive scan
- `/modules` - List modules
- `/status` - Check scan status

## 🔧 Configuration Options

### .env File

```env
# Breach Checking (Optional)
HIBP_API_KEY=your_key                 # Have I Been Pwned
DEHASHED_API_KEY=your_key             # Dehashed
INTELX_API_KEY=your_key               # Intelligence X

# Bot (Optional)
TELEGRAM_BOT_TOKEN=your_token         # Telegram bot

# Web Server
FLASK_HOST=0.0.0.0                    # Listen on all interfaces
FLASK_PORT=5000                       # Port number

# Application Settings
LOG_LEVEL=INFO                        # DEBUG, INFO, WARNING, ERROR
MAX_SCAN_DEPTH=3                      # Maximum recursive depth
RATE_LIMIT=60                         # Requests per minute
MODULE_TIMEOUT=300                    # Module timeout (seconds)
```

## 📦 Available Modules

| Module | Target Type | Description | External Tool |
|--------|-------------|-------------|---------------|
| **sherlock** | Username | Search 300+ social media sites | Python library |
| **holehe** | Email | Check email accounts on services | Python library |
| **leak_checker** | Email | Data breach search (HIBP, Dehashed) | API keys |
| **theharvester** | Domain/Email | Email & domain reconnaissance | CLI tool |
| **subfinder** | Domain | Subdomain enumeration | CLI tool |
| **exiftool** | File | Extract file metadata | CLI tool |

### Module Status

✅ **Works without setup:** sherlock, holehe (if installed)  
🔑 **Requires API keys:** leak_checker  
🛠️ **Requires external tools:** theharvester, subfinder, exiftool  

## 🎨 Report Formats

### JSON
```bash
python athena.py run target --format json
```
- Machine-readable
- Full data export
- Easy to parse

### HTML
```bash
python athena.py run target --format html
```
- Beautiful web page
- Styled tables and lists
- Perfect for presentations

### CSV
```bash
python athena.py run target --format csv
```
- Spreadsheet compatible
- Easy filtering
- Data analysis ready

### All Formats
```bash
python athena.py run target --format all
```

## 🚀 Advanced Features

### Intelligence Analysis

```bash
# Enable pattern recognition and entity correlation
python athena.py run target --use-intelligence
```

Features:
- Extract related domains from emails
- Generate username variations
- Infer password policies
- Map entity relationships
- Calculate risk scores

### Recursive Scanning

```bash
# Automatically discover and scan related targets
python athena.py deepscan johndoe --depth 2
```

Features:
- Depth-first investigation
- Automatic target discovery
- Duplicate detection
- Progress tracking
- Safety limits

## 💡 Pro Tips

1. **Start Small:** Test with single modules before running full scans
2. **Use Intelligence:** Enable `--use-intelligence` for better insights
3. **Check Logs:** Review `logs/` directory for detailed information
4. **Rate Limits:** Respect API rate limits to avoid blocks
5. **API Keys:** Get HIBP key for breach checking ($3.50/month)
6. **External Tools:** Install theHarvester and Subfinder for best results

## 🔒 Legal & Ethical Use

⚠️ **Important:**
- **Authorization Required:** Only scan targets you're authorized to investigate
- **Respect Privacy:** Follow GDPR, CCPA, and local privacy laws
- **No Harassment:** Do not use for stalking or harassment
- **Terms of Service:** Respect API provider terms
- **Rate Limits:** Don't abuse free tiers

**Disclaimer:** Developers are not responsible for misuse.

## 🐛 Common Issues

### "Module not found"
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### "API key not configured"
```bash
# Check .env file exists and has valid keys
python athena.py config-check
```

### "External tool not found"
```bash
# Install the tool or skip it
python athena.py modules  # Check which modules are available
```

### Web server won't start
```bash
# Check port not in use
netstat -ano | findstr :5000

# Or change port in .env
FLASK_PORT=8080
```

## 📚 Learn More

- **Full Documentation:** [README.md](README.md)
- **Installation Guide:** [INSTALL.md](INSTALL.md)
- **Project Status:** [PROJECT_STATUS.md](PROJECT_STATUS.md)
- **Help Command:** `python athena.py --help`

## 🎯 Real-World Examples

### Investigate Compromised Email
```bash
python athena.py run victim@company.com --modules leak_checker --format html
```

### Find Social Media Profiles
```bash
python athena.py run johndoe --modules sherlock --format json
```

### Domain Reconnaissance
```bash
python athena.py run target-company.com --modules theharvester,subfinder --format csv
```

### Complete Investigation
```bash
python athena.py deepscan suspect@email.com --depth 2 --use-intelligence
```

---

## ✅ You're Ready!

Start investigating with:
```bash
python athena.py run your-target
```

**Questions?** Check the full [README.md](README.md) or create an issue.

**Happy Investigating! 🔍**
