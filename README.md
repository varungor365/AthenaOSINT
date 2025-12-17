# 🔍 AthenaOSINT - Advanced Open Source Intelligence Framework

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

## 📋 Overview

**AthenaOSINT** is a comprehensive, modular OSINT (Open Source Intelligence) framework designed for security researchers, penetration testers, and investigators. It aggregates data from multiple sources, performs intelligent analysis, and generates actionable intelligence reports.

### ✨ Key Features

- 🎯 **Multi-Source Intelligence**: Integrates 10+ OSINT tools and APIs
- 🤖 **Intelligent Automation**: Self-improving scans with entity correlation
- 🌐 **Web Dashboard**: Modern Flask-based interface with real-time updates
- 💬 **Telegram Bot**: Remote control via Telegram commands
- 📊 **Advanced Reporting**: JSON, HTML, CSV, and Excel output formats
- 🔗 **Recursive Scanning**: Deep investigation with relationship mapping
- ⚡ **Async Operations**: Fast, concurrent module execution
- 🛡️ **Privacy-Focused**: All data stays local

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/AthenaOSINT.git
cd AthenaOSINT

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up configuration
cp .env.example .env
# Edit .env with your API keys
```

### Basic Usage

#### Command Line Interface

```bash
# Simple scan
python athena.py run email@example.com

# Specify modules
python athena.py run johndoe --modules sherlock,holehe,leak_checker

# Choose output format
python athena.py run example.com --format html

# Deep scan with intelligence
python athena.py deepscan johndoe --depth 2
```

#### Web Interface

```bash
# Start web server
python run_web.py

# Open browser to http://localhost:5000
```

#### Telegram Bot

```bash
# Start bot
python run_bot.py

# Use commands:
# /scan <target>
# /quickscan <target>
# /fullscan <target>
# /deepscan <target> <depth>
```

## 🧩 Modules

| Module | Description | Input Type |
|--------|-------------|------------|
| **Sherlock** | Username enumeration across 300+ sites | Username |
| **Holehe** | Email account discovery | Email |
| **TheHarvester** | Email & domain reconnaissance | Domain/Email |
| **Subfinder** | Subdomain enumeration | Domain |
| **Leak Checker** | Data breach search (HIBP, Dehashed) | Email |
| **ExifTool** | File metadata extraction | File path |
| **Social Scanner** | Social media profile aggregation | Username/Email |
| **DNS Recon** | DNS records and zone transfers | Domain |

## ⚙️ Configuration

Create a `.env` file with your API keys:

```env
# Required for leak checking
HIBP_API_KEY=your_hibp_key
DEHASHED_API_KEY=your_dehashed_key
INTELX_API_KEY=your_intelx_key

# Required for Telegram bot
TELEGRAM_BOT_TOKEN=your_bot_token

# Optional
SHODAN_API_KEY=your_shodan_key
VIRUSTOTAL_API_KEY=your_vt_key
```

## 📊 Output Examples

### JSON Report
```json
{
  "target_query": "johndoe",
  "scan_timestamp": "2025-12-17T10:30:00",
  "usernames": {
    "github": "johndoe",
    "twitter": "johndoe89",
    "instagram": "john_doe"
  },
  "emails": ["john@example.com"],
  "breaches": [
    {
      "name": "Example Breach 2023",
      "date": "2023-05-15",
      "data_classes": ["Emails", "Passwords"]
    }
  ]
}
```

## 🏗️ Architecture

```
AthenaOSINT/
├── athena.py              # Main CLI entry point
├── run_web.py             # Web interface launcher
├── run_bot.py             # Telegram bot launcher
├── config/
│   ├── config.py          # Configuration manager
│   └── __init__.py
├── core/
│   ├── engine.py          # Main orchestrator
│   ├── validators.py      # Input validation
│   └── __init__.py
├── modules/               # OSINT tool integrations
│   ├── sherlock.py
│   ├── holehe.py
│   ├── theharvester.py
│   ├── leak_checker.py
│   └── ...
├── intelligence/          # AI/ML layer
│   ├── analyzer.py        # Pattern recognition
│   ├── automator.py       # Recursive scanning
│   └── __init__.py
├── web/                   # Flask application
│   ├── routes.py
│   ├── templates/
│   └── static/
└── bot/                   # Telegram integration
    ├── bot_handler.py
    └── __init__.py
```

## 🔒 Security & Ethics

⚠️ **Important Notice**:

- This tool is for **legal and ethical** use only
- Always obtain proper authorization before investigating targets
- Respect privacy laws and regulations (GDPR, CCPA, etc.)
- Do not use for harassment, stalking, or illegal activities
- The developers are not responsible for misuse

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-module`)
3. Commit your changes (`git commit -m 'Add amazing module'`)
4. Push to the branch (`git push origin feature/amazing-module`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Sherlock Project](https://github.com/sherlock-project/sherlock)
- [TheHarvester](https://github.com/laramies/theHarvester)
- [Holehe](https://github.com/megadose/holehe)
- [ProjectDiscovery](https://projectdiscovery.io/)

## 📧 Contact

For questions or suggestions:
- GitHub Issues: [Create an issue](https://github.com/yourusername/AthenaOSINT/issues)
- Email: security@example.com

---

**Disclaimer**: This software is provided "as is" without warranty. Use at your own risk.
