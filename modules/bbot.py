"""
BBOT Wrapper.
Wraps the Black Lantern Security BBOT framework.
"""
import sys
import subprocess
import shutil
from pathlib import Path
from core.engine import Profile

META = {
    'description': 'Recursive Modular OSINT Framework',
    'target_type': 'domain'
}

def is_installed():
    """Check if bbot is in path."""
    return shutil.which('bbot') is not None

def install():
    """Install BBOT via pip."""
    if is_installed():
        return

    print("[-] Installing BBOT...")
    try:
        # BBOT is huge, strictly use pip
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'bbot'], check=True)
        print("[+] BBOT installed successfully.")
    except Exception as e:
        print(f"[!] Failed to install BBOT: {e}")

def scan(target: str, profile: Profile) -> None:
    install()
    
    if not is_installed():
        print("[-] BBOT binary not found even after install attempt.")
        return

    print(f"[-] Running BBOT on {target}...")
    
    # BBOT usage: bbot -t target.com -f subdomain-enum -y (auto-yes)
    # BBOT produces a lot of output. We usually want to trust its default output dir.
    # We will try to capture its summary or basic findings.
    
    try:
        # We run a basic subdomain enum scan to avoid a 2-hour recursive crawl default
        # -f subdomain-enum
        # -o data/scans/bbot_... (optional, bbot manages its own scans usually in ~/.bbot)
        # --silent to reduce noise? No, we might want to see progress in logs.
        
        cmd = ['bbot', '-t', target, '-f', 'subdomain-enum', '--yes']
        
        # We can run it and wait
        process = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        # Parse stdout for interesting lines? 
        # BBOT outputs CSV/JSON.
        
        profile.add_pattern("BBOT Scan", "info", "BBOT execution complete (check terminal/logs)")
        
        # We could try to read ~/.bbot/scans/latest/output.csv if we want to populate the profile.
        # But BBOT structure is complex. For now, "Execution" is the primary goal.
        
    except subprocess.TimeoutExpired:
        print("[-] BBOT scan timed out (limit 10 mins).")
    except Exception as e:
        print(f"BBOT error: {e}")
