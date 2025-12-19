#!/usr/bin/env python3
"""
Breach Monitoring Daemon - Multiprocessing Edition

Uses separate process instead of threading to completely avoid
asyncio/eventlet conflicts with the main Flask application.
"""

import multiprocessing as mp
import asyncio
import psutil
import time
import signal
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict
from loguru import logger
import sys


class BreachDaemonProcess(mp.Process):
    """Separate process for breach monitoring - no eventloop conflicts."""
    
    def __init__(
        self,
        max_cpu_percent: float = 30.0,
        max_memory_mb: int = 512,
        check_interval: int = 1800,
        data_dir: Path = None,
        stats_queue: mp.Queue = None,
        command_queue: mp.Queue = None
    ):
        """
        Initialize breach daemon process.
        
        Args:
            max_cpu_percent: Maximum CPU usage percentage
            max_memory_mb: Maximum memory usage in MB
            check_interval: Seconds between monitoring cycles
            data_dir: Directory for breach data storage
            stats_queue: Queue for sending stats to parent
            command_queue: Queue for receiving commands from parent
        """
        super().__init__(daemon=True, name="BreachDaemonProcess")
        
        self.max_cpu_percent = max_cpu_percent
        self.max_memory_mb = max_memory_mb
        self.check_interval = check_interval
        self.data_dir = data_dir or Path("data/breach_vault")
        self.stats_queue = stats_queue
        self.command_queue = command_queue
        
        self.running = False
        self.paused = False
        
    def get_resource_usage(self) -> dict:
        """Get current resource usage."""
        try:
            process = psutil.Process()
            return {
                'cpu_percent': process.cpu_percent(interval=0.1),
                'memory_mb': process.memory_info().rss / 1024 / 1024,
                'threads': process.num_threads()
            }
        except Exception:
            return {'cpu_percent': 0, 'memory_mb': 0, 'threads': 0}
    
    def should_run(self) -> bool:
        """Check if daemon should run based on resource constraints."""
        if self.paused:
            return False
        
        usage = self.get_resource_usage()
        
        if usage['cpu_percent'] > self.max_cpu_percent:
            return False
        
        if usage['memory_mb'] > self.max_memory_mb:
            return False
        
        return True
    
    async def process_downloaded_files(self, indexer):
        """Index newly downloaded breach files."""
        download_dir = self.data_dir / "downloads"
        if not download_dir.exists():
            return 0
        
        indexed_count = 0
        
        for file_path in download_dir.glob("*.txt"):
            if not self.should_run():
                logger.info("Pausing indexing due to resource constraints")
                await asyncio.sleep(60)
                continue
            
            try:
                logger.info(f"Indexing file: {file_path.name}")
                
                result = indexer.index_file(file_path)
                
                if 'error' not in result:
                    indexed_count += result.get('indexed', 0)
                    
                    # Move to processed
                    processed_path = self.data_dir / "processed" / file_path.name
                    file_path.rename(processed_path)
                    logger.info(f"Indexed and moved: {file_path.name}")
                else:
                    logger.error(f"Indexing failed: {result['error']}")
                
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
        
        return indexed_count
    
    async def monitoring_cycle(self, monitor, indexer, stats):
        """Execute one monitoring and indexing cycle."""
        if not self.should_run():
            logger.info("Skipping cycle due to resource constraints")
            stats['status'] = 'resource_limited'
            self._send_stats(stats)
            return
        
        logger.info("=== Starting Breach Monitoring Cycle ===")
        stats['status'] = 'running'
        self._send_stats(stats)
        
        cycle_start = time.time()
        
        try:
            # Monitor for new breaches
            items_found = await monitor.monitor_cycle()
            stats['items_discovered'] += items_found
            
            # Process downloaded files
            items_indexed = await self.process_downloaded_files(indexer)
            stats['items_indexed'] += items_indexed
            
            # Optimize database periodically
            if stats['cycles_completed'] % 10 == 0:
                logger.info("Optimizing database...")
                indexer.optimize_database()
            
            # Update stats
            stats['cycles_completed'] += 1
            stats['last_run'] = datetime.utcnow().isoformat()
            
            cycle_duration = time.time() - cycle_start
            logger.info(f"=== Cycle Complete ({cycle_duration:.1f}s) ===")
            
            stats['status'] = 'idle'
            
        except Exception as e:
            logger.error(f"Monitoring cycle error: {e}", exc_info=True)
            stats['status'] = 'error'
            stats['last_error'] = str(e)
        
        finally:
            self._send_stats(stats)
    
    def _send_stats(self, stats):
        """Send stats to parent process."""
        if self.stats_queue:
            try:
                # Non-blocking put
                if self.stats_queue.full():
                    self.stats_queue.get_nowait()
                self.stats_queue.put_nowait(stats.copy())
            except Exception:
                pass
    
    def _check_commands(self):
        """Check for commands from parent process."""
        if not self.command_queue:
            return
        
        try:
            while not self.command_queue.empty():
                command = self.command_queue.get_nowait()
                
                if command == 'pause':
                    self.paused = True
                    logger.info("Daemon paused by command")
                elif command == 'resume':
                    self.paused = False
                    logger.info("Daemon resumed by command")
                elif command == 'stop':
                    self.running = False
                    logger.info("Daemon stopping by command")
                    
        except Exception as e:
            logger.error(f"Error checking commands: {e}")
    
    def run(self):
        """Main daemon loop - runs in separate process."""
        # This runs in a SEPARATE process, so no eventlet conflicts!
        logger.info("BreachDaemon process starting...")
        
        self.running = True
        
        stats = {
            'started': datetime.utcnow().isoformat(),
            'cycles_completed': 0,
            'items_discovered': 0,
            'items_indexed': 0,
            'last_run': None,
            'status': 'starting',
            'last_error': None
        }
        
        # Initialize components in this process
        try:
            from intelligence.breach_monitor import BreachMonitor
            from intelligence.breach_indexer import BreachIndexer
            
            monitor = BreachMonitor(data_dir=self.data_dir)
            indexer = BreachIndexer(db_path=self.data_dir / "breach_index.db")
            
            logger.info("BreachDaemon components initialized")
            stats['status'] = 'idle'
            self._send_stats(stats)
            
        except Exception as e:
            logger.error(f"Failed to initialize daemon: {e}", exc_info=True)
            stats['status'] = 'failed'
            stats['last_error'] = str(e)
            self._send_stats(stats)
            return
        
        # Main loop
        try:
            while self.running:
                # Check for commands
                self._check_commands()
                
                if not self.paused:
                    # Run async monitoring cycle
                    try:
                        asyncio.run(self.monitoring_cycle(monitor, indexer, stats))
                    except Exception as e:
                        logger.error(f"Cycle error: {e}", exc_info=True)
                        stats['last_error'] = str(e)
                        stats['status'] = 'error'
                        self._send_stats(stats)
                
                # Sleep until next cycle
                logger.info(f"Sleeping for {self.check_interval}s...")
                for _ in range(self.check_interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            logger.info("BreachDaemon interrupted")
        finally:
            # Cleanup
            try:
                if monitor and monitor.browser:
                    asyncio.run(monitor._close_browser())
            except Exception:
                pass
            
            stats['status'] = 'stopped'
            self._send_stats(stats)
            logger.info("BreachDaemon process stopped")


class BreachDaemonManager:
    """Manager for controlling the breach daemon process."""
    
    def __init__(self):
        self.process: Optional[BreachDaemonProcess] = None
        self.stats_queue = mp.Queue(maxsize=1)
        self.command_queue = mp.Queue()
        self.last_stats = {
            'status': 'not_started',
            'cycles_completed': 0,
            'items_discovered': 0,
            'items_indexed': 0
        }
        
    def start(self, **kwargs):
        """Start the daemon process."""
        if self.process and self.process.is_alive():
            logger.warning("BreachDaemon already running")
            return False
        
        logger.info("Starting BreachDaemon process...")
        
        self.process = BreachDaemonProcess(
            stats_queue=self.stats_queue,
            command_queue=self.command_queue,
            **kwargs
        )
        self.process.start()
        
        logger.info(f"BreachDaemon process started (PID: {self.process.pid})")
        return True
    
    def stop(self):
        """Stop the daemon process."""
        if not self.process or not self.process.is_alive():
            logger.warning("BreachDaemon not running")
            return False
        
        logger.info("Stopping BreachDaemon process...")
        
        # Send stop command
        self.command_queue.put('stop')
        
        # Wait for graceful shutdown
        self.process.join(timeout=10)
        
        # Force terminate if still alive
        if self.process.is_alive():
            logger.warning("Force terminating daemon process")
            self.process.terminate()
            self.process.join(timeout=5)
        
        if self.process.is_alive():
            logger.error("Failed to stop daemon, killing...")
            self.process.kill()
        
        self.process = None
        logger.info("BreachDaemon stopped")
        return True
    
    def pause(self):
        """Pause daemon operations."""
        if not self.is_running():
            return False
        self.command_queue.put('pause')
        logger.info("Pause command sent to daemon")
        return True
    
    def resume(self):
        """Resume daemon operations."""
        if not self.is_running():
            return False
        self.command_queue.put('resume')
        logger.info("Resume command sent to daemon")
        return True
    
    def is_running(self) -> bool:
        """Check if daemon is running."""
        return self.process is not None and self.process.is_alive()
    
    def get_stats(self) -> dict:
        """Get current daemon statistics."""
        # Update with latest stats from queue
        try:
            while not self.stats_queue.empty():
                self.last_stats = self.stats_queue.get_nowait()
        except Exception:
            pass
        
        # Add process info
        stats = self.last_stats.copy()
        stats['is_running'] = self.is_running()
        
        if self.process and self.is_running():
            try:
                process = psutil.Process(self.process.pid)
                stats['resource_usage'] = {
                    'cpu_percent': process.cpu_percent(interval=0.1),
                    'memory_mb': process.memory_info().rss / 1024 / 1024,
                    'threads': process.num_threads()
                }
            except Exception:
                pass
        
        return stats


# Global daemon manager
_daemon_manager: Optional[BreachDaemonManager] = None


def get_daemon_manager() -> BreachDaemonManager:
    """Get the global daemon manager instance."""
    global _daemon_manager
    if _daemon_manager is None:
        _daemon_manager = BreachDaemonManager()
    return _daemon_manager


if __name__ == '__main__':
    # Test daemon
    mp.set_start_method('spawn', force=True)
    
    manager = get_daemon_manager()
    manager.start(check_interval=300)
    
    try:
        while True:
            time.sleep(10)
            stats = manager.get_stats()
            print(f"\nDaemon Running: {stats['is_running']}")
            print(f"Status: {stats.get('status', 'unknown')}")
            print(f"Cycles: {stats.get('cycles_completed', 0)}")
            print(f"Discovered: {stats.get('items_discovered', 0)}")
            print(f"Indexed: {stats.get('items_indexed', 0)}")
            
            if 'resource_usage' in stats:
                usage = stats['resource_usage']
                print(f"CPU: {usage['cpu_percent']:.1f}%")
                print(f"RAM: {usage['memory_mb']:.1f}MB")
    except KeyboardInterrupt:
        manager.stop()
