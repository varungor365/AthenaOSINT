"""
Flask routes for AthenaOSINT web interface.

This module provides the web API and dashboard for running OSINT scans.
"""

import threading
import time
from flask import render_template, request, jsonify, send_file
from flask_socketio import emit
from pathlib import Path
from loguru import logger

from web import app, socketio, create_app
from config import get_config
from core.engine import AthenaEngine
from core.validators import validate_target, detect_target_type
from modules import get_available_modules


# Initialize app
app, socketio = create_app()
config = get_config()


@app.route('/')
def index():
    """Render the main dashboard."""
    return render_template('dashboard.html')


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
            quiet=True
        )
        
        # Run each module with progress updates
        total_modules = len(modules)
        for idx, module_name in enumerate(modules):
            progress = int(10 + (idx / total_modules) * 80)
            
            socketio.emit('scan_update', {
                'scan_id': scan_id,
                'status': 'progress',
                'message': f'Running {module_name} module...',
                'progress': progress,
                'current_module': module_name
            })
            
            try:
                engine._run_module(module_name)
            except Exception as e:
                logger.error(f"Module {module_name} failed: {e}")
                socketio.emit('scan_update', {
                    'scan_id': scan_id,
                    'status': 'warning',
                    'message': f'Module {module_name} failed: {str(e)}',
                    'progress': progress
                })
        
        # Finish scan
        engine.profile.scan_duration = time.time() - engine.start_time if engine.start_time else 0
        
        # Run intelligence if enabled
        if use_intelligence:
            socketio.emit('scan_update', {
                'scan_id': scan_id,
                'status': 'progress',
                'message': 'Running intelligence analysis...',
                'progress': 90
            })
            
            try:
                from intelligence.analyzer import IntelligenceAnalyzer
                analyzer = IntelligenceAnalyzer()
                analyzer.analyze_profile(engine.profile)
            except Exception as e:
                logger.error(f"Intelligence analysis failed: {e}")
        
        # Generate reports
        socketio.emit('scan_update', {
            'scan_id': scan_id,
            'status': 'progress',
            'message': 'Generating reports...',
            'progress': 95
        })
        
        json_report = engine.generate_report('json', custom_filename=f"web_{scan_id}")
        html_report = engine.generate_report('html', custom_filename=f"web_{scan_id}")
        
        # Send completion with results
        socketio.emit('scan_update', {
            'scan_id': scan_id,
            'status': 'completed',
            'message': 'Scan completed successfully!',
            'progress': 100,
            'results': engine.profile.to_dict(),
            'summary': engine.profile.get_summary(),
            'reports': {
                'json': str(json_report),
                'html': str(html_report)
            }
        })
        
        logger.info(f"Scan {scan_id} completed successfully")
    
    except Exception as e:
        logger.error(f"Scan {scan_id} failed: {e}")
        socketio.emit('scan_update', {
            'scan_id': scan_id,
            'status': 'failed',
            'message': f'Scan failed: {str(e)}',
            'error': str(e)
        })


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

if __name__ == '__main__':
    # This is for development only
    socketio.run(
        app,
        host=config.get('FLASK_HOST'),
        port=config.get('FLASK_PORT'),
        debug=(config.get('FLASK_ENV') == 'development')
    )

