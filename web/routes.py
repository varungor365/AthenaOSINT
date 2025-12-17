"""
Web Interface Routes for AthenaOSINT.
"""

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import threading
import sys
import os
import json

# Ensure we can import core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine import AthenaEngine
from config import get_config

app = Flask(__name__)
app.config['SECRET_KEY'] = get_config().get('FLASK_SECRET_KEY', 'default_secret')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    """Render dashboard."""
    return render_template('dashboard.html')

@app.route('/vision')
def vision():
    """Render graph visualization."""
    return render_template('vision.html')

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'})

@socketio.on('start_scan')
def handle_scan(data):
    """Handle scan request from websocket."""
    target = data.get('target')
    scan_type = data.get('type', 'full')
    
    if not target:
        emit('scan_update', {'status': 'error', 'message': 'Target required'})
        return
    
    emit('scan_update', {'status': 'info', 'message': f'Starting {scan_type} scan for {target} Use Intelligence: ON'})
    
    # Run scan in thread to not block websocket
    thread = threading.Thread(target=_run_scan_process, args=(target, scan_type))
    thread.start()

def _run_scan_process(target, scan_type):
    """Run the scan logic."""
    try:
        # Initialize Engine with WebSocket logger?
        # For now, we'll just run it and let it finish, sending a final update.
        # Ideally, AthenaEngine should emit events. 
        # We'll create a subclass or callback mechanism later.
        
        engine = AthenaEngine(target, use_intelligence=True)
        
        # Select modules
        modules = [
             'sherlock', 'theharvester', 'holehe', 'subfinder', 'leak_checker',
             'dnsdumpster', 'amass', 'nuclei', 'foca' # 'exiftool' needs file
        ]
        
        engine.run_scan(modules)
        
        # Get results
        results = engine.profile.to_dict()
        graph_data = engine.profile.get_graph_data()
        
        # Generate Report
        report_path = engine.generate_report('html')
        
        socketio.emit('scan_complete', {
             'status': 'success',
             'message': 'Scan completed successfully',
             'data': results,
             'graph': graph_data,
             'report': str(report_path)
        })
        
    except Exception as e:
        socketio.emit('scan_update', {'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    socketio.run(app, debug=True, port=int(get_config().get('FLASK_PORT', 5000)))
