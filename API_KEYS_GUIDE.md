# API Key Auto-Gathering System

## Overview

AthenaOSINT now includes an intelligent API key management system that automatically gathers, rotates, and monitors API keys from free public services.

## Features

### 🔄 Automatic Rotation
- Distributes load across multiple keys per service
- Rotates when approaching rate limits
- Cooldown period for exhausted keys
- Health monitoring and failure detection

### 🎯 Supported Services (14+)

| Service | Free Tier | Daily Limit | Use Case |
|---------|-----------|-------------|----------|
| OpenWeatherMap | ✅ | 1,000,000 | Weather data |
| NewsAPI | ✅ | 100,000 | News articles |
| HaveIBeenPwned | ✅ | 1,000 | Breach checking |
| GitHub API | ✅ | 5,000/hour | Repository data |
| NASA API | ✅ | 1,000/hour | Space data |
| TMDb | ✅ | 1,000,000 | Movie/TV data |
| ExchangeRate-API | ✅ | 1,000 | Currency data |
| IP Geolocation | ✅ | 10,000 | Geolocation |
| Spotify | ✅ | 10,000/hour | Music data |
| Pexels | ✅ | 200/hour | Stock photos |
| Unsplash | ✅ | 50/hour | Stock photos |
| RapidAPI | ✅ | Varies | API marketplace |
| Groq | ✅ | 14,400 | AI inference |
| DeHashed | ❌ | 100 | Breach data |

## Usage

### Web Interface

**Access:** http://143.110.254.40/api-keys

Features:
- View all configured API services
- Add keys manually with auto-validation
- Auto-gather demo keys
- Monitor usage statistics
- Validate existing keys

### API Endpoints

#### Get Available Services
```bash
GET /api/keys/services
```

Returns signup URLs and configuration for all supported services.

#### Add API Key
```bash
POST /api/keys/add
Content-Type: application/json

{
  "service": "openweathermap",
  "key": "your_api_key_here"
}
```

Validates the key before adding to rotation pool.

#### Get Statistics
```bash
GET /api/keys/stats
```

Returns usage stats for all services.

#### Validate All Keys
```bash
POST /api/keys/validate
```

Tests all configured keys and marks failed ones.

#### Auto-Gather Keys
```bash
POST /api/keys/gather
```

Attempts to discover free demo keys from public sources.

### Programmatic Usage

```python
from core.api_rotator import get_rotator

# Get rotator instance
rotator = get_rotator()

# Get best available key for a service
key = rotator.get_key('openweathermap')

# Force rotation
key = rotator.rotate_key('openweathermap')

# Mark key as failed
rotator.mark_key_failed('openweathermap', key, 'Invalid key')

# Get stats
stats = rotator.get_service_stats('openweathermap')
```

## How It Works

### Key Rotation Algorithm

1. **Load Distribution**: Selects key with lowest usage count
2. **Threshold Monitoring**: Warns at 80% of daily limit
3. **Automatic Rotation**: Switches to fresh key when limit approached
4. **Cooldown**: Exhausted keys marked inactive for 24 hours
5. **Daily Reset**: Counters reset at midnight UTC

### Health Monitoring

- Validates keys on addition
- Tests endpoints periodically
- Marks failed keys automatically
- Tracks success/failure rates

### Auto-Discovery

The system can discover keys from:
- Public documentation (demo keys)
- GitHub repositories (public examples)
- API marketplaces (free tiers)

**Note:** Only gathers publicly documented demo keys - never scrapes private credentials.

## Manual Setup

### Getting Your Own Keys

1. **Visit API Keys page:** http://143.110.254.40/api-keys
2. **Click service signup link**
3. **Register for free account**
4. **Copy API key**
5. **Paste into "Add API Key" form**

### Example: OpenWeatherMap

```bash
# 1. Register
https://home.openweathermap.org/users/sign_up

# 2. Get API key
https://home.openweathermap.org/api_keys

# 3. Test
curl "https://api.openweathermap.org/data/2.5/weather?q=London&appid=YOUR_KEY"

# 4. Add to AthenaOSINT
curl -X POST http://143.110.254.40/api/keys/add \
  -H "Content-Type: application/json" \
  -d '{"service": "openweathermap", "key": "YOUR_KEY"}'
```

## Integration with OSINT Modules

Modules automatically use the rotator:

```python
# In your module
from core.api_rotator import get_rotator

def search_news(query):
    rotator = get_rotator()
    api_key = rotator.get_key('newsapi')
    
    if not api_key:
        raise Exception("No NewsAPI key available")
    
    # Use the key
    response = requests.get(
        f'https://newsapi.org/v2/everything?q={query}&apiKey={api_key}'
    )
    
    return response.json()
```

## Advanced Features

### Rate Limiting

Each service has configurable rate limits:

```python
service_configs = {
    'openweathermap': {
        'daily_limit': 1000000,
        'rate_limit': 60,  # per minute
    }
}
```

### Usage Tracking

```python
# Get detailed stats
stats = rotator.get_service_stats('openweathermap')

print(stats['total_calls'])    # Total API calls made
print(stats['failed_calls'])   # Failed requests
print(stats['active_keys'])    # Number of working keys
```

### Automated Validation

Run via cron to validate keys daily:

```bash
# Add to crontab
0 0 * * * curl -X POST http://localhost:5000/api/keys/validate
```

### Reset Daily Limits

```python
from core.api_rotator import get_rotator

rotator = get_rotator()
rotator.reset_daily_limits()
```

## Best Practices

1. **Multiple Keys**: Add 2-3 keys per service for redundancy
2. **Monitor Usage**: Check stats regularly
3. **Validate Weekly**: Run validation to catch expired keys
4. **Respect Limits**: Stay under 80% of daily quotas
5. **Use Free Tiers**: Most services offer generous free tiers

## Troubleshooting

### Key Marked as Failed

```python
# Check why
stats = rotator.get_service_stats('service_name')
for key_data in rotator.api_keys['service_name']:
    if key_data['status'] == 'failed':
        print(key_data['error'])
```

### No Keys Available

1. Check web UI: http://143.110.254.40/api-keys
2. Add keys manually
3. Run auto-gather: `curl -X POST /api/keys/gather`

### Rate Limit Exceeded

1. Add more keys for that service
2. Check usage stats
3. Wait for daily reset (midnight UTC)

## Security

- Keys stored in `data/api_keys.json` (600 permissions)
- Never logged in plaintext
- Masked in UI display
- Rotation prevents key exhaustion
- Failed keys quarantined

## Future Enhancements

- [ ] Encrypted key storage
- [ ] OAuth2 flow automation
- [ ] More service integrations
- [ ] Predictive rotation
- [ ] Cost tracking
- [ ] Multi-user key pools

## Contributing

To add a new service:

1. Add to `AUTO_SIGNUP_SERVICES` in `core/api_gatherer.py`
2. Add config to `service_configs` in `core/api_rotator.py`
3. Implement test endpoint
4. Update documentation

Example:

```python
'newservice': {
    'signup_url': 'https://newservice.com/signup',
    'test_endpoint': 'https://api.newservice.com/test?key={key}',
    'daily_limit': 10000,
    'free_tier': True
}
```
