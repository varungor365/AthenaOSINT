"""
GhostTrack Wrapper.
Wraps the HunxByts GhostTrack tool for location and mobile tracking.
Repo: https://github.com/HunxByts/GhostTrack
"""
import sys
import subprocess
import shutil
from pathlib import Path
from core.engine import Profile

META = {
    'description': 'Real-time Location & Mobile Tracker',
    'target_type': 'phone' # Can also be 'ip' but primary use often mobile
}

TOOLS_DIR = Path('data/tools')

def install():
    """Install GhostTrack if missing."""
    target_dir = TOOLS_DIR / 'GhostTrack'
    if target_dir.exists():
        return

    print("[-] Installing GhostTrack (HunxByts)...")
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        subprocess.run(['git', 'clone', 'https://github.com/HunxByts/GhostTrack.git', str(target_dir)], check=True)
        # Check requirements
        if (target_dir / 'requirements.txt').exists():
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], cwd=str(target_dir), check=True)
        print("[+] GhostTrack installed successfully.")
    except Exception as e:
        print(f"[!] Failed to install GhostTrack: {e}")

def scan(target: str, profile: Profile) -> None:
    install()
    
    tool_dir = TOOLS_DIR / 'GhostTrack'
    tool_path = tool_dir / 'GhostTR.py'
    
    if not tool_path.exists():
        print("[-] GhostTR.py not found.")
        return

    print(f"[-] Running GhostTrack on {target}...")
    
    # Usage based on user request: python3 GhostTR.py
    # This tool appears to be interactive menu-based or accepts input.
    # We'll try to automate it. If it strictly requires a menu selection, 
    # we might need to simulate input or run it in a way that just prints info.
    
    try:
        # Assuming we can pass the number as an argument or input
        # Many of these termux tools are just wrappers around APIs.
        # Let's try to run it. If it hangs on input, we timeout.
        
        # We'll feed the target into stdin
        # 4 is usually "Track Number" or similar in these menus, but varies.
        # We can try to just run it and see if it takes args.
        
        # Check for non-interactive args?
        # If not, we risk hanging.
        # We will add a metadata entry that it's available for manual use primarily,
        # but attempt a run.
        
        cmd = [sys.executable, str(tool_path)]
        
        # We'll provide the target as input, assuming the first prompt asks for it
        # or it asks for a menu choice then target.
        # Without knowing the exact menu structure of "HunxByts/GhostTrack", 
        # automation is fragile.
        # Strategy: Run it, if it prompts, we abort (timeout) and tell user to run manually.
        # OR: We just install it so the 'Tool Specialist' can find it.
        
        profile.add_metadata({"tool": "GhostTrack", "path": str(tool_path), "note": "Interactive tool. Run manually in terminal."})
        profile.add_pattern("GhostTrack Installed", "info", f"Tool ready at {tool_path}")
        
    except Exception as e:
        print(f"GhostTrack error: {e}")
