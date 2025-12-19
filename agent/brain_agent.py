import json
import os
import shlex
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests

# Simple, safe-ish agent helper for Athena.
# - Stores tasks in data/agent_tasks.json
# - Plans via local Ollama HTTP API (agent_orchestrator)
# - Executes only allowlisted commands in a bounded workdir

# Allowed commands (first token only)
ALLOWED_COMMANDS = {
    "ls",
    "pwd",
    "cat",
    "echo",
    "touch",
    "mkdir",
    "rm",
    "cp",
    "mv",
    "python",
    "pip",
    "git"
}

# Workspace where commands may run
WORKDIR = Path(os.getenv("AI_AGENT_WORKDIR", "/opt/agent/workdir")).resolve()
WORKDIR.mkdir(parents=True, exist_ok=True)

# Tasks persistence
TASKS_PATH = Path("data/agent_tasks.json")
TASKS_PATH.parent.mkdir(parents=True, exist_ok=True)

OLLAMA_URL = os.getenv("AGENT_ORCHESTRATOR_URL", "http://127.0.0.1:8081/api/generate")
MODEL_NAME = os.getenv("AGENT_MODEL", "wizard-vicuna-uncensored")


def _load_tasks() -> Dict[str, Any]:
    if TASKS_PATH.exists():
        try:
            return json.loads(TASKS_PATH.read_text())
        except Exception:
            return {}
    return {}


def _save_tasks(data: Dict[str, Any]) -> None:
    TASKS_PATH.write_text(json.dumps(data, indent=2))


def list_tasks() -> Dict[str, Any]:
    return _load_tasks()


def get_task(task_id: str) -> Dict[str, Any]:
    return _load_tasks().get(task_id) or {}


def create_task(prompt: str, mode: str = "manual") -> Dict[str, Any]:
    data = _load_tasks()
    task_id = str(uuid.uuid4())
    task = {
        "id": task_id,
        "prompt": prompt,
        "mode": mode,
        "status": "pending" if mode != "auto" else "queued",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "logs": [],
        "plan": [],
        "result": None,
    }
    data[task_id] = task
    _save_tasks(data)
    return task


def approve_task(task_id: str) -> Dict[str, Any]:
    data = _load_tasks()
    task = data.get(task_id)
    if not task:
        return {"success": False, "error": "task not found"}
    if task.get("status") not in {"pending", "queued"}:
        return {"success": False, "error": "task not pending"}
    task["status"] = "queued"
    data[task_id] = task
    _save_tasks(data)
    return {"success": True, "task": task}


def run_task(task_id: str, auto_run: bool = False) -> Dict[str, Any]:
    data = _load_tasks()
    task = data.get(task_id)
    if not task:
        return {"success": False, "error": "task not found"}
    if not auto_run and task.get("status") not in {"queued", "pending"}:
        return {"success": False, "error": "task not ready"}

    task["status"] = "running"
    task["started_at"] = datetime.utcnow().isoformat() + "Z"
    _append_log(task, "planning", "Requesting plan from model...")
    _save_tasks(data)

    plan_resp = _plan_commands(task.get("prompt", ""))
    if not plan_resp["success"]:
        task["status"] = "failed"
        _append_log(task, "error", plan_resp["error"])
        data[task_id] = task
        _save_tasks(data)
        return {"success": False, "error": plan_resp["error"], "task": task}

    steps = plan_resp.get("steps", [])
    task["plan"] = steps
    _append_log(task, "plan", json.dumps(steps, indent=2))
    _save_tasks(data)

    exec_resp = _execute_steps(steps)
    task["result"] = exec_resp
    task["status"] = "done" if exec_resp["success"] else "failed"
    task["finished_at"] = datetime.utcnow().isoformat() + "Z"
    data[task_id] = task
    _append_log(task, "result", json.dumps(exec_resp, indent=2))
    _save_tasks(data)
    return {"success": True, "task": task}


def _append_log(task: Dict[str, Any], level: str, message: str) -> None:
    logs = task.get("logs", [])
    logs.append({"ts": datetime.utcnow().isoformat() + "Z", "level": level, "message": message})
    task["logs"] = logs


def _plan_commands(prompt: str) -> Dict[str, Any]:
    plan_prompt = f"""
You are an OS-safe planning agent. Task: {prompt}
Output ONLY JSON like: {{"steps":[{{"cmd":"<shell command>","description":"<why>"}}...]}}
Rules:
- Use only these commands: {sorted(ALLOWED_COMMANDS)}
- Work inside {WORKDIR}
- Keep commands short; avoid pipes and redirection
- If no action needed, return empty steps
"""
    try:
        resp = requests.post(OLLAMA_URL, json={"prompt": plan_prompt, "model": MODEL_NAME}, timeout=120)
        resp.raise_for_status()
        text = resp.json().get("output") if resp.headers.get("content-type", "").startswith("application/json") else resp.text
        parsed = _extract_json(text)
        steps = parsed.get("steps") if isinstance(parsed, dict) else []
        if not isinstance(steps, list):
            steps = []
        steps = _sanitize_steps(steps)
        return {"success": True, "steps": steps}
    except Exception as e:
        return {"success": False, "error": f"planning failed: {e}"}


def _extract_json(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        # attempt to find first brace region
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            snippet = text[start : end + 1]
            try:
                return json.loads(snippet)
            except Exception:
                return {}
        return {}


def _sanitize_steps(steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    clean: List[Dict[str, Any]] = []
    for step in steps:
        cmd = str(step.get("cmd", "")).strip()
        if not cmd:
            continue
        parts = shlex.split(cmd)
        if not parts:
            continue
        if parts[0] not in ALLOWED_COMMANDS:
            continue
        clean.append({"cmd": cmd, "description": step.get("description", "")})
    return clean


def _execute_steps(steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    results: List[Dict[str, Any]] = []
    for step in steps:
        cmd = step.get("cmd")
        desc = step.get("description", "")
        out, err, code = _run_command(cmd)
        results.append({"cmd": cmd, "description": desc, "stdout": out, "stderr": err, "code": code})
        if code != 0:
            return {"success": False, "steps": results, "error": f"command failed: {cmd}"}
    return {"success": True, "steps": results}


def _run_command(cmd: str) -> Tuple[str, str, int]:
    parts = shlex.split(cmd)
    try:
        proc = subprocess.run(parts, cwd=str(WORKDIR), capture_output=True, text=True, timeout=60)
        return proc.stdout.strip(), proc.stderr.strip(), proc.returncode
    except subprocess.TimeoutExpired as e:
        return "", f"timeout after {e.timeout}s", 124
    except Exception as e:
        return "", str(e), 1


__all__ = [
    "create_task",
    "approve_task",
    "run_task",
    "list_tasks",
    "get_task",
]
