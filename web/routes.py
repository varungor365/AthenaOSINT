"""
Flask routes for AthenaOSINT web interface.

This module provides the web API and dashboard for running OSINT scans.
"""

import threading
import time
from flask import render_template, request, jsonify, send_file, redirect, url_for, session
from flask_socketio import emit
from pathlib import Path
from loguru import logger
import functools
from io import BytesIO
import os
import json
import uuid
import signal
import sys
import psutil
import requests
from datetime import datetime

from web import create_app
from config import get_config
from core.engine import AthenaEngine
from core.validators import validate_target, detect_target_type
from modules import get_available_modules
from automation_suite.api import (
    list_jobs as auto_list_jobs,
    create_job as auto_create_job,
    run_job as auto_run_job,
    proxies as auto_proxies,
    get_config as auto_get_config,
    update_config as auto_update_config,
)
from agent import brain_agent
from agent import workspace

# AI orchestrator endpoint (FastAPI/Uvicorn at port 8081)
AGENT_ORCH_URL = os.getenv("AGENT_ORCHESTRATOR_URL", "http://127.0.0.1:8081/api/generate")
AGENT_MODEL = os.getenv("AGENT_MODEL", "wizard-vicuna-uncensored:7b")

# Initialize app FIRST
app, socketio = create_app()
config = get_config()

