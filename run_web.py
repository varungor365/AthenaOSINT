"""
Run Script for AthenaOSINT Web Interface.
"""
from web.routes import app, socketio
from config import get_config

if __name__ == "__main__":
    port = int(get_config().get('FLASK_PORT', 5000))
    print(f"Starting Web Interface on port {port}...")
    socketio.run(app, debug=True, port=port)
