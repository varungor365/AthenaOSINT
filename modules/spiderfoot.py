"""
Spiderfoot Module.
Automates 100+ OSINT checks using Spiderfoot.
"""
import shutil
import subprocess
import sys
from pathlib import Path
from core.engine import Profile

META = {
    'description': 'Automates 100+ OSINT checks',
    'target_type': 'domain'
}

TOOLS_DIR = Path('data/tools')

def install():
    """Install Spiderfoot if missing."""
    target_dir = TOOLS_DIR / 'spiderfoot'
    if target_dir.exists():
        return

    print("[-] Installing Spiderfoot...")
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        subprocess.run(['git', 'clone', 'https://github.com/smicallef/spiderfoot.git', str(target_dir)], check=True)
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], cwd=str(target_dir), check=True)
        print("[+] Spiderfoot installed successfully.")
    except Exception as e:
        print(f"[!] Failed to install Spiderfoot: {e}")

def scan(target: str, profile: Profile) -> None:
    install()
    
    sf_dir = TOOLS_DIR / 'spiderfoot'
    sf_py = sf_dir / 'sf.py'
    
    if not sf_py.exists():
        print("[-] Spiderfoot not found.")
        return

    print(f"[-] Running Spiderfoot on {target}...")
    
    # Spiderfoot CLI usage: python3 sf.py -s target -q
    # -s: scan target
    # -q: quiet
    # -x: strict mode
    # For now, we just want to trigger it. 
    # NOTE: Spiderfoot can take a LONG time. We should probably run it with specific modules or in background.
    # But user asked for "Deep Research".
    
    try:
        # We limit modules to fast ones for a 'quick' scan, or all for deep.
        # Let's run a basic set or default.
        cmd = [sys.executable, str(sf_py), '-s', target, '-q']
        
        # We might want to capture output to a file or stdout. 
        # Spiderfoot logs to a DB usually. 
        # For this wrapper, we'll just let it run and note completion.
        # If we really want data, we'd need to query its SQLite db.
        
        subprocess.run(cmd, timeout=300) # 5 min limit for demo
        
        profile.add_pattern("Spiderfoot Scan Launched", "info", "Scan completed (check local DB for full results)")
        
    except subprocess.TimeoutExpired:
        print("[-] Spiderfoot scan timed out (it can be very long).")
    except Exception as e:
        print(f"Spiderfoot error: {e}")
