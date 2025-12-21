"""
Production Configuration for 16GB RAM Droplet.
High-performance settings for concurrent scan processing.
"""

# Gunicorn Configuration (optimized for 16GB RAM)
GUNICORN_CONFIG = {
    'bind': '127.0.0.1:5000',
    'workers': 12,  # 16GB RAM: 12 workers for high concurrency
    'worker_class': 'gevent',  # Async workers for Socket.IO + concurrent requests
    'worker_connections': 1000,  # Max concurrent connections per worker
    'timeout': 300,  # 5 min timeout for long-running scans
    'max_requests': 5000,  # Restart worker after 5K requests (memory management)
    'max_requests_jitter': 500,
    'keepalive': 5,
    'threads': 4,  # 4 threads per worker
    'preload_app': True,  # Load app before forking workers
}

# Scan Engine Configuration
SCAN_CONFIG = {
    'max_parallel_modules': 8,  # Run 8 modules in parallel
    'max_concurrent_scans': 6,  # Support 6 simultaneous scans
    'thread_pool_size': 16,  # 16 threads for I/O-bound operations
    'process_pool_size': 8,  # 8 processes for CPU-intensive tasks
    'enable_caching': True,
    'cache_ttl': 3600,  # 1 hour cache
}

# Sentinel Scheduler Configuration
SENTINEL_CONFIG = {
    'max_jobs': 100,  # Support up to 100 scheduled monitors
    'parallel_jobs': 8,  # Run 8 monitors concurrently
    'job_timeout': 600,  # 10 min per job
}

# LLM Configuration (16GB RAM - use 13B models)
LLM_CONFIG = {
    'model': 'wizard-vicuna-uncensored:13b',
    'context_size': 8192,
    'threads': 8,
    'parallel_requests': 4,
    'enable_embeddings': True,  # Enable vector embeddings for semantic search
}

# Memory Management
MEMORY_CONFIG = {
    'max_memory_percent': 85,  # Alert if > 85% RAM used
    'enable_gc': True,  # Aggressive garbage collection
    'cache_max_size_mb': 2048,  # 2GB cache maximum
}

# Database/Storage (future: PostgreSQL/Redis)
STORAGE_CONFIG = {
    'scan_history_max': 1000,  # Keep 1000 most recent scans
    'enable_compression': True,
    'compression_level': 6,  # zlib level 6
}
