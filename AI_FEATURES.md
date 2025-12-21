# 🤖 AI-Powered Self-Learning OSINT System

## Overview

AthenaOSINT now features **fully automated AI-driven intelligence harvesting** that learns from its operations, prevents crashes, and continuously optimizes itself using a local LLM.

---

## 🧠 AI Features

### 1. **Self-Learning Task Optimization**

The harvester learns from every task execution:

```python
# Tracks for each task type:
{
  "breach_monitoring": {
    "total": 247,
    "success": 231,  # 93.5% success rate
    "avg_time": 12.4,  # seconds
    "threats_found": 8
  }
}
```

**What it learns:**
- ✅ Success rates per task type
- ⏱️ Average execution times
- 🎯 Which tasks find the most threats
- 📊 Optimal scan intervals

**Actions taken:**
- Disables tasks with < 30% success rate
- Prioritizes high-threat tasks first
- Adjusts intervals based on findings
- Optimizes resource allocation

### 2. **Automatic Crash Prevention**

Real-time resource monitoring prevents system failures:

```python
Resource Monitoring:
├─ CPU Usage: 45.2% (limit: 60%)
├─ RAM: 1,234 MB (limit: 2,048 MB)
├─ Disk: 67% (warning at 90%)
└─ Network: Active
```

**Protection mechanisms:**
- 🛑 Auto-throttles when approaching CPU/RAM limits
- ⏸️ Pauses task generation if resources constrained
- 🔄 Workers self-heal after 3 consecutive errors
- 💾 Monitors disk space before saving results

**Stats tracked:**
- `crashes_prevented`: Times throttling prevented crash
- `auto_recoveries`: Worker self-healing events

### 3. **AI-Powered Threat Prioritization**

Tasks are scored and prioritized based on:

```python
Task Score = 
  (Historical Threat Rate × 100) +     # 0-100 points
  (Speed Bonus: <30s=20, <60s=10) +    # 0-20 points  
  (Recent Pattern Match × 5)            # 0-50 points
```

**Example:**
```
High Priority:
1. breach_check [Score: 145] - Found 12 threats, avg 8.2s
2. cloud_storage_scan [Score: 98] - Found 5 threats, avg 15s

Low Priority:
8. social_scrape [Score: 22] - Found 0 threats, avg 92s
```

### 4. **LLM-Guided System Refinement**

Every 10 cycles (~5 hours), the local AI reviews performance:

```
🤖 AI Recommendations:

1. Increase subdomain_discovery interval to 45 min (currently 30 min)
   - 95% success rate but avg time 67s, reduce frequency

2. Enable dark_web_monitoring for high-value targets
   - Recent threat patterns show 23% dark web mentions

3. Reduce max_concurrent from 4 to 3 workers  
   - CPU usage averaging 58%, close to 60% limit

4. Prioritize breach_monitoring - 8/10 recent threats from this task
   - Adjust task weights in prioritization

5. Consider disabling social_scraping
   - 0 threats found in last 100 runs, 12% failure rate
```

**Review includes:**
- Performance metrics analysis
- Resource usage optimization
- Task effectiveness scoring
- Configuration recommendations

### 5. **Error Pattern Recognition**

Tracks errors to prevent recurring issues:

```json
{
  "error_patterns": [
    {
      "task": "dark_web_monitor",
      "error": "Tor not installed",
      "count": 12,
      "last_seen": "2025-12-21T10:30:00"
    }
  ]
}
```

**Intelligent responses:**
- 🔕 Auto-disables tasks with repeated infrastructure errors
- ⏰ Implements exponential backoff for rate-limited APIs
- 🔧 Suggests fixes in AI review
- 📝 Logs patterns for human review

---

## 📚 Learning Database

Location: `data/harvester_learning.json`

```json
{
  "task_success_rates": {
    "breach_check": {
      "total": 247,
      "success": 231,
      "avg_time": 12.4,
      "threats_found": 8
    }
  },
  
  "threat_patterns": [
    {
      "task_type": "breach_check",
      "timestamp": "2025-12-21T10:15:00",
      "execution_time": 8.2
    }
  ],
  
  "optimization_history": [
    {
      "timestamp": "2025-12-21T05:00:00",
      "recommendations": "...",
      "stats_snapshot": {...}
    }
  ],
  
  "last_ai_review": "2025-12-21T10:00:00"
}
```

---

## 🔧 AI Configuration

In `data/harvester_config.json`:

```json
{
  "ai_enabled": true,              // Master AI toggle
  "ai_learning": true,             // Learn from executions
  "ai_auto_optimize": true,        // Auto-disable bad tasks
  "ai_crash_prevention": true,     // Resource throttling
  "ai_task_prioritization": true,  // Threat-based ordering
  
  "max_memory_mb": 2048,
  "max_cpu_percent": 60,
  "interval_minutes": 30
}
```

**Toggle any feature:**
- `ai_enabled: false` → Runs in dumb mode (no AI)
- `ai_learning: false` → Doesn't track performance
- `ai_auto_optimize: false` → Manual task management
- `ai_crash_prevention: false` → No resource limits
- `ai_task_prioritization: false` → Random task order

---

## 📊 AI Statistics

View via dashboard or API:

```bash
curl http://localhost:5000/api/harvester/status | jq
```

```json
{
  "stats": {
    "tasks_completed": 1247,
    "tasks_failed": 23,          // 98.2% success rate
    "threats_found": 45,
    "crashes_prevented": 7,       // 🛡️ AI saved system
    "auto_recoveries": 3,         // 🔧 Self-healed
    "ai_optimizations": 12,       // 🤖 Auto-adjustments
    "uptime_hours": 72.5
  }
}
```

---

## 🎯 How It Works

