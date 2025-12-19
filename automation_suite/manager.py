import asyncio
from typing import Dict, List, Optional, Callable
from pathlib import Path
import json

from .config import SuiteConfig
from .jobs import Job, STATUS_QUEUED, STATUS_RUNNING, STATUS_COMPLETED, STATUS_FAILED
from .proxies import ProxyManager
from .browser import BrowserAutomation

_manager: Optional["AutomationManager"] = None

class AutomationManager:
    def __init__(self, config: SuiteConfig | None = None):
        self.config = config or SuiteConfig()
        self.jobs: Dict[str, Job] = {}
        self._lock = asyncio.Lock()
        self._browser = BrowserAutomation()
        self._proxy_mgr = ProxyManager([s.__dict__ for s in self.config.proxy_sources])
        Path(self.config.storage_path).mkdir(parents=True, exist_ok=True)
        self.jobs_path = Path(self.config.storage_path) / "jobs.json"
        self._load_jobs()

    # Storage helpers
    def _load_jobs(self):
        if self.jobs_path.exists():
            try:
                data = json.loads(self.jobs_path.read_text(encoding="utf-8"))
                for j in data:
                    job = Job(**j)
                    self.jobs[job.id] = job
            except Exception:
                pass

    def _save_jobs(self):
        try:
            payload = [j.__dict__ for j in self.jobs.values()]
            self.jobs_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception:
            pass

    def list_jobs(self) -> List[Dict]:
        return [j.__dict__ for j in sorted(self.jobs.values(), key=lambda x: x.created_at, reverse=True)]

    def create_job(self, target: str, job_type: str, params: Dict) -> Job:
        # Enforce target policy: only allowed domains unless explicitly enabled
        policy = self.config.target_policy
        if not policy.allow_external:
            allowed = policy.allowed_domains or []
            if not any(target.endswith(d) for d in allowed):
                raise ValueError("Target not authorized. Add domain to allowed_domains.")

        job = Job(target=target, job_type=job_type, params=params)
        self.jobs[job.id] = job
        self._save_jobs()
        return job

    async def run_job(self, job_id: str, on_progress: Optional[Callable[[Dict], None]] = None):
        job = self.jobs.get(job_id)
        if not job:
            raise KeyError("Job not found")

        async with self._lock:
            job.status = STATUS_RUNNING
            job.started_at = __import__("datetime").datetime.utcnow().isoformat()
            job.log("info", f"Starting job: {job.job_type}")
            self._save_jobs()

            try:
                if job.job_type == "browser_scrape":
                    url = job.params.get("url")
                    job.log("info", f"Navigating {url}")
                    result = await self._browser.navigate(url)
                    job.results = result
                    job.log("success", "Scrape complete")
                elif job.job_type == "screenshot":
                    url = job.params.get("url")
                    img = await self._browser.screenshot(url)
                    out = Path(self.config.storage_path) / f"shot_{job.id}.png"
                    out.write_bytes(img)
                    job.results = {"file": str(out)}
                    job.log("success", "Screenshot saved")
                elif job.job_type == "fuzzer":
                    # Safe, authorized fuzzer stub: requires explicit allowlist endpoint
                    endpoint = job.params.get("endpoint")
                    allowed = job.params.get("allowed", False)
                    if not allowed:
                        raise ValueError("Fuzzer requires explicit authorization (allowed=True)")
                    # TODO: implement rate-limited fuzzing against owned endpoint
                    job.log("warning", "Fuzzer executed in dry-run mode")
                    job.results = {"status": "dry-run"}
                elif job.job_type == "proxy_refresh":
                    count = len(self._proxy_mgr.fetch())
                    job.results = {"proxies": count}
                    job.log("success", f"Fetched {count} proxies")
                else:
                    raise ValueError("Unsupported job_type")

                job.status = STATUS_COMPLETED
                job.finished_at = __import__("datetime").datetime.utcnow().isoformat()
                self._save_jobs()
                if on_progress:
                    on_progress({"job_id": job.id, "status": job.status})
            except Exception as e:
                job.log("error", str(e))
                job.status = STATUS_FAILED
                job.finished_at = __import__("datetime").datetime.utcnow().isoformat()
                self._save_jobs()
                if on_progress:
                    on_progress({"job_id": job.id, "status": job.status, "error": str(e)})
                raise

    def proxies(self) -> List[str]:
        return self._proxy_mgr.list()


def get_manager() -> AutomationManager:
    global _manager
    if _manager is None:
        _manager = AutomationManager()
    return _manager
