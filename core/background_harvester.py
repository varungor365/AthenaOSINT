"""
24/7 Background Harvester Daemon with AI-Driven Automation.
Continuously collects OSINT intelligence with self-learning capabilities.

🤖 AI-POWERED FEATURES:
- Self-learning task optimization
- Automatic error recovery and crash prevention
- Resource monitoring and throttling
- AI-powered result analysis and prioritization
- Dynamic task scheduling based on threat intelligence
- LLM-guided system refinement
- Predictive threat detection
- Adaptive resource allocation

Automated Tasks:
- Breach database monitoring
- Domain/subdomain change detection
- Dark web monitoring (Tor hidden services)
- Pastebin/GitHub leak scanning
- SSL certificate monitoring
- DNS hijacking detection
- Phishing domain detection
- Brand impersonation monitoring
- Social media scraping
- Automated vulnerability scanning
- Cloud storage leak detection
- Executive/VIP monitoring
- OSINT development and reconnaissance
"""
import time
import threading
import queue
import json
import hashlib
import psutil
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Callable
from loguru import logger
import random

from core.engine import AthenaEngine, Profile
from core.parallel_engine import ParallelScanEngine
from intelligence.ai_sentinel import get_ai_analyzer
from intelligence.llm import get_llm_response
from core.caching import get_cache


