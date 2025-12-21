"""
24/7 Background Harvester Daemon.
Continuously collects OSINT intelligence in the background.

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
"""
import time
import threading
import queue
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Callable
from loguru import logger
import random

from core.engine import AthenaEngine, Profile
from core.parallel_engine import ParallelScanEngine
from intelligence.ai_sentinel import get_ai_analyzer
from core.caching import get_cache


class BackgroundHarvester:
    """
    24/7 autonomous OSINT harvester that runs in background.
    Continuously collects intelligence and detects threats.
    """
    
    def __init__(self, config_file: str = "data/harvester_config.json"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
        self.running = False
        self.worker_threads = []
        self.task_queue = queue.Queue()
        self.results_dir = Path("data/harvester_results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.stats = {
            'tasks_completed': 0,
            'targets_monitored': 0,
            'threats_found': 0,
            'data_harvested_mb': 0,
            'uptime_hours': 0,
            'last_activity': None
        }
        
        logger.info("Background Harvester initialized")
    
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
            
            # Task types (enable/disable)
            'tasks': {
                'breach_monitoring': True,
                'subdomain_discovery': True,
                'leak_scanning': True,
                'ssl_monitoring': True,
                'dns_monitoring': True,
                'phishing_detection': True,
                'social_scraping': True,
                'vulnerability_scanning': True,
                'dark_web_monitoring': False,  # Requires Tor
                'github_secrets': True,
                'pastebin_monitoring': True,
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
        }
        
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
        """Worker thread that processes tasks from queue."""
        logger.info(f"Worker {threading.current_thread().name} started")
        
        while self.running:
            try:
                # Get task from queue (with timeout to check running flag)
                try:
                    task = self.task_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                # Execute task
                self._execute_task(task)
                self.task_queue.task_done()
                self.stats['tasks_completed'] += 1
                self.stats['last_activity'] = datetime.now().isoformat()
                
            except Exception as e:
                logger.error(f"Worker error: {e}")
    
    def _task_generator_loop(self):
        """Continuously generates tasks based on configuration."""
        logger.info("Task generator started")
        
        while self.running:
            try:
                # Generate tasks for all enabled task types
                tasks = self._generate_tasks()
                
                for task in tasks:
                    self.task_queue.put(task)
                
                logger.info(f"Generated {len(tasks)} tasks")
                
                # Sleep for configured interval
                interval_seconds = self.config['interval_minutes'] * 60
                for _ in range(interval_seconds):
                    if not self.running:
                        break
                    time.sleep(1)
                
            except Exception as e:
                logger.error(f"Task generator error: {e}")
                time.sleep(60)
    
    def _stats_tracker_loop(self):
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
        if self.config['tasks']['breach_monitoring']:
            for email in self.config['watchlist_emails']:
                tasks.append({
                    'type': 'breach_check',
                    'target': email,
                    'modules': ['holehe', 'leak_checker']
                })
        
        # Subdomain discovery
        if self.config['tasks']['subdomain_discovery']:
            for domain in self.config['watchlist_domains']:
                tasks.append({
                    'type': 'subdomain_scan',
                    'target': domain,
                    'modules': ['subfinder', 'amass']
                })
        
        # Leak scanning (Pastebin, GitHub)
        if self.config['tasks']['leak_scanning']:
            for keyword in self.config['watchlist_keywords']:
                tasks.append({
                    'type': 'leak_scan',
                    'target': keyword,
                    'modules': ['auto_dorker']  # Google dorking
                })
        
        # GitHub secrets
        if self.config['tasks']['github_secrets']:
            for keyword in self.config['watchlist_keywords']:
                tasks.append({
                    'type': 'github_secrets',
                    'target': keyword,
                    'modules': ['auto_dorker']
                })
        
        # Pastebin monitoring
        if self.config['tasks']['pastebin_monitoring']:
            for keyword in self.config['watchlist_keywords']:
                tasks.append({
                    'type': 'pastebin_monitor',
                    'target': keyword,
                    'modules': ['auto_dorker']
                })
        
        # SSL monitoring
        if self.config['tasks']['ssl_monitoring']:
            for domain in self.config['watchlist_domains']:
                tasks.append({
                    'type': 'ssl_check',
                    'target': domain,
                    'modules': []  # Custom SSL check
                })
        
        # Vulnerability scanning
        if self.config['tasks']['vulnerability_scanning']:
            for domain in self.config['watchlist_domains']:
                tasks.append({
                    'type': 'vuln_scan',
                    'target': domain,
                    'modules': ['nuclei']
                })
        
        # Social media scraping
        if self.config['tasks']['social_scraping']:
            for username in self.config['watchlist_usernames']:
                tasks.append({
                    'type': 'social_scrape',
                    'target': username,
                    'modules': ['sherlock', 'profile_scraper']
                })
        
        # Shuffle to avoid patterns
        random.shuffle(tasks)
        
        return tasks[:20]  # Limit to 20 tasks per cycle
    
    def _execute_task(self, task: Dict):
        """Execute a single harvesting task."""
        task_type = task['type']
        target = task['target']
        
        logger.info(f"Executing {task_type} for {target}")
        
        try:
            if task_type == 'breach_check':
                self._breach_check(target, task['modules'])
            elif task_type == 'subdomain_scan':
                self._subdomain_scan(target, task['modules'])
            elif task_type == 'leak_scan':
                self._leak_scan(target)
            elif task_type == 'github_secrets':
                self._github_secrets(target)
            elif task_type == 'ssl_check':
                self._ssl_check(target)
            elif task_type == 'vuln_scan':
                self._vuln_scan(target, task['modules'])
            elif task_type == 'social_scrape':
                self._social_scrape(target, task['modules'])
            else:
                logger.warning(f"Unknown task type: {task_type}")
        
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
    
    def _breach_check(self, email: str, modules: List[str]):
        """Check for new breaches."""
        cache = get_cache()
        cache_key = f"breach_{email}"
        
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
        
        # Update cache
        cache.set(cache_key, engine.profile.breaches, ttl=3600)
        
        # Save results
        self._save_result('breach_check', email, engine.profile.to_dict())
    
    def _subdomain_scan(self, domain: str, modules: List[str]):
        """Scan for new subdomains."""
        cache = get_cache()
        cache_key = f"subdomains_{domain}"
        
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
    
    def _leak_scan(self, keyword: str):
        """Scan for leaks containing keyword."""
        logger.info(f"Scanning for leaks: {keyword}")
        
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
