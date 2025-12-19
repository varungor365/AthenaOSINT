from typing import Dict
import asyncio

from .manager import get_manager

# API layer consumed by Flask routes

def list_jobs():
    mgr = get_manager()
    return {"success": True, "jobs": mgr.list_jobs()}


def create_job(payload: Dict):
    mgr = get_manager()
    target = payload.get("target", "")
    job_type = payload.get("job_type", "browser_scrape")
    params = payload.get("params", {})
    job = mgr.create_job(target=target, job_type=job_type, params=params)
    return {"success": True, "job": job.__dict__}


def run_job(job_id: str, on_progress=None):
    mgr = get_manager()
    # Fire-and-forget background task
    loop = asyncio.get_event_loop()
    loop.create_task(mgr.run_job(job_id, on_progress=on_progress))
    return {"success": True, "job_id": job_id}


def proxies():
    mgr = get_manager()
    return {"success": True, "proxies": mgr.proxies()}
