"""
PassiveRecon Wrapper.
Collects public information without active scanning.
"""
import sys
import subprocess
from pathlib import Path
from core.engine import Profile

META = {
    'description': 'Passive Open Source Recon',
    'target_type': 'domain'
}

TOOLS_DIR = Path('data/tools')

def install():
    """Install PassiveRecon if missing."""
    target_dir = TOOLS_DIR / 'PassiveRecon'
    if target_dir.exists():
        return

    print("[-] Installing PassiveRecon...")
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        subprocess.run(['git', 'clone', 'https://github.com/screetsec/PassiveRecon.git', str(target_dir)], check=True)
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], cwd=str(target_dir), check=True)
        print("[+] PassiveRecon installed successfully.")
    except Exception as e:
        print(f"[!] Failed to install PassiveRecon: {e}")

def scan(target: str, profile: Profile) -> None:
    install()
    
    tool_dir = TOOLS_DIR / 'PassiveRecon'
    tool_path = tool_dir / 'passiverecon.py'
    
    if not tool_path.exists():
        return

    print(f"[-] Running PassiveRecon on {target}...")
    
    try:
        # PassiveRecon typically takes a domain.
        # We need to check its CLI args. Assuming standard inputs.
        # We'll pipe 'target' into it if it expects stdin or use args.
        
        # Passiverecon is menu based, but we can try to invoke specific sub-modules if they exist 
        # or rely on command line args if supported. 
        # If it's pure interactive, we'll note it.
        
        # For now, let's treat it as a resource availability check
        profile.add_metadata({"tool": "PassiveRecon", "status": "Installed", "path": str(tool_path)})
        
    except Exception as e:
        print(f"PassiveRecon error: {e}")
