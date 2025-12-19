import os
import subprocess
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Minimal Orchestrator serving a chat UI and a simple text generation API.
# Generation is proxied to Ollama CLI if available; otherwise returns a helpful error.

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
    # Try Ollama first
    if _has_ollama():
        try:
            text = _ollama_generate(MODEL_NAME, req.prompt, req.system, req.temperature, req.max_tokens)
            return {"success": True, "model": MODEL_NAME, "output": text}
        except Exception as e:
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)
    # Otherwise, advise how to install
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
    # Use ollama CLI with JSON mode for simplicity
    import json
    import tempfile
    # Build JSON prompt object
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
