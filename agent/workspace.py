import os
import json
from pathlib import Path
from typing import Dict, Any, List
import requests

WORKSPACE_ROOT = Path(os.getenv("AI_WORKSPACE_ROOT", "/opt/agent/workdir")).resolve()
WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
MODEL_NAME = os.getenv("AGENT_MODEL", "dolphin-llama3:8b-256k-v2.9-q5_K_M")
OLLAMA_URL = os.getenv("AGENT_ORCHESTRATOR_URL", "http://127.0.0.1:8081/api/generate")

ALLOWED_COMMANDS = {"ls", "pwd", "cat", "echo", "touch", "mkdir", "rm", "cp", "mv", "python", "pip", "git"}


def _safe_path(rel_path: str) -> Path:
    target = (WORKSPACE_ROOT / rel_path).resolve()
    if not str(target).startswith(str(WORKSPACE_ROOT)):
        raise ValueError("path outside workspace")
    return target


def list_files(rel_path: str = "") -> Dict[str, Any]:
    base = _safe_path(rel_path)
    if not base.exists():
        return {"success": False, "error": "path not found"}
    items = []
    for entry in sorted(base.iterdir()):
        items.append({
            "name": entry.name,
            "is_dir": entry.is_dir(),
            "size": entry.stat().st_size,
        })
    return {"success": True, "path": str(base.relative_to(WORKSPACE_ROOT)), "items": items}


def read_file(rel_path: str) -> Dict[str, Any]:
    path = _safe_path(rel_path)
    if not path.exists() or not path.is_file():
        return {"success": False, "error": "file not found"}
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        return {"success": False, "error": str(e)}
    return {"success": True, "path": rel_path, "content": content}


def propose_edit(rel_path: str, instruction: str) -> Dict[str, Any]:
    file_info = read_file(rel_path)
    if not file_info.get("success"):
        return file_info
    content = file_info["content"]
    prompt = f"""
You are a code editor. Modify the file per instruction and return ONLY the full new file content (no markdown, no explanations).
Instruction:
{instruction}
---
Current file ({rel_path}):
{content}
---
Return just the revised file text.
"""
    try:
        resp = requests.post(OLLAMA_URL, json={"prompt": prompt, "model": MODEL_NAME}, timeout=180)
        resp.raise_for_status()
        data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {"output": resp.text}
        new_content = data.get("output", "")
        return {"success": True, "path": rel_path, "proposed": new_content}
    except Exception as e:
        return {"success": False, "error": str(e)}


def apply_edit(rel_path: str, new_content: str) -> Dict[str, Any]:
    path = _safe_path(rel_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(new_content, encoding="utf-8")
        return {"success": True, "path": rel_path}
    except Exception as e:
        return {"success": False, "error": str(e)}


def run_command(cmd: str) -> Dict[str, Any]:
    import shlex
    import subprocess
    parts = shlex.split(cmd)
    if not parts or parts[0] not in ALLOWED_COMMANDS:
        return {"success": False, "error": "command not allowed"}
    try:
        proc = subprocess.run(parts, cwd=str(WORKSPACE_ROOT), capture_output=True, text=True, timeout=120)
        return {
            "success": proc.returncode == 0,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "code": proc.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}

__all__ = [
    "list_files",
    "read_file",
    "propose_edit",
    "apply_edit",
    "run_command",
]
