# 🚀 AthenaOSINT v3.0 - Enterprise-Grade OSINT Framework

## 📦 Complete Feature Set

### Core Intelligence Gathering
✅ **27+ OSINT Modules** - Email lookup, username search, subdomain enumeration, breach monitoring
✅ **AI-Powered Analysis** - LLM-driven pattern recognition, anomaly detection, threat assessment
✅ **Graph Visualization** - Interactive relationship mapping, entity clustering
✅ **Automated Reporting** - PDF/JSON/CSV export, executive summaries

### High-Performance Infrastructure (16GB Optimized)
✅ **13B Parameter LLM** - Uncensored wizard-vicuna model with 8K context window
✅ **Parallel Scan Engine** - Execute 8 modules simultaneously (8x faster)
✅ **12 Concurrent Workers** - Handle 12+ simultaneous users (gevent-based)
✅ **Distributed Task Queue** - Process 6 scans concurrently with priority scheduling
✅ **Intelligent Caching** - 2GB LRU cache, deduplication, smart result merging

### AI-Powered Sentinel Mode
✅ **Change Detection** - Monitor websites for modifications with difflib
✅ **LLM Diff Analysis** - Understand WHAT changed and WHY it matters
✅ **Vulnerability Lab** - Integrated Nuclei scanner with critical/high filtering
✅ **Threat Scoring** - Automated risk assessment (0-100 scale)
✅ **Real-Time Alerts** - Socket.IO notifications for suspicious activity
✅ **Scheduled Monitoring** - APScheduler with customizable intervals

### Automation & Orchestration
✅ **Safe Automation Suite** - Playwright-based scraping with allowlist controls
✅ **Agent Brain** - Manual/auto modes with sandboxed command execution
✅ **Code Workspace** - VS Code-like editor with AI-assisted edits
✅ **Custom Scripts** - Upload and run Python scripts in isolated environment
✅ **Scheduled Tasks** - Cron-based recurring jobs

### Web Dashboard
✅ **Cyberpunk UI** - Modern dark theme with real-time updates
✅ **Login System** - Password-protected access
✅ **Live Notifications** - Socket.IO toast messages for all events
✅ **API Documentation** - RESTful endpoints for integration
✅ **Mobile Responsive** - Works on phones/tablets

## 📊 Performance Comparison

| Feature | v1.0 (8GB) | v3.0 (16GB) | Improvement |
|---------|------------|-------------|-------------|
| **LLM Model** | 7B params | 13B params | +86% parameters |
| **Context Window** | 2K tokens | 8K tokens | 4x larger |
| **Flask Workers** | 1-2 | 12 | 6x concurrency |
| **Parallel Modules** | Sequential | 8 simultaneous | 8x faster |
| **Concurrent Scans** | 1 | 6 | 6x throughput |
| **Caching** | None | 2GB LRU | Instant dedup |
| **Inference Threads** | 1 | 8 | 8x CPU utilization |
| **Max Users** | 1-2 | 12+ | 6x capacity |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Browser/API Client                   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                    ┌───────▼────────┐
                    │  Nginx Proxy   │
                    │  (Port 80/443) │
                    └───────┬────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼───────┐  ┌────────▼────────┐  ┌──────▼──────┐
│ Flask Web App │  │  AI Orchestrator │  │   Ollama    │
│ 12 workers    │  │  (FastAPI)       │  │   (LLM)     │
│ Port 5000     │  │  Port 8081       │  │  Port 11434 │
└───────┬───────┘  └────────┬────────┘  └──────┬──────┘
        │                   │                   │
        └───────────────────┴───────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐ ┌────────▼────────┐ ┌───────▼──────┐
│ Parallel Engine│ │ Sentinel Monitor│ │ Task Queue   │
│ 8 modules/scan │ │ APScheduler     │ │ 6 concurrent │
└───────┬────────┘ └────────┬────────┘ └───────┬──────┘
        │                   │                   │
        └───────────────────┴───────────────────┘
                            │
                ┌───────────▼───────────┐
                │  27+ OSINT Modules    │
                │  (sherlock, nuclei,   │
                │   subfinder, etc.)    │
                └───────────────────────┘
