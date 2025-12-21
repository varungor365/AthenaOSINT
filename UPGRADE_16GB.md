# AthenaOSINT v3.0 - 16GB RAM Optimization Complete

## 🚀 What's New

### Performance Upgrades
- **13B Parameter LLM** - Upgraded from 7B to wizard-vicuna-uncensored:13b
- **8K Context Window** - 4x larger context for better analysis (was 2K)
- **12 Flask Workers** - Increased from 1-2 to 12 concurrent workers (gevent)
- **Parallel Scan Engine** - Run up to 8 modules simultaneously
- **Distributed Task Queue** - Support 6 concurrent scans
- **Intelligent Caching** - 2GB in-memory cache with TTL and LRU eviction

### New Capabilities
1. **Parallel Execution Framework** (`core/parallel_engine.py`)
   - Thread pool executor with 8-16 workers
   - Concurrent module execution
   - Progress callbacks and timeout management
   - Distributed scan queue with priority scheduling

2. **Intelligent Caching System** (`core/caching.py`)
   - Thread-safe LRU cache (2GB max)
   - Automatic deduplication
   - Smart result merging
   - Hit rate tracking

3. **AI-Powered Sentinel** (`intelligence/ai_sentinel.py`)
   - LLM-based diff analysis (understands WHAT changed and WHY)
   - Automated threat assessment
   - Anomaly detection with baseline comparison
   - Executive intelligence report generation
   - Real-time threat scoring (0-100)

4. **Production Configuration** (`config/production.py`)
   - Optimized for 16GB RAM
   - Tunable worker counts, timeouts, cache sizes
   - Memory management settings
   - Compression and storage optimization

### API Endpoints Added
- `GET /sentinel` - Sentinel monitoring dashboard
- `POST /api/sentinel/add` - Create monitoring job
- `GET /api/sentinel/jobs` - List active monitors
- `POST /api/sentinel/remove` - Delete monitoring job
- `POST /api/sentinel/analyze-diff` - AI diff analysis
- `POST /api/sentinel/analyze-vuln` - AI vulnerability assessment
- `GET /api/sentinel/alerts` - Recent alerts feed

## 📊 Performance Metrics

### Before (8GB RAM)
- Model: wizard-vicuna-uncensored:7b
- Context: 2048 tokens
- Workers: 1-2
- Parallel modules: 1 (sequential)
- Concurrent scans: 1
- Inference: Single-threaded

### After (16GB RAM)
- Model: wizard-vicuna-uncensored:13b  
- Context: 8192 tokens (4x larger)
- Workers: 12 (6x more)
- Parallel modules: 8 (8x faster scans)
- Concurrent scans: 6
- Inference: 8 threads, 4 parallel requests

**Expected Improvements:**
- Scan throughput: **8-10x faster** (parallel modules)
- Dashboard concurrency: **6x more users** (12 workers)
- LLM quality: **Better analysis** (13B vs 7B)
- LLM context: **4x more context** (8K vs 2K)

## 🛠️ Deployment

### On Droplet (16GB RAM)
```bash
# SSH to droplet
ssh root@143.110.254.40

# Navigate to project
cd /root/AthenaOSINT

# Pull updates
git pull origin main

# Run deployment script
chmod +x scripts/deploy_16gb.sh
./scripts/deploy_16gb.sh
```

The deployment script will:
1. Update codebase
2. Install dependencies (including gevent)
3. Configure Ollama for 16GB RAM
4. Pull 13B model
5. Update orchestrator configuration
6. Create optimized gunicorn config
7. Update systemd services
8. Optimize nginx
9. Restart all services
10. Verify deployment

### Manual Verification
```bash
# Check services
systemctl status athena-web
systemctl status agent-orchestrator

# Verify model
curl http://127.0.0.1:8081/api/health

# Check workers
ps aux | grep gunicorn

# Monitor logs
journalctl -u athena-web -f
```

## 🧪 Testing New Features

### 1. Parallel Scan Engine
```python
from core.parallel_engine import ParallelScanEngine
from core.engine import Profile

engine = ParallelScanEngine(max_workers=8)
profile = Profile(target_query="example.com")

result = engine.run_parallel_scan(
    target="example.com",
    modules=['subfinder', 'theharvester', 'shodan', 'wayback'],
    profile=profile
)

print(f"Completed {result['completed']}/{result['total']} in {result['elapsed']:.1f}s")
```

### 2. Intelligent Caching
```python
from core.caching import get_cache

cache = get_cache()
cache.set('scan_123', results, ttl=3600)
cached = cache.get('scan_123')
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']:.1f}%")
```

