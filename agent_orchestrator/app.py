import os
import subprocess
import requests
import json
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Minimal Orchestrator serving a chat UI and a simple text generation API.
# Generation is proxied to Ollama CLI if available; otherwise returns a helpful error.

app = FastAPI(title="Agent Orchestrator", version="0.1.0")

# Configuration (Optimized for 16GB RAM)
MODEL_NAME = os.getenv("AGENT_MODEL", "wizard-vicuna-uncensored:13b")  # Larger model
CONTEXT_SIZE = int(os.getenv("AGENT_CONTEXT", "8192"))  # 8K context
NUM_THREADS = int(os.getenv("AGENT_THREADS", "8"))  # Parallel processing
NUM_PARALLEL = int(os.getenv("AGENT_PARALLEL", "4"))  # Concurrent requests
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
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; }}
        textarea, input {{ width: 100%; padding: 10px; margin: 8px 0; box-sizing: border-box; }}
        button {{ padding: 10px 16px; cursor: pointer; }}
        button:disabled {{ opacity: 0.5; cursor: not-allowed; }}
        pre {{ background:#111; color:#0f0; padding: 10px; min-height: 120px; white-space: pre-wrap; }}
        .loading {{ color: #ff0; }}
      </style>
    </head>
    <body>
      <h2>Agent Orchestrator</h2>
      <p>Model: <b>{MODEL_NAME}</b></p>
      <textarea id='prompt' rows='6' placeholder='Type your instruction here...'></textarea>
      <button id='btn' onclick='run()'>Generate</button>
      <pre id='out'></pre>
      <script>
        async function run() {{
          const prompt = document.getElementById('prompt').value;
          const btn = document.getElementById('btn');
          const out = document.getElementById('out');
          
          if (!prompt.trim()) {{
            out.textContent = 'Error: Please enter a prompt';
            return;
          }}
          
          btn.disabled = true;
          out.className = 'loading';
          out.textContent = 'Generating response... (this may take 30-60 seconds for first request)';
          
          try {{
            const r = await fetch('/api/generate', {{
              method: 'POST',
              headers: {{ 'Content-Type': 'application/json' }},
              body: JSON.stringify({{ prompt }})
            }});
            
            if (!r.ok) {{
              const err = await r.text();
              out.textContent = 'Error: ' + err;
              out.className = '';
              btn.disabled = false;
              return;
            }}
            
            const data = await r.json();
            out.className = '';
            out.textContent = data.success ? data.output : ('Error: ' + (data.error || 'unknown'));
          }} catch (e) {{
            out.className = '';
            out.textContent = 'Error: ' + e.message;
          }} finally {{
            btn.disabled = false;
          }}
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
    """Generate text using Ollama HTTP API with 16GB RAM optimizations."""
    url = "http://127.0.0.1:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
            "num_ctx": CONTEXT_SIZE,  # 8K context window
            "num_thread": NUM_THREADS,  # 8 parallel threads
            "num_parallel": NUM_PARALLEL,  # 4 concurrent requests
            "num_gpu": 0,  # CPU-only inference
            "top_p": 0.9,
            "top_k": 40
        }
    }
    if system:
        payload["system"] = system
    
    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        
        # Ollama returns newline-delimited JSON; parse the last complete response
        lines = response.text.strip().split('\n')
        if lines:
            last_response = json.loads(lines[-1])
            return last_response.get('response', '').strip()
        return ""
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Ollama service not running on http://127.0.0.1:11434")
    except requests.exceptions.Timeout:
        raise RuntimeError("Ollama request timed out (model may be loading)")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid response from Ollama: {e}")
    except Exception as e:
        raise RuntimeError(f"Ollama error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
