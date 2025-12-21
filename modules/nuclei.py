"""
Nuclei Module.
Automated Vulnerability Scanner with 'Critical Only' filtering.
"""

import subprocess
import json
import shutil
import tempfile
import os
import sys
from typing import Dict, List, Any
from colorama import Fore, Style
from loguru import logger
from pathlib import Path

from core.engine import Profile

META = {
    'name': 'nuclei',
    'description': 'Advanced Vulnerability Scanner',
    'category': 'exploitation',
    'risk': 'aggressive',
    'emoji': '☢️'
}

def install():
    """Attempt to install Nuclei via Go."""
    if shutil.which('nuclei'):
        return

    print("[-] It seems nuclei is missing. Attempting auto-install via Go...")
    try:
        # go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
        subprocess.run(['go', 'install', '-v', 'github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest'], check=True)
        
        # Add go bin to path if needed (though usually handled by env)
        home = str(Path.home())
        go_bin = os.path.join(home, 'go', 'bin')
        if go_bin not in os.environ['PATH']:
            os.environ['PATH'] += os.pathsep + go_bin
            
        if shutil.which('nuclei'):
             print("[+] Nuclei installed.")
        else:
             print("[!] Install appeared to work but 'nuclei' not in PATH. Check go/bin.")
             
    except Exception as e:
        print(f"[!] Nuclei install failed: {e}")

def scan(target: str, profile: Profile) -> None:
    """Scan a target using Nuclei."""
    install() # Ensure it's there
    
    nuclei_path = shutil.which('nuclei')
    if not nuclei_path:
        # Fallback check for user's go/bin
        home = str(Path.home())
        potential_path = os.path.join(home, 'go', 'bin', 'nuclei')
        if os.path.exists(potential_path):
            nuclei_path = potential_path
    
    if not nuclei_path:
        logger.warning("Nuclei not found. Skipping.")
        return

    # Filter targets
    targets_to_scan = []
    if not '@' in target: targets_to_scan.append(target)
    if profile.subdomains: targets_to_scan.extend(profile.subdomains)
    
    # Cap targets for safety in auto-mode
    targets_to_scan = targets_to_scan[:50] 

    print(f"{Fore.CYAN}[+] Nuclei Sentinel: Scanning {len(targets_to_scan)} targets (Critical/High only)...{Style.RESET_ALL}")
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as target_file:
            for t in targets_to_scan:
                target_file.write(f"{t}\n")
            target_list_path = target_file.name
            
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as output_file:
            output_path = output_file.name

        # Run nuclei with strict filtering
        cmd = [
            nuclei_path,
            '-l', target_list_path,
            '-json-export', output_path,
            '-severity', 'critical,high', # ONLY High/Critical for Lab
            '-rate-limit', '50',
            '-silent' 
        ]
        
        subprocess.run(cmd, timeout=900) # 15 min timeout

        # Parse
        vulns = 0
        if os.path.exists(output_path):
             content = ""
             with open(output_path, 'r') as f: content = f.read()
             
             # JSONL parsing
             if content.strip():
                 lines = content.splitlines()
                 for line in lines:
                     try:
                         entry = json.loads(line)
                         info = entry.get('info', {})
                         sev = info.get('severity', 'low')
                         name = info.get('name', 'Unknown')
                         url = entry.get('matched-at', '')
                         
                         profile.add_pattern("Vulnerability", sev, f"{name} at {url}")
                         
                         # Add to raw data
                         if 'nuclei' not in profile.raw_data: profile.raw_data['nuclei'] = []
                         profile.raw_data['nuclei'].append(entry)
                         vulns += 1
                     except: pass
                     
        if vulns > 0:
            print(f"  {Fore.RED}└─ Nuclei found {vulns} CRITICAL issues!{Style.RESET_ALL}")
        else:
             print(f"  {Fore.GREEN}└─ Clean scan.{Style.RESET_ALL}")

        # Cleanup
        os.unlink(target_list_path)
        if os.path.exists(output_path): os.unlink(output_path)

    except Exception as e:
        logger.error(f"Nuclei Error: {e}")
