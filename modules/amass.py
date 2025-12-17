"""
Amass module for AthenaOSINT.

This module wraps the Amass tool for advanced subdomain enumeration.
Requires 'amass' to be installed and in the system PATH.
"""

import subprocess
import json
import shutil
import tempfile
import os
from typing import Dict, List, Any
from colorama import Fore, Style
from loguru import logger
from pathlib import Path

from core.engine import Profile

def scan(target: str, profile: Profile) -> None:
    """Scan a domain using Amass.
    
    Args:
        target: Domain to scan
        profile: Profile object to update
    """
    # Only run on domains
    if '@' in target or not '.' in target:
        return
        
    # Check if amass is installed
    amass_path = shutil.which('amass')
    if not amass_path:
        logger.warning("Amass binary not found in PATH. Skipping module.")
        print(f"{Fore.YELLOW}[!] Amass tool not found. Please install it to use this module.{Style.RESET_ALL}")
        return

    print(f"{Fore.CYAN}[+] Running Amass module (this may take a while)...{Style.RESET_ALL}")
    
    try:
        # Create temp file for output
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp_file:
            output_path = tmp_file.name
            
        # Run amass enum
        # -d target -json output.json -active (careful with active, maybe stick to passive for now or make it configurable)
        # Using passive for speed and safety by default unless we add config
        cmd = [
            amass_path, 'enum',
            '-d', target,
            '-json', output_path,
            '-passive' 
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for completion (could add timeout logic here)
        stdout, stderr = process.communicate(timeout=600)  # 10 min timeout
        
        if process.returncode != 0:
            logger.error(f"Amass failed: {stderr}")
            print(f"{Fore.RED}[!] Amass scan returned error{Style.RESET_ALL}")
            return
            
        # Parse Output
        found_subs = 0
        found_ips = 0
        
        with open(output_path, 'r') as f:
            for line in f:
                try:
                    if not line.strip():
                        continue
                    entry = json.loads(line)
                    
                    # Extract name (subdomain)
                    name = entry.get('name')
                    if name:
                        profile.add_subdomain(name)
                        found_subs += 1
                        
                    # Extract addresses
                    addresses = entry.get('addresses', [])
                    for addr in addresses:
                        ip = addr.get('ip')
                        if ip:
                            profile.add_ip(ip)
                            found_ips += 1
                            
                except json.JSONDecodeError:
                    continue
                    
        # Clean up
        os.unlink(output_path)
            
        print(f"  {Fore.GREEN}└─ Found {found_subs} subdomains and {found_ips} IPs{Style.RESET_ALL}")
        logger.info(f"Amass: Found {found_subs} subdomains, {found_ips} IPs")

    except subprocess.TimeoutExpired:
        logger.error("Amass scan timed out")
        print(f"{Fore.RED}[!] Amass scan timed out{Style.RESET_ALL}")
    except Exception as e:
        logger.error(f"Amass wrapper failed: {e}")
        print(f"{Fore.RED}[!] Amass wrapper failed: {e}{Style.RESET_ALL}")