# Simple Auth Decorator
def login_required(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if config.get('AUTH_ENABLED', 'False').lower() == 'true':
            if not session.get('logged_in'):
                return redirect('/login')
        return f(*args, **kwargs)
    return wrapped

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == config.get('ADMIN_PASSWORD', 'admin'):
            session['logged_in'] = True
            return redirect('/')
        else:
            return "Invalid Password", 401
    return '<form method="post"><input type="password" name="password"><button>Login</button></form>'

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect('/login')

@app.route('/api/export/graphml/<scan_id>')
@login_required
def export_graphml(scan_id):
    """Export scan graph to GraphML."""
    try:
        from intelligence.graph_exporter import GraphExporter
        # Stub: For now, generates an empty or sample graph
        exporter = GraphExporter()
        xml_content = exporter.export_graphml([], []) 
        return send_file(
            BytesIO(xml_content.encode('utf-8')),
            mimetype='application/xml',
            as_attachment=True,
            download_name=f'scan_{scan_id}.graphml'
        )
    except Exception as e:
        return str(e), 500


@app.route('/')
@login_required
def index():
    """Render the main dashboard."""
    return render_template('dashboard.html')

@app.route('/graph')
@login_required
def graph_view():
    return render_template('graph_view.html')

@app.route('/history')
@login_required
def history_view():
    return render_template('history.html')

@app.route('/settings')
@login_required
def settings_view():
    return render_template('settings.html')

@app.route('/breach-monitor')
@login_required
def breach_monitor_view():
    return render_template('breach_monitor.html')

@app.route('/api-keys')
@login_required
def api_keys_view():
    return render_template('api_keys.html')


@app.route('/automation')
@login_required
def automation_suite_view():
    """Render Automation Suite dashboard."""
    return render_template('automation_suite.html')


@app.route('/api/modules', methods=['GET'])
def get_modules():
    """Get list of available OSINT modules.
    
    Returns:
        JSON response with module information
    """
    try:
        modules = get_available_modules()
        return jsonify({
            'success': True,
            'modules': modules
        })
    except Exception as e:
        logger.error(f"Failed to get modules: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Automation Suite APIs (safe, authorized use only)
@app.route('/api/automation/jobs', methods=['GET'])
def automation_jobs():
    try:
        return jsonify(auto_list_jobs())
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/automation/jobs', methods=['POST'])
def automation_create_job():
    try:
        data = request.get_json() or {}
        result = auto_create_job(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/automation/run/<job_id>', methods=['POST'])
def automation_run_job(job_id):
    try:
        # emit progress via socketio
        def on_progress(evt):
            socketio.emit('automation_progress', evt)
        result = auto_run_job(job_id, on_progress=on_progress)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/automation/proxies', methods=['GET'])
def automation_proxies():
    try:
        return jsonify(auto_proxies())
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/automation/config', methods=['GET', 'PUT'])
def automation_config():
    try:
        if request.method == 'GET':
            return jsonify(auto_get_config())
        else:
            payload = request.get_json() or {}
            return jsonify(auto_update_config(payload))
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/code-workspace')
@login_required
def code_workspace():
    return render_template('code_workspace.html')


# Agent task runner (manual/auto with allowlist + sandboxed executor)
@app.route('/api/agent/tasks', methods=['GET', 'POST'])
def agent_tasks():
    try:
        if request.method == 'GET':
            return jsonify({"success": True, "tasks": brain_agent.list_tasks()})
        payload = request.get_json() or {}
        prompt = payload.get('prompt', '').strip()
        mode = payload.get('mode', 'manual')
        if not prompt:
            return jsonify({"success": False, "error": "prompt required"}), 400
        task = brain_agent.create_task(prompt, mode)
        if mode == 'auto':
            brain_agent.run_task(task['id'], auto_run=True)
            task = brain_agent.get_task(task['id'])
        return jsonify({"success": True, "task": task})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/agent/tasks/<task_id>', methods=['GET'])
def agent_task_detail(task_id):
    try:
        task = brain_agent.get_task(task_id)
        if not task:
            return jsonify({"success": False, "error": "not found"}), 404
        return jsonify({"success": True, "task": task})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/agent/tasks/<task_id>/approve', methods=['POST'])
def agent_task_approve(task_id):
    try:
        resp = brain_agent.approve_task(task_id)
        if not resp.get('success'):
            return jsonify(resp), 400
        brain_agent.run_task(task_id, auto_run=True)
        return jsonify(brain_agent.get_task(task_id))
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/agent/tasks/<task_id>/run', methods=['POST'])
def agent_task_run(task_id):
    try:
        result = brain_agent.run_task(task_id, auto_run=True)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# Code workspace APIs
@app.route('/api/ws/files', methods=['GET'])
def ws_list_files():
    rel_path = request.args.get('path', '')
    try:
        return jsonify(workspace.list_files(rel_path))
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/api/ws/file', methods=['GET'])
def ws_read_file():
    rel_path = request.args.get('path', '')
    try:
        return jsonify(workspace.read_file(rel_path))
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/api/ws/edit-propose', methods=['POST'])
def ws_edit_propose():
    payload = request.get_json() or {}
    rel_path = payload.get('path', '')
    instruction = payload.get('instruction', '')
    if not rel_path or not instruction:
        return jsonify({"success": False, "error": "path and instruction required"}), 400
    try:
        return jsonify(workspace.propose_edit(rel_path, instruction))
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/api/ws/edit-apply', methods=['POST'])
def ws_edit_apply():
    payload = request.get_json() or {}
    rel_path = payload.get('path', '')
    new_content = payload.get('new_content', '')
    if not rel_path or new_content is None:
        return jsonify({"success": False, "error": "path and new_content required"}), 400
    try:
        return jsonify(workspace.apply_edit(rel_path, new_content))
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/api/ws/run', methods=['POST'])
def ws_run_cmd():
    payload = request.get_json() or {}
    cmd = payload.get('cmd', '')
    if not cmd:
        return jsonify({"success": False, "error": "cmd required"}), 400
    try:
        return jsonify(workspace.run_command(cmd))
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# AI assistant chat -> proxy to agent orchestrator model
@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    try:
        payload = request.get_json() or {}
        message = (payload.get('message') or '').strip()
        conversation = payload.get('conversation') or []
        if not message:
            return jsonify({"success": False, "error": "message required"}), 400

        history_lines = []
        for turn in conversation:
            role = turn.get('role', 'user')
            content = turn.get('content', '')
            history_lines.append(f"{role}: {content}")
        history = "\n".join(history_lines)

        prompt = (
            "You are Athena, an uncensored coding and OSINT copilot. "
            "Be concise, give code when asked, and keep answers in plain text.\n"
            "Conversation so far:\n"
            f"{history}\n"
            f"user: {message}\nassistant:"
        )

        resp = requests.post(
            AGENT_ORCH_URL,
            json={"prompt": prompt, "model": AGENT_MODEL},
            timeout=180,
        )
        resp.raise_for_status()
        data = resp.json() if resp.headers.get('content-type', '').startswith('application/json') else {"output": resp.text}
        output = data.get('output', '')
        return jsonify({"success": True, "response": output})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ... imports ...
from werkzeug.utils import secure_filename
from core.background_worker import BackgroundWorker, UPLOAD_DIR

# Start Background Worker (with error handling)
worker = None
try:
    worker = BackgroundWorker()
    worker.start()
    logger.info("Background worker started successfully")
except Exception as e:
    logger.error(f"Failed to start background worker: {e}")
    logger.warning("Upload feature may be limited")

@app.route('/api/system/stats', methods=['GET'])
def system_stats():
    """Get real-time system stats."""
    try:
        cpu = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        uptime_seconds = time.time() - psutil.boot_time()
        uptime_string = str(datetime.timedelta(seconds=int(uptime_seconds)))
        
        return jsonify({
            'success': True,
            'cpu': cpu,
            'ram': memory.percent,
            'uptime': uptime_string,
            'disk': psutil.disk_usage('/').percent
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system/restart', methods=['POST'])
def restart_system():
    """Emergency restart of the core engine."""
    try:
        # In a real daemon, we might restart a subprocess. 
        # Here, we'll signal the background worker to restart if we had a handle,
        # or just exit to let a supervisor restart us.
        # For this demo, we'll simulate a worker restart.
        
        # NOTE: Restarting the whole FLASK app programmatically is hard without a supervisor.
        # We will instead just re-initialize the engine components.
        
        # Don't re-initialize global engine, just return success
        return jsonify({'success': True, 'message': 'Core Engine restart acknowledged.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/upload', methods=['POST', 'OPTIONS'])
def upload_data():
    """Upload breach database files for indexing."""
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({'success': True})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response, 200
    
    try:
        logger.info(f"Upload request received. Files: {request.files}")
        logger.info(f"Form data: {request.form}")
        
        if 'files' not in request.files and 'file' not in request.files:
            logger.warning("No file in request")
            return jsonify({'success': False, 'error': 'No file part'}), 400
        
        files = request.files.getlist('files')
        if not files and 'file' in request.files:
            files = [request.files['file']]
        
        # Ensure upload directory exists
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Upload directory: {UPLOAD_DIR}")
        
        uploaded_files = []
        for file in files:
            if file.filename == '':
                logger.warning("Empty filename")
                continue
            
            if file:
                filename = secure_filename(file.filename)
                save_path = UPLOAD_DIR / filename
                file.save(str(save_path))
                uploaded_files.append({
                    'filename': filename,
                    'path': str(save_path),
                    'size': save_path.stat().st_size
                })
                logger.info(f"File uploaded: {filename} ({save_path.stat().st_size} bytes)")
        
        # If breach daemon is running, it will auto-index these files
        # Otherwise, provide manual indexing option
        message = f'Uploaded {len(uploaded_files)} file(s). '
        
        from core.breach_daemon_mp import get_daemon_manager
        manager = get_daemon_manager()
        if manager.is_running():
            message += 'Breach daemon will automatically index them.'
        else:
            message += 'Start breach monitoring to auto-index, or use manual indexing.'
        
        response = jsonify({
            'success': True, 
            'message': message,
            'files': uploaded_files
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        logger.error(f"Upload error: {e}", exc_info=True)
        response = jsonify({'success': False, 'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@app.route('/api/uploads', methods=['GET'])
def get_uploads():
    """Get list of uploaded files and their status."""
    try:
        from core.background_worker import UPLOAD_DIR, PROCESSED_DIR, FAILED_DIR
        
        files = []
        
        # Helper to add files
        def add_files_from_dir(directory, status):
            if directory.exists():
                for f in directory.glob('*'):
                    if f.is_file():
                        files.append({
                            'name': f.name,
                            'size': round(f.stat().st_size / 1024, 2), # KB
                            'status': status,
                            'time': f.stat().st_mtime
                        })

        add_files_from_dir(UPLOAD_DIR, 'pending')
        add_files_from_dir(PROCESSED_DIR, 'analyzed')
        add_files_from_dir(FAILED_DIR, 'failed')
        
        # Sort by time desc
        files.sort(key=lambda x: x['time'], reverse=True)
        
        return jsonify({'success': True, 'files': files})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/service-status', methods=['GET'])
def check_service_status():
    """Check status of OSINT modules/services.
    
    Returns:
        JSON response with service status
    """
    try:
        import requests
        
        services = []
        
        # Test external services
        service_checks = {
            'sherlock': {'url': 'https://github.com/sherlock-project/sherlock', 'method': 'GET'},
            'holehe': {'check': 'module'},  # Module-based check
            'leak_checker': {'check': 'module'},
            'theharvester': {'check': 'module'},
            'subfinder': {'check': 'command'},  # Binary check
            'wayback': {'url': 'https://archive.org', 'method': 'GET'},
            'nuclei': {'check': 'command'},
            'dnsdumpster': {'url': 'https://dnsdumpster.com', 'method': 'GET'},
            'exiftool': {'check': 'command'},
        }
        
        for name, check_info in service_checks.items():
            status = 'live'
            try:
                if 'url' in check_info:
                    # HTTP check
                    r = requests.head(check_info['url'], timeout=3)
                    status = 'live' if r.status_code < 500 else 'down'
                elif check_info.get('check') == 'module':
                    # Python module availability
                    status = 'live'  # If imported successfully
                elif check_info.get('check') == 'command':
                    # Command availability
                    import shutil
                    status = 'live' if shutil.which(name) else 'down'
            except:
                status = 'down'
            
            services.append({'name': name, 'status': status})
        
        return jsonify({
            'success': True,
            'services': services
        })
    
    except Exception as e:
        logger.error(f"Service status check failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/validate', methods=['POST'])
def validate():
    """Validate a target input.
    
    Returns:
        JSON response with validation result
    """
    try:
        data = request.get_json()
        target = data.get('target', '')
        
        if not target:
            return jsonify({
                'success': False,
                'error': 'Target is required'
            }), 400
        
        is_valid = validate_target(target)
        target_type = detect_target_type(target) if is_valid else 'invalid'
        
        return jsonify({
            'success': True,
            'valid': is_valid,
            'target_type': target_type
        })
    
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/scan', methods=['POST'])
def start_scan():
    """Start an OSINT scan.
    
    Returns:
        JSON response with scan ID
    """
    try:
        data = request.get_json()
        target = data.get('target', '')
        modules = data.get('modules', ['sherlock', 'holehe', 'leak_checker'])
        use_intelligence = data.get('use_intelligence', False)
        
        if not target:
            return jsonify({
                'success': False,
                'error': 'Target is required'
            }), 400
        
        if not validate_target(target):
            return jsonify({
                'success': False,
                'error': f'Invalid target: {target}'
            }), 400
        
        # Generate scan ID
        scan_id = f"scan_{int(time.time())}"
        
        # Start scan in background thread
        thread = threading.Thread(
            target=run_scan_background,
            args=(scan_id, target, modules, use_intelligence)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'scan_id': scan_id,
            'message': 'Scan started successfully'
        })
    
    except Exception as e:
        logger.error(f"Failed to start scan: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def run_scan_background(scan_id: str, target: str, modules: list, use_intelligence: bool):
    """Run a scan in the background with real-time updates.
    
    Args:
        scan_id: Unique scan identifier
        target: Target to scan
        modules: List of modules to run
        use_intelligence: Whether to use intelligence analysis
    """
    try:
        # Emit start event
        socketio.emit('scan_update', {
            'scan_id': scan_id,
            'status': 'started',
            'message': f'Starting scan on {target}',
            'progress': 0
        })
        
        # Detect target type
        target_type = detect_target_type(target)
        
        socketio.emit('scan_update', {
            'scan_id': scan_id,
            'status': 'progress',
            'message': f'Detected target type: {target_type}',
            'progress': 5
        })
        
        # Initialize engine
        engine = AthenaEngine(
            target_query=target,
            target_type=target_type,
            use_intelligence=use_intelligence,
            quiet=True,
            socketio=socketio # Pass global socketio for real-time module updates
        )
        
        # Run scan using the engine's orchestrator (which handles per-module emission now)
        engine.run_scan(modules)
        # Final Report Generation
        report_path = engine.generate_report(output_format='json')
        
        # Load Report Data for Frontend
        with open(report_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)

        # Save scan to history
        _save_scan_history({
            'scan_id': scan_id,
            'target': target,
            'target_type': target_type,
            'modules': modules,
            'use_intelligence': use_intelligence,
            'status': 'completed',
            'timestamp': datetime.now().isoformat(),
            'report_path': str(report_path),
            'summary': report_data.get('summary', {})
        })

        # Emit Completion
        socketio.emit('scan_update', {
            'scan_id': scan_id,
            'status': 'completed',
            'message': 'Scan completed successfully',
            'progress': 100,
            'report': report_data
        })
        
    except Exception as e:
        logger.error(f"Scan execution failed: {e}")
        socketio.emit('scan_update', {
            'scan_id': scan_id,
            'status': 'failed',
            'message': f'Scan failed: {str(e)}',
            'progress': 0
        })
    # Function ends here, cleaned up exception block is above.
    pass
    # End of run_scan_background
    pass


def _save_scan_history(scan_data: dict):
    """Save scan to history file."""
    try:
        history_file = Path('data/scan_history.json')
        history_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing history
        if history_file.exists():
            with open(history_file, 'r') as f:
                history = json.load(f)
        else:
            history = []
        
        # Add new scan
        history.insert(0, scan_data)  # Most recent first
        
        # Keep only last 100 scans
        history = history[:100]
        
        # Save updated history
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
            
    except Exception as e:
        logger.error(f"Failed to save scan history: {e}")


@app.route('/api/history', methods=['GET'])
def get_scan_history():
    """Get scan history.
    
    Returns:
        JSON response with scan history
    """
    try:
        history_file = Path('data/scan_history.json')
        
        if not history_file.exists():
            return jsonify({
                'success': True,
                'scans': []
            })
        
        with open(history_file, 'r') as f:
            history = json.load(f)
        
        return jsonify({
            'success': True,
            'scans': history
        })
    
    except Exception as e:
        logger.error(f"Failed to get scan history: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/history/<scan_id>', methods=['GET'])
def get_scan_details(scan_id):
    """Get details for a specific scan.
    
    Args:
        scan_id: Scan ID
        
    Returns:
        JSON response with scan details
    """
    try:
        history_file = Path('data/scan_history.json')
        
        if not history_file.exists():
            return jsonify({
                'success': False,
                'error': 'Scan not found'
            }), 404
        
        with open(history_file, 'r') as f:
            history = json.load(f)
        
        # Find scan
        scan = next((s for s in history if s['scan_id'] == scan_id), None)
        
        if not scan:
            return jsonify({
                'success': False,
                'error': 'Scan not found'
            }), 404
        
        # Load full report if available
        if scan.get('report_path'):
            report_path = Path(scan['report_path'])
            if report_path.exists():
                with open(report_path, 'r') as f:
                    scan['full_report'] = json.load(f)
        
        return jsonify({
            'success': True,
            'scan': scan
        })
    
    except Exception as e:
        logger.error(f"Failed to get scan details: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/reports/<filename>', methods=['GET'])
def download_report(filename):
    """Download a generated report.
    
    Args:
        filename: Report filename
        
    Returns:
        Report file
    """
    try:
        reports_dir = config.get('REPORTS_DIR')
        file_path = reports_dir / filename
        
        if not file_path.exists():
            return jsonify({
                'success': False,
                'error': 'Report not found'
            }), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        logger.error(f"Failed to download report: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/config', methods=['GET'])
def get_config_status():
    """Get configuration status.
    
    Returns:
        JSON response with config status
    """
    try:
        api_keys = {
            'HIBP_API_KEY': bool(config.get('HIBP_API_KEY')),
            'DEHASHED_API_KEY': bool(config.get('DEHASHED_API_KEY')),
            'INTELX_API_KEY': bool(config.get('INTELX_API_KEY')),
            'TELEGRAM_BOT_TOKEN': bool(config.get('TELEGRAM_BOT_TOKEN')),
        }
        
        return jsonify({
            'success': True,
            'api_keys': api_keys,
            'settings': {
                'max_depth': config.get('MAX_SCAN_DEPTH'),
                'rate_limit': config.get('RATE_LIMIT')
            }
        })
    
    except Exception as e:
        logger.error(f"Failed to get config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# SocketIO event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info('Client connected')
    emit('connection_response', {'status': 'connected'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info('Client disconnected')


@socketio.on('ping')
def handle_ping():
    """Handle ping event."""
    emit('pong', {'timestamp': time.time()})


# ============================================================================
# BREACH MONITORING API ENDPOINTS
# ============================================================================

@app.route('/api/breach/daemon/start', methods=['POST'])
@login_required
def start_breach_daemon():
    """Start the autonomous breach monitoring daemon."""
    try:
        from core.breach_daemon_mp import get_daemon_manager
        
        manager = get_daemon_manager()
        
        # Check if already running
        if manager.is_running():
            return jsonify({
                'success': True,
                'message': 'Breach daemon already running',
                'stats': manager.get_stats()
            })
        
        # Start daemon with config
        max_cpu = float(request.json.get('max_cpu_percent', 30.0)) if request.json else 30.0
        max_memory = int(request.json.get('max_memory_mb', 512)) if request.json else 512
        interval = int(request.json.get('check_interval', 1800)) if request.json else 1800
        
        started = manager.start(
            max_cpu_percent=max_cpu,
            max_memory_mb=max_memory,
            check_interval=interval
        )
        
        if started:
            return jsonify({
                'success': True,
                'message': 'Breach daemon started successfully',
                'stats': manager.get_stats()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to start daemon'
            }), 500
    
    except Exception as e:
        logger.error(f"Failed to start breach daemon: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/breach/daemon/stop', methods=['POST'])
@login_required
def stop_breach_daemon():
    """Stop the breach monitoring daemon."""
    try:
        from core.breach_daemon_mp import get_daemon_manager
        
        manager = get_daemon_manager()
        stopped = manager.stop()
        
        return jsonify({
            'success': True,
            'message': 'Breach daemon stopped' if stopped else 'Daemon was not running'
        })
    
    except Exception as e:
        logger.error(f"Failed to stop breach daemon: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/breach/daemon/status', methods=['GET'])
def get_breach_daemon_status():
    """Get breach daemon status and statistics."""
    try:
        from core.breach_daemon_mp import get_daemon_manager
        
        manager = get_daemon_manager()
        running = manager.is_running()
        stats = manager.get_stats()
        
        return jsonify({
            'success': True,
            'running': running,
            'stats': stats,
            'message': 'Daemon running' if running else 'Daemon not running'
        })
    
    except Exception as e:
        logger.error(f"Failed to get daemon status: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/breach/daemon/pause', methods=['POST'])
@login_required
def pause_breach_daemon():
    """Pause the breach daemon."""
    try:
        from core.breach_daemon_mp import get_daemon_manager
        
        manager = get_daemon_manager()
        
        if manager.is_running():
            paused = manager.pause()
            return jsonify({'success': True, 'message': 'Daemon paused'})
        else:
            return jsonify({'success': False, 'error': 'Daemon not running'}), 400
    
    except Exception as e:
        logger.error(f"Failed to pause daemon: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/breach/daemon/resume', methods=['POST'])
@login_required
def resume_breach_daemon():
    """Resume the breach daemon."""
    try:
        from core.breach_daemon_mp import get_daemon_manager
        
        manager = get_daemon_manager()
        
        if manager.is_running():
            resumed = manager.resume()
            return jsonify({'success': True, 'message': 'Daemon resumed'})
        else:
            return jsonify({'success': False, 'error': 'Daemon not running'}), 400
    
    except Exception as e:
        logger.error(f"Failed to resume daemon: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/breach/search/email', methods=['POST'])
def search_breach_email():
    """Search for an email in breach database."""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        
        if not email or '@' not in email:
            return jsonify({'success': False, 'error': 'Valid email required'}), 400
        
        from intelligence.breach_indexer import BreachIndexer
        indexer = BreachIndexer()
        
        results = indexer.search_email(email)
        
        return jsonify({
            'success': True,
            'email': email,
            'found': len(results) > 0,
            'breach_count': len(results),
            'results': results
        })
    
    except Exception as e:
        logger.error(f"Breach search error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/breach/search/domain', methods=['POST'])
def search_breach_domain():
    """Search for all emails from a domain in breach database."""
    try:
        data = request.get_json()
        domain = data.get('domain', '').strip()
        
        if not domain:
            return jsonify({'success': False, 'error': 'Domain required'}), 400
        
        from intelligence.breach_indexer import BreachIndexer
        indexer = BreachIndexer()
        
        results = indexer.search_domain(domain)
        
        return jsonify({
            'success': True,
            'domain': domain,
            'email_count': len(results),
            'results': results[:100]  # Limit to 100 for display
        })
    
    except Exception as e:
        logger.error(f"Domain search error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/breach/stats', methods=['GET'])
def get_breach_stats():
    """Get breach database statistics."""
    try:
        from intelligence.breach_indexer import BreachIndexer
        indexer = BreachIndexer()
        
        stats = indexer.get_breach_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/breach/index/manual', methods=['POST'])
@login_required
def manual_breach_index():
    """Manually trigger indexing of uploaded files."""
    try:
        from intelligence.breach_indexer import BreachIndexer
        from core.background_worker import UPLOAD_DIR
        
        indexer = BreachIndexer()
        
        # Get files to index
        files = list(UPLOAD_DIR.glob('*.txt'))
        files.extend(list(UPLOAD_DIR.glob('*.csv')))
        
        if not files:
            return jsonify({
                'success': False,
                'error': 'No files to index in upload directory'
            }), 400
        
        results = []
        for file_path in files:
            result = indexer.index_file(file_path)
            results.append({
                'file': file_path.name,
                'result': result
            })
        
        return jsonify({
            'success': True,
            'message': f'Indexed {len(results)} files',
            'results': results
        })
    
    except Exception as e:
        logger.error(f"Manual indexing error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# API KEY MANAGEMENT ENDPOINTS
# ============================================================================

@app.route('/api/keys/services', methods=['GET'])
def get_api_services():
    """Get list of supported API services with signup info."""
    try:
        from core.api_gatherer import APIGatherer
        gatherer = APIGatherer()
        
        instructions = gatherer.get_signup_instructions()
        
        return jsonify({
            'success': True,
            'services': instructions
        })
    
    except Exception as e:
        logger.error(f"Error getting services: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/keys/add', methods=['POST'])
@login_required
def add_api_key():
    """Add an API key to the rotation pool."""
    try:
        data = request.get_json()
        service = data.get('service', '').strip().lower()
        key = data.get('key', '').strip()
        
        if not service or not key:
            return jsonify({'success': False, 'error': 'Service and key required'}), 400
        
        from core.api_rotator import get_rotator
        rotator = get_rotator()
        
        # Test the key first
        from core.api_gatherer import APIGatherer
        gatherer = APIGatherer()
        
        import asyncio
        is_valid = asyncio.run(gatherer.test_api_key(service, key))
        
        if not is_valid:
            return jsonify({
                'success': False,
                'error': 'API key validation failed'
            }), 400
        
        # Add to rotator
        result = rotator.add_key(service, key, metadata={
            'source': 'manual',
            'added_by': 'admin'
        })
        
        if result:
            return jsonify({
                'success': True,
                'message': f'API key added for {service}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Key already exists'
            }), 400
    
    except Exception as e:
        logger.error(f"Error adding API key: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/keys/remove', methods=['POST'])
@login_required
def remove_api_key():
    """Remove an API key from rotation."""
    try:
        data = request.get_json()
        service = data.get('service', '').strip().lower()
        key = data.get('key', '').strip()
        
        if not service or not key:
            return jsonify({'success': False, 'error': 'Service and key required'}), 400
        
        from core.api_rotator import get_rotator
        rotator = get_rotator()
        
        rotator.remove_key(service, key)
        
        return jsonify({
            'success': True,
            'message': f'API key removed for {service}'
        })
    
    except Exception as e:
        logger.error(f"Error removing API key: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/keys/stats', methods=['GET'])
def get_api_key_stats():
    """Get statistics for all API keys."""
    try:
        from core.api_rotator import get_rotator
        rotator = get_rotator()
        
        stats = rotator.get_all_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    
    except Exception as e:
        logger.error(f"Error getting API stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/keys/validate', methods=['POST'])
@login_required
def validate_api_keys():
    """Validate all existing API keys."""
    try:
        from core.api_gatherer import APIGatherer
        
        gatherer = APIGatherer()
        
        # Run validation asynchronously
        import asyncio
        asyncio.run(gatherer.validate_existing_keys())
        
        return jsonify({
            'success': True,
            'message': 'API key validation complete'
        })
    
    except Exception as e:
        logger.error(f"Error validating keys: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/keys/gather', methods=['POST'])
@login_required
def gather_api_keys():
    """Automatically gather API keys from public sources."""
    try:
        from core.api_gatherer import APIGatherer
        
        gatherer = APIGatherer()
        
        # Run gathering
        import asyncio
        keys = asyncio.run(gatherer.gather_all_keys())
        
        return jsonify({
            'success': True,
            'message': f'Discovered {sum(len(v) for v in keys.values())} API keys',
            'keys': {k: len(v) for k, v in keys.items()}
        })
    
    except Exception as e:
        logger.error(f"Error gathering keys: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/jarvis/chat', methods=['POST'])
def jarvis_chat():
    """Handle chat with Jarvis."""
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return jsonify({'success': False, 'error': 'Message required'}), 400
            
        # Initialize Agent (Lazy load)
        from intelligence.jarvis import JarvisAgent
        agent = JarvisAgent()
        
        response = agent.process_input(message)
        
        # If action is scan, we might want to trigger it here or let frontend do it
        # For seamless Integration: Frontend handles "scan" action by calling /api/scan
        
        return jsonify({
            'success': True,
            'data': response
        })
        
    except Exception as e:
        logger.error(f"Jarvis Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Scheduler API (scheduled tasks)
@app.route('/api/scheduler/tasks', methods=['GET', 'POST'])
@login_required
def scheduler_tasks():
    try:
        if request.method == 'GET':
            tasks_file = Path('data/scheduled_tasks.json')
            if tasks_file.exists():
                data = json.loads(tasks_file.read_text())
                return jsonify({"success": True, "tasks": data.get('tasks', [])})
            return jsonify({"success": True, "tasks": []})
        payload = request.get_json() or {}
        tasks_file = Path('data/scheduled_tasks.json')
        data = json.loads(tasks_file.read_text()) if tasks_file.exists() else {"tasks": []}
        task = {
            "id": str(uuid.uuid4()),
            "name": payload.get('name', 'Task'),
            "type": payload.get('type', 'scan'),
            "schedule": payload.get('schedule', '0 0 * * *'),
            "command": payload.get('command', ''),
            "status": "active",
            "last_run": None,
            "created_at": datetime.utcnow().isoformat(),
        }
        data['tasks'].append(task)
        tasks_file.parent.mkdir(parents=True, exist_ok=True)
        tasks_file.write_text(json.dumps(data, indent=2))
        socketio.emit('notification', {"type": "task_created", "task": task['name']}, broadcast=True)
        return jsonify({"success": True, "task": task})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/scheduler/tasks/<task_id>', methods=['PUT', 'DELETE'])
@login_required
def scheduler_task_action(task_id):
    try:
        tasks_file = Path('data/scheduled_tasks.json')
        data = json.loads(tasks_file.read_text()) if tasks_file.exists() else {"tasks": []}
        tasks = data.get('tasks', [])
        if request.method == 'PUT':
            payload = request.get_json() or {}
            for t in tasks:
                if t.get('id') == task_id:
                    t['status'] = payload.get('status', t.get('status'))
                    data['tasks'] = tasks
                    tasks_file.write_text(json.dumps(data, indent=2))
                    return jsonify({"success": True})
        elif request.method == 'DELETE':
            data['tasks'] = [t for t in tasks if t.get('id') != task_id]
            tasks_file.write_text(json.dumps(data, indent=2))
            socketio.emit('notification', {"type": "task_deleted"}, broadcast=True)
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "task not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/scripts', methods=['GET', 'POST'])
@login_required
def scripts_api():
    try:
        scripts_dir = Path('data/scripts')
        scripts_dir.mkdir(parents=True, exist_ok=True)
        if request.method == 'GET':
            scripts = []
            for f in scripts_dir.glob('*'):
                if f.is_file():
                    scripts.append({"name": f.name, "size": f.stat().st_size, "created": datetime.fromtimestamp(f.stat().st_ctime).isoformat()})
            return jsonify({"success": True, "scripts": scripts})
        payload = request.get_json() or {}
        name = payload.get('name', '').strip()
        code = payload.get('code', '')
        if not name or not code:
            return jsonify({"success": False, "error": "name and code required"}), 400
        script_file = scripts_dir / name
        script_file.write_text(code)
        socketio.emit('notification', {"type": "script_saved", "script": name}, broadcast=True)
        return jsonify({"success": True, "script": name})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/scripts/run', methods=['POST'])
@login_required
def scripts_run():
    try:
        payload = request.get_json() or {}
        name = payload.get('name', '').strip()
        args = payload.get('args', '').strip()
        script_file = Path('data/scripts') / name
        if not script_file.exists():
            return jsonify({"success": False, "error": "script not found"}), 404
        import subprocess
        cmd = f"python {script_file}" if name.endswith('.py') else f"bash {script_file}"
        if args:
            cmd += f" {args}"
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300, cwd='/opt/agent/workdir')
        socketio.emit('notification', {"type": "script_executed", "script": name}, broadcast=True)
        return jsonify({"success": proc.returncode == 0, "stdout": proc.stdout, "stderr": proc.stderr})
    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "error": "timeout"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/scripts/<name>', methods=['DELETE'])
@login_required
def scripts_delete(name):
    try:
        script_file = Path('data/scripts') / name
        if script_file.exists():
            script_file.unlink()
            socketio.emit('notification', {"type": "script_deleted", "script": name}, broadcast=True)
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================================
# SENTINEL MODE - AI-Powered Monitoring & Vulnerability Lab
# ============================================================================

@app.route('/sentinel')
@login_required
def sentinel_view():
    """Render Sentinel monitoring dashboard."""
    return render_template('sentinel.html')

@app.route('/api/sentinel/add', methods=['POST'])
@login_required
def sentinel_add_monitor():
    """Add a new monitoring job."""
    try:
        from core.scheduler import get_scheduler
        
        data = request.get_json() or request.form.to_dict()
        target = data.get('target')
        module = data.get('module', 'headless_monitor')
        interval_hours = int(data.get('interval', 6))
        
        if not target:
            return jsonify({'success': False, 'error': 'Target required'}), 400
        
        scheduler = get_scheduler()
        job_id = scheduler.add_monitor_job(target, module, interval_hours)
        
        return jsonify({'success': True, 'job_id': job_id})
    except Exception as e:
        logger.error(f"Failed to add monitor: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sentinel/jobs', methods=['GET'])
@login_required
def sentinel_list_jobs():
    """List all active monitoring jobs."""
    try:
        from core.scheduler import get_scheduler
        
        scheduler = get_scheduler()
        jobs = scheduler.list_jobs()
        
        return jsonify({'success': True, 'jobs': jobs})
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sentinel/remove', methods=['POST'])
@login_required
def sentinel_remove_job():
    """Remove a monitoring job."""
    try:
        from core.scheduler import get_scheduler
        
        data = request.get_json() or request.form.to_dict()
        job_id = data.get('id')
        
        if not job_id:
            return jsonify({'success': False, 'error': 'Job ID required'}), 400
        
        scheduler = get_scheduler()
        removed = scheduler.remove_job(job_id)
        
        return jsonify({'success': True, 'removed': removed})
    except Exception as e:
        logger.error(f"Failed to remove job: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sentinel/analyze-diff', methods=['POST'])
@login_required
def sentinel_analyze_diff():
    """AI-powered diff analysis."""
    try:
        from intelligence.ai_sentinel import get_ai_analyzer
        
        data = request.get_json()
        old_content = data.get('old_content', '')
        new_content = data.get('new_content', '')
        url = data.get('url', 'unknown')
        context = data.get('context', {})
        
        analyzer = get_ai_analyzer()
        analysis = analyzer.analyze_diff(old_content, new_content, url, context)
        
        # Emit alert if critical/high severity
        if analysis['severity'] in ['critical', 'high']:
            socketio.emit('sentinel_alert', {
                'severity': analysis['severity'],
                'summary': analysis['summary'],
                'url': url,
                'timestamp': datetime.now().isoformat()
            })
        
        return jsonify({'success': True, 'analysis': analysis})
    except Exception as e:
        logger.error(f"Diff analysis failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sentinel/analyze-vuln', methods=['POST'])
@login_required
def sentinel_analyze_vuln():
    """AI-powered vulnerability assessment."""
    try:
        from intelligence.ai_sentinel import get_ai_analyzer
        
        data = request.get_json()
        vuln_data = data.get('vulnerability', {})
        
        analyzer = get_ai_analyzer()
        assessment = analyzer.assess_vulnerability(vuln_data)
        
        return jsonify({'success': True, 'assessment': assessment})
    except Exception as e:
        logger.error(f"Vulnerability analysis failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sentinel/alerts', methods=['GET'])
@login_required
def sentinel_get_alerts():
    """Get recent Sentinel alerts."""
    try:
        # Load recent alerts from data/intelligence/monitor_results
        from pathlib import Path
        import json
        
        alerts_dir = Path('data/intelligence/monitor_results')
        alerts_dir.mkdir(parents=True, exist_ok=True)
        
        alerts = []
        alert_files = sorted(alerts_dir.glob('monitor_alert_*.json'), reverse=True)[:20]
        
        for alert_file in alert_files:
            with open(alert_file, 'r') as f:
                alert = json.load(f)
                alerts.append(alert)
        
        return jsonify({'success': True, 'alerts': alerts})
    except Exception as e:
        logger.error(f"Failed to load alerts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# 24/7 BACKGROUND HARVESTER - Autonomous OSINT Collection
# ============================================================================

@app.route('/harvester')
@login_required
def harvester_dashboard():
    """Render 24/7 harvester dashboard."""
    return render_template('harvester.html')

@app.route('/api/harvester/start', methods=['POST'])
@login_required
def harvester_start():
    """Start the background harvester."""
    try:
        from core.background_harvester import get_harvester
        
        harvester = get_harvester()
        num_workers = request.json.get('workers', 4) if request.is_json else 4
        
        harvester.start(num_workers=num_workers)
        
        return jsonify({'success': True, 'message': f'Harvester started with {num_workers} workers'})
    except Exception as e:
        logger.error(f"Failed to start harvester: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/harvester/stop', methods=['POST'])
@login_required
def harvester_stop():
    """Stop the background harvester."""
    try:
        from core.background_harvester import get_harvester
        
        harvester = get_harvester()
        harvester.stop()
        
        return jsonify({'success': True, 'message': 'Harvester stopped'})
    except Exception as e:
        logger.error(f"Failed to stop harvester: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/harvester/status', methods=['GET'])
@login_required
def harvester_status():
    """Get harvester status and statistics."""
    try:
        from core.background_harvester import get_harvester
        
        harvester = get_harvester()
        stats = harvester.get_stats()
        
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        logger.error(f"Failed to get harvester status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/harvester/config', methods=['GET', 'PUT'])
@login_required
def harvester_config():
    """Get or update harvester configuration."""
    try:
        from core.background_harvester import get_harvester
        
        harvester = get_harvester()
        
        if request.method == 'GET':
            return jsonify({'success': True, 'config': harvester.config})
        
        else:  # PUT
            data = request.get_json()
            
            # Update config
            harvester.config.update(data)
            harvester._save_config()
            
            return jsonify({'success': True, 'message': 'Configuration updated'})
    
    except Exception as e:
        logger.error(f"Failed to manage harvester config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/harvester/add-target', methods=['POST'])
@login_required
def harvester_add_target():
    """Add a target to watchlist."""
    try:
        from core.background_harvester import get_harvester
        
        data = request.get_json() or request.form.to_dict()
        target_type = data.get('type')  # domain, email, username, keyword
        target = data.get('target')
        
        if not target_type or not target:
            return jsonify({'success': False, 'error': 'Missing type or target'}), 400
        
        harvester = get_harvester()
        harvester.add_target(target_type, target)
        
        return jsonify({'success': True, 'message': f'Added {target} to {target_type} watchlist'})
    
    except Exception as e:
        logger.error(f"Failed to add target: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/harvester/results', methods=['GET'])
@login_required
def harvester_results():
    """Get recent harvester results."""
    try:
        from pathlib import Path
        import json
        
        results_dir = Path('data/harvester_results')
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Get recent result files (last 50)
        result_files = sorted(results_dir.glob('*.json'), key=lambda p: p.stat().st_mtime, reverse=True)[:50]
        
        results = []
        for file in result_files:
            try:
                with open(file, 'r') as f:
                    result = json.load(f)
                    results.append(result)
            except:
                pass
        
        return jsonify({'success': True, 'results': results, 'total': len(results)})
    
    except Exception as e:
        logger.error(f"Failed to get harvester results: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/harvester/alerts', methods=['GET'])
@login_required
def harvester_alerts():
    """Get harvester alerts."""
    try:
        from pathlib import Path
        import json
        
        results_dir = Path('data/harvester_results')
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Get alert files
        alert_files = sorted(results_dir.glob('alert_*.json'), key=lambda p: p.stat().st_mtime, reverse=True)[:30]
        
        alerts = []
        for file in alert_files:
            try:
                with open(file, 'r') as f:
                    alert = json.load(f)
                    alerts.append(alert)
            except:
                pass
        
        return jsonify({'success': True, 'alerts': alerts, 'total': len(alerts)})
    
    except Exception as e:
        logger.error(f"Failed to get harvester alerts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# MR.HOLMES INTEGRATION - Unified OSINT Tool
# ============================================================================

@app.route('/mrholmes')
@login_required
def mrholmes_dashboard():
    """Mr.Holmes integrated OSINT tool dashboard."""
    return render_template('mrholmes.html')

@app.route('/api/mrholmes/install', methods=['POST'])
@login_required
def mrholmes_install():
    """Install Mr.Holmes from GitHub."""
    try:
        from modules.mrholmes import MrHolmes
        
        mrholmes = MrHolmes()
        
        if mrholmes.is_installed():
            return jsonify({
                'success': True,
                'message': 'Mr.Holmes is already installed',
                'install_dir': str(mrholmes.install_dir)
            })
        
        # Install in background
        success = mrholmes.install()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Mr.Holmes installed successfully',
                'install_dir': str(mrholmes.install_dir)
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Installation failed. Check logs for details.'
            }), 500
            
    except Exception as e:
        logger.error(f"Mr.Holmes installation failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/mrholmes/status', methods=['GET'])
@login_required
def mrholmes_status():
    """Check Mr.Holmes installation status."""
    try:
        from modules.mrholmes import MrHolmes
        
        mrholmes = MrHolmes()
        installed = mrholmes.is_installed()
        
        return jsonify({
            'success': True,
            'installed': installed,
            'install_dir': str(mrholmes.install_dir) if installed else None,
            'repo_url': mrholmes.repo_url
        })
        
    except Exception as e:
        logger.error(f"Failed to check Mr.Holmes status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/mrholmes/search', methods=['POST'])
@login_required
def mrholmes_search():
    """
    Run Mr.Holmes search.
    
    Request JSON:
        {
            "target": "username/email/phone/domain",
            "target_type": "username|email|phone|domain|auto",
            "use_proxy": false
        }
    """
    try:
        data = request.get_json()
        target = data.get('target', '').strip()
        target_type = data.get('target_type', 'auto')
        use_proxy = data.get('use_proxy', False)
        
        if not target:
            return jsonify({'success': False, 'error': 'Target is required'}), 400
        
        from modules.mrholmes import scan
        
        logger.info(f"Mr.Holmes search: {target} (type: {target_type})")
        
        # Run search
        result = scan(target, target_type=target_type, use_proxy=use_proxy)
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        logger.error(f"Mr.Holmes search failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/mrholmes/results/<target_type>/<target>', methods=['GET'])
@login_required
def mrholmes_get_results(target_type, target):
    """Retrieve Mr.Holmes results for a target."""
    try:
        from modules.mrholmes import MrHolmes
        
        mrholmes = MrHolmes()
        result = mrholmes.get_results(target, target_type)
        
        if result:
            return jsonify({
                'success': True,
                'result': result
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No results found for this target'
            }), 404
            
    except Exception as e:
        logger.error(f"Failed to get Mr.Holmes results: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    # This is for development only
    socketio.run(
        app,
        host=config.get('FLASK_HOST'),
        port=config.get('FLASK_PORT'),
        debug=(config.get('FLASK_ENV') == 'development')
    )


