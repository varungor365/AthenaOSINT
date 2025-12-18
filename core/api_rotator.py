#!/usr/bin/env python3
"""
API Key Rotator

Manages multiple API keys per service, automatic rotation,
health checking, and fallback mechanisms.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from loguru import logger
import threading


class APIRotator:
    """Manages API key rotation and health monitoring."""
    
    def __init__(self, keys_file: Path = None):
        """Initialize API rotator."""
        self.keys_file = keys_file or Path("data/api_keys.json")
        self.keys_file.parent.mkdir(parents=True, exist_ok=True)
        
        # API keys storage: {service: [{key, calls, last_used, status, limits}]}
        self.api_keys: Dict[str, List[Dict]] = defaultdict(list)
        
        # Usage tracking
        self.usage_stats = defaultdict(lambda: {
            'total_calls': 0,
            'failed_calls': 0,
            'last_rotation': None
        })
        
        # Service configurations (rate limits, etc.)
        self.service_configs = {
            'openweathermap': {
                'daily_limit': 1000000,
                'rate_limit': 60,  # calls per minute
                'free_tier': True
            },
            'newsapi': {
                'daily_limit': 100000,
                'rate_limit': 100,
                'free_tier': True
            },
            'hibp': {
                'daily_limit': 1000,
                'rate_limit': 1,  # 1 per 1.5s
                'free_tier': True
            },
            'rapidapi': {
                'daily_limit': 10000,
                'rate_limit': 100,
                'free_tier': True
            },
            'github': {
                'hourly_limit': 5000,
                'rate_limit': 100,
                'free_tier': True
            },
            'exchangerate': {
                'daily_limit': 1000,
                'rate_limit': 10,
                'free_tier': True
            },
            'ipgeolocation': {
                'daily_limit': 10000,
                'rate_limit': 100,
                'free_tier': True
            },
            'spotify': {
                'hourly_limit': 10000,
                'rate_limit': 100,
                'free_tier': True
            },
            'tmdb': {
                'daily_limit': 1000000,
                'rate_limit': 40,
                'free_tier': True
            },
            'nasa': {
                'hourly_limit': 1000,
                'rate_limit': 100,
                'free_tier': True
            },
            'pexels': {
                'hourly_limit': 200,
                'rate_limit': 50,
                'free_tier': True
            },
            'unsplash': {
                'hourly_limit': 50,
                'rate_limit': 50,
                'free_tier': True
            },
            'groq': {
                'daily_limit': 14400,
                'rate_limit': 30,
                'free_tier': True
            },
            'dehashed': {
                'daily_limit': 100,
                'rate_limit': 1,
                'free_tier': False
            }
        }
        
        self._load_keys()
        self._lock = threading.Lock()
        
        logger.info("APIRotator initialized")
    
    def _load_keys(self):
        """Load API keys from storage."""
        if self.keys_file.exists():
            try:
                data = json.loads(self.keys_file.read_text())
                self.api_keys = defaultdict(list, data.get('keys', {}))
                self.usage_stats = defaultdict(
                    lambda: {'total_calls': 0, 'failed_calls': 0, 'last_rotation': None},
                    data.get('stats', {})
                )
                logger.info(f"Loaded {len(self.api_keys)} API services with keys")
            except Exception as e:
                logger.error(f"Failed to load API keys: {e}")
    
    def _save_keys(self):
        """Save API keys to storage."""
        try:
            data = {
                'keys': dict(self.api_keys),
                'stats': dict(self.usage_stats),
                'last_updated': datetime.utcnow().isoformat()
            }
            self.keys_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"Failed to save API keys: {e}")
    
    def add_key(self, service: str, key: str, metadata: Dict = None):
        """Add an API key for a service."""
        with self._lock:
            # Check if key already exists
            for existing in self.api_keys[service]:
                if existing['key'] == key:
                    logger.warning(f"Key already exists for {service}")
                    return False
            
            key_data = {
                'key': key,
                'added': datetime.utcnow().isoformat(),
                'calls': 0,
                'last_used': None,
                'status': 'active',
                'metadata': metadata or {}
            }
            
            self.api_keys[service].append(key_data)
            self._save_keys()
            logger.info(f"Added API key for {service}")
            return True
    
    def remove_key(self, service: str, key: str):
        """Remove an API key."""
        with self._lock:
            self.api_keys[service] = [
                k for k in self.api_keys[service] if k['key'] != key
            ]
            self._save_keys()
            logger.info(f"Removed API key for {service}")
    
    def get_key(self, service: str) -> Optional[str]:
        """Get the best available API key for a service."""
        with self._lock:
            if service not in self.api_keys or not self.api_keys[service]:
                logger.warning(f"No API keys available for {service}")
                return None
            
            # Filter active keys
            active_keys = [k for k in self.api_keys[service] if k['status'] == 'active']
            
            if not active_keys:
                logger.warning(f"No active keys for {service}")
                return None
            
            # Get key with least usage
            best_key = min(active_keys, key=lambda k: k['calls'])
            
            # Update usage
            best_key['calls'] += 1
            best_key['last_used'] = datetime.utcnow().isoformat()
            
            # Check if we should rotate
            config = self.service_configs.get(service, {})
            daily_limit = config.get('daily_limit', 10000)
            
            if best_key['calls'] >= daily_limit * 0.8:  # 80% threshold
                logger.warning(f"Key for {service} approaching limit, consider rotation")
            
            self._save_keys()
            return best_key['key']
    
    def rotate_key(self, service: str) -> Optional[str]:
        """Force rotation to next available key."""
        with self._lock:
            if service not in self.api_keys or len(self.api_keys[service]) < 2:
                return self.get_key(service)
            
            # Mark current most-used key as exhausted temporarily
            active_keys = [k for k in self.api_keys[service] if k['status'] == 'active']
            if active_keys:
                most_used = max(active_keys, key=lambda k: k['calls'])
                most_used['status'] = 'cooling_down'
                most_used['cooldown_until'] = (
                    datetime.utcnow() + timedelta(hours=24)
                ).isoformat()
            
            self.usage_stats[service]['last_rotation'] = datetime.utcnow().isoformat()
            self._save_keys()
            
            return self.get_key(service)
    
    def mark_key_failed(self, service: str, key: str, error: str = None):
        """Mark a key as failed/invalid."""
        with self._lock:
            for key_data in self.api_keys[service]:
                if key_data['key'] == key:
                    key_data['status'] = 'failed'
                    key_data['error'] = error or 'Unknown error'
                    key_data['failed_at'] = datetime.utcnow().isoformat()
                    logger.error(f"Marked {service} key as failed: {error}")
                    break
            
            self.usage_stats[service]['failed_calls'] += 1
            self._save_keys()
    
    def reset_daily_limits(self):
        """Reset daily usage counters (run via cron)."""
        with self._lock:
            for service in self.api_keys:
                for key_data in self.api_keys[service]:
                    key_data['calls'] = 0
                    
                    # Reactivate cooled-down keys
                    if key_data['status'] == 'cooling_down':
                        cooldown_until = datetime.fromisoformat(
                            key_data.get('cooldown_until', datetime.utcnow().isoformat())
                        )
                        if datetime.utcnow() >= cooldown_until:
                            key_data['status'] = 'active'
            
            self._save_keys()
            logger.info("Reset daily API limits")
    
    def get_service_stats(self, service: str) -> Dict:
        """Get statistics for a service."""
        stats = {
            'service': service,
            'total_keys': len(self.api_keys.get(service, [])),
            'active_keys': len([
                k for k in self.api_keys.get(service, []) 
                if k['status'] == 'active'
            ]),
            'failed_keys': len([
                k for k in self.api_keys.get(service, []) 
                if k['status'] == 'failed'
            ]),
            'total_calls': self.usage_stats[service]['total_calls'],
            'failed_calls': self.usage_stats[service]['failed_calls'],
            'last_rotation': self.usage_stats[service]['last_rotation'],
            'config': self.service_configs.get(service, {})
        }
        return stats
    
    def get_all_stats(self) -> Dict:
        """Get statistics for all services."""
        return {
            service: self.get_service_stats(service)
            for service in self.api_keys.keys()
        }
    
    def health_check(self, service: str, key: str, check_func) -> bool:
        """Health check a specific API key."""
        try:
            result = check_func(key)
            if result:
                logger.info(f"Health check passed for {service}")
                return True
            else:
                self.mark_key_failed(service, key, "Health check failed")
                return False
        except Exception as e:
            self.mark_key_failed(service, key, str(e))
            return False


# Global rotator instance
_rotator_instance: Optional[APIRotator] = None


def get_rotator() -> APIRotator:
    """Get global API rotator instance."""
    global _rotator_instance
    if _rotator_instance is None:
        _rotator_instance = APIRotator()
    return _rotator_instance


if __name__ == '__main__':
    rotator = APIRotator()
    
    # Example usage
    rotator.add_key('openweathermap', 'test_key_123')
    rotator.add_key('openweathermap', 'test_key_456')
    
    key = rotator.get_key('openweathermap')
    print(f"Got key: {key}")
    
    stats = rotator.get_service_stats('openweathermap')
    print(json.dumps(stats, indent=2))
