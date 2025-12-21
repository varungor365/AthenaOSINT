"""
High-Performance Parallel Scan Engine (16GB RAM Optimized).
Concurrent module execution with thread/process pools.
"""
import concurrent.futures
import threading
import multiprocessing as mp
from queue import Queue, Empty
from typing import List, Dict, Callable, Optional
from dataclasses import dataclass
from datetime import datetime
import time
from loguru import logger

from core.engine import Profile
from config.production import SCAN_CONFIG


@dataclass
class ScanTask:
    """Represents a single module scan task."""
    module_name: str
    target: str
    profile: Profile
    priority: int = 0  # Higher = more important
    timeout: int = 300
    

class ParallelScanEngine:
    """
    High-performance parallel scan engine using thread and process pools.
    Optimized for 16GB RAM with concurrent module execution.
    """
    
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or SCAN_CONFIG['max_parallel_modules']
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix='scan_worker'
        )
        self.results = {}
        self.lock = threading.Lock()
        self.active_tasks = 0
        logger.info(f"Parallel Engine initialized with {self.max_workers} workers")
        
    def run_parallel_scan(
        self,
        target: str,
        modules: List[str],
        profile: Profile,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, any]:
        """
        Execute multiple modules in parallel.
        
        Args:
            target: Target identifier
            modules: List of module names to run
            profile: Shared Profile object (thread-safe operations required)
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dict with results and timing info
        """
        start_time = time.time()
        tasks = []
        
        # Create tasks
        for idx, module_name in enumerate(modules):
            task = ScanTask(
                module_name=module_name,
                target=target,
                profile=profile,
                priority=idx,
                timeout=SCAN_CONFIG.get('module_timeout', 300)
            )
            tasks.append(task)
        
        logger.info(f"Submitting {len(tasks)} tasks to parallel executor")
        
        # Submit all tasks
        futures = {}
        for task in tasks:
            future = self.thread_pool.submit(
                self._execute_module_safe,
                task,
                progress_callback
            )
            futures[future] = task
        
        # Wait for completion with timeout
        completed = 0
        failed = 0
        errors = []
        
        for future in concurrent.futures.as_completed(futures, timeout=900):  # 15 min total timeout
            task = futures[future]
            try:
                result = future.result(timeout=task.timeout)
                completed += 1
                
                if progress_callback:
                    progress_callback(task.module_name, 'completed', result)
                    
                logger.success(f"✓ {task.module_name} completed")
                
            except concurrent.futures.TimeoutError:
                failed += 1
                error = f"{task.module_name} timed out"
                errors.append({'module': task.module_name, 'error': 'timeout'})
                logger.error(f"✗ {error}")
                
                if progress_callback:
                    progress_callback(task.module_name, 'timeout', None)
                    
            except Exception as e:
                failed += 1
                errors.append({'module': task.module_name, 'error': str(e)})
                logger.error(f"✗ {task.module_name} failed: {e}")
                
                if progress_callback:
                    progress_callback(task.module_name, 'failed', str(e))
        
        elapsed = time.time() - start_time
        
        return {
            'completed': completed,
            'failed': failed,
            'total': len(tasks),
            'elapsed': elapsed,
            'errors': errors,
            'avg_time_per_module': elapsed / len(tasks) if tasks else 0
        }
    
    def _execute_module_safe(self, task: ScanTask, progress_callback: Optional[Callable]) -> Dict:
        """Thread-safe module execution wrapper."""
        try:
            if progress_callback:
                progress_callback(task.module_name, 'starting', None)
            
            # Dynamic import
            try:
                module = __import__(f'modules.{task.module_name}', fromlist=['scan'])
                scan_func = getattr(module, 'scan')
            except (ImportError, AttributeError) as e:
                raise RuntimeError(f"Module {task.module_name} not found or invalid: {e}")
            
            # Execute with timeout monitoring
            start = time.time()
            
            # Call the module's scan function
            scan_func(task.target, task.profile)
            
            elapsed = time.time() - start
            
            return {
                'module': task.module_name,
                'status': 'success',
                'elapsed': elapsed
            }
            
        except Exception as e:
            logger.exception(f"Module {task.module_name} exception")
            raise
    
    def shutdown(self):
        """Gracefully shutdown the thread pool."""
        logger.info("Shutting down parallel scan engine")
        self.thread_pool.shutdown(wait=True, cancel_futures=False)


class DistributedScanQueue:
    """
    Distributed task queue for managing multiple concurrent scans.
    Supports priority scheduling and load balancing.
    """
    
    def __init__(self, max_concurrent: int = None):
        self.max_concurrent = max_concurrent or SCAN_CONFIG['max_concurrent_scans']
        self.queue = Queue()
        self.active_scans = {}
        self.lock = threading.Lock()
        self.worker_thread = None
        self.running = False
        
    def start(self):
        """Start the background worker thread."""
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            logger.info(f"Distributed scan queue started (max_concurrent={self.max_concurrent})")
    
    def stop(self):
        """Stop the background worker."""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
    
    def enqueue_scan(
        self,
        scan_id: str,
        target: str,
        modules: List[str],
        callback: Optional[Callable] = None,
        priority: int = 0
    ):
        """Add a scan to the queue."""
        self.queue.put({
            'scan_id': scan_id,
            'target': target,
            'modules': modules,
            'callback': callback,
            'priority': priority,
            'enqueued_at': datetime.now().isoformat()
        })
        logger.info(f"Scan {scan_id} enqueued (priority={priority})")
    
    def _worker_loop(self):
        """Background worker that processes the queue."""
        engine = ParallelScanEngine()
        
        while self.running:
            try:
                # Check if we can run more scans
                with self.lock:
                    if len(self.active_scans) >= self.max_concurrent:
                        time.sleep(1)
                        continue
                
                # Get next task (with timeout to allow shutdown)
                try:
                    task = self.queue.get(timeout=1)
                except Empty:
                    continue
                
                # Execute in background thread
                scan_thread = threading.Thread(
                    target=self._execute_scan,
                    args=(engine, task),
                    daemon=True
                )
                
                with self.lock:
                    self.active_scans[task['scan_id']] = {
                        'thread': scan_thread,
                        'task': task,
                        'started_at': datetime.now().isoformat()
                    }
                
                scan_thread.start()
                
            except Exception as e:
                logger.error(f"Queue worker error: {e}")
    
    def _execute_scan(self, engine: ParallelScanEngine, task: Dict):
        """Execute a single scan task."""
        scan_id = task['scan_id']
        try:
            from core.engine import Profile, AthenaEngine
            
            # Create profile
            profile = Profile(target_query=task['target'])
            
            # Run parallel scan
            result = engine.run_parallel_scan(
                target=task['target'],
                modules=task['modules'],
                profile=profile,
                progress_callback=task.get('callback')
            )
            
            # Callback with results
            if task.get('callback'):
                task['callback']('completed', result, profile)
                
        except Exception as e:
            logger.error(f"Scan {scan_id} failed: {e}")
            if task.get('callback'):
                task['callback']('failed', {'error': str(e)}, None)
        finally:
            # Remove from active scans
            with self.lock:
                self.active_scans.pop(scan_id, None)


# Global queue instance
_global_queue = None

def get_scan_queue() -> DistributedScanQueue:
    """Get or create the global scan queue."""
    global _global_queue
    if _global_queue is None:
        _global_queue = DistributedScanQueue()
        _global_queue.start()
    return _global_queue
