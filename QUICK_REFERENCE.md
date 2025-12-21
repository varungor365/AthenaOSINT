# AthenaOSINT v3.0 - Quick Reference

## 🚀 Deployment Commands

### From Local Machine
```bash
# Push code
git push origin main

# Deploy to droplet
ssh root@143.110.254.40 "cd /root/AthenaOSINT && git pull && ./scripts/deploy_16gb.sh"
```

### On Droplet
```bash
cd /root/AthenaOSINT
git pull origin main
./scripts/deploy_16gb.sh
```

## 📊 Key Performance Metrics

| Metric | Before (8GB) | After (16GB) | Improvement |
|--------|--------------|--------------|-------------|
| Model | 7B params | 13B params | Better quality |
| Context | 2K tokens | 8K tokens | 4x larger |
| Workers | 1-2 | 12 | 6x more |
| Parallel Modules | 1 | 8 | 8x faster scans |
| Concurrent Scans | 1 | 6 | 6x throughput |
| Cache | None | 2GB LRU | Dedup & speed |

## 🎯 New Capabilities

### 1. Parallel Scans (8x faster)
Run multiple modules simultaneously instead of sequentially.

### 2. AI-Powered Sentinel
- LLM analyzes **what** changed and **why** it matters
- Automated threat scoring (0-100)
- Real-time anomaly detection

### 3. Intelligent Caching
- Prevents duplicate scans within 30 minutes
- Auto-merges overlapping results
- 2GB in-memory cache with TTL

### 4. High Concurrency
- 12 gevent workers = handle 12+ simultaneous users
- 6 concurrent scans = process multiple targets at once

## 🛠️ Quick Checks

### Service Status
```bash
systemctl status athena-web
systemctl status agent-orchestrator
systemctl status ollama
```

### Model Verification
```bash
curl http://127.0.0.1:8081/api/health
# Expected: {"status":"ok","model":"wizard-vicuna-uncensored:13b"}
```

### Resource Usage
```bash
free -h  # Should show ~14GB used, 2GB free
ps aux | grep gunicorn | wc -l  # Should show 13 (1 master + 12 workers)
```

### Logs
```bash
# Flask
journalctl -u athena-web -f

# Orchestrator
journalctl -u agent-orchestrator -f

# Ollama
journalctl -u ollama -f
```

## 🔧 Tuning

### If RAM is tight (<1GB free)
Edit `/root/AthenaOSINT/config/production.py`:
```python
GUNICORN_CONFIG['workers'] = 8  # Reduce from 12
MEMORY_CONFIG['cache_max_size_mb'] = 1024  # Reduce from 2048
```

### If scans are slow
```python
SCAN_CONFIG['max_parallel_modules'] = 12  # Increase from 8
LLM_CONFIG['threads'] = 12  # Increase from 8
```

### Restart after tuning
```bash
systemctl restart athena-web agent-orchestrator
```

## 📍 Dashboard URLs

- **Main Dashboard:** http://143.110.254.40/
- **Sentinel Mode:** http://143.110.254.40/sentinel
- **Automation Suite:** http://143.110.254.40/automation
- **AI Assistant:** http://143.110.254.40/ai-assistant
- **Code Workspace:** http://143.110.254.40/code-workspace

## 🧪 Test Commands

### Test Parallel Engine (locally)
```python
from core.parallel_engine import ParallelScanEngine, get_scan_queue
from core.engine import Profile

# Quick test
engine = ParallelScanEngine(max_workers=8)
profile = Profile(target_query="example.com")
result = engine.run_parallel_scan(
    "example.com",
    ['subfinder', 'theharvester'],
    profile
)
print(f"Completed in {result['elapsed']:.1f}s")
```

### Test AI Sentinel
```python
from intelligence.ai_sentinel import get_ai_analyzer

analyzer = get_ai_analyzer()
analysis = analyzer.analyze_diff(
    "Old content here",
    "New content with suspicious changes",
    "https://example.com"
)
print(f"Severity: {analysis['severity']}, Score: {analysis['threat_score']}")
```

### Test Caching
```python
from core.caching import get_cache

cache = get_cache()
cache.set('test', {'data': 'value'}, ttl=60)
print(cache.get('test'))
print(cache.get_stats())
```

## 🐛 Common Issues

### "Connection refused" on port 8081
```bash
systemctl restart agent-orchestrator
journalctl -u agent-orchestrator -n 50
```

### High memory usage
```bash
# Check what's using RAM
ps aux --sort=-%mem | head -10

# Reduce workers if needed
nano /root/AthenaOSINT/gunicorn.conf.py
# Change: workers = 8
systemctl restart athena-web
```

### Ollama OOM
```bash
# Use smaller model
ollama pull wizard-vicuna-uncensored:7b

# Update config
nano /opt/agent/orchestrator/.env
# Change: AGENT_MODEL=wizard-vicuna-uncensored:7b

systemctl restart agent-orchestrator
```

## 📈 Monitoring

### Real-time Dashboard Stats
```bash
curl http://localhost:5000/api/system/stats | jq
```

### Cache Performance
```python
from core.caching import get_cache
stats = get_cache().get_stats()
print(f"Hit rate: {stats['hit_rate']:.1f}%")
print(f"Cache size: {stats['size_mb']:.1f}MB")
```

### Scan Queue Status
```python
from core.parallel_engine import get_scan_queue
queue = get_scan_queue()
print(f"Active scans: {len(queue.active_scans)}")
```

---

**Version:** 3.0
**Date:** Dec 21, 2025
**Optimized for:** 16GB RAM
