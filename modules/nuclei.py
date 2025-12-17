"""
Nuclei module for AthenaOSINT.

This module wraps the ProjectDiscovery Nuclei tool for vulnerability scanning.
Requires 'nuclei' to be installed and in the system PATH.
"""

import subprocess
import json
import shutil
import tempfile
import os
from typing import Dict, List, Any
from colorama import Fore, Style
from loguru import logger

from core.engine import Profile

def scan(target: str, profile: Profile) -> None:
    """Scan a target using Nuclei.
    
    Args:
        target: Target domain/URL to scan
        profile: Profile object to update
    """
    # Only run on domains or URLs
    if '@' in target:
        return
        
    nuclei_path = shutil.which('nuclei')
    if not nuclei_path:
        logger.warning("Nuclei binary not found in PATH. Skipping module.")
        print(f"{Fore.YELLOW}[!] Nuclei tool not found. Please install it to use this module.{Style.RESET_ALL}")
        return

    # Check if we have gathered subdomains to scan
    targets_to_scan = [target]
    if profile.subdomains:
        targets_to_scan.extend(profile.subdomains)
    
    # Limit number of targets to avoid massive long scans in this framework context
    # or write them to a file target_list.txt
    
    print(f"{Fore.CYAN}[+] Running Nuclei on {len(targets_to_scan)} targets...{Style.RESET_ALL}")
    
    try:
        # Write targets to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as target_file:
            for t in targets_to_scan:
                target_file.write(f"{t}\n")
            target_list_path = target_file.name
            
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as output_file:
            output_path = output_file.name

        # Run nuclei
        # -l targets.txt -json -o output.json -t cves,exposures (limit templates for speed)
        cmd = [
            nuclei_path,
            '-l', target_list_path,
            '-json-export', output_path,
            '-tags', 'cve,misconfig,exposure', # Reasonable default tags
            '-rate-limit', '50'
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 5 minute timeout? Nuclei can be long. Let's say 10 mins.
        try:
             stdout, stderr = process.communicate(timeout=600)
        except subprocess.TimeoutExpired:
             process.kill()
             logger.warning("Nuclei scan timed out")
             print(f"{Fore.YELLOW}[!] Nuclei scan timed out{Style.RESET_ALL}")

        vulns_found = 0
        
        # Parse output
        if os.path.exists(output_path):
            with open(output_path, 'r') as f:
                # Nuclei outputs JSON lines output (sometimes) or list
                # Usually json-export is a JSON array in recent versions? 
                # Or -json is jsonl. Let's handle json lines.
                content = f.read()
                if content.strip():
                    try:
                        # Try parsing as whole json
                        entries = json.loads(content)
                        if isinstance(entries, list):
                            for entry in entries:
                                _process_nuclei_entry(entry, profile)
                                vulns_found += 1
                        else:
                            # Single entry?
                            _process_nuclei_entry(entries, profile)
                            vulns_found += 1
                    except json.JSONDecodeError:
                        # Try lines
                        lines = content.splitlines()
                        for line in lines:
                             try:
                                 entry = json.loads(line)
                                 _process_nuclei_entry(entry, profile)
                                 vulns_found += 1
                             except:
                                 pass
        
        # Clean up
        os.unlink(target_list_path)
        if os.path.exists(output_path):
            os.unlink(output_path)
            
        if vulns_found > 0:
            print(f"  {Fore.RED}└─ Found {vulns_found} potential vulnerabilities!{Style.RESET_ALL}")
            logger.warning(f"Nuclei: Found {vulns_found} issues")
        else:
            print(f"  {Fore.GREEN}└─ No critical vulnerabilities found.{Style.RESET_ALL}")

    except Exception as e:
        logger.error(f"Nuclei wrapper failed: {e}")
        print(f"{Fore.RED}[!] Nuclei wrapper failed: {e}{Style.RESET_ALL}")

def _process_nuclei_entry(entry: Dict, profile: Profile):
    """Process a single nuclei result."""
    info = entry.get('info', {})
    severity = info.get('severity', 'low')
    name = info.get('name', 'Unknown')
    host = entry.get('host', '')
    
    # Store in profile.raw_data or profile.breaches (as vulnerability)
    # Maybe add a 'vulnerabilities' field to Profile later? 
    # For now, put in raw_data['nuclei'] list
    
    if 'nuclei' not in profile.raw_data:
        profile.raw_data['nuclei'] = []
    
    # Only keep medium/high/critical?
    if severity in ['medium', 'high', 'critical']:
        profile.raw_data['nuclei'].append({
            'name': name,
            'severity': severity,
            'host': host,
            'matched': entry.get('matched-at', '')
        })