```

## 📁 New Files & Components

### Core System
- **`core/parallel_engine.py`** (380 lines) - Thread pool executor, distributed queue
- **`core/caching.py`** (300 lines) - LRU cache, deduplication, result merging
- **`core/scheduler.py`** (90 lines) - APScheduler for Sentinel jobs
- **`config/production.py`** (60 lines) - 16GB RAM configuration

### Intelligence Layer
- **`intelligence/ai_sentinel.py`** (380 lines) - LLM diff analysis, threat assessment
- **`modules/headless_monitor.py`** (enhanced) - Change detection with difflib
- **`modules/nuclei.py`** (enhanced) - Critical/High vulnerability filtering

### Web Interface
- **`web/templates/sentinel.html`** - Sentinel dashboard UI
- **`web/routes.py`** (enhanced) - 8 new Sentinel API endpoints

### Deployment
- **`scripts/deploy_16gb.sh`** - Automated deployment script
- **`UPGRADE_16GB.md`** - Complete upgrade documentation
- **`QUICK_REFERENCE.md`** - Quick command reference

## 🎯 Use Cases

### 1. Corporate Security Monitoring
- Monitor company domains for subdomain takeovers
- Detect leaked credentials in data breaches
- Track unauthorized mentions on social media
- Alert on SSL/DNS changes

### 2. Penetration Testing
- Automated reconnaissance phase
- Parallel vulnerability scanning
- Asset discovery and enumeration
- Evidence collection and reporting

### 3. Threat Intelligence
- Monitor adversary infrastructure
- Track IOCs across multiple sources
- Anomaly detection on dark web forums
- Real-time change alerts

### 4. Incident Response
- Quick OSINT gathering on suspicious IPs/domains
- Breach exposure checks for employees
- Historical data analysis
- Automated intelligence briefs

### 5. Brand Protection
- Monitor for phishing domains
- Track leaked customer data
- Detect fake social media profiles
- Alert on brand impersonation

## 🔧 Configuration Options

### Tunable Performance Parameters

```python
# config/production.py

# Scan Engine (adjust based on workload)
SCAN_CONFIG = {
    'max_parallel_modules': 8,        # 4-12 recommended
    'max_concurrent_scans': 6,        # 2-10 recommended
    'thread_pool_size': 16,           # 8-32 recommended
    'enable_caching': True,
}

# Flask Workers (adjust for user count)
GUNICORN_CONFIG = {
    'workers': 12,                    # 4-16 recommended
    'worker_class': 'gevent',
    'worker_connections': 1000,       # 500-2000 recommended
}

# LLM Settings (adjust for quality vs speed)
LLM_CONFIG = {
    'model': 'wizard-vicuna-uncensored:13b',  # 7b|13b|34b
    'context_size': 8192,             # 2048-8192
    'threads': 8,                     # 4-12 recommended
    'parallel_requests': 4,           # 2-8 recommended
}

# Memory Management
MEMORY_CONFIG = {
    'cache_max_size_mb': 2048,        # 512-4096 recommended
    'max_memory_percent': 85,         # 70-90 recommended
}
```

## 📈 Expected Performance

### Scan Throughput
- **Before:** ~2-3 minutes for full scan (20+ modules sequential)
- **After:** ~15-20 seconds for same scan (8 modules parallel)
- **Speedup:** 8-10x faster

### User Capacity
- **Before:** 1-2 simultaneous users
- **After:** 12+ simultaneous users
- **Capacity:** 6x improvement

### AI Analysis Quality
- **Before:** 7B model, limited context
- **After:** 13B model, 4x larger context
- **Quality:** Better reasoning, fewer hallucinations

### Resource Efficiency
- **Cache hit rate:** 60-80% for duplicate scans
- **RAM utilization:** 85-90% (optimal)
- **CPU utilization:** 60-80% during scans

## 🛡️ Security Features

### Sandboxed Execution
- Commands restricted to allowlist (ls, cat, python, etc.)
- Write operations limited to `/opt/agent/workdir`
- Timeout protection (60-300s)
- No shell access from web interface

### Authentication
- Password-protected dashboard
- Session management
- HTTPS support (via nginx)

### Rate Limiting
- API throttling (50 requests/min per module)
- Scan queue limits (max 6 concurrent)
- Resource monitoring

### Data Protection
- No credential storage (modules query APIs directly)
- Scan results stored locally only
- Optional encryption for sensitive data

## 📚 Documentation

- **[UPGRADE_16GB.md](UPGRADE_16GB.md)** - Complete upgrade guide
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Command cheat sheet
- **[DEPLOY_INSTRUCTIONS.md](DEPLOY_INSTRUCTIONS.md)** - Deployment walkthrough
- **[README.md](README.md)** - Project overview
- **[API_KEYS_GUIDE.md](API_KEYS_GUIDE.md)** - API configuration

## 🚀 Quick Start

### 1. Deploy to Droplet
```bash
ssh root@143.110.254.40
cd /root/AthenaOSINT
git pull origin main
chmod +x scripts/deploy_16gb.sh
./scripts/deploy_16gb.sh
```

### 2. Verify Deployment
```bash
systemctl status athena-web agent-orchestrator
curl http://127.0.0.1:8081/api/health
```

### 3. Access Dashboard
Open browser: `http://143.110.254.40`

