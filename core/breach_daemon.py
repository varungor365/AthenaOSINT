#!/usr/bin/env python3
"""
Breach Monitoring Daemon

Runs autonomously in the background, manages CPU/RAM usage,
and coordinates breach discovery and indexing operations.
"""

import asyncio
import threading
import psutil
import time
from pathlib import Path
from datetime import datetime
from typing import Optional
from loguru import logger

from intelligence.breach_monitor import BreachMonitor
from intelligence.breach_indexer import BreachIndexer


class BreachDaemon(threading.Thread):
    """Background daemon for autonomous breach monitoring."""
    
    def __init__(
        self,
        max_cpu_percent: float = 30.0,
        max_memory_mb: int = 512,
        check_interval: int = 1800,  # 30 minutes
        data_dir: Path = None
    ):
        """
        Initialize breach daemon.
        
        Args:
            max_cpu_percent: Maximum CPU usage percentage (0-100)
            max_memory_mb: Maximum memory usage in MB
            check_interval: Seconds between monitoring cycles
            data_dir: Directory for breach data storage
        """
        super().__init__(daemon=True, name="BreachDaemon")
        
        self.max_cpu_percent = max_cpu_percent
        self.max_memory_mb = max_memory_mb
        self.check_interval = check_interval
        self.data_dir = data_dir or Path("data/breach_vault")
        
        self.monitor: Optional[BreachMonitor] = None
        self.indexer: Optional[BreachIndexer] = None
        self.process = psutil.Process()
        
        self.running = False
        self.paused = False
        self.stats = {
            'started': None,
            'cycles_completed': 0,
            'items_discovered': 0,
            'items_indexed': 0,
            'last_run': None,
            'status': 'initializing'
        }
        
        logger.info(f"BreachDaemon initialized (CPU: {max_cpu_percent}%, RAM: {max_memory_mb}MB)")
    
    def get_resource_usage(self) -> dict:
        """Get current resource usage."""
        try:
            return {
                'cpu_percent': self.process.cpu_percent(interval=0.1),
                'memory_mb': self.process.memory_info().rss / 1024 / 1024,
                'threads': self.process.num_threads()
            }
        except Exception as e:
            logger.error(f"Error getting resource usage: {e}")
            return {'cpu_percent': 0, 'memory_mb': 0, 'threads': 0}
    
    def should_run(self) -> bool:
        """Check if daemon should run based on resource constraints."""
        if self.paused:
            return False
        
        usage = self.get_resource_usage()
        
        if usage['cpu_percent'] > self.max_cpu_percent:
            logger.debug(f"CPU usage too high: {usage['cpu_percent']:.1f}%")
            return False
        
        if usage['memory_mb'] > self.max_memory_mb:
            logger.debug(f"Memory usage too high: {usage['memory_mb']:.1f}MB")
            return False
        
        return True
    
    async def process_downloaded_files(self):
        """Index newly downloaded breach files."""
        download_dir = self.data_dir / "downloads"
        if not download_dir.exists():
            return
        
        # Get unprocessed files
        for file_path in download_dir.glob("*.txt"):
            if not self.should_run():
                logger.info("Pausing indexing due to resource constraints")
                await asyncio.sleep(60)
                continue
            
            try:
                logger.info(f"Indexing file: {file_path.name}")
                
                # Index the file
                result = self.indexer.index_file(file_path)
                
                if 'error' not in result:
                    self.stats['items_indexed'] += result.get('indexed', 0)
                    
                    # Move to processed
                    processed_path = self.data_dir / "processed" / file_path.name
                    file_path.rename(processed_path)
                    logger.info(f"Indexed and moved: {file_path.name}")
                else:
                    logger.error(f"Indexing failed: {result['error']}")
                
                # Small delay to prevent overwhelming system
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
    
    async def monitoring_cycle(self):
        """Execute one monitoring and indexing cycle."""
        self.stats['status'] = 'running'
        
        try:
            # Check if we should run
            if not self.should_run():
                logger.info("Skipping cycle due to resource constraints")
                self.stats['status'] = 'resource_limited'
                return
            
            logger.info("=== Starting Breach Monitoring Cycle ===")
            cycle_start = time.time()
            
            # Monitor for new breaches
            items_found = await self.monitor.monitor_cycle()
            self.stats['items_discovered'] += items_found
            
            # Process downloaded files
            await self.process_downloaded_files()
            
            # Optimize database periodically
            if self.stats['cycles_completed'] % 10 == 0:
                logger.info("Optimizing database...")
                self.indexer.optimize_database()
            
            # Update stats
            self.stats['cycles_completed'] += 1
            self.stats['last_run'] = datetime.utcnow().isoformat()
            
            cycle_duration = time.time() - cycle_start
            logger.info(f"=== Cycle Complete ({cycle_duration:.1f}s) ===")
            
            self.stats['status'] = 'idle'
            
        except Exception as e:
            logger.error(f"Monitoring cycle error: {e}")
            self.stats['status'] = 'error'
    
    def run(self):
        """Main daemon loop."""
        logger.info("BreachDaemon starting...")
        self.running = True
        self.stats['started'] = datetime.utcnow().isoformat()
        self.stats['status'] = 'starting'
        
        # Initialize components
        try:
            self.monitor = BreachMonitor(data_dir=self.data_dir)
            self.indexer = BreachIndexer(
                db_path=self.data_dir / "breach_index.db"
            )
            logger.info("BreachDaemon components initialized")
        except Exception as e:
            logger.error(f"Failed to initialize daemon: {e}")
            self.stats['status'] = 'failed'
            return
        
        # Create event loop for async operations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        self.stats['status'] = 'idle'
        
        try:
            while self.running:
                try:
                    # Run monitoring cycle
                    loop.run_until_complete(self.monitoring_cycle())
                    
                    # Sleep until next cycle
                    logger.info(f"Sleeping for {self.check_interval}s...")
                    time.sleep(self.check_interval)
                    
                except Exception as e:
                    logger.error(f"Daemon cycle error: {e}")
                    time.sleep(60)  # Wait a minute before retrying
        
        finally:
            # Cleanup
            if self.monitor:
                loop.run_until_complete(self.monitor._close_browser())
            loop.close()
            logger.info("BreachDaemon stopped")
            self.stats['status'] = 'stopped'
    
    def pause(self):
        """Pause daemon operations."""
        logger.info("Pausing BreachDaemon")
        self.paused = True
        self.stats['status'] = 'paused'
    
    def resume(self):
        """Resume daemon operations."""
        logger.info("Resuming BreachDaemon")
        self.paused = False
        self.stats['status'] = 'idle'
    
    def stop(self):
        """Stop daemon."""
        logger.info("Stopping BreachDaemon")
        self.running = False
        self.stats['status'] = 'stopping'
    
    def get_stats(self) -> dict:
        """Get daemon statistics."""
        stats = self.stats.copy()
        stats['resource_usage'] = self.get_resource_usage()
        
        # Add indexer stats if available
        if self.indexer:
            try:
                stats['breach_stats'] = self.indexer.get_breach_stats()
            except Exception as e:
                logger.error(f"Error getting breach stats: {e}")
        
        return stats


