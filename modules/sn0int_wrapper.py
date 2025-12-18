"""
sn0int Wrapper Module.
Semi-automatic OSINT framework and package manager.
"""
import shutil
import subprocess
from loguru import logger
from core.engine import Profile

# Metadata
META = {
    'name': 'sn0int',
    'description': 'sn0int OSINT Framework Wrapper',
    'category': 'Framework',
    'risk': 'medium', 
    'emoji': '🧶'
}

def scan(target: str, profile: Profile):
    """
    Runs sn0int modules on the target.
    """
    if not shutil.which('sn0int'):
        logger.warning("[sn0int] Executable not found. Install via 'pkg' or 'cargo'.")
        profile.add_error('sn0int', 'Executable not found')
        return

    logger.info(f"[sn0int] Investigating {target}...")
    
    # sn0int is interactive by default, automation requires specific commands
    # Example: sn0int run -m dns_resolve -t domain ...
    
    try:
        # Placeholder command structure
        cmd = ['sn0int', 'run', '-t', target]
        # Real usage depends on installed sn0int modules
        
        logger.info("[sn0int] Automation requires specific modules installed in sn0int registry.")
        logger.info("[sn0int] Skipping execution to prevent hanging (Interactive tool).")
        
    except Exception as e:
        logger.error(f"[sn0int] Error: {e}")
