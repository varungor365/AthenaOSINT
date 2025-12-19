#!/usr/bin/env bash
set -euo pipefail

# Agent Orchestrator Bootstrap for Ubuntu 22.04 (8GB RAM / 4 vCPU)
# - Creates swap (8G), installs deps, sets up Python venv, installs orchestrator,
# - Installs Ollama and pulls a small model (mistral),
# - Configures systemd service for the orchestrator on port 8081.

if [[ $(id -u) -ne 0 ]]; then
  echo "Please run as root: sudo bash $0" >&2
  exit 1
fi

AGENT_DIR="/opt/agent"
APP_DIR="$AGENT_DIR/orchestrator"
VENV_DIR="$AGENT_DIR/venv"
PORT="8081"
MODEL="mistral"

mkdir -p "$AGENT_DIR" "$APP_DIR" "$AGENT_DIR/models" "$AGENT_DIR/logs"

# 1) Optional: Create swap (8G) if none exists
if ! swapon --show | grep -q "^/swapfile"; then
  echo "Creating 8G swapfile..."
  fallocate -l 8G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=8192
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  if ! grep -q "/swapfile" /etc/fstab; then echo '/swapfile none swap sw 0 0' >> /etc/fstab; fi
fi

# 2) System deps
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y \
  git curl ca-certificates build-essential python3-venv python3-pip \
  pkg-config libssl-dev

# 3) Install Ollama (CPU runtime)
if ! command -v ollama >/dev/null 2>&1; then
  echo "Installing Ollama..."
  curl -fsSL https://ollama.com/install.sh | sh
  systemctl enable ollama
  systemctl start ollama
fi

# 4) Pull a default model (can be changed later)
if ! ollama list | grep -q "^$MODEL[[:space:]]"; then
  echo "Pulling model: $MODEL"
  ollama pull "$MODEL"
fi

# 5) Orchestrator app setup
if [[ ! -d "$APP_DIR" ]]; then
  mkdir -p "$APP_DIR"
fi

# Expect the user to place app files or fetch from a repo
# If this script is being run standalone, write a minimal app
cat >/tmp/requirements.txt <<'REQ'
fastapi==0.115.5
uvicorn[standard]==0.32.0
jinja2==3.1.4
pydantic==2.10.4
httpx==0.27.2
REQ

cat >"$APP_DIR/app.py" <<'PY'
import os
import subprocess
from typing import Optional
from fastapi import FastAPI
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="Agent Orchestrator", version="0.1.0")
MODEL_NAME = os.getenv("AGENT_MODEL", "mistral")
HOST = os.getenv("AGENT_HOST", "0.0.0.0")
PORT = int(os.getenv("AGENT_PORT", "8081"))

class GenerateRequest(BaseModel):
    prompt: str
    system: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 512

@app.get("/api/health")
async def health():
    return {"status": "ok", "model": MODEL_NAME}

@app.post("/api/generate")
async def generate(req: GenerateRequest):
    if _has_ollama():
        try:
            text = _ollama_generate(MODEL_NAME, req.prompt, req.system, req.temperature, req.max_tokens)
            return {"success": True, "model": MODEL_NAME, "output": text}
        except Exception as e:
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)
    return JSONResponse({
        "success": False,
        "error": "No local model runtime found. Install Ollama and pull a model (e.g., 'mistral').",
        "hint": "curl -fsSL https://ollama.com/install.sh | sh && ollama pull mistral"
    }, status_code=500)

@app.get("/")
async def index():
    html = f"""
    <!doctype html>
    <html>
    <head>
      <meta charset='utf-8'/>
      <meta name='viewport' content='width=device-width, initial-scale=1'/>
      <title>Agent Orchestrator</title>
      <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; }}
        textarea, input {{ width: 100%; padding: 10px; margin: 8px 0; }}
        button {{ padding: 10px 16px; }}
        pre {{ background:#111; color:#0f0; padding: 10px; min-height: 120px; white-space: pre-wrap; }}
      </style>
    </head>
    <body>
      <h2>Agent Orchestrator</h2>
      <p>Model: <b>{MODEL_NAME}</b></p>
      <textarea id='prompt' rows='6' placeholder='Type your instruction here...'></textarea>
      <button onclick='run()'>Generate</button>
      <pre id='out'></pre>
      <script>
        async function run() {{
          const prompt = document.getElementById('prompt').value;
          const r = await fetch('/api/generate', {{
            method: 'POST', headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ prompt }})
          }});
          const data = await r.json();
          document.getElementById('out').textContent = data.success ? data.output : ('Error: ' + (data.error || 'unknown'));
        }}
      </script>
    </body>
    </html>
    """
    return HTMLResponse(html)


def _has_ollama() -> bool:
    try:
        subprocess.run(["ollama", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except Exception:
        return False


def _ollama_generate(model: str, prompt: str, system: Optional[str], temperature: float, max_tokens: int) -> str:
    import json, tempfile
    req = {"model": model, "prompt": prompt, "options": {"temperature": temperature, "num_predict": max_tokens}}
    if system:
        req["system"] = system
    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        json.dump(req, f)
        f.flush()
        cmd = ["ollama", "run", model, "-J", f.name]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip() or res.stdout.strip())
        return res.stdout.strip()
PY

# 6) Python venv + deps
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r /tmp/requirements.txt

# 7) Systemd service
cat >/etc/systemd/system/agent-orchestrator.service <<SERVICE
[Unit]
Description=Agent Orchestrator (FastAPI)
After=network-online.target ollama.service
Wants=network-online.target

[Service]
Type=simple
Environment=AGENT_MODEL=$MODEL
Environment=AGENT_HOST=0.0.0.0
Environment=AGENT_PORT=$PORT
WorkingDirectory=$APP_DIR
ExecStart=$VENV_DIR/bin/python -m uvicorn app:app --host 0.0.0.0 --port $PORT --workers 1
Restart=always
RestartSec=3
User=root
Group=root

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable agent-orchestrator
systemctl restart agent-orchestrator

# 8) UFW allow (optional)
if command -v ufw >/dev/null 2>&1; then
  ufw allow $PORT/tcp || true
fi

echo "\nBootstrap complete. Access the UI at: http://<SERVER-IP>:$PORT/"
echo "Service: systemctl status agent-orchestrator"
echo "Model: $MODEL (change via AGENT_MODEL env in service if needed)"
