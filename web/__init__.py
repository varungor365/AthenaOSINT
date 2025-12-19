"""Web interface package for AthenaOSINT."""

from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS

app = None
socketio = None


def create_app():
    """Create and configure the Flask application."""
    global app, socketio
    
    from config import get_config
    
    config = get_config()
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = config.get('FLASK_SECRET_KEY')
    app.config['JSON_SORT_KEYS'] = False
    
    # Enable CORS
    CORS(app)
    
    # Initialize SocketIO with better error handling and configuration
    socketio = SocketIO(
        app, 
        cors_allowed_origins="*",
        async_mode='eventlet',
        logger=False,  # Disable verbose logging
        engineio_logger=False,  # Disable engine.io logging
        ping_timeout=60,
        ping_interval=25,
        max_http_buffer_size=1000000
    )
    
    # Register routes
    from . import routes
    
    return app, socketio


__all__ = ['create_app', 'app', 'socketio']
