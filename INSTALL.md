# Installation & Setup Guide

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git
- Virtual environment tool (venv, conda, etc.)

## Step 1: Clone or Download the Project

```bash
cd d:\osint-website
# or wherever you have the project
```

## Step 2: Create Virtual Environment

### Windows (PowerShell)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Windows (CMD)
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

### Linux/Mac
```bash
python3 -m venv venv
source venv/bin/activate
```

## Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Note:** Some dependencies might fail if they're not available. The core functionality will still work.

## Step 4: Configure Environment Variables

1. Copy the example configuration:
```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

2. Edit `.env` file with your favorite text editor and add your API keys:

```env
# Required for full functionality
HIBP_API_KEY=your_hibp_api_key_here
DEHASHED_API_KEY=your_dehashed_key_here
DEHASHED_USERNAME=your_dehashed_username
INTELX_API_KEY=your_intelx_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Optional
SHODAN_API_KEY=your_shodan_key
VIRUSTOTAL_API_KEY=your_virustotal_key
```

### How to Get API Keys:

1. **HIBP (Have I Been Pwned)**: https://haveibeenpwned.com/API/Key
   - Paid service ($3.50/month)
   - Required for breach checking

2. **Dehashed**: https://dehashed.com/
   - Paid service
   - Advanced leak searching

3. **Intelligence X**: https://intelx.io/
   - Free tier available
   - Data breach search

4. **Telegram Bot Token**: https://t.me/BotFather
   - Free
   - Talk to @BotFather on Telegram
   - Use `/newbot` command

5. **Shodan** (Optional): https://account.shodan.io/
   - Free tier available

6. **VirusTotal** (Optional): https://www.virustotal.com/
   - Free tier available

**Note:** The tool will work without API keys, but some modules will be disabled.

## Step 5: Install External Tools (Optional but Recommended)

### theHarvester
```bash
# Install via pip
pip install theHarvester

# Or from GitHub
git clone https://github.com/laramies/theHarvester
cd theHarvester
pip install -r requirements.txt
python theHarvester.py -h
```

### Subfinder
```bash
# Download from: https://github.com/projectdiscovery/subfinder/releases
# Extract and add to PATH

# Or install with Go:
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
```

### ExifTool
```bash
# Windows: Download from https://exiftool.org/
# Extract and add to PATH

# Linux:
sudo apt-get install libimage-exiftool-perl

# Mac:
brew install exiftool
```

## Step 6: Test Installation

```bash
# Check configuration
python athena.py config-check

# List available modules
python athena.py modules

# Run a test scan (won't make actual requests without API keys)
python athena.py run test@example.com --modules leak_checker
```

## Step 7: Run the Application

### Command Line Interface
```bash
python athena.py run email@example.com
python athena.py run johndoe --modules sherlock,holehe
python athena.py run example.com --format html
```

### Web Interface
```bash
python run_web.py
# Then open: http://localhost:5000
```

### Telegram Bot
```bash
python run_bot.py
# Then talk to your bot on Telegram
```

## Troubleshooting

### Import Errors
If you see "Import could not be resolved" errors in your editor, these are expected before installation. Install dependencies with `pip install -r requirements.txt`.

### Module Not Found
```bash
# Make sure you're in the virtual environment
# Windows
.\venv\Scripts\Activate.ps1

# Then reinstall
pip install -r requirements.txt
```

### API Errors
- Check your `.env` file has correct API keys
- Verify API keys are active and have remaining quota
- Some APIs require payment

### External Tools Not Found
- Make sure tools are in your system PATH
- Or provide full path to tools
- Some modules will skip if tools aren't available

### Permission Errors
```bash
# Windows: Run PowerShell as Administrator
# Linux/Mac: Use sudo for system-wide installation
```

## Directory Structure After Installation

```
osint-website/
├── venv/                   # Virtual environment
├── data/                   # Created automatically
├── reports/                # Created automatically
├── logs/                   # Created automatically
├── .env                    # Your configuration (don't commit!)
├── athena.py              # Main CLI
├── run_web.py             # Web server
├── run_bot.py             # Telegram bot
├── requirements.txt
├── README.md
└── ... (other files)
```

## Next Steps

1. Read the [README.md](README.md) for usage examples
2. Check [PROJECT_STATUS.md](PROJECT_STATUS.md) for feature status
3. Run `python athena.py --help` for all commands
4. Start with simple scans before using deep scans

## Security Notes

- **Never commit `.env` file** - it contains your API keys
- Keep your API keys secure
- This tool is for legal and authorized use only
- Always get permission before investigating targets
- Respect rate limits and terms of service

## Getting Help

- Check the logs in `logs/` directory
- Use `python athena.py --help` for command help
- Create an issue on GitHub
- Read the documentation in each module

## Updating

```bash
# Activate virtual environment
# Then reinstall requirements
pip install --upgrade -r requirements.txt
```

---

**Installation complete! 🎉**

Start scanning with:
```bash
python athena.py run your-target@example.com
```