### 3. AI Sentinel Analysis
```python
from intelligence.ai_sentinel import get_ai_analyzer

analyzer = get_ai_analyzer()
analysis = analyzer.analyze_diff(
    old_content="Original page content",
    new_content="Modified page with malware link",
    url="https://target.com"
)

print(f"Severity: {analysis['severity']}")
print(f"Threat Score: {analysis['threat_score']}/100")
print(f"Summary: {analysis['summary']}")
```

### 4. Distributed Scan Queue
```python
from core.parallel_engine import get_scan_queue

queue = get_scan_queue()
queue.enqueue_scan(
    scan_id="scan_456",
    target="example.com",
    modules=['all'],
    priority=10,
    callback=lambda status, result, profile: print(f"Scan {status}")
)
```

## 📈 Resource Usage

### Expected RAM Distribution (16GB Total)
- **System:** ~1GB
- **Ollama (13B model):** ~8-9GB (loaded)
- **Flask workers (12x):** ~3-4GB
- **Cache:** ~2GB (max)
- **Available:** ~1-2GB buffer

### Monitoring
```bash
# RAM usage
free -h

# Per-process memory
ps aux --sort=-%mem | head -15

# Cache statistics
curl http://localhost:5000/api/system/stats
```

## ⚙️ Configuration Files

### `gunicorn.conf.py` (auto-created by deployment script)
- 12 gevent workers
- 4 threads per worker
- 1000 connections per worker
- 300s timeout
- RAM-backed temp directory (`/dev/shm`)

### `config/production.py`
- `SCAN_CONFIG['max_parallel_modules']`: 8
- `SCAN_CONFIG['max_concurrent_scans']`: 6
- `LLM_CONFIG['context_size']`: 8192
- `MEMORY_CONFIG['cache_max_size_mb']`: 2048

## 🔧 Tuning Parameters

### Reduce Resource Usage (if needed)
```python
# config/production.py
SCAN_CONFIG['max_parallel_modules'] = 4  # Lower to 4
GUNICORN_CONFIG['workers'] = 8  # Reduce to 8 workers
MEMORY_CONFIG['cache_max_size_mb'] = 1024  # 1GB cache
```

### Increase Performance (if headroom available)
```python
SCAN_CONFIG['max_parallel_modules'] = 12  # More parallelism
GUNICORN_CONFIG['workers'] = 16  # More workers
LLM_CONFIG['parallel_requests'] = 6  # More concurrent LLM calls
```

## 🐛 Troubleshooting

### OOM (Out of Memory)
- Reduce `GUNICORN_CONFIG['workers']` to 8
- Lower `cache_max_size_mb` to 1024
- Use smaller model: `wizard-vicuna-uncensored:7b`

### Slow LLM Inference
- Increase `LLM_CONFIG['threads']` to 12
- Enable model quantization (Q4)
- Check Ollama logs: `journalctl -u ollama -f`

### High CPU Usage
- Reduce `max_parallel_modules` to 4
- Lower gunicorn workers to 8
- Disable caching: `SCAN_CONFIG['enable_caching'] = False`

## 📚 Code Structure

```
core/
├── parallel_engine.py      # Parallel scan execution
├── caching.py              # Intelligent caching system
├── scheduler.py            # Sentinel scheduler (existing)
└── engine.py               # Core engine (existing)

intelligence/
├── ai_sentinel.py          # AI-powered analysis
├── analyzer.py             # Pattern analysis (existing)
└── jarvis.py               # LLM integration (existing)

config/
└── production.py           # 16GB RAM configuration

scripts/
└── deploy_16gb.sh          # Deployment automation
```

## 🎯 Next Steps

1. Deploy to droplet: `./scripts/deploy_16gb.sh`
2. Verify services are running
3. Test Sentinel mode at `/sentinel`
4. Run a parallel scan to verify 8x speedup
5. Monitor RAM usage and adjust if needed
6. Enable AI diff analysis on watchlist URLs

## 📞 Support

If you encounter issues:
1. Check logs: `journalctl -u athena-web -f`
2. Verify model loaded: `curl http://127.0.0.1:8081/api/health`
3. Check RAM: `free -h` (should have 1-2GB free)
4. Restart services: `systemctl restart athena-web agent-orchestrator`

---

**Version:** 3.0
**Optimized for:** 16GB RAM DigitalOcean Droplet
**Deployment Date:** Dec 21, 2025
