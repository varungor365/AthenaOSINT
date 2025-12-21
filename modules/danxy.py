"""
DanxyTools Wrapper.
Wraps the DanxyTools multi-tool framework.
Repo: https://github.com/NgakuNgakuDevTapiScRecodePunyaGw/Danxy
"""
import sys
import subprocess
import shutil
from pathlib import Path
from core.engine import Profile

META = {
    'description': 'All-in-One Multi-Tool Framework',
    'target_type': 'none' # Dashboard tool
}

TOOLS_DIR = Path('data/tools')

def install():
    """Install DanxyTools if missing."""
    target_dir = TOOLS_DIR / 'Danxy'
    if target_dir.exists():
        return

    print("[-] Installing DanxyTools...")
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        subprocess.run(['git', 'clone', 'https://github.com/NgakuNgakuDevTapiScRecodePunyaGw/Danxy', str(target_dir)], check=True)
        # It uses a Makefile
        # make install
        if (target_dir / 'Makefile').exists():
            print("[-] Running make install for Danxy...")
            # We must be careful running 'make install' as it might try to install system packages.
            # Inspecting user request: "pkg install ... make install".
            # For this environment, we might skip the system package install part if it requires sudo/root 
            # and just try to ensure dependencies are present.
            # We'll try running it, but capture output to avoid spam.
            subprocess.run(['make', 'install'], cwd=str(target_dir), capture_output=False) # Let user see init
            
        print("[+] DanxyTools installed.")
    except Exception as e:
        print(f"[!] Failed to install Danxy: {e}")

def scan(target: str, profile: Profile) -> None:
    install()
    
    tool_dir = TOOLS_DIR / 'Danxy'
    # It runs via 'make run' or python script?
    # User said: 'make run'
    
    # Since this is an interactive dashboard, we can't easily automate a specific scan without more info.
    # We will treat this as a "system tool" that the Agent can deploy for the user to use,
    # or potentially trigger if we find CLI args.
    
    print(f"[-] DanxyTools is an interactive framework.")
    print(f"[-] To use it, run: cd {tool_dir} && make run")
    
    profile.add_metadata({"tool": "DanxyTools", "path": str(tool_dir), "note": "Interactive Framework. Run manually."})
    profile.add_pattern("DanxyTools Installed", "info", f"Framework ready at {tool_dir}")

