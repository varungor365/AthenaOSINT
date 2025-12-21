"""
Intelligent Caching & Result Aggregation System.
In-memory caching with TTL, deduplication, and smart merging.
"""
import time
import hashlib
import json
import threading
from typing import Any, Optional, Dict, List
from collections import OrderedDict
from datetime import datetime, timedelta
from loguru import logger

from config.production import MEMORY_CONFIG, SCAN_CONFIG


class IntelligentCache:
    """
    Thread-safe LRU cache with TTL and smart deduplication.
    Optimized for 16GB RAM with configurable size limits.
    """
    
    def __init__(self, max_size_mb: int = None, default_ttl: int = 3600):
        self.max_size_bytes = (max_size_mb or MEMORY_CONFIG['cache_max_size_mb']) * 1024 * 1024
        self.default_ttl = default_ttl
        self.cache = OrderedDict()
        self.metadata = {}  # Stores TTL and size info
        self.current_size = 0
        self.lock = threading.RLock()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'size_evictions': 0
        }
        logger.info(f"Cache initialized: {max_size_mb}MB max, {default_ttl}s TTL")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        with self.lock:
            if key not in self.cache:
                self.stats['misses'] += 1
                return None
            
            # Check expiration
            meta = self.metadata[key]
            if time.time() > meta['expires_at']:
                self._evict(key)
                self.stats['misses'] += 1
                return None
            
            # Move to end (LRU)
            self.cache.move_to_end(key)
            self.stats['hits'] += 1
            
            logger.debug(f"Cache HIT: {key[:50]}")
            return self.cache[key]
    
    def set(self, key: str, value: Any, ttl: int = None):
        """Store value in cache with optional TTL."""
        with self.lock:
            # Calculate size
            try:
                value_size = len(json.dumps(value, default=str).encode('utf-8'))
            except:
                value_size = 1024  # Estimate
            
            # Check if single item exceeds max size
            if value_size > self.max_size_bytes:
                logger.warning(f"Cache item too large ({value_size} bytes), skipping")
                return
            
            # Evict old items if needed
            while (self.current_size + value_size > self.max_size_bytes) and self.cache:
                # Remove oldest item
                oldest_key = next(iter(self.cache))
                self._evict(oldest_key)
                self.stats['size_evictions'] += 1
            
            # Store
            self.cache[key] = value
            self.metadata[key] = {
                'size': value_size,
                'expires_at': time.time() + (ttl or self.default_ttl),
                'created_at': time.time()
            }
            self.current_size += value_size
            
            # Move to end
            self.cache.move_to_end(key)
            
            logger.debug(f"Cache SET: {key[:50]} ({value_size} bytes)")
    
    def _evict(self, key: str):
        """Remove item from cache."""
        if key in self.cache:
            size = self.metadata[key]['size']
            del self.cache[key]
            del self.metadata[key]
            self.current_size -= size
            self.stats['evictions'] += 1
    
    def clear(self):
        """Clear all cache."""
        with self.lock:
            self.cache.clear()
            self.metadata.clear()
            self.current_size = 0
            logger.info("Cache cleared")
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        with self.lock:
            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                **self.stats,
                'size_mb': self.current_size / 1024 / 1024,
                'items': len(self.cache),
                'hit_rate': hit_rate
            }


class ResultDeduplicator:
    """
    Smart deduplication and merging of scan results.
    Prevents redundant scans and intelligently merges overlapping data.
    """
    
    def __init__(self):
        self.hash_cache = {}
        self.lock = threading.Lock()
    
    def get_scan_hash(self, target: str, modules: List[str]) -> str:
        """Generate unique hash for scan configuration."""
        canonical = json.dumps({
            'target': target.lower().strip(),
            'modules': sorted(modules)
        }, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()
    
    def is_duplicate_scan(
        self,
        target: str,
        modules: List[str],
        recent_minutes: int = 30
    ) -> Optional[Dict]:
        """
        Check if identical scan was run recently.
        
        Returns:
            Recent scan data if found, None otherwise
        """
        scan_hash = self.get_scan_hash(target, modules)
        
        with self.lock:
            if scan_hash in self.hash_cache:
                cached = self.hash_cache[scan_hash]
                age_minutes = (time.time() - cached['timestamp']) / 60
                
                if age_minutes < recent_minutes:
                    logger.info(f"Duplicate scan detected (age: {age_minutes:.1f}m)")
                    return cached['result']
        
        return None
    
    def store_scan(self, target: str, modules: List[str], result: Any):
        """Store scan result for deduplication."""
        scan_hash = self.get_scan_hash(target, modules)
        
        with self.lock:
            self.hash_cache[scan_hash] = {
                'timestamp': time.time(),
                'result': result
            }
            
            # Cleanup old entries (> 2 hours)
            cutoff = time.time() - 7200
            to_delete = [
                k for k, v in self.hash_cache.items()
                if v['timestamp'] < cutoff
            ]
            for k in to_delete:
                del self.hash_cache[k]
    
    def merge_profiles(self, profiles: List[Any]) -> Any:
        """
        Intelligently merge multiple Profile objects.
        Deduplicates and combines all findings.
        """
        if not profiles:
            return None
        
        if len(profiles) == 1:
            return profiles[0]
        
        # Use first profile as base
        merged = profiles[0]
        
        for profile in profiles[1:]:
            # Merge emails (deduplicate)
            merged.emails = list(set(merged.emails + profile.emails))
            
            # Merge usernames (dict merge)
            merged.usernames.update(profile.usernames)
            
            # Merge lists with dedup
            merged.phone_numbers = list(set(merged.phone_numbers + profile.phone_numbers))
            merged.domains = list(set(merged.domains + profile.domains))
            merged.subdomains = list(set(merged.subdomains + profile.subdomains))
            merged.related_ips = list(set(merged.related_ips + profile.related_ips))
            
            # Merge complex data (deduplicate by content hash)
            merged.breaches = self._deduplicate_dicts(merged.breaches + profile.breaches)
            merged.metadata = self._deduplicate_dicts(merged.metadata + profile.metadata)
            merged.social_posts = self._deduplicate_dicts(merged.social_posts + profile.social_posts)
            
            # Merge raw data
            for key, value in profile.raw_data.items():
                if key not in merged.raw_data:
                    merged.raw_data[key] = value
                elif isinstance(value, list):
                    merged.raw_data[key] = self._deduplicate_dicts(
                        merged.raw_data[key] + value
                    )
            
            # Merge modules run
            merged.modules_run = list(set(merged.modules_run + profile.modules_run))
            
            # Merge errors
            merged.errors = self._deduplicate_dicts(merged.errors + profile.errors)
        
        logger.info(f"Merged {len(profiles)} profiles into one")
        return merged
    
    def _deduplicate_dicts(self, items: List[Dict]) -> List[Dict]:
        """Deduplicate list of dicts by content hash."""
        seen = set()
        unique = []
        
        for item in items:
            # Generate hash from sorted keys/values
            item_hash = hashlib.md5(
                json.dumps(item, sort_keys=True, default=str).encode()
            ).hexdigest()
            
            if item_hash not in seen:
                seen.add(item_hash)
                unique.append(item)
        
        return unique


# Global instances
_global_cache = None
_global_deduplicator = None

def get_cache() -> IntelligentCache:
    """Get or create global cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = IntelligentCache()
    return _global_cache

def get_deduplicator() -> ResultDeduplicator:
    """Get or create global deduplicator instance."""
    global _global_deduplicator
    if _global_deduplicator is None:
        _global_deduplicator = ResultDeduplicator()
    return _global_deduplicator
