#!/usr/bin/env python3
"""
24/7 Harvester Daemon Runner.
Starts the background harvester as a standalone service.
"""
import signal
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.background_harvester import get_harvester
from loguru import logger


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down...")
    harvester = get_harvester()
    harvester.stop()
    sys.exit(0)


def main():
    """Main entry point for harvester daemon."""
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Configure logging
    logger.add(
        "logs/harvester_{time}.log",
        rotation="1 day",
        retention="30 days",
        level="INFO"
    )
    
    logger.info("=" * 60)
    logger.info("🚀 AthenaOSINT 24/7 Background Harvester Starting...")
    logger.info("=" * 60)
    
    # Start harvester
    harvester = get_harvester()
    harvester.start(num_workers=4)
    
    logger.success("✓ Harvester is now running 24/7")
    logger.info("Configuration file: data/harvester_config.json")
    logger.info("Results directory: data/harvester_results/")
    logger.info("Press Ctrl+C to stop")
    
    # Keep daemon running
    try:
        while True:
            time.sleep(60)
            
            # Print stats every hour
            if int(time.time()) % 3600 == 0:
                stats = harvester.get_stats()
                logger.info(f"📊 Stats: {stats['tasks_completed']} tasks, "
                           f"{stats['threats_found']} threats, "
                           f"{stats['uptime_hours']:.1f}h uptime")
    
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        harvester.stop()
        logger.success("Harvester stopped gracefully")


if __name__ == '__main__':
    main()
