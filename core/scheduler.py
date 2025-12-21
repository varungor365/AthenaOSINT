"""
Sentinel Scheduler.
Manages periodic background monitoring tasks using APScheduler.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger
from datetime import datetime
import json
from pathlib import Path

# Job store (persisted in database or file in future, memory for now)
# We will just schedule jobs based on a config file or database.

class SentinelScheduler:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SentinelScheduler, cls).__new__(cls)
            cls._instance.scheduler = BackgroundScheduler()
            cls._instance.scheduler.start()
            logger.info("Sentinel Scheduler started.")
        return cls._instance

    def add_monitor_job(self, target: str, module: str, interval_hours: int = 6):
        """
        Add a recurrent monitoring job.
        
        Args:
            target: The query/domain to monitor
            module: The module to run (e.g., 'headless_monitor', 'subfinder')
            interval_hours: Frequency
        """
        job_id = f"{module}_{target}"
        
        # Check if exists
        if self.scheduler.get_job(job_id):
            logger.info(f"Job {job_id} already exists. Updating interval.")
            self.scheduler.reschedule_job(job_id, trigger=IntervalTrigger(hours=interval_hours))
            return job_id
            
        self.scheduler.add_job(
            func=self._execute_monitor_task,
            trigger=IntervalTrigger(hours=interval_hours),
            args=[target, module],
            id=job_id,
            name=f"Monitor: {target} ({module})",
            replace_existing=True
        )
        logger.info(f"Added monitoring job: {job_id} every {interval_hours}h")
        return job_id

    def list_jobs(self):
        """List all active jobs."""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': str(job.next_run_time),
                'interval': str(job.trigger)
            })
        return jobs

    def remove_job(self, job_id: str):
        """Remove a job."""
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed job: {job_id}")
            return True
        return False

    def _execute_monitor_task(self, target: str, module_name: str):
        """
        The actual function run by the scheduler.
        Triggers a specialized Engine scan or Module run.
        """
        logger.info(f"SENTINEL: starting check on {target} with {module_name}")
        
        try:
            # We instantiate a fresh Engine for this specific task
            from core.engine import AthenaEngine
            
            # Sentinel runs should be quiet but log heavily
            engine = AthenaEngine(target, quiet=True)
            
            # Execute specific module
            engine.run_scan([module_name])
            
            # Compare results? 
            # The specific modules (like 'headless_monitor') will handle saving diffs.
            # But the Engine is responsible for the overall 'Scan Profile'.
            # Ideally, we save this check as a mini-scan.
            
            # engine.generate_report('json', custom_filename=f"sentinel_{module_name}_{target}_{int(datetime.now().timestamp())}")
            
            logger.success(f"SENTINEL: check complete for {target}")
            
        except Exception as e:
            logger.error(f"SENTINEL FAILED: {target} - {e}")

# Global instance accessor
def get_scheduler():
    return SentinelScheduler()
