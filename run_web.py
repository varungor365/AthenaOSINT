#!/usr/bin/env python3
"""
Web interface launcher for AthenaOSINT.

This script starts the Flask web server with SocketIO support.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from web.routes import app, socketio
from config import get_config
from loguru import logger


def main():
    """Start the web interface."""
    config = get_config()
    
    host = config.get('FLASK_HOST', '0.0.0.0')
    port = config.get('FLASK_PORT', 5000)
    debug = config.get('FLASK_ENV') == 'development'
    
    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║                    AthenaOSINT Web Interface                  ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

Starting web server on http://{host}:{port}
Press CTRL+C to stop the server
    """)
    
    logger.info(f"Starting web server on {host}:{port}")
    
    try:
        socketio.run(
            app,
            host=host,
            port=port,
            debug=debug,
            allow_unsafe_werkzeug=True  # For development
        )
    except KeyboardInterrupt:
        print("\n\nShutting down web server...")
        logger.info("Web server stopped")
    except Exception as e:
        logger.error(f"Web server error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
