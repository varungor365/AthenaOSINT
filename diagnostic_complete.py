#!/usr/bin/env python3
"""
Complete System Diagnostic for AthenaOSINT

Tests every component:
- Module availability and execution
- API endpoints
- Database connections
- Breach system
- Dependencies
- Configuration
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
import importlib

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

class SystemDiagnostic:
    """Comprehensive system diagnostic tool."""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests_passed': 0,
            'tests_failed': 0,
            'issues': []
        }
        
    def log(self, message, level='INFO'):
        """Log diagnostic message."""
        prefix = {
            'INFO': '✓',
            'WARN': '⚠',
            'ERROR': '✗',
            'TEST': '🔍'
        }.get(level, 'ℹ')
        print(f"{prefix} {message}")
        
    def add_issue(self, category, issue, severity='ERROR'):
        """Add issue to results."""
        self.results['issues'].append({
            'category': category,
            'issue': issue,
            'severity': severity
        })
        if severity == 'ERROR':
            self.results['tests_failed'] += 1
        
    def test_imports(self):
        """Test critical imports."""
        self.log("Testing Python imports...", 'TEST')
        
        critical_modules = [
            ('flask', 'Flask'),
            ('flask_socketio', 'Flask-SocketIO'),
            ('eventlet', 'Eventlet'),
            ('playwright', 'Playwright'),
            ('aiohttp', 'AioHTTP'),
            ('bs4', 'BeautifulSoup4'),
            ('magic', 'python-magic'),
            ('mmh3', 'MurmurHash3'),
            ('loguru', 'Loguru'),
            ('psutil', 'PSUtil'),
        ]
        
        for module_name, display_name in critical_modules:
            try:
                importlib.import_module(module_name)
                self.log(f"{display_name}: OK", 'INFO')
                self.results['tests_passed'] += 1
            except ImportError as e:
                self.log(f"{display_name}: FAILED - {e}", 'ERROR')
                self.add_issue('Dependencies', f'{display_name} not installed: {e}')
                
    def test_project_imports(self):
        """Test project modules."""
        self.log("\nTesting project modules...", 'TEST')
        
        project_modules = [
            'config.config',
            'core.engine',
            'core.validators',
            'core.api_manager',
            'intelligence.breach_monitor',
            'intelligence.breach_indexer',
            'intelligence.llm',
            'modules',
            'web.routes'
        ]
        
        for module_name in project_modules:
            try:
                importlib.import_module(module_name)
                self.log(f"{module_name}: OK", 'INFO')
                self.results['tests_passed'] += 1
            except Exception as e:
                self.log(f"{module_name}: FAILED - {e}", 'ERROR')
                self.add_issue('Project Modules', f'{module_name} import failed: {e}')
                
    def test_configuration(self):
        """Test configuration."""
        self.log("\nTesting configuration...", 'TEST')
        
        try:
            from config import get_config
            config = get_config()
            
            # Check critical config values
            checks = [
                ('FLASK_HOST', config.get('FLASK_HOST')),
                ('FLASK_PORT', config.get('FLASK_PORT')),
                ('DATA_DIR', config.get('DATA_DIR')),
            ]
            
            for key, value in checks:
                if value:
                    self.log(f"Config {key}: {value}", 'INFO')
                    self.results['tests_passed'] += 1
                else:
                    self.log(f"Config {key}: NOT SET", 'WARN')
                    self.add_issue('Configuration', f'{key} not configured', 'WARN')
                    
            # Check API keys (warnings only)
            api_keys = [
                'GROQ_API_KEY',
                'OPENAI_API_KEY', 
                'HIBP_API_KEY',
                'SHODAN_API_KEY'
            ]
            
            for key in api_keys:
                if config.get(key):
                    self.log(f"API Key {key}: SET ({'*' * 10})", 'INFO')
                else:
                    self.log(f"API Key {key}: NOT SET (optional)", 'WARN')
                    
        except Exception as e:
            self.log(f"Configuration test failed: {e}", 'ERROR')
            self.add_issue('Configuration', f'Config system failed: {e}')
            
    def test_directories(self):
        """Test required directories."""
        self.log("\nTesting directory structure...", 'TEST')
        
        required_dirs = [
            'data',
            'data/breach_vault',
            'data/breach_vault/downloads',
            'data/breach_vault/processed',
            'data/breach_vault/quarantine',
            'logs',
            'reports',
            'modules',
            'intelligence',
            'core',
            'web',
            'web/templates'
        ]
        
        for dir_path in required_dirs:
            path = Path(dir_path)
            if path.exists():
                self.log(f"Directory {dir_path}: OK", 'INFO')
                self.results['tests_passed'] += 1
            else:
                self.log(f"Directory {dir_path}: MISSING", 'WARN')
                self.add_issue('File System', f'Directory missing: {dir_path}', 'WARN')
                
    def test_modules_availability(self):
        """Test OSINT modules."""
        self.log("\nTesting OSINT modules...", 'TEST')
        
        try:
            from modules import get_available_modules
            modules = get_available_modules()
            
            available = sum(1 for m in modules.values() if m.get('available'))
            total = len(modules)
            
            self.log(f"Modules available: {available}/{total}", 'INFO')
            self.results['tests_passed'] += 1
            
            # Check critical modules
            critical = ['sherlock', 'holehe', 'theharvester', 'subfinder', 'nuclei']
            for module_name in critical:
                if module_name in modules and modules[module_name].get('available'):
                    self.log(f"  {module_name}: AVAILABLE", 'INFO')
                else:
                    self.log(f"  {module_name}: UNAVAILABLE", 'WARN')
                    self.add_issue('Modules', f'{module_name} not available', 'WARN')
                    
        except Exception as e:
            self.log(f"Module test failed: {e}", 'ERROR')
            self.add_issue('Modules', f'Module system failed: {e}')
            
    def test_breach_system(self):
        """Test breach monitoring system."""
        self.log("\nTesting breach system...", 'TEST')
        
        try:
            # Test indexer
            from intelligence.breach_indexer import BreachIndexer
            indexer = BreachIndexer()
            stats = indexer.get_breach_stats()
            
            self.log(f"Breach indexer: OK", 'INFO')
            self.log(f"  Total credentials: {stats.get('total_credentials', 0)}", 'INFO')
            self.log(f"  Total breaches: {stats.get('total_breaches', 0)}", 'INFO')
            self.results['tests_passed'] += 1
            
            # Test monitor (import only, don't run)
            from intelligence.breach_monitor import BreachMonitor
            self.log(f"Breach monitor: OK (import)", 'INFO')
            self.results['tests_passed'] += 1
            
        except Exception as e:
            self.log(f"Breach system test failed: {e}", 'ERROR')
            self.add_issue('Breach System', f'Breach system failed: {e}')
            
    def test_database(self):
        """Test database connections."""
        self.log("\nTesting databases...", 'TEST')
        
        try:
            import sqlite3
            
            # Check breach database
            db_path = Path('data/breach_vault/breach_index.db')
            if db_path.exists():
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM breaches")
                count = cursor.fetchone()[0]
                conn.close()
                
                self.log(f"Breach DB: OK ({count} records)", 'INFO')
                self.results['tests_passed'] += 1
            else:
                self.log(f"Breach DB: NOT INITIALIZED", 'WARN')
                self.add_issue('Database', 'Breach database not initialized', 'WARN')
                
        except Exception as e:
            self.log(f"Database test failed: {e}", 'ERROR')
            self.add_issue('Database', f'Database test failed: {e}')
            
    def test_playwright(self):
        """Test Playwright browser."""
        self.log("\nTesting Playwright...", 'TEST')
        
        try:
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                # Check if browser is installed
                browser_types = [p.chromium, p.firefox, p.webkit]
                available = []
                
                for bt in browser_types:
                    try:
                        browser = bt.launch(headless=True)
                        browser.close()
                        available.append(bt.name)
                    except Exception:
                        pass
                        
                if available:
                    self.log(f"Playwright browsers: {', '.join(available)}", 'INFO')
                    self.results['tests_passed'] += 1
                else:
                    self.log(f"Playwright: NO BROWSERS INSTALLED", 'ERROR')
                    self.add_issue('Playwright', 'No browsers installed. Run: playwright install')
                    
        except Exception as e:
            self.log(f"Playwright test failed: {e}", 'ERROR')
            self.add_issue('Playwright', f'Playwright failed: {e}')
            
    def test_engine(self):
        """Test core engine."""
        self.log("\nTesting core engine...", 'TEST')
        
        try:
            from core.engine import AthenaEngine
            from core.validators import validate_target, detect_target_type
            
            # Test validators
            test_cases = [
                ('example.com', 'domain'),
                ('user123', 'username'),
                ('test@example.com', 'email'),
                ('192.168.1.1', 'ip')
            ]
            
            for target, expected_type in test_cases:
                detected = detect_target_type(target)
                is_valid = validate_target(target, detected)
                
                if is_valid and detected == expected_type:
                    self.log(f"Validator {expected_type}: OK", 'INFO')
                    self.results['tests_passed'] += 1
                else:
                    self.log(f"Validator {expected_type}: FAILED", 'ERROR')
                    self.add_issue('Engine', f'Validator failed for {expected_type}')
                    
        except Exception as e:
            self.log(f"Engine test failed: {e}", 'ERROR')
            self.add_issue('Engine', f'Core engine failed: {e}')
            
    def test_api_rotator(self):
        """Test API key rotation system."""
        self.log("\nTesting API rotation...", 'TEST')
        
        try:
            from core.api_rotator import APIRotator
            
            rotator = APIRotator()
            stats = rotator.get_all_stats()
            
            total_keys = sum(len(s['keys']) for s in stats.values())
            self.log(f"API Rotator: OK ({total_keys} keys configured)", 'INFO')
            self.results['tests_passed'] += 1
            
            # Check for configured services
            if stats:
                for service, data in list(stats.items())[:5]:
                    key_count = len(data['keys'])
                    self.log(f"  {service}: {key_count} key(s)", 'INFO')
                    
        except Exception as e:
            self.log(f"API rotator test failed: {e}", 'ERROR')
            self.add_issue('API System', f'API rotator failed: {e}')
            
    def generate_report(self):
        """Generate diagnostic report."""
        self.log("\n" + "="*70, 'TEST')
        self.log("DIAGNOSTIC SUMMARY", 'TEST')
        self.log("="*70, 'TEST')
        
        total_tests = self.results['tests_passed'] + self.results['tests_failed']
        pass_rate = (self.results['tests_passed'] / total_tests * 100) if total_tests > 0 else 0
        
        self.log(f"\nTotal Tests: {total_tests}", 'INFO')
        self.log(f"Passed: {self.results['tests_passed']}", 'INFO')
        self.log(f"Failed: {self.results['tests_failed']}", 'ERROR' if self.results['tests_failed'] > 0 else 'INFO')
        self.log(f"Pass Rate: {pass_rate:.1f}%", 'INFO')
        
        if self.results['issues']:
            self.log(f"\nISSUES FOUND ({len(self.results['issues'])}):", 'WARN')
            
            # Group by category
            by_category = {}
            for issue in self.results['issues']:
                cat = issue['category']
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(issue)
                
            for category, issues in by_category.items():
                self.log(f"\n{category}:", 'WARN')
                for issue in issues:
                    severity = issue['severity']
                    symbol = '✗' if severity == 'ERROR' else '⚠'
                    self.log(f"  {symbol} {issue['issue']}", severity)
        else:
            self.log("\n✓ NO ISSUES FOUND - SYSTEM HEALTHY!", 'INFO')
            
        # Save report
        report_file = Path('diagnostic_report.json')
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        self.log(f"\nReport saved to: {report_file}", 'INFO')
        
        return self.results['tests_failed'] == 0
        
    def run_all(self):
        """Run all diagnostic tests."""
        self.log("="*70, 'TEST')
        self.log("AthenaOSINT COMPLETE SYSTEM DIAGNOSTIC", 'TEST')
        self.log("="*70, 'TEST')
        
        self.test_imports()
        self.test_project_imports()
        self.test_configuration()
        self.test_directories()
        self.test_modules_availability()
        self.test_breach_system()
        self.test_database()
        self.test_playwright()
        self.test_engine()
        self.test_api_rotator()
        
        return self.generate_report()


if __name__ == '__main__':
    diagnostic = SystemDiagnostic()
    success = diagnostic.run_all()
    sys.exit(0 if success else 1)
