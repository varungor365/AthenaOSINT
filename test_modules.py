#!/usr/bin/env python3
"""
Module Integration Test Suite

Tests actual execution of critical OSINT modules to ensure they work properly.
"""

import sys
import json
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))


class ModuleIntegrationTests:
    """Test suite for module integrations."""
    
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
        
    def log(self, message, level='INFO'):
        """Log test message."""
        symbols = {
            'INFO': '✓',
            'WARN': '⚠',
            'ERROR': '✗',
            'TEST': '🔍'
        }
        print(f"{symbols.get(level, 'ℹ')} {message}")
        
    def test_module(self, module_name, target, target_type):
        """Test a specific module."""
        self.log(f"Testing {module_name} with {target}...", 'TEST')
        
        try:
            from core.engine import AthenaEngine
            
            engine = AthenaEngine()
            
            # Run scan with timeout
            result = engine.run_scan(
                target=target,
                target_type=target_type,
                modules=[module_name],
                max_depth=1
            )
            
            if result and 'error' not in str(result).lower():
                self.log(f"{module_name}: PASSED", 'INFO')
                self.passed += 1
                self.results.append({
                    'module': module_name,
                    'status': 'passed',
                    'target': target
                })
                return True
            else:
                self.log(f"{module_name}: FAILED - {result.get('error', 'Unknown error')}", 'ERROR')
                self.failed += 1
                self.results.append({
                    'module': module_name,
                    'status': 'failed',
                    'error': str(result)
                })
                return False
                
        except Exception as e:
            self.log(f"{module_name}: ERROR - {e}", 'ERROR')
            self.failed += 1
            self.results.append({
                'module': module_name,
                'status': 'error',
                'error': str(e)
            })
            return False
    
    def test_validators(self):
        """Test target validators."""
        self.log("\nTesting validators...", 'TEST')
        
        from core.validators import validate_target, detect_target_type
        
        test_cases = [
            ('example.com', 'domain', True),
            ('test@example.com', 'email', True),
            ('user123', 'username', True),
            ('192.168.1.1', 'ip', True),
            ('not-valid@', 'email', False),
        ]
        
        for target, expected_type, should_be_valid in test_cases:
            detected = detect_target_type(target)
            is_valid = validate_target(target)
            
            if detected == expected_type and is_valid == should_be_valid:
                self.log(f"Validator {target}: OK", 'INFO')
                self.passed += 1
            else:
                self.log(f"Validator {target}: FAILED (detected={detected}, valid={is_valid})", 'ERROR')
                self.failed += 1
    
    def test_breach_indexer(self):
        """Test breach indexer with sample data."""
        self.log("\nTesting breach indexer...", 'TEST')
        
        try:
            from intelligence.breach_indexer import BreachIndexer
            
            indexer = BreachIndexer()
            
            # Create test file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                test_file = Path(f.name)
                f.write("test@example.com:password123\n")
                f.write("user@test.org:secret456\n")
            
            # Index test file
            result = indexer.index_file(test_file)
            
            if 'error' not in result and result.get('indexed', 0) > 0:
                self.log("Breach indexer: PASSED", 'INFO')
                self.passed += 1
                
                # Test search
                search_result = indexer.search_email('test@example.com')
                if search_result:
                    self.log("Breach search: PASSED", 'INFO')
                    self.passed += 1
                else:
                    self.log("Breach search: FAILED", 'ERROR')
                    self.failed += 1
            else:
                self.log("Breach indexer: FAILED", 'ERROR')
                self.failed += 1
            
            # Cleanup
            test_file.unlink(missing_ok=True)
            
        except Exception as e:
            self.log(f"Breach indexer test: ERROR - {e}", 'ERROR')
            self.failed += 1
    
    def test_api_rotator(self):
        """Test API key rotation system."""
        self.log("\nTesting API rotator...", 'TEST')
        
        try:
            from core.api_rotator import APIRotator
            
            rotator = APIRotator()
            
            # Add test key
            rotator.add_key('github', 'test_key_12345')
            
            # Get key
            key = rotator.get_key('github')
            
            if key:
                self.log("API rotator: PASSED", 'INFO')
                self.passed += 1
            else:
                self.log("API rotator: FAILED", 'ERROR')
                self.failed += 1
            
            # Get stats
            stats = rotator.get_all_stats()
            if stats and 'github' in stats:
                self.log("API stats: PASSED", 'INFO')
                self.passed += 1
            else:
                self.log("API stats: FAILED", 'ERROR')
                self.failed += 1
                
        except Exception as e:
            self.log(f"API rotator test: ERROR - {e}", 'ERROR')
            self.failed += 1
    
    def test_web_endpoints(self):
        """Test web API endpoints."""
        self.log("\nTesting web endpoints...", 'TEST')
        
        try:
            import requests
            
            base_url = 'http://127.0.0.1:5000'
            
            endpoints = [
                ('/', 'Dashboard'),
                ('/api/modules', 'Modules API'),
                ('/api/system/stats', 'System Stats'),
                ('/api/breach/daemon/status', 'Daemon Status'),
            ]
            
            for path, name in endpoints:
                try:
                    response = requests.get(f'{base_url}{path}', timeout=5)
                    if response.status_code == 200:
                        self.log(f"{name}: OK", 'INFO')
                        self.passed += 1
                    else:
                        self.log(f"{name}: FAILED (HTTP {response.status_code})", 'ERROR')
                        self.failed += 1
                except Exception as e:
                    self.log(f"{name}: ERROR - {e}", 'ERROR')
                    self.failed += 1
                    
        except ImportError:
            self.log("requests library not available, skipping web tests", 'WARN')
    
    def generate_report(self):
        """Generate test report."""
        self.log("\n" + "="*70, 'TEST')
        self.log("MODULE INTEGRATION TEST SUMMARY", 'TEST')
        self.log("="*70, 'TEST')
        
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        
        self.log(f"\nTotal Tests: {total}", 'INFO')
        self.log(f"Passed: {self.passed}", 'INFO')
        self.log(f"Failed: {self.failed}", 'ERROR' if self.failed > 0 else 'INFO')
        self.log(f"Pass Rate: {pass_rate:.1f}%", 'INFO')
        
        # Save results
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': total,
            'passed': self.passed,
            'failed': self.failed,
            'pass_rate': pass_rate,
            'results': self.results
        }
        
        report_file = Path('module_test_results.json')
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.log(f"\nReport saved to: {report_file}", 'INFO')
        
        return self.failed == 0
    
    def run_all(self):
        """Run all integration tests."""
        self.log("="*70, 'TEST')
        self.log("ATHENA OSINT MODULE INTEGRATION TESTS", 'TEST')
        self.log("="*70, 'TEST')
        
        # Core functionality tests
        self.test_validators()
        self.test_breach_indexer()
        self.test_api_rotator()
        
        # Module execution tests (lightweight targets only)
        self.log("\nTesting module execution...", 'TEST')
        
        # Note: These are lightweight tests, not full scans
        critical_modules = [
            ('sentiment', 'This is a test', 'text'),
            # Add more safe, quick tests here
        ]
        
        for module, target, target_type in critical_modules:
            self.test_module(module, target, target_type)
        
        # Web endpoint tests
        self.test_web_endpoints()
        
        return self.generate_report()


if __name__ == '__main__':
    tests = ModuleIntegrationTests()
    success = tests.run_all()
    sys.exit(0 if success else 1)
