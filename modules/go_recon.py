"""
Go Recon Arsenal Wrapper.
Wraps advanced Go-based tools: Chaos, Katana, Dalfox, GAU, Hakrawler.
"""
import shutil
import subprocess
import os
from pathlib import Path
from core.engine import Profile

META = {
    'description': 'Advanced Go-based Recon Arsenal',
    'target_type': 'domain'
}

GO_TOOLS = [
    'chaos', 'katana', 'dalfox', 'gau', 'hakrawler', 'dnsx', 'subfinder'
]

def check_go_installed() -> bool:
    return shutil.which('go') is not None

def install_tool(tool_name: str):
    """Attempt to install a tool via go install."""
    if shutil.which(tool_name):
        return

    print(f"[-] Installing {tool_name}...")
    
    install_map = {
        'chaos': 'github.com/projectdiscovery/chaos-client/cmd/chaos@latest',
        'katana': 'github.com/projectdiscovery/katana/cmd/katana@latest',
        'dalfox': 'github.com/hahwul/dalfox/v2@latest',
        'gau': 'github.com/lc/gau/v2/cmd/gau@latest',
        'hakrawler': 'github.com/hakluke/hakrawler@latest',
        'dnsx': 'github.com/projectdiscovery/dnsx/cmd/dnsx@latest',
        'subfinder': 'github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest'
    }
    
    path = install_map.get(tool_name)
    if not path:
        return
        
    try:
        subprocess.run(['go', 'install', '-v', path], check=True)
        # Ensure GOPATH/bin is in PATH for this session
        home = Path.home()
        go_bin = home / 'go' / 'bin'
        if go_bin.exists():
            os.environ['PATH'] += os.pathsep + str(go_bin)
    except Exception as e:
        print(f"[!] Failed to install {tool_name}: {e}")

def scan(target: str, profile: Profile) -> None:
    if not check_go_installed():
        profile.add_error('go_recon', 'Go language not installed')
        return

    # 1. Chaos (Subdomains)
    install_tool('chaos')
    if shutil.which('chaos'):
        try:
            print(f"[-] Running Chaos on {target}...")
            # chaos -d target -silent
            res = subprocess.run(['chaos', '-d', target, '-silent'], capture_output=True, text=True, timeout=60)
            subs = [l.strip() for l in res.stdout.splitlines() if l.strip()]
            if subs:
                profile.add_metadata({'tool': 'chaos', 'subdomains': len(subs)})
                profile.raw_data.setdefault('subdomains', []).extend(subs)
        except Exception:
            pass

    # 2. Katana (Crawling)
    install_tool('katana')
    if shutil.which('katana'):
        try:
            print(f"[-] Running Katana on {target}...")
            # katana -u target -silent -jc
            res = subprocess.run(['katana', '-u', f"https://{target}", '-silent', '-jc', '-timeout', '10'], capture_output=True, text=True, timeout=120)
            urls = [l.strip() for l in res.stdout.splitlines() if l.strip()]
            if urls:
                profile.add_metadata({'tool': 'katana', 'urls': len(urls)})
                profile.raw_data.setdefault('urls', []).extend(urls)
        except Exception:
            pass
            
    # 3. GAU (Historical URLs)
    install_tool('gau')
    if shutil.which('gau'):
        try:
            print(f"[-] Running GAU on {target}...")
            res = subprocess.run(['gau', target, '--subs'], capture_output=True, text=True, timeout=60)
            urls = [l.strip() for l in res.stdout.splitlines() if l.strip()]
            if urls:
                profile.add_metadata({'tool': 'gau', 'urls': len(urls)})
                profile.raw_data.setdefault('urls', []).extend(urls)
        except Exception:
            pass

    # Clean duplicates in profile
    if 'subdomains' in profile.raw_data:
        profile.raw_data['subdomains'] = list(set(profile.raw_data['subdomains']))
    if 'urls' in profile.raw_data:
        profile.raw_data['urls'] = list(set(profile.raw_data['urls']))