### Startup
```
1. Load config (data/harvester_config.json)
2. Load learning database (data/harvester_learning.json)
3. Start 4 worker threads
4. Start task generator (with AI prioritization)
5. Start stats tracker (resource monitoring)
```

### Task Execution Cycle
```
1. Task Generator:
   ├─ Check resources (CPU/RAM/Disk)
   ├─ Generate 30 tasks from watchlists
   ├─ AI prioritizes based on threat history
   └─ Add to queue

2. Worker (×4):
   ├─ Check if should throttle (resources high?)
   ├─ Get task from queue
   ├─ Execute with timing
   ├─ AI learns from result
   └─ Auto-recover on 3+ errors

3. Every 10 cycles (~5 hours):
   ├─ LLM reviews performance
   ├─ Generate optimization recommendations
   ├─ Auto-adjust config
   └─ Save learning database
```

### Self-Healing Example
```
Worker-1: Task failed (1/3)
Worker-1: Task failed (2/3)  
Worker-1: Task failed (3/3)
Worker-1: 🤖 Self-healing - pausing 60s
[60 seconds later]
Worker-1: Resumed, errors reset
```

### Resource Protection Example
```
CPU: 62% (limit: 60%)
🤖 AI Throttling: CPU usage high
Worker-2: Pausing for 30s
Worker-3: Pausing for 30s
[Resources stabilize]
Workers: Resumed
Crashes Prevented: +1
```

---

## 🚀 Benefits

### 1. **Zero Maintenance**
- System optimizes itself
- No manual tuning required
- Self-heals from errors
- Adapts to environment

### 2. **Maximum Uptime**
- Crash prevention mechanisms
- Resource-aware scheduling
- Auto-recovery from failures
- Predictive error avoidance

### 3. **Optimal Performance**
- AI learns what works best
- Prioritizes high-value tasks
- Disables ineffective modules
- Adjusts timing automatically

### 4. **Threat-Focused**
- More time on tasks that find threats
- Less time on empty searches
- Dynamic prioritization
- Pattern recognition

### 5. **Cost Efficiency**
- Uses local LLM (free)
- Optimizes resource usage
- Prevents wasted cycles
- Intelligent throttling

---

## 📖 Real-World Examples

### Example 1: Learning from Failures

**Initial state:**
```
dark_web_monitoring: enabled
Executions: 50
Failures: 49 (Tor not installed)
Success rate: 2%
```

**After 50 runs:**
```
🤖 AI Optimization: Disabling dark_web_monitoring (success rate: 2%)
Config updated: tasks.dark_web_monitoring = false
AI Optimizations: +1
```

### Example 2: Frequency Adjustment

**Initial:**
```
Interval: 30 minutes
Threats found: 45 in 24 hours
```

**After AI review:**
```
🤖 AI Optimization: Increased scan frequency (30→20 min)
Reason: High threat rate detected
```

**Result:**
```
Interval: 20 minutes  
Threats found: 67 in 24 hours (+49%)
```

### Example 3: Task Prioritization

**Before AI (random order):**
```
Queue: [social_scrape, ssl_check, breach_check, ...]
Threats/hour: 1.2
```

**After AI (threat-scored):**
```
Queue: [breach_check, cloud_scan, leak_scan, ...]
Threats/hour: 2.8 (+133%)
```

---

## 🔍 Monitoring AI Decisions

### Check Learning Database
```bash
cat data/harvester_learning.json | jq '.task_success_rates'
```

### View AI Recommendations
```bash
cat data/harvester_learning.json | jq '.optimization_history[-1]'
```

### Watch Resource Stats
```bash
curl http://localhost:5000/api/harvester/status | jq '.stats'
```

### Monitor Logs
```bash
journalctl -u athena-harvester -f | grep "🤖"
```

Output:
```
🤖 AI Worker harvester-worker-0 started
🤖 Generated 28 AI-prioritized tasks (cycle #1)
🤖 AI Throttling: CPU usage high: 62%
🤖 Worker harvester-worker-1 self-healing: too many errors, pausing 60s
🤖 Running AI system review...
🤖 AI Recommendations: [details]
🤖 AI Optimization: Disabling social_scraping (success rate: 12%)
```

---

## 🎓 Teaching the LLM

The system "teaches" the LLM about OSINT operations through:

1. **Performance Summaries**
   - Task success/failure rates
   - Resource usage patterns
   - Threat detection efficacy
   - Error frequency analysis

2. **Context-Rich Prompts**
   ```
   "You are an AI analyzing an OSINT system. This domain scanner
   has 45% success rate but uses 120s avg. Should we:
   A) Increase timeout
   B) Reduce frequency  
   C) Disable entirely
   D) Optimize query"
   ```

3. **Feedback Loops**
   - LLM suggests optimization
   - System implements change
   - Measures impact
   - Reports back to LLM
   - LLM refines suggestions

4. **Pattern Recognition**
   - "Tasks with <30% success usually have infrastructure issues"
   - "High CPU tasks should run at lower frequency"
   - "Threat patterns cluster around breach_monitoring"

Over time, the LLM becomes an expert OSINT systems engineer!

---

## 🛠️ Troubleshooting

### AI not making recommendations
```bash
# Check if AI is enabled
grep ai_enabled data/harvester_config.json

# Check last review time  
jq '.last_ai_review' data/harvester_learning.json

# Manually trigger review (every 10 cycles)
# Wait for log: "🤖 Running AI system review..."
```

### Too aggressive optimization
```json
// In config:
{
  "ai_auto_optimize": false  // Manual approval only
}
```

### Resource limits too strict
```json
{
  "max_cpu_percent": 80,     // Increase from 60
  "max_memory_mb": 4096      // Increase from 2048
}
```

---

**The harvester now thinks for itself. Set it and forget it! 🤖✨**
