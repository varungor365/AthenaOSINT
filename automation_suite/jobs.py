from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
import uuid

STATUS_QUEUED = "queued"
STATUS_RUNNING = "running"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"

@dataclass
class Job:
    target: str
    job_type: str  # e.g., 'browser_scrape', 'fuzzer'
    params: Dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    status: str = STATUS_QUEUED
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    logs: List[Dict] = field(default_factory=list)
    results: Dict = field(default_factory=dict)

    def log(self, level: str, message: str):
        self.logs.append({
            "time": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
        })