### 4. Run First Scan
- Navigate to main dashboard
- Enter target (email/domain/username)
- Select modules or use "All"
- Click "Start Scan"
- Watch parallel execution in real-time

### 5. Enable Sentinel
- Go to `/sentinel`
- Add domains to watchlist
- Enable vulnerability lab
- Receive AI-powered alerts

## 🎓 Training Resources

### Example API Calls

**Start Parallel Scan:**
```bash
curl -X POST http://localhost:5000/api/scan \
  -H "Content-Type: application/json" \
  -d '{
    "target": "example.com",
    "modules": ["subfinder", "theharvester", "nuclei"],
    "use_intelligence": true
  }'
```

**Get Scan Status:**
```bash
curl http://localhost:5000/api/history/SCAN_ID
```

**AI Diff Analysis:**
```bash
curl -X POST http://localhost:5000/api/sentinel/analyze-diff \
  -H "Content-Type: application/json" \
  -d '{
    "old_content": "Original content",
    "new_content": "Modified content",
    "url": "https://target.com"
  }'
```

### Python SDK Example

```python
import requests

# Start scan
response = requests.post('http://localhost:5000/api/scan', json={
    'target': 'example.com',
    'modules': ['all']
})
scan_id = response.json()['scan_id']

# Poll for results
import time
while True:
    status = requests.get(f'http://localhost:5000/api/history/{scan_id}')
    if status.json()['status'] == 'completed':
        results = status.json()
        break
    time.sleep(5)

print(f"Found {len(results['emails'])} emails")
print(f"Found {len(results['subdomains'])} subdomains")
```

## 🏆 Feature Highlights

### What Makes v3.0 Enterprise-Grade

1. **Production-Ready Performance**
   - 12 workers handle enterprise user loads
   - Parallel execution for time-critical investigations
   - Intelligent caching prevents redundant work

2. **AI-First Intelligence**
   - 13B LLM analyzes findings in context
   - Automated threat scoring and prioritization
   - Natural language interaction with AI assistant

3. **Real-Time Monitoring**
   - Sentinel mode for continuous surveillance
   - Socket.IO live updates across all features
   - Scheduled jobs for recurring tasks

4. **Developer-Friendly**
   - RESTful API for integration
   - Python SDK examples
   - Modular architecture for easy extension

5. **Enterprise Scalability**
   - Distributed task queue
   - Resource-aware scheduling
   - Graceful degradation under load

---

## 📞 Support & Contributions

**Repository:** https://github.com/varungor365/AthenaOSINT
**Version:** 3.0
**Release Date:** December 21, 2025
**License:** MIT

**System Requirements:**
- 16GB RAM (minimum 8GB)
- 4 vCPUs (minimum 2)
- 160GB SSD
- Ubuntu 22.04 LTS

**Recommended Setup:**
- DigitalOcean 16GB Droplet
- Ollama with wizard-vicuna-uncensored:13b
- Nginx reverse proxy with SSL
- Scheduled backups

---

**Built with ❤️ for the OSINT community**
