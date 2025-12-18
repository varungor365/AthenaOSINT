"""
OWASP Maryam Wrapper.
Integrates OWASP Maryam OSINT framework capabilities.
"""
from loguru import logger
from core.engine import Profile
import subprocess
import json
import shutil

# Metadata
META = {
    'name': 'maryam',
    'description': 'OWASP Maryam (OSINT Framework) Wrapper',
    'category': 'Framework',
    'risk': 'medium', 
    'emoji': '🦄'
}

def scan(target: str, profile: Profile):
    """
    Wraps Maryam CLI for specific checks.
    """
    # Check if maryam is installed (it should be via pip)
    if not shutil.which('maryam'):
        logger.warning("[Maryam] 'maryam' executable not found. Please install: pip install maryam")
        profile.add_error('maryam', 'Executable not found')
        return

    logger.info(f"[Maryam] Running comprehensive checks on {target}...")

    # Define tasks based on target type (heuristic)
    # Maryam has many modules: dns_search, crawler, email_search, etc.
    
    tasks = []
    if '.' in target and '@' not in target: # Domain
        tasks.append(['-e', 'dns_search', '-d', target])
        tasks.append(['-e', 'dnsbrute', '-d', target])
    elif '@' in target: # Email
        tasks.append(['-e', 'email_search', '-q', target])
        # linkedin?

    for task_args in tasks:
        try:
            # maryam -e <mod> ... --json (if supported? Description says --api shows results as json)
            # Command: maryam -e dns_search -d domain --api
            cmd = ['maryam'] + task_args + ['--api']
            
            logger.info(f"[Maryam] Executing: {' '.join(cmd)}")
            
            # Run subprocess
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=120
            )
            
            if result.stdout:
                # Try to parse JSON output if --api works as expected
                try:
                    data = json.loads(result.stdout)
                    profile.add_metadata({'maryam_data': data})
                    logger.success(f"[Maryam] Task {' '.join(task_args)} yielded results.")
                except json.JSONDecodeError:
                    # Fallback to raw text
                    profile.add_metadata({'maryam_raw': result.stdout[:1000]})
                    logger.info(f"[Maryam] Task finished (Text output).")
            
            if result.stderr:
                logger.debug(f"[Maryam] Stderr: {result.stderr}")

        except Exception as e:
            logger.error(f"[Maryam] Task failed: {e}")
            profile.add_error('maryam', str(e))
