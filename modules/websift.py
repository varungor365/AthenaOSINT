"""
WebSift Wrapper.
Wraps the official WebSift tool for contact extraction.
Repo: https://github.com/s-r-e-e-r-a-j/WebSift
"""
import sys
import subprocess
import shutil
from pathlib import Path
from core.engine import Profile

META = {
    'description': 'Extract Contacts (Email/Phone/Socials)',
    'target_type': 'url'
}

TOOLS_DIR = Path('data/tools')

def install():
    """Install WebSift if missing."""
    target_dir = TOOLS_DIR / 'WebSift'
    if target_dir.exists():
        return

    print("[-] Installing WebSift...")
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        subprocess.run(['git', 'clone', 'https://github.com/s-r-e-e-r-a-j/WebSift.git', str(target_dir)], check=True)
        # Check for requirements
        if (target_dir / 'requirements.txt').exists():
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], cwd=str(target_dir), check=True)
        print("[+] WebSift installed successfully.")
    except Exception as e:
        print(f"[!] Failed to install WebSift: {e}")

def scan(target: str, profile: Profile) -> None:
    install()
    
    tool_dir = TOOLS_DIR / 'WebSift'
    # Check for main script. Repo structure varies. Warning: Repo might be capitalized differently.
    # checking file list in repo usually 'websift.py' or 'main.py'
    tool_path = tool_dir / 'websift.py'
    
    if not tool_path.exists():
        # Fallback check
        tool_path = tool_dir / 'main.py'
        if not tool_path.exists(): 
             # It might be executed differently. For now assuming websift.py based on common patterns
             pass

    if not tool_path.exists():
        print("[-] WebSift script not found in cloned dir.")
        return

    print(f"[-] Running WebSift on {target}...")
    
    # WebSift usage: python websift.py -u <url> -o <output>
    # We will try to parse stdout if it prints results, or checks output file.
    
    try:
        # NOTE: If WebSift is interactive, this might hang. We assume non-interactive flags if available.
        # Based on standard OSINT tools, -u is common. 
        cmd = [sys.executable, str(tool_path), '-u', target]
        
        # Capture output
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        # Simple parsing of stdout for now
        output = res.stdout
        
        # Look for emails/phones in output to add to profile
        import re
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', output)
        for email in emails:
            profile.add_email(email)
            
        # Add raw output to metadata
        profile.add_metadata({"tool": "websift", "log": output[:500] + "..."})
        
        if res.returncode == 0:
            profile.add_pattern("WebSift Scan", "info", "WebSift extraction complete")
        else:
            print(f"WebSift exited with code {res.returncode}")
            
    except subprocess.TimeoutExpired:
        print("[-] WebSift timed out.")
    except Exception as e:
        print(f"WebSift error: {e}")
