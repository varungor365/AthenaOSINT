# Mr.Holmes Integration for AthenaOSINT

## Overview

Mr.Holmes is a comprehensive OSINT (Open Source Intelligence) tool that has been integrated into AthenaOSINT. It provides powerful information gathering capabilities for:

- **Usernames**: Search across 500+ social media platforms
- **Email Addresses**: Validation, breach checking, and associated accounts
- **Phone Numbers**: Carrier info, location, timezone, and associated accounts
- **Domains/Websites**: WHOIS, DNS records, reputation checks, and more

**Original Repository**: https://github.com/Lucksi/Mr.Holmes

## Features

### Username Search
- Search username across 500+ social media sites
- Profile scraping (Instagram, Twitter, GitHub, etc.)
- Hypothesis generation about target's interests
- Geographic location from posts
- Interactive maps of visited places
- Relationship graphs

### Email Lookup
- Email validation
- Breach database checking
- Associated social media accounts
- Domain reputation analysis
- WHOIS integration

### Phone Number Search
- Carrier identification
- Geographic location
- Timezone information
- International format validation
- Associated online accounts
- Google/Yandex dorks

### Domain/Website OSINT
- WHOIS lookup with API integration
- DNS record enumeration
- Subdomain discovery
- Website reputation checking
- Technology fingerprinting
- SSL/TLS certificate analysis
- Port scanning
- Robots.txt analysis
- Traceroute

## Web Interface

Access Mr.Holmes through the AthenaOSINT dashboard:

1. Navigate to **http://your-server/mrholmes**
2. Select search type (Username, Email, Phone, or Domain)
3. Enter target information
4. Click "Start Search"

The web interface provides:
- Auto-detection of target type
- Proxy support (if configured)
- Real-time results display
- Export capabilities
- Search history

## Installation

Mr.Holmes can be installed automatically through the web interface:

1. Go to **/mrholmes**
2. Click "Install Mr.Holmes" button
3. Wait for installation to complete
4. Start searching!

**Manual Installation**:
```bash
cd ~
git clone https://github.com/Lucksi/Mr.Holmes.git .mrholmes
cd .mrholmes
pip3 install -r requirements.txt
```

## API Endpoints

### Check Installation Status
```bash
GET /api/mrholmes/status
```

Response:
```json
{
  "success": true,
  "installed": true,
  "install_dir": "/root/.mrholmes",
  "repo_url": "https://github.com/Lucksi/Mr.Holmes"
}
```

### Install Mr.Holmes
```bash
POST /api/mrholmes/install
```

### Run Search
```bash
POST /api/mrholmes/search
Content-Type: application/json

{
  "target": "johndoe",
  "target_type": "username",
  "use_proxy": false
}
```

Response:
```json
{
  "success": true,
  "result": {
    "target": "johndoe",
    "target_type": "username",
    "profiles_found": ["Twitter", "GitHub", "Instagram"],
    "social_accounts": {...},
    "scraped_data": {...}
  }
}
```

### Get Results
```bash
GET /api/mrholmes/results/{target_type}/{target}
```

## Module Integration

Use Mr.Holmes programmatically in Python:

```python
from modules.mrholmes import scan, MrHolmes

# Auto-detect target type
result = scan("johndoe")

# Specify target type
result = scan("user@example.com", target_type="email")

# Use MrHolmes class directly
mrholmes = MrHolmes()
result = mrholmes.search_username("johndoe", use_proxy=True)
result = mrholmes.search_email("user@example.com")
result = mrholmes.search_phone("+1234567890")
result = mrholmes.search_domain("example.com")
```

## Interactive Mode

**Note**: Mr.Holmes is primarily an interactive CLI tool. For full functionality, you can use it directly:

```bash
cd ~/.mrholmes
python3 MrHolmes.py
```

The web interface will provide instructions when interactive mode is required.

## Features in Detail

### Google/Yandex Dorks
- Automated dork generation for specific searches
- Date range filtering
- File type specification
- Custom dork lists

### Profile Scraping
- Instagram profile data, follower count, posts
- Twitter/X profile, tweets, location
- GitHub repositories, contributions
- LinkedIn professional info
- TikTok, YouTube, and more

### Report Generation
- Text reports (.txt)
- JSON export (.json)
- Encoded reports (.mh)
- PDF reports (graphs, maps)
- QR code file transfer

### Hypothesis Generation
Mr.Holmes can generate hypotheses about:
- Possible hobbies/interests based on social media activity
- Geographic locations frequently visited
- Activity patterns
- Professional interests

### Interactive Maps
- Leaflet.js integration
- Geographic location plotting
- Place visit history
- GPS coordinate extraction

## Configuration

Mr.Holmes stores configuration in:
- `~/.mrholmes/Configuration/Configuration.ini`
- API keys: `~/.mrholmes/Configuration/api_keys.json`

### WHOIS API Key
For enhanced domain/email lookups, configure WHOIS API:
1. Get API key from https://whois.whoisxmlapi.com
2. Add to configuration file
3. Restart search

## Advanced Features

### Proxy Support
- HTTP/HTTPS proxy configuration
- Proxy rotation
- Anonymous searching
- IP geolocation display

### Custom Site Lists
- Add custom sites to search
- NSFW site filtering
- Site-specific scraping rules
- JSON-based configuration

### Encoding/Decoding
- Encode reports for security
- Decode reports for viewing
- Password protection

## Dashboard Integration

The Mr.Holmes interface is accessible from:
- Main dashboard sidebar → "Mr.Holmes OSINT"
- Direct URL: `/mrholmes`
- Automation section in main menu

## Troubleshooting

### Installation Failed
```bash
# Check logs
tail -f /root/AthenaOSINT/logs/athena.log

# Manual installation
cd ~/.mrholmes
pip3 install -r requirements.txt
```

### Interactive Mode Required
Some advanced features require running Mr.Holmes directly:
```bash
cd ~/.mrholmes
python3 MrHolmes.py
```

### No Results Found
1. Verify target format (email format, phone with +country code)
2. Check if target exists on platforms
3. Try different search type
4. Enable proxy for anonymity

## Credits

**Mr.Holmes Original Creator**: Luca Garofalo (Lucksi)
- GitHub: https://github.com/Lucksi
- License: GPL-3.0
- Copyright: (C) 2021-2025 Lucksi

**Integration by**: AthenaOSINT Team

## License

This integration module follows AthenaOSINT's license while respecting Mr.Holmes' GPL-3.0 license.

## Support

For issues specific to:
- **Mr.Holmes functionality**: https://github.com/Lucksi/Mr.Holmes/issues
- **AthenaOSINT integration**: https://github.com/varungor365/AthenaOSINT/issues

## Links

- Mr.Holmes Website: https://lucksi.github.io/Mr.Holmes/
- Mr.Holmes GitHub: https://github.com/Lucksi/Mr.Holmes
- AthenaOSINT: https://github.com/varungor365/AthenaOSINT
