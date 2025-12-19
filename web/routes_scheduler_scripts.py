# Additional API endpoints for scheduler, scripts, and notifications
# Add these to web/routes.py after the existing agent task routes

@app.route('/api/scheduler/tasks', methods=['GET', 'POST'])
@login_required
def scheduler_tasks():
    """Manage scheduled tasks"""
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
    """Update or delete a scheduled task"""
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
    """List or save custom scripts"""
    try:
        scripts_dir = Path('data/scripts')
        scripts_dir.mkdir(parents=True, exist_ok=True)
        
        if request.method == 'GET':
            scripts = []
            for f in scripts_dir.glob('*'):
                if f.is_file():
                    scripts.append({
                        "name": f.name,
                        "size": f.stat().st_size,
                        "created": datetime.fromtimestamp(f.stat().st_ctime).isoformat(),
                    })
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
    """Execute a saved script"""
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
    """Delete a custom script"""
    try:
        script_file = Path('data/scripts') / name
        if script_file.exists():
            script_file.unlink()
            socketio.emit('notification', {"type": "script_deleted", "script": name}, broadcast=True)
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