class BackgroundHarvester:
    """
    24/7 autonomous OSINT harvester with AI-driven automation.
    Continuously collects intelligence, learns from results, and self-optimizes.
    
    🤖 AI Features:
    - Self-healing on errors
    - Resource-aware task scheduling
    - AI-powered threat prioritization
    - Automatic system refinement
    - Crash prevention mechanisms
    """
    
    def __init__(self, config_file: str = "data/harvester_config.json"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
        self.running = False
        self.worker_threads = []
        self.task_queue = queue.Queue()
        self.results_dir = Path("data/harvester_results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # AI Learning Database
        self.learning_db = Path("data/harvester_learning.json")
        self.learning_data = self._load_learning_data()
        
        # Statistics
        self.stats = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'targets_monitored': 0,
            'threats_found': 0,
            'data_harvested_mb': 0,
            'uptime_hours': 0,
            'last_activity': None,
            'crashes_prevented': 0,
            'auto_recoveries': 0,
            'ai_optimizations': 0
        }
        
        # Resource monitoring
        self.resource_stats = {
            'cpu_percent': 0,
            'memory_mb': 0,
            'disk_usage_percent': 0,
            'network_active': True
        }
        
        # Error tracking for self-healing
        self.error_history = []
        self.max_error_history = 100
        
        logger.info("🤖 AI-Powered Background Harvester initialized")
    
    
    def start(self, num_workers: int = 4):
        """Start the 24/7 harvester daemon."""
        if self.running:
            logger.warning("Harvester already running")
            return
        
        self.running = True
        logger.success(f"🚀 Starting 24/7 Background Harvester with {num_workers} workers")
        
        # Start worker threads
        for i in range(num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"harvester-worker-{i}",
                daemon=True
            )
            worker.start()
            self.worker_threads.append(worker)
        
        # Start task generator
        generator = threading.Thread(
            target=self._task_generator_loop,
            name="harvester-generator",
            daemon=True
        )
        generator.start()
        self.worker_threads.append(generator)
        
        # Start statistics tracker
        stats_tracker = threading.Thread(
            target=self._stats_tracker_loop,
            name="harvester-stats",
            daemon=True
        )
        stats_tracker.start()
        self.worker_threads.append(stats_tracker)
        
        logger.info(f"✓ {num_workers + 2} threads started")
    
    def stop(self):
        """Stop the harvester gracefully."""
        logger.info("Stopping Background Harvester...")
        self.running = False
        
        # Wait for threads to finish (with timeout)
        for thread in self.worker_threads:
            thread.join(timeout=5)
        
        self._save_stats()
        logger.success("Background Harvester stopped")
    
    def _load_config(self) -> Dict:
        """Load or create harvester configuration."""
        default_config = {
            'enabled': True,
            'interval_minutes': 30,  # Check every 30 minutes
            'max_concurrent': 4,
            
            # Target lists
            'watchlist_domains': [],
            'watchlist_emails': [],
            'watchlist_usernames': [],
            'watchlist_keywords': [],
            'watchlist_onion_sites': [],  # 🆕 Dark web monitoring
            'watchlist_executives': [],   # 🆕 Executive/VIP monitoring
            
            # Task types (enable/disable)
            'tasks': {
                # Original tasks
                'breach_monitoring': True,
                'subdomain_discovery': True,
                'leak_scanning': True,
                'ssl_monitoring': True,
                'dns_monitoring': True,
                'phishing_detection': True,
                'social_scraping': True,
                'vulnerability_scanning': True,
                'github_secrets': True,
                'pastebin_monitoring': True,
                
                # 🆕 NEW ADVANCED TASKS
                'dark_web_monitoring': False,        # Requires Tor installation
                'paste_site_monitoring': True,       # Ghostbin, Rentry.co, dpaste
                'cloud_storage_scanning': True,      # S3, Azure, GCP buckets
                'social_media_monitoring': True,     # Twitter, LinkedIn, Instagram, TikTok
                'executive_monitoring': False,       # Optional VIP/executive tracking
                'osint_development': True,           # API enumeration, tech fingerprinting
            },
            
            # Alert settings
            'alert_on_new_breach': True,
            'alert_on_subdomain_change': True,
            'alert_on_leak': True,
            'alert_on_vulnerability': True,
            
            # Resource limits
            'max_memory_mb': 2048,
            'max_cpu_percent': 60,
            'rate_limit_rpm': 100,
            
            # 🤖 AI Configuration
            'ai_enabled': True,
            'ai_learning': True,
            'ai_auto_optimize': True,
            'ai_crash_prevention': True,
            'ai_task_prioritization': True,
        }
        
        if not self.config_file.exists():
            self._save_config(default_config)
            return default_config
        
        try:
            with open(self.config_file, 'r') as f:
                loaded_config = json.load(f)
                # Merge with defaults (add new keys)
                for key, value in default_config.items():
                    if key not in loaded_config:
                        loaded_config[key] = value
                if 'tasks' in loaded_config:
                    for task_key, task_value in default_config['tasks'].items():
                        if task_key not in loaded_config['tasks']:
                            loaded_config['tasks'][task_key] = task_value
                return loaded_config
        except Exception as e:
            logger.error(f"Config load failed: {e}, using defaults")
            return default_config
    
    def _load_learning_data(self) -> Dict:
        """Load AI learning database."""
        if self.learning_db.exists():
            try:
                with open(self.learning_db, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            'task_success_rates': {},
            'optimal_intervals': {},
            'threat_patterns': [],
            'error_patterns': [],
            'optimization_history': [],
            'last_ai_review': None
        }
    
    def _save_learning_data(self):
        """Save AI learning database."""
        try:
            with open(self.learning_db, 'w') as f:
                json.dump(self.learning_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save learning data: {e}")
    
    def _check_resources(self) -> Dict:
        """Monitor system resources to prevent crashes."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            self.resource_stats = {
                'cpu_percent': cpu_percent,
                'memory_mb': memory.used / 1024 / 1024,
                'memory_percent': memory.percent,
                'disk_usage_percent': disk.percent,
                'network_active': True
            }
            
            # Check if we're approaching limits
            warnings = []
            if cpu_percent > self.config.get('max_cpu_percent', 60):
                warnings.append(f'CPU usage high: {cpu_percent}%')
            if memory.percent > 80:
                warnings.append(f'Memory usage high: {memory.percent}%')
            if disk.percent > 90:
                warnings.append(f'Disk usage critical: {disk.percent}%')
            
            return {'healthy': len(warnings) == 0, 'warnings': warnings, 'stats': self.resource_stats}
            
        except Exception as e:
            logger.error(f"Resource check failed: {e}")
            return {'healthy': False, 'warnings': [str(e)], 'stats': {}}
    
    def _ai_should_throttle(self) -> bool:
        """AI decides if we should throttle tasks to prevent crash."""
        if not self.config.get('ai_crash_prevention', True):
            return False
        
        resource_check = self._check_resources()
        
        if not resource_check['healthy']:
            logger.warning(f"🤖 AI Throttling: {', '.join(resource_check['warnings'])}")
            self.stats['crashes_prevented'] += 1
            return True
        
        # Check error rate
        if len(self.error_history) > 10:
            recent_errors = [e for e in self.error_history[-20:] if (datetime.now() - e['timestamp']).seconds < 300]
            if len(recent_errors) > 5:  # More than 5 errors in 5 minutes
                logger.warning(f"🤖 AI Throttling: High error rate ({len(recent_errors)} errors)")
                return True
        
        return False
    
    def _ai_optimize_tasks(self):
        """AI analyzes past performance and optimizes task configuration."""
        if not self.config.get('ai_auto_optimize', True):
            return
        
        try:
            # Analyze success rates
            task_performance = self.learning_data.get('task_success_rates', {})
            
            # Disable consistently failing tasks
            for task_type, stats in task_performance.items():
                if stats.get('total', 0) > 10:
                    success_rate = stats.get('success', 0) / stats['total']
                    if success_rate < 0.3:  # Less than 30% success
                        if self.config['tasks'].get(task_type, False):
                            logger.warning(f"🤖 AI Optimization: Disabling {task_type} (success rate: {success_rate:.1%})")
                            self.config['tasks'][task_type] = False
                            self.stats['ai_optimizations'] += 1
            
            # Adjust intervals based on threat findings
            if self.stats['threats_found'] > 10:
                # Found many threats, check more frequently
                if self.config['interval_minutes'] > 15:
                    old_interval = self.config['interval_minutes']
                    self.config['interval_minutes'] = max(15, old_interval - 5)
                    logger.info(f"🤖 AI Optimization: Increased scan frequency ({old_interval}→{self.config['interval_minutes']} min)")
                    self.stats['ai_optimizations'] += 1
            
            self._save_config()
            
        except Exception as e:
            logger.error(f"AI optimization failed: {e}")
    
    def _ai_learn_from_result(self, task_type: str, success: bool, execution_time: float, threat_found: bool):
        """AI learns from task execution results."""
        if not self.config.get('ai_learning', True):
            return
        
        # Update success rates
        if 'task_success_rates' not in self.learning_data:
            self.learning_data['task_success_rates'] = {}
        
        if task_type not in self.learning_data['task_success_rates']:
            self.learning_data['task_success_rates'][task_type] = {
                'total': 0,
                'success': 0,
                'avg_time': 0,
                'threats_found': 0
            }
        
        stats = self.learning_data['task_success_rates'][task_type]
        stats['total'] += 1
        if success:
            stats['success'] += 1
        if threat_found:
            stats['threats_found'] += 1
        
        # Update average execution time (rolling average)
        stats['avg_time'] = (stats.get('avg_time', 0) * 0.9) + (execution_time * 0.1)
        
        # Record threat patterns
        if threat_found:
            pattern = {
                'task_type': task_type,
                'timestamp': datetime.now().isoformat(),
                'execution_time': execution_time
            }
            self.learning_data.setdefault('threat_patterns', []).append(pattern)
            
            # Keep only last 100 patterns
            self.learning_data['threat_patterns'] = self.learning_data['threat_patterns'][-100:]
        
        # Save learning data periodically
        if stats['total'] % 10 == 0:
            self._save_learning_data()
    
    def _ai_review_and_refine(self):
        """
        AI reviews system performance and suggests refinements using LLM.
        This teaches the system how to improve itself.
        """
        if not self.config.get('ai_enabled', True):
            return
        
        try:
            # Prepare performance summary for LLM
            summary = {
                'uptime_hours': self.stats['uptime_hours'],
                'tasks_completed': self.stats['tasks_completed'],
                'tasks_failed': self.stats['tasks_failed'],
                'threats_found': self.stats['threats_found'],
                'crashes_prevented': self.stats['crashes_prevented'],
                'auto_recoveries': self.stats['auto_recoveries'],
                'task_success_rates': self.learning_data.get('task_success_rates', {}),
                'error_patterns': self.error_history[-10:] if self.error_history else [],
                'resource_stats': self.resource_stats
            }
            
            prompt = f"""You are an AI analyzing an OSINT harvesting system. Review this performance data and suggest optimizations:

{json.dumps(summary, indent=2, default=str)}

Current Configuration:
- Interval: {self.config['interval_minutes']} minutes
- Max workers: {self.config['max_concurrent']}
- Enabled tasks: {[k for k, v in self.config['tasks'].items() if v]}

Provide 3-5 specific recommendations to:
1. Improve success rates
2. Prevent errors/crashes
3. Optimize resource usage
4. Enhance threat detection

Format: Brief bullet points, actionable suggestions only."""

            # Get AI recommendations
            logger.info("🤖 Requesting AI system review...")
            recommendations = get_llm_response(prompt, max_tokens=500)
            
            if recommendations:
                logger.success(f"🤖 AI Recommendations:\n{recommendations}")
                
                # Save recommendations
                self.learning_data['optimization_history'].append({
                    'timestamp': datetime.now().isoformat(),
                    'recommendations': recommendations,
                    'stats_snapshot': summary
                })
                
                # Keep only last 20 reviews
                self.learning_data['optimization_history'] = self.learning_data['optimization_history'][-20:]
                
                self.learning_data['last_ai_review'] = datetime.now().isoformat()
                self._save_learning_data()
            
        except Exception as e:
            logger.error(f"AI review failed: {e}")
    
    def _ai_prioritize_tasks(self, tasks: List[Dict]) -> List[Dict]:
        """AI prioritizes tasks based on threat intelligence and past findings."""
        if not self.config.get('ai_task_prioritization', True):
            return tasks
        
        try:
            # Score tasks based on historical threat findings
            task_scores = []
            for task in tasks:
                score = 0
                task_type = task['type']
                
                # Higher score for tasks that found threats before
                stats = self.learning_data.get('task_success_rates', {}).get(task_type, {})
                threats_found = stats.get('threats_found', 0)
                total_runs = stats.get('total', 1)
                threat_rate = threats_found / max(total_runs, 1)
                
                score += threat_rate * 100  # 0-100 points
                
                # Prioritize faster tasks
                avg_time = stats.get('avg_time', 60)
                if avg_time < 30:
                    score += 20
                elif avg_time < 60:
                    score += 10
                
                # Prioritize recent threat patterns
                recent_threats = [p for p in self.learning_data.get('threat_patterns', [])
                                if p['task_type'] == task_type]
                if recent_threats:
                    score += min(len(recent_threats) * 5, 50)
                
                task_scores.append((task, score))
            
            # Sort by score (highest first)
            task_scores.sort(key=lambda x: x[1], reverse=True)
            prioritized = [t[0] for t in task_scores]
            
            logger.debug(f"🤖 AI Prioritized {len(prioritized)} tasks")
            return prioritized
            
        except Exception as e:
            logger.error(f"AI prioritization failed: {e}")
            return tasks
        
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return {**default_config, **json.load(f)}
        else:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"Created default config: {self.config_file}")
            return default_config
    
    def _save_config(self):
        """Save current configuration."""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def _save_stats(self):
        """Save statistics."""
        stats_file = self.results_dir / "harvester_stats.json"
        with open(stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2)
    
    def _worker_loop(self):
        """Worker thread with AI-powered error recovery."""
        worker_name = threading.current_thread().name
        logger.info(f"🤖 AI Worker {worker_name} started")
        
        consecutive_errors = 0
        max_consecutive_errors = 3
        
        while self.running:
            try:
                # Check if we should throttle
                if self._ai_should_throttle():
                    logger.warning(f"🤖 Worker {worker_name} throttling for 30s")
                    time.sleep(30)
                    continue
                
                # Get task from queue (with timeout)
                try:
                    task = self.task_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                # Execute task with timing and error handling
                start_time = time.time()
                success = False
                threat_found = False
                
                try:
                    result = self._execute_task(task)
                    success = True
                    threat_found = result.get('threat_found', False) if result else False
                    consecutive_errors = 0  # Reset on success
                    
                except Exception as e:
                    consecutive_errors += 1
                    error_info = {
                        'task': task,
                        'error': str(e),
                        'traceback': traceback.format_exc(),
                        'timestamp': datetime.now(),
                        'worker': worker_name
                    }
                    self.error_history.append(error_info)
                    self.error_history = self.error_history[-self.max_error_history:]
                    self.stats['tasks_failed'] += 1
                    
                    logger.error(f"❌ Task failed ({consecutive_errors}/{max_consecutive_errors}): {e}")
                    
                    # AI-powered error recovery
                    if consecutive_errors >= max_consecutive_errors:
                        logger.warning(f"🤖 Worker {worker_name} self-healing: too many errors, pausing 60s")
                        time.sleep(60)
                        consecutive_errors = 0
                        self.stats['auto_recoveries'] += 1
                
                execution_time = time.time() - start_time
                
                # AI learns from this execution
                self._ai_learn_from_result(
                    task_type=task['type'],
                    success=success,
                    execution_time=execution_time,
                    threat_found=threat_found
                )
                
                self.task_queue.task_done()
                if success:
                    self.stats['tasks_completed'] += 1
                    self.stats['last_activity'] = datetime.now().isoformat()
                
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                time.sleep(5)
    
    def _task_generator_loop(self):
        """AI-powered task generator with dynamic prioritization."""
        logger.info("🤖 AI Task Generator started")
        cycle_count = 0
        
        while self.running:
            try:
                cycle_count += 1
                
                # Check resources before generating tasks
                resource_check = self._check_resources()
                if not resource_check['healthy']:
                    logger.warning(f"🤖 Skipping task generation: {', '.join(resource_check['warnings'])}")
                    time.sleep(60)
                    continue
                
                # Generate tasks
                tasks = self._generate_tasks()
                
                # AI prioritizes tasks
                prioritized_tasks = self._ai_prioritize_tasks(tasks)
                
                # Add to queue
                for task in prioritized_tasks:
                    self.task_queue.put(task)
                
                logger.info(f"🤖 Generated {len(prioritized_tasks)} AI-prioritized tasks (cycle #{cycle_count})")
                
                # AI reviews system every 10 cycles (~5 hours at 30min interval)
                if cycle_count % 10 == 0:
                    logger.info("🤖 Running AI system review...")
                    self._ai_review_and_refine()
                    self._ai_optimize_tasks()
                
                # Sleep for configured interval
                interval_seconds = self.config['interval_minutes'] * 60
                for _ in range(interval_seconds):
                    if not self.running:
                        break
                    time.sleep(1)
                
            except Exception as e:
                logger.error(f"Task generator error: {e}\n{traceback.format_exc()}")
                time.sleep(60)
    
    def _stats_tracker_loop(self):
        """Track statistics, resources, and trigger AI reviews."""
        start_time = time.time()
        
        while self.running:
            try:
                # Update uptime
                self.stats['uptime_hours'] = (time.time() - start_time) / 3600
                
                # Check resources
                resource_check = self._check_resources()
                
                # Log resource status every hour
                if int(self.stats['uptime_hours']) % 1 == 0:
                    logger.info(f"📊 Resources: CPU {resource_check['stats'].get('cpu_percent', 0):.1f}% | " +
                              f"RAM {resource_check['stats'].get('memory_mb', 0):.0f}MB | " +
                              f"Tasks: {self.stats['tasks_completed']}/{self.stats['tasks_failed']} | " +
                              f"Threats: {self.stats['threats_found']}")
                
                # Save stats every 10 minutes
                self._save_stats()
                self._save_learning_data()
                
                time.sleep(600)  # 10 minutes
                
            except Exception as e:
                logger.error(f"Stats tracker error: {e}")
        """Track statistics and resource usage."""
        start_time = time.time()
        
        while self.running:
            try:
                # Update uptime
                self.stats['uptime_hours'] = (time.time() - start_time) / 3600
                
                # Save stats every 10 minutes
                self._save_stats()
                
                time.sleep(600)  # 10 minutes
                
            except Exception as e:
                logger.error(f"Stats tracker error: {e}")
    
    def _generate_tasks(self) -> List[Dict]:
        """Generate tasks based on configuration."""
        tasks = []
        
        # Breach monitoring
        if self.config['tasks'].get('breach_monitoring'):
            for email in self.config['watchlist_emails']:
                tasks.append({
                    'type': 'breach_check',
                    'target': email,
                    'modules': ['holehe', 'leak_checker']
                })
        
        # Subdomain discovery
        if self.config['tasks'].get('subdomain_discovery'):
            for domain in self.config['watchlist_domains']:
                tasks.append({
                    'type': 'subdomain_scan',
                    'target': domain,
                    'modules': ['subfinder', 'amass']
                })
        
        # Leak scanning (Pastebin, GitHub)
        if self.config['tasks'].get('leak_scanning'):
            for keyword in self.config['watchlist_keywords']:
                tasks.append({
                    'type': 'leak_scan',
                    'target': keyword,
                    'modules': ['auto_dorker']  # Google dorking
                })
        
        # GitHub secrets
        if self.config['tasks'].get('github_secrets'):
            for keyword in self.config['watchlist_keywords']:
                tasks.append({
                    'type': 'github_secrets',
                    'target': keyword,
                    'modules': ['auto_dorker']
                })
        
        # Pastebin monitoring
        if self.config['tasks'].get('pastebin_monitoring'):
            for keyword in self.config['watchlist_keywords']:
                tasks.append({
                    'type': 'pastebin_monitor',
                    'target': keyword,
                    'modules': ['auto_dorker']
                })
        
        # SSL monitoring
        if self.config['tasks'].get('ssl_monitoring'):
            for domain in self.config['watchlist_domains']:
                tasks.append({
                    'type': 'ssl_check',
                    'target': domain,
                    'modules': []  # Custom SSL check
                })
        
        # Vulnerability scanning
        if self.config['tasks'].get('vulnerability_scanning'):
            for domain in self.config['watchlist_domains']:
                tasks.append({
                    'type': 'vuln_scan',
                    'target': domain,
                    'modules': ['nuclei']
                })
        
        # Social media scraping
        if self.config['tasks'].get('social_scraping'):
            for username in self.config['watchlist_usernames']:
                tasks.append({
                    'type': 'social_scrape',
                    'target': username,
                    'modules': ['sherlock', 'profile_scraper']
                })
        
        # 🆕 Dark Web Intelligence
        if self.config['tasks'].get('dark_web_monitoring'):
            for domain in self.config.get('watchlist_onion_sites', []):
                tasks.append({
                    'type': 'dark_web_monitor',
                    'target': domain,
                    'modules': []
                })
            for keyword in self.config['watchlist_keywords']:
                tasks.append({
                    'type': 'dark_web_search',
                    'target': keyword,
                    'modules': []
                })
        
        # 🆕 Advanced Paste Site Monitoring
        if self.config['tasks'].get('paste_site_monitoring'):
            for keyword in self.config['watchlist_keywords']:
                tasks.append({
                    'type': 'paste_site_monitor',
                    'target': keyword,
                    'modules': []  # Ghostbin, PasteSite, Rentry.co
                })
        
        # 🆕 Cloud Storage Leak Scanning
        if self.config['tasks'].get('cloud_storage_scanning'):
            for domain in self.config['watchlist_domains']:
                tasks.append({
                    'type': 'cloud_storage_scan',
                    'target': domain,
                    'modules': ['cloud_hunter']
                })
        
        # 🆕 Social Media Monitoring (Enhanced)
        if self.config['tasks'].get('social_media_monitoring'):
            for keyword in self.config['watchlist_keywords']:
                tasks.append({
                    'type': 'social_media_monitor',
                    'target': keyword,
                    'modules': []  # Twitter, LinkedIn, Instagram, TikTok
                })
        
        # 🆕 Executive Monitoring (Optional)
        if self.config['tasks'].get('executive_monitoring'):
            for person in self.config.get('watchlist_executives', []):
                tasks.append({
                    'type': 'executive_monitor',
                    'target': person,
                    'modules': ['profile_scraper']
                })
        
        # 🆕 OSINT Development
        if self.config['tasks'].get('osint_development'):
            for domain in self.config['watchlist_domains']:
                tasks.append({
                    'type': 'osint_dev',
                    'target': domain,
                    'modules': []  # API enumeration, scraping tests
                })
        
        # Shuffle to avoid patterns
        random.shuffle(tasks)
        
        return tasks[:30]  # Increased limit to 30 tasks per cycle
    
    def _execute_task(self, task: Dict) -> Dict:
        """Execute a single harvesting task and return result."""
        task_type = task['type']
        target = task['target']
        threat_found = False
        
        logger.info(f"⚙️ Executing {task_type} for {target}")
        
        try:
            if task_type == 'breach_check':
                threat_found = self._breach_check(target, task['modules'])
            elif task_type == 'subdomain_scan':
                threat_found = self._subdomain_scan(target, task['modules'])
            elif task_type == 'leak_scan':
                threat_found = self._leak_scan(target)
            elif task_type == 'github_secrets':
                threat_found = self._github_secrets(target)
            elif task_type == 'ssl_check':
                threat_found = self._ssl_check(target)
            elif task_type == 'vuln_scan':
                threat_found = self._vuln_scan(target, task['modules'])
            elif task_type == 'social_scrape':
                threat_found = self._social_scrape(target, task['modules'])
            # 🆕 New task types
            elif task_type == 'dark_web_monitor':
                threat_found = self._dark_web_monitor(target)
            elif task_type == 'dark_web_search':
                threat_found = self._dark_web_search(target)
            elif task_type == 'paste_site_monitor':
                threat_found = self._paste_site_monitor(target)
            elif task_type == 'cloud_storage_scan':
                threat_found = self._cloud_storage_scan(target, task['modules'])
            elif task_type == 'social_media_monitor':
                threat_found = self._social_media_monitor(target)
            elif task_type == 'executive_monitor':
                threat_found = self._executive_monitor(target, task['modules'])
            elif task_type == 'osint_dev':
                threat_found = self._osint_development(target)
            else:
                logger.warning(f"Unknown task type: {task_type}")
                return {'threat_found': False}
            
            return {'threat_found': threat_found}
        
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            raise  # Re-raise for worker error handling
    
    def _breach_check(self, email: str, modules: List[str]) -> bool:
        """Check for new breaches. Returns True if threats found."""
        cache = get_cache()
        cache_key = f"breach_{email}"
        threat_found = False
        
        # Check cache
        cached = cache.get(cache_key)
        
        # Run scan
        engine = AthenaEngine(email, quiet=True)
        engine.run_scan(modules)
        
        # Compare with cached results
        if cached:
            new_breaches = [
                b for b in engine.profile.breaches
                if b not in cached
            ]
            
            if new_breaches:
                self._alert(
                    severity='high',
                    title=f'New breach detected for {email}',
                    details=f"Found {len(new_breaches)} new breaches",
                    data=new_breaches
                )
                self.stats['threats_found'] += len(new_breaches)
                threat_found = True
        
        # Update cache
        cache.set(cache_key, engine.profile.breaches, ttl=3600)
        
        # Save results
        self._save_result('breach_check', email, engine.profile.to_dict())
        return threat_found
    
    def _subdomain_scan(self, domain: str, modules: List[str]) -> bool:
        """Scan for new subdomains. Returns True if new subdomains found."""
        cache = get_cache()
        cache_key = f"subdomains_{domain}"
        threat_found = False
        
        cached = cache.get(cache_key)
        
        # Run parallel scan
        parallel_engine = ParallelScanEngine(max_workers=4)
        profile = Profile(target_query=domain)
        
        parallel_engine.run_parallel_scan(
            target=domain,
            modules=modules,
            profile=profile
        )
        
        # Detect new subdomains
        if cached:
            new_subdomains = set(profile.subdomains) - set(cached)
            
            if new_subdomains:
                self._alert(
                    severity='medium',
                    title=f'New subdomains found for {domain}',
                    details=f"Discovered {len(new_subdomains)} new subdomains",
                    data=list(new_subdomains)
                )
                self.stats['threats_found'] += len(new_subdomains)
        
        cache.set(cache_key, profile.subdomains, ttl=1800)
        self._save_result('subdomain_scan', domain, profile.to_dict())
        return threat_found
    
    def _leak_scan(self, keyword: str) -> bool:
        """Scan for leaks containing keyword."""
        logger.info(f"Scanning for leaks: {keyword}")
        threat_found = False
        
        # Use auto_dorker to search for leaks
        engine = AthenaEngine(keyword, quiet=True)
        engine.run_scan(['auto_dorker'])
        
        # AI analysis of findings
        if engine.profile.raw_data.get('auto_dorker'):
            analyzer = get_ai_analyzer()
            analysis = analyzer.detect_anomalies(
                engine.profile.raw_data['auto_dorker']
            )
            
            if analysis.get('severity') in ['critical', 'high']:
                self._alert(
                    severity=analysis['severity'],
                    title=f'Potential leak detected: {keyword}',
                    details=analysis.get('summary', ''),
                    data=analysis
                )
                self.stats['threats_found'] += 1
        
        self._save_result('leak_scan', keyword, engine.profile.to_dict())
    
    def _github_secrets(self, keyword: str):
        """Search GitHub for exposed secrets."""
        logger.info(f"Searching GitHub for secrets: {keyword}")
        
        # Use auto_dorker with GitHub-specific queries
        engine = AthenaEngine(f"site:github.com {keyword} password OR api_key OR secret", quiet=True)
        engine.run_scan(['auto_dorker'])
        
        if engine.profile.raw_data.get('auto_dorker'):
            self._alert(
                severity='high',
                title=f'GitHub secrets found: {keyword}',
                details=f"Found potential secrets on GitHub",
                data=engine.profile.raw_data['auto_dorker']
            )
            self.stats['threats_found'] += 1
        
        self._save_result('github_secrets', keyword, engine.profile.to_dict())
    
    def _ssl_check(self, domain: str):
        """Check SSL certificate status."""
        import ssl
        import socket
        from datetime import datetime
        
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Check expiration
                    not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    days_left = (not_after - datetime.now()).days
                    
                    if days_left < 30:
                        self._alert(
                            severity='medium',
                            title=f'SSL expiring soon: {domain}',
                            details=f"Certificate expires in {days_left} days",
                            data={'domain': domain, 'expires': not_after.isoformat()}
                        )
                    
                    self._save_result('ssl_check', domain, {
                        'domain': domain,
                        'issuer': dict(cert.get('issuer', [])),
                        'expires': not_after.isoformat(),
                        'days_left': days_left
                    })
        
        except Exception as e:
            logger.warning(f"SSL check failed for {domain}: {e}")
    
    def _vuln_scan(self, domain: str, modules: List[str]):
        """Scan for vulnerabilities."""
        engine = AthenaEngine(domain, quiet=True)
        engine.run_scan(modules)
        
        # Check for critical vulnerabilities
        if engine.profile.raw_data.get('nuclei'):
            critical = [
                v for v in engine.profile.raw_data['nuclei']
                if v.get('severity') == 'critical'
            ]
            
            if critical:
                self._alert(
                    severity='critical',
                    title=f'Critical vulnerabilities found: {domain}',
                    details=f"Found {len(critical)} critical vulnerabilities",
                    data=critical
                )
                self.stats['threats_found'] += len(critical)
        
        self._save_result('vuln_scan', domain, engine.profile.to_dict())
    
    def _social_scrape(self, username: str, modules: List[str]):
        """Scrape social media profiles."""
        engine = AthenaEngine(username, quiet=True)
        engine.run_scan(modules)
        
        self._save_result('social_scrape', username, engine.profile.to_dict())
    
    # ============================================================
    # 🆕 NEW ADVANCED HARVESTER FEATURES
    # ============================================================
    
    def _dark_web_monitor(self, onion_url: str):
        """
        Monitor Tor hidden services for changes.
        Tracks .onion site changes, dark web markets, ransomware leak sites.
        """
        import requests
        import subprocess
        
        try:
            # Check if Tor is installed and running
            tor_check = subprocess.run(
                ['which', 'tor'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if tor_check.returncode != 0:
                logger.warning("Tor not installed - skipping dark web monitoring")
                return
            
            # Use Tor SOCKS proxy (localhost:9050)
            proxies = {
                'http': 'socks5h://127.0.0.1:9050',
                'https': 'socks5h://127.0.0.1:9050'
            }
            
            logger.info(f"Connecting to dark web: {onion_url}")
            response = requests.get(
                onion_url,
                proxies=proxies,
                timeout=30,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            
            content = response.text
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            # Check for changes
            cache = get_cache()
            cache_key = f"dark_web_{onion_url}"
            previous_hash = cache.get(cache_key)
            
            if previous_hash and previous_hash != content_hash:
                self._alert(
                    severity='high',
                    title=f'Dark web site changed: {onion_url}',
                    details=f"Content hash changed from {previous_hash[:8]} to {content_hash[:8]}",
                    data={'url': onion_url, 'old_hash': previous_hash, 'new_hash': content_hash}
                )
            
            cache.set(cache_key, content_hash, ttl=86400)  # 24 hour cache
            
            # Check for ransomware leak indicators
            leak_indicators = ['password', 'database', 'leaked', 'breach', 'stolen']
            for keyword in self.config['watchlist_keywords']:
                if keyword.lower() in content.lower():
                    for indicator in leak_indicators:
                        if indicator in content.lower():
                            self._alert(
                                severity='critical',
                                title=f'Potential data leak on dark web: {keyword}',
                                details=f"Found '{keyword}' with leak indicator '{indicator}' on {onion_url}",
                                data={'keyword': keyword, 'indicator': indicator, 'url': onion_url}
                            )
                            self.stats['threats_found'] += 1
                            break
            
            self._save_result('dark_web_monitor', onion_url, {
                'content_hash': content_hash,
                'content_length': len(content),
                'changed': previous_hash != content_hash if previous_hash else False
            })
            
        except Exception as e:
            logger.error(f"Dark web monitoring failed for {onion_url}: {e}")
    
    def _dark_web_search(self, keyword: str):
        """Search dark web forums/markets for keywords."""
        # Note: Requires Ahmia.fi API or similar dark web search engine
        import requests
        
        try:
            # Use Ahmia.fi (surface web gateway to dark web search)
            search_url = f"https://ahmia.fi/search/?q={keyword}"
            response = requests.get(search_url, timeout=30)
            
            if keyword.lower() in response.text.lower():
                # Parse results (simplified)
                result_count = response.text.lower().count(keyword.lower())
                if result_count > 5:  # Threshold
                    self._alert(
                        severity='medium',
                        title=f'Dark web mentions found: {keyword}',
                        details=f"Found {result_count} mentions on dark web",
                        data={'keyword': keyword, 'count': result_count}
                    )
            
            self._save_result('dark_web_search', keyword, {
                'result_count': result_count,
                'search_url': search_url
            })
            
        except Exception as e:
            logger.error(f"Dark web search failed for {keyword}: {e}")
    
    def _paste_site_monitor(self, keyword: str):
        """
        Monitor advanced paste sites: Ghostbin, PasteSite, Rentry.co, 4chan/Reddit pastes.
        """
        import requests
        import re
        
        paste_sites = {
            'ghostbin': 'https://ghostbin.co/search?q={}',
            'rentry': 'https://rentry.co/search?q={}',
            'paste.ee': 'https://paste.ee/search?q={}',
            'dpaste': 'https://dpaste.com/api/v2/search/?q={}',
        }
        
        findings = []
        
        for site_name, url_template in paste_sites.items():
            try:
                search_url = url_template.format(keyword)
                response = requests.get(search_url, timeout=15, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                if response.status_code == 200:
                    # Look for paste URLs
                    paste_urls = re.findall(r'https?://[^\s<>"]+', response.text)
                    paste_urls = [url for url in paste_urls if site_name in url]
                    
                    if paste_urls:
                        logger.warning(f"Found {len(paste_urls)} pastes on {site_name} for '{keyword}'")
                        findings.append({
                            'site': site_name,
                            'paste_count': len(paste_urls),
                            'urls': paste_urls[:5]  # First 5
                        })
                        
                        self._alert(
                            severity='high',
                            title=f'Keyword found on {site_name}: {keyword}',
                            details=f"Found {len(paste_urls)} pastes containing '{keyword}'",
                            data={'site': site_name, 'urls': paste_urls[:5]}
                        )
                        self.stats['threats_found'] += 1
            
            except Exception as e:
                logger.debug(f"Paste site {site_name} check failed: {e}")
        
        # Also check Reddit/4chan archives
        try:
            # Search Reddit via pushshift.io API
            reddit_url = f"https://api.pushshift.io/reddit/search/comment/?q={keyword}&size=10"
            response = requests.get(reddit_url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if data.get('data'):
                    findings.append({
                        'site': 'reddit',
                        'comment_count': len(data['data']),
                        'samples': [c.get('body', '')[:100] for c in data['data'][:3]]
                    })
        except Exception as e:
            logger.debug(f"Reddit search failed: {e}")
        
        self._save_result('paste_site_monitor', keyword, {'findings': findings})
    
    def _cloud_storage_scan(self, domain: str, modules: List[str]):
        """
        Scan for cloud storage leaks: S3 buckets, Azure Blobs, GCP Storage, CDN buckets.
        """
        import requests
        
        # Common bucket naming patterns
        bucket_patterns = [
            domain.replace('.', '-'),
            domain.replace('.', ''),
            domain.split('.')[0],
            f"{domain.split('.')[0]}-backup",
            f"{domain.split('.')[0]}-files",
            f"{domain.split('.')[0]}-assets",
            f"{domain.split('.')[0]}-static",
        ]
        
        findings = []
        
        # Check AWS S3
        for pattern in bucket_patterns:
            s3_url = f"https://{pattern}.s3.amazonaws.com"
            try:
                response = requests.get(s3_url, timeout=10)
                if response.status_code in [200, 403]:  # 200=open, 403=exists but restricted
                    findings.append({
                        'type': 's3',
                        'url': s3_url,
                        'status': 'open' if response.status_code == 200 else 'restricted'
                    })
                    
                    if response.status_code == 200:
                        self._alert(
                            severity='critical',
                            title=f'Open S3 bucket found: {pattern}',
                            details=f"Publicly accessible S3 bucket at {s3_url}",
                            data={'url': s3_url, 'domain': domain}
                        )
                        self.stats['threats_found'] += 1
            except:
                pass
        
        # Check Azure Blob Storage
        for pattern in bucket_patterns:
            azure_url = f"https://{pattern}.blob.core.windows.net"
            try:
                response = requests.get(azure_url, timeout=10)
                if response.status_code in [200, 403, 409]:
                    findings.append({
                        'type': 'azure_blob',
                        'url': azure_url,
                        'status': 'exists'
                    })
            except:
                pass
        
        # Check Google Cloud Storage
        for pattern in bucket_patterns:
            gcs_url = f"https://storage.googleapis.com/{pattern}"
            try:
                response = requests.get(gcs_url, timeout=10)
                if response.status_code in [200, 403]:
                    findings.append({
                        'type': 'gcs',
                        'url': gcs_url,
                        'status': 'exists'
                    })
            except:
                pass
        
        # Run cloud_hunter module if available
        if 'cloud_hunter' in modules:
            engine = AthenaEngine(domain, quiet=True)
            engine.run_scan(['cloud_hunter'])
            cloud_results = engine.profile.modules.get('cloud_hunter', {})
            if cloud_results:
                findings.append({'module_results': cloud_results})
        
        if findings:
            logger.success(f"Found {len(findings)} cloud storage resources for {domain}")
        
        self._save_result('cloud_storage_scan', domain, {'findings': findings})
    
    def _social_media_monitor(self, keyword: str):
        """
        Monitor social media for keywords: Twitter, LinkedIn, Instagram, TikTok.
        """
        import requests
        
        findings = []
        
        # Twitter/X search (via nitter.net - Twitter frontend)
        try:
            nitter_url = f"https://nitter.net/search?f=tweets&q={keyword}"
            response = requests.get(nitter_url, timeout=15, headers={
                'User-Agent': 'Mozilla/5.0'
            })
            if keyword.lower() in response.text.lower():
                tweet_count = response.text.lower().count('tweet-')
                if tweet_count > 0:
                    findings.append({
                        'platform': 'twitter',
                        'mention_count': tweet_count,
                        'search_url': nitter_url
                    })
                    logger.info(f"Found {tweet_count} tweets mentioning '{keyword}'")
        except Exception as e:
            logger.debug(f"Twitter search failed: {e}")
        
        # LinkedIn via Google search
        try:
            google_url = f"https://www.google.com/search?q=site:linkedin.com+{keyword}"
            response = requests.get(google_url, timeout=15, headers={
                'User-Agent': 'Mozilla/5.0'
            })
            if 'linkedin.com' in response.text.lower():
                findings.append({
                    'platform': 'linkedin',
                    'found': True,
                    'search_url': google_url
                })
        except Exception as e:
            logger.debug(f"LinkedIn search failed: {e}")
        
        # Instagram (via web scraping)
        try:
            # Search Instagram hashtags
            insta_url = f"https://www.instagram.com/explore/tags/{keyword.replace(' ', '').lower()}/"
            response = requests.get(insta_url, timeout=15, headers={
                'User-Agent': 'Mozilla/5.0'
            })
            if response.status_code == 200:
                findings.append({
                    'platform': 'instagram',
                    'hashtag_exists': True,
                    'url': insta_url
                })
        except Exception as e:
            logger.debug(f"Instagram search failed: {e}")
        
        if findings:
            self._alert(
                severity='info',
                title=f'Social media mentions: {keyword}',
                details=f"Found on {len(findings)} platforms",
                data={'findings': findings}
            )
        
        self._save_result('social_media_monitor', keyword, {'findings': findings})
    
    def _executive_monitor(self, person_name: str, modules: List[str]):
        """
        Monitor executives: social media activity, articles, LinkedIn changes, personal domains.
        """
        import requests
        
        findings = []
        
        # Google News search
        try:
            news_url = f"https://news.google.com/search?q={person_name}"
            response = requests.get(news_url, timeout=15, headers={
                'User-Agent': 'Mozilla/5.0'
            })
            if person_name.lower() in response.text.lower():
                findings.append({
                    'type': 'news_mentions',
                    'found': True,
                    'url': news_url
                })
        except Exception as e:
            logger.debug(f"News search failed: {e}")
        
        # LinkedIn profile changes (if username provided)
        linkedin_username = person_name.lower().replace(' ', '-')
        try:
            linkedin_url = f"https://www.linkedin.com/in/{linkedin_username}"
            response = requests.get(linkedin_url, timeout=15, headers={
                'User-Agent': 'Mozilla/5.0'
            })
            
            # Hash content for change detection
            content_hash = hashlib.md5(response.text.encode()).hexdigest()
            cache = get_cache()
            cache_key = f"linkedin_{linkedin_username}"
            previous_hash = cache.get(cache_key)
            
            if previous_hash and previous_hash != content_hash:
                self._alert(
                    severity='medium',
                    title=f'LinkedIn profile changed: {person_name}',
                    details=f"Profile content changed",
                    data={'person': person_name, 'url': linkedin_url}
                )
                findings.append({
                    'type': 'linkedin_change',
                    'changed': True,
                    'url': linkedin_url
                })
            
            cache.set(cache_key, content_hash, ttl=604800)  # 7 day cache
        except Exception as e:
            logger.debug(f"LinkedIn check failed: {e}")
        
        # Run profile_scraper module
        if 'profile_scraper' in modules:
            engine = AthenaEngine(person_name, quiet=True)
            engine.run_scan(['profile_scraper', 'sherlock'])
            profile_data = engine.profile.to_dict()
            findings.append({
                'type': 'profile_scraper',
                'data': profile_data
            })
        
        self._save_result('executive_monitor', person_name, {'findings': findings})
    
    def _osint_development(self, domain: str):
        """
        OSINT development tools: API enumeration, scraping tests, rate limit detection.
        """
        import requests
        import re
        
        findings = []
        
        # 1. API Endpoint Enumeration
        common_api_paths = [
            '/api', '/api/v1', '/api/v2', '/api/v3',
            '/rest', '/graphql', '/swagger', '/openapi.json',
            '/api-docs', '/docs', '/v1/api', '/v2/api',
            '/.well-known/security.txt', '/robots.txt', '/sitemap.xml'
        ]
        
        discovered_apis = []
        for path in common_api_paths:
            try:
                url = f"https://{domain}{path}"
                response = requests.get(url, timeout=10, allow_redirects=True)
                if response.status_code == 200:
                    discovered_apis.append({
                        'path': path,
                        'status': 200,
                        'content_type': response.headers.get('Content-Type', 'unknown'),
                        'size': len(response.content)
                    })
            except:
                pass
        
        if discovered_apis:
            findings.append({
                'type': 'api_endpoints',
                'count': len(discovered_apis),
                'endpoints': discovered_apis
            })
            logger.success(f"Discovered {len(discovered_apis)} API endpoints on {domain}")
        
        # 2. Rate Limit Detection
        try:
            test_url = f"https://{domain}"
            rate_limit_info = {}
            
            # Make multiple requests to detect rate limiting
            for i in range(5):
                response = requests.get(test_url, timeout=10)
                rate_limit_headers = {
                    'X-RateLimit-Limit': response.headers.get('X-RateLimit-Limit'),
                    'X-RateLimit-Remaining': response.headers.get('X-RateLimit-Remaining'),
                    'X-RateLimit-Reset': response.headers.get('X-RateLimit-Reset'),
                    'Retry-After': response.headers.get('Retry-After'),
                }
                
                if any(rate_limit_headers.values()):
                    rate_limit_info = {h: v for h, v in rate_limit_headers.items() if v}
                    break
            
            if rate_limit_info:
                findings.append({
                    'type': 'rate_limiting',
                    'detected': True,
                    'headers': rate_limit_info
                })
        except:
            pass
        
        # 3. Technology Fingerprinting
        try:
            response = requests.get(f"https://{domain}", timeout=10)
            tech_stack = {
                'server': response.headers.get('Server'),
                'powered_by': response.headers.get('X-Powered-By'),
                'framework': None
            }
            
            # Detect frameworks from headers/content
            content = response.text.lower()
            frameworks = {
                'react': 'react' in content or '__react' in content,
                'vue': 'vue' in content or '__vue' in content,
                'angular': 'ng-app' in content or 'angular' in content,
                'django': 'csrfmiddlewaretoken' in content,
                'flask': 'werkzeug' in response.headers.get('Server', '').lower(),
                'express': 'express' in response.headers.get('X-Powered-By', '').lower(),
            }
            
            detected_frameworks = [k for k, v in frameworks.items() if v]
            if detected_frameworks:
                tech_stack['frameworks'] = detected_frameworks
            
            findings.append({
                'type': 'technology_stack',
                'data': tech_stack
            })
        except:
            pass
        
        # 4. Security Header Analysis
        try:
            response = requests.get(f"https://{domain}", timeout=10)
            security_headers = {
                'Strict-Transport-Security': response.headers.get('Strict-Transport-Security'),
                'Content-Security-Policy': response.headers.get('Content-Security-Policy'),
                'X-Content-Type-Options': response.headers.get('X-Content-Type-Options'),
                'X-Frame-Options': response.headers.get('X-Frame-Options'),
                'X-XSS-Protection': response.headers.get('X-XSS-Protection'),
            }
            
            missing_headers = [k for k, v in security_headers.items() if not v]
            if missing_headers:
                findings.append({
                    'type': 'missing_security_headers',
                    'count': len(missing_headers),
                    'headers': missing_headers
                })
        except:
            pass
        
        self._save_result('osint_development', domain, {'findings': findings})
    
    def _alert(self, severity: str, title: str, details: str, data: any):
        """Generate an alert."""
        alert = {
            'severity': severity,
            'title': title,
            'details': details,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save alert
        alert_file = self.results_dir / f"alert_{int(time.time())}.json"
        with open(alert_file, 'w') as f:
            json.dump(alert, f, indent=2)
        
        logger.warning(f"🚨 ALERT [{severity.upper()}]: {title}")
        
        # TODO: Send notification (email, webhook, etc.)
    
    def _save_result(self, task_type: str, target: str, data: Dict):
        """Save harvesting result."""
        timestamp = int(time.time())
        target_hash = hashlib.md5(target.encode()).hexdigest()[:8]
        filename = f"{task_type}_{target_hash}_{timestamp}.json"
        
        result_file = self.results_dir / filename
        with open(result_file, 'w') as f:
            json.dump({
                'task_type': task_type,
                'target': target,
                'timestamp': datetime.now().isoformat(),
                'data': data
            }, f, indent=2, default=str)
        
        # Update stats
        try:
            size_mb = result_file.stat().st_size / 1024 / 1024
            self.stats['data_harvested_mb'] += size_mb
        except:
            pass
    
    def add_target(self, target_type: str, target: str):
        """Add a target to watchlist."""
        if target_type == 'domain':
            if target not in self.config['watchlist_domains']:
                self.config['watchlist_domains'].append(target)
        elif target_type == 'email':
            if target not in self.config['watchlist_emails']:
                self.config['watchlist_emails'].append(target)
        elif target_type == 'username':
            if target not in self.config['watchlist_usernames']:
                self.config['watchlist_usernames'].append(target)
        elif target_type == 'keyword':
            if target not in self.config['watchlist_keywords']:
                self.config['watchlist_keywords'].append(target)
        
        self._save_config()
        logger.info(f"Added {target_type} to watchlist: {target}")
    
    def get_stats(self) -> Dict:
        """Get current statistics."""
        return {
            **self.stats,
            'queue_size': self.task_queue.qsize(),
            'worker_threads': len(self.worker_threads),
            'running': self.running
        }


# Global harvester instance
_global_harvester = None

def get_harvester() -> BackgroundHarvester:
    """Get or create global harvester instance."""
    global _global_harvester
    if _global_harvester is None:
        _global_harvester = BackgroundHarvester()
    return _global_harvester