# Global daemon instance
_daemon_instance: Optional[BreachDaemon] = None


def get_daemon() -> Optional[BreachDaemon]:
    """Get the global daemon instance."""
    return _daemon_instance


def start_daemon(**kwargs) -> BreachDaemon:
    """Start the global breach daemon."""
    global _daemon_instance
    
    if _daemon_instance and _daemon_instance.is_alive():
        logger.warning("BreachDaemon already running")
        return _daemon_instance
    
    _daemon_instance = BreachDaemon(**kwargs)
    _daemon_instance.start()
    
    logger.info("BreachDaemon started successfully")
    return _daemon_instance


def stop_daemon():
    """Stop the global breach daemon."""
    global _daemon_instance
    
    if _daemon_instance:
        _daemon_instance.stop()
        _daemon_instance = None
        logger.info("BreachDaemon stopped")


if __name__ == '__main__':
    # Test daemon
    daemon = start_daemon(check_interval=300)
    
    try:
        while True:
            time.sleep(10)
            stats = daemon.get_stats()
            print(f"\nDaemon Status: {stats['status']}")
            print(f"Cycles: {stats['cycles_completed']}")
            print(f"Discovered: {stats['items_discovered']}")
            print(f"Indexed: {stats['items_indexed']}")
            print(f"CPU: {stats['resource_usage']['cpu_percent']:.1f}%")
            print(f"RAM: {stats['resource_usage']['memory_mb']:.1f}MB")
    except KeyboardInterrupt:
        stop_daemon()
